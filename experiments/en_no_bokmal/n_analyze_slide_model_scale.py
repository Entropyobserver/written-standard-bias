import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from experiments.en_no_bokmal.model_registry import MODELS, output_prefix


DEFAULT_MODEL_IDS = list(MODELS)
DEFAULT_CONDITIONS = ["original", "original_subsampled", "bokmal"]
DEFAULT_TESTS = ["original", "bokmal"]
DEFAULT_SEEDS = [42, 123, 456]
DEFAULT_FIELDS = ["prediction", "reference"]


def read_json(path: Path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def prediction_path(output_root: Path, model_id: str, condition: str, test: str, seed: int) -> Path:
    prefix = output_prefix(model_id)
    return output_root / f"{prefix}_eval_model_{condition}_test_{test}" / f"seed_{seed}" / "predictions.json"


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


def classify_texts(texts: list[str], tokenizer, model, labels: list[str], device: str, batch_size: int):
    rows = []
    for start, batch in batched(texts, batch_size):
        encoded = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=256,
            return_tensors="pt",
        )
        encoded = {key: value.to(device) for key, value in encoded.items()}
        with torch.no_grad():
            probs = torch.sigmoid(model(**encoded).logits).cpu().tolist()

        for offset, prob_values in enumerate(probs):
            row = {label: float(prob_values[i]) for i, label in enumerate(labels)}
            row["index"] = start + offset
            rows.append(row)
    return rows


def category(score: dict, threshold: float) -> str:
    nb = score.get("nb", 0.0) >= threshold
    nn = score.get("nn", 0.0) >= threshold
    if nb and nn:
        return "mixed"
    if nb:
        return "nb_only"
    if nn:
        return "nn_only"
    return "uncertain"


def summarize(scores: list[dict], threshold: float) -> dict:
    n = len(scores)
    counts = Counter(category(score, threshold) for score in scores)
    mean_nb = sum(score.get("nb", 0.0) for score in scores) / n if n else 0.0
    mean_nn = sum(score.get("nn", 0.0) for score in scores) / n if n else 0.0
    return {
        "n": n,
        "threshold": threshold,
        "nb_only_pct": counts["nb_only"] / n if n else 0.0,
        "nn_only_pct": counts["nn_only"] / n if n else 0.0,
        "mixed_pct": counts["mixed"] / n if n else 0.0,
        "uncertain_pct": counts["uncertain"] / n if n else 0.0,
        "nb_only": counts["nb_only"],
        "nn_only": counts["nn_only"],
        "mixed": counts["mixed"],
        "uncertain": counts["uncertain"],
        "mean_nb": mean_nb,
        "mean_nn": mean_nn,
        "mean_nb_minus_nn": mean_nb - mean_nn,
    }


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return (sum((value - m) ** 2 for value in values) / (len(values) - 1)) ** 0.5


def analyze_file(path: Path, fields: list[str], threshold: float, tokenizer, slide_model, labels, device: str, batch_size: int):
    prediction_rows = read_json(path)
    scores_by_field = {}
    summaries_by_field = {}

    for field in fields:
        texts = [row[field] for row in prediction_rows]
        scores = classify_texts(texts, tokenizer, slide_model, labels, device, batch_size)
        for score in scores:
            score["category"] = category(score, threshold)
        scores_by_field[field] = scores
        summaries_by_field[field] = summarize(scores, threshold)

    sentence_rows = []
    for i, row in enumerate(prediction_rows):
        out = {
            "source": row.get("source"),
            "prediction": row.get("prediction"),
            "reference": row.get("reference"),
        }
        for field, scores in scores_by_field.items():
            out.update({f"{field}_{key}": value for key, value in scores[i].items() if key != "index"})
        sentence_rows.append(out)
    return summaries_by_field, sentence_rows


def aggregate_seed_rows(seed_rows: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for row in seed_rows:
        groups[(row["model_id"], row["condition"], row["test"], row["field"])].append(row)

    metric_names = [
        "nb_only_pct",
        "nn_only_pct",
        "mixed_pct",
        "uncertain_pct",
        "mean_nb",
        "mean_nn",
        "mean_nb_minus_nn",
    ]
    aggregated = []
    for (model_id, condition, test, field), rows in sorted(groups.items()):
        out = {
            "model_id": model_id,
            "condition": condition,
            "test": test,
            "field": field,
            "seeds": len(rows),
            "n_mean": mean([float(row["n"]) for row in rows]),
        }
        for metric in metric_names:
            values = [float(row[metric]) for row in rows]
            out[f"{metric}_mean"] = mean(values)
            out[f"{metric}_std"] = stdev(values)
        aggregated.append(out)
    return aggregated


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--slide-model", default="ltg/SLIDE-base")
    parser.add_argument("--model-ids", nargs="+", default=DEFAULT_MODEL_IDS)
    parser.add_argument("--conditions", nargs="+", default=DEFAULT_CONDITIONS)
    parser.add_argument("--tests", nargs="+", default=DEFAULT_TESTS)
    parser.add_argument("--seeds", nargs="+", type=int, default=DEFAULT_SEEDS)
    parser.add_argument("--fields", nargs="+", default=DEFAULT_FIELDS, choices=["prediction", "reference", "source"])
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "outputs/slide_analysis_model_scale"))
    args = parser.parse_args()

    output_root = PROJECT_ROOT / "outputs"
    output_dir = Path(args.output_dir)
    tokenizer, slide_model, labels = load_slide(args.slide_model, args.device)

    seed_rows = []
    missing = []
    for model_id in args.model_ids:
        for condition in args.conditions:
            for test in args.tests:
                for seed in args.seeds:
                    path = prediction_path(output_root, model_id, condition, test, seed)
                    if not path.exists():
                        missing.append(str(path.relative_to(PROJECT_ROOT)))
                        continue
                    summaries, sentence_rows = analyze_file(
                        path,
                        args.fields,
                        args.threshold,
                        tokenizer,
                        slide_model,
                        labels,
                        args.device,
                        args.batch_size,
                    )
                    per_seed_dir = output_dir / f"{model_id}_{condition}_{test}" / f"seed_{seed}"
                    write_json(per_seed_dir / "slide_sentence_scores.json", sentence_rows)
                    for field, summary in summaries.items():
                        seed_rows.append(
                            {
                                "model_id": model_id,
                                "condition": condition,
                                "test": test,
                                "seed": seed,
                                "field": field,
                                **summary,
                            }
                        )

    model_rows = aggregate_seed_rows(seed_rows)
    write_csv(output_dir / "summary_by_seed.csv", seed_rows)
    write_csv(output_dir / "summary_by_model.csv", model_rows)
    write_json(output_dir / "summary.json", {"by_seed": seed_rows, "by_model": model_rows, "missing": missing})
    if missing:
        write_json(output_dir / "missing_predictions.json", missing)

    print(json.dumps({"seed_rows": len(seed_rows), "model_rows": len(model_rows), "missing": len(missing)}, indent=2))


if __name__ == "__main__":
    main()
