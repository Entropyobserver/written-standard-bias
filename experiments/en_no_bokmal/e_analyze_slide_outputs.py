import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

DEFAULT_MODELS = ["original", "original_subsampled", "bokmal"]
DEFAULT_TESTS = ["original", "bokmal", "flores_nob", "flores_nno"]
DEFAULT_SEEDS = [42, 123, 456]


def read_json(path: Path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def prediction_path(output_root: Path, model_name: str, test_name: str, seed: int) -> Path:
    return output_root / f"p2_eval_model_{model_name}_test_{test_name}" / f"seed_{seed}" / "predictions.json"


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
        return "nb_nn_mixed"
    if nb:
        return "nb_only"
    if nn:
        return "nn_only"
    return "no_nb_nn"


def summarize(scores: list[dict], threshold: float) -> dict:
    n = len(scores)
    counts = Counter(category(score, threshold) for score in scores)
    label_means = {
        label: sum(score.get(label, 0.0) for score in scores) / n if n else 0.0
        for label in ["nb", "nn", "da", "sv", "other"]
    }
    return {
        "n": n,
        "threshold": threshold,
        "nb_only": counts["nb_only"],
        "nn_only": counts["nn_only"],
        "nb_nn_mixed": counts["nb_nn_mixed"],
        "no_nb_nn": counts["no_nb_nn"],
        "nb_only_pct": counts["nb_only"] / n if n else 0.0,
        "nn_only_pct": counts["nn_only"] / n if n else 0.0,
        "nb_nn_mixed_pct": counts["nb_nn_mixed"] / n if n else 0.0,
        "no_nb_nn_pct": counts["no_nb_nn"] / n if n else 0.0,
        "mean_nb": label_means["nb"],
        "mean_nn": label_means["nn"],
        "mean_nb_minus_nn": label_means["nb"] - label_means["nn"],
        "mean_da": label_means["da"],
        "mean_sv": label_means["sv"],
        "mean_other": label_means["other"],
    }


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = list(rows[0])
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def analyze_file(path: Path, args, tokenizer, slide_model, labels, device: str):
    prediction_rows = read_json(path)
    texts_by_field = {
        field: [row[field] for row in prediction_rows]
        for field in args.fields
    }

    scores_by_field = {}
    summaries_by_field = {}
    for field, texts in texts_by_field.items():
        scores = classify_texts(texts, tokenizer, slide_model, labels, device, args.batch_size)
        for score in scores:
            score["category"] = category(score, args.threshold)
        scores_by_field[field] = scores
        summaries_by_field[field] = summarize(scores, args.threshold)

    sentence_rows = []
    for i, row in enumerate(prediction_rows):
        base = {
            "source": row.get("source"),
            "prediction": row.get("prediction"),
            "reference": row.get("reference"),
        }
        for field, scores in scores_by_field.items():
            scored = {f"{field}_{key}": value for key, value in scores[i].items() if key != "index"}
            base.update(scored)
        sentence_rows.append(base)

    return summaries_by_field, sentence_rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--slide-model", default="ltg/SLIDE-base")
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--tests", nargs="+", default=DEFAULT_TESTS)
    parser.add_argument("--seeds", nargs="+", type=int, default=DEFAULT_SEEDS)
    parser.add_argument("--fields", nargs="+", default=["prediction", "reference"], choices=["prediction", "reference", "source"])
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "outputs/slide_analysis"))
    args = parser.parse_args()

    output_root = PROJECT_ROOT / "outputs"
    output_dir = Path(args.output_dir)
    tokenizer, slide_model, labels = load_slide(args.slide_model, args.device)

    summary_rows = []
    missing = []

    for model_name in args.models:
        for test_name in args.tests:
            for seed in args.seeds:
                path = prediction_path(output_root, model_name, test_name, seed)
                if not path.exists():
                    missing.append(str(path.relative_to(PROJECT_ROOT)))
                    continue

                summaries, sentence_rows = analyze_file(path, args, tokenizer, slide_model, labels, args.device)
                per_seed_dir = output_dir / f"model_{model_name}_test_{test_name}" / f"seed_{seed}"
                write_json(per_seed_dir / "slide_sentence_scores.json", sentence_rows)

                for field, summary in summaries.items():
                    summary_rows.append(
                        {
                            "model": model_name,
                            "test": test_name,
                            "seed": seed,
                            "field": field,
                            **summary,
                        }
                    )

    write_json(output_dir / "summary.json", summary_rows)
    write_csv(output_dir / "summary.csv", summary_rows)
    if missing:
        write_json(output_dir / "missing_predictions.json", missing)

    print(f"Wrote {len(summary_rows)} summary rows to {output_dir}")
    if missing:
        print(f"Skipped {len(missing)} missing prediction files; see missing_predictions.json")


if __name__ == "__main__":
    main()
