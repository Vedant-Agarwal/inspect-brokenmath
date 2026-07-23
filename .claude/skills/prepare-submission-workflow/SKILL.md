---
name: prepare-submission-workflow
description: Prepare an evaluation for PR submission — add dependencies, tests, linting, eval.yaml, and README. Use when user asks to prepare an eval for submission or finalize a PR. Trigger when the user asks you to run the "Prepare Evaluation For Submission" workflow.
---
<!-- MANAGED FILE - Updates pulled from template. See MANAGED_FILES.md -->

# Prepare Eval For Submission

## Workflow Steps

To prepare an evaluation for submission as a pull request:

1. Add custom dependencies in the [pyproject.toml](../../../pyproject.toml) file, if required. Add the package to the top-level `[project] dependencies` list (or to a dependency group if you want to keep it optional).

   ```toml
   [project]
   dependencies = [
       "inspect_ai>=0.3.158",
       "pyyaml>=5.1.0",
       "example-python-package",  # add your eval's runtime deps here
   ]
   ```

   Pin the package version if your evaluation might be sensitive to version updates.

   Make sure your module does not import your custom dependencies at module import time when those imports might fail. This can break the way `inspect_ai` discovers tasks via entry points.

   To check for this, uninstall your optional dependencies and run another eval with `--limit=0`. If it fails due to one of your imports, you need to defer that import (move it inside the function that uses it).

2. Add pytest tests covering the custom functions included in your evaluation. See the [Testing Standards](../../../CONTRIBUTING.md#testing-standards) section for more details.

3. Run `pytest` to ensure all new and existing tests pass. `uv sync` installs
   the `dev` dependency group (which includes `pytest`) by default, so a plain
   sync is enough:

   ```bash
   uv sync
   uv run pytest
   ```

4. Add an `eval.yaml` file to your evaluation directory (e.g., `src/<eval_name>/eval.yaml`) so the auto-generated README sections (Usage, Options, Parameters, Contributors) can be populated by `tools/generate_readmes.py`. See the [eval.yaml Reference](../../../CONTRIBUTING.md#evalyaml-reference) section in CONTRIBUTING.md for a complete example and field documentation.

5. Register the eval in `pyproject.toml` under `[project.entry-points.inspect_ai]` so `uv run inspect eval <eval_name>/<task_name>` resolves it:

   ```toml
   [project.entry-points.inspect_ai]
   <eval_name> = "<eval_name>"
   ```

6. Run linting, formatting, and type checking and address any issues:

   ```bash
   make check
   ```

   This runs the full check suite via `tools/run_checks.sh`, including
   autolint against the registry's recommended structural standards.
   Failures of advisory checks are reported but don't fail the build by
   default — see README.md "Checks and enforcement" for the toggle table.
   The same workflows run on incoming PRs, so address any enforced
   failures before opening a PR.

7. Fill in the missing sections of the generated README.md which are marked with 'TODO:'.
