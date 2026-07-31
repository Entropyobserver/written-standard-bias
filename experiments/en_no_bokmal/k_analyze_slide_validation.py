import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LABELS = ["nb_only", "nn_only", "mixed", "uncertain"]


def read_csv(path: Path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def normalize_human_label(value: str, item_id: str) -> str:
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "nb": "nb_only",
        "bokmal": "nb_only",
        "bokmål": "nb_only",
        "bm": "nb_only",
        "nb_only": "nb_only",
        "nn": "nn_only",
        "nynorsk": "nn_only",
        "nn_only": "nn_only",
        "mixed": "mixed",
        "both": "mixed",
        "nb_nn_mixed": "mixed",
        "uncertain": "uncertain",
        "unsure": "uncertain",
        "ambiguous": "uncertain",
        "other": "uncertain",
        "no_nb_nn": "uncertain",
    }
    if normalized in aliases:
        return aliases[normalized]
    raise ValueError(f"{item_id}: unknown human label {value!r}")


def safe_div(num: float, den: float):
    return num / den if den else None


def f1_score(precision, recall):
    if precision is None or recall is None or precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def cohen_kappa(confusion):
    total = sum(sum(row.values()) for row in confusion.values())
    if total == 0:
        return None
    observed = sum(confusion[label][label] for label in LABELS) / total
    row_totals = {label: sum(confusion[label].values()) for label in LABELS}
    col_totals = {
        label: sum(confusion[human_label][label] for human_label in LABELS)
        for label in LABELS
    }
    expected = sum(row_totals[label] * col_totals[label] for label in LABELS) / (total * total)
    if expected == 1:
        return None
    return (observed - expected) / (1 - expected)


def analyze(annotation_rows, key_rows):
    key_by_id = {row["item_id"]: row for row in key_rows}
    confusion = {human: Counter({slide: 0 for slide in LABELS}) for human in LABELS}
    by_pool = defaultdict(lambda: {"n": 0, "correct": 0})
    by_field = defaultdict(lambda: {"n": 0, "correct": 0})
    skipped = []

    for row in annotation_rows:
        item_id = row["item_id"]
        key = key_by_id[item_id]
        raw_label = row.get("human_label_nb_only_nn_only_mixed_uncertain", "")
        if not raw_label.strip():
            skipped.append(item_id)
            continue
        human_label = normalize_human_label(raw_label, item_id)
        slide_label = key["slide_label"]
        if slide_label not in LABELS:
            raise ValueError(f"{item_id}: unknown SLIDE label {slide_label!r}")

        correct = human_label == slide_label
        confusion[human_label][slide_label] += 1
        by_pool[key["pool"]]["n"] += 1
        by_pool[key["pool"]]["correct"] += int(correct)
        by_field[key["field"]]["n"] += 1
        by_field[key["field"]]["correct"] += int(correct)

    total = sum(sum(row.values()) for row in confusion.values())
    correct = sum(confusion[label][label] for label in LABELS)
    per_label = {}
    f1_values = []
    for label in LABELS:
        tp = confusion[label][label]
        predicted = sum(confusion[human_label][label] for human_label in LABELS)
        actual = sum(confusion[label].values())
        precision = safe_div(tp, predicted)
        recall = safe_div(tp, actual)
        f1 = f1_score(precision, recall)
        f1_values.append(f1)
        per_label[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support_human": actual,
            "support_slide": predicted,
        }

    summary = {
        "n_annotated": total,
        "n_skipped_blank": len(skipped),
        "skipped_item_ids": skipped,
        "accuracy": safe_div(correct, total),
        "macro_f1": sum(f1_values) / len(f1_values) if f1_values else None,
        "cohen_kappa_slide_vs_human": cohen_kappa(confusion),
        "per_label": per_label,
        "confusion_matrix_rows_human_cols_slide": {
            human: {slide: confusion[human][slide] for slide in LABELS}
            for human in LABELS
        },
        "by_pool": {
            pool: {
                "n": stats["n"],
                "accuracy": safe_div(stats["correct"], stats["n"]),
            }
            for pool, stats in sorted(by_pool.items())
        },
        "by_field": {
            field: {
                "n": stats["n"],
                "accuracy": safe_div(stats["correct"], stats["n"]),
            }
            for field, stats in sorted(by_field.items())
        },
        "note": "Rows are human labels and columns are SLIDE labels. The validation sample is stratified and is not a prevalence estimate.",
    }
    return summary


def fmt(value):
    if value is None:
        return "NA"
    return f"{value:.3f}"


def write_markdown(path: Path, summary):
    lines = [
        "# SLIDE Validation Summary",
        "",
        f"Annotated items: {summary['n_annotated']}",
        f"Blank/skipped items: {summary['n_skipped_blank']}",
        f"Accuracy: {fmt(summary['accuracy'])}",
        f"Macro-F1: {fmt(summary['macro_f1'])}",
        f"Cohen's kappa: {fmt(summary['cohen_kappa_slide_vs_human'])}",
        "",
        "## Per Label",
        "",
        "| Label | Precision | Recall | F1 | Human support | SLIDE support |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for label in LABELS:
        stats = summary["per_label"][label]
        lines.append(
            "| {label} | {precision} | {recall} | {f1} | {human} | {slide} |".format(
                label=label,
                precision=fmt(stats["precision"]),
                recall=fmt(stats["recall"]),
                f1=fmt(stats["f1"]),
                human=stats["support_human"],
                slide=stats["support_slide"],
            )
        )

    lines.extend(["", "## Confusion Matrix", "", "Rows are human labels; columns are SLIDE labels.", ""])
    lines.append("| Human \\ SLIDE | " + " | ".join(LABELS) + " |")
    lines.append("|---|" + "|".join(["---:"] * len(LABELS)) + "|")
    for human in LABELS:
        row = summary["confusion_matrix_rows_human_cols_slide"][human]
        lines.append("| " + human + " | " + " | ".join(str(row[slide]) for slide in LABELS) + " |")

    lines.extend(["", "## By Pool", "", "| Pool | N | Accuracy |", "|---|---:|---:|"])
    for pool, stats in summary["by_pool"].items():
        lines.append(f"| {pool} | {stats['n']} | {fmt(stats['accuracy'])} |")

    lines.extend(["", "## By Field", "", "| Field | N | Accuracy |", "|---|---:|---:|"])
    for field, stats in summary["by_field"].items():
        lines.append(f"| {field} | {stats['n']} | {fmt(stats['accuracy'])} |")

    lines.extend(["", summary["note"]])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Analyze human validation labels for SLIDE.")
    parser.add_argument(
        "--annotations",
        type=Path,
        default=PROJECT_ROOT / "outputs/slide_validation/slide_validation_sheet_filled.csv",
    )
    parser.add_argument(
        "--key",
        type=Path,
        default=PROJECT_ROOT / "outputs/slide_validation/slide_validation_key.csv",
    )
    parser.add_argument("--out-dir", type=Path, default=PROJECT_ROOT / "outputs/slide_validation")
    args = parser.parse_args()

    annotation_rows = read_csv(args.annotations)
    key_rows = read_csv(args.key)
    summary = analyze(annotation_rows, key_rows)
    if summary["n_annotated"] == 0:
        raise ValueError(
            "No annotated rows found. Fill the human label column before running analysis."
        )

    write_json(args.out_dir / "slide_validation_summary.json", summary)
    write_markdown(args.out_dir / "slide_validation_summary.md", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
