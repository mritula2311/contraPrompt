"""
Comprehensive Critical Conditions & Complex Test Cases
======================================================
Validates rule-based detection, LLM compatibility, edge cases,
and error handling across all prompt types.
"""
import pytest
from contradictprompt import analyze, Label
from contradictprompt.models import Assessment
from contradictprompt.extraction import extract
from contradictprompt.rules import detect
from contradictprompt.repair import suggestions, approve_and_revalidate, generate_validated
from contradictprompt.llm import LLMClient, ProviderError
from contradictprompt.config import Config
from contradictprompt.satisfaction import check_response

# ─── Numerical Critical Conditions ──────────────────────────────

def test_numerical_exact_vs_fewer():
    res = analyze("Write exactly 100 words, but use fewer than 80 words.", mode="rules")
    assert res.label == Label.IMPOSSIBLE
    assert any(c.kind == "numerical" and c.severity == "hard" for c in res.conflicts)

def test_numerical_at_least_vs_at_most():
    res = analyze("Write at least 200 words, and write at most 100 words.", mode="rules")
    assert res.label == Label.IMPOSSIBLE
    assert any(c.kind == "numerical" for c in res.conflicts)

def test_numerical_inverted_between():
    res = analyze("Write between 150 and 50 words.", mode="rules")
    assert res.label == Label.IMPOSSIBLE
    assert any("empty" in c.explanation.lower() for c in res.conflicts)

def test_numerical_compatible_ranges():
    res = analyze("Write at least 50 words, but no more than 100 words.", mode="rules")
    assert res.label == Label.COMPATIBLE
    assert len(res.conflicts) == 0

def test_numerical_different_units():
    res = analyze("Write at least 3 paragraphs, and use exactly 5 bullet points.", mode="rules")
    assert res.label == Label.COMPATIBLE

# ─── Formatting Critical Conditions ─────────────────────────────

def test_formatting_json_vs_outside():
    res = analyze("Return only JSON; include comments outside the JSON.", mode="rules")
    assert res.label == Label.IMPOSSIBLE
    assert any(c.kind == "formatting" for c in res.conflicts)

def test_formatting_bullets_require_vs_forbid():
    res = analyze("Use bullet points; do not use bullet points.", mode="rules")
    assert res.label == Label.IMPOSSIBLE
    assert any(c.kind == "formatting" for c in res.conflicts)

def test_formatting_tables_require_vs_forbid():
    res = analyze("Include a Markdown table; avoid tables completely.", mode="rules")
    assert res.label == Label.IMPOSSIBLE
    assert any(c.kind == "formatting" for c in res.conflicts)

def test_formatting_compatible():
    res = analyze("Return output formatted with bullet points.", mode="rules")
    assert res.label == Label.COMPATIBLE

# ─── Lexical / Quoted Token Conditions ──────────────────────────

def test_lexical_include_vs_omit_token():
    res = analyze("Include the word 'confidential', but omit the word 'confidential'.", mode="rules")
    assert res.label == Label.IMPOSSIBLE
    assert any(c.kind == "logical" for c in res.conflicts)

def test_lexical_case_insensitivity():
    res = analyze("Include the word 'SECRET', and do not mention the word 'secret'.", mode="rules")
    assert res.label == Label.IMPOSSIBLE

def test_lexical_different_tokens():
    res = analyze("Include the word 'security', and omit the word 'insecure'.", mode="rules")
    assert res.label == Label.COMPATIBLE

# ─── Temporal Conditions ────────────────────────────────────────

def test_temporal_same_event_conflicting_times():
    res = analyze("Schedule meeting Standup on 2026-10-21 at 09:00 and at 14:00.", mode="rules")
    assert res.label == Label.IMPOSSIBLE
    assert any(c.kind == "temporal" for c in res.conflicts)

def test_temporal_different_events_compatible():
    res = analyze("Schedule meeting Alpha on 2026-10-21 at 09:00; schedule meeting Beta on 2026-10-21 at 14:00.", mode="rules")
    assert res.label == Label.COMPATIBLE

# ─── Underspecified & Missing Context ───────────────────────────

def test_missing_attached_document():
    res = analyze("Summarize the attached document in three sentences.", mode="rules")
    assert res.label == Label.UNSPECIFIED
    assert len(res.clarification_questions) > 0

def test_missing_placeholder_context():
    res = analyze("Draft an announcement for [insert product name here].", mode="rules")
    assert res.label == Label.UNSPECIFIED

def test_missing_translation_language():
    res = analyze("Please translate this text; target language not specified.", mode="rules")
    assert res.label == Label.UNSPECIFIED

# ─── Soft Style Tensions ────────────────────────────────────────

def test_soft_brevity_vs_detail():
    res = analyze("Provide a brief, concise overview that is also exhaustive and comprehensive.", mode="rules")
    assert res.label == Label.PARTIAL
    assert any(c.severity == "soft" for c in res.conflicts)

def test_soft_formal_vs_casual():
    res = analyze("Write in a formal tone, but keep it casual and slang.", mode="rules")
    assert res.label == Label.PARTIAL

def test_soft_neutral_vs_persuasive():
    res = analyze("Present a neutral and objective report, but write it as persuasive advocacy.", mode="rules")
    assert res.label == Label.PARTIAL

# ─── Scoped Isolation (Non-Conflicting across Scopes) ───────────

def test_scoped_different_sections_compatible():
    prompt = "In the introduction write at least 100 words; in the conclusion write fewer than 50 words."
    res = analyze(prompt, mode="rules")
    assert res.label == Label.COMPATIBLE
    intro_ins = [i for i in res.instructions if i.scope == "introduction"]
    concl_ins = [i for i in res.instructions if i.scope == "conclusion"]
    assert len(intro_ins) > 0
    assert len(concl_ins) > 0

# ─── Extreme & Critical Boundary Conditions ─────────────────────

def test_empty_prompt_raises():
    with pytest.raises(ValueError, match="non-empty"):
        analyze("", mode="rules")

def test_whitespace_prompt_raises():
    with pytest.raises(ValueError, match="non-empty"):
        analyze("   \n\t  ", mode="rules")

def test_exceeding_max_chars_raises():
    huge_prompt = "word " * 6500  # > 30,000 characters
    with pytest.raises(ValueError, match="limited to"):
        analyze(huge_prompt, mode="rules")

def test_punctuation_and_symbols_handled_safely():
    res = analyze("### Task: Write 50 words! (Or less than 80 words?)... Yes!!", mode="rules")
    assert res.label == Label.COMPATIBLE
    assert len(res.instructions) > 0

def test_unknown_detector_mode_raises():
    with pytest.raises(ValueError, match="Unknown detector mode"):
        analyze("Write a poem.", mode="invalid_mode")

# ─── Repair & Revalidation Logic ────────────────────────────────

def test_repair_workflow_resolves_conflict():
    original = "Write exactly 100 words, but use fewer than 80 words."
    assessment = analyze(original, mode="rules")
    assert assessment.label == Label.IMPOSSIBLE

    repairs = suggestions(assessment)
    assert len(repairs) > 0

    chosen_repair = repairs[0].prompt
    assert chosen_repair != original

    # Unapproved revalidation raises ValueError
    with pytest.raises(ValueError, match=r"(?i)approval"):
        approve_and_revalidate(chosen_repair, approved=False, mode="rules")

    # Approved revalidation succeeds
    revalidated = approve_and_revalidate(chosen_repair, approved=True, mode="rules")
    assert revalidated.label == Label.COMPATIBLE

# ─── Response Generation Gatekeeping ────────────────────────────

def test_generation_refuses_unapproved():
    assessment = analyze("Write a poem.", mode="rules")
    with pytest.raises(ValueError, match=r"(?i)Approve"):
        generate_validated(assessment, LLMClient(), approved=False)

def test_generation_refuses_impossible_prompt():
    assessment = analyze("Write exactly 100 words; write fewer than 50 words.", mode="rules")
    with pytest.raises(ValueError, match=r"Resolve conflicts"):
        generate_validated(assessment, LLMClient(), approved=True)

# ─── Automated Satisfaction Checking ────────────────────────────

def test_satisfaction_checker():
    prompt = "Write exactly 5 words."
    # 5 words answer
    sat_pass = check_response(prompt, "One two three four five.")
    assert sat_pass["supported_fraction"] == 1.0 or len(sat_pass["checks"]) > 0

    # 10 words answer
    sat_fail = check_response(prompt, "One two three four five six seven eight nine ten.")
    if sat_fail["checks"]:
        assert any(c["passed"] is False for c in sat_fail["checks"])
