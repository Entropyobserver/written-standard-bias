import argparse
import csv
import json
from collections import Counter, defaultdict
from math import comb
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def read_csv(path: Path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def parse_score(value: str, field: str, item_id: str) -> int:
    value = value.strip()
    if value not in {"0", "1", "2"}:
        raise ValueError(f"{item_id}: {field} must be 0, 1, or 2; got {value!r}")
    return int(value)


def parse_preference(value: str, item_id: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"a", "system a"}:
        return "a"
    if normalized in {"b", "system b"}:
        return "b"
    if normalized in {"tie", "t", "equal", "same"}:
        return "tie"
    raise ValueError(f"{item_id}: preference must be A, B, or Tie; got {value!r}")


def exact_sign_test(wins: int, losses: int) -> float:
    n = wins + losses
    if n == 0:
        return 1.0
    smaller = min(wins, losses)
    prob = sum(comb(n, k) for k in range(smaller + 1)) / (2**n)
    return min(1.0, 2 * prob)


def mean(values):
    return sum(values) / len(values) if values else None


def analyze(annotation_rows, key_rows):
    key_by_id = {row["item_id"]: row for row in key_rows}
    model_scores = defaultdict(lambda: defaultdict(list))
    stratum_scores = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    preference_counts = Counter()
    preference_by_stratum = defaultdict(Counter)
    paired_deltas = defaultdict(list)

    for row in annotation_rows:
        item_id = row["item_id"]
        key = key_by_id[item_id]
        stratum = key["stratum"]
        model_a = key["system_a_model"]
        model_b = key["system_b_model"]

        adequacy_a = parse_score(row["adequacy_a_0_1_2"], "adequacy_a_0_1_2", item_id)
        adequacy_b = parse_score(row["adequacy_b_0_1_2"], "adequacy_b_0_1_2", item_id)
        bokmal_a = parse_score(row["bokmal_a_0_1_2"], "bokmal_a_0_1_2", item_id)
        bokmal_b = parse_score(row["bokmal_b_0_1_2"], "bokmal_b_0_1_2", item_id)
        preference = parse_preference(row["preferred_for_bokmal_a_b_tie"], item_id)

        side_scores = {
            model_a: {"adequacy": adequacy_a, "bokmal": bokmal_a},
            model_b: {"adequacy": adequacy_b, "bokmal": bokmal_b},
        }
        for model, scores in side_scores.items():
            for metric, value in scores.items():
                model_scores[model][metric].append(value)
                stratum_scores[stratum][model][metric].append(value)

        for metric in ("adequacy", "bokmal"):
            delta = side_scores["bokmal"][metric] - side_scores["original_subsampled"][metric]
            paired_deltas[metric].append(delta)
            stratum_scores[stratum]["delta_bokmal_minus_original_subsampled"][metric].append(delta)

        if preference == "tie":
            winner = "tie"
        elif preference == "a":
            winner = model_a
        else:
            winner = model_b
        preference_counts[winner] += 1
        preference_by_stratum[stratum][winner] += 1

    summary = {
        "n_items": len(annotation_rows),
        "model_means": {
            model: {metric: mean(values) for metric, values in metrics.items()}
            for model, metrics in model_scores.items()
        },
        "paired_delta_bokmal_minus_original_subsampled": {
            metric: mean(values) for metric, values in paired_deltas.items()
        },
        "preference_counts": dict(preference_counts),
        "preference_sign_test_p": exact_sign_test(
            preference_counts["bokmal"], preference_counts["original_subsampled"]
        ),
        "by_stratum": {},
    }

    for stratum, models in stratum_scores.items():
        summary["by_stratum"][stratum] = {}
        for model, metrics in models.items():
            summary["by_stratum"][stratum][model] = {
                metric: mean(values) for metric, values in metrics.items()
            }
        summary["by_stratum"][stratum]["preference_counts"] = dict(preference_by_stratum[stratum])

    return summary


def write_markdown(path: Path, summary):
    lines = [
        "# Human Evaluation Summary",
        "",
        f"Items: {summary['n_items']}",
        "",
        "## Model Means",
        "",
        "| Model | Adequacy | Bokmal conformity |",
        "|---|---:|---:|",
    ]
    for model, metrics in sorted(summary["model_means"].items()):
        lines.append(f"| {model} | {metrics.get('adequacy', 0):.3f} | {metrics.get('bokmal', 0):.3f} |")

    delta = summary["paired_delta_bokmal_minus_original_subsampled"]
    lines.extend(
        [
            "",
            "## Paired Deltas",
            "",
            f"- Adequacy, Bokmal minus original-subsampled: {delta.get('adequacy', 0):+.3f}",
            f"- Bokmal conformity, Bokmal minus original-subsampled: {delta.get('bokmal', 0):+.3f}",
            "",
            "## Preference",
            "",
            f"- Counts: {summary['preference_counts']}",
            f"- Exact sign-test p-value, excluding ties: {summary['preference_sign_test_p']:.4f}",
            "",
            "## By Stratum",
            "",
        ]
    )
    for stratum, block in sorted(summary["by_stratum"].items()):
        lines.append(f"### {stratum}")
        lines.append("")
        lines.append(json.dumps(block, indent=2))
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--annotations",
        type=Path,
        default=PROJECT_ROOT / "outputs/human_eval/human_eval_sheet_filled.csv",
    )
    parser.add_argument("--key", type=Path, default=PROJECT_ROOT / "outputs/human_eval/human_eval_key.csv")
    parser.add_argument("--out-dir", type=Path, default=PROJECT_ROOT / "outputs/human_eval")
    args = parser.parse_args()

    annotation_rows = read_csv(args.annotations)
    key_rows = read_csv(args.key)
    summary = analyze(annotation_rows, key_rows)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "human_eval_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    write_markdown(args.out_dir / "human_eval_summary.md", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
