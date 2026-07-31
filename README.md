# Bokmal Filtering for English-Norwegian Petroleum MT

This repository contains the experiments for a Bokmal written-standard filtering
study in English-to-Norwegian petroleum-domain machine translation.

The central question is whether training on a Bokmal-only version of the NPD
petroleum corpus improves target-standard consistency, terminology behavior,
and translation quality compared with training on the original mixed or
uncertain Norwegian data.

## Research Setup

The paper compares three training conditions:

| Condition | Training data | Purpose |
| --- | --- | --- |
| `original` | Original NPD train split | Main baseline |
| `bokmal` | SLIDE-filtered Bokmal-only NPD split | Written-standard-aware model |
| `original_subsampled` | Size-matched sample from the original split | Control for data-size reduction |

All models use the same base model and training recipe:

- Base model: `facebook/nllb-200-distilled-600M`
- Direction: English to Norwegian Bokmal (`eng_Latn` -> `nob_Latn`)
- Fine-tuning: LoRA
- Seeds: `42`, `123`, `456`
- Metrics: BLEU, chrF, term recall, term precision, term F1, and SLIDE-based output standard analysis

## Repository Layout

```text
.
+-- config.yaml                         # original NPD training config
+-- data/
|   +-- final_splits_npd/               # original NPD train/val/test
|   +-- final_splits_npd_bokmal/        # Bokmal-filtered train/val/test
|   +-- final_splits_npd_original_subsampled/
|   +-- flores_ood/                     # FLORES nob/nno OOD test sets
|   +-- term/                           # terminology glossary
+-- experiments/
|   +-- en_no_bokmal/                   # paper experiments
+-- scripts/
|   +-- data/                           # dataset loading
|   +-- evaluation/                     # BLEU/chrF/term metrics
|   +-- model/                          # LoRA training utilities
+-- docs/                               # technical reports and experiment notes
+-- paper/                              # paper drafts, bibliography, and EAMT template files
+-- outputs/                            # generated results
```

## Main Experiment Pipeline

Run scripts from the project root.

### 1. Analyze written-standard distribution

```bash
python experiments/en_no_bokmal/a_analyze_training_slide_distribution.py
```

This compares SLIDE labels and scores in the original and Bokmal-filtered
training data.

### 2. Build the size-matched control

```bash
python experiments/en_no_bokmal/a_make_original_subsampled.py
```

This creates `data/final_splits_npd_original_subsampled/`, matching the
Bokmal-filtered data size while keeping examples from the original distribution.

### 3. Prepare FLORES OOD test sets

```bash
python experiments/en_no_bokmal/a_prepare_flores_ood.py
```

This creates English-to-Bokmal and English-to-Nynorsk FLORES test files under
`data/flores_ood/`.

### 4. Train models

On UPPMAX/Pelle:

```bash
sbatch experiments/en_no_bokmal/b_train_original.sh
sbatch experiments/en_no_bokmal/b_train_bokmal.sh
sbatch experiments/en_no_bokmal/b_train_original_subsampled.sh
```

The direct Python form is:

```bash
python experiments/en_no_bokmal/b_train.py --data original
python experiments/en_no_bokmal/b_train.py --data bokmal
python experiments/en_no_bokmal/b_train.py --data original_subsampled
```

### 5. Evaluate models

Examples:

```bash
sbatch experiments/en_no_bokmal/c_evaluate_base_all.sh
sbatch experiments/en_no_bokmal/c_evaluate_original_on_original.sh
sbatch experiments/en_no_bokmal/c_evaluate_original_on_bokmal.sh
sbatch experiments/en_no_bokmal/c_evaluate_bokmal_on_original.sh
sbatch experiments/en_no_bokmal/c_evaluate_bokmal_on_bokmal.sh
sbatch experiments/en_no_bokmal/c_evaluate_original_subsampled_on_original.sh
sbatch experiments/en_no_bokmal/c_evaluate_original_subsampled_on_bokmal.sh
sbatch experiments/en_no_bokmal/c_evaluate_flores_ood.sh
```

The direct Python form is:

```bash
python experiments/en_no_bokmal/c_evaluate.py --model bokmal --test bokmal
python experiments/en_no_bokmal/c_evaluate.py --model original --test original
python experiments/en_no_bokmal/c_evaluate.py --model base --test flores_nob
```

Available models:

- `base`
- `original`
- `bokmal`
- `original_subsampled`

Available test sets:

- `original`
- `bokmal`
- `original_subsampled`
- `flores_nob`
- `flores_nno`

### 6. Summarize results

If predictions already exist and only the metric definitions changed, recompute
metrics without loading any model:

```bash
python experiments/en_no_bokmal/c_recompute_metrics_from_predictions.py --all
```

Then summarize the updated result files:

```bash
python experiments/en_no_bokmal/d_summarize_results.py
```

This writes summary tables and figures under `outputs/p2_analysis/`.

### 6b. Run significance tests

```bash
python experiments/en_no_bokmal/g_significance_tests.py --n-bootstrap 1000
```

This writes paired bootstrap and McNemar test results to:

```text
outputs/p2_analysis/significance_tests.json
outputs/p2_analysis/significance_tests.csv
outputs/p2_analysis/significance_tests.md
```

### 7. Analyze generated written standard

```bash
sbatch experiments/en_no_bokmal/e_analyze_slide_outputs.sh
```

or:

```bash
python experiments/en_no_bokmal/e_analyze_slide_outputs.py
```

This applies SLIDE to model outputs and references, then reports whether the
generated Norwegian is Bokmal, Nynorsk, or uncertain.

### 8. Select qualitative examples

```bash
python experiments/en_no_bokmal/f_select_qualitative_examples.py
```

This creates example tables for the paper under `outputs/paper_examples/`.

### 9. Optional human validation

Create a blinded annotation sheet from the existing predictions:

```bash
python experiments/en_no_bokmal/h_make_human_eval_sheet.py --n-shift 20 --n-control 20
```

This writes:

```text
outputs/human_eval/human_eval_sheet.csv
outputs/human_eval/human_eval_key.csv
outputs/human_eval/instructions.md
```

Give only `human_eval_sheet.csv` and `instructions.md` to the annotator.
Keep `human_eval_key.csv` hidden until analysis. After the annotator fills the
score columns, save the completed file as:

```text
outputs/human_eval/human_eval_sheet_filled.csv
```

Then analyze it:

```bash
python experiments/en_no_bokmal/i_analyze_human_eval.py
```

This writes:

```text
outputs/human_eval/human_eval_summary.json
outputs/human_eval/human_eval_summary.md
```

### 10. Optional NLLB model-scale robustness

The main paper uses NLLB-600M as the controlled model. To check whether the
Bokmal-filtering pattern is stable across NLLB scale, run the same three
training conditions on NLLB-1.3B and NLLB-3.3B:

```bash
sbatch experiments/en_no_bokmal/b_train_nllb_1_3b_original.sh
sbatch experiments/en_no_bokmal/b_train_nllb_1_3b_bokmal.sh
sbatch experiments/en_no_bokmal/b_train_nllb_1_3b_original_subsampled.sh
sbatch experiments/en_no_bokmal/b_train_nllb_3_3b_original.sh
sbatch experiments/en_no_bokmal/b_train_nllb_3_3b_bokmal.sh
sbatch experiments/en_no_bokmal/b_train_nllb_3_3b_original_subsampled.sh
```

After the training jobs finish, evaluate on the Bokmal and original test sets:

```bash
sbatch experiments/en_no_bokmal/c_evaluate_nllb_1_3b_original.sh
sbatch experiments/en_no_bokmal/c_evaluate_nllb_1_3b_bokmal.sh
sbatch experiments/en_no_bokmal/c_evaluate_nllb_1_3b_original_subsampled.sh
sbatch experiments/en_no_bokmal/c_evaluate_nllb_3_3b_original.sh
sbatch experiments/en_no_bokmal/c_evaluate_nllb_3_3b_bokmal.sh
sbatch experiments/en_no_bokmal/c_evaluate_nllb_3_3b_original_subsampled.sh
```

Then summarize the model-scale robustness table:

```bash
python experiments/en_no_bokmal/d_summarize_model_scale.py
```

This writes:

```text
outputs/p2_analysis/model_scale_results.csv
outputs/p2_analysis/model_scale_deltas.csv
outputs/p2_analysis/model_scale_results.json
```

## Outputs

Important generated directories:

```text
outputs/p2_train_original/
outputs/p2_train_bokmal/
outputs/p2_train_original_subsampled/
outputs/p2_eval_model_*_test_*/
outputs/slide_training_distribution/
outputs/slide_analysis/
outputs/p2_analysis/
outputs/paper_examples/
outputs/human_eval/
outputs/p2_robust_nllb_1_3b_*/
outputs/p2_robust_nllb_3_3b_*/
```

These are experiment artifacts and are not required to be committed unless a
result archive is needed.

## Notes

- `config.yaml` is the original NPD configuration.
- `experiments/en_no_bokmal/config_bokmal.yaml` is the Bokmal-filtered
  configuration.
- `experiments/en_no_bokmal/config_original_subsampled.yaml` is the
  size-control configuration.
- The terminology evaluator is implemented in
  `scripts/evaluation/fta_evaluator.py`.
- The main paper draft is under `paper/`.
