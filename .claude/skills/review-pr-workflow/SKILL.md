---
name: review-pr-workflow
description: Automatically review a pull request against the agent-checkable standards in EVALUATION_CHECKLIST.md and BEST_PRACTICES.md. Produces a SUMMARY.md suitable for posting as a PR comment. Use when the user asks to run the "Review PR According to Agent-Checkable Standards" workflow, or to review a PR against template standards.
---
<!-- This skill is template-local; it is not synced from upstream inspect_evals. -->

# Review PR According to Agent-Checkable Standards

This workflow is designed to run in CI (GitHub Actions) to automatically review pull requests against the agent-checkable standards in EVALUATION_CHECKLIST.md. It produces a SUMMARY.md file that is posted as a PR comment.

## Important Notes

- This workflow is optimized for automated CI runs, not interactive use.
- The SUMMARY.md file location is `/tmp/SUMMARY.md` (appropriate for GitHub runners).
- Unlike other workflows, this one does NOT create folders in agent_artefacts since it runs in ephemeral CI environments.

## Workflow Steps

1. **Identify if an evaluation was modified**: Look at the changed files in the PR to determine which evaluation(s) are affected. Use `git diff` commands to see what has changed. If an evaluation (a directory under `src/` other than `examples/` or `utils/`) was modified, complete all steps in the workflow. If no evaluation was modified, skip any steps that say (Evaluation) in them.

2. **(Evaluation) Read the standards**: Read EVALUATION_CHECKLIST.md, focusing on the [Agent Runnable Checks](../../../EVALUATION_CHECKLIST.md#agent-runnable-checks) section. These are the standards you will check against.

3. **(Evaluation) Check each standard**: For each evaluation modified in the PR, go through every item in the Agent Runnable Checks section:
   - Read the relevant files in the evaluation
   - Compare against the standard
   - For any violations found, add an entry to `/tmp/NOTES.md` with:
     - **Standard**: Which standard was violated
     - **Issue**: Description of the issue
     - **Location**: `file_path:line_number` or `file_path` if not line-specific
     - **Recommendation**: What should be changed

   Only worry about violations that exist within the code that was actually changed. Pre-existing violations that were not touched or worsened by this PR can be safely ignored.

4. **Examine test coverage**: Use the ensure-test-coverage skill and appropriate commands to identify any meaningful gaps in test coverage. You can skip this step if a previous step showed no tests were found, since this issue will already be pointed out.

5. **Apply code quality analysis**: Examine all files changed for quality according to BEST_PRACTICES.md. Perform similar analysis and note-taking as in Step 3. If you notice poor quality in a way that is not mentioned in BEST_PRACTICES.md, add this to your notes, and under **Standard**, write "No explicit standard - agent's opinion". Err on the side of including issues here — it is easier for us to notice something too nitpicky than to notice the absence of something important.

6. **Check infrastructure standards**: Also apply the [Infrastructure Changes (Agent)](../../../EVALUATION_CHECKLIST.md#infrastructure-changes-agent) check from EVALUATION_CHECKLIST.md — this applies to all PRs, not just eval submissions. It's a quick check: if high-impact files changed, did the relevant docs follow?

7. **Write the summary**: After checking all standards, create `/tmp/SUMMARY.md` by consolidating the issues from NOTES.md:

   ```markdown
   ## Summary

   Brief overview of what was reviewed and overall assessment.

   ## Issues Found

   ### [Standard Category Name]

   **Issue**: Description of the issue
   **Location**: `file_path:line_number` or `file_path` if not line-specific
   **Recommendation**: What should be changed

   (Repeat for each issue from NOTES.md)

   ## Notes

   Any additional observations or suggestions that aren't violations but could improve the code.
   ```

   If no issues are found, write a brief summary confirming the PR passes all agent-checkable standards. Do NOT include a list of passed checks - it is assumed that anything not mentioned is fine.

8. **Important**: Always write to `/tmp/SUMMARY.md` even if there are no issues. The CI workflow depends on this file existing.

End your comment with 'This is an automatic review performed by Claude Code. Any issues raised here should be fixed or justified, but a human review is still required in order for the PR to be merged.'

## What This Workflow Does NOT Check

- Human-required checks (these need manual review)
- Evaluation report quality (requires running the evaluation)
- Whether the evaluation actually works (requires execution)

This workflow only checks code-level standards that can be verified by reading the code.
