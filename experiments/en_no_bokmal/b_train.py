import argparse
import csv
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

from scripts.data.data_loader import DataManager
from scripts.evaluation.fta_evaluator import FTAEvaluator
from scripts.model.lora_trainer import LoRATrainer
from experiments.en_no_bokmal.model_registry import MODELS, apply_model_spec, output_prefix


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
    logger = logging.getLogger(f"p2_train:{output_dir}")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s  %(message)s", datefmt="%H:%M:%S")

    for handler in (logging.StreamHandler(), logging.FileHandler(output_dir / "experiment.log", encoding="utf-8")):
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def read_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data, *, ensure_ascii=True):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=ensure_ascii)


def load_config(data_condition: str) -> dict:
    config_paths = {
        "original": PROJECT_ROOT / "config.yaml",
        "bokmal": SCRIPT_DIR / "config_bokmal.yaml",
        "original_subsampled": SCRIPT_DIR / "config_original_subsampled.yaml",
    }
    config_path = config_paths[data_condition]
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_lora_config(cfg: dict, logger: logging.Logger) -> tuple[int, int, float]:
    best_path = PROJECT_ROOT / cfg["paths"]["output_dir"] / "exp3_optuna_stage2" / "best_config.json"
    if not best_path.exists():
        logger.info("No paper1 best_config.json found; using r=8, alpha=64, dropout=0.0")
        return 8, 64, 0.0

    best = read_json(best_path)
    logger.info(
        "Loaded paper1 LoRA config: "
        f"r={best['r']}, alpha={best['alpha']}, dropout={best['dropout']}"
    )
    return best["r"], best["alpha"], best["dropout"]


def make_train_config(cfg: dict, seed: int, seed_dir: Path, r: int, alpha: int, dropout: float) -> dict:
    max_length = cfg["model"].get("max_length", 128)
    return {
        "output_dir": str(seed_dir / "training"),
        "seed": seed,
        "r": r,
        "alpha": alpha,
        "dropout": dropout,
        "target_modules": cfg["lora"]["target_modules"],
        "epochs": cfg["training"]["epochs"],
        "batch_size": cfg["training"]["batch_size"],
        "gradient_accumulation_steps": cfg["training"].get("grad_accumulation", 4),
        "learning_rate": cfg["training"]["lr"],
        "warmup_steps": cfg["training"]["warmup_steps"],
        "eval_steps": cfg["training"]["eval_steps"],
        "early_stopping_patience": cfg["training"]["early_stopping_patience"],
        "fp16": cfg["training"]["fp16"],
        "max_length": max_length,
        "generation_max_length": cfg["generation"].get("max_length", max_length),
        "generation_num_beams": cfg["generation"]["num_beams"],
        "save_total_limit": 2,
        "save_final_model": True,
    }


def load_splits(cfg: dict):
    train_ds, val_ds, test_ds = DataManager(cfg).load_splits()
    train_data = [sample.to_dict() for sample in train_ds.samples]
    val_data = [sample.to_dict() for sample in val_ds.samples]
    sources = [sample.source for sample in test_ds.samples]
    references = [sample.target for sample in test_ds.samples]
    return train_data, val_data, test_ds, sources, references


def evaluate_on_test(trainer, model, test_ds, cfg, evaluator, sources, references) -> tuple[list[str], dict]:
    eval_batch_size = cfg.get("evaluation", {}).get("batch_size", cfg["training"]["batch_size"])
    predictions = trainer.generate_predictions(
        model,
        test_ds,
        batch_size=eval_batch_size,
        max_length=cfg["generation"].get("max_length", cfg["model"].get("max_length", 128)),
        num_beams=cfg["generation"]["num_beams"],
    )
    return predictions, evaluator.evaluate_all(sources, predictions, references)


def result_row(model_id, data_condition, seed, lora_config, train_result, test_metrics, train_data, val_data, sources):
    row = {
        "model_id": model_id,
        "data_condition": data_condition,
        "seed": seed,
        "configuration": lora_config,
        "final_model_path": train_result.get("final_model_path"),
        "val_bleu": train_result["bleu"],
        "val_chrf": train_result["chrf"],
        "val_loss": train_result["loss"],
        "test_bleu": test_metrics["bleu"],
        "test_chrf": test_metrics["chrf"],
        "dataset_sizes": {"train": len(train_data), "val": len(val_data), "test": len(sources)},
    }
    row.update({f"test_{name}": test_metrics.get(name) for name in TERM_METRICS})
    return row


def train_seed(seed, model_id, data_condition, cfg, lora_config, data, evaluator, output_dir, logger):
    train_data, val_data, test_ds, sources, references = data
    seed_dir = output_dir / f"seed_{seed}"
    seed_dir.mkdir(parents=True, exist_ok=True)

    result_path = seed_dir / "results.json"
    if result_path.exists():
        logger.info(f"seed={seed} already finished; reading cached result")
        return read_json(result_path)

    trainer = LoRATrainer(
        model_name=cfg["model"]["pretrained"],
        src_lang=cfg["model"]["src_lang"],
        tgt_lang=cfg["model"]["tgt_lang"],
    )

    try:
        train_config = make_train_config(cfg, seed, seed_dir, **lora_config)
        train_result = trainer.train(train_data, val_data, train_config)
        predictions, test_metrics = evaluate_on_test(
            trainer, train_result["model"], test_ds, cfg, evaluator, sources, references
        )

        logger.info(
            f"seed={seed}  val BLEU={train_result['bleu']:.4f}  "
            f"test BLEU={test_metrics['bleu']:.4f}  "
            f"chrF={test_metrics['chrf']:.2f}  "
            f"TermR={test_metrics.get('term_recall', 0):.4f}  "
            f"TermP={test_metrics.get('term_precision', 0):.4f}  "
            f"TermF1={test_metrics.get('term_f1', 0):.4f}"
        )

        row = result_row(
            model_id, data_condition, seed, lora_config, train_result, test_metrics, train_data, val_data, sources
        )
        write_json(result_path, row)
        write_json(
            seed_dir / "test_predictions.json",
            [
                {"source": src, "prediction": pred, "reference": ref}
                for src, pred, ref in zip(sources, predictions, references)
            ],
            ensure_ascii=False,
        )
        return row

    except Exception as exc:
        error_text = f"seed={seed} failed: {exc}\n{traceback.format_exc()}"
        logger.error(error_text)
        with open(seed_dir / "error.txt", "w", encoding="utf-8") as f:
            f.write(error_text)
        return {
            "data_condition": data_condition,
            "model_id": model_id,
            "seed": seed,
            "failed": True,
            "test_bleu": 0.0,
            "test_chrf": 0.0,
            "test_fta": None,
            "test_term_recall": None,
            "test_term_precision": None,
            "test_term_f1": None,
        }

    finally:
        del trainer
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()


def save_summary(results, output_dir: Path, logger: logging.Logger):
    write_json(output_dir / "all_results.json", results)

    rows = [row for row in results if not row.get("failed")]
    failed = [row for row in results if row.get("failed")]
    if failed:
        failed_seeds = ", ".join(str(row.get("seed")) for row in failed)
        logger.warning(
            f"{len(failed)} seed(s) failed ({failed_seeds}). "
            "Do not use this run as a final paper result until rerun."
        )
    if not rows:
        logger.error("No successful runs.")
        return

    keys = sorted({key for row in results for key in row})
    with open(output_dir / "all_results.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in results:
            writer.writerow(
                {
                    key: json.dumps(row[key], ensure_ascii=False) if isinstance(row.get(key), (dict, list)) else row.get(key)
                    for key in keys
                }
            )

    bleu = [row.get("test_bleu") for row in rows if row.get("test_bleu") is not None]
    chrf = [row.get("test_chrf") for row in rows if row.get("test_chrf") is not None]
    term_recall = [row["test_term_recall"] for row in rows if row.get("test_term_recall") is not None]
    term_precision = [row["test_term_precision"] for row in rows if row.get("test_term_precision") is not None]
    term_f1 = [row["test_term_f1"] for row in rows if row.get("test_term_f1") is not None]

    if bleu:
        logger.info(f"Test BLEU: {statistics.mean(bleu):.4f} +/- {statistics.stdev(bleu) if len(bleu) > 1 else 0.0:.4f}")
    if chrf:
        logger.info(f"Test chrF: {statistics.mean(chrf):.2f} +/- {statistics.stdev(chrf) if len(chrf) > 1 else 0.0:.2f}")
    if term_recall:
        logger.info(
            f"Test term recall: {statistics.mean(term_recall):.4f} +/- "
            f"{statistics.stdev(term_recall) if len(term_recall) > 1 else 0.0:.4f}"
        )
    if term_precision:
        logger.info(
            f"Test term precision: {statistics.mean(term_precision):.4f} +/- "
            f"{statistics.stdev(term_precision) if len(term_precision) > 1 else 0.0:.4f}"
        )
    if term_f1:
        logger.info(
            f"Test term F1: {statistics.mean(term_f1):.4f} +/- "
            f"{statistics.stdev(term_f1) if len(term_f1) > 1 else 0.0:.4f}"
        )
    logger.info(f"Results saved to {output_dir}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", choices=["original", "bokmal", "original_subsampled"], required=True)
    parser.add_argument("--model-id", choices=sorted(MODELS), default="nllb_600m")
    args = parser.parse_args()

    cfg = apply_model_spec(load_config(args.data), args.model_id)
    prefix = output_prefix(args.model_id)
    output_dir = PROJECT_ROOT / cfg["paths"]["output_dir"] / f"{prefix}_train_{args.data}"
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = make_logger(output_dir)

    logger.info(f"Paper2 train: model_id={args.model_id} data={args.data}")
    logger.info(f"Base model: {cfg['model']['pretrained']}")
    r, alpha, dropout = load_lora_config(cfg, logger)
    lora_config = {"r": r, "alpha": alpha, "dropout": dropout}
    logger.info(f"LoRA config: {lora_config}")

    data = load_splits(cfg)
    logger.info(f"Train={len(data[0])}  Val={len(data[1])}  Test={len(data[3])}")

    evaluator = FTAEvaluator(str(GLOSSARY_PATH), src_lang="en", tgt_lang="no", use_comet=False)
    seeds = cfg.get("experiment", {}).get("seeds", [42, 123, 456])

    results = [
        train_seed(seed, args.model_id, args.data, cfg, lora_config, data, evaluator, output_dir, logger)
        for seed in seeds
    ]
    save_summary(results, output_dir, logger)


if __name__ == "__main__":
    main()
