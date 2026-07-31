# Bokmal Filtering Paper TODO Status

This checklist tracks the eight issues raised for the EAMT-style draft.

## 1. Qualitative examples

Status: done for the current draft.

Needed files:
- `outputs/.../predictions.json`
- `outputs/slide_analysis/.../slide_sentence_scores.json`

What to add:
- 5-8 examples with source, reference, original-subsampled output, and Bokmal-filtered output.
- Select examples where the reference is SLIDE NN/mixed and the Bokmal model output is SLIDE NB.
- Highlight shifts such as `ikkje -> ikke`, `fraa/fra`, `vere -> vaere`, `noko -> noe`.

Current paper handling:
- Added a qualitative examples table with six real examples from `seed_42`.
- Examples compare source, reference, original-subsampled output, and Bokmal-filtered output.

## 2. Significance tests / variance

Status: done.

Done:
- Added seed-level standard deviations to the in-domain table.
- Added seed-level standard deviations to the FLORES table.
- Added `experiments/en_no_bokmal/g_significance_tests.py`.
- Added paired bootstrap tests for sentence-level chrF and terminology metrics.
- Added McNemar tests for SLIDE NB-only and NN-only output rates.
- Updated the paper with the main significance-test findings.

## 2b. Filtering threshold sensitivity

Status: data-selection check done; no retraining.

Done:
- Added `experiments/en_no_bokmal/l_filter_threshold_sensitivity.py`.
- Generated `outputs/slide_training_distribution/filter_threshold_sensitivity.csv`.
- Generated `outputs/slide_training_distribution/filter_threshold_sensitivity.md`.
- Added a paper paragraph reporting that nearby thresholds retain 9,925--10,212 training sentences, or 71.2--73.3% of the original train split.

Current paper handling:
- Presents this as a data-selection robustness check, not a substitute for retraining every threshold.

## 3. Human evaluation

Status: done for the current draft.

Done:
- Completed two blind human-evaluation sheets and combined them in `outputs/human_eval/analysis_sheet2_sheet3_combined/`.
- Reported the evaluation as diagnostic rather than distribution-estimating.
- Kept preference counts explicitly scoped to the enriched diagnostic sample.

Current paper handling:
- Added a blind human evaluation section focused on adequacy and Bokmal conformity.
- Reports comparable adequacy, higher Bokmal conformity, preference counts, and exact agreement.

## 3b. SLIDE validation / triangulation

Status: done for the current draft.

Why this matters:
- The paper uses SLIDE for target-side filtering and written-standard analysis.
- A reviewer may read this as circular unless SLIDE is checked independently on petroleum-domain text.

Done:
- Generated a 120-item stratified validation sheet in `outputs/slide_validation/`.
- Analyzed manual review in `outputs/slide_validation/review2_analysis/`.
- Reported exact agreement, four-class macro-F1, Cohen's kappa, and the main interpretation of the confusion matrix.

Current paper handling:
- Explicitly states that SLIDE percentages are classifier-based evidence rather than fully independent proof.
- Reports 60.0% exact agreement, four-class macro-F1 0.549, and Cohen's kappa 0.467 on a stratified 120-item petroleum-domain validation sample.
- Explains that SLIDE is stronger for NB-only and NN-only contrasts than for fine-grained mixed/uncertain distinctions.
- Triangulates SLIDE with BLEU/chrF reversals, terminology metrics, and blind human judgments.

## 3c. Model-scale SLIDE analysis

Status: done for the key size-controlled comparison.

Purpose:
- Strengthen the model-scale claim from "automatic metric reversal persists" to "both automatic metric reversal and written-standard shift persist across model sizes."

Done:
- Added `experiments/en_no_bokmal/n_analyze_slide_model_scale.py`.
- Added `experiments/en_no_bokmal/n_analyze_slide_model_scale.sh`.
- The script reads existing prediction files for 600M, 1.3B, and 3.3B systems; it does not retrain or regenerate translations.
- Ran the key comparison locally for `original_subsampled` and `bokmal` predictions on the original and Bokmal in-domain test sets.
- Updated the paper to state that both the automatic metric reversal and the SLIDE-measured written-standard shift persist across 600M, 1.3B, and 3.3B.

Run:
- `sbatch experiments/en_no_bokmal/n_analyze_slide_model_scale.sh`

Current key outputs:
- `outputs/slide_analysis_model_scale_key/summary_by_seed.csv`
- `outputs/slide_analysis_model_scale_key/summary_by_model.csv`
- `outputs/slide_analysis_model_scale_key/summary.json`
- Per-seed `slide_sentence_scores.json` files for traceability.

Optional full outputs:
- Running the SLURM script without filtering conditions will write the full three-condition analysis under `outputs/slide_analysis_model_scale/`.

## 4. Training hyperparameters

Status: done.

Added to paper:
- LoRA rank/alpha/dropout/target modules.
- Learning rate.
- Batch size and gradient accumulation.
- Effective batch size.
- Epochs.
- Warmup steps.
- Evaluation/checkpoint interval.
- Early stopping patience.
- Max length.
- FP16.
- AdamW via Hugging Face Seq2SeqTrainer.
- Weight decay.
- Beam size.

## 5. Title / author placeholders

Status: adjusted for submission.

EAMT 2026 submissions should be anonymized, so the draft now uses:
- `Anonymous submission`

For camera-ready, replace with real names, affiliations, and email.

## 6. Official style files

Status: done locally.

Available in the same folder as the `.tex` file:
- `eamt26.sty`
- `eamt26.bst`

Note:
- Local TeX executables are still unavailable in this workspace, so PDF compilation must be done in Overleaf or another TeX environment.

## 7. Acknowledgements

Status: left commented out for anonymous submission.

For camera-ready, add:
- UPPMAX/Pelle HPC acknowledgement.
- Funding acknowledgement if applicable.
- Supervisor/advisor acknowledgement if appropriate.

## 8. Structural issues

Status: mostly done.

Done:
- Moved Related Work after Research Questions.
- Matched five contributions to five RQs.
- Replaced recall-only FTA reporting with glossary-based TermR, TermP, and TermF1.
- Added terminology metric-validity point to the abstract and discussion.
- Removed redundant standalone size-controlled table and folded comparison into prose.
- Removed empty standalone Qualitative Analysis section; moved note into Discussion.

Still useful:
- Review examples manually and replace any weak/awkward example before submission.
- Compile the final PDF in Overleaf or another TeX environment and check table placement/page length.

## Reviewer-risk coverage

This section maps the eight reviewer-risk points to the current paper handling.

1. SLIDE circularity
   - Code prepared for blind SLIDE validation: `experiments/en_no_bokmal/j_make_slide_validation_sheet.py` and `experiments/en_no_bokmal/k_analyze_slide_validation.py`.
   - Generated a 120-item stratified validation sheet in `outputs/slide_validation/`.
   - Paper now states that SLIDE percentages are classifier-based evidence, not fully independent proof, and triangulates them with BLEU/chrF, terminology metrics, and human judgments.
   - Paper now reports a 120-item SLIDE validation sample: 60.0% exact agreement, four-class macro-F1 0.549, Cohen's kappa 0.467; interpretation is restricted to robust NB-only/NN-only contrasts rather than precise mixedness.

2. Filtering threshold sensitivity
   - Added data-selection sensitivity script: `experiments/en_no_bokmal/l_filter_threshold_sensitivity.py`.
   - Generated `outputs/slide_training_distribution/filter_threshold_sensitivity.csv` and `.md`.
   - Paper reports nearby thresholds retain 9,925--10,212 training sentences, or 71.2--73.3% of the original training split.

3. Human-eval selection bias
   - Paper now states in the Human Evaluation section that the sample is diagnostic rather than distribution-estimating.
   - It explicitly says intentionally enriched shift cases mean preference counts are not population-level rates.

4. Bias term overload
   - Abstract and Introduction now clarify that bias is used in the evaluation sense, not demographic stereotyping.
   - Target-standard bias is defined as systematic preference for one legitimate written standard over another.

5. Related work too narrow
   - Added a broader Related Work paragraph on variant and standard bias beyond Norwegian.
   - Added citations on language-variety MT, Portuguese varieties, Arabic dialect/MSA evaluation, and Chinese localization conventions.

6. No mitigation
   - Added a Discussion paragraph framing the paper as diagnostic/audit-oriented.
   - Added concrete mitigation/audit options: balanced data, target-standard tags, written-standard distribution reporting, standard-specific references, and explicit terminology-form reporting.

7. Single language/model/domain
   - Limitations now frame Norwegian as a controlled case study of a broader multi-standard evaluation problem.
   - The paper explicitly says the magnitude should not be assumed to generalize across languages.

8. Glossary is 70 terms and NB-oriented
   - Paper consistently interprets TermR/TermP/TermF1 as Bokmal term-form conformity, not standard-neutral terminology accuracy.
   - Discussion now says NB-oriented terminology is legitimate for NB deployment; the audit problem is silent use of NB-oriented metrics as general Norwegian quality.
   - Mitigation paragraph avoids inventing NN terms: dual-standard glossary only when stable NN variants exist; otherwise report the metric as NB-form conformity.
