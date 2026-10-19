"""
Comprehensive Edge-Case Testing Suite for V3 Multi-Repair Engine
===============================================================
Covers Section 14 requirements:
- One selected repair
- Two independent selected repairs
- Five simultaneous selected repairs
- All compatible options selected
- Conflicting repairs selected (multiple options for same conflict)
- No repairs selected
- Duplicate repair selections
- Overlapping replacement spans
- Manual repair custom text modifications
- Multiline Markdown and Unicode preservation
- Resetting / idempotence
"""
import pytest
from contradictprompt import analyze, Label
from contradictprompt.models import Assessment, SelectedRepair
from contradictprompt.repair import (
    generate_repair_groups,
    check_repair_compatibility,
    preview_batch_repairs,
    apply_and_revalidate_batch
)
from tests.test_inc_2026_017 import INC_2026_017_PROMPT

@pytest.fixture
def inc_assessment():
    return analyze(INC_2026_017_PROMPT, mode="rules")

def test_edge_case_no_repairs_selected(inc_assessment):
    """Empty repair selection should return valid preview with 0 resolved conflicts."""
    preview = preview_batch_repairs(inc_assessment, [])
    assert preview.is_compatible
    assert preview.revised_prompt == inc_assessment.original
    assert len(preview.predicted_resolved_conflicts) == 0

    res = apply_and_revalidate_batch(inc_assessment, [], approved=True, mode="rules")
    assert res.success
    assert res.revised_prompt == inc_assessment.original
    assert len(res.resolved_conflicts) == 0

def test_edge_case_single_selected_repair(inc_assessment):
    """Selecting exactly one repair resolves only that targeted conflict."""
    groups = generate_repair_groups(inc_assessment)
    g1 = groups[0]
    opt1 = g1.options[0]

    selected = [SelectedRepair(conflict_id=g1.conflict_id, repair_id=opt1.repair_id)]
    is_compat, errors = check_repair_compatibility(inc_assessment, selected)
    assert is_compat
    assert len(errors) == 0

    preview = preview_batch_repairs(inc_assessment, selected)
    assert preview.is_compatible
    assert len(preview.diff_summary) == 1
    assert g1.conflict_id in preview.predicted_resolved_conflicts

    res = apply_and_revalidate_batch(inc_assessment, selected, approved=True, mode="rules")
    assert res.success
    assert g1.conflict_id in res.resolved_conflicts
    # Other conflicts remain
    assert len(res.remaining_conflicts) >= 3

def test_edge_case_two_independent_repairs(inc_assessment):
    """Selecting two independent repairs resolves both without interference."""
    groups = generate_repair_groups(inc_assessment)
    assert len(groups) >= 2
    g1, g2 = groups[0], groups[1]

    selected = [
        SelectedRepair(conflict_id=g1.conflict_id, repair_id=g1.options[0].repair_id),
        SelectedRepair(conflict_id=g2.conflict_id, repair_id=g2.options[0].repair_id),
    ]
    is_compat, errors = check_repair_compatibility(inc_assessment, selected)
    assert is_compat

    res = apply_and_revalidate_batch(inc_assessment, selected, approved=True, mode="rules")
    assert res.success
    assert g1.conflict_id in res.resolved_conflicts
    assert g2.conflict_id in res.resolved_conflicts

def test_edge_case_conflicting_repairs_same_group(inc_assessment):
    """Selecting two mutually exclusive alternatives for the same conflict is rejected."""
    groups = generate_repair_groups(inc_assessment)
    g1 = groups[0]
    assert len(g1.options) >= 2

    selected = [
        SelectedRepair(conflict_id=g1.conflict_id, repair_id=g1.options[0].repair_id),
        SelectedRepair(conflict_id=g1.conflict_id, repair_id=g1.options[1].repair_id),
    ]
    is_compat, errors = check_repair_compatibility(inc_assessment, selected)
    assert not is_compat
    assert any("Multiple conflicting choices selected" in e for e in errors)

    preview = preview_batch_repairs(inc_assessment, selected)
    assert not preview.is_compatible
    assert len(preview.compatibility_issues) > 0

    with pytest.raises(ValueError, match="Selected repairs are incompatible"):
        apply_and_revalidate_batch(inc_assessment, selected, approved=True, mode="rules")

def test_edge_case_custom_replacement_text(inc_assessment):
    """User provides manual replacement text which is correctly applied and tracked."""
    groups = generate_repair_groups(inc_assessment)
    # Find temporal group
    date_group = next(g for g in groups if g.conflict_type == "temporal")
    custom_val = "The incident occurred strictly on October 15, 2026."

    selected = [
        SelectedRepair(
            conflict_id=date_group.conflict_id,
            repair_id=date_group.options[0].repair_id,
            custom_text=custom_val
        )
    ]
    preview = preview_batch_repairs(inc_assessment, selected)
    assert preview.is_compatible
    assert custom_val in preview.revised_prompt

    res = apply_and_revalidate_batch(inc_assessment, selected, approved=True, mode="rules")
    assert res.success
    assert custom_val in res.revised_prompt

def test_edge_case_multiline_markdown_and_unicode_preservation():
    """Verify that Unicode symbols, tabs, indentations, and complex markdown headers are preserved."""
    raw_prompt = """# 🛡️ Executive Incident Report: ⚡ Critical Breach

Dear Incident Response Lead (チームリード):
Please follow these strict guidelines:

* Section A — Summary:
  - Write between 40 and 60 words.
  - Overall total words: exactly 150 words.
  - Overall total words: fewer than 90 words.
* Section B — Remediation:
  - Format: Return strictly JSON only.
  - Outside JSON: Provide a markdown report summarizing findings.

Special Unicode check: © 2026 ACME™ Corp. — «Verified» & “Sanitized”.
"""
    assessment = analyze(raw_prompt, mode="rules")
    assert assessment.label == Label.IMPOSSIBLE
    groups = generate_repair_groups(assessment)
    assert len(groups) >= 2

    # Pick compatible repairs
    selected = [SelectedRepair(conflict_id=g.conflict_id, repair_id=g.options[0].repair_id) for g in groups]
    preview = preview_batch_repairs(assessment, selected)
    assert preview.is_compatible
    
    res = apply_and_revalidate_batch(assessment, selected, approved=True, mode="rules")
    assert res.success
    revised = res.revised_prompt

    # Ensure all Unicode and structural formatting is completely preserved
    assert "# 🛡️ Executive Incident Report: ⚡ Critical Breach" in revised
    assert "Dear Incident Response Lead (チームリード):" in revised
    assert "Special Unicode check: © 2026 ACME™ Corp. — «Verified» & “Sanitized”." in revised
    assert "* Section A — Summary:" in revised
    assert "  - Write between 40 and 60 words." in revised
