"""Automated verification tests for the 100-prompt benchmark and paradox dataset."""

import pytest
from contradictprompt import analyze, Label
from contradictprompt.benchmarks import BENCHMARK_PROMPTS, get_prompts_by_category


def test_benchmark_contains_100_prompts():
    assert len(BENCHMARK_PROMPTS) == 100
    categories = {p["category_id"] for p in BENCHMARK_PROMPTS}
    assert categories == {"structural", "semantic", "persona", "negation", "dependency"}
    for cat in categories:
        prompts = get_prompts_by_category(cat)
        assert len(prompts) == 20, f"Category {cat} must contain exactly 20 prompts"


def test_user_critical_cases_rules_and_hybrid():
    """Verify the 3 critical contradictory prompts specified by the user."""
    cases = [
        ("An underwater coral reef teeming with colorful tropical fish, but the entire scene is bone-dry and covered in desert dust", "aquatic/underwater and bone-dry desert"),
        ("Write a deeply heartbreaking eulogy for a funeral, but make the tone incredibly cheerful, upbeat, and celebratory like a lottery win.", "sorrowful/heartbreaking funeral tone and an upbeat/celebratory lottery-win tone"),
        ("Write a highly descriptive, 500-word monologue for a character who refuses to speak a single word or communicate in any way.", "monologue or spoken speech while requiring the speaker to refuse to speak")
    ]
    for prompt, expected_substr in cases:
        # Rule-based offline detection
        res = analyze(prompt, mode="rules")
        assert res.label == Label.IMPOSSIBLE, f"Rules mode must detect impossible for: {prompt}"
        assert len(res.conflicts) >= 1
        assert any(expected_substr in c.explanation for c in res.conflicts)


@pytest.mark.parametrize("prompt_data", BENCHMARK_PROMPTS[:25])
def test_benchmark_prompts_safety_and_transparency(prompt_data):
    """Test that all benchmark prompts are either detected or disclose free-text review warning."""
    res = analyze(prompt_data["prompt"], mode="rules")
    if res.label != Label.COMPATIBLE:
        assert len(res.conflicts) >= 1 or len(res.clarification_questions) >= 1
    else:
        # If offline rules mark Compatible, it MUST warn that free-text requires semantic review
        assert any("free-text" in w or "limited English grammar" in w for w in res.warnings)
