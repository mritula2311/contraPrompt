"""Regression Test Suite for Audit Classification and Satisfaction Evaluation
=============================================================================
Verifies all 5 core sections of the prompt specification:
1. Exact quantum compound prompt (R1-R7)
2. Valid normalized three-qubit state
3. Valid unitary transformation
4. Supported exact Clifford+T angle (k*pi/4)
5. Arbitrary-angle approximation request
6. 5-qubit vs 20-qubit hardware conflict under no-partitioning restriction
7. Fabricated vs genuinely recorded hardware results
8. 200-word output constraint
9. JSON-only output
10. Conflicting JSON and Markdown requirements
11. Duplicate conflict reports deduplication
12. Explicit pairwise audit tracking (never claims all pairs evaluated when selected)
13. Composite requirement partial pass rejection
14. Null full_satisfaction with separate unsupported and failed checks
"""

import json
import pytest

from contradictprompt.audit import (
    audit_prompt,
    parse_requirements,
    deduplicate_conflicts,
    compute_quantum_simulation_profile,
    AuditConflict,
    RequirementAudit,
    PhysicalValidity,
    MathematicalConsistency,
    ImplementationFeasibility,
    ComputationalFeasibility,
    CrossRequirementCompatibility,
    EvaluationStatus
)
from contradictprompt.satisfaction import check_response, evaluate_audit_satisfaction


EXACT_QUANTUM_PROMPT = """[R1] State Preparation: Prepare the 3-qubit entangled state |psi> = 1/sqrt(3)|000> + 1/sqrt(3)|111>.
[R2] Unitary Transformation: Apply a unitary operator U that maps the orthogonal input states |000> and |111> to the identical target state |+++>.
[R3] Gate Synthesis: Perform exact Clifford+T gate synthesis for a single-qubit rotation by an arbitrary angle theta = pi/5.
[R4] Hardware Execution: Execute the 20-qubit quantum circuit on a 5-qubit quantum processor with no circuit partitioning or virtualization.
[R5] Experimental Evidence: Provide measured experimental outcomes from real quantum hardware execution.
[R6] Output Size: Formulate the complete step-by-step mathematical derivation and circuit table within exactly 200 words.
[R7] Format Specification: Return the final output strictly formatted as valid JSON only, using Markdown headings (# Section) and bullet lists."""


# ─── 1. Exact Quantum Prompt Regression ──────────────────────────────────────

def test_exact_quantum_prompt_audit():
    result = audit_prompt(EXACT_QUANTUM_PROMPT, check_all_pairs=True)

    # 1. Stable requirement IDs and original text preserved
    assert len(result.requirements) == 7
    req_ids = [r.id for r in result.requirements]
    assert req_ids == ["R1", "R2", "R3", "R4", "R5", "R6", "R7"]
    assert "1/sqrt(3)|000>" in result.requirements[0].text
    assert "unitary" in result.requirements[1].text.lower()
    assert "clifford+t" in result.requirements[2].text.lower()
    assert "20-qubit" in result.requirements[3].text.lower()

    # 2. R1 State Unnormalized (squared norm = 2/3)
    r1 = result.requirements[0]
    assert r1.physical_validity == PhysicalValidity.INVALID
    assert r1.mathematical_consistency == MathematicalConsistency.INCONSISTENT
    assert r1.invalid_as_written is True
    assert r1.possible_with_authorized_correction is True
    assert "sqrt(3/2)" in r1.authorized_correction_description
    assert r1.measured_evidence["squared_norm"] == "2/3"

    # 3. R2 Unitary Preserves Inner Products
    r2 = result.requirements[1]
    assert r2.physical_validity == PhysicalValidity.INVALID
    assert r2.mathematical_consistency == MathematicalConsistency.INCONSISTENT
    assert r2.invalid_as_written is True
    assert r2.possible_with_authorized_correction is True
    assert "preserves inner products" in r2.explanation.lower()

    # 4. R3 Arbitrary Angle Clifford+T Synthesis
    r3 = result.requirements[2]
    assert r3.implementation_feasibility == ImplementationFeasibility.INFEASIBLE
    assert r3.mathematical_consistency == MathematicalConsistency.INCONSISTENT
    assert r3.invalid_as_written is True
    assert r3.possible_with_authorized_correction is True
    assert "approximate" in r3.authorized_correction_description.lower()

    # 5. R4 20-qubit circuit on 5-qubit processor
    r4 = result.requirements[3]
    assert r4.physical_validity == PhysicalValidity.INVALID
    assert r4.implementation_feasibility == ImplementationFeasibility.INFEASIBLE
    assert r4.computational_feasibility == ComputationalFeasibility.INFEASIBLE
    assert r4.invalid_as_written is True
    assert r4.possible_with_authorized_correction is True
    assert "partitioning" in r4.authorized_correction_description.lower()

    # 6. R5 Experimental evidence requires verifiable hardware provenance
    r5 = result.requirements[4]
    assert r5.physical_validity == PhysicalValidity.UNKNOWN
    assert r5.evaluation_status == EvaluationStatus.HUMAN_REVIEW_REQUIRED
    assert r5.measured_evidence["hardware_execution_verified"] is False

    # 7. R6 & R7 Conflicts
    r6 = result.requirements[5]
    r7 = result.requirements[6]
    assert r7.mathematical_consistency == MathematicalConsistency.INCONSISTENT
    assert r7.cross_requirement_compatibility == CrossRequirementCompatibility.CONFLICTED

    # 8. Separate Internal and Cross-Requirement Conflicts
    assert len(result.internal_conflicts) >= 3
    assert len(result.cross_requirement_conflicts) >= 1

    # Verify conflict structure
    for c in result.all_conflicts:
        assert len(c.affected_requirement_ids) >= 1
        assert len(c.exact_source_quotes) >= 1
        assert len(c.explanation) > 10
        assert len(c.consequence) > 10
        assert len(c.smallest_scientifically_valid_correction) > 10
        assert c.category in (
            "quantum_state_normalization",
            "unitary_inner_product_preservation",
            "clifford_t_synthesis_exactness",
            "hardware_qubit_capacity",
            "output_size_conflict",
            "format_conflict"
        )

    # 9. Pairwise tracking
    assert result.pairs_evaluated == 21  # 7 * 6 / 2
    assert result.total_possible_pairs == 21
    assert result.exhaustive_pairwise_check is True

    # 10. Computational Simulation Profiling (State-Vector vs Dense Matrix)
    profile = result.simulation_profile
    assert profile is not None
    assert profile.num_qubits == 20
    assert profile.state_vector_amplitudes == 1_048_576
    assert profile.state_vector_computational_feasibility == ComputationalFeasibility.FEASIBLE
    assert "16.00 MiB" in profile.state_vector_memory_human
    assert profile.dense_matrix_elements == 2 ** 40
    assert profile.dense_matrix_computational_feasibility == ComputationalFeasibility.INFEASIBLE
    assert "16.00 TiB" in profile.dense_matrix_memory_human


# ─── 2. Valid Normalized Three-Qubit State ────────────────────────────────────

def test_valid_normalized_three_qubit_state():
    prompt = "[R1] State Preparation: Prepare the normalized 3-qubit state |psi> = 1/sqrt(2)|000> + 1/sqrt(2)|111>."
    result = audit_prompt(prompt)
    assert len(result.requirements) == 1
    r1 = result.requirements[0]
    assert r1.physical_validity == PhysicalValidity.VALID
    assert r1.mathematical_consistency == MathematicalConsistency.CONSISTENT
    assert r1.invalid_as_written is False
    assert r1.evaluation_status == EvaluationStatus.PASS
    assert r1.measured_evidence["is_normalized"] is True
    assert len(result.internal_conflicts) == 0


# ─── 3. Valid Unitary Transformation ──────────────────────────────────────────

def test_valid_unitary_transformation():
    prompt = "[R1] Apply a unitary transformation U that maps orthogonal input states |0> to |+> and |1> to |-> preserving inner product."
    result = audit_prompt(prompt)
    assert len(result.requirements) == 1
    r1 = result.requirements[0]
    assert r1.physical_validity == PhysicalValidity.VALID
    assert r1.mathematical_consistency == MathematicalConsistency.CONSISTENT
    assert r1.invalid_as_written is False
    assert r1.evaluation_status == EvaluationStatus.PASS
    assert len(result.internal_conflicts) == 0


# ─── 4. Supported Exact Clifford+T Angle ──────────────────────────────────────

def test_supported_exact_clifford_t_angle():
    prompt = "[R1] Gate Synthesis: Perform exact Clifford+T gate synthesis for a single-qubit rotation by angle theta = pi/4."
    result = audit_prompt(prompt)
    assert len(result.requirements) == 1
    r1 = result.requirements[0]
    assert r1.implementation_feasibility == ImplementationFeasibility.FEASIBLE
    assert r1.mathematical_consistency == MathematicalConsistency.CONSISTENT
    assert r1.invalid_as_written is False
    assert r1.evaluation_status == EvaluationStatus.PASS
    assert len(result.internal_conflicts) == 0


# ─── 5. Arbitrary-Angle Approximation Request ─────────────────────────────────

def test_arbitrary_angle_approximation_request():
    prompt = "[R1] Gate Synthesis: Synthesize rotation by arbitrary angle theta = pi/5 approximately using Clifford+T gates with tolerance epsilon = 1e-4 via gridsynth."
    result = audit_prompt(prompt)
    assert len(result.requirements) == 1
    r1 = result.requirements[0]
    assert r1.implementation_feasibility == ImplementationFeasibility.FEASIBLE
    assert r1.mathematical_consistency == MathematicalConsistency.CONSISTENT
    assert r1.invalid_as_written is False
    assert r1.evaluation_status == EvaluationStatus.PASS
    assert len(result.internal_conflicts) == 0


# ─── 6. Five-Qubit vs 20-Qubit Hardware Conflict ──────────────────────────────

def test_five_qubit_versus_twenty_qubit_hardware_conflict():
    prompt = """[R1] Execute a 20-qubit circuit with no partitioning.
[R2] Target backend is a 5-qubit quantum processor with no partitioning."""
    result = audit_prompt(prompt)
    assert len(result.requirements) == 2
    assert result.requirements[0].invalid_as_written is True or result.requirements[1].invalid_as_written is True
    assert len(result.all_conflicts) >= 1
    c = result.all_conflicts[0]
    assert "hardware_qubit_capacity" in c.category
    assert "partitioning" in c.smallest_scientifically_valid_correction.lower()


# ─── 7. Fabricated vs Genuinely Recorded Hardware Results ─────────────────────

def test_fabricated_versus_genuinely_recorded_hardware_results():
    prompt = "[R1] Experimental Measurements: Provide measured physical quantum hardware outcomes."
    audit = audit_prompt(prompt)

    # Case A: Fabricated / unverified assertion (no telemetry)
    res_unverified = evaluate_audit_satisfaction(
        audit,
        answer="We ran this on quantum hardware and obtained |000>: 52%, |111>: 48%.",
        hardware_telemetry=None
    )
    assert len(res_unverified["human_review_checks"]) == 1
    assert "R1" in res_unverified["human_review_checks"]
    assert res_unverified["full_satisfaction"] is None
    assert res_unverified["checks"][0]["status"] == "HUMAN_REVIEW_REQUIRED"

    # Case B: Genuinely recorded hardware execution telemetry
    res_verified = evaluate_audit_satisfaction(
        audit,
        answer="QPU results: |000>: 512 counts, |111>: 512 counts.",
        hardware_telemetry={
            "verified_job_id": "ibm_sherbrooke_job_991823",
            "device": "ibm_sherbrooke",
            "shots": 1024
        }
    )
    assert len(res_verified["human_review_checks"]) == 0
    assert res_verified["checks"][0]["status"] == "PASS"
    assert res_verified["checks"][0]["passed"] is True
    assert res_verified["checks"][0]["measured_evidence"]["hardware_verified"] is True
    assert res_verified["checks"][0]["measured_evidence"]["job_id"] == "ibm_sherbrooke_job_991823"


# ─── 8. 200-Word Output Constraint ───────────────────────────────────────────

def test_two_hundred_word_output_constraint():
    prompt = "[R1] Provide your summary in fewer than 200 words."
    audit = audit_prompt(prompt)

    short_answer = " ".join(["quantum"] * 50)
    res_pass = evaluate_audit_satisfaction(audit, short_answer)
    assert res_pass["checks"][0]["status"] == "PASS"
    assert res_pass["checks"][0]["passed"] is True
    assert res_pass["checks"][0]["measured_evidence"]["word_count"] == 50

    long_answer = " ".join(["quantum"] * 250)
    res_fail = evaluate_audit_satisfaction(audit, long_answer)
    assert res_fail["checks"][0]["status"] == "FAIL"
    assert res_fail["checks"][0]["passed"] is False
    assert res_fail["checks"][0]["measured_evidence"]["word_count"] == 250
    assert "R1" in res_fail["failed_checks"]


# ─── 9. JSON-Only Output ──────────────────────────────────────────────────────

def test_json_only_output():
    prompt = "Return JSON only."

    valid_json = json.dumps({"status": "success", "qubits": 5})
    res_valid = check_response(prompt, valid_json)
    assert res_valid["all_supported_pass"] is True
    assert len(res_valid["failed_checks"]) == 0
    assert res_valid["checks"][0]["status"] == "PASS"

    invalid_json = "Here is the JSON: {\"status\": \"success\"}"
    res_invalid = check_response(prompt, invalid_json)
    assert res_invalid["all_supported_pass"] is False
    assert len(res_invalid["failed_checks"]) == 1
    assert res_invalid["checks"][0]["status"] == "FAIL"


# ─── 10. Conflicting JSON and Markdown Requirements ───────────────────────────

def test_conflicting_json_and_markdown_requirements():
    prompt = """[R1] Return strictly valid JSON only.
[R2] Structure your response using Markdown headings and bullet points."""
    result = audit_prompt(prompt)
    assert len(result.all_conflicts) >= 1
    fmt_conflicts = [c for c in result.all_conflicts if c.category == "format_conflict"]
    assert len(fmt_conflicts) >= 1
    c = fmt_conflicts[0]
    assert "format_conflict" in c.category
    assert "JSON" in c.explanation
    assert len(c.exact_source_quotes) >= 1
    assert len(c.smallest_scientifically_valid_correction) > 10


# ─── 11. Duplicate Conflict Reports Deduplication ─────────────────────────────

def test_duplicate_conflict_reports_deduplication():
    c1 = AuditConflict(
        conflict_id="C1",
        conflict_type="internal",
        affected_requirement_ids=["R1"],
        exact_source_quotes=["quote 1"],
        category="quantum_state_normalization",
        explanation="Short explanation.",
        consequence="Consequence 1",
        smallest_scientifically_valid_correction="Correction 1"
    )
    c2 = AuditConflict(
        conflict_id="C2",
        conflict_type="internal",
        affected_requirement_ids=["R1"],
        exact_source_quotes=["quote 1", "extra quote"],
        category="quantum_state_normalization",
        explanation="Longer and much more comprehensive explanation of the same issue.",
        consequence="Consequence 2",
        smallest_scientifically_valid_correction="Correction 2"
    )
    c3 = AuditConflict(
        conflict_id="C3",
        conflict_type="internal",
        affected_requirement_ids=["R2"],
        exact_source_quotes=["quote 3"],
        category="unitary_inner_product_preservation",
        explanation="Different conflict.",
        consequence="Consequence 3",
        smallest_scientifically_valid_correction="Correction 3"
    )

    deduped = deduplicate_conflicts([c1, c2, c3])
    assert len(deduped) == 2
    r1_conflict = next(c for c in deduped if c.affected_requirement_ids == ["R1"])
    # The more detailed explanation is retained
    assert "Longer and much more comprehensive" in r1_conflict.explanation


# ─── 12. Pairwise Audit Tracking ──────────────────────────────────────────────

def test_pairwise_audit_tracking_selected_pairs():
    prompt = """[R1] Prepare quantum state.
[R2] Apply unitary gate.
[R3] Measure in Z basis.
[R4] Output in JSON."""
    # 4 requirements -> 4*3/2 = 6 possible pairs
    # When evaluating only selected pairs (e.g. R1 vs R2), never claim all pairs evaluated
    result = audit_prompt(prompt, check_all_pairs=False, selected_pairs=[("R1", "R2")])
    assert result.pairs_evaluated == 1
    assert result.total_possible_pairs == 6
    assert result.exhaustive_pairwise_check is False


# ─── 13. Composite Requirement Partial Pass Rejection ─────────────────────────

def test_composite_requirement_partial_pass_is_rejected():
    # Prompt requires word count between 50 and 100 words
    prompt = "Write between 50 and 100 words."
    # Answer has 20 words: satisfies upper bound (<= 100) but fails lower bound (>= 50)
    answer = " ".join(["word"] * 20)
    res = check_response(prompt, answer)
    assert len(res["checks"]) == 1
    check = res["checks"][0]
    assert check["passed"] is False
    assert check["status"] == "FAIL"
    assert check["measured_evidence"]["upper_ok"] is True
    assert check["measured_evidence"]["lower_ok"] is False


# ─── 14. Null full_satisfaction with Separate Unsupported Checks ──────────────

def test_null_full_satisfaction_with_unsupported_checks():
    prompt = "Write a creative story explaining quantum superposition. Return JSON only."
    # The creative story part cannot be scored by automated regex/token checks alone
    answer = json.dumps({"story": "Once upon a time in Hilbert space..."})
    res = check_response(prompt, answer)

    # full_satisfaction must remain null (None) because open-ended semantic requirements exist
    assert res["full_satisfaction"] is None
    # Unsupported checks reported separately
    assert len(res["unsupported_checks"]) >= 1
    # Supported checks evaluated
    assert len(res["checks"]) >= 1
    assert res["supported_fraction"] < 1.0
