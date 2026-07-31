# English--Norwegian Bokmal Filtering Experiment: File Inventory and Pipeline Notes

This report documents the experiment folder `experiments/en_no_bokmal/` for the
Norwegian MT target-standard bias paper. It records what each script does, its
main inputs and outputs, and how the files connect to the paper evidence chain.

The experiment studies whether target-side Bokmal filtering changes English--
Norwegian petroleum-domain MT behavior and evaluation outcomes. The core
comparison is:

- `original`: LoRA fine-tuning on the full mixed-standard petroleum corpus.
- `bokmal`: LoRA fine-tuning on the SLIDE-filtered Bokmal subset.
- `original_subsampled`: LoRA fine-tuning on a size-matched random subset of the
  original corpus.
- `base`: zero-shot NLLB, no fine-tuning.

The current paper uses these evidence layers:

- Automatic MT metrics: BLEU, chrF, TermR, TermP, TermF1.
- Written-standard analysis: SLIDE categories and NB--NN margins.
- Model-scale robustness: NLLB-200 600M, 1.3B, and 3.3B.
- Out-of-domain evaluation: FLORES NB and FLORES NN.
- Significance tests: paired bootstrap for sentence-level chrF and terminology
  metrics; exact McNemar tests for SLIDE NB-only/NN-only labels.
- Human evaluation: diagnostic adequacy and Bokmal-conformity sample.
- SLIDE validation: stratified manual check of SLIDE labels on petroleum-domain
  sentences.

## Directory Map

### Main Code

`experiments/en_no_bokmal/`

This is the main experiment pipeline. The filename prefixes encode the rough
execution order:

| Prefix | Stage | Main role |
| --- | --- | --- |
| `a_*` | Data preparation and data diagnostics | SLIDE training-distribution analysis, original-subsampled split, FLORES data |
| `b_*` | Training | LoRA fine-tuning for 600M/1.3B/3.3B NLLB conditions |
| `c_*` | Evaluation | Generate predictions and compute BLEU/chrF/terminology metrics |
| `d_*` | Summaries | Aggregate result tables and model-scale result files |
| `e_*` | SLIDE analysis | Written-standard analysis for 600M predictions and references |
| `f_*` | Examples | Select qualitative paper examples |
| `g_*` | Significance | Paired bootstrap and McNemar tests |
| `h_*` | Human eval sheet | Create blinded human-evaluation sheet |
| `i_*` | Human eval analysis | Analyze filled human-evaluation sheets |
| `j_*` | SLIDE validation sheet | Create blinded SLIDE-validation sheet |
| `k_*` | SLIDE validation analysis | Analyze filled SLIDE-validation sheet |
| `l_*` | Threshold sensitivity | Check retained data size under nearby SLIDE thresholds |
| `n_*` | Model-scale SLIDE | Written-standard analysis across 600M/1.3B/3.3B |

### Main Data

| Path | Content | Used by |
| --- | --- | --- |
| `data/final_splits_npd/` | Original mixed-standard petroleum train/val/test splits (`.json`, `.tsv`) | `b_train.py`, `c_evaluate.py`, `a_make_original_subsampled.py` |
| `data/final_splits_npd_bokmal/` | SLIDE-filtered Bokmal train/val/test splits (`.jsonl`) | `b_train.py`, `c_evaluate.py`, threshold and training diagnostics |
| `data/final_splits_npd_original_subsampled/` | Size-matched random subset of original data | `b_train.py`, `c_evaluate.py` |
| `data/flores_ood/flores_nob/devtest.json` | FLORES English-to-Bokmal evaluation set | `c_evaluate.py` |
| `data/flores_ood/flores_nno/devtest.json` | FLORES English-to-Nynorsk evaluation set | `c_evaluate.py` |
| `data/term/npd_glossary_cleaned.json` | Cleaned petroleum glossary, English to Norwegian term pairs | `b_train.py`, `c_evaluate.py`, `g_significance_tests.py` |

### Main Outputs

| Path | Content |
| --- | --- |
| `outputs/p2_train_*` | 600M fine-tuning outputs and per-seed training artifacts |
| `outputs/p2_eval_model_*_test_*` | 600M evaluation metrics and predictions |
| `outputs/p2_robust_nllb_1_3b_*` | 1.3B training/evaluation outputs |
| `outputs/p2_robust_nllb_3_3b_*` | 3.3B training/evaluation outputs |
| `outputs/p2_analysis/` | Aggregated metric tables, model-scale summaries, significance tests, plots |
| `outputs/slide_analysis/` | SLIDE written-standard analysis for 600M outputs |
| `outputs/slide_analysis_model_scale_key/` | Key model-scale SLIDE analysis for original-subsampled vs Bokmal |
| `outputs/slide_training_distribution/` | SLIDE distribution and threshold sensitivity for training data |
| `outputs/human_eval/` | Human-evaluation sheets, keys, and summaries |
| `outputs/slide_validation/` | SLIDE validation sheets, keys, review files, and summaries |
| `outputs/paper_examples/` | Qualitative examples selected for paper inspection |

## Configuration Files

### `config.yaml`

Main configuration for the original-data condition and default 600M NLLB model.

Main fields:

- Model: `facebook/nllb-200-distilled-600M`
- Source/target codes: `eng_Latn` to `nob_Latn`
- Max length: 128
- Training: 3 epochs, batch size 4, gradient accumulation 4, learning rate
  `5e-4`, warmup 100, eval/checkpoint every 200 steps, early stopping patience 3
- Generation: beam size 5, max length 128
- Data: `data/final_splits_npd/{train,val,test}.json`
- Seeds: 42, 123, 456

Note: the current paper reports LoRA rank/alpha/dropout as `8/64/0.0`, while the
base YAML still contains `16/32/0.1`. The training script loads
`outputs/exp3_optuna_stage2/best_config.json` when available, so the YAML is not
the only source of the final LoRA hyperparameters. Do not infer final paper
hyperparameters from the YAML alone.

### `experiments/en_no_bokmal/config_bokmal.yaml`

Same general training settings as `config.yaml`, but data paths point to:

- `data/final_splits_npd_bokmal/train.jsonl`
- `data/final_splits_npd_bokmal/val.jsonl`
- `data/final_splits_npd_bokmal/test.jsonl`

### `experiments/en_no_bokmal/config_original_subsampled.yaml`

Same general training settings as `config.yaml`, but data paths point to:

- `data/final_splits_npd_original_subsampled/train.json`
- `data/final_splits_npd_original_subsampled/val.json`
- `data/final_splits_npd_original_subsampled/test.json`

### `experiments/en_no_bokmal/model_registry.py`

Central registry for NLLB model scales and output prefixes:

| `model_id` | Hugging Face model | Output prefix |
| --- | --- | --- |
| `nllb_600m` | `facebook/nllb-200-distilled-600M` | `p2` |
| `nllb_1_3b` | `facebook/nllb-200-1.3B` | `p2_robust_nllb_1_3b` |
| `nllb_3_3b` | `facebook/nllb-200-3.3B` | `p2_robust_nllb_3_3b` |

Used by `b_train.py`, `c_evaluate.py`, `d_summarize_model_scale.py`, and
`n_analyze_slide_model_scale.py`.

## Python Scripts

### `a_analyze_training_slide_distribution.py`

Purpose:

- Scores the original training targets with SLIDE.
- Compares the original training set with the already-filtered Bokmal training
  split.
- Produces data-selection diagnostics for the paper.

Main inputs:

- `data/final_splits_npd/train.json`
- `data/final_splits_npd_bokmal/train.jsonl`
- SLIDE model, default `ltg/SLIDE-base`

Main outputs:

- `outputs/slide_training_distribution/manifest.json`
- `outputs/slide_training_distribution/original_train_slide_scores.json`
- `outputs/slide_training_distribution/training_slide_distribution.csv`

Important options:

- `--original-train`
- `--bokmal-train`
- `--output-dir`
- `--slide-model`
- `--batch-size`
- `--device`

Notes:

- The script caches SLIDE scores in `original_train_slide_scores.json`.
- This is a diagnostic script, not a filtering script; the filtered Bokmal split
  already exists in `data/final_splits_npd_bokmal/`.

### `a_make_original_subsampled.py`

Purpose:

- Creates the size-matched `original_subsampled` train/validation/test splits.
- This is the key control for separating data-size effects from Bokmal filtering
  effects.

Main inputs:

- `data/final_splits_npd/train.json`
- `data/final_splits_npd/val.json`
- `data/final_splits_npd/test.json`

Main outputs:

- `data/final_splits_npd_original_subsampled/train.json`
- `data/final_splits_npd_original_subsampled/val.json`
- `data/final_splits_npd_original_subsampled/test.json`
- `data/final_splits_npd_original_subsampled/manifest.json`

Target sizes:

- Train: 10,114
- Validation: 1,305
- Test: 1,313

Notes:

- Sampling is deterministic through a fixed random seed.
- This split is used as the size-controlled baseline in the paper.

### `a_prepare_flores_ood.py`

Purpose:

- Downloads/prepares FLORES-200 dev or devtest data for out-of-domain
  evaluation.

Main input:

- Hugging Face dataset `Muennighoff/flores200`

Main outputs:

- `data/flores_ood/flores_nob/devtest.json`
- `data/flores_ood/flores_nno/devtest.json`
- `data/flores_ood/manifest.json`

Important option:

- `--split`, default `devtest`, choices `dev` or `devtest`

Notes:

- FLORES NB uses `eng_Latn -> nob_Latn`.
- FLORES NN uses `eng_Latn -> nno_Latn`.
- All evaluated systems decode with `nob_Latn`; FLORES NN is therefore used as a
  written-standard mismatch test, not as a direct Nynorsk-generation test.

### `b_train.py`

Purpose:

- Fine-tunes NLLB models with LoRA for one data condition and one model scale.

Main inputs:

- A condition-specific config:
  - `config.yaml` for `original`
  - `experiments/en_no_bokmal/config_bokmal.yaml` for `bokmal`
  - `experiments/en_no_bokmal/config_original_subsampled.yaml` for
    `original_subsampled`
- Optional best LoRA config:
  - `outputs/exp3_optuna_stage2/best_config.json`
- Training/validation/test data from the selected config
- Glossary: `data/term/npd_glossary_cleaned.json`

Main outputs:

- `outputs/{prefix}_train_{condition}/all_results.json`
- `outputs/{prefix}_train_{condition}/seed_{seed}/result.json`
- `outputs/{prefix}_train_{condition}/seed_{seed}/test_predictions.json`
- Per-seed training/checkpoint/final-model directories under the same output
  tree

Important options:

- `--data`, required; choices `original`, `bokmal`, `original_subsampled`
- `--model-id`, default `nllb_600m`; choices from `model_registry.py`

Output prefixes:

- 600M: `outputs/p2_train_*`
- 1.3B: `outputs/p2_robust_nllb_1_3b_train_*`
- 3.3B: `outputs/p2_robust_nllb_3_3b_train_*`

Notes:

- Trains all configured seeds, currently 42, 123, 456.
- Saves metrics and predictions for the condition's own test split.
- The evaluation paper tables are based primarily on the separate
  `c_evaluate.py` outputs, not only the training-time test outputs.

### `c_evaluate.py`

Purpose:

- Evaluates base or fine-tuned systems on a chosen test set.
- Generates predictions and computes BLEU, chrF, and glossary terminology
  metrics.

Main inputs:

- Model condition:
  - `base`
  - `original`
  - `bokmal`
  - `original_subsampled`
- Test set:
  - `original`
  - `bokmal`
  - `original_subsampled`
  - `flores_nob`
  - `flores_nno`
- Fine-tuned LoRA adapters from the corresponding training output directory
  when the model is not `base`
- Glossary: `data/term/npd_glossary_cleaned.json`

Main outputs:

- `outputs/{prefix}_eval_model_{model}_test_{test}/seed_{seed}/metrics.json`
- `outputs/{prefix}_eval_model_{model}_test_{test}/seed_{seed}/predictions.json`
- `outputs/{prefix}_eval_model_{model}_test_{test}/summary.json`

Important options:

- `--model`, required; choices `base`, `original`, `bokmal`,
  `original_subsampled`
- `--model-id`, default `nllb_600m`
- `--test`, required; choices `original`, `bokmal`, `original_subsampled`,
  `flores_nob`, `flores_nno`

Notes:

- For `base`, only seed 0 is used.
- For fine-tuned conditions, the script evaluates seeds 42, 123, and 456.
- This is the source of the paper's main metric tables.

### `c_recompute_metrics_from_predictions.py`

Purpose:

- Recomputes metrics from already saved `predictions.json` files.
- Useful when metric definitions changed after generation, without rerunning
  model inference.

Main inputs:

- One existing evaluation directory, or all matching `p2_eval_model_*_test_*`
  directories.
- `predictions.json` files under seed directories.
- Glossary: `data/term/npd_glossary_cleaned.json`

Main outputs:

- Updated per-seed `metrics.json`
- Updated evaluation-directory `summary.json`

Important options:

- `--eval-dir`
- `--all`

Notes:

- This is a metric repair/recomputation utility.
- It does not regenerate predictions.

### `d_summarize_results.py`

Purpose:

- Aggregates the main 600M evaluation summaries into analysis files and plots.

Main inputs:

- `outputs/p2_eval_model_*_test_*/summary.json`

Main outputs:

- `outputs/p2_analysis/comparison_table.csv`
- `outputs/p2_analysis/bleu_comparison.png`
- `outputs/p2_analysis/term_recall_comparison.png`
- `outputs/p2_analysis/term_precision_comparison.png`
- `outputs/p2_analysis/term_f1_comparison.png`

Notes:

- This script summarizes the 600M diagnostic matrix.
- The PNG plots are secondary artifacts; the paper currently keeps most exact
  metric values in tables.

### `d_summarize_model_scale.py`

Purpose:

- Aggregates size-controlled metric results across NLLB model sizes.
- Produces the model-scale robustness table inputs.

Main inputs:

- `outputs/{prefix}_eval_model_{condition}_test_{test}/summary.json`
- Model prefixes from `model_registry.py`

Main outputs:

- `outputs/p2_analysis/model_scale_results.csv`
- `outputs/p2_analysis/model_scale_deltas.csv`
- `outputs/p2_analysis/model_scale_results.json`

Notes:

- Covers 600M, 1.3B, and 3.3B.
- Focuses on in-domain `original` and `bokmal` test sets.

### `e_analyze_slide_outputs.py`

Purpose:

- Applies SLIDE to saved 600M predictions and references.
- Produces written-standard categories and NB--NN margins.

Main inputs:

- `outputs/p2_eval_model_{model}_test_{test}/seed_{seed}/predictions.json`
- SLIDE model, default `ltg/SLIDE-base`

Default model/test coverage:

- Models: `original`, `original_subsampled`, `bokmal`
- Tests: `original`, `bokmal`, `flores_nob`, `flores_nno`
- Seeds: 42, 123, 456
- Fields: `prediction`, `reference`

Main outputs:

- Per seed:
  - `outputs/slide_analysis/model_{model}_test_{test}/seed_{seed}/slide_sentence_scores.json`
- Aggregate:
  - `outputs/slide_analysis/summary.json`
  - `outputs/slide_analysis/summary.csv`
  - `outputs/slide_analysis/missing_predictions.json`, if needed

Important options:

- `--slide-model`
- `--models`
- `--tests`
- `--seeds`
- `--fields`
- `--threshold`, default 0.5
- `--batch-size`
- `--device`
- `--output-dir`

Notes:

- SLIDE categories are derived with threshold 0.5:
  - `nb_only`
  - `nn_only`
  - `nb_nn_mixed`
  - `no_nb_nn`
- This script is a major source for the paper's written-standard tables.

### `f_select_qualitative_examples.py`

Purpose:

- Selects example sentence pairs for qualitative inspection and paper examples.

Main inputs:

- `outputs/p2_eval_model_original_subsampled_test_original/seed_42/predictions.json`
- `outputs/p2_eval_model_bokmal_test_original/seed_42/predictions.json`
- `outputs/slide_analysis/model_original_subsampled_test_original/seed_42/slide_sentence_scores.json`
- `outputs/slide_analysis/model_bokmal_test_original/seed_42/slide_sentence_scores.json`

Main outputs:

- Files under `outputs/paper_examples/`
  - JSON examples
  - Table-ready text output

Notes:

- Focuses on original-test cases where the written-standard behavior differs
  between original-subsampled and Bokmal-filtered models.
- Selected examples still need manual inspection before being used in the final
  paper, especially because old local outputs may contain mojibake.

### `g_significance_tests.py`

Purpose:

- Runs statistical tests for the 600M diagnostic matrix.

Main inputs:

- Prediction files:
  - `outputs/p2_eval_model_{model}_test_{test}/seed_{seed}/predictions.json`
- SLIDE sentence scores:
  - `outputs/slide_analysis/model_{model}_test_{test}/seed_{seed}/slide_sentence_scores.json`
- Glossary:
  - `data/term/npd_glossary_cleaned.json`

Main comparisons:

- `bokmal` vs `original_subsampled` on `bokmal`
- `bokmal` vs `original_subsampled` on `original`
- `bokmal` vs `original` on `bokmal`
- `bokmal` vs `original` on `original`

Tests:

- Paired bootstrap over sentence indices for:
  - sentence-level chrF
  - TermR
  - TermP
  - TermF1
- Exact McNemar tests for:
  - `slide_nb_only`
  - `slide_nn_only`

Main outputs:

- `outputs/p2_analysis/significance_tests.json`
- `outputs/p2_analysis/significance_tests.csv`
- `outputs/p2_analysis/significance_tests.md`

Important options:

- `--n-bootstrap`, default 1000
- `--seed`, default 13

Notes:

- The paper should describe this as 1,000 bootstrap resamples, not
  "1,000 samples".
- BLEU is reported as a corpus-level descriptive score and is not bootstrapped.

### `h_make_human_eval_sheet.py`

Purpose:

- Creates a blinded human-evaluation sheet for diagnostic evaluation of adequacy
  and Bokmal conformity.

Main inputs:

- `outputs/p2_eval_model_original_subsampled_test_original/seed_{seed}/predictions.json`
- `outputs/p2_eval_model_bokmal_test_original/seed_{seed}/predictions.json`
- Corresponding SLIDE outputs under `outputs/slide_analysis/`

Main outputs:

- `outputs/human_eval/human_eval_sheet.csv`
- `outputs/human_eval/human_eval_key.csv`
- `outputs/human_eval/instructions.md`
- `outputs/human_eval/manifest.json`

Important options:

- `--seed`, default 42
- `--n-shift`, default 20
- `--n-control`, default 20
- `--random-seed`, default 2026
- `--max-chars`, default 360
- `--out-dir`

Notes:

- The sample is diagnostic, not distribution-estimating.
- Shift cases are intentionally enriched.
- This is why the paper must not present human preference counts as
  corpus-level rates.

### `i_analyze_human_eval.py`

Purpose:

- Analyzes filled human-evaluation sheets.

Main inputs:

- Filled annotations, default:
  - `outputs/human_eval/human_eval_sheet_filled.csv`
- Hidden key:
  - `outputs/human_eval/human_eval_key.csv`

Main outputs:

- `outputs/human_eval/human_eval_summary.json`
- `outputs/human_eval/human_eval_summary.md`

Important options:

- `--annotations`
- `--key`
- `--out-dir`

Notes:

- The current paper uses combined filled sheets under
  `outputs/human_eval/analysis_sheet2_sheet3_combined/`.
- The paper reports this as a diagnostic sample with 80 annotator-item
  decisions.

### `j_make_slide_validation_sheet.py`

Purpose:

- Creates a blinded manual-validation sheet for checking SLIDE labels on
  petroleum-domain sentences.

Candidate pools:

- Original references from `original_subsampled` on original test, seed 42
- Bokmal references from `original_subsampled` on Bokmal test, seed 42
- Original-subsampled predictions on original test, seed 42
- Bokmal predictions on original test, seed 42

Main inputs:

- `outputs/slide_analysis/model_{model}_test_{test}/seed_{seed}/slide_sentence_scores.json`

Main outputs:

- `outputs/slide_validation/slide_validation_sheet.csv`
- `outputs/slide_validation/slide_validation_key.csv`
- `outputs/slide_validation/instructions.md`
- `outputs/slide_validation/manifest.json`

Important options:

- `--n-per-label`, default 30
- `--random-seed`, default 2026
- `--out-dir`

Notes:

- Samples 30 items per SLIDE label:
  - `nb_only`
  - `nn_only`
  - `mixed`
  - `uncertain`
- Total sample size is 120.
- This is stratified by SLIDE label and must not be interpreted as corpus
  prevalence.
- In the actual selected sample, the final 120 items came from:
  - `original_reference`: 51
  - `original_subsampled_prediction`: 52
  - `bokmal_prediction`: 17
  - `bokmal_reference`: 0
  This is acceptable for the paper wording "drawn from references and model
  predictions", but the report should not claim all candidate pools are equally
  represented.

### `k_analyze_slide_validation.py`

Purpose:

- Analyzes manually filled SLIDE-validation labels against hidden SLIDE labels.

Main inputs:

- Filled annotation CSV, default:
  - `outputs/slide_validation/slide_validation_sheet_filled.csv`
- Hidden key:
  - `outputs/slide_validation/slide_validation_key.csv`

Main outputs:

- `slide_validation_summary.json`
- `slide_validation_summary.md`

Important options:

- `--annotations`
- `--key`
- `--out-dir`

Current paper-relevant run:

```bash
python experiments/en_no_bokmal/k_analyze_slide_validation.py \
  --annotations outputs/slide_validation/slide_validation_sheet_review2.csv \
  --key outputs/slide_validation/slide_validation_key.csv \
  --out-dir outputs/slide_validation/review2_analysis
```

Current review2 results:

- Annotated items: 120
- Exact agreement: 0.600
- Four-class macro-F1: 0.549
- Cohen's kappa: 0.467
- SLIDE NB-only precision: 0.967
- SLIDE NN-only recall: 1.000
- SLIDE NN-only precision: 0.633
- Mixed F1: 0.000

Important audit note:

- Earlier summaries reported macro-F1 0.732 because the script skipped the
  `mixed` class when its F1 was zero. This has been corrected. Standard
  four-class macro-F1 is 0.549 for `review2_analysis`.
- The `review_analysis` file is derived from the draft-label path and should not
  be treated as a fully independent human validation. The current paper should
  use `review2_analysis`, which is more conservative.

### `l_filter_threshold_sensitivity.py`

Purpose:

- Checks how many training examples would be retained under nearby SLIDE
  filtering thresholds.

Main input:

- `outputs/slide_training_distribution/original_train_slide_scores.json`

Main outputs:

- `outputs/slide_training_distribution/filter_threshold_sensitivity.csv`
- `outputs/slide_training_distribution/filter_threshold_sensitivity.md`

Threshold grid:

- NB thresholds: 0.6, 0.7, 0.8, 0.9
- NN exclusion thresholds: 0.1, 0.2, 0.3, 0.4

Notes:

- This is a data-selection sensitivity check only.
- It does not retrain MT models under different thresholds.
- Current range: 9,925 to 10,212 retained training sentences, or 71.2--73.3%
  of the original training split.

### `n_analyze_slide_model_scale.py`

Purpose:

- Applies SLIDE to predictions/references across model scales.
- Supports the paper claim that written-standard shift persists across 600M,
  1.3B, and 3.3B backbones.

Main inputs:

- Prediction files:
  - `outputs/{prefix}_eval_model_{condition}_test_{test}/seed_{seed}/predictions.json`
- Model prefixes from `model_registry.py`
- SLIDE model, default `ltg/SLIDE-base`

Defaults:

- Model IDs: all registered models
- Conditions: `original`, `original_subsampled`, `bokmal`
- Tests: `original`, `bokmal`
- Seeds: 42, 123, 456
- Fields: `prediction`, `reference`
- Threshold: 0.5

Main outputs:

- Per seed:
  - `{output_dir}/{model_id}_{condition}_{test}/seed_{seed}/slide_sentence_scores.json`
- Aggregate:
  - `{output_dir}/summary_by_seed.csv`
  - `{output_dir}/summary_by_model.csv`
  - `{output_dir}/summary.json`
  - `{output_dir}/missing_predictions.json`, if needed

Current key run:

```bash
python experiments/en_no_bokmal/n_analyze_slide_model_scale.py \
  --conditions original_subsampled bokmal \
  --fields prediction \
  --output-dir outputs/slide_analysis_model_scale_key
```

Current key outputs:

- `outputs/slide_analysis_model_scale_key/summary_by_seed.csv`
- `outputs/slide_analysis_model_scale_key/summary_by_model.csv`
- `outputs/slide_analysis_model_scale_key/summary.json`

Notes:

- This script does not retrain or regenerate translations.
- It reads existing prediction files and runs SLIDE on them.

## SLURM Shell Scripts

The `.sh` files are wrappers for the Python scripts, mainly for UPPMAX/Pelle GPU
jobs. They write logs under `experiments/en_no_bokmal/logs/`.

### Training Wrappers

| Script | Command | Purpose |
| --- | --- | --- |
| `b_train_original.sh` | `python .../b_train.py --data original` | Train 600M on original data |
| `b_train_bokmal.sh` | `python .../b_train.py --data bokmal` | Train 600M on Bokmal-filtered data |
| `b_train_original_subsampled.sh` | `python .../b_train.py --data original_subsampled` | Train 600M on size-matched original subset |
| `b_train_nllb_1_3b_original.sh` | `--data original --model-id nllb_1_3b` | Train 1.3B original |
| `b_train_nllb_1_3b_bokmal.sh` | `--data bokmal --model-id nllb_1_3b` | Train 1.3B Bokmal |
| `b_train_nllb_1_3b_original_subsampled.sh` | `--data original_subsampled --model-id nllb_1_3b` | Train 1.3B original-subsampled |
| `b_train_nllb_3_3b_original.sh` | `--data original --model-id nllb_3_3b` | Train 3.3B original |
| `b_train_nllb_3_3b_bokmal.sh` | `--data bokmal --model-id nllb_3_3b` | Train 3.3B Bokmal |
| `b_train_nllb_3_3b_original_subsampled.sh` | `--data original_subsampled --model-id nllb_3_3b` | Train 3.3B original-subsampled |

### Evaluation Wrappers

| Script | Command pattern | Purpose |
| --- | --- | --- |
| `c_evaluate_base_all.sh` | `c_evaluate.py --model base --test "$TEST"` | Evaluate zero-shot 600M base on all configured tests |
| `c_evaluate_original_on_original.sh` | `--model original --test original` | Evaluate 600M original on original test |
| `c_evaluate_original_on_bokmal.sh` | `--model original --test bokmal` | Evaluate 600M original on Bokmal test |
| `c_evaluate_bokmal_on_original.sh` | `--model bokmal --test original` | Evaluate 600M Bokmal-filtered on original test |
| `c_evaluate_bokmal_on_bokmal.sh` | `--model bokmal --test bokmal` | Evaluate 600M Bokmal-filtered on Bokmal test |
| `c_evaluate_original_subsampled_on_original.sh` | `--model original_subsampled --test original` | Evaluate 600M size-control on original test |
| `c_evaluate_original_subsampled_on_bokmal.sh` | `--model original_subsampled --test bokmal` | Evaluate 600M size-control on Bokmal test |
| `c_evaluate_flores_ood.sh` | loops over `MODEL` and `TEST` | Evaluate fine-tuned 600M systems on FLORES NB/NN |
| `c_evaluate_nllb_1_3b_original.sh` | `--model original --model-id nllb_1_3b` on original and Bokmal tests | Evaluate 1.3B original |
| `c_evaluate_nllb_1_3b_bokmal.sh` | `--model bokmal --model-id nllb_1_3b` on original and Bokmal tests | Evaluate 1.3B Bokmal |
| `c_evaluate_nllb_1_3b_original_subsampled.sh` | `--model original_subsampled --model-id nllb_1_3b` on original and Bokmal tests | Evaluate 1.3B size-control |
| `c_evaluate_nllb_3_3b_original.sh` | `--model original --model-id nllb_3_3b` on original and Bokmal tests | Evaluate 3.3B original |
| `c_evaluate_nllb_3_3b_bokmal.sh` | `--model bokmal --model-id nllb_3_3b` on original and Bokmal tests | Evaluate 3.3B Bokmal |
| `c_evaluate_nllb_3_3b_original_subsampled.sh` | `--model original_subsampled --model-id nllb_3_3b` on original and Bokmal tests | Evaluate 3.3B size-control |

### SLIDE Analysis Wrappers

| Script | Command | Purpose |
| --- | --- | --- |
| `e_analyze_slide_outputs.sh` | `python .../e_analyze_slide_outputs.py` | Run 600M SLIDE analysis over default models/tests/seeds |
| `n_analyze_slide_model_scale.sh` | `python .../n_analyze_slide_model_scale.py` | Run model-scale SLIDE analysis over default models/conditions/tests |

## Recommended Reproduction Order

The expected full pipeline is:

```bash
python experiments/en_no_bokmal/a_analyze_training_slide_distribution.py
python experiments/en_no_bokmal/a_make_original_subsampled.py
python experiments/en_no_bokmal/a_prepare_flores_ood.py

sbatch experiments/en_no_bokmal/b_train_original.sh
sbatch experiments/en_no_bokmal/b_train_bokmal.sh
sbatch experiments/en_no_bokmal/b_train_original_subsampled.sh

sbatch experiments/en_no_bokmal/c_evaluate_base_all.sh
sbatch experiments/en_no_bokmal/c_evaluate_original_on_original.sh
sbatch experiments/en_no_bokmal/c_evaluate_original_on_bokmal.sh
sbatch experiments/en_no_bokmal/c_evaluate_bokmal_on_original.sh
sbatch experiments/en_no_bokmal/c_evaluate_bokmal_on_bokmal.sh
sbatch experiments/en_no_bokmal/c_evaluate_original_subsampled_on_original.sh
sbatch experiments/en_no_bokmal/c_evaluate_original_subsampled_on_bokmal.sh
sbatch experiments/en_no_bokmal/c_evaluate_flores_ood.sh

python experiments/en_no_bokmal/c_recompute_metrics_from_predictions.py --all
python experiments/en_no_bokmal/d_summarize_results.py
python experiments/en_no_bokmal/d_summarize_model_scale.py

sbatch experiments/en_no_bokmal/e_analyze_slide_outputs.sh
python experiments/en_no_bokmal/f_select_qualitative_examples.py
python experiments/en_no_bokmal/g_significance_tests.py --n-bootstrap 1000

python experiments/en_no_bokmal/h_make_human_eval_sheet.py --n-shift 20 --n-control 20
# after annotation:
python experiments/en_no_bokmal/i_analyze_human_eval.py

python experiments/en_no_bokmal/j_make_slide_validation_sheet.py
# after annotation:
python experiments/en_no_bokmal/k_analyze_slide_validation.py \
  --annotations outputs/slide_validation/slide_validation_sheet_review2.csv \
  --out-dir outputs/slide_validation/review2_analysis

python experiments/en_no_bokmal/l_filter_threshold_sensitivity.py

python experiments/en_no_bokmal/n_analyze_slide_model_scale.py \
  --conditions original_subsampled bokmal \
  --fields prediction \
  --output-dir outputs/slide_analysis_model_scale_key
```

Optional model-scale training/evaluation:

```bash
sbatch experiments/en_no_bokmal/b_train_nllb_1_3b_original.sh
sbatch experiments/en_no_bokmal/b_train_nllb_1_3b_bokmal.sh
sbatch experiments/en_no_bokmal/b_train_nllb_1_3b_original_subsampled.sh
sbatch experiments/en_no_bokmal/b_train_nllb_3_3b_original.sh
sbatch experiments/en_no_bokmal/b_train_nllb_3_3b_bokmal.sh
sbatch experiments/en_no_bokmal/b_train_nllb_3_3b_original_subsampled.sh

sbatch experiments/en_no_bokmal/c_evaluate_nllb_1_3b_original.sh
sbatch experiments/en_no_bokmal/c_evaluate_nllb_1_3b_bokmal.sh
sbatch experiments/en_no_bokmal/c_evaluate_nllb_1_3b_original_subsampled.sh
sbatch experiments/en_no_bokmal/c_evaluate_nllb_3_3b_original.sh
sbatch experiments/en_no_bokmal/c_evaluate_nllb_3_3b_bokmal.sh
sbatch experiments/en_no_bokmal/c_evaluate_nllb_3_3b_original_subsampled.sh
```

## Current Audit Notes

1. SLIDE validation macro-F1 was corrected.
   - Old value in some notes: 0.732.
   - Correct standard four-class macro-F1 for `review2_analysis`: 0.549.
   - Reason: the `mixed` class had F1 0.0 and was previously skipped from the
     macro average.

2. SLIDE validation should be described carefully.
   - Agreement is moderate: exact agreement 60.0%, kappa 0.467.
   - SLIDE is not reliable as a fine-grained gold standard for mixedness.
   - It is more defensible for detecting large NB-only increases and NN-only
     suppression, especially when triangulated with BLEU/chrF, terminology
     metrics, FLORES mismatch, and human evaluation.

3. Human evaluation is diagnostic, not distribution-estimating.
   - Shift cases are intentionally enriched.
   - Preference counts should not be interpreted as population-level rates.

4. Threshold sensitivity is not a mitigation or retraining experiment.
   - It only shows data-selection counts are stable near the chosen threshold.
   - It does not prove model behavior is identical under every threshold.

5. Obsolete draft-label script removed.
   - `experiments/en_no_bokmal/m_make_slide_validation_draft.py` was removed
     during cleanup because it generated hard-coded draft labels and should not
     be treated as independent annotation.
   - Existing draft outputs under `outputs/slide_validation/` are historical
     artifacts only.
   - Use `review2_analysis` for the paper's SLIDE validation numbers.

6. Old local qualitative outputs contain mojibake in some Norwegian examples.
   - If qualitative examples are used in the paper, inspect and repair them
     manually from a reliable UTF-8 source before final submission.
