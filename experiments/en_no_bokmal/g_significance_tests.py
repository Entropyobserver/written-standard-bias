import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

COMPARISONS = [
    ("bokmal", "original_subsampled", "bokmal"),
    ("bokmal", "original_subsampled", "original"),
    ("bokmal", "original", "bokmal"),
    ("bokmal", "original", "original"),
]

METRICS = ["sentence_chrf", "term_recall", "term_precision", "term_f1"]
SLIDE_CATEGORIES = ["nb_only", "nn_only"]


def read_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def read_config() -> dict:
    with open(PROJECT_ROOT / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def normalize_term(term: str) -> str:
    return " ".join(term.lower().split())


def load_term_pairs(path: Path) -> list[tuple[str, str]]:
    glossary = read_json(path)
    pairs = []

    if isinstance(glossary, list):
        for item in glossary:
            source_term = item.get("en")
            target_term = item.get("no")
            if source_term and target_term:
                pairs.append((normalize_term(source_term), normalize_term(target_term)))
        return pairs

    for source_term, translations in glossary.items():
        if isinstance(translations, str):
            target_term = translations
        else:
            target_term = translations.get("no", "")
        if source_term and target_term:
            pairs.append((normalize_term(source_term), normalize_term(target_term)))
    return pairs


def build_target_index(term_pairs: list[tuple[str, str]]) -> dict[str, list[str]]:
    target_to_sources = defaultdict(list)
    for source_term, target_term in term_pairs:
        target_to_sources[target_term].append(source_term)
    return dict(target_to_sources)


def prediction_path(output_root: Path, model: str, test: str, seed: int) -> Path:
    return output_root / f"p2_eval_model_{model}_test_{test}" / f"seed_{seed}" / "predictions.json"


def slide_path(output_root: Path, model: str, test: str, seed: int) -> Path:
    return output_root / "slide_analysis" / f"model_{model}_test_{test}" / f"seed_{seed}" / "slide_sentence_scores.json"


def check_alignment(rows_a: list[dict], rows_b: list[dict], label: str):
    if len(rows_a) != len(rows_b):
        raise ValueError(f"{label}: row count differs: {len(rows_a)} vs {len(rows_b)}")
    for i, (row_a, row_b) in enumerate(zip(rows_a, rows_b)):
        if row_a["source"] != row_b["source"] or row_a["reference"] != row_b["reference"]:
            raise ValueError(f"{label}: source/reference mismatch at row {i}")


def sentence_term_counts(row: dict, term_pairs: list[tuple[str, str]], target_to_sources: dict[str, list[str]]) -> dict:
    source_lower = row["source"].lower()
    prediction_lower = row["prediction"].lower()

    source_terms = [
        (source_term, target_term)
        for source_term, target_term in term_pairs
        if source_term in source_lower
    ]
    predicted_terms = [
        target_term
        for target_term in target_to_sources
        if target_term in prediction_lower
    ]
    hits = sum(1 for _, target_term in source_terms if target_term in prediction_lower)
    false_positives = sum(
        1
        for target_term in predicted_terms
        if not any(source_term in source_lower for source_term in target_to_sources[target_term])
    )
    return {
        "source_instances": len(source_terms),
        "prediction_instances": len(predicted_terms),
        "hits": hits,
        "false_positives": false_positives,
    }


def char_ngrams(text: str, order: int) -> list[str]:
    text = " ".join(text.lower().split())
    if len(text) < order:
        return []
    return [text[i : i + order] for i in range(len(text) - order + 1)]


def sentence_chrf(prediction: str, reference: str, max_order: int = 6, beta: float = 2.0) -> float:
    scores = []
    for order in range(1, max_order + 1):
        pred_ngrams = char_ngrams(prediction, order)
        ref_ngrams = char_ngrams(reference, order)
        if not pred_ngrams or not ref_ngrams:
            scores.append(0.0)
            continue

        pred_counts = defaultdict(int)
        ref_counts = defaultdict(int)
        for item in pred_ngrams:
            pred_counts[item] += 1
        for item in ref_ngrams:
            ref_counts[item] += 1

        overlap = sum(min(count, ref_counts.get(item, 0)) for item, count in pred_counts.items())
        precision = overlap / len(pred_ngrams)
        recall = overlap / len(ref_ngrams)
        if precision + recall == 0:
            scores.append(0.0)
            continue
        beta2 = beta * beta
        scores.append((1 + beta2) * precision * recall / (beta2 * precision + recall))
    return 100 * sum(scores) / len(scores)


def prepare_rows(rows: list[dict], term_pairs: list[tuple[str, str]], target_to_sources: dict[str, list[str]]) -> list[dict]:
    prepared = []
    for row in rows:
        item = dict(row)
        item["_term_counts"] = sentence_term_counts(row, term_pairs, target_to_sources)
        item["_sentence_chrf"] = sentence_chrf(row["prediction"], row["reference"])
        prepared.append(item)
    return prepared


def load_prepared_predictions(
    path: Path,
    term_pairs: list[tuple[str, str]],
    target_to_sources: dict[str, list[str]],
    cache: dict[str, list[dict]],
) -> list[dict]:
    key = str(path)
    if key not in cache:
        cache[key] = prepare_rows(read_json(path), term_pairs, target_to_sources)
    return cache[key]


def metric_arrays(rows: list[dict]) -> dict[str, np.ndarray]:
    return {
        "sentence_chrf": np.array([row["_sentence_chrf"] for row in rows], dtype=np.float64),
        "hits": np.array([row["_term_counts"]["hits"] for row in rows], dtype=np.float64),
        "source_instances": np.array(
            [row["_term_counts"]["source_instances"] for row in rows], dtype=np.float64
        ),
        "prediction_instances": np.array(
            [row["_term_counts"]["prediction_instances"] for row in rows], dtype=np.float64
        ),
        "false_positives": np.array(
            [row["_term_counts"]["false_positives"] for row in rows], dtype=np.float64
        ),
    }


def aggregate_arrays(arrays: dict[str, np.ndarray], indices: np.ndarray | None = None) -> dict[str, float]:
    if indices is None:
        sentence_chrf_score = float(arrays["sentence_chrf"].mean()) if len(arrays["sentence_chrf"]) else 0.0
        hits = float(arrays["hits"].sum())
        source_instances = float(arrays["source_instances"].sum())
        prediction_instances = float(arrays["prediction_instances"].sum())
        false_positives = float(arrays["false_positives"].sum())
    else:
        sentence_chrf_score = float(arrays["sentence_chrf"][indices].mean()) if len(indices) else 0.0
        hits = float(arrays["hits"][indices].sum())
        source_instances = float(arrays["source_instances"][indices].sum())
        prediction_instances = float(arrays["prediction_instances"][indices].sum())
        false_positives = float(arrays["false_positives"][indices].sum())

    term_recall = hits / source_instances if source_instances else 0.0
    true_predictions = prediction_instances - false_positives
    term_precision = true_predictions / prediction_instances if prediction_instances else 0.0
    term_f1 = (
        2 * term_precision * term_recall / (term_precision + term_recall)
        if term_precision + term_recall
        else 0.0
    )
    return {
        "sentence_chrf": sentence_chrf_score,
        "term_recall": term_recall,
        "term_precision": term_precision,
        "term_f1": term_f1,
    }


def bootstrap_test(rows_a: list[dict], rows_b: list[dict], n_bootstrap: int, rng: np.random.Generator) -> list[dict]:
    arrays_a = metric_arrays(rows_a)
    arrays_b = metric_arrays(rows_b)
    observed_a = aggregate_arrays(arrays_a)
    observed_b = aggregate_arrays(arrays_b)
    n = len(rows_a)

    deltas = {metric: [] for metric in METRICS}
    for _ in range(n_bootstrap):
        indices = rng.integers(0, n, size=n)
        metrics_a = aggregate_arrays(arrays_a, indices)
        metrics_b = aggregate_arrays(arrays_b, indices)

        for metric in METRICS:
            deltas[metric].append(metrics_a[metric] - metrics_b[metric])

    results = []
    for metric in METRICS:
        values = sorted(deltas[metric])
        observed_delta = observed_a[metric] - observed_b[metric]
        le_zero = sum(1 for value in values if value <= 0) / len(values)
        ge_zero = sum(1 for value in values if value >= 0) / len(values)
        p_value = min(1.0, 2 * min(le_zero, ge_zero))
        results.append(
            {
                "test_type": "paired_bootstrap",
                "metric": metric,
                "observed_a": observed_a[metric],
                "observed_b": observed_b[metric],
                "observed_delta": observed_delta,
                "bootstrap_mean_delta": sum(values) / len(values),
                "ci_low": percentile(values, 2.5),
                "ci_high": percentile(values, 97.5),
                "p_value_two_sided": p_value,
                "significant_05": p_value < 0.05,
                "n_units": n,
                "n_bootstrap": n_bootstrap,
            }
        )
    return results


def percentile(sorted_values: list[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    position = (len(sorted_values) - 1) * pct / 100
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[int(position)]
    fraction = position - lower
    return sorted_values[lower] * (1 - fraction) + sorted_values[upper] * fraction


def logsumexp(values: list[float]) -> float:
    max_value = max(values)
    return max_value + math.log(sum(math.exp(value - max_value) for value in values))


def exact_binomial_two_sided(k: int, n: int) -> float:
    if n == 0:
        return 1.0
    tail = min(k, n - k)
    log_probs = [
        math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1) - n * math.log(2)
        for i in range(tail + 1)
    ]
    return min(1.0, 2 * math.exp(logsumexp(log_probs)))


def mcnemar_test(labels_a: list[bool], labels_b: list[bool]) -> dict:
    a_yes_b_no = sum(1 for a, b in zip(labels_a, labels_b) if a and not b)
    a_no_b_yes = sum(1 for a, b in zip(labels_a, labels_b) if not a and b)
    discordant = a_yes_b_no + a_no_b_yes
    return {
        "a_yes_b_no": a_yes_b_no,
        "a_no_b_yes": a_no_b_yes,
        "discordant": discordant,
        "p_value_two_sided": exact_binomial_two_sided(min(a_yes_b_no, a_no_b_yes), discordant),
    }


def slide_category_rows(output_root: Path, model: str, test: str, seed: int, category: str) -> list[bool] | None:
    path = slide_path(output_root, model, test, seed)
    if not path.exists():
        return None
    rows = read_json(path)
    return [row.get("prediction_category") == category for row in rows]


def add_identity(row: dict, model_a: str, model_b: str, test: str, seed_label: str) -> dict:
    out = {
        "comparison": f"{model_a}_vs_{model_b}_on_{test}",
        "model_a": model_a,
        "model_b": model_b,
        "test": test,
        "seed": seed_label,
    }
    out.update(row)
    return out


def run_comparison(
    output_root: Path,
    term_pairs: list[tuple[str, str]],
    target_to_sources: dict[str, list[str]],
    model_a: str,
    model_b: str,
    test: str,
    seeds: list[int],
    n_bootstrap: int,
    rng: np.random.Generator,
    prepared_cache: dict[str, list[dict]],
) -> list[dict]:
    results = []
    pooled_a = []
    pooled_b = []

    for seed in seeds:
        path_a = prediction_path(output_root, model_a, test, seed)
        path_b = prediction_path(output_root, model_b, test, seed)
        if not path_a.exists() or not path_b.exists():
            print(f"Missing predictions for {model_a} vs {model_b} on {test}, seed={seed}")
            continue

        rows_a = load_prepared_predictions(path_a, term_pairs, target_to_sources, prepared_cache)
        rows_b = load_prepared_predictions(path_b, term_pairs, target_to_sources, prepared_cache)
        check_alignment(rows_a, rows_b, f"{model_a} vs {model_b} on {test}, seed={seed}")

        pooled_a.extend(rows_a)
        pooled_b.extend(rows_b)

        for row in bootstrap_test(rows_a, rows_b, n_bootstrap, rng):
            results.append(add_identity(row, model_a, model_b, test, str(seed)))

        for category in SLIDE_CATEGORIES:
            labels_a = slide_category_rows(output_root, model_a, test, seed, category)
            labels_b = slide_category_rows(output_root, model_b, test, seed, category)
            if labels_a is None or labels_b is None:
                continue
            mcnemar = mcnemar_test(labels_a, labels_b)
            rate_a = sum(labels_a) / len(labels_a) if labels_a else 0.0
            rate_b = sum(labels_b) / len(labels_b) if labels_b else 0.0
            row = {
                "test_type": "mcnemar",
                "metric": f"slide_{category}",
                "observed_a": rate_a,
                "observed_b": rate_b,
                "observed_delta": rate_a - rate_b,
                "p_value_two_sided": mcnemar["p_value_two_sided"],
                "significant_05": mcnemar["p_value_two_sided"] < 0.05,
                "n_units": len(labels_a),
                **mcnemar,
            }
            results.append(add_identity(row, model_a, model_b, test, str(seed)))

    if pooled_a:
        for row in bootstrap_test(pooled_a, pooled_b, n_bootstrap, rng):
            results.append(add_identity(row, model_a, model_b, test, "pooled"))

    return results


def write_csv(path: Path, rows: list[dict]):
    fieldnames = sorted({key for row in rows for key in row})
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def format_p(value) -> str:
    if value is None:
        return ""
    if value < 0.001:
        return "<0.001"
    return f"{value:.3f}"


def write_markdown(path: Path, rows: list[dict]):
    pooled = [row for row in rows if row.get("seed") == "pooled"]
    groups = {}
    for row in pooled:
        groups.setdefault(row["comparison"], []).append(row)

    lines = ["# Significance Tests", ""]
    for comparison, group_rows in groups.items():
        lines.append(f"## {comparison}")
        lines.append("")
        lines.append("| Test | Metric | Delta | 95% CI | p |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for row in group_rows:
            if row["test_type"] != "paired_bootstrap":
                continue
            lines.append(
                "| paired bootstrap | "
                f"{row['metric']} | "
                f"{row['observed_delta']:+.4f} | "
                f"[{row['ci_low']:+.4f}, {row['ci_high']:+.4f}] | "
                f"{format_p(row['p_value_two_sided'])} |"
            )
        lines.append("")

    mcnemar_rows = [row for row in rows if row["test_type"] == "mcnemar"]
    if mcnemar_rows:
        lines.append("## McNemar SLIDE Tests")
        lines.append("")
        lines.append("| Comparison | Seed | Metric | A rate | B rate | Delta | p |")
        lines.append("| --- | --- | --- | ---: | ---: | ---: | ---: |")
        for row in mcnemar_rows:
            lines.append(
                f"| {row['comparison']} | {row['seed']} | {row['metric']} | "
                f"{row['observed_a']:.4f} | {row['observed_b']:.4f} | "
                f"{row['observed_delta']:+.4f} | {format_p(row['p_value_two_sided'])} |"
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=13)
    args = parser.parse_args()

    cfg = read_config()
    seeds = cfg.get("experiment", {}).get("seeds", [42, 123, 456])
    output_root = PROJECT_ROOT / cfg["paths"]["output_dir"]
    analysis_dir = output_root / "p2_analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    term_pairs = load_term_pairs(PROJECT_ROOT / "data/term/npd_glossary_cleaned.json")
    target_to_sources = build_target_index(term_pairs)
    rng = np.random.default_rng(args.seed)
    prepared_cache = {}

    results = []
    for model_a, model_b, test in COMPARISONS:
        print(f"Testing {model_a} vs {model_b} on {test}")
        results.extend(
            run_comparison(
                output_root=output_root,
                term_pairs=term_pairs,
                target_to_sources=target_to_sources,
                model_a=model_a,
                model_b=model_b,
                test=test,
                seeds=seeds,
                n_bootstrap=args.n_bootstrap,
                rng=rng,
                prepared_cache=prepared_cache,
            )
        )

    json_path = analysis_dir / "significance_tests.json"
    csv_path = analysis_dir / "significance_tests.csv"
    md_path = analysis_dir / "significance_tests.md"
    write_json(json_path, results)
    write_csv(csv_path, results)
    write_markdown(md_path, results)

    print(f"written: {json_path}")
    print(f"written: {csv_path}")
    print(f"written: {md_path}")


if __name__ == "__main__":
    main()
