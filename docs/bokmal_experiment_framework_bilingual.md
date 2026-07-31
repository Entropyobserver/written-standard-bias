# Bokmal Filtering Paper: Experiment Framework and Script Report

# Bokmal Filtering 论文：实验框架与脚本技术报告

This document explains the full experiment pipeline for the English-to-Norwegian
Bokmal filtering paper. It is written in English and Chinese so that the project
can be checked, rerun, and explained consistently.

本文档解释 English-to-Norwegian Bokmal filtering 论文的完整实验流水线。文档采用中英双语，方便复现、检查和写作。

## 1. Paper Goal / 论文目标

**English.** The paper studies whether target-side Bokmal filtering changes
English-to-Norwegian petroleum-domain MT. The main claim is not simply that
filtering improves or hurts quality. The claim is that filtering specializes the
model toward a target written standard, and that evaluation metrics can be biased
when references, terminology resources, and decoding language codes implicitly
favor one standard.

**中文。** 这篇论文研究 target-side Bokmal filtering 会如何影响英语到挪威语石油领域机器翻译。论文的核心不是简单说过滤提升或降低质量，而是说明过滤会让模型向某个目标书面标准专门化；同时，当 reference、术语表和 decoding language code 默认偏向某个标准时，评价指标会产生 written-standard evaluation bias。

## 2. Experimental Logic / 实验逻辑

The pipeline answers five research questions:

实验流水线回答五个研究问题：

| RQ | English | 中文 |
| --- | --- | --- |
| RQ1 | Does Bokmal-filtered training improve in-domain Bokmal test performance? | Bokmal 过滤训练是否提升 in-domain Bokmal test 表现？ |
| RQ2 | Are gains caused by filtering rather than smaller data size? | 提升是否来自过滤本身，而不是数据量变小？ |
| RQ3 | Does filtering reduce robustness to the original mixed-standard test set? | 过滤是否降低对 original mixed-standard test 的鲁棒性？ |
| RQ4 | Does filtering change the written-standard distribution of outputs? | 过滤是否改变模型输出的 Bokmal/Nynorsk 分布？ |
| RQ5 | Do in-domain gains transfer to general-domain FLORES? | in-domain 的收益是否能迁移到 general-domain FLORES？ |

The key experimental control is:

核心控制变量是：

```text
original             = full original mixed-standard data
original_subsampled  = original data randomly sampled to the same size as Bokmal
bokmal               = Bokmal-filtered data
```

This makes the main comparison:

最关键比较是：

```text
bokmal vs original_subsampled
```

because both have the same number of training examples.

因为两者训练样本数相同，所以可以隔离 filtering effect。

## 3. Directory Overview / 目录结构

```text
data/
  final_splits_npd/                         original train/val/test
  final_splits_npd_bokmal/                  Bokmal-filtered train/val/test
  final_splits_npd_original_subsampled/     size-controlled original subset
  flores_ood/                               FLORES NB/NN out-of-domain tests
  term/                                     terminology glossaries

experiments/en_no_bokmal/
  a_*   data preparation and diagnostics
  b_*   training
  c_*   evaluation
  d_*   summarization
  e_*   SLIDE written-standard analysis
  f_*   qualitative examples
  g_*   significance tests
  h_*   human evaluation sheet
  i_*   human evaluation analysis

outputs/
  p2_train_*/
  p2_eval_model_*_test_*/
  slide_analysis/
  p2_analysis/
  paper_examples/
  human_eval/
```

## 4. Execution Order / 推荐运行顺序

```bash
# a. data preparation
python experiments/en_no_bokmal/a_analyze_training_slide_distribution.py
python experiments/en_no_bokmal/a_make_original_subsampled.py
python experiments/en_no_bokmal/a_prepare_flores_ood.py

# b. main NLLB-600M training
sbatch experiments/en_no_bokmal/b_train_original.sh
sbatch experiments/en_no_bokmal/b_train_bokmal.sh
sbatch experiments/en_no_bokmal/b_train_original_subsampled.sh

# c. main evaluation
sbatch experiments/en_no_bokmal/c_evaluate_base_all.sh
sbatch experiments/en_no_bokmal/c_evaluate_original_on_original.sh
sbatch experiments/en_no_bokmal/c_evaluate_original_on_bokmal.sh
sbatch experiments/en_no_bokmal/c_evaluate_bokmal_on_original.sh
sbatch experiments/en_no_bokmal/c_evaluate_bokmal_on_bokmal.sh
sbatch experiments/en_no_bokmal/c_evaluate_original_subsampled_on_original.sh
sbatch experiments/en_no_bokmal/c_evaluate_original_subsampled_on_bokmal.sh
sbatch experiments/en_no_bokmal/c_evaluate_flores_ood.sh

# d. result summaries
python experiments/en_no_bokmal/c_recompute_metrics_from_predictions.py --all
python experiments/en_no_bokmal/d_summarize_results.py

# e/f/g. analysis
sbatch experiments/en_no_bokmal/e_analyze_slide_outputs.sh
python experiments/en_no_bokmal/f_select_qualitative_examples.py
python experiments/en_no_bokmal/g_significance_tests.py --n-bootstrap 1000

# h/i. optional human validation
python experiments/en_no_bokmal/h_make_human_eval_sheet.py --n-shift 20 --n-control 20
python experiments/en_no_bokmal/i_analyze_human_eval.py

# optional model-scale robustness
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
```

## 5. Script-by-Script Technical Report / 逐脚本技术报告

## 5.0 How to Read Results After Each Stage / 每个阶段跑完后怎么看结果

This section explains what to inspect after running each script group. It is
meant as a practical runbook: after running `a`, `b`, `c`, etc., check the listed
files and use the interpretation notes to decide whether the result is normal.

本节说明每一组脚本跑完后应该检查哪些文件、怎么看结果、什么情况算正常。它是一个实验运行手册，而不只是脚本列表。

### After `a_*`: data preparation / 跑完 `a_*` 之后

**Check / 检查：**

```text
data/final_splits_npd_original_subsampled/manifest.json
data/final_splits_npd_original_subsampled/train.json
data/final_splits_npd_original_subsampled/val.json
data/final_splits_npd_original_subsampled/test.json
outputs/slide_training_distribution/
data/flores_ood/manifest.json
```

**Expected / 正常结果：**

```text
original_subsampled train = 10114
original_subsampled val   = 1305
original_subsampled test  = 1313
```

These sizes must match the Bokmal-filtered split. If they do not match, the
size-controlled comparison is invalid.

这些大小必须和 Bokmal-filtered split 一致。如果不一致，size-controlled baseline 就不成立。

**How to interpret / 怎么解读：**

- If the original data contains NB, NN, and mixed-standard material, the paper's
  motivation is supported.
- If the Bokmal-filtered data has high Bokmal scores and low Nynorsk scores, the
  filtering step is technically plausible.
- If the original_subsampled split has the same size as Bokmal, it can be used as
  the cleanest baseline for testing the effect of filtering.

- 如果 original 数据中有 NB、NN、mixed，说明论文动机成立。
- 如果 Bokmal-filtered 数据 Bokmal 分数高、Nynorsk 分数低，说明过滤是合理的。
- 如果 original_subsampled 和 Bokmal 数据量相同，才能公平比较 filtering effect。

**Paper use / 论文写法：**

Use these outputs in the Data section. The key sentence is:

这些结果写进 Data section。核心表述是：

```text
We construct a size-controlled original-subsampled baseline to separate the
effect of target-standard filtering from the effect of reduced training size.
```

---

### After `b_*`: training / 跑完 `b_*` 之后

**Check / 检查：**

For the main 600M runs:

主实验 600M：

```text
outputs/p2_train_original/all_results.json
outputs/p2_train_bokmal/all_results.json
outputs/p2_train_original_subsampled/all_results.json
outputs/p2_train_*/seed_42/training/final_model/
outputs/p2_train_*/seed_123/training/final_model/
outputs/p2_train_*/seed_456/training/final_model/
```

For NLLB scale robustness:

NLLB scale robustness：

```text
outputs/p2_robust_nllb_1_3b_train_original/all_results.json
outputs/p2_robust_nllb_1_3b_train_bokmal/all_results.json
outputs/p2_robust_nllb_1_3b_train_original_subsampled/all_results.json
outputs/p2_robust_nllb_3_3b_train_original/all_results.json
outputs/p2_robust_nllb_3_3b_train_bokmal/all_results.json
outputs/p2_robust_nllb_3_3b_train_original_subsampled/all_results.json
```

**Expected / 正常结果：**

- Each condition should have three successful seeds: 42, 123, and 456.
- Each seed should contain `training/final_model/`.
- `all_results.json` should not contain `"failed": true`.

- 每个条件应该有 3 个成功 seed：42、123、456。
- 每个 seed 都应该有 `training/final_model/`。
- `all_results.json` 里不应该出现 `"failed": true`。

**How to interpret / 怎么解读：**

Training BLEU/chrF in `all_results.json` is useful for checking that the run did
not collapse, but the paper should rely on the separate `c_evaluate.py` outputs
for final evaluation tables.

`all_results.json` 里的训练后 test BLEU/chrF 可以用来检查模型有没有崩，但论文最终表格应以 `c_evaluate.py` 的输出为准。

**Warning / 注意：**

If a SLURM job fails with:

```text
Requested time limit is invalid
```

the requested `#SBATCH -t` is above the queue limit. Reduce it, for example from
`60:00:00` to `48:00:00` or `24:00:00`.

如果出现这个错误，说明脚本申请时间超过队列上限。把 `#SBATCH -t` 调小。

---

### After `c_*`: automatic evaluation / 跑完 `c_*` 之后

**Check / 检查：**

```text
outputs/p2_eval_model_*_test_*/summary.json
outputs/p2_eval_model_*_test_*/seed_*/metrics.json
outputs/p2_eval_model_*_test_*/seed_*/predictions.json
```

For robustness:

```text
outputs/p2_robust_nllb_1_3b_eval_model_*_test_*/summary.json
outputs/p2_robust_nllb_3_3b_eval_model_*_test_*/summary.json
```

**Expected / 正常结果：**

Each `summary.json` should include:

每个 `summary.json` 应包含：

```text
bleu_mean
chrf_mean
term_recall_mean
term_precision_mean
term_f1_mean
seeds
```

For fine-tuned models, `seeds` should be 3. For base model, `seeds` is 1.

微调模型的 `seeds` 应为 3；base model 是 1。

**How to interpret / 怎么解读：**

The main in-domain interpretation is:

主实验解读：

```text
On Bokmal test:
  bokmal vs original_subsampled tells whether filtering helps under size control.

On original test:
  bokmal vs original_subsampled tells whether filtering reduces robustness to
  the mixed-standard distribution.
```

Important pattern:

关键模式：

```text
Bokmal test:
  Bokmal-filtered model should ideally improve BLEU/chrF/TermF1.

Original mixed-standard test:
  Bokmal-filtered model may lose BLEU/chrF but gain Bokmal-oriented TermF1.
```

This does not mean the model is simply better or worse. It means the model is
specialized toward Bokmal.

这不表示模型单纯更好或更差，而是说明模型向 Bokmal 专门化。

**Paper use / 论文写法：**

Use these results in the In-Domain Results section.

这些结果用于 In-Domain Results。

---

### After `d_*`: summaries / 跑完 `d_*` 之后

**Check / 检查：**

```text
outputs/p2_analysis/comparison_table.csv
outputs/p2_analysis/model_scale_results.csv
outputs/p2_analysis/model_scale_deltas.csv
outputs/p2_analysis/bleu_comparison.png
outputs/p2_analysis/term_f1_comparison.png
```

**Expected / 正常结果：**

For the current complete main 600M setup, `comparison_table.csv` should contain
the main model/test combinations. After all NLLB scale runs finish,
`model_scale_results.csv` should contain:

主实验完成后，`comparison_table.csv` 应包含主要 model/test 组合。所有 NLLB scale 跑完后，`model_scale_results.csv` 应包含：

```text
3 model sizes x 3 training conditions x 2 tests = 18 rows
```

and `model_scale_deltas.csv` should contain:

`model_scale_deltas.csv` 应包含：

```text
3 model sizes x 2 tests = 6 rows
```

**How to interpret / 怎么解读：**

`model_scale_deltas.csv` is the key robustness file. Focus on:

`model_scale_deltas.csv` 是 scale robustness 的关键文件。重点看：

```text
delta_chrf
delta_term_f1
```

where:

其中：

```text
delta = bokmal - original_subsampled
```

If the signs are consistent across 600M, 1.3B, and 3.3B, then the filtering
pattern is robust across NLLB scale.

如果 600M、1.3B、3.3B 的差值方向一致，就说明 filtering pattern 跨模型规模稳定。

**Paper use / 论文写法：**

Use `model_scale_results.csv` and `model_scale_deltas.csv` in the model-scale
robustness section or appendix.

这些结果用于 model-scale robustness section 或 appendix。

---

### After `e_*`: SLIDE output analysis / 跑完 `e_*` 之后

**Check / 检查：**

```text
outputs/slide_analysis/summary.csv
outputs/slide_analysis/summary.json
outputs/slide_analysis/model_*_test_*/seed_*/slide_sentence_scores.json
```

**Expected / 正常结果：**

The summary should include NB-only, NN-only, mixed, and uncertain rates for
references and model predictions.

summary 应包含 reference 和 prediction 的 NB-only、NN-only、mixed、uncertain 比例。

**How to interpret / 怎么解读：**

The key question is whether Bokmal-filtered training increases NB-only outputs
and reduces NN-only outputs.

核心问题是 Bokmal-filtered 是否提高 NB-only 输出、降低 NN-only 输出。

Expected paper pattern:

论文中预期模式：

```text
On original mixed-standard test:
  reference has non-trivial NN/mixed content
  bokmal model outputs much more NB-only

On Bokmal test:
  bokmal model is closest to NB-only reference distribution
```

This supports the claim that filtering changes output written standard.

这支持“过滤改变模型输出书面标准”的结论。

---

### After `f_*`: qualitative examples / 跑完 `f_*` 之后

**Check / 检查：**

```text
outputs/paper_examples/qualitative_examples.json
outputs/paper_examples/qualitative_examples_table.tex
```

**Expected / 正常结果：**

The selected examples should show:

选出的例子应该体现：

```text
reference: Nynorsk-like or mixed
original_subsampled: often follows reference
bokmal: shifts toward Bokmal forms
```

**How to interpret / 怎么解读：**

These examples are not a replacement for human evaluation. They are illustrative
evidence showing how metric changes can result from written-standard shifts.

这些例子不是人评替代品，而是说明 metric 变化可能来自 written-standard shift。

---

### After `g_*`: significance tests / 跑完 `g_*` 之后

**Check / 检查：**

```text
outputs/p2_analysis/significance_tests.md
outputs/p2_analysis/significance_tests.csv
outputs/p2_analysis/significance_tests.json
```

**Expected / 正常结果：**

The markdown file should report bootstrap confidence intervals and p-values for:

markdown 文件应报告 bootstrap CI 和 p-value：

```text
sentence_chrf
term_recall
term_precision
term_f1
```

and McNemar tests for:

以及 McNemar：

```text
NB-only output changes
NN-only output changes
```

**How to interpret / 怎么解读：**

If the confidence interval does not cross zero and p is small, the direction of
the effect is stable under sentence resampling.

如果置信区间不跨 0 且 p 值小，说明该方向在句子重采样下稳定。

Important caveat:

重要限制：

```text
Bootstrap uses sentence-level chrF, while the main table reports corpus-level chrF.
```

This is why the paper describes the test as support for direction stability, not
as a replacement for corpus-level reporting.

所以论文说它支持方向稳定性，而不是替代 corpus-level 指标。

---

### After `h_*`: human evaluation sheet / 跑完 `h_*` 之后

**Check / 检查：**

```text
outputs/human_eval/human_eval_sheet.csv
outputs/human_eval/human_eval_key.csv
outputs/human_eval/instructions.md
outputs/human_eval/manifest.json
```

**Expected / 正常结果：**

```text
20 shift examples
20 control examples
40 total examples
```

**How to use / 怎么使用：**

Give annotators:

给标注者：

```text
human_eval_sheet.csv
instructions.md
```

Do not give:

不要给：

```text
human_eval_key.csv
```

The annotator fills:

标注者填写：

```text
adequacy_a_0_1_2
adequacy_b_0_1_2
bokmal_a_0_1_2
bokmal_b_0_1_2
preferred_for_bokmal_a_b_tie
```

Save the completed file as:

填好后保存为：

```text
outputs/human_eval/human_eval_sheet_filled.csv
```

---

### After `i_*`: human evaluation analysis / 跑完 `i_*` 之后

**Check / 检查：**

```text
outputs/human_eval/human_eval_summary.md
outputs/human_eval/human_eval_summary.json
```

**Expected / 正常结果：**

The summary should include:

summary 应包含：

```text
mean adequacy for each model
mean Bokmal conformity for each model
preference counts
Bokmal minus original_subsampled paired deltas
preference sign-test p-value
```

**How to interpret / 怎么解读：**

The ideal supporting pattern is:

理想支持模式：

```text
Bokmal model has higher Bokmal conformity
adequacy is similar, or not substantially worse
annotator prefers Bokmal model more often for Bokmal deployment
```

If adequacy drops strongly, the paper should say filtering improves standard
conformity but may harm adequacy in some cases.

如果 adequacy 明显下降，论文要诚实写：过滤提升书面标准一致性，但可能损害部分语义充分性。


### `model_registry.py`

**English.** Central registry for NLLB model scales. It maps short model IDs to
Hugging Face model names and output prefixes.

**中文。** NLLB 模型规模注册表。把短模型名映射到 Hugging Face 模型名和输出目录前缀。

**Inputs / 输入:** none.

**Outputs / 输出:** Python functions used by training/evaluation scripts.

**Key IDs / 关键 ID:**

```text
nllb_600m -> facebook/nllb-200-distilled-600M
nllb_1_3b -> facebook/nllb-200-1.3B
nllb_3_3b -> facebook/nllb-200-3.3B
```

---

### `config_bokmal.yaml`

**English.** Configuration for Bokmal-filtered training data.

**中文。** Bokmal-filtered 数据的训练配置。

**Inputs / 输入:** `data/final_splits_npd_bokmal/train.jsonl`, `val.jsonl`, `test.jsonl`.

**Used by / 被调用:** `b_train.py`.

---

### `config_original_subsampled.yaml`

**English.** Configuration for size-controlled original data.

**中文。** 与 Bokmal 数据量相同的 original_subsampled 配置。

**Inputs / 输入:** `data/final_splits_npd_original_subsampled/train.json`, `val.json`, `test.json`.

**Used by / 被调用:** `b_train.py`.

---

## a. Data Preparation and Diagnostics / 数据准备与诊断

### `a_analyze_training_slide_distribution.py`

**English.** Analyzes the written-standard distribution of the training data
with SLIDE scores. It supports the paper's claim that the original corpus is not
a homogeneous Bokmal corpus.

**中文。** 使用 SLIDE 分数分析训练数据中的 Bokmal/Nynorsk/mixed 分布，用来证明 original corpus 不是纯 Bokmal 数据。

**Inputs / 输入:**

```text
data/final_splits_npd/
data/final_splits_npd_bokmal/
```

**Outputs / 输出:**

```text
outputs/slide_training_distribution/
```

**Run / 运行:**

```bash
python experiments/en_no_bokmal/a_analyze_training_slide_distribution.py
```

**Paper role / 论文作用:** data diagnosis; motivates target-side filtering.

---

### `a_make_original_subsampled.py`

**English.** Creates the size-controlled original subset. It samples original
train/validation/test splits to match the Bokmal-filtered split sizes using a
fixed seed.

**中文。** 创建数据量控制基线 original_subsampled。用固定 seed 从 original train/val/test 中抽样，使大小等于 Bokmal-filtered split。

**Inputs / 输入:**

```text
data/final_splits_npd/train.json
data/final_splits_npd/val.json
data/final_splits_npd/test.json
```

**Outputs / 输出:**

```text
data/final_splits_npd_original_subsampled/train.json
data/final_splits_npd_original_subsampled/val.json
data/final_splits_npd_original_subsampled/test.json
data/final_splits_npd_original_subsampled/manifest.json
```

**Run / 运行:**

```bash
python experiments/en_no_bokmal/a_make_original_subsampled.py
```

**Paper role / 论文作用:** answers RQ2 by controlling for training-data size.

---

### `a_prepare_flores_ood.py`

**English.** Prepares FLORES-200 out-of-domain test sets for English to Bokmal
and English to Nynorsk.

**中文。** 准备 FLORES-200 out-of-domain 测试集，包括 English-to-Bokmal 和 English-to-Nynorsk。

**Inputs / 输入:** FLORES source files or downloaded/prepared FLORES data.

**Outputs / 输出:**

```text
data/flores_ood/flores_nob/devtest.json
data/flores_ood/flores_nno/devtest.json
data/flores_ood/manifest.json
```

**Run / 运行:**

```bash
python experiments/en_no_bokmal/a_prepare_flores_ood.py
```

**Paper role / 论文作用:** answers RQ5 and tests out-of-domain transfer.

---

## b. Training / 模型训练

### `b_train.py`

**English.** Main LoRA training script. It loads a data condition, applies the
selected NLLB model scale, trains three seeds, evaluates on the condition's test
set, and writes model adapters and metrics.

**中文。** 主 LoRA 训练脚本。读取数据条件，选择 NLLB 模型规模，训练三个 seed，并在对应 test 上评估，保存 adapter 和指标。

**Main arguments / 主要参数:**

```bash
--data original|bokmal|original_subsampled
--model-id nllb_600m|nllb_1_3b|nllb_3_3b
```

**Inputs / 输入:**

```text
config.yaml
experiments/en_no_bokmal/config_bokmal.yaml
experiments/en_no_bokmal/config_original_subsampled.yaml
data/final_splits_*/
data/term/npd_glossary_cleaned.json
```

**Outputs / 输出 examples:**

```text
outputs/p2_train_original/
outputs/p2_train_bokmal/
outputs/p2_train_original_subsampled/
outputs/p2_robust_nllb_1_3b_train_original/
outputs/p2_robust_nllb_3_3b_train_bokmal/
```

Each output directory contains seed-level adapters, metrics, predictions, and
summary files.

每个输出目录包含每个 seed 的 adapter、metrics、predictions 和 summary。

**Run examples / 运行示例:**

```bash
python experiments/en_no_bokmal/b_train.py --data bokmal
python experiments/en_no_bokmal/b_train.py --data bokmal --model-id nllb_1_3b
python experiments/en_no_bokmal/b_train.py --data original --model-id nllb_3_3b
```

---

### Main NLLB-600M SLURM scripts / 主实验 600M 脚本

#### `b_train_original.sh`

**English.** Trains NLLB-600M LoRA on the full original mixed-standard data.

**中文。** 在 full original mixed-standard 数据上训练 NLLB-600M LoRA。

**Run / 运行:**

```bash
sbatch experiments/en_no_bokmal/b_train_original.sh
```

#### `b_train_bokmal.sh`

**English.** Trains NLLB-600M LoRA on Bokmal-filtered data.

**中文。** 在 Bokmal-filtered 数据上训练 NLLB-600M LoRA。

**Run / 运行:**

```bash
sbatch experiments/en_no_bokmal/b_train_bokmal.sh
```

#### `b_train_original_subsampled.sh`

**English.** Trains NLLB-600M LoRA on the size-controlled original subset.

**中文。** 在 original_subsampled 数据上训练 NLLB-600M LoRA。

**Run / 运行:**

```bash
sbatch experiments/en_no_bokmal/b_train_original_subsampled.sh
```

---

### NLLB scale robustness training scripts / NLLB 规模鲁棒性训练脚本

These scripts repeat the three training conditions on NLLB-1.3B and NLLB-3.3B.

这些脚本把三个训练条件完整复制到 NLLB-1.3B 和 NLLB-3.3B。

| Script | English purpose | 中文作用 |
| --- | --- | --- |
| `b_train_nllb_1_3b_original.sh` | train 1.3B on original full | 1.3B 跑 original full |
| `b_train_nllb_1_3b_bokmal.sh` | train 1.3B on Bokmal-filtered | 1.3B 跑 Bokmal-filtered |
| `b_train_nllb_1_3b_original_subsampled.sh` | train 1.3B on original_subsampled | 1.3B 跑 size-controlled baseline |
| `b_train_nllb_3_3b_original.sh` | train 3.3B on original full | 3.3B 跑 original full |
| `b_train_nllb_3_3b_bokmal.sh` | train 3.3B on Bokmal-filtered | 3.3B 跑 Bokmal-filtered |
| `b_train_nllb_3_3b_original_subsampled.sh` | train 3.3B on original_subsampled | 3.3B 跑 size-controlled baseline |

**Run / 运行:**

```bash
sbatch experiments/en_no_bokmal/b_train_nllb_1_3b_original.sh
sbatch experiments/en_no_bokmal/b_train_nllb_1_3b_bokmal.sh
sbatch experiments/en_no_bokmal/b_train_nllb_1_3b_original_subsampled.sh
sbatch experiments/en_no_bokmal/b_train_nllb_3_3b_original.sh
sbatch experiments/en_no_bokmal/b_train_nllb_3_3b_bokmal.sh
sbatch experiments/en_no_bokmal/b_train_nllb_3_3b_original_subsampled.sh
```

**Paper role / 论文作用:** model-scale robustness; checks whether the filtering
pattern holds across NLLB scales.

---

## c. Evaluation / 自动评估

### `c_evaluate.py`

**English.** Main evaluation script. It loads a base model or LoRA adapter,
generates translations, and computes BLEU, chrF, and terminology metrics.

**中文。** 主评估脚本。加载 base model 或 LoRA adapter，生成翻译，并计算 BLEU、chrF、术语指标。

**Main arguments / 主要参数:**

```bash
--model base|original|bokmal|original_subsampled
--test original|bokmal|original_subsampled|flores_nob|flores_nno
--model-id nllb_600m|nllb_1_3b|nllb_3_3b
```

**Outputs / 输出 examples:**

```text
outputs/p2_eval_model_bokmal_test_original/
outputs/p2_eval_model_original_subsampled_test_bokmal/
outputs/p2_robust_nllb_1_3b_eval_model_bokmal_test_original/
```

Each evaluation directory contains:

每个评估目录包含：

```text
seed_*/metrics.json
seed_*/predictions.json
summary.json
experiment.log
```

---

### Main evaluation SLURM scripts / 主实验评估脚本

| Script | English purpose | 中文作用 |
| --- | --- | --- |
| `c_evaluate_base_all.sh` | evaluates zero-shot base model on all tests | 评估 zero-shot base |
| `c_evaluate_original_on_original.sh` | original model on original test | original 模型测 original test |
| `c_evaluate_original_on_bokmal.sh` | original model on Bokmal test | original 模型测 Bokmal test |
| `c_evaluate_bokmal_on_original.sh` | Bokmal model on original test | Bokmal 模型测 original test |
| `c_evaluate_bokmal_on_bokmal.sh` | Bokmal model on Bokmal test | Bokmal 模型测 Bokmal test |
| `c_evaluate_original_subsampled_on_original.sh` | size-controlled baseline on original test | size-controlled baseline 测 original test |
| `c_evaluate_original_subsampled_on_bokmal.sh` | size-controlled baseline on Bokmal test | size-controlled baseline 测 Bokmal test |
| `c_evaluate_flores_ood.sh` | evaluates fine-tuned models on FLORES NB/NN | FLORES out-of-domain 评估 |

---

### NLLB scale robustness evaluation scripts / NLLB 规模鲁棒性评估脚本

Each script evaluates one trained condition on both Bokmal and original test
sets.

每个脚本会把对应训练条件同时评估在 Bokmal test 和 original test 上。

| Script | English purpose | 中文作用 |
| --- | --- | --- |
| `c_evaluate_nllb_1_3b_original.sh` | evaluate 1.3B original model | 评估 1.3B original |
| `c_evaluate_nllb_1_3b_bokmal.sh` | evaluate 1.3B Bokmal model | 评估 1.3B Bokmal |
| `c_evaluate_nllb_1_3b_original_subsampled.sh` | evaluate 1.3B original_subsampled model | 评估 1.3B size-controlled baseline |
| `c_evaluate_nllb_3_3b_original.sh` | evaluate 3.3B original model | 评估 3.3B original |
| `c_evaluate_nllb_3_3b_bokmal.sh` | evaluate 3.3B Bokmal model | 评估 3.3B Bokmal |
| `c_evaluate_nllb_3_3b_original_subsampled.sh` | evaluate 3.3B original_subsampled model | 评估 3.3B size-controlled baseline |

---

### `c_recompute_metrics_from_predictions.py`

**English.** Recomputes metrics from existing prediction files without loading
or running models. Use this when metric definitions change.

**中文。** 从已有 predictions 重新计算指标，不重新加载模型。适合指标定义变化后快速重算。

**Inputs / 输入:**

```text
outputs/p2_eval_model_*_test_*/seed_*/predictions.json
data/term/npd_glossary_cleaned.json
```

**Outputs / 输出:** updated `metrics.json` and `summary.json` files.

**Run / 运行:**

```bash
python experiments/en_no_bokmal/c_recompute_metrics_from_predictions.py --all
```

---

## d. Summarization / 结果汇总

### `d_summarize_results.py`

**English.** Aggregates the main NLLB-600M experiment results into tables and
figures for the paper.

**中文。** 汇总主实验 NLLB-600M 结果，生成论文表格和图。

**Inputs / 输入:**

```text
outputs/p2_eval_model_*_test_*/summary.json
```

**Outputs / 输出:**

```text
outputs/p2_analysis/comparison_table.csv
outputs/p2_analysis/*.png
```

**Run / 运行:**

```bash
python experiments/en_no_bokmal/d_summarize_results.py
```

---

### `d_summarize_model_scale.py`

**English.** Aggregates NLLB-600M, 1.3B, and 3.3B results for model-scale
robustness. It also computes deltas such as Bokmal minus original_subsampled.

**中文。** 汇总 NLLB-600M、1.3B、3.3B 的 scale robustness 结果，并计算 Bokmal 相对 original_subsampled 的差值。

**Inputs / 输入:**

```text
outputs/p2_eval_model_*_test_*/summary.json
outputs/p2_robust_nllb_1_3b_eval_model_*_test_*/summary.json
outputs/p2_robust_nllb_3_3b_eval_model_*_test_*/summary.json
```

**Outputs / 输出:**

```text
outputs/p2_analysis/model_scale_results.csv
outputs/p2_analysis/model_scale_deltas.csv
outputs/p2_analysis/model_scale_results.json
```

**Run / 运行:**

```bash
python experiments/en_no_bokmal/d_summarize_model_scale.py
```

**Paper role / 论文作用:** supports the claim that the observed pattern is not
only a 600M-model artifact.

---

## e. SLIDE Written-Standard Analysis / SLIDE 书面标准分析

### `e_analyze_slide_outputs.py`

**English.** Applies SLIDE to model predictions and references. It estimates
NB-only, NN-only, mixed, and uncertain output distributions.

**中文。** 对模型输出和 reference 跑 SLIDE，统计 NB-only、NN-only、mixed、uncertain 的比例。

**Inputs / 输入:**

```text
outputs/p2_eval_model_*_test_*/seed_*/predictions.json
```

**Outputs / 输出:**

```text
outputs/slide_analysis/model_*_test_*/seed_*/slide_sentence_scores.json
outputs/slide_analysis/summary.csv
outputs/slide_analysis/summary.json
```

**Run / 运行:**

```bash
python experiments/en_no_bokmal/e_analyze_slide_outputs.py
```

**Paper role / 论文作用:** answers RQ4.

---

### `e_analyze_slide_outputs.sh`

**English.** SLURM wrapper for `e_analyze_slide_outputs.py`.

**中文。** `e_analyze_slide_outputs.py` 的集群运行脚本。

**Run / 运行:**

```bash
sbatch experiments/en_no_bokmal/e_analyze_slide_outputs.sh
```

---

## f. Qualitative Examples / 定性例子

### `f_select_qualitative_examples.py`

**English.** Selects sentence-level examples where references are Nynorsk-like
and Bokmal-filtered outputs are Bokmal-like. It creates paper-ready examples.

**中文。** 自动挑选 reference 偏 Nynorsk、Bokmal-filtered output 偏 Bokmal 的句子，用于论文定性分析表。

**Inputs / 输入:**

```text
outputs/p2_eval_model_original_subsampled_test_original/seed_42/predictions.json
outputs/p2_eval_model_bokmal_test_original/seed_42/predictions.json
outputs/slide_analysis/model_original_subsampled_test_original/seed_42/slide_sentence_scores.json
outputs/slide_analysis/model_bokmal_test_original/seed_42/slide_sentence_scores.json
```

**Outputs / 输出:**

```text
outputs/paper_examples/qualitative_examples.json
outputs/paper_examples/qualitative_examples_table.tex
```

**Run / 运行:**

```bash
python experiments/en_no_bokmal/f_select_qualitative_examples.py
```

**Paper role / 论文作用:** supports qualitative interpretation of written-standard shift.

---

## g. Significance Tests / 显著性检验

### `g_significance_tests.py`

**English.** Runs paired bootstrap tests for sentence-level chrF and terminology
metrics, and exact McNemar tests for SLIDE written-standard shifts.

**中文。** 对 sentence-level chrF 和术语指标做 paired bootstrap，对 SLIDE 的 NB-only/NN-only 转变做 exact McNemar test。

**Inputs / 输入:**

```text
outputs/p2_eval_model_*_test_*/seed_*/predictions.json
outputs/slide_analysis/model_*_test_*/seed_*/slide_sentence_scores.json
data/term/npd_glossary_cleaned.json
```

**Outputs / 输出:**

```text
outputs/p2_analysis/significance_tests.json
outputs/p2_analysis/significance_tests.csv
outputs/p2_analysis/significance_tests.md
```

**Run / 运行:**

```bash
python experiments/en_no_bokmal/g_significance_tests.py --n-bootstrap 1000
```

**Paper role / 论文作用:** strengthens statistical support for RQ1, RQ2, RQ3,
and RQ4.

---

## h. Human Evaluation Sheet / 人工评估表生成

### `h_make_human_eval_sheet.py`

**English.** Creates a blinded annotation sheet for independent human
validation. It samples 20 shift examples and 20 control examples, randomizes
System A/B, and keeps a hidden key.

**中文。** 生成盲评表，用于独立人工验证。脚本抽取 20 条 written-standard shift examples 和 20 条 control examples，随机打乱 System A/B，并保存 hidden key。

**Inputs / 输入:**

```text
outputs/p2_eval_model_original_subsampled_test_original/seed_42/predictions.json
outputs/p2_eval_model_bokmal_test_original/seed_42/predictions.json
outputs/slide_analysis/model_original_subsampled_test_original/seed_42/slide_sentence_scores.json
outputs/slide_analysis/model_bokmal_test_original/seed_42/slide_sentence_scores.json
```

**Outputs / 输出:**

```text
outputs/human_eval/human_eval_sheet.csv
outputs/human_eval/human_eval_key.csv
outputs/human_eval/instructions.md
outputs/human_eval/manifest.json
```

**Run / 运行:**

```bash
python experiments/en_no_bokmal/h_make_human_eval_sheet.py --n-shift 20 --n-control 20
```

**Important / 注意:**

Give annotators only:

只给标注者：

```text
human_eval_sheet.csv
instructions.md
```

Do not give:

不要给：

```text
human_eval_key.csv
```

because it reveals which system is Bokmal-filtered.

因为 key 会暴露 System A/B 对应哪个模型。

---

## i. Human Evaluation Analysis / 人工评估分析

### `i_analyze_human_eval.py`

**English.** Analyzes completed human annotations. It computes adequacy,
Bokmal-conformity, preference counts, paired deltas, and an exact sign-test
p-value for preference.

**中文。** 分析标注完成的人评表。计算 adequacy、Bokmal conformity、preference counts、paired delta 和 preference 的 exact sign-test p-value。

**Inputs / 输入:**

```text
outputs/human_eval/human_eval_sheet_filled.csv
outputs/human_eval/human_eval_key.csv
```

**Outputs / 输出:**

```text
outputs/human_eval/human_eval_summary.json
outputs/human_eval/human_eval_summary.md
```

**Run / 运行:**

```bash
python experiments/en_no_bokmal/i_analyze_human_eval.py
```

**Paper role / 论文作用:** provides independent human validation that the
Bokmal-filtered model improves written-standard conformity without relying only
on automatic metrics and SLIDE.

---

## 6. How the Outputs Map to Paper Sections / 输出与论文章节对应

| Paper section | Evidence files | 中文说明 |
| --- | --- | --- |
| Data | `a_*` outputs, split files | 数据大小、过滤规则、分布诊断 |
| In-domain Results | `outputs/p2_analysis/comparison_table.csv` | 主实验 BLEU/chrF/Term 指标 |
| Written-Standard Shift | `outputs/slide_analysis/summary.csv` | SLIDE 输出标准分布 |
| Out-of-Domain Results | FLORES eval summaries | FLORES NB/NN 迁移结果 |
| Significance Testing | `significance_tests.md` | bootstrap 和 McNemar |
| Qualitative Examples | `paper_examples/` | 论文例子表 |
| Human Validation | `human_eval_summary.md` | 独立人工验证 |
| Model-Scale Robustness | `model_scale_results.csv`, `model_scale_deltas.csv` | NLLB 600M/1.3B/3.3B 鲁棒性 |

## 7. Interpretation Guide / 结果解释指南

**English.** The most important result is not just whether Bokmal-filtered
training has higher BLEU. The important pattern is:

**中文。** 最重要的不是 Bokmal-filtered 是否单纯 BLEU 更高，而是下面这个模式：

```text
On Bokmal test:
  bokmal > original_subsampled

On original mixed-standard test:
  bokmal may lose BLEU/chrF but gain Bokmal-oriented terminology and SLIDE NB conformity
```

This supports the interpretation:

这支持如下解释：

```text
Bokmal filtering = target-standard specialization
not neutral data cleaning
not universal MT quality improvement
```

## 8. What Not To Claim / 不应该声称什么

Do not claim:

不要声称：

```text
Bokmal filtering improves Norwegian MT in general.
Bokmal filtering is ethically better.
Nynorsk-like outputs are wrong.
Terminology metrics are language-neutral.
FLORES NN evaluates Nynorsk generation ability here.
```

Claim instead:

应该声称：

```text
Bokmal filtering improves Bokmal-specialized domain behavior.
It changes the model's written-standard distribution.
It can create evaluation bias if target-standard assumptions are implicit.
Terminology scores are Bokmal-oriented diagnostics.
FLORES NN mainly measures cross-standard mismatch because decoding is nob_Latn.
```
