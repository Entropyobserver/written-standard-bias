# SLIDE Validation Summary

Annotated items: 120
Blank/skipped items: 0
Accuracy: 0.608
Macro-F1: 0.552
Cohen's kappa: 0.478

## Per Label

| Label | Precision | Recall | F1 | Human support | SLIDE support |
|---|---:|---:|---:|---:|---:|
| nb_only | 0.900 | 0.574 | 0.701 | 47 | 30 |
| nn_only | 0.733 | 0.957 | 0.830 | 23 | 30 |
| mixed | 0.000 | 0.000 | 0.000 | 9 | 30 |
| uncertain | 0.800 | 0.585 | 0.676 | 41 | 30 |

## Confusion Matrix

Rows are human labels; columns are SLIDE labels.

| Human \ SLIDE | nb_only | nn_only | mixed | uncertain |
|---|---:|---:|---:|---:|
| nb_only | 27 | 0 | 16 | 4 |
| nn_only | 1 | 22 | 0 | 0 |
| mixed | 1 | 6 | 0 | 2 |
| uncertain | 1 | 2 | 14 | 24 |

## By Pool

| Pool | N | Accuracy |
|---|---:|---:|
| bokmal_prediction | 17 | 0.529 |
| original_reference | 51 | 0.608 |
| original_subsampled_prediction | 52 | 0.635 |

## By Field

| Field | N | Accuracy |
|---|---:|---:|
| prediction | 69 | 0.609 |
| reference | 51 | 0.608 |

Rows are human labels and columns are SLIDE labels. The validation sample is stratified and is not a prevalence estimate.