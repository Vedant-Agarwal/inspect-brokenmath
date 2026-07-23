<!-- MANAGED FILE - Updates pulled from template. See MANAGED_FILES.md -->
# Task Versioning

> **Note for template users:** this document is synced from
> [inspect_evals](https://github.com/UKGovernmentBEIS/inspect_evals) where
> these standards are required for registry submission. In this template they
> are **recommended, not required** — see
> [Checks and enforcement](README.md#checks-and-enforcement) for how to opt
> in or out per check.

Inspect AI [Tasks](https://inspect.aisi.org.uk/tasks.html) evolve via bug fixes, refactors, dataset updates, or evaluation logic changes.

Changes that can break task invocations or affect the comparability of eval results require a task version bump.

## Task version structure

The task `version` attribute should be set on every task. The version is read from `eval.yaml` (see the example below) and must conform to the scheme `N-X`.

`N` tracks changes that affect task comparability, signaling that evaluation results may not be comparable with previous versions. Integer `1, 2, 3, ...`.

`X` tracks changes that affect the `Task` interface. Upper case `A, B, C, ...`.

Increments to `N` and `X` components never decrease, e.g. `1-C` to `2-C`, but never `1-C` to `2-A`.

Since `N` and `X` are independent, a change can affect both simultaneously, e.g. `1-C` to `2-D`.

Versions for new evals should be set as `1-A`.

### Example

Version information is set on the `eval.yaml` in the associated eval folder:

```yaml
title: 'MASK: Disentangling Honesty from Accuracy in AI Systems'
description: |
  Evaluates honesty in large language models by testing whether they contradict their own beliefs when pressured to lie.
arxiv: https://arxiv.org/abs/2503.03750
group: Safeguards
contributors:
- 'Scott-Simmons'
version: "2-A"
tasks:
- name: mask
  dataset_samples: 1000
```

## When to bump the task version

### Bump `N` when

A task changes in a way that breaks fair evaluation comparisons between versions of that task.

### Bump `X` when

A task’s interface changes in a way that could break compatibility with users’ workflows.

## Examples of when to bump the task version

### `N` --> `N+1`: Changes to a Task's comparability

Bump a task version whenever a change could make results non-comparable for the same model across versions, e.g. `3-D` goes to `4-D`.

Examples include:

- Bug fixes that affect evaluation results
- Changes to scoring logic
- Dataset changes
- Parameter changes that influence model behavior or scoring
- Prompt or template changes

### `X` --> `Y` (next letter): Incompatible changes to a Task's interface

Backward or forward-incompatible Task interface changes require a version bump, e.g. `3-D` goes to `3-E`.

#### Backward-incompatible change

Changes that break existing invocations.

Before:

```python
@task
def example_task(
    max_toks: int,
    ...,
) -> Task:
    ...
```

After:

```python
@task
def example_task(
    max_tokens: int,
    ...,
) -> Task:
    ...
```

A version bump is required because old invocations using `max_toks` will fail after the change is applied.

#### Forward-incompatible change

Changes that old versions cannot express.

Before:

```python
@task
def example_task(
    ...,
) -> Task:
    dataset = get_dataset(shuffle=False)
    ...
```

After:

```python
@task
def example_task(
    ...,
    shuffle: bool = False,
) -> Task:
    dataset = get_dataset(shuffle=shuffle)
    ...
```

A version bump is required because old versions would fail when explicitly invoked with the `shuffle` parameter (i.e. -T shuffle=... will fail).

#### Required environment variables

Renaming, adding, or removing a required environment variable is an interface change.

Example: renaming `HF_AUTH_TOKEN` to `HF_TOKEN`. Users who had `HF_AUTH_TOKEN` set in their shell, `.env`, or CI secrets will hit a loud error on the next invocation — same task call signature, but the task's runtime requirements have changed.

Adding a *new* required env var falls under the same rule (existing setups stop working). Adding an *optional* env var that defaults to preserving the prior behavior does not require a bump.
