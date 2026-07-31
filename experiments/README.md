# Experiments

This repository currently keeps one experiment line:

```text
en_no_bokmal/
```

It contains the Bokmal written-standard filtering experiments for
English-to-Norwegian petroleum-domain machine translation.

## `en_no_bokmal`

The scripts are ordered by experiment stage:

| Stage | Files | Purpose |
| --- | --- | --- |
| `a_*` | data and diagnostic preparation | SLIDE distribution, size-matched control, FLORES OOD data |
| `b_*` | training | LoRA fine-tuning for original, Bokmal, and original-subsampled conditions |
| `c_*` | evaluation | BLEU, chrF, and terminology metrics on in-domain and OOD tests |
| `d_*` | summary | aggregate result tables, figures, and model-scale robustness |
| `e_*` | SLIDE output analysis | written-standard analysis of model outputs |
| `f_*` | qualitative examples | paper-ready example selection |
| `g_*` | significance tests | paired bootstrap and McNemar tests |
| `h_*` | human evaluation sheet | blinded annotation sheet creation |
| `i_*` | human evaluation analysis | summarize annotated adequacy, Bokmal conformity, and preference |
| `n_*` | model-scale SLIDE analysis | written-standard analysis across NLLB model sizes |

Recommended order:

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
```

Optional NLLB scale robustness jobs:

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

python experiments/en_no_bokmal/d_summarize_model_scale.py
sbatch experiments/en_no_bokmal/n_analyze_slide_model_scale.sh
```

For the paper's key size-controlled SLIDE replication, the local completed run used:

```bash
python experiments/en_no_bokmal/n_analyze_slide_model_scale.py \
  --conditions original_subsampled bokmal \
  --fields prediction \
  --output-dir outputs/slide_analysis_model_scale_key
```

The expected outputs are written under `outputs/`.
