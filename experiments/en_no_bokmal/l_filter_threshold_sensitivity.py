import argparse
import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = PROJECT_ROOT / "outputs/slide_training_distribution/original_train_slide_scores.json"
DEFAULT_OUT_DIR = PROJECT_ROOT / "outputs/slide_training_distribution"
NB_THRESHOLDS = [0.6, 0.7, 0.8, 0.9]
NN_THRESHOLDS = [0.1, 0.2, 0.3, 0.4]


def read_json(path: Path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows):
    lines = [
        "# Bokmal Filter Threshold Sensitivity",
        "",
        "This is a data-selection sensitivity check only; it does not retrain MT models.",
        "",
        "| NB threshold | NN threshold | Retained | Retained % | Mean NB | Mean NN |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {nb_threshold:.1f} | {nn_threshold:.1f} | {retained} | {retained_pct:.2f} | {mean_nb:.4f} | {mean_nn:.4f} |".format(
                **row
            )
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Summarize how Bokmal filtering size changes under nearby SLIDE thresholds."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    rows = read_json(args.input)
    summary = []
    for nb_threshold in NB_THRESHOLDS:
        for nn_threshold in NN_THRESHOLDS:
            kept = [
                row
                for row in rows
                if row["bokmal_score"] >= nb_threshold and row["nynorsk_score"] < nn_threshold
            ]
            summary.append(
                {
                    "nb_threshold": nb_threshold,
                    "nn_threshold": nn_threshold,
                    "retained": len(kept),
                    "retained_pct": len(kept) / len(rows) * 100,
                    "mean_nb": sum(row["bokmal_score"] for row in kept) / len(kept) if kept else 0.0,
                    "mean_nn": sum(row["nynorsk_score"] for row in kept) / len(kept) if kept else 0.0,
                }
            )

    write_csv(args.out_dir / "filter_threshold_sensitivity.csv", summary)
    write_markdown(args.out_dir / "filter_threshold_sensitivity.md", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
