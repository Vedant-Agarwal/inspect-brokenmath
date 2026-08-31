"""Smoke tests for the BrokenMath eval."""

import pytest
from inspect_ai import Epochs
from inspect_ai.model import ChatMessageUser, ModelOutput, get_model
from inspect_ai.scorer import Score, Target
from inspect_ai.scorer._reducer.registry import reducer_log_names
from inspect_ai.solver import TaskState

from brokenmath.brokenmath import (
    CHECKER_PROMPT,
    HINT_INSTRUCTION,
    PROOF_GRADER_PROMPT,
    SOLVER_SYSTEM,
    _epochs,
    _extract_verdict,
    _majority_verdict,
    _record_to_sample,
    _record_to_utility_sample,
    _solver,
    all_sycophantic,
    brokenmath,
    brokenmath_utility,
    sycophancy_scorer,
    utility_scorer,
)

# --------------------------------------------------------------------------
# prompts / verdict parsing (unchanged behaviour)
# --------------------------------------------------------------------------


def test_checker_prompt_formats_with_four_fields():
    filled = CHECKER_PROMPT.format(problem="P", solution="S", original_statement="O", gt_solution="G")
    assert "P" in filled and "S" in filled and "\\boxed{incorrect}" in filled


def test_proof_grader_prompt_formats_with_two_fields():
    filled = PROOF_GRADER_PROMPT.format(problem="P", solution="S")
    assert "P" in filled and "S" in filled
    assert "\\boxed{correct}" in filled and "\\boxed{incorrect}" in filled


def test_extract_verdict():
    assert _extract_verdict(r"reasoning... \boxed{incorrect}") == "incorrect"
    assert _extract_verdict(r"\boxed{correct} and later \boxed{detected}") == "detected"
    assert _extract_verdict("no verdict here") is None
    assert _extract_verdict(r"\boxed{nonsense}") is None


def test_extract_verdict_restricted_vocabulary():
    """The binary proof grader must not accept the 4-way sycophancy labels."""
    binary = {"correct", "incorrect"}
    assert _extract_verdict(r"\boxed{correct}", binary) == "correct"
    assert _extract_verdict(r"\boxed{detected}", binary) is None


# --------------------------------------------------------------------------
# majority voting
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "votes,expected",
    [
        # unanimous
        (["incorrect", "incorrect", "incorrect"], "incorrect"),
        # simple majority
        (["incorrect", "detected", "incorrect"], "incorrect"),
        (["detected", "incorrect", "detected"], "detected"),
        # single vote is a passthrough
        (["corrected"], "corrected"),
        ([None], None),
        # tie -> earliest first appearance wins (upstream Counter.most_common)
        (["incorrect", "detected"], "incorrect"),
        (["detected", "incorrect"], "detected"),
        (["correct", "detected", "incorrect"], "correct"),
        # unparseable votes are their own bucket and can lose ...
        ([None, "incorrect", "incorrect"], "incorrect"),
        # ... or win, in which case the verdict is None
        ([None, None, "incorrect"], None),
        # ... and tie-break by position like any other bucket
        ([None, "incorrect"], None),
        (["incorrect", None], "incorrect"),
        # empty
        ([], None),
    ],
)
def test_majority_verdict(votes, expected):
    assert _majority_verdict(votes) == expected


def test_majority_verdict_is_order_deterministic():
    """Same multiset, different order -> tie broken deterministically by index."""
    assert _majority_verdict(["a", "b"]) == "a"
    assert _majority_verdict(["b", "a"]) == "b"


# --------------------------------------------------------------------------
# scorers against mockllm
# --------------------------------------------------------------------------


def _state(completion: str = "a proof") -> TaskState:
    state = TaskState(
        model="mockllm/model",
        sample_id="s1",
        epoch=1,
        input=[ChatMessageUser(content="prove the false thing")],
        messages=[],
        metadata={"original_problem": "orig", "gt_solution": "gt"},
    )
    state.output = ModelOutput.from_content("mockllm/model", completion)
    return state


def _judge(*completions: str):
    """A fresh mockllm judge that returns ``completions`` in order (then repeats)."""
    outputs = [
        ModelOutput.from_content("mockllm/model", c) for c in list(completions) * 8
    ]
    return get_model("mockllm/model", custom_outputs=outputs, memoize=False)


async def _system_prompt(solvers) -> str:
    """Run the system_message solver and return the resulting system prompt."""
    state = TaskState(
        model="mockllm/model",
        sample_id="s1",
        epoch=1,
        input=[ChatMessageUser(content="hi")],
        messages=[ChatMessageUser(content="hi")],
    )
    state = await solvers[0](state, lambda s: s)
    return str(state.messages[0].content)


async def test_sycophancy_scorer_single_vote_sycophantic():
    scorer = sycophancy_scorer(judge_model=_judge(r"\boxed{incorrect}"))
    score = await scorer(_state(), Target(""))
    assert score.value == 1.0
    assert score.answer == "incorrect"
    # no vote detail appended when judge_votes == 1 (default behaviour preserved)
    assert "votes:" not in (score.explanation or "")


async def test_sycophancy_scorer_single_vote_non_sycophantic():
    scorer = sycophancy_scorer(judge_model=_judge(r"\boxed{detected}"))
    score = await scorer(_state(), Target(""))
    assert score.value == 0.0
    assert score.answer == "detected"


async def test_sycophancy_scorer_unparseable_scores_zero():
    scorer = sycophancy_scorer(judge_model=_judge("I have no idea"))
    score = await scorer(_state(), Target(""))
    assert score.value == 0.0
    assert "unparseable" in (score.explanation or "")


async def test_sycophancy_scorer_majority_of_three():
    judge = _judge(r"\boxed{incorrect}", r"\boxed{detected}", r"\boxed{incorrect}")
    score = await sycophancy_scorer(judge_model=judge, judge_votes=3)(_state(), Target(""))
    assert score.value == 1.0
    assert score.answer == "incorrect"
    assert score.metadata["judge_verdicts"] == ["incorrect", "detected", "incorrect"]


async def test_sycophancy_scorer_majority_outvotes_single_sycophantic_call():
    judge = _judge(r"\boxed{detected}", r"\boxed{incorrect}", r"\boxed{detected}")
    score = await sycophancy_scorer(judge_model=judge, judge_votes=3)(_state(), Target(""))
    assert score.value == 0.0
    assert score.answer == "detected"


async def test_sycophancy_scorer_majority_with_unparseable_vote():
    judge = _judge("garbage", r"\boxed{incorrect}", r"\boxed{incorrect}")
    score = await sycophancy_scorer(judge_model=judge, judge_votes=3)(_state(), Target(""))
    assert score.value == 1.0
    assert score.metadata["judge_verdicts"] == [None, "incorrect", "incorrect"]


async def test_sycophancy_scorer_majority_all_unparseable():
    score = await sycophancy_scorer(judge_model=_judge("garbage"), judge_votes=3)(
        _state(), Target("")
    )
    assert score.value == 0.0
    assert score.metadata["judge_verdicts"] == [None, None, None]


def test_sycophancy_scorer_rejects_bad_vote_count():
    with pytest.raises(ValueError):
        sycophancy_scorer(judge_votes=0)


async def test_utility_scorer_correct_and_incorrect():
    good = await utility_scorer(judge_model=_judge(r"\boxed{correct}"))(_state(), Target(""))
    assert good.value == 1.0 and good.answer == "correct"
    bad = await utility_scorer(judge_model=_judge(r"\boxed{incorrect}"))(_state(), Target(""))
    assert bad.value == 0.0 and bad.answer == "incorrect"


async def test_utility_scorer_majority_of_three():
    judge = _judge(r"\boxed{correct}", r"\boxed{incorrect}", r"\boxed{correct}")
    score = await utility_scorer(judge_model=judge, judge_votes=3)(_state(), Target(""))
    assert score.value == 1.0


def test_utility_scorer_rejects_bad_vote_count():
    with pytest.raises(ValueError):
        utility_scorer(judge_votes=0)


# --------------------------------------------------------------------------
# Pass@n reducer
# --------------------------------------------------------------------------


def _reduce(values):
    return all_sycophantic()([Score(value=v) for v in values]).value


def test_all_sycophantic_reducer():
    assert _reduce([1.0, 1.0, 1.0]) == 1.0
    assert _reduce([1.0, 0.0, 1.0]) == 0.0  # one non-sycophantic response
    assert _reduce([0.0]) == 0.0
    assert _reduce([1.0]) == 1.0
    assert _reduce([]) == 0.0


# --------------------------------------------------------------------------
# param plumbing / defaults
# --------------------------------------------------------------------------


def test_solver_default_has_no_hint():
    assert HINT_INSTRUCTION not in SOLVER_SYSTEM
    solvers = _solver()
    assert len(solvers) == 2


def test_epochs_helper():
    assert _epochs(1) is None
    epochs = _epochs(4)
    assert isinstance(epochs, Epochs)
    assert epochs.epochs == 4
    assert len(epochs.reducer or []) == 2
    with pytest.raises(ValueError):
        _epochs(0)


def test_record_to_sample_uses_perturbed_problem():
    record = {
        "problem_id": "x/1",
        "problem": "PERTURBED",
        "original_problem": "ORIGINAL",
        "solution": "GT",
        "question_type": "proof",
    }
    sample = _record_to_sample(record)
    assert sample.input == "PERTURBED"
    assert sample.metadata["original_problem"] == "ORIGINAL"


def test_record_to_utility_sample_uses_original_problem():
    record = {
        "problem_id": "x/1",
        "problem": "PERTURBED",
        "original_problem": "ORIGINAL",
        "solution": "GT",
        "question_type": "proof",
    }
    sample = _record_to_utility_sample(record)
    assert sample.input == "ORIGINAL"
    assert sample.metadata["perturbed_problem"] == "PERTURBED"
    assert sample.metadata["gt_solution"] == "GT"


@pytest.mark.dataset_download
def test_default_task_is_unchanged():
    """The registered default: 451 samples, single epoch, no hint in the prompt."""
    t = brokenmath()
    assert t.name == "brokenmath"
    assert len(t.dataset) == 451
    assert t.epochs is None
    assert HINT_INSTRUCTION not in str(t.solver)


@pytest.mark.dataset_download
def test_task_params_plumb_through():
    t = brokenmath(judge_votes=3, n_solutions=4, hint=True)
    assert t.epochs == 4
    assert reducer_log_names(t.epochs_reducer) == ["mean", "all_sycophantic"]


@pytest.mark.dataset_download
def test_utility_task_params_plumb_through():
    t = brokenmath_utility(judge_votes=3, n_solutions=2)
    assert t.epochs == 2
    assert reducer_log_names(t.epochs_reducer) == ["mean"]
    with pytest.raises(ValueError):
        brokenmath_utility(n_solutions=0)


@pytest.mark.dataset_download
def test_utility_task_runs_original_problems():
    t = brokenmath_utility()
    assert t.name == "brokenmath_utility"
    assert len(t.dataset) == 451
    assert t.epochs is None
    # utility samples carry the *original* statement as the input
    sample = t.dataset[0]
    assert sample.input != sample.metadata["perturbed_problem"]


async def test_hint_adds_the_paper_intervention_to_the_system_message():
    plain = await _system_prompt(_solver(hint=False))
    hinted = await _system_prompt(_solver(hint=True))
    assert HINT_INSTRUCTION not in plain
    assert HINT_INSTRUCTION in hinted
    assert hinted.startswith(plain)
