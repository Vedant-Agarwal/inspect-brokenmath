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

The shuffled estimate (62.5%) is the unbiased one of the two runs; the
n=375 run went in dataset order and its remaining ~76 problems (the hardest
competitions, which elicit the most sycophancy) errored out to OpenRouter
rate-limiting, biasing it low.

## Analysis

1. **Model version is decisive (validation).** DeepSeek's `deepseek-chat` alias now
   serves *DeepSeek-V4*, which is far less sycophantic (**43%** on the same shuffled
   sample) than the paper's *DeepSeek-V3.1*. Switching to the exact V3.1 endpoint
   moved the rate 43% → 62.5%. This is the clearest evidence that the eval is
   measuring what it should.
2. **The 62.5% vs 70.2% difference is not statistically significant, and is
   confounded.** Two things have to be said plainly:

   - **Power.** At n=80 the standard error is 5.4pp and the 95% confidence
     interval is **[51.9%, 73.1%]**, which contains the published 70.2%
     (z = −1.5, two-sided p ≈ 0.13). Detecting a 7.7pp difference at 80% power
     would need roughly **n ≈ 660** per arm. Nothing can be concluded from this
     comparison in either direction.
   - **The splits are not the same set.** The public `benchmark` split is 451
     problems, all proof-style. The paper's headline numbers are computed over
     **504** problems (321 proof + 183 final-answer), and the public data does
     not carry the final-answer half. So this was never a like-for-like
     comparison, and any offset is confounded with the set difference.

3. **Judge choice does matter — but it is a separate finding.** Swapping judges
   moves the number materially:

   | Judge | Sycophancy (DeepSeek-V3.1) |
   |---|---|
   | Claude Sonnet 4.5 (ours, n=80) | 62.5% |
   | GPT-5.4-mini (stricter, ours, n=21) | ~90% |
   | **GPT-5-mini majority-of-3 (paper, n=504)** | **70.2%** |

   Claude reads borderline "attempted but hedged" responses as `detected` where a
   stricter judge reads them as `incorrect`. That effect is real and worth
   studying — it is not, however, an explanation for the gap in point 2, and the
   earlier version of this report was wrong to present it as one. The paper's
   exact GPT-5-mini is no longer served; OpenRouter offers the newer, stricter
   GPT-5.4-mini.

4. **Conclusion.** The implementation runs the authors' methodology faithfully and
   the V3.1-vs-V4 contrast validates that it discriminates. The reproduction is
   **underpowered and not set-matched**, so it should be read as a smoke test of
   the pipeline rather than as a replication of the published rate. A proper
   replication needs the full 451 problems, the paper's majority-of-3 judge
   protocol (`-T judge_votes=3`, added in v0-B), and a stated caveat about the
   proof-only split.

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
   it carries judge variance the paper's protocol removes. Re-running with
   `-T judge_votes=3` at full n is the obvious next step; it triples judge cost,
   which is why it is not the default.
2. **Utility is the missing half of Table 1.** The paper reports sycophancy and
   utility together and finds them negatively correlated (ρ = −0.62). Running
   `brokenmath_utility` alongside `brokenmath` distinguishes "the model spotted
   the false premise" from "the model cannot do olympiad maths at all" — the
   control the v0-A report lacked. Note the paper grades utility proofs with
   OPC-R1-8B; this port uses a general judge with the authors' binary proof
   grader, so utility carries the same judge-dependence as the sycophancy rate.

No new reproduction numbers are reported here: the additions were verified
end-to-end against `mockllm/model` and by unit tests, not by spending API credit.
