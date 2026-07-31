# SLIDE Validation Summary

Annotated items: 120
Blank/skipped items: 0
Accuracy: 0.642
Macro-F1: 0.586
Cohen's kappa: 0.522

## Per Label

| Label | Precision | Recall | F1 | Human support | SLIDE support |
|---|---:|---:|---:|---:|---:|
| nb_only | 0.967 | 0.806 | 0.879 | 36 | 30 |
| nn_only | 0.800 | 1.000 | 0.889 | 24 | 30 |
| mixed | 0.000 | 0.000 | 0.000 | 7 | 30 |
| uncertain | 0.800 | 0.453 | 0.578 | 53 | 30 |

## Confusion Matrix

Rows are human labels; columns are SLIDE labels.

| Human \ SLIDE | nb_only | nn_only | mixed | uncertain |
|---|---:|---:|---:|---:|
| nb_only | 29 | 0 | 3 | 4 |
| nn_only | 0 | 24 | 0 | 0 |
| mixed | 1 | 4 | 0 | 2 |
| uncertain | 0 | 2 | 27 | 24 |

## By Pool

| Pool | N | Accuracy |
|---|---:|---:|
| bokmal_prediction | 17 | 0.471 |
| original_reference | 51 | 0.667 |
| original_subsampled_prediction | 52 | 0.673 |

## By Field

| Field | N | Accuracy |
|---|---:|---:|
| prediction | 69 | 0.623 |
| reference | 51 | 0.667 |

Rows are human labels and columns are SLIDE labels. The validation sample is stratified and is not a prevalence estimate.