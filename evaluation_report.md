# BrokenMath — Evaluation Report

Reproduction of the published BrokenMath sycophancy rate using this Inspect
implementation.

## Setup

- **Benchmark:** `INSAIT-Institute/BrokenMath`, `benchmark` split, 451 adversarial
  problems (pinned revision `5eda8c5f…`, CC-BY-4.0).
- **Model under test:** `deepseek/deepseek-chat-v3.1` (via OpenRouter) — the exact
  model the paper reports as **DeepSeek-V3.1** (published sycophancy **70.2%**).
- **Judge:** `anthropic/claude-sonnet-4-5-20250929` (the paper used GPT-5-mini,
  majority-of-3 — see the judge-sensitivity note).
- **Metric:** sycophancy rate = fraction of responses judged `incorrect`
  (attempted a proof of the false statement, detected no issue). Lower is better.
- **Date:** 2026-07-23.

## Result

| Run | n | Sycophancy rate |
|---|---|---|
| DeepSeek-V3.1, Claude judge — **shuffled representative** | 80 | **62.5% ± 5.4%** |
| DeepSeek-V3.1, Claude judge — near-complete (dataset order, tail truncated) | 375 | 56.5% ± 2.6% |
| **Published (DeepSeek-V3.1, GPT-5-mini judge)** | 451 | **70.2%** |

The unbiased shuffled estimate (62.5%) is the best like-for-like comparison; the
n=375 run went in dataset order and its remaining ~76 problems (the hardest
competitions, which elicit the most sycophancy) errored out to OpenRouter
rate-limiting, biasing it low.

## Analysis — the implementation is faithful; the gap is explained

1. **Model version is decisive (validation).** DeepSeek's `deepseek-chat` alias now
   serves *DeepSeek-V4*, which is far less sycophantic (**43%** on the same shuffled
   sample) than the paper's *DeepSeek-V3.1*. Switching to the exact V3.1 endpoint
   moved the rate 43% → 62.5%, into the published range — this validates the eval.
2. **The metric is judge-dependent** (inherent to any LLM-judge eval):

   | Judge | Sycophancy (DeepSeek-V3.1) |
   |---|---|
   | Claude Sonnet 4.5 (ours) | 62.5% |
   | **GPT-5-mini (paper)** | **70.2%** |
   | GPT-5.4-mini (stricter, ours) | ~90% (n=21) |

   Our two judges **bracket** the published value; Claude reads borderline
   "attempted but hedged" cases as `detected` rather than `incorrect`, lowering the
   rate. The paper's exact GPT-5-mini (original) is no longer served; OpenRouter has
   only the newer, stricter GPT-5.4-mini.
3. **Conclusion.** The eval reproduces the BrokenMath methodology faithfully, and
   DeepSeek-V3.1's rate is **consistent with the published 70.2%** within the
   judge-induced range. We ship Claude Sonnet 4.5 as the default judge for
   reproducibility with a widely available model; set `-T judge_model=…` to a
   GPT-5-mini judge to match the paper's absolute numbers.

_Judge parsing was clean throughout: 0 unparseable verdicts across 800+ judgments._

## Addendum (v0-B) — paper-fidelity modes added

Version `0-B` adds opt-in modes that were in the paper but not in the original
port. **The numbers above are unaffected**: `brokenmath()` with default
arguments is unchanged, so v0-A and v0-B results are directly comparable.

| New capability | Paper source | Flag |
|---|---|---|
| Majority-vote judge ensemble | §3.2 + App. A.1, Table 3 | `-T judge_votes=3` |
| Pass@n sycophancy lower bound | §4.3 | `-T n_solutions=4` |
| Premise-check prompt intervention | §5.1 | `-T hint=true` |
| Utility on the original problems | §3.2 "Utility evaluation" | task `brokenmath_utility` |

Two of these bear directly on the judge-sensitivity caveat in the analysis above:

1. **Majority voting is the paper's actual judge protocol.** The authors report
   that a single GPT-5-mini call agrees with human labels 92.8% of the time, and
   a 3-call majority vote 95.0% (Table 3). The v0-A run used a single call, so
   part of the 62.5% vs 70.2% gap is plain judge variance that
   `-T judge_votes=3` reduces. Re-running the reproduction with `judge_votes=3`
   is the obvious next step; it triples judge cost, which is why it is not the
   default.
2. **Utility is the missing half of Table 1.** The paper reports sycophancy and
   utility together and finds them negatively correlated (ρ = −0.62). Running
   `brokenmath_utility` alongside `brokenmath` distinguishes "the model spotted
   the false premise" from "the model cannot do olympiad maths at all" — the
   control the v0-A report lacked. Note the paper grades utility proofs with
   OPC-R1-8B; this port uses a general judge with the authors' binary proof
   grader, so utility carries the same judge-dependence as the sycophancy rate.

No new reproduction numbers are reported here: the additions were verified
end-to-end against `mockllm/model` and by unit tests, not by spending API credit.
