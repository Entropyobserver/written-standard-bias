import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

EVAL_COMBOS = [
    ("original", "original"),
    ("original", "bokmal"),
    ("bokmal", "original"),
    ("bokmal", "bokmal"),
]


def read_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read_config() -> dict:
    with open(PROJECT_ROOT / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_summary(output_dir: Path, model: str, test: str):
    path = output_dir / f"p2_eval_model_{model}_test_{test}" / "summary.json"
    if not path.exists():
        print(f"Missing: {path}")
        return None
    return read_json(path)


def metric_text(mean, std, digits=2):
    if mean is None:
        return "NA"
    return f"{mean:.{digits}f} +/- {std:.{digits}f}"


def build_table(results: list[dict]) -> pd.DataFrame:
    rows = []
    for result in results:
        if result is None:
            continue
        rows.append(
            {
                "model": result["model"],
                "test": result["test"],
                "BLEU": metric_text(result["bleu_mean"], result["bleu_std"]),
                "chrF": metric_text(result["chrf_mean"], result["chrf_std"]),
                "TermR": metric_text(result.get("term_recall_mean"), result.get("term_recall_std", 0.0), digits=4),
                "TermP": metric_text(result.get("term_precision_mean"), result.get("term_precision_std", 0.0), digits=4),
                "TermF1": metric_text(result.get("term_f1_mean"), result.get("term_f1_std", 0.0), digits=4),
                "TermCov": metric_text(
                    result.get("term_source_coverage_mean"),
                    result.get("term_source_coverage_std", 0.0),
                    digits=4,
                ),
            }
        )
    return pd.DataFrame(rows)


def plot_metric(results: list[dict], output_dir: Path, metric: str, ylabel: str):
    valid = [result for result in results if result and result.get(f"{metric}_mean") is not None]
    if not valid:
        print(f"No {ylabel} data to plot.")
        return

    labels = [f"M={result['model']}\nT={result['test']}" for result in valid]
    means = [result[f"{metric}_mean"] for result in valid]
    stds = [result[f"{metric}_std"] for result in valid]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(
        range(len(labels)),
        means,
        yerr=stds,
        capsize=5,
        color=["#4C72B0", "#4C72B0", "#DD8452", "#DD8452"][: len(labels)],
    )
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel(ylabel)
    ax.set_title(f"{ylabel}: original vs Bokmal model by test set")
    plt.tight_layout()

    path = output_dir / f"{metric}_comparison.png"
    fig.savefig(path, dpi=150)
    plt.close()
    print(f"Saved: {path}")


def main():
    cfg = read_config()
    output_dir = PROJECT_ROOT / cfg["paths"]["output_dir"]
    analysis_dir = output_dir / "p2_analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    results = [load_summary(output_dir, model, test) for model, test in EVAL_COMBOS]
    table = build_table(results)
    print("\n" + table.to_string(index=False))

    table.to_csv(analysis_dir / "comparison_table.csv", index=False)
    print(f"\nSaved: {analysis_dir / 'comparison_table.csv'}")

    plot_metric(results, analysis_dir, "bleu", "BLEU")
    plot_metric(results, analysis_dir, "term_recall", "Term recall")
    plot_metric(results, analysis_dir, "term_precision", "Term precision")
    plot_metric(results, analysis_dir, "term_f1", "Term F1")


if __name__ == "__main__":
    main()
