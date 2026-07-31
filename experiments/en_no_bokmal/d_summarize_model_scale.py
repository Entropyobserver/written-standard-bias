import csv
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from experiments.en_no_bokmal.model_registry import MODELS, output_prefix

OUTPUT_ROOT = PROJECT_ROOT / "outputs"
ANALYSIS_DIR = OUTPUT_ROOT / "p2_analysis"
TRAIN_CONDITIONS = ["original", "original_subsampled", "bokmal"]
TEST_SETS = ["bokmal", "original"]
METRICS = ["bleu", "chrf", "term_recall", "term_precision", "term_f1"]


def read_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def summary_path(model_id: str, condition: str, test_set: str) -> Path:
    prefix = output_prefix(model_id)
    return OUTPUT_ROOT / f"{prefix}_eval_model_{condition}_test_{test_set}" / "summary.json"


def load_rows():
    rows = []
    for model_id in MODELS:
        for condition in TRAIN_CONDITIONS:
            for test_set in TEST_SETS:
                path = summary_path(model_id, condition, test_set)
                if not path.exists():
                    continue
                summary = read_json(path)
                row = {
                    "model_id": model_id,
                    "condition": condition,
                    "test": test_set,
                    "seeds": summary.get("seeds", 0),
                }
                for metric in METRICS:
                    row[f"{metric}_mean"] = summary.get(f"{metric}_mean")
                    row[f"{metric}_std"] = summary.get(f"{metric}_std")
                rows.append(row)
    return rows


def make_delta_rows(rows):
    by_key = {(row["model_id"], row["condition"], row["test"]): row for row in rows}
    delta_rows = []
    for model_id in MODELS:
        for test_set in TEST_SETS:
            sub = by_key.get((model_id, "original_subsampled", test_set))
            bok = by_key.get((model_id, "bokmal", test_set))
            if not sub or not bok:
                continue
            row = {
                "model_id": model_id,
                "test": test_set,
                "comparison": "bokmal_minus_original_subsampled",
            }
            for metric in METRICS:
                bok_value = bok.get(f"{metric}_mean")
                sub_value = sub.get(f"{metric}_mean")
                row[f"delta_{metric}"] = None if bok_value is None or sub_value is None else bok_value - sub_value
            delta_rows.append(row)
    return delta_rows


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main():
    rows = load_rows()
    delta_rows = make_delta_rows(rows)

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(ANALYSIS_DIR / "model_scale_results.csv", rows)
    write_csv(ANALYSIS_DIR / "model_scale_deltas.csv", delta_rows)
    (ANALYSIS_DIR / "model_scale_results.json").write_text(
        json.dumps({"results": rows, "deltas": delta_rows}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps({"results": len(rows), "deltas": len(delta_rows)}, indent=2))


if __name__ == "__main__":
    main()
