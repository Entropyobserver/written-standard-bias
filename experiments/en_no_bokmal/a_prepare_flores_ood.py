import argparse
import json
from pathlib import Path

from datasets import load_dataset


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "data/flores_ood"

DATASET_NAME = "Muennighoff/flores200"
LANG_PAIRS = {
    "flores_nob": ("eng_Latn", "nob_Latn"),
    "flores_nno": ("eng_Latn", "nno_Latn"),
}


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def convert_split(test_name: str, src_lang: str, tgt_lang: str, split: str):
    ds = load_dataset(
        DATASET_NAME,
        f"{src_lang}-{tgt_lang}",
        split=split,
        trust_remote_code=True,
    )
    rows = []
    for item in ds:
        rows.append(
            {
                "source": item[f"sentence_{src_lang}"],
                "target": item[f"sentence_{tgt_lang}"],
                "metadata": {
                    "dataset": "flores200",
                    "source": DATASET_NAME,
                    "split": split,
                    "source_lang": src_lang,
                    "target_lang": tgt_lang,
                    "id": item.get("id"),
                    "domain": item.get("domain"),
                    "topic": item.get("topic"),
                    "url": item.get("URL"),
                },
            }
        )

    out_path = OUTPUT_DIR / test_name / f"{split}.json"
    write_json(out_path, rows)
    return out_path, len(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", default="devtest", choices=["dev", "devtest"])
    args = parser.parse_args()

    manifest = {
        "dataset": DATASET_NAME,
        "split": args.split,
        "tests": {},
    }

    for test_name, (src_lang, tgt_lang) in LANG_PAIRS.items():
        out_path, n = convert_split(test_name, src_lang, tgt_lang, args.split)
        manifest["tests"][test_name] = {
            "source_lang": src_lang,
            "target_lang": tgt_lang,
            "path": str(out_path.relative_to(PROJECT_ROOT)),
            "size": n,
        }

    write_json(OUTPUT_DIR / "manifest.json", manifest)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
