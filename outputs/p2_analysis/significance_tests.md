# Significance Tests

## bokmal_vs_original_subsampled_on_bokmal

| Test | Metric | Delta | 95% CI | p |
| --- | --- | ---: | ---: | ---: |
| paired bootstrap | sentence_chrf | +1.0585 | [+0.8561, +1.2522] | <0.001 |
| paired bootstrap | term_recall | +0.0388 | [+0.0288, +0.0497] | <0.001 |
| paired bootstrap | term_precision | +0.0074 | [+0.0021, +0.0129] | 0.006 |
| paired bootstrap | term_f1 | +0.0210 | [+0.0147, +0.0282] | <0.001 |

## bokmal_vs_original_subsampled_on_original

| Test | Metric | Delta | 95% CI | p |
| --- | --- | ---: | ---: | ---: |
| paired bootstrap | sentence_chrf | -1.7956 | [-2.0872, -1.5148] | <0.001 |
| paired bootstrap | term_recall | +0.1060 | [+0.0920, +0.1197] | <0.001 |
| paired bootstrap | term_precision | +0.0238 | [+0.0182, +0.0298] | <0.001 |
| paired bootstrap | term_f1 | +0.0599 | [+0.0517, +0.0685] | <0.001 |

## bokmal_vs_original_on_bokmal

| Test | Metric | Delta | 95% CI | p |
| --- | --- | ---: | ---: | ---: |
| paired bootstrap | sentence_chrf | +0.4956 | [+0.3109, +0.7051] | <0.001 |
| paired bootstrap | term_recall | +0.0397 | [+0.0284, +0.0512] | <0.001 |
| paired bootstrap | term_precision | +0.0053 | [+0.0001, +0.0102] | 0.044 |
| paired bootstrap | term_f1 | +0.0202 | [+0.0131, +0.0269] | <0.001 |

## bokmal_vs_original_on_original

| Test | Metric | Delta | 95% CI | p |
| --- | --- | ---: | ---: | ---: |
| paired bootstrap | sentence_chrf | -2.4496 | [-2.7285, -2.1566] | <0.001 |
| paired bootstrap | term_recall | +0.1169 | [+0.1011, +0.1324] | <0.001 |
| paired bootstrap | term_precision | +0.0243 | [+0.0180, +0.0301] | <0.001 |
| paired bootstrap | term_f1 | +0.0653 | [+0.0555, +0.0748] | <0.001 |

## McNemar SLIDE Tests

| Comparison | Seed | Metric | A rate | B rate | Delta | p |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| bokmal_vs_original_subsampled_on_bokmal | 42 | slide_nb_only | 0.9886 | 0.9383 | +0.0503 | <0.001 |
| bokmal_vs_original_subsampled_on_bokmal | 42 | slide_nn_only | 0.0000 | 0.0487 | -0.0487 | <0.001 |
| bokmal_vs_original_subsampled_on_bokmal | 123 | slide_nb_only | 0.9863 | 0.9490 | +0.0373 | <0.001 |
| bokmal_vs_original_subsampled_on_bokmal | 123 | slide_nn_only | 0.0008 | 0.0388 | -0.0381 | <0.001 |
| bokmal_vs_original_subsampled_on_bokmal | 456 | slide_nb_only | 0.9893 | 0.9558 | +0.0335 | <0.001 |
| bokmal_vs_original_subsampled_on_bokmal | 456 | slide_nn_only | 0.0000 | 0.0350 | -0.0350 | <0.001 |
| bokmal_vs_original_subsampled_on_original | 42 | slide_nb_only | 0.9334 | 0.7819 | +0.1515 | <0.001 |
| bokmal_vs_original_subsampled_on_original | 42 | slide_nn_only | 0.0075 | 0.1493 | -0.1418 | <0.001 |
| bokmal_vs_original_subsampled_on_original | 123 | slide_nb_only | 0.9334 | 0.7922 | +0.1412 | <0.001 |
| bokmal_vs_original_subsampled_on_original | 123 | slide_nn_only | 0.0069 | 0.1378 | -0.1309 | <0.001 |
| bokmal_vs_original_subsampled_on_original | 456 | slide_nb_only | 0.9346 | 0.7968 | +0.1378 | <0.001 |
| bokmal_vs_original_subsampled_on_original | 456 | slide_nn_only | 0.0063 | 0.1401 | -0.1338 | <0.001 |
| bokmal_vs_original_on_bokmal | 42 | slide_nb_only | 0.9886 | 0.9520 | +0.0366 | <0.001 |
| bokmal_vs_original_on_bokmal | 42 | slide_nn_only | 0.0000 | 0.0335 | -0.0335 | <0.001 |
| bokmal_vs_original_on_bokmal | 123 | slide_nb_only | 0.9863 | 0.9482 | +0.0381 | <0.001 |
| bokmal_vs_original_on_bokmal | 123 | slide_nn_only | 0.0008 | 0.0388 | -0.0381 | <0.001 |
| bokmal_vs_original_on_bokmal | 456 | slide_nb_only | 0.9893 | 0.9520 | +0.0373 | <0.001 |
| bokmal_vs_original_on_bokmal | 456 | slide_nn_only | 0.0000 | 0.0343 | -0.0343 | <0.001 |
| bokmal_vs_original_on_original | 42 | slide_nb_only | 0.9334 | 0.7910 | +0.1424 | <0.001 |
| bokmal_vs_original_on_original | 42 | slide_nn_only | 0.0075 | 0.1389 | -0.1315 | <0.001 |
| bokmal_vs_original_on_original | 123 | slide_nb_only | 0.9334 | 0.7887 | +0.1447 | <0.001 |
| bokmal_vs_original_on_original | 123 | slide_nn_only | 0.0069 | 0.1441 | -0.1372 | <0.001 |
| bokmal_vs_original_on_original | 456 | slide_nb_only | 0.9346 | 0.7905 | +0.1441 | <0.001 |
| bokmal_vs_original_on_original | 456 | slide_nn_only | 0.0063 | 0.1401 | -0.1338 | <0.001 |
