import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LABELS = ["nb_only", "nn_only", "mixed", "uncertain"]

DEFAULT_POOLS = [
    ("original_reference", "original_subsampled", "original", 42, "reference"),
    ("bokmal_reference", "original_subsampled", "bokmal", 42, "reference"),
    ("original_subsampled_prediction", "original_subsampled", "original", 42, "prediction"),
    ("bokmal_prediction", "bokmal", "original", 42, "prediction"),
]


def read_json(path: Path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"No rows to write: {path}")
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def fix_display_text(text: str) -> str:
    """Repair common UTF-8-as-GBK mojibake in old local outputs."""
    replacements = {
        "氓": "å",
        "酶": "ø",
        "忙": "æ",
        "脜": "Å",
        "脴": "Ø",
        "脝": "Æ",
        "芦": "«",
        "禄": "»",
        "掳": "°",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return " ".join(text.split())


def slide_path(model: str, test_set: str, seed: int) -> Path:
    return (
        PROJECT_ROOT
        / "outputs"
        / "slide_analysis"
        / f"model_{model}_test_{test_set}"
        / f"seed_{seed}"
        / "slide_sentence_scores.json"
    )


def normalize_slide_category(category: str) -> str:
    if category == "nb_nn_mixed":
        return "mixed"
    if category == "no_nb_nn":
        return "uncertain"
    if category in {"nb_only", "nn_only"}:
        return category
    raise ValueError(f"Unknown SLIDE category: {category!r}")


def load_candidates(pools):
    candidates = []
    seen = set()

    for pool_name, model, test_set, seed, field in pools:
        path = slide_path(model, test_set, seed)
        rows = read_json(path)
        for source_index, row in enumerate(rows):
            text = fix_display_text(row.get(field, ""))
            if not text:
                continue

            dedupe_key = (field, text.lower())
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            raw_category = row[f"{field}_category"]
            slide_label = normalize_slide_category(raw_category)
            candidates.append(
                {
                    "pool": pool_name,
                    "model": model,
                    "test_set": test_set,
                    "seed": seed,
                    "field": field,
                    "source_index": source_index,
                    "sentence": text,
                    "slide_label": slide_label,
                    "raw_slide_category": raw_category,
                    "slide_nb": row.get(f"{field}_nb"),
                    "slide_nn": row.get(f"{field}_nn"),
                    "slide_margin_nb_minus_nn": (
                        row.get(f"{field}_nb", 0.0) - row.get(f"{field}_nn", 0.0)
                    ),
                }
            )

    return candidates


def sample_by_slide_label(candidates, n_per_label: int, rng: random.Random):
    by_label = defaultdict(list)
    for row in candidates:
        by_label[row["slide_label"]].append(row)

    selected = []
    label_counts = {}
    shortages = {}
    for label in LABELS:
        rows = list(by_label[label])
        rng.shuffle(rows)
        take = min(n_per_label, len(rows))
        selected.extend(rows[:take])
        label_counts[label] = take
        if take < n_per_label:
            shortages[label] = {"requested": n_per_label, "available": len(rows)}

    rng.shuffle(selected)
    return selected, label_counts, shortages


def make_rows(selected):
    annotation_rows = []
    key_rows = []
    for item_no, row in enumerate(selected, start=1):
        item_id = f"S{item_no:03d}"
        annotation_rows.append(
            {
                "item_id": item_id,
                "sentence": row["sentence"],
                "human_label_nb_only_nn_only_mixed_uncertain": "",
                "notes": "",
            }
        )
        key = {"item_id": item_id}
        key.update(row)
        key_rows.append(key)
    return annotation_rows, key_rows


def write_instructions(path: Path):
    text = """# SLIDE Validation Annotation Instructions

Goal: independently check whether SLIDE written-standard labels are reliable on the petroleum-domain sentences used in the paper.

Annotate only the written standard of the Norwegian sentence. Do not judge translation adequacy, fluency, terminology quality, or whether the sentence is a good reference.

Use exactly one label:

- nb_only: the sentence is clearly Bokmal only.
- nn_only: the sentence is clearly Nynorsk only.
- mixed: the sentence contains clear cues from both Bokmal and Nynorsk.
- uncertain: the sentence is too short, mostly names/numbers/terms, ambiguous between standards, or otherwise not safely classifiable.

Fill only `human_label_nb_only_nn_only_mixed_uncertain` and optional `notes`. The model/source metadata and SLIDE scores are intentionally hidden from the annotation sheet.

This sample is stratified by SLIDE label to test classifier reliability. It should not be used to estimate how frequent each written standard is in the corpus.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Create a blind human annotation sheet for validating SLIDE labels."
    )
    parser.add_argument("--n-per-label", type=int, default=30)
    parser.add_argument("--random-seed", type=int, default=2026)
    parser.add_argument("--out-dir", type=Path, default=PROJECT_ROOT / "outputs/slide_validation")
    args = parser.parse_args()

    rng = random.Random(args.random_seed)
    candidates = load_candidates(DEFAULT_POOLS)
    selected, label_counts, shortages = sample_by_slide_label(candidates, args.n_per_label, rng)
    annotation_rows, key_rows = make_rows(selected)

    write_csv(args.out_dir / "slide_validation_sheet.csv", annotation_rows)
    write_csv(args.out_dir / "slide_validation_key.csv", key_rows)
    write_instructions(args.out_dir / "instructions.md")

    manifest = {
        "total_candidates": len(candidates),
        "requested_n_per_slide_label": args.n_per_label,
        "selected_items": len(annotation_rows),
        "selected_by_slide_label": label_counts,
        "shortages": shortages,
        "pools": [
            {
                "pool": pool,
                "model": model,
                "test_set": test_set,
                "seed": seed,
                "field": field,
            }
            for pool, model, test_set, seed, field in DEFAULT_POOLS
        ],
        "annotation_sheet": str(args.out_dir / "slide_validation_sheet.csv"),
        "hidden_key": str(args.out_dir / "slide_validation_key.csv"),
        "instructions": str(args.out_dir / "instructions.md"),
        "note": "The sample is stratified by SLIDE label for validation, not corpus prevalence estimation.",
    }
    write_json(args.out_dir / "manifest.json", manifest)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
