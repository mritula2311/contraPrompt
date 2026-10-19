"""Metamorphic and Property-Based Testing Suite (Section 17).

Verifies fundamental invariance and variance relations under prompt transformations:
1. Irrelevant text perturbation invariance: Adding noise must not alter proven conflict labels.
2. Instruction reordering invariance: Permuting independent clauses preserves satisfiability.
3. Monotonicity of contradiction: Adding compatible constraints cannot resolve existing conflicts.
4. Scope separation variance: Partitioning conflicting bounds into disjoint sections resolves impossibility.
"""
import pytest
from contradictprompt import analyze, Label

def test_metamorphic_irrelevant_text_invariance():
    """Property: Injecting irrelevant narrative prose should not eliminate a proven contradiction."""
    base_prompt = "Write exactly 100 words. Keep the length fewer than 80 words."
    noisy_prompt = (
        "Once upon a time in a distant galaxy, stars were shining brightly and planets orbited smoothly. "
        + base_prompt
        + " Furthermore, birds were singing in the forest."
    )
    res_base = analyze(base_prompt, mode='rules')
    res_noisy = analyze(noisy_prompt, mode='rules')
    assert res_base.label == Label.IMPOSSIBLE
    assert res_noisy.label == Label.IMPOSSIBLE

def test_metamorphic_instruction_reordering():
    """Property: Swapping the order of contradictory clauses preserves the impossible label."""
    order_a = "Write exactly 100 words. Keep the length fewer than 80 words."
    order_b = "Keep the length fewer than 80 words. Write exactly 100 words."
    res_a = analyze(order_a, mode='rules')
    res_b = analyze(order_b, mode='rules')
    assert res_a.label == res_b.label == Label.IMPOSSIBLE

def test_metamorphic_monotonicity_of_contradiction():
    """Property: Appending a compatible instruction cannot undo a fatal contradiction."""
    base_prompt = "Write exactly 100 words. Keep the length fewer than 80 words."
    extended_prompt = base_prompt + " Ensure the output is written in standard American English."
    res_base = analyze(base_prompt, mode='rules')
    res_ext = analyze(extended_prompt, mode='rules')
    assert res_base.label == Label.IMPOSSIBLE
    assert res_ext.label == Label.IMPOSSIBLE

def test_metamorphic_scope_separation_variance():
    """Property: Separating contradictory bounds into distinct section scopes turns an impossible prompt into compatible instructions."""
    # Global scope (contradiction)
    global_conflict = "Write exactly 50 words. Write exactly 500 words."
    res_global = analyze(global_conflict, mode='rules')
    assert res_global.label == Label.IMPOSSIBLE

    # Disjoint scopes (valid)
    scoped_prompt = (
        "In the Summary section, write exactly 50 words. "
        "In the Body section, write exactly 500 words."
    )
    res_scoped = analyze(scoped_prompt, mode='rules')
    assert res_scoped.label != Label.IMPOSSIBLE
