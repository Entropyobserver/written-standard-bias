# Human Evaluation Summary

Items: 40

## Model Means

| Model | Adequacy | Bokmal conformity |
|---|---:|---:|
| bokmal | 1.925 | 1.800 |
| original_subsampled | 1.975 | 1.025 |

## Paired Deltas

- Adequacy, Bokmal minus original-subsampled: -0.050
- Bokmal conformity, Bokmal minus original-subsampled: +0.775

## Preference

- Counts: {'bokmal': 22, 'tie': 15, 'original_subsampled': 3}
- Exact sign-test p-value, excluding ties: 0.0002

## By Stratum

### control

{
  "bokmal": {
    "adequacy": 1.9,
    "bokmal": 1.65
  },
  "original_subsampled": {
    "adequacy": 1.95,
    "bokmal": 1.8
  },
  "delta_bokmal_minus_original_subsampled": {
    "adequacy": -0.05,
    "bokmal": -0.15
  },
  "preference_counts": {
    "tie": 15,
    "bokmal": 2,
    "original_subsampled": 3
  }
}

### shift

{
  "bokmal": {
    "adequacy": 1.95,
    "bokmal": 1.95
  },
  "original_subsampled": {
    "adequacy": 2.0,
    "bokmal": 0.25
  },
  "delta_bokmal_minus_original_subsampled": {
    "adequacy": -0.05,
    "bokmal": 1.7
  },
  "preference_counts": {
    "bokmal": 20
  }
}
