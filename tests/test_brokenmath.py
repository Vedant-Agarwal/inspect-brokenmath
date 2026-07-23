"""Smoke tests for the BrokenMath eval."""

from brokenmath.brokenmath import CHECKER_PROMPT, _extract_verdict


def test_checker_prompt_formats_with_four_fields():
    filled = CHECKER_PROMPT.format(problem="P", solution="S", original_statement="O", gt_solution="G")
    assert "P" in filled and "S" in filled and "\\boxed{incorrect}" in filled


def test_extract_verdict():
    assert _extract_verdict(r"reasoning... \boxed{incorrect}") == "incorrect"
    assert _extract_verdict(r"\boxed{correct} and later \boxed{detected}") == "detected"
    assert _extract_verdict("no verdict here") is None
    assert _extract_verdict(r"\boxed{nonsense}") is None
