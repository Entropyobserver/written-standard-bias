import argparse
import csv
import json
import random
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SEED = 42


def read_json(path: Path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def fix_display_text(text: str) -> str:
    """Fix mojibake that appears in old prediction files before human annotation."""
    replacements = {
        "氓": "å",
        "酶": "ø",
        "忙": "æ",
        "芦": "«",
        "禄": "»",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return " ".join(text.split())


def short_text(text: str, max_chars: int) -> str:
    text = fix_display_text(text)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def prediction_path(model: str, test_set: str, seed: int) -> Path:
    return PROJECT_ROOT / f"outputs/p2_eval_model_{model}_test_{test_set}/seed_{seed}/predictions.json"


def slide_path(model: str, test_set: str, seed: int) -> Path:
    return PROJECT_ROOT / f"outputs/slide_analysis/model_{model}_test_{test_set}/seed_{seed}/slide_sentence_scores.json"


def load_rows(seed: int):
    sub_preds = read_json(prediction_path("original_subsampled", "original", seed))
    bok_preds = read_json(prediction_path("bokmal", "original", seed))
    sub_slide = read_json(slide_path("original_subsampled", "original", seed))
    bok_slide = read_json(slide_path("bokmal", "original", seed))

    rows = []
    for idx, (sub_pred, bok_pred, sub_score, bok_score) in enumerate(
        zip(sub_preds, bok_preds, sub_slide, bok_slide)
    ):
        rows.append(
            {
                "source_index": idx,
                "source": sub_pred["source"],
                "reference": sub_pred["reference"],
                "original_subsampled": sub_pred["prediction"],
                "bokmal": bok_pred["prediction"],
                "reference_nb": bok_score.get("reference_nb", 0.0),
                "reference_nn": bok_score.get("reference_nn", 0.0),
                "original_subsampled_nb": sub_score.get("prediction_nb", 0.0),
                "original_subsampled_nn": sub_score.get("prediction_nn", 0.0),
                "bokmal_nb": bok_score.get("prediction_nb", 0.0),
                "bokmal_nn": bok_score.get("prediction_nn", 0.0),
            }
        )
    return rows


def select_shift_examples(rows, n_items: int):
    candidates = []
    for row in rows:
        if row["reference_nn"] < 0.45:
            continue
        if row["bokmal_nb"] < 0.80:
            continue
        score = (
            (row["reference_nn"] - row["reference_nb"])
            + (row["bokmal_nb"] - row["bokmal_nn"])
            + max(0.0, row["original_subsampled_nn"] - row["bokmal_nn"])
        )
        candidates.append((score, row))
    return [row for _, row in sorted(candidates, key=lambda item: item[0], reverse=True)[:n_items]]


def select_control_examples(rows, n_items: int, rng: random.Random):
    candidates = [
        row
        for row in rows
        if row["reference_nb"] >= 0.80
        and row["reference_nn"] < 0.20
        and row["bokmal_nb"] >= 0.80
        and row["original_subsampled_nb"] >= 0.80
    ]
    rng.shuffle(candidates)
    return candidates[:n_items]


def make_annotation_rows(shift_rows, control_rows, rng: random.Random, max_chars: int):
    annotation_rows = []
    key_rows = []
    selected = [("shift", row) for row in shift_rows] + [("control", row) for row in control_rows]
    rng.shuffle(selected)

    for item_no, (stratum, row) in enumerate(selected, start=1):
        item_id = f"H{item_no:03d}"
        if rng.random() < 0.5:
            system_a_name = "original_subsampled"
            system_b_name = "bokmal"
        else:
            system_a_name = "bokmal"
            system_b_name = "original_subsampled"

        annotation_rows.append(
            {
                "item_id": item_id,
                "source": short_text(row["source"], max_chars),
                "reference": short_text(row["reference"], max_chars),
                "system_a": short_text(row[system_a_name], max_chars),
                "system_b": short_text(row[system_b_name], max_chars),
                "adequacy_a_0_1_2": "",
                "adequacy_b_0_1_2": "",
                "bokmal_a_0_1_2": "",
                "bokmal_b_0_1_2": "",
                "preferred_for_bokmal_a_b_tie": "",
                "notes": "",
            }
        )
        key_rows.append(
            {
                "item_id": item_id,
                "stratum": stratum,
                "source_index": row["source_index"],
                "system_a_model": system_a_name,
                "system_b_model": system_b_name,
                "reference_nb": row["reference_nb"],
                "reference_nn": row["reference_nn"],
                "original_subsampled_nb": row["original_subsampled_nb"],
                "original_subsampled_nn": row["original_subsampled_nn"],
                "bokmal_nb": row["bokmal_nb"],
                "bokmal_nn": row["bokmal_nn"],
            }
        )
    return annotation_rows, key_rows


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"No rows to write: {path}")
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_instructions(path: Path):
    text = """# Human Evaluation Instructions

Please evaluate System A and System B independently. The system identities are hidden.

Scores:

- adequacy: 2 = meaning preserved, 1 = partly correct, 0 = wrong or misleading
- bokmal: 2 = natural Bokmal, 1 = mixed or acceptable but non-standard, 0 = clearly not Bokmal or unnatural
- preference: A, B, or Tie, assuming the target use case is Norwegian Bokmal petroleum translation

Use the notes column only when something is unclear.
"""
    path.write_text(text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--n-shift", type=int, default=20)
    parser.add_argument("--n-control", type=int, default=20)
    parser.add_argument("--random-seed", type=int, default=2026)
    parser.add_argument("--max-chars", type=int, default=360)
    parser.add_argument("--out-dir", type=Path, default=PROJECT_ROOT / "outputs/human_eval")
    args = parser.parse_args()

    rng = random.Random(args.random_seed)
    rows = load_rows(args.seed)
    shift_rows = select_shift_examples(rows, args.n_shift)
    control_rows = select_control_examples(rows, args.n_control, rng)
    annotation_rows, key_rows = make_annotation_rows(shift_rows, control_rows, rng, args.max_chars)

    write_csv(args.out_dir / "human_eval_sheet.csv", annotation_rows)
    write_csv(args.out_dir / "human_eval_key.csv", key_rows)
    write_instructions(args.out_dir / "instructions.md")

    summary = {
        "seed": args.seed,
        "shift_items": len(shift_rows),
        "control_items": len(control_rows),
        "total_items": len(annotation_rows),
        "annotation_sheet": str(args.out_dir / "human_eval_sheet.csv"),
        "hidden_key": str(args.out_dir / "human_eval_key.csv"),
    }
    (args.out_dir / "manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
