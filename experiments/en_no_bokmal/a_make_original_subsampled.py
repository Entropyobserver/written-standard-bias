import json
import random
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SEED = 42

SOURCE_DIR = PROJECT_ROOT / "data/final_splits_npd"
TARGET_DIR = PROJECT_ROOT / "data/final_splits_npd_original_subsampled"

TARGET_SIZES = {
    "train": 10114,
    "val": 1305,
    "test": 1313,
}


def read_json(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def sample_split(split: str, size: int) -> list[dict]:
    data = read_json(SOURCE_DIR / f"{split}.json")
    if size > len(data):
        raise ValueError(f"Cannot sample {size} examples from {split}; only {len(data)} available")

    rng = random.Random(f"{SEED}:{split}")
    indices = sorted(rng.sample(range(len(data)), size))
    return [data[i] for i in indices]


def main():
    manifest = {
        "source_dir": str(SOURCE_DIR.relative_to(PROJECT_ROOT)),
        "seed": SEED,
        "splits": {},
    }

    for split, size in TARGET_SIZES.items():
        sampled = sample_split(split, size)
        write_json(TARGET_DIR / f"{split}.json", sampled)
        manifest["splits"][split] = {
            "source_size": len(read_json(SOURCE_DIR / f"{split}.json")),
            "sampled_size": len(sampled),
        }

    write_json(TARGET_DIR / "manifest.json", manifest)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
