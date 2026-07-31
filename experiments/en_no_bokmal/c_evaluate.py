import argparse
import gc
import json
import logging
import os
import statistics
import sys
import traceback
from pathlib import Path

import torch
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

GLOSSARY_PATH = Path(
    os.environ.get("NPD_GLOSSARY_PATH", PROJECT_ROOT / "data/term/npd_glossary_cleaned.json")
)

if os.environ.get("HF_CACHE_DIR"):
    cache_dir = os.environ["HF_CACHE_DIR"]
    os.environ.setdefault("HF_HOME", cache_dir)
    os.environ.setdefault("TRANSFORMERS_CACHE", cache_dir)
    os.environ.setdefault("HF_DATASETS_CACHE", cache_dir)
    os.environ.setdefault("TORCH_HOME", cache_dir)

from peft import PeftModel
from transformers import AutoModelForSeq2SeqLM

from scripts.data.data_loader import DataManager
from scripts.data.dataset import TranslationDataset
from scripts.evaluation.fta_evaluator import FTAEvaluator
from scripts.model.lora_trainer import LoRATrainer
from experiments.en_no_bokmal.model_registry import MODELS, apply_model_spec, output_prefix

DATASETS = {
    "original": {
        "train": "data/final_splits_npd/train.json",
        "val": "data/final_splits_npd/val.json",
        "test": "data/final_splits_npd/test.json",
    },
    "bokmal": {
        "train": "data/final_splits_npd_bokmal/train.jsonl",
        "val": "data/final_splits_npd_bokmal/val.jsonl",
        "test": "data/final_splits_npd_bokmal/test.jsonl",
    },
    "original_subsampled": {
        "train": "data/final_splits_npd_original_subsampled/train.json",
        "val": "data/final_splits_npd_original_subsampled/val.json",
        "test": "data/final_splits_npd_original_subsampled/test.json",
    },
    "flores_nob": {
        "test": "data/flores_ood/flores_nob/devtest.json",
    },
    "flores_nno": {
        "test": "data/flores_ood/flores_nno/devtest.json",
    },
}

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


def make_logger(output_dir: Path) -> logging.Logger:
    logger = logging.getLogger(f"p2_eval:{output_dir}")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s  %(message)s", datefmt="%H:%M:%S")

    for handler in (logging.StreamHandler(), logging.FileHandler(output_dir / "experiment.log", encoding="utf-8")):
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def read_config() -> dict:
    with open(PROJECT_ROOT / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def write_json(path: Path, data, *, ensure_ascii=True):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=ensure_ascii)


def load_test_set(base_cfg: dict, test_name: str):
    dataset = DATASETS[test_name]
    test_path = PROJECT_ROOT / dataset["test"]

    if "train" not in dataset or "val" not in dataset:
        return TranslationDataset.from_file(
            test_path,
            src_lang=base_cfg["model"]["src_lang"],
            tgt_lang=base_cfg["model"]["tgt_lang"],
        )

    cfg = dict(base_cfg)
    cfg["data"] = dataset
    _, _, test_ds = DataManager(cfg).load_splits()
    return test_ds


def adapter_path(output_dir: Path, model_id: str, model_name: str, seed: int) -> Path:
    prefix = output_prefix(model_id)
    return output_dir / f"{prefix}_train_{model_name}" / f"seed_{seed}" / "training" / "final_model"


def load_adapter(cfg: dict, path: Path):
    base_model = AutoModelForSeq2SeqLM.from_pretrained(
        cfg["model"]["pretrained"],
        torch_dtype=torch.float16,
        device_map="auto",
    )
    model = PeftModel.from_pretrained(base_model, str(path))
    model.eval()
    return model, base_model


def load_base_model(cfg: dict):
    model = AutoModelForSeq2SeqLM.from_pretrained(
        cfg["model"]["pretrained"],
        torch_dtype=torch.float16,
        device_map="auto",
    )
    model.eval()
    return model


def evaluate_seed(seed, args, cfg, test_ds, evaluator, logger):
    trainer = LoRATrainer(
        model_name=cfg["model"]["pretrained"],
        src_lang=cfg["model"]["src_lang"],
        tgt_lang=cfg["model"]["tgt_lang"],
    )

    try:
        if args.model == "base":
            model = load_base_model(cfg)
        else:
            path = adapter_path(PROJECT_ROOT / cfg["paths"]["output_dir"], args.model_id, args.model, seed)
            if not path.exists():
                logger.warning(f"seed={seed}: missing adapter at {path}")
                return None, None
            model, base_model = load_adapter(cfg, path)

        sources = [sample.source for sample in test_ds.samples]
        references = [sample.target for sample in test_ds.samples]
        predictions = trainer.generate_predictions(
            model,
            test_ds,
            batch_size=8,
            max_length=cfg["generation"].get("max_length", 128),
            num_beams=cfg["generation"]["num_beams"],
        )
        metrics = evaluator.evaluate_all(sources, predictions, references)
        row = {
            "model_id": args.model_id,
            "model": args.model,
            "test": args.test,
            "seed": seed,
            "bleu": metrics["bleu"],
            "chrf": metrics["chrf"],
        }
        row.update({name: metrics.get(name) for name in TERM_METRICS})
        pred_rows = [
            {"source": src, "prediction": pred, "reference": ref}
            for src, pred, ref in zip(sources, predictions, references)
        ]
        logger.info(
            f"seed={seed}  BLEU={row['bleu']:.4f}  chrF={row['chrf']:.2f}  "
            f"TermR={row['term_recall']:.4f}  "
            f"TermP={row['term_precision']:.4f}  "
            f"TermF1={row['term_f1']:.4f}"
        )
        return row, pred_rows

    except Exception as exc:
        logger.error(f"seed={seed} failed: {exc}\n{traceback.format_exc()}")
        return None, None

    finally:
        del trainer
        if "model" in locals():
            del model
        if "base_model" in locals():
            del base_model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()


def summarize(rows: list[dict], model_name: str, test_name: str) -> dict:
    def mean_std(metric: str):
        values = [row[metric] for row in rows if row.get(metric) is not None]
        if not values:
            return None, 0.0
        return statistics.mean(values), statistics.stdev(values) if len(values) > 1 else 0.0

    summary = {
        "model": model_name,
        "test": test_name,
        "seeds": len(rows),
    }
    for metric in ["bleu", "chrf", *TERM_METRICS]:
        mean, std = mean_std(metric)
        summary[f"{metric}_mean"] = mean
        summary[f"{metric}_std"] = std
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=["base", "original", "bokmal", "original_subsampled"], required=True)
    parser.add_argument("--model-id", choices=sorted(MODELS), default="nllb_600m")
    parser.add_argument(
        "--test",
        choices=["original", "bokmal", "original_subsampled", "flores_nob", "flores_nno"],
        required=True,
    )
    args = parser.parse_args()

    cfg = apply_model_spec(read_config(), args.model_id)
    prefix = output_prefix(args.model_id)
    output_dir = PROJECT_ROOT / cfg["paths"]["output_dir"] / f"{prefix}_eval_model_{args.model}_test_{args.test}"
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = make_logger(output_dir)

    logger.info(f"Paper2 eval: model_id={args.model_id} model={args.model} test={args.test}")
    logger.info(f"Base model: {cfg['model']['pretrained']}")
    test_ds = load_test_set(cfg, args.test)
    logger.info(f"Test examples: {len(test_ds)}")

    evaluator = FTAEvaluator(str(GLOSSARY_PATH), src_lang="en", tgt_lang="no", use_comet=False)
    rows = []

    seeds = [0] if args.model == "base" else cfg.get("experiment", {}).get("seeds", [42, 123, 456])
    for seed in seeds:
        seed_dir = output_dir / f"seed_{seed}"
        seed_dir.mkdir(parents=True, exist_ok=True)

        row, predictions = evaluate_seed(seed, args, cfg, test_ds, evaluator, logger)
        if row is None:
            continue

        write_json(seed_dir / "metrics.json", row)
        write_json(seed_dir / "predictions.json", predictions, ensure_ascii=False)
        rows.append(row)

    if not rows:
        logger.error("No results collected.")
        return

    summary = summarize(rows, args.model, args.test)
    write_json(output_dir / "summary.json", summary)
    logger.info(
        f"SUMMARY  BLEU={summary['bleu_mean']:.4f}+/-{summary['bleu_std']:.4f}  "
        f"chrF={summary['chrf_mean']:.2f}+/-{summary['chrf_std']:.2f}  "
        f"TermR={summary['term_recall_mean']:.4f}+/-{summary['term_recall_std']:.4f}  "
        f"TermP={summary['term_precision_mean']:.4f}+/-{summary['term_precision_std']:.4f}  "
        f"TermF1={summary['term_f1_mean']:.4f}+/-{summary['term_f1_std']:.4f}"
    )
    logger.info(f"Results saved to {output_dir}")


if __name__ == "__main__":
    main()
