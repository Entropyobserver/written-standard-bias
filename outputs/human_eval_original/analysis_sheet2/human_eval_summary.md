# Human Evaluation Summary

Items: 40

## Model Means

| Model | Adequacy | Bokmal conformity |
|---|---:|---:|
| bokmal | 1.900 | 1.975 |
| original_subsampled | 1.875 | 0.975 |

## Paired Deltas

- Adequacy, Bokmal minus original-subsampled: +0.025
- Bokmal conformity, Bokmal minus original-subsampled: +1.000

## Preference

- Counts: {'bokmal': 26, 'tie': 11, 'original_subsampled': 3}
- Exact sign-test p-value, excluding ties: 0.0000

## By Stratum

### control

{
  "bokmal": {
    "adequacy": 1.85,
    "bokmal": 1.95
  },
  "original_subsampled": {
    "adequacy": 1.9,
    "bokmal": 1.9
  },
  "delta_bokmal_minus_original_subsampled": {
    "adequacy": -0.05,
    "bokmal": 0.05
  },
  "preference_counts": {
    "tie": 11,
    "bokmal": 6,
    "original_subsampled": 3
  }
}

### shift

{
  "bokmal": {
    "adequacy": 1.95,
    "bokmal": 2.0
  },
  "original_subsampled": {
    "adequacy": 1.85,
    "bokmal": 0.05
  },
  "delta_bokmal_minus_original_subsampled": {
    "adequacy": 0.1,
    "bokmal": 1.95
  },
  "preference_counts": {
    "bokmal": 20
  }
}
