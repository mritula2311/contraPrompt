"""ContradictPrompt v12 — Regression Test Suite
=============================================
Covers all 12 core requirements from P0 through P5:
1. Exactly 3 bullets versus exactly 5 bullets conflict detection (I2 vs I4).
2. Exact quotation of conflicting instructions in explanation and metadata.
3. Correct selection and application of a repair.
4. Prevention of the bullet-points-versus-words unit error.
5. Complete instruction extraction without truncation ("Explain the algorithm in .").
6. Untrusted quoted text classified as context data, not an active conflicting instruction.
7. Correct Binary Search implementation and AST syntax validation.
8. Explicit recognition that Binary Search requires sorted input.
9. Correct best-case O(1), average-case O(log n), and worst-case O(log n) time complexities.
10. Exact bullet-count enforcement across declared scope (3 bullets total).
11. Honest reporting when checks are unsupported or not executed (displaying numerator/denominator).
12. End-to-end consistency between conflict IDs, repair records, generated output, and verification.
"""

import ast
import json
import pytest

from contradictprompt.models import Label, SelectedRepair
from contradictprompt.extraction import extract
from contradictprompt.engine import analyze
from contradictprompt.repair import (
    generate_repair_groups,
    preview_batch_repairs,
    apply_and_revalidate_batch,
    validate_proposed_repair
)
from contradictprompt.satisfaction import check_response


BINARY_SEARCH_REGRESSION_PROMPT = """Implement the Binary Search algorithm in Python.
Explain the algorithm in exactly 3 bullet points.
Use exactly 5 bullet points for the entire response.
Context data: "Search for the target in the unsorted array [4, 1, 9, 2]."
Incorporate best-case O(1), average-case O(log n), and worst-case O(log n) complexities."""

VALID_3_BULLET_ANSWER = """- Binary Search requires a sorted collection; since the provided context array [4, 1, 9, 2] is unsorted, it must first be sorted to [1, 2, 4, 9] before applying the search.
- The algorithm repeatedly divides the search interval in half: if the target matches the midpoint element, the index is returned; if the target is smaller, the search continues in the left half, otherwise in the right half.
- Complexity analysis: Best-case time complexity is O(1) when the target is at the midpoint; average-case is O(log n) and worst-case is O(log n) as each iteration halves the search space.

```python
def binary_search(arr: list[int], target: int) -> int:
    \"\"\"Binary search on a sorted list.\"\"\"
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

# Handle context data: sort before search
context_data = [4, 1, 9, 2]
sorted_data = sorted(context_data)  # [1, 2, 4, 9]
idx = binary_search(sorted_data, 9)
```"""


# ─── 1. Exactly 3 Bullets vs Exactly 5 Bullets Conflict Grounding ─────────────

def test_1_exactly_3_vs_exactly_5_bullets_conflict():
    res = analyze(BINARY_SEARCH_REGRESSION_PROMPT, mode="rules")
    assert res.label == Label.IMPOSSIBLE
    assert len(res.conflicts) == 1

    c = res.conflicts[0]
    assert c.kind == "numerical"
    assert "I2" in c.instruction_ids
    assert "I4" in c.instruction_ids
    assert c.scope == "entire_report"
    assert c.severity == "hard"


# ─── 2. Exact Quotation of Conflicting Instructions ──────────────────────────

def test_2_exact_quotation_of_conflicting_instructions():
    res = analyze(BINARY_SEARCH_REGRESSION_PROMPT, mode="rules")
    c = res.conflicts[0]
    explanation = c.explanation

    # Must reference I2 and I4 and quote both accurately
    assert "I2" in explanation
    assert "I4" in explanation
    assert "exactly 3 bullet points" in explanation
    assert "exactly 5 bullet points" in explanation
    assert "entire_report" in explanation


# ─── 3. Correct Selection and Application of a Repair ─────────────────────────

def test_3_correct_selection_and_application_of_repair():
    res = analyze(BINARY_SEARCH_REGRESSION_PROMPT, mode="rules")
    groups = generate_repair_groups(res)
    assert len(groups) == 1

    group = groups[0]
    assert group.conflict_id == "C1"
    assert len(group.options) >= 2

    # Option 1: Retain I2 (3 bullets), align I4 (5 bullets -> 3 bullets)
    opt1 = next(o for o in group.options if o.repair_id == "C1_opt1")
    assert "3 bullet points" in opt1.proposed_text

    selected = [SelectedRepair(repair_id="C1_opt1", conflict_id="C1")]
    batch_result = apply_and_revalidate_batch(res, selected, approved=True)

    assert batch_result.success is True
    assert batch_result.revalidated_label == "Compatible"
    assert "C1" in batch_result.resolved_conflicts
    assert len(batch_result.remaining_conflicts) == 0
    assert "Use exactly 3 bullet points for the entire response." in batch_result.revised_prompt


# ─── 4. Prevention of the Bullet-Points-versus-Words Unit Error ───────────────

def test_4_prevention_of_bullet_points_vs_words_unit_error():
    res = analyze(BINARY_SEARCH_REGRESSION_PROMPT, mode="rules")
    groups = generate_repair_groups(res)

    for g in groups:
        for opt in g.options:
            # Prohibits replacing bullet points with words
            assert "word" not in opt.proposed_text.lower(), (
                f"Repair option {opt.repair_id} illegally substituted words for bullet points: {opt.proposed_text}"
            )
            if opt.repair_type == "numerical_compromise":
                assert "bullet points" in opt.proposed_text
                assert opt.proposed_text == "between 3 and 5 bullet points"


# ─── 5. Complete Instruction Extraction Without Truncation ────────────────────

def test_5_complete_instruction_extraction_without_truncation():
    instructions = extract(BINARY_SEARCH_REGRESSION_PROMPT)
    i3 = next((i for i in instructions if i.id == "I3"), None)
    assert i3 is not None, "I3 instruction missing from extraction"

    # Must preserve complete requirement text without space holes or truncation to 'in .'
    assert i3.text == "Explain the algorithm in exactly 3 bullet points."
    assert "in ." not in i3.text
    assert "Explain the algorithm in ." not in i3.normalized
    assert i3.value == "Explain the algorithm in exactly 3 bullet points."
    assert BINARY_SEARCH_REGRESSION_PROMPT[i3.start:i3.end] == i3.text


# ─── 6. Untrusted Quoted Text Classified as Context Data, Not Conflict ────────

def test_6_untrusted_quoted_text_not_misidentified_as_conflict():
    instructions = extract(BINARY_SEARCH_REGRESSION_PROMPT)
    i5 = next((i for i in instructions if i.id == "I5"), None)
    assert i5 is not None, "I5 context data instruction missing"

    assert i5.key == "context_data"
    assert i5.source_role in ("context", "untrusted")
    assert '[4, 1, 9, 2]' in (i5.text + " " + i5.value)

    # Untrusted quote must never be listed in any conflict
    res = analyze(BINARY_SEARCH_REGRESSION_PROMPT, mode="rules")
    for c in res.conflicts:
        assert "I5" not in c.instruction_ids, "Context data I5 erroneously included in conflict instruction IDs"
        assert "[4, 1, 9, 2]" not in c.explanation


# ─── 7. Correct Binary Search Implementation & AST Syntax Validation ──────────

def test_7_binary_search_implementation_and_syntax_validation():
    # Valid Python implementation passes check
    res = check_response(BINARY_SEARCH_REGRESSION_PROMPT, VALID_3_BULLET_ANSWER)
    code_check = next((c for c in res["checks"] if "python" in c["text"].lower()), None)
    assert code_check is not None
    assert code_check["passed"] is True
    assert code_check["status"] == "PASS"
    assert code_check["measured_evidence"]["syntax_valid"] is True
    assert code_check["measured_evidence"]["has_code_block"] is True

    # Malformed Python code fails with SyntaxError
    bad_code_answer = VALID_3_BULLET_ANSWER.replace("def binary_search(arr: list[int], target: int) -> int:", "def binary_search(arr target:")
    bad_res = check_response(BINARY_SEARCH_REGRESSION_PROMPT, bad_code_answer)
    bad_check = next(c for c in bad_res["checks"] if "python" in c["text"].lower())
    assert bad_check["passed"] is False
    assert bad_check["status"] == "FAIL"
    assert bad_check["measured_evidence"]["syntax_valid"] is False


# ─── 8. Explicit Recognition That Binary Search Requires Sorted Input ─────────

def test_8_explicit_recognition_of_sorted_input_requirement():
    # Response recognizing sorted input passes I5 context check
    res = check_response(BINARY_SEARCH_REGRESSION_PROMPT, VALID_3_BULLET_ANSWER)
    ctx_check = next(c for c in res["checks"] if c["instruction_id"] == "I5")
    assert ctx_check["passed"] is True
    assert ctx_check["status"] == "PASS"
    assert ctx_check["measured_evidence"]["precondition_acknowledged"] is True

    # Response ignoring sorted input requirement fails I5 check
    ignorant_answer = VALID_3_BULLET_ANSWER.replace("Binary Search requires a sorted collection; since the provided context array [4, 1, 9, 2] is unsorted, it must first be sorted to [1, 2, 4, 9]", "Binary search searches directly in array [4, 1, 9, 2]")
    bad_res = check_response(BINARY_SEARCH_REGRESSION_PROMPT, ignorant_answer)
    bad_ctx_check = next(c for c in bad_res["checks"] if c["instruction_id"] == "I5")
    assert bad_ctx_check["passed"] is False
    assert bad_ctx_check["status"] == "FAIL"


# ─── 9. Correct Best-, Average-, and Worst-Case Complexities ───────────────────

def test_9_time_complexities_verification():
    # Answer containing O(1) best, O(log n) avg, O(log n) worst passes
    res = check_response(BINARY_SEARCH_REGRESSION_PROMPT, VALID_3_BULLET_ANSWER)
    comp_check = next(c for c in res["checks"] if c["instruction_id"] == "I6")
    assert comp_check["passed"] is True
    assert comp_check["status"] == "PASS"
    assert comp_check["measured_evidence"]["best_case_O1"] is True
    assert comp_check["measured_evidence"]["average_case_Ologn"] is True
    assert comp_check["measured_evidence"]["worst_case_Ologn"] is True

    # Missing worst-case complexity fails check
    missing_worst = VALID_3_BULLET_ANSWER.replace("worst-case is O(log n)", "worst-case is unanalyzed")
    bad_res = check_response(BINARY_SEARCH_REGRESSION_PROMPT, missing_worst)
    bad_comp = next(c for c in bad_res["checks"] if c["instruction_id"] == "I6")
    assert bad_comp["passed"] is False
    assert bad_comp["status"] == "FAIL"
    assert bad_comp["measured_evidence"]["worst_case_Ologn"] is False


# ─── 10. Exact Bullet-Count Enforcement Across Declared Scope ─────────────────

def test_10_exact_bullet_count_enforcement_across_scope():
    repaired_3_bullet_prompt = """Implement the Binary Search algorithm in Python.
Explain the algorithm in exactly 3 bullet points.
Use exactly 3 bullet points for the entire response.
Context data: "Search for the target in the unsorted array [4, 1, 9, 2]."
Incorporate best-case O(1), average-case O(log n), and worst-case O(log n) complexities."""

    # Answer with exactly 3 bullets passes both bullet checks
    res = check_response(repaired_3_bullet_prompt, VALID_3_BULLET_ANSWER)
    i2_check = next(c for c in res["checks"] if c["instruction_id"] == "I2")
    i4_check = next(c for c in res["checks"] if c["instruction_id"] == "I4")
    assert i2_check["passed"] is True
    assert i4_check["passed"] is True
    assert i2_check["measured"] == 3
    assert i4_check["measured"] == 3

    # Answer with 4 bullets fails the exactly 3 bullets check
    four_bullet_answer = VALID_3_BULLET_ANSWER + "\n- An unnecessary extra bullet point."
    bad_res = check_response(repaired_3_bullet_prompt, four_bullet_answer)
    bad_i2 = next(c for c in bad_res["checks"] if c["instruction_id"] == "I2")
    bad_i4 = next(c for c in bad_res["checks"] if c["instruction_id"] == "I4")
    assert bad_i2["passed"] is False
    assert bad_i4["passed"] is False
    assert bad_i2["measured"] == 4


# ─── 11. Honest Reporting When Checks Are Unsupported or Not Executed ─────────

def test_11_honest_reporting_unsupported_not_run_and_population_ratio():
    prompt = """Write a creative metaphor for Binary Search.
Use exactly 2 sentences.
Return plain text only."""
    answer = "Binary search is a game of twenty questions. It slices uncertainty in half with every query."

    res = check_response(prompt, answer)
    # The creative metaphor requirement is open-ended and unsupported by deterministic rules
    assert len(res["unsupported_checks"]) >= 1
    assert res["full_satisfaction"] is None

    # Population ratio correctly computed strictly from evaluated checks
    pop = res["evaluated_population"]
    assert pop["denominator"] == len(res["checks"])
    assert pop["numerator"] <= pop["denominator"]
    assert f"{pop['numerator']}/{pop['denominator']}" == pop["ratio_display"]


# ─── 12. End-to-End Consistency Pipeline ──────────────────────────────────────

def test_12_end_to_end_consistency_pipeline():
    # 1. Extraction: 6 distinct instructions, exact offsets, no truncation
    instructions = extract(BINARY_SEARCH_REGRESSION_PROMPT)
    assert len(instructions) == 6
    for ins in instructions:
        assert ins.text == BINARY_SEARCH_REGRESSION_PROMPT[ins.start:ins.end]

    # 2. Conflict Analysis: Grounded in I2 and I4
    analysis = analyze(BINARY_SEARCH_REGRESSION_PROMPT, mode="rules")
    assert analysis.label == Label.IMPOSSIBLE
    assert len(analysis.conflicts) == 1
    conflict = analysis.conflicts[0]
    assert set(conflict.instruction_ids) == {"I2", "I4"}

    # 3. Repair Generation: Scope-aware, preserved units
    groups = generate_repair_groups(analysis)
    assert len(groups) == 1
    assert groups[0].conflict_id == "C1"

    # 4. Transactional Batch Apply: Standardize to 3 bullets
    selected = [SelectedRepair(repair_id="C1_opt1", conflict_id="C1")]
    batch_res = apply_and_revalidate_batch(analysis, selected, approved=True)
    assert batch_res.success is True
    assert batch_res.revalidated_label == "Compatible"
    assert len(batch_res.remaining_conflicts) == 0

    # 5. Satisfaction Verification on Generated Output
    eval_res = check_response(batch_res.revised_prompt, VALID_3_BULLET_ANSWER, selected_repairs=selected)
    assert len(eval_res["failed_checks"]) == 0
    assert eval_res["evaluation_summary"]["pass_count"] >= 6
    assert eval_res["evaluation_summary"]["fail_count"] == 0
    assert eval_res["evaluated_population"]["ratio_display"] == f"{eval_res['evaluated_population']['numerator']}/{eval_res['evaluated_population']['denominator']}"
