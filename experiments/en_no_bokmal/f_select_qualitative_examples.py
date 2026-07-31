import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SEED = 42


def read_json(path: Path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def clean(text: str, max_len: int = 240) -> str:
    text = " ".join(text.split())
    return text if len(text) <= max_len else text[: max_len - 3] + "..."


def marker_note(ref: str, sub: str, bok: str) -> str:
    pairs = [
        ("ikkje", "ikke"),
        ("frå", "fra"),
        ("vere", "være"),
        ("vore", "vært"),
        ("vert", "blir"),
        ("noko", "noe"),
        ("nokon", "noen"),
        ("eit", "et"),
        ("ein", "en"),
        ("meir", "mer"),
        ("sjølv", "selv"),
        ("område", "område"),
    ]
    ref_l = ref.lower()
    sub_l = sub.lower()
    bok_l = bok.lower()
    hits = []
    for nn, nb in pairs:
        if (nn in ref_l or nn in sub_l) and nb in bok_l:
            hits.append(f"{nn}->{nb}")
    return ", ".join(hits[:3]) if hits else "SLIDE NN reference vs NB Bokmal output"


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in text)


def main():
    sub_pred_path = PROJECT_ROOT / f"outputs/p2_eval_model_original_subsampled_test_original/seed_{SEED}/predictions.json"
    bok_pred_path = PROJECT_ROOT / f"outputs/p2_eval_model_bokmal_test_original/seed_{SEED}/predictions.json"
    sub_slide_path = PROJECT_ROOT / f"outputs/slide_analysis/model_original_subsampled_test_original/seed_{SEED}/slide_sentence_scores.json"
    bok_slide_path = PROJECT_ROOT / f"outputs/slide_analysis/model_bokmal_test_original/seed_{SEED}/slide_sentence_scores.json"

    sub_preds = read_json(sub_pred_path)
    bok_preds = read_json(bok_pred_path)
    sub_slide = read_json(sub_slide_path)
    bok_slide = read_json(bok_slide_path)

    candidates = []
    for i, (sub_row, bok_row, sub_score, bok_score) in enumerate(zip(sub_preds, bok_preds, sub_slide, bok_slide)):
        ref_nn = bok_score.get("reference_nn", 0.0)
        ref_nb = bok_score.get("reference_nb", 0.0)
        bok_nb = bok_score.get("prediction_nb", 0.0)
        bok_nn = bok_score.get("prediction_nn", 0.0)
        sub_nn = sub_score.get("prediction_nn", 0.0)
        sub_nb = sub_score.get("prediction_nb", 0.0)
        score = (ref_nn - ref_nb) + (bok_nb - bok_nn) + max(0.0, sub_nn - bok_nn)

        if ref_nn < 0.45 or bok_nb < 0.80:
            continue

        note = marker_note(bok_row["reference"], sub_row["prediction"], bok_row["prediction"])
        candidates.append(
            {
                "i": i,
                "score": score,
                "ref_nn": ref_nn,
                "ref_nb": ref_nb,
                "sub_nb": sub_nb,
                "sub_nn": sub_nn,
                "bok_nb": bok_nb,
                "bok_nn": bok_nn,
                "source": clean(bok_row["source"]),
                "reference": clean(bok_row["reference"]),
                "original_subsampled": clean(sub_row["prediction"]),
                "bokmal": clean(bok_row["prediction"]),
                "note": note,
            }
        )

    selected = []
    seen_sources = set()
    for row in sorted(candidates, key=lambda item: item["score"], reverse=True):
        source_key = re.sub(r"\W+", " ", row["source"].lower())[:80]
        if source_key in seen_sources:
            continue
        seen_sources.add(source_key)
        selected.append(row)
        if len(selected) == 8:
            break

    out_dir = PROJECT_ROOT / "outputs/paper_examples"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "qualitative_examples.json", "w", encoding="utf-8") as f:
        json.dump(selected, f, indent=2, ensure_ascii=False)

    with open(out_dir / "qualitative_examples_table.tex", "w", encoding="utf-8") as f:
        for row in selected[:6]:
            f.write(
                f"{latex_escape(row['source'])} & "
                f"{latex_escape(row['reference'])} & "
                f"{latex_escape(row['original_subsampled'])} & "
                f"{latex_escape(row['bokmal'])} ({latex_escape(row['note'])}) \\\\\n"
            )

    print(json.dumps(selected[:8], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
