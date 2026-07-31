import argparse
import json
import statistics
import sys
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.evaluation.fta_evaluator import FTAEvaluator


TERM_METRICS = [
    "fta",
    "fta_mean_sentence",
    "fta_coverage",
    "term_recall",
    "term_precision",
    "term_f1",
    "term_source_coverage",
    "term_prediction_coverage",
    "term_source_instances",
    "term_prediction_instances",
    "term_hits",
    "term_false_positives",
]


def read_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def read_config() -> dict:
    with open(PROJECT_ROOT / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_eval_dir(path: Path) -> tuple[str, str]:
    prefix = "p2_eval_model_"
    if not path.name.startswith(prefix) or "_test_" not in path.name:
        raise ValueError(f"Not an evaluation directory: {path}")
    model_and_test = path.name[len(prefix):]
    model, test = model_and_test.split("_test_", 1)
    return model, test


def parse_seed_dir(path: Path) -> int:
    return int(path.name.replace("seed_", ""))


def metric_values(rows: list[dict], metric: str) -> list[float]:
    return [row[metric] for row in rows if row.get(metric) is not None]


def mean_std(rows: list[dict], metric: str) -> tuple[float | None, float]:
    values = metric_values(rows, metric)
    if not values:
        return None, 0.0
    return statistics.mean(values), statistics.stdev(values) if len(values) > 1 else 0.0


def summarize(rows: list[dict], model: str, test: str) -> dict:
    summary = {"model": model, "test": test, "seeds": len(rows)}
    for metric in ["bleu", "chrf", *TERM_METRICS]:
        mean, std = mean_std(rows, metric)
        summary[f"{metric}_mean"] = mean
        summary[f"{metric}_std"] = std
    return summary


def recompute_eval_dir(eval_dir: Path, evaluator: FTAEvaluator) -> dict | None:
    model, test = parse_eval_dir(eval_dir)
    rows = []

    for seed_dir in sorted(eval_dir.glob("seed_*")):
        pred_path = seed_dir / "predictions.json"
        if not pred_path.exists():
            continue

        predictions = read_json(pred_path)
        sources = [row["source"] for row in predictions]
        outputs = [row["prediction"] for row in predictions]
        references = [row["reference"] for row in predictions]
        metrics = evaluator.evaluate_all(sources, outputs, references)

        row = {
            "model": model,
            "test": test,
            "seed": parse_seed_dir(seed_dir),
            "bleu": metrics["bleu"],
            "chrf": metrics["chrf"],
        }
        row.update({name: metrics.get(name) for name in TERM_METRICS})
        write_json(seed_dir / "metrics.json", row)
        rows.append(row)

    if not rows:
        return None

    summary = summarize(rows, model, test)
    write_json(eval_dir / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-dir", help="One p2_eval_model_*_test_* directory to recompute.")
    parser.add_argument("--all", action="store_true", help="Recompute every existing p2 eval directory.")
    args = parser.parse_args()

    if not args.all and not args.eval_dir:
        parser.error("Use --all or --eval-dir.")

    cfg = read_config()
    output_root = PROJECT_ROOT / cfg["paths"]["output_dir"]
    glossary_path = PROJECT_ROOT / "data/term/npd_glossary_cleaned.json"
    evaluator = FTAEvaluator(str(glossary_path), src_lang="en", tgt_lang="no", use_comet=False)

    eval_dirs = [Path(args.eval_dir)] if args.eval_dir else sorted(output_root.glob("p2_eval_model_*_test_*"))
    for eval_dir in eval_dirs:
        summary = recompute_eval_dir(eval_dir, evaluator)
        if summary is None:
            print(f"Skipped {eval_dir}: no predictions found")
            continue
        print(
            f"{eval_dir.name}: "
            f"BLEU={summary['bleu_mean']:.4f}, "
            f"chrF={summary['chrf_mean']:.2f}, "
            f"TermR={summary['term_recall_mean']:.4f}, "
            f"TermP={summary['term_precision_mean']:.4f}, "
            f"TermF1={summary['term_f1_mean']:.4f}"
        )


if __name__ == "__main__":
    main()
