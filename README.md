# BrokenMath (Inspect AI)

An [Inspect AI](https://inspect.aisi.org.uk/) implementation of **BrokenMath** —
a benchmark for **sycophancy in LLM theorem proving**
(Petrov et al., *NeurIPS 2025 Datasets & Benchmarks*,
[arXiv:2510.04721](https://arxiv.org/abs/2510.04721)).

## What it measures

BrokenMath takes 451 recent olympiad problems and **adversarially modifies each
into a false statement**. The model is asked to prove the (false) theorem. A
**sycophantic** model plays along and produces a bogus "proof" instead of
flagging the flawed premise — a safety-relevant failure mode adjacent to
deceptive alignment.

- **Solver:** single-turn `generate()` — the model is asked to prove the false
  statement (proof-writing instructions verbatim from the authors).
- **Scorer:** an LLM judge applies the authors' **4-way rubric** and classifies
  each response as `correct` / `detected` / `corrected` / `incorrect`.
- **Metric — sycophancy rate:** the fraction judged `incorrect` (the model
  attempted a proof and detected no issue). **Lower is better.**

## Running

```bash
uv sync
# solver = model under test; judge = model that applies the rubric
uv run inspect eval brokenmath \
  --model openrouter/deepseek/deepseek-chat-v3.1 \
  -T judge_model=anthropic/claude-sonnet-4-5-20250929
```

Set the relevant provider keys (`OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`, …).

## Data & pinning

- **Dataset:** HF [`INSAIT-Institute/BrokenMath`](https://huggingface.co/datasets/INSAIT-Institute/BrokenMath)
  (`benchmark` split, 451 problems), **CC-BY-4.0**, loaded with a pinned `revision=`.
  All problems are fully public with `original_problem` + ground-truth `solution`.
- **Judge prompt:** the 4-way checker in `src/brokenmath/prompts/checker.txt` is
  vendored verbatim from [`insait-institute/broken-math`](https://github.com/insait-institute/broken-math)
  (Apache-2.0).

## Reproduction

See [`evaluation_report.md`](evaluation_report.md) for a baseline reproduction.
Note the metric is **judge-dependent** (as with any LLM-judge eval): the paper's
published rates use a **GPT-5-mini** judge, so absolute numbers shift with the
judge model. Model *ranking* and the methodology reproduce faithfully.

## License

MIT (this implementation). Upstream data is CC-BY-4.0; the vendored judge prompt
is Apache-2.0. See [LICENSE](LICENSE) and upstream attribution above.

## Citation

```bibtex
@inproceedings{petrov2025brokenmath,
  title={BrokenMath: A Benchmark for Sycophancy in Theorem Proving with LLMs},
  author={Petrov, Ivo and Dekoninck, Jasper and Vechev, Martin},
  booktitle={NeurIPS Datasets and Benchmarks},
  year={2025}
}
```
