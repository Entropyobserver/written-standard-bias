# Paper Files

This directory contains the canonical EAMT template folder for the paper.

## Main Files

- `eamt26_template/latex_template/eamt26.tex`  
  Canonical EAMT-style paper draft. This is the only manuscript version to edit.
- `eamt26_template/latex_template/eamt26.bib`  
  Bibliography for the canonical paper. All entries are cited by the manuscript.
- `PAPER_TODO.md`  
  Paper completion checklist and status notes.

## Template Files

- `eamt26_template/latex_template/eamt26.sty`
- `eamt26_template/latex_template/eamt26.bst`
- `eamt26_template/latex_template/clone1.png`
- `eamt26_template/latex_template/clone2.png`

## SLIDE Validation Workflow

The paper uses SLIDE both for target-side filtering and written-standard analysis, so the automatic labels are triangulated with a small validation sample.

1. Generate the annotation sheet:

   `python experiments/en_no_bokmal/j_make_slide_validation_sheet.py --n-per-label 30`

2. Fill `outputs/slide_validation/slide_validation_sheet.csv`, using only `nb_only`, `nn_only`, `mixed`, or `uncertain`.

3. Save the filled sheet as `outputs/slide_validation/slide_validation_sheet_filled.csv`.

4. Analyze agreement:

   `python experiments/en_no_bokmal/k_analyze_slide_validation.py`

Current reported validation uses `outputs/slide_validation/review2_analysis/`: 120 annotated items, 60.0% exact agreement, four-class macro-F1 0.549, and Cohen's kappa 0.467. The validation sample is stratified by SLIDE label to test classifier reliability. It is not a corpus prevalence estimate.
