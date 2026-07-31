# Human Evaluation Report for the Bokmal Filtering Study

## Purpose

This human evaluation checks whether the Bokmal-filtered model improves written-standard conformity without harming translation adequacy. It complements the automatic BLEU, chrF, terminology, and SLIDE-based analyses in the Bokmal filtering paper.

The evaluation focuses on the comparison between:

- `bokmal`: the model trained on the Bokmal-filtered training data.
- `original_subsampled`: the size-controlled baseline trained on the original data subsampled to the same training size.

The key question is not whether one model is universally better, but whether the Bokmal-filtered model produces more appropriate Bokmal outputs, especially in cases where the baseline output shows written-standard shift.

## Files

The human evaluation files are stored under:

`outputs/human_eval/`

Main files:

- `human_eval_sheet2.csv`: completed annotation sheet from annotator 1.
- `human_eval_sheet3.csv`: completed annotation sheet from annotator 2.
- `human_eval_key.csv`: hidden system key mapping System A/System B to model identities.
- `instructions.md`: annotation instructions.
- `analysis_sheet2/human_eval_summary.json`: annotator 1 analysis.
- `analysis_sheet3/human_eval_summary.json`: annotator 2 analysis.
- `analysis_sheet2_sheet3_combined/human_eval_combined_summary.json`: combined analysis across both annotators.
- `human_evaluation_report.md`: this report.

Removed temporary files:

- Earlier temporary analysis outputs were removed because they should not be part of the final human evaluation package.

## Evaluation Design

The evaluation uses 40 sentence-level translation items:

- 20 shift items: cases where the two systems differ strongly in written-standard behavior.
- 20 control items: cases where the systems are expected to be closer.

Each item contains:

- English source sentence.
- Norwegian reference.
- System A output.
- System B output.
- Adequacy score for System A.
- Adequacy score for System B.
- Bokmal conformity score for System A.
- Bokmal conformity score for System B.
- Preference for Bokmal output: A, B, or Tie.
- Optional notes.

The system identity was hidden from annotators during scoring and recovered only during analysis using `human_eval_key.csv`.

## Scoring Scheme

Adequacy:

- 0: incorrect or seriously incomplete translation.
- 1: partially adequate translation with some meaning loss, awkwardness, or terminology problems.
- 2: adequate translation preserving the source meaning.

Bokmal conformity:

- 0: clearly not Bokmal, or strongly Nynorsk-like/mixed written standard.
- 1: partly Bokmal but with noticeable written-standard inconsistency.
- 2: natural or acceptable Bokmal.

Preference:

- A: System A is preferred for Bokmal translation.
- B: System B is preferred for Bokmal translation.
- Tie: no clear preference.

## Annotator-Level Results

Annotator 1 (`human_eval_sheet2.csv`):

| Model | Adequacy | Bokmal conformity |
|---|---:|---:|
| Bokmal-filtered | 1.900 | 1.975 |
| Original-subsampled | 1.875 | 0.975 |

Preference counts:

| Preferred model | Count |
|---|---:|
| Bokmal-filtered | 26 |
| Original-subsampled | 3 |
| Tie | 11 |

Exact sign test, excluding ties:

- `p = 1.52e-05`

Annotator 2 (`human_eval_sheet3.csv`):

| Model | Adequacy | Bokmal conformity |
|---|---:|---:|
| Bokmal-filtered | 1.925 | 1.800 |
| Original-subsampled | 1.975 | 1.025 |

Preference counts:

| Preferred model | Count |
|---|---:|
| Bokmal-filtered | 22 |
| Original-subsampled | 3 |
| Tie | 15 |

Exact sign test, excluding ties:

- `p = 0.0001565`

## Combined Results

Combined over two annotators:

| Model | Adequacy | Bokmal conformity |
|---|---:|---:|
| Bokmal-filtered | 1.9125 | 1.8875 |
| Original-subsampled | 1.9250 | 1.0000 |

Paired mean difference, Bokmal-filtered minus original-subsampled:

| Metric | Difference |
|---|---:|
| Adequacy | -0.0125 |
| Bokmal conformity | +0.8875 |

Preference counts:

| Preferred model | Count |
|---|---:|
| Bokmal-filtered | 48 |
| Original-subsampled | 6 |
| Tie | 26 |

Exact sign test, excluding ties:

- `p = 3.26e-09`

Interpretation:

- Adequacy is essentially unchanged. The Bokmal-filtered model is not meaningfully worse in semantic adequacy.
- Bokmal conformity improves strongly.
- Human preference strongly favors the Bokmal-filtered model when the task is explicitly Bokmal translation.

## Stratum-Level Results

Shift items:

| Model | Adequacy | Bokmal conformity |
|---|---:|---:|
| Bokmal-filtered | 1.950 | 1.975 |
| Original-subsampled | 1.925 | 0.150 |

Differences:

| Metric | Difference |
|---|---:|
| Adequacy | +0.025 |
| Bokmal conformity | +1.825 |

Preference counts:

| Preferred model | Count |
|---|---:|
| Bokmal-filtered | 40 |
| Original-subsampled | 0 |
| Tie | 0 |

Control items:

| Model | Adequacy | Bokmal conformity |
|---|---:|---:|
| Bokmal-filtered | 1.875 | 1.800 |
| Original-subsampled | 1.925 | 1.850 |

Differences:

| Metric | Difference |
|---|---:|
| Adequacy | -0.050 |
| Bokmal conformity | -0.050 |

Preference counts:

| Preferred model | Count |
|---|---:|
| Bokmal-filtered | 8 |
| Original-subsampled | 6 |
| Tie | 26 |

Interpretation:

- On shift items, the Bokmal-filtered model is unanimously preferred and shows much higher Bokmal conformity.
- On control items, the systems are broadly comparable and most judgments are ties.
- This supports the paper's main interpretation: filtering mainly changes target-standard behavior rather than broadly changing translation adequacy.

## Inter-Annotator Agreement

Exact agreement between the two annotation sheets:

| Field | Agreement |
|---|---:|
| Adequacy A | 95.0% |
| Adequacy B | 92.5% |
| Bokmal conformity A | 82.5% |
| Bokmal conformity B | 87.5% |
| Preference | 90.0% |

Interpretation:

- Adequacy agreement is very high.
- Bokmal conformity agreement is also high, though slightly lower, which is expected because written-standard conformity involves more fine-grained linguistic judgment.
- Preference agreement is high enough to support using the results as a reliability check in the paper.

## Representative Cases

The paper should include only a small number of qualitative cases. The purpose is not to prove the result again, but to make the quantitative pattern interpretable. Three cases are sufficient:

1. A typical written-standard shift case.
2. A control case where both systems are effectively comparable.
3. A trade-off case where the Bokmal-filtered model improves written-standard conformity but has a minor adequacy or terminology weakness.

### Case 1: Typical written-standard shift

Item: `H005`

Stratum: `shift`

Source:

> Production from Vale and Volund was also closed due to technical problems.

Reference:

> Produksjonen frå Vale og Volund var og stengd pga. tekniske problem.

Original-subsampled:

> Produksjonen frå Vale og Volund var også stengd på grunn av tekniske problem.

Bokmal-filtered:

> Produksjonen fra Vale og Volund ble også stengt på grunn av tekniske problemer.

Human judgment:

- Both systems preserve the source meaning.
- The original-subsampled output keeps Nynorsk-like or mixed forms such as `frå` and `stengd`.
- The Bokmal-filtered output normalizes these to Bokmal forms such as `fra`, `ble`, and `stengt`.
- Preference: Bokmal-filtered.

Paper role:

- This example illustrates the central finding: filtering changes the target written standard while preserving adequacy.

### Case 2: Control case

Item: `H008`

Stratum: `control`

Source:

> The atlas provides an overview over areas where CO2 can be stored safely in the subsurface for a long time.

Reference:

> Atlaset gir en oversikt over områder der det er mulig å langtidslagre CO2 trygt i undergrunnen.

Original-subsampled:

> Atlaset gir en oversikt over områder der CO2 kan lagres trygt i undergrunnen i lang tid.

Bokmal-filtered:

> Atlaset gir oversikt over områder der CO2 kan lagres trygt i undergrunnen i lang tid.

Human judgment:

- Both systems are adequate.
- Both systems are natural Bokmal.
- Preference: tie.

Paper role:

- This example shows that filtering does not force arbitrary changes when both systems already produce acceptable Bokmal.

### Case 3: Trade-off case

Item: `H038`

Stratum: `shift`

Source:

> In July production from the Vale field was closed due to technical problems and the Gimle and Tordis fields were closed due to barrier-weakness in well.

Reference:

> Produksjonen frå Vale var stengd i juli pga tekniske problem og Gimle og Tordis stengd pga barriere-svikt i brønn

Original-subsampled:

> I juli var produksjonen frå Valefeltet stengd på grunn av tekniske problem og Gimle- og Tordisfeltet stengd på grunn av barriere svakhet i brønn.

Bokmal-filtered:

> I juli ble produksjonen fra Vale-feltet stengt på grunn av tekniske problemer og feltene Gimle og Tordis stengt på grunn av barrierefølsomhet i brønn.

Human judgment:

- The Bokmal-filtered output is more consistent Bokmal.
- The original-subsampled output is less Bokmal-conforming because of forms such as `frå` and `stengd`.
- However, the Bokmal-filtered output renders `barrier-weakness` less precisely as `barrierefølsomhet`, while the original-subsampled output uses a more literal `svakhet`.
- Preference for a Bokmal use case: Bokmal-filtered, but with a noted terminology/adequacy trade-off.

Paper role:

- This example prevents the qualitative analysis from looking one-sided. It shows that written-standard conformity and semantic/terminological adequacy are related but not identical.

## Suggested Paper Wording

The following wording can be adapted into the paper:

> To complement automatic metrics, we conducted a blind human evaluation on 40 sentence-level items, consisting of 20 written-standard shift cases and 20 control cases. Two annotators rated each system output for adequacy and Bokmal conformity on a 0--2 scale and selected the preferred output for Bokmal translation. System identities were hidden during annotation.

> Averaged across annotators, the Bokmal-filtered model achieved comparable adequacy to the size-controlled original-subsampled baseline (1.913 vs. 1.925), while substantially improving Bokmal conformity (1.888 vs. 1.000). Preference judgments also favored the Bokmal-filtered model (48 vs. 6, excluding 26 ties; exact sign test p < 0.001). The effect was concentrated in shift cases, where the Bokmal-filtered model was preferred in all 40 annotator-item judgments, while control cases were mostly ties. This supports the interpretation that target-side filtering primarily improves written-standard conformity rather than simply changing semantic adequacy.

## Main Claim Supported by Human Evaluation

The human evaluation supports three claims:

1. Bokmal filtering improves Bokmal written-standard conformity.
2. The improvement is strongest exactly where the original-subsampled model shows written-standard shift.
3. The adequacy difference is negligible, so the effect is better interpreted as target-standard specialization rather than general translation-quality degradation.

## Limitations

The human evaluation is intentionally small and diagnostic:

- It covers 40 sentence-level items.
- It evaluates only the Bokmal-filtered model against the size-controlled original-subsampled baseline.
- It focuses on English-to-Norwegian petroleum-domain translation.
- It is designed to validate the interpretation of the automatic analyses, not to replace full-scale human MT evaluation.

These limitations should be stated clearly in the paper.
