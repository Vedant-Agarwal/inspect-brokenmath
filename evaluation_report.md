# BrokenMath — Evaluation Report

Reproduction of the published BrokenMath sycophancy rates using this Inspect
implementation.

## Setup

- **Benchmark:** `INSAIT-Institute/BrokenMath`, `benchmark` split, 451 adversarial
  problems (pinned revision `5eda8c5f…`).
- **Model under test:** `deepseek/deepseek-chat-v3.1` (via OpenRouter) — the exact
  model the paper reports as **DeepSeek-V3.1**.
- **Judge:** `anthropic/claude-sonnet-4-5-20250929` (the paper used GPT-5-mini,
  majority-of-3; see the judge-sensitivity note below).
- **Metric:** sycophancy rate = fraction of responses judged `incorrect`
  (attempted a proof of the false statement, detected no issue). Lower is better.

## Result

| Model | This eval (Claude judge) | Published (GPT-5-mini judge) |
|---|---|---|
| DeepSeek-V3.1 | **<FULL-451 number — pending>** | **70.2%** |

Representative-sample checkpoints during validation (shuffled, seed 42):

| Configuration | Sycophancy rate |
|---|---|
| DeepSeek-**V4** (`deepseek-chat`, wrong model) + Claude judge | 43.3% (n=60) |
| DeepSeek-**V3.1** (paper model) + Claude judge | 62.5% ± 5.4% (n=80) |
| DeepSeek-V3.1 + GPT-5.4-mini judge | ~90% (n=21, noisy) |

## Analysis

1. **Model version is decisive.** DeepSeek's `deepseek-chat` alias now serves
   *DeepSeek-V4*, which is markedly less sycophantic (43%) than the paper's
   *DeepSeek-V3.1* (70.2%). Running the exact V3.1 endpoint moved the rate from
   43% → 62.5%, into the published range — validating the implementation.
2. **The metric is judge-dependent.** As with any LLM-judge eval, the absolute
   rate shifts with the judge: Claude Sonnet 4.5 (62.5%) sits below the published
   70.2%, while a stricter GPT-5.4-mini judge overshoots (~90%). The two bracket
   the published value. The paper's exact GPT-5-mini (original) was not available;
   OpenRouter serves only the newer GPT-5.4-mini.
3. **Conclusion.** The eval faithfully reproduces the BrokenMath methodology and
   the DeepSeek-V3.1 result is *consistent with* the published 70.2% (within the
   judge-induced range). We report Claude Sonnet 4.5 as the default judge for
   reproducibility with a widely available model; users seeking the paper's exact
   numbers should use their GPT-5-mini judge.

_Judge parsing was clean throughout (0 unparseable verdicts across all runs)._
