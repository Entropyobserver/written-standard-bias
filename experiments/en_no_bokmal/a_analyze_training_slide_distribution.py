import argparse
import csv
import json
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ORIGINAL = PROJECT_ROOT / "data/final_splits_npd/train.json"
DEFAULT_BOKMAL = PROJECT_ROOT / "data/final_splits_npd_bokmal/train.jsonl"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs/slide_training_distribution"

BINS = [
    ("0.9-1.0", 0.9, 1.0000001),
    ("0.8-0.9", 0.8, 0.9),
    ("0.7-0.8", 0.7, 0.8),
    ("0.6-0.7", 0.6, 0.7),
    ("0.5-0.6", 0.5, 0.6),
    ("<0.5", float("-inf"), 0.5),
]


def read_rows(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig") as f:
        first = f.read(1)
        f.seek(0)
        if first == "[":
            return json.load(f)
        return [json.loads(line) for line in f if line.strip()]


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def row_key(row: dict) -> tuple[str, str]:
    return (row.get("source", "").strip(), row.get("target", "").strip())


def bin_label(score: float) -> str:
    for label, low, high in BINS:
        if low <= score < high:
            return label
    raise ValueError(f"Score outside expected range: {score}")


def batched(items: list[str], batch_size: int):
    for start in range(0, len(items), batch_size):
        yield start, items[start : start + batch_size]


def load_slide(model_name: str, device: str):
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForSequenceClassification.from_pretrained(model_name, trust_remote_code=True)
    model.to(device)
    model.eval()
    labels = [model.config.id2label[i] for i in range(model.config.num_labels)]
    return tokenizer, model, labels


def score_targets(rows: list[dict], model_name: str, device: str, batch_size: int, cache_path: Path) -> list[dict]:
    if all("bokmal_score" in row for row in rows):
        return rows
    if cache_path.exists():
        cached = read_rows(cache_path)
        if len(cached) == len(rows) and all("bokmal_score" in row for row in cached):
            return cached

    tokenizer, model, labels = load_slide(model_name, device)
    scored = read_rows(cache_path) if cache_path.exists() else [dict(row) for row in rows]
    if len(scored) != len(rows):
        scored = [dict(row) for row in rows]

    texts = [row["target"] for row in rows]

    for start, batch in batched(texts, batch_size):
        if all("bokmal_score" in row for row in scored[start : start + len(batch)]):
            continue

        encoded = tokenizer(batch, padding=True, truncation=True, max_length=256, return_tensors="pt")
        encoded = {key: value.to(device) for key, value in encoded.items()}
        with torch.no_grad():
            probs = torch.sigmoid(model(**encoded).logits).cpu().tolist()

        for offset, values in enumerate(probs):
            scores = {labels[i]: float(values[i]) for i in range(len(labels))}
            scored[start + offset]["bokmal_score"] = scores.get("nb", 0.0)
            scored[start + offset]["nynorsk_score"] = scores.get("nn", 0.0)

        write_json(cache_path, scored)
        done = sum(1 for row in scored if "bokmal_score" in row)
        print(f"Scored {done}/{len(scored)} targets", flush=True)

    return scored


def summarize(rows: list[dict], group_name: str) -> list[dict]:
    total = len(rows)
    out = []
    for label, low, high in BINS:
        items = [row for row in rows if low <= float(row["bokmal_score"]) < high]
        out.append(
            {
                "group": group_name,
                "nb_probability_bin": label,
                "sentences": len(items),
                "percentage": round(100 * len(items) / total, 2) if total else 0.0,
            }
        )
    return out


def main():
    parser = argparse.ArgumentParser(
        description="Summarize SLIDE Bokmal-score distribution in the original training data."
    )
    parser.add_argument("--original-train", type=Path, default=DEFAULT_ORIGINAL)
    parser.add_argument("--bokmal-train", type=Path, default=DEFAULT_BOKMAL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--slide-model", default="ltg/SLIDE-base")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    cache_path = args.output_dir / "original_train_slide_scores.json"
    original = score_targets(
        read_rows(args.original_train),
        args.slide_model,
        args.device,
        args.batch_size,
        cache_path,
    )
    bokmal = read_rows(args.bokmal_train)
    retained_keys = {row_key(row) for row in bokmal}

    retained = []
    removed = []
    scored_rows = []
    for row in original:
        score = float(row["bokmal_score"])
        status = "retained" if row_key(row) in retained_keys else "removed"
        scored = {
            "source": row.get("source", ""),
            "target": row.get("target", ""),
            "bokmal_score": score,
            "nynorsk_score": float(row.get("nynorsk_score", 0.0)),
            "bin": bin_label(score),
            "filter_status": status,
        }
        scored_rows.append(scored)
        (retained if status == "retained" else removed).append(scored)

    summary = []
    summary.extend(summarize(scored_rows, "all_original"))
    summary.extend(summarize(retained, "retained_bokmal"))
    summary.extend(summarize(removed, "removed_by_filter"))

    manifest = {
        "original_train": str(args.original_train.relative_to(PROJECT_ROOT)),
        "bokmal_train": str(args.bokmal_train.relative_to(PROJECT_ROOT)),
        "original_size": len(original),
        "retained_size": len(retained),
        "removed_size": len(removed),
        "retained_pct": round(100 * len(retained) / len(original), 2),
        "removed_pct": round(100 * len(removed) / len(original), 2),
    }

    write_json(args.output_dir / "manifest.json", manifest)
    write_json(args.output_dir / "original_train_slide_scores.json", scored_rows)
    write_csv(args.output_dir / "training_slide_distribution.csv", summary)

    print(json.dumps(manifest, indent=2))
    print()
    for row in summary:
        print(
            f"{row['group']:18s} {row['nb_probability_bin']:7s} "
            f"{row['sentences']:5d} {row['percentage']:6.2f}%"
        )


if __name__ == "__main__":
    main()
