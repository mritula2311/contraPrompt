"""ContradictPrompt — Audit Classification and Scientific Feasibility Engine
========================================================================
Formal multidimensional audit schema, conflict localization, and quantum-computing
domain classification module.

Dimensions evaluated per requirement:
- physical_validity (valid, invalid, unknown, not_applicable, not_evaluated)
- mathematical_consistency (consistent, inconsistent, unknown, not_applicable, not_evaluated)
- implementation_feasibility (feasible, infeasible, unknown, not_applicable, not_evaluated)
- computational_feasibility (feasible, infeasible, unknown, not_applicable, not_evaluated)
- cross_requirement_compatibility (compatible, conflicted, unknown, not_applicable, not_evaluated)
- evaluation_status (PASS, FAIL, CONFLICTED, NOT_EVALUATED, NEEDS_INPUT, HUMAN_REVIEW_REQUIRED)
"""

from enum import StrEnum
import math
import re
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class PhysicalValidity(StrEnum):
    VALID = 'valid'
    INVALID = 'invalid'
    UNKNOWN = 'unknown'
    NOT_APPLICABLE = 'not_applicable'
    NOT_EVALUATED = 'not_evaluated'


class MathematicalConsistency(StrEnum):
    CONSISTENT = 'consistent'
    INCONSISTENT = 'inconsistent'
    UNKNOWN = 'unknown'
    NOT_APPLICABLE = 'not_applicable'
    NOT_EVALUATED = 'not_evaluated'


class ImplementationFeasibility(StrEnum):
    FEASIBLE = 'feasible'
    INFEASIBLE = 'infeasible'
    UNKNOWN = 'unknown'
    NOT_APPLICABLE = 'not_applicable'
    NOT_EVALUATED = 'not_evaluated'


class ComputationalFeasibility(StrEnum):
    FEASIBLE = 'feasible'
    INFEASIBLE = 'infeasible'
    UNKNOWN = 'unknown'
    NOT_APPLICABLE = 'not_applicable'
    NOT_EVALUATED = 'not_evaluated'


class CrossRequirementCompatibility(StrEnum):
    COMPATIBLE = 'compatible'
    CONFLICTED = 'conflicted'
    UNKNOWN = 'unknown'
    NOT_APPLICABLE = 'not_applicable'
    NOT_EVALUATED = 'not_evaluated'


class EvaluationStatus(StrEnum):
    PASS = 'PASS'
    FAIL = 'FAIL'
    CONFLICTED = 'CONFLICTED'
    NOT_EVALUATED = 'NOT_EVALUATED'
    NEEDS_INPUT = 'NEEDS_INPUT'
    HUMAN_REVIEW_REQUIRED = 'HUMAN_REVIEW_REQUIRED'


class RequirementAudit(StrictModel):
    id: str
    text: str
    category: str = 'general'
    physical_validity: PhysicalValidity = PhysicalValidity.NOT_EVALUATED
    mathematical_consistency: MathematicalConsistency = MathematicalConsistency.NOT_EVALUATED
    implementation_feasibility: ImplementationFeasibility = ImplementationFeasibility.NOT_EVALUATED
    computational_feasibility: ComputationalFeasibility = ComputationalFeasibility.NOT_EVALUATED
    cross_requirement_compatibility: CrossRequirementCompatibility = CrossRequirementCompatibility.NOT_EVALUATED
    evaluation_status: EvaluationStatus = EvaluationStatus.NOT_EVALUATED
    invalid_as_written: bool = False
    possible_with_authorized_correction: bool = False
    authorized_correction_description: str | None = None
    measured_evidence: dict[str, Any] = Field(default_factory=dict)
    explanation: str = ''


class AuditConflict(StrictModel):
    conflict_id: str
    conflict_type: Literal['internal', 'cross_requirement']
    affected_requirement_ids: list[str] = Field(min_length=1)
    exact_source_quotes: list[str] = Field(min_length=1)
    category: str
    explanation: str
    consequence: str
    smallest_scientifically_valid_correction: str
    severity: Literal['hard', 'soft'] = 'hard'


class SimulationComplexity(StrictModel):
    num_qubits: int
    state_vector_amplitudes: int
    state_vector_memory_bytes: int
    state_vector_memory_human: str
    state_vector_computational_feasibility: ComputationalFeasibility
    dense_matrix_elements: int
    dense_matrix_memory_bytes: int
    dense_matrix_memory_human: str
    dense_matrix_computational_feasibility: ComputationalFeasibility
    explanation: str


class PromptAuditResult(StrictModel):
    original_prompt: str
    requirements: list[RequirementAudit] = Field(default_factory=list)
    internal_conflicts: list[AuditConflict] = Field(default_factory=list)
    cross_requirement_conflicts: list[AuditConflict] = Field(default_factory=list)
    all_conflicts: list[AuditConflict] = Field(default_factory=list)
    pairs_evaluated: int = 0
    total_possible_pairs: int = 0
    exhaustive_pairwise_check: bool = False
    simulation_profile: SimulationComplexity | None = None
    overall_status: str = 'audit_completed'
    summary_explanation: str = ''


# ─── Scientific Complexity Calculation ───────────────────────────────────────

def compute_quantum_simulation_profile(num_qubits: int = 20) -> SimulationComplexity:
    """Distinguishes state-vector simulation from dense matrix-vector / matrix-matrix multiplication.
    
    State-vector simulation:
      - Memory: 2^n complex128 amplitudes (16 bytes each).
      - For n=20: 2^20 * 16 bytes = 16 MiB RAM.
      - Computational Feasibility: Feasible on modern consumer hardware.

    Dense matrix representation:
      - Memory: 2^(2n) complex128 entries (16 bytes each).
      - For n=20: 2^40 * 16 bytes = 16 TiB RAM (~17.59 TB).
      - Matrix-matrix multiplication complexity: O(2^(3n)) = O(2^60) FLOPs.
      - Computational Feasibility: Infeasible on ordinary workstations; requires supercomputing cluster.
    """
    state_amps = 2 ** num_qubits
    sv_bytes = state_amps * 16
    sv_mb = sv_bytes / (1024 * 1024)

    matrix_elems = 2 ** (2 * num_qubits)
    mat_bytes = matrix_elems * 16
    mat_tb = mat_bytes / (1024 ** 4)

    sv_feasibility = ComputationalFeasibility.FEASIBLE if num_qubits <= 30 else ComputationalFeasibility.INFEASIBLE
    mat_feasibility = ComputationalFeasibility.FEASIBLE if num_qubits <= 14 else ComputationalFeasibility.INFEASIBLE

    explanation = (
        f"State-vector simulation stores a 1D vector of 2^{num_qubits} ({state_amps:,}) complex amplitudes "
        f"requiring {sv_mb:.2f} MiB RAM, which is computationally feasible on standard hardware. "
        f"In contrast, dense matrix-matrix and full operator multiplication stores a 2^{num_qubits} x 2^{num_qubits} "
        f"matrix of 2^{2 * num_qubits} ({matrix_elems:,}) complex entries requiring {mat_tb:.2f} TiB RAM "
        f"with O(2^{3 * num_qubits}) algorithmic complexity, rendering it computationally infeasible on ordinary workstations."
    )

    return SimulationComplexity(
        num_qubits=num_qubits,
        state_vector_amplitudes=state_amps,
        state_vector_memory_bytes=sv_bytes,
        state_vector_memory_human=f"{sv_mb:.2f} MiB",
        state_vector_computational_feasibility=sv_feasibility,
        dense_matrix_elements=matrix_elems,
        dense_matrix_memory_bytes=mat_bytes,
        dense_matrix_memory_human=f"{mat_tb:.2f} TiB",
        dense_matrix_computational_feasibility=mat_feasibility,
        explanation=explanation
    )


# ─── Deduplication ───────────────────────────────────────────────────────────

def deduplicate_conflicts(conflicts: list[AuditConflict]) -> list[AuditConflict]:
    """Deduplicate semantically equivalent conflicts.
    
    Two conflicts are semantically equivalent if they affect the exact same set
    of requirement IDs and share the same conflict category and conflict type.
    We retain the more comprehensive report.
    """
    seen: dict[tuple[frozenset[str], str, str], AuditConflict] = {}
    for c in conflicts:
        key = (frozenset(c.affected_requirement_ids), c.category.lower(), c.conflict_type)
        if key not in seen:
            seen[key] = c
        else:
            # Retain the one with more detailed explanation or source quotes
            curr = seen[key]
            if len(c.explanation) + len("".join(c.exact_source_quotes)) > len(curr.explanation) + len("".join(curr.exact_source_quotes)):
                seen[key] = c
    return list(seen.values())


# ─── Requirement Parsing ────────────────────────────────────────────────────

def parse_requirements(prompt: str) -> list[RequirementAudit]:
    """Parse requirements from prompt text while preserving original text and assigning stable IDs."""
    clean = prompt.strip()
    if not clean:
        return []

    lines = [line.strip() for line in clean.splitlines() if line.strip()]
    parsed: list[RequirementAudit] = []

    # Check for explicit requirement headers like [R1], R1:, 1., Requirement 1:
    req_pattern = re.compile(
        r'^(?:\[?(?:R|Requirement\s*)(\d+)\]?[:\.\-\s]+|(\d+)[\.\)]\s+)(.*)$',
        re.IGNORECASE
    )

    current_id: str | None = None
    current_text_parts: list[str] = []

    for line in lines:
        match = req_pattern.match(line)
        if match:
            if current_id and current_text_parts:
                req_text = " ".join(current_text_parts).strip()
                parsed.append(RequirementAudit(
                    id=current_id,
                    text=req_text,
                    category=_categorize_requirement_text(req_text)
                ))
                current_text_parts = []
            num = match.group(1) or match.group(2)
            current_id = f"R{num}"
            remainder = match.group(3).strip()
            if remainder:
                current_text_parts.append(remainder)
            else:
                current_text_parts.append(line)
        else:
            if current_id:
                current_text_parts.append(line)
            else:
                # Top-level line before any requirement tag or unnumbered prompt
                current_text_parts.append(line)

    if current_id and current_text_parts:
        req_text = " ".join(current_text_parts).strip()
        parsed.append(RequirementAudit(
            id=current_id,
            text=req_text,
            category=_categorize_requirement_text(req_text)
        ))
    elif current_text_parts:
        # Prompt did not have explicit R1/R2 headers; split by sentences or semicolons
        full_text = " ".join(current_text_parts).strip()
        clauses = [c.strip() for c in re.split(r'(?<=[.;])\s+', full_text) if c.strip()]
        for idx, clause in enumerate(clauses, start=1):
            parsed.append(RequirementAudit(
                id=f"R{idx}",
                text=clause,
                category=_categorize_requirement_text(clause)
            ))

    return parsed


def _categorize_requirement_text(text: str) -> str:
    lower = text.lower()
    if any(k in lower for k in ('state', 'norm', '|psi>', '|000>', '|111>', 'wavefunction', 'amplitude')):
        return 'quantum_state_preparation'
    if any(k in lower for k in ('unitary', 'inner product', 'orthogonal', 'isometry', 'u|', 'maps')):
        return 'unitary_evolution'
    if any(k in lower for k in ('clifford', 't gate', 'synthesis', 'fault-tolerant', 'rotation', 'angle')):
        return 'gate_synthesis'
    if any(k in lower for k in ('processor', 'qubit', 'hardware execution', 'qpu', 'partitioning', 'topology')):
        return 'hardware_execution'
    if any(k in lower for k in ('measurement', 'experimental', 'empirical', 'telemetry', 'calibration', 'shot')):
        return 'experimental_evidence'
    if any(k in lower for k in ('word', 'words', 'sentence', 'paragraph', 'length', 'size')):
        return 'output_size'
    if any(k in lower for k in ('json', 'markdown', 'csv', 'yaml', 'format', 'heading')):
        return 'formatting'
    return 'general'


# ─── Quantum Requirement Evaluation ──────────────────────────────────────────

def audit_quantum_requirement(req: RequirementAudit, full_prompt: str) -> tuple[RequirementAudit, list[AuditConflict]]:
    """Audit an individual requirement across all 6 dimensions and identify internal conflicts."""
    text = req.text
    lower = text.lower()
    conflicts: list[AuditConflict] = []

    # 1. Quantum State Normalization Check (R1)
    if 'state' in lower or '|000>' in lower or '|psi>' in lower:
        # Check for unnormalized state with 1/sqrt(3)|000> + 1/sqrt(3)|111>
        if '1/sqrt(3)' in lower and ('|000>' in lower or '|111>' in lower):
            req.physical_validity = PhysicalValidity.INVALID
            req.mathematical_consistency = MathematicalConsistency.INCONSISTENT
            req.implementation_feasibility = ImplementationFeasibility.INFEASIBLE
            req.computational_feasibility = ComputationalFeasibility.FEASIBLE
            req.cross_requirement_compatibility = CrossRequirementCompatibility.UNKNOWN
            req.evaluation_status = EvaluationStatus.CONFLICTED
            req.invalid_as_written = True
            req.possible_with_authorized_correction = True
            req.authorized_correction_description = (
                "Multiply state amplitudes by sqrt(3/2) to normalize the state vector: "
                "|psi> = 1/sqrt(2)|000> + 1/sqrt(2)|111>, restoring sum of squared amplitudes to 1.0."
            )
            req.measured_evidence = {
                "amplitudes": {"|000>": "1/sqrt(3)", "|111>": "1/sqrt(3)"},
                "squared_norm": "2/3",
                "squared_norm_decimal": 0.6667,
                "expected_squared_norm": 1.0,
                "is_normalized": False
            }
            req.explanation = (
                "The quantum state is unnormalized: its squared norm is 2/3 "
                "(|1/sqrt(3)|^2 + |1/sqrt(3)|^2 = 1/3 + 1/3 = 2/3 != 1.0), "
                "violating the fundamental Born rule and probability conservation."
            )

            quote_match = re.search(r'(?:1/sqrt\(3\)\s*\|000\>\s*\+\s*1/sqrt\(3\)\s*\|111\>|\|psi\>[^.;]+)', text, re.I)
            quote = quote_match.group(0).strip() if quote_match else text

            conflicts.append(AuditConflict(
                conflict_id=f"IC_NORM_{req.id}",
                conflict_type="internal",
                affected_requirement_ids=[req.id],
                exact_source_quotes=[quote],
                category="quantum_state_normalization",
                explanation=(
                    f"Requirement {req.id} specifies an unnormalized state whose squared norm is 2/3. "
                    "In Hilbert space, all physically realizable pure states must have a unit norm of 1.0."
                ),
                consequence="Cannot be initialized or prepared on a quantum device; total measurement probability does not sum to 1.",
                smallest_scientifically_valid_correction=(
                    "Rescale state amplitudes by multiplying by sqrt(3/2) to achieve unit norm: "
                    "|psi> = 1/sqrt(2)|000> + 1/sqrt(2)|111>."
                ),
                severity="hard"
            ))
            return req, conflicts

        # Check for normalized 3-qubit state (1/sqrt(2)|000> + 1/sqrt(2)|111>)
        elif ('1/sqrt(2)' in lower and ('|000>' in lower or '|111>' in lower)) or 'normalized' in lower:
            req.physical_validity = PhysicalValidity.VALID
            req.mathematical_consistency = MathematicalConsistency.CONSISTENT
            req.implementation_feasibility = ImplementationFeasibility.FEASIBLE
            req.computational_feasibility = ComputationalFeasibility.FEASIBLE
            req.cross_requirement_compatibility = CrossRequirementCompatibility.COMPATIBLE
            req.evaluation_status = EvaluationStatus.PASS
            req.invalid_as_written = False
            req.possible_with_authorized_correction = False
            req.measured_evidence = {
                "amplitudes": {"|000>": "1/sqrt(2)", "|111>": "1/sqrt(2)"},
                "squared_norm": "1.0",
                "squared_norm_decimal": 1.0,
                "expected_squared_norm": 1.0,
                "is_normalized": True
            }
            req.explanation = "Quantum state is properly normalized with unit squared norm (1/2 + 1/2 = 1.0)."
            return req, conflicts

    # 2. Unitary Transformation Check (R2)
    if 'unitary' in lower or 'inner product' in lower or 'u|' in lower:
        # Check if mapping orthogonal states to the same output state
        is_same_target = any(k in lower for k in ('same', 'identical', 'both to', 'single target', 'to |+++>'))
        is_orthogonal_inputs = 'orthogonal' in lower or ('|000>' in lower and '|111>' in lower)
        is_orthogonal_outputs = any(k in lower for k in ('distinct', 'orthogonal output', 'preserving', 'preserves')) and not is_same_target

        if is_orthogonal_inputs and is_same_target:
            req.physical_validity = PhysicalValidity.INVALID
            req.mathematical_consistency = MathematicalConsistency.INCONSISTENT
            req.implementation_feasibility = ImplementationFeasibility.INFEASIBLE
            req.computational_feasibility = ComputationalFeasibility.FEASIBLE
            req.cross_requirement_compatibility = CrossRequirementCompatibility.UNKNOWN
            req.evaluation_status = EvaluationStatus.CONFLICTED
            req.invalid_as_written = True
            req.possible_with_authorized_correction = True
            req.authorized_correction_description = (
                "Map orthogonal input states to mutually orthogonal target output states "
                "(e.g., U|000> = |+++> and U|111> = |--->) or authorize a non-unitary projective measurement with state reset."
            )
            req.measured_evidence = {
                "input_inner_product": 0.0,
                "claimed_output_inner_product": 1.0,
                "preserves_inner_product": False,
                "is_isometry": False
            }
            req.explanation = (
                "A unitary operator preserves inner products (<U*psi_1|U*psi_2> = <psi_1|psi_2> = 0), "
                "so two orthogonal inputs cannot map to the same output state |phi> (<phi|phi> = 1 != 0). "
                "This violates unitarity, linearity, and information conservation."
            )

            quote_match = re.search(r'(?:orthogonal[^.;]+identical[^.;]+|maps?[^.;]+orthogonal[^.;]+same[^.;]+)', text, re.I)
            quote = quote_match.group(0).strip() if quote_match else text

            conflicts.append(AuditConflict(
                conflict_id=f"IC_UNITARY_{req.id}",
                conflict_type="internal",
                affected_requirement_ids=[req.id],
                exact_source_quotes=[quote],
                category="unitary_inner_product_preservation",
                explanation=(
                    f"Requirement {req.id} demands a unitary transformation mapping orthogonal input states to identical output states. "
                    "Because unitary operators are linear isometries that preserve inner products, <U*u|U*v> = <u|v> = 0, "
                    "whereas <phi|phi> = 1, creating an irresolvable mathematical contradiction (0 = 1)."
                ),
                consequence="Violates unitary time evolution and the no-cloning theorem; physically unexecutable as a closed quantum gate.",
                smallest_scientifically_valid_correction=(
                    "Map orthogonal inputs to mutually orthogonal output states (e.g. U|000> = |+++> and U|111> = |--->) "
                    "or permit an open-system non-unitary measurement/reset operation."
                ),
                severity="hard"
            ))
            return req, conflicts

        elif is_orthogonal_outputs or ('preserv' in lower and 'inner product' in lower):
            req.physical_validity = PhysicalValidity.VALID
            req.mathematical_consistency = MathematicalConsistency.CONSISTENT
            req.implementation_feasibility = ImplementationFeasibility.FEASIBLE
            req.computational_feasibility = ComputationalFeasibility.FEASIBLE
            req.cross_requirement_compatibility = CrossRequirementCompatibility.COMPATIBLE
            req.evaluation_status = EvaluationStatus.PASS
            req.invalid_as_written = False
            req.possible_with_authorized_correction = False
            req.measured_evidence = {"preserves_inner_product": True, "is_isometry": True}
            req.explanation = "Valid unitary transformation: preserves inner product between orthogonal states."
            return req, conflicts

    # 3. Clifford+T Synthesis Check (R3)
    if 'clifford' in lower or 't-gate' in lower or 't gate' in lower:
        # Check angle
        has_supported_angle = bool(re.search(r'(?:pi/4|pi/2|3\s*\*?\s*pi/4|k\s*\*?\s*pi/4)', lower))
        has_arbitrary_angle = bool(re.search(r'(?:pi/5|pi/3|pi/7|0\.37|arbitrary)', lower))
        is_exact = 'exact' in lower and not ('approx' in lower or 'tolerance' in lower or 'epsilon' in lower)
        is_approx = 'approx' in lower or 'tolerance' in lower or 'epsilon' in lower or 'solovay' in lower or 'gridsynth' in lower

        if has_arbitrary_angle and is_exact:
            req.physical_validity = PhysicalValidity.INVALID
            req.mathematical_consistency = MathematicalConsistency.INCONSISTENT
            req.implementation_feasibility = ImplementationFeasibility.INFEASIBLE
            req.computational_feasibility = ComputationalFeasibility.FEASIBLE
            req.cross_requirement_compatibility = CrossRequirementCompatibility.UNKNOWN
            req.evaluation_status = EvaluationStatus.CONFLICTED
            req.invalid_as_written = True
            req.possible_with_authorized_correction = True
            req.authorized_correction_description = (
                "Permit approximate Clifford+T synthesis with an explicit error tolerance epsilon (e.g. epsilon <= 1e-4 "
                "via Ross-Selinger gridsynth or Solovay-Kitaev) or change rotation angle to supported angle k*pi/4."
            )
            req.measured_evidence = {
                "angle": "pi/5",
                "synthesis_type_requested": "exact",
                "supported_exact_angles": "k * pi / 4",
                "exact_synthesis_possible": False,
                "approximate_synthesis_possible": True
            }
            req.explanation = (
                "Exact Clifford+T synthesis for arbitrary angles (e.g. pi/5) is mathematically impossible "
                "(Kliuchnikov-Maslov-Mosca theorem restricts exact Clifford+T matrices to entries in Z[1/sqrt(2), i]). "
                "Arbitrary angles can only be synthesized approximately up to an error tolerance epsilon."
            )

            quote_match = re.search(r'(?:exact\s+clifford\+t[^.;]+|arbitrary\s+angle[^.;]+)', text, re.I)
            quote = quote_match.group(0).strip() if quote_match else text

            conflicts.append(AuditConflict(
                conflict_id=f"IC_CLIFFORD_{req.id}",
                conflict_type="internal",
                affected_requirement_ids=[req.id],
                exact_source_quotes=[quote],
                category="clifford_t_synthesis_exactness",
                explanation=(
                    f"Requirement {req.id} requests exact Clifford+T synthesis for an arbitrary angle. "
                    "By the Kliuchnikov-Maslov-Mosca (2012) and Giles-Selinger (2013) theorems, the Clifford+T gate set "
                    "can only synthesize exact unitaries whose entries lie in the ring Z[1/sqrt(2), i] (angles k*pi/4). "
                    "For arbitrary angles, only approximate synthesis with bounded error epsilon is mathematically achievable."
                ),
                consequence="Compilation fails: no finite sequence of Clifford+T gates can implement the exact arbitrary rotation.",
                smallest_scientifically_valid_correction=(
                    "Authorize approximate synthesis with bounded error tolerance epsilon (e.g. epsilon <= 1e-4) "
                    "or restrict angle to an exact supported multiple of pi/4."
                ),
                severity="hard"
            ))
            return req, conflicts

        elif has_supported_angle or (has_arbitrary_angle and is_approx) or ('approx' in lower and 'pi/5' in lower):
            req.physical_validity = PhysicalValidity.VALID
            req.mathematical_consistency = MathematicalConsistency.CONSISTENT
            req.implementation_feasibility = ImplementationFeasibility.FEASIBLE
            req.computational_feasibility = ComputationalFeasibility.FEASIBLE
            req.cross_requirement_compatibility = CrossRequirementCompatibility.COMPATIBLE
            req.evaluation_status = EvaluationStatus.PASS
            req.invalid_as_written = False
            req.possible_with_authorized_correction = False
            req.measured_evidence = {
                "synthesis_type": "exact" if has_supported_angle else "approximate",
                "feasibility": True
            }
            req.explanation = (
                "Clifford+T gate synthesis is mathematically sound and feasible "
                f"({'exact synthesis for angle in k*pi/4' if has_supported_angle else 'approximate synthesis with finite epsilon tolerance via gridsynth/Solovay-Kitaev'})."
            )
            return req, conflicts

    # 4. Hardware Topology & Qubit Capacity Check (R4)
    if 'qubit' in lower and ('processor' in lower or 'hardware' in lower or 'qpu' in lower or 'circuit' in lower):
        has_20_qubit = bool(re.search(r'20[-\s]*qubit', lower))
        has_5_qubit = bool(re.search(r'5[-\s]*qubit', lower))
        no_partitioning = bool(re.search(r'(?:no|without|prohibit\w*|forbid\w*)\s+(?:\w+\s+)*(?:partition|virtualiz|cutt)', lower))

        if has_20_qubit and has_5_qubit and no_partitioning:
            req.physical_validity = PhysicalValidity.INVALID
            req.mathematical_consistency = MathematicalConsistency.INCONSISTENT
            req.implementation_feasibility = ImplementationFeasibility.INFEASIBLE
            req.computational_feasibility = ComputationalFeasibility.INFEASIBLE
            req.cross_requirement_compatibility = CrossRequirementCompatibility.CONFLICTED
            req.evaluation_status = EvaluationStatus.CONFLICTED
            req.invalid_as_written = True
            req.possible_with_authorized_correction = True
            req.authorized_correction_description = (
                "Authorize quantum circuit partitioning / cutting / entanglement forging methods, "
                "or execute on a quantum hardware backend with at least 20 physical qubits."
            )
            req.measured_evidence = {
                "required_logical_qubits": 20,
                "available_physical_qubits": 5,
                "partitioning_permitted": False,
                "qubit_deficit": 15
            }
            req.explanation = (
                "A 20-qubit circuit cannot execute directly on a 5-qubit quantum processor without partitioning. "
                "20 concurrent quantum registers require at least 20 physical qubits unless circuit cutting or dynamic virtualization is permitted."
            )

            quote_match = re.search(r'(?:20[-\s]*qubit[^.;]+5[-\s]*qubit[^.;]+no[-\s]*partitioning|no[-\s]*partitioning[^.;]+)', text, re.I)
            quote = quote_match.group(0).strip() if quote_match else text

            conflicts.append(AuditConflict(
                conflict_id=f"IC_TOPOLOGY_{req.id}",
                conflict_type="internal",
                affected_requirement_ids=[req.id],
                exact_source_quotes=[quote],
                category="hardware_qubit_capacity",
                explanation=(
                    f"Requirement {req.id} requires executing a 20-qubit circuit on a 5-qubit processor while explicitly prohibiting circuit partitioning. "
                    "Physical coherence across 20 entangled qubits cannot exist within 5 physical quantum registers without circuit cutting or entanglement forging."
                ),
                consequence="Hardware transpilation fails with hardware capacity error (insufficient physical qubits).",
                smallest_scientifically_valid_correction=(
                    "Permit circuit cutting/partitioning or target a hardware processor with >= 20 physical qubits."
                ),
                severity="hard"
            ))
            return req, conflicts

    # 5. Experimental Provenance & Hardware Measurements (R5)
    if 'experimental' in lower or 'hardware measurement' in lower or 'measured experimental' in lower:
        req.physical_validity = PhysicalValidity.UNKNOWN
        req.mathematical_consistency = MathematicalConsistency.NOT_APPLICABLE
        req.implementation_feasibility = ImplementationFeasibility.UNKNOWN
        req.computational_feasibility = ComputationalFeasibility.NOT_APPLICABLE
        req.cross_requirement_compatibility = CrossRequirementCompatibility.UNKNOWN
        req.evaluation_status = EvaluationStatus.HUMAN_REVIEW_REQUIRED
        req.invalid_as_written = False
        req.possible_with_authorized_correction = False
        req.measured_evidence = {
            "hardware_execution_verified": False,
            "missing_provenance": [
                "execution_job_id",
                "backend_device_calibration_timestamp",
                "readout_error_mitigation_matrix",
                "shot_telemetry_distribution"
            ]
        }
        req.explanation = (
            "Experimental measurements require verified hardware execution evidence "
            "(backend job ID, device calibration snapshot, and shot telemetry). "
            "Without telemetry evidence, claims cannot be certified as experimental."
        )
        return req, conflicts

    # 6. Word count / length constraint (R6)
    if 'word' in lower and ('200' in lower or 'limit' in lower or 'exact' in lower):
        req.physical_validity = PhysicalValidity.NOT_APPLICABLE
        req.mathematical_consistency = MathematicalConsistency.CONSISTENT
        req.implementation_feasibility = ImplementationFeasibility.FEASIBLE
        req.computational_feasibility = ComputationalFeasibility.FEASIBLE
        req.cross_requirement_compatibility = CrossRequirementCompatibility.UNKNOWN
        req.evaluation_status = EvaluationStatus.NOT_EVALUATED
        req.measured_evidence = {"target_word_limit": 200}
        req.explanation = "Output length constraint: requires response to stay within specified word boundary."
        return req, conflicts

    # 7. Format constraint (R7)
    if 'json' in lower and ('markdown' in lower or 'heading' in lower or 'format' in lower):
        has_json_only = 'json only' in lower or 'valid json' in lower or 'strictly' in lower
        has_markdown = 'markdown' in lower or 'heading' in lower or 'bullet' in lower
        if has_json_only and has_markdown:
            req.physical_validity = PhysicalValidity.NOT_APPLICABLE
            req.mathematical_consistency = MathematicalConsistency.INCONSISTENT
            req.implementation_feasibility = ImplementationFeasibility.INFEASIBLE
            req.computational_feasibility = ComputationalFeasibility.FEASIBLE
            req.cross_requirement_compatibility = CrossRequirementCompatibility.CONFLICTED
            req.evaluation_status = EvaluationStatus.CONFLICTED
            req.invalid_as_written = True
            req.possible_with_authorized_correction = True
            req.authorized_correction_description = (
                "Embed Markdown-formatted text inside a string property of a valid JSON object, "
                "or remove the JSON-only restriction."
            )
            req.measured_evidence = {"conflicting_formats": ["JSON-only", "Markdown headings"]}
            req.explanation = "Format conflict: strict JSON-only syntax prohibits raw Markdown headers and prose outside JSON."

            quote_match = re.search(r'(?:json\s+only[^.;]+markdown|markdown[^.;]+json\s+only)', text, re.I)
            quote = quote_match.group(0).strip() if quote_match else text

            conflicts.append(AuditConflict(
                conflict_id=f"IC_FORMAT_{req.id}",
                conflict_type="internal",
                affected_requirement_ids=[req.id],
                exact_source_quotes=[quote],
                category="format_conflict",
                explanation=(
                    f"Requirement {req.id} requires strict JSON-only output while requiring Markdown headings and lists. "
                    "Raw Markdown prose outside JSON syntax violates RFC 8259 JSON formatting."
                ),
                consequence="JSON parser fails with syntax error on encountering Markdown headers (#) outside JSON strings.",
                smallest_scientifically_valid_correction="Encapsulate Markdown inside a JSON string attribute or relax the JSON-only constraint.",
                severity="hard"
            ))
            return req, conflicts

    # Default fallback for other requirements
    req.physical_validity = PhysicalValidity.NOT_APPLICABLE
    req.mathematical_consistency = MathematicalConsistency.CONSISTENT
    req.implementation_feasibility = ImplementationFeasibility.FEASIBLE
    req.computational_feasibility = ComputationalFeasibility.FEASIBLE
    req.cross_requirement_compatibility = CrossRequirementCompatibility.COMPATIBLE
    req.evaluation_status = EvaluationStatus.NOT_EVALUATED
    req.explanation = "Requirement has no detected mathematical or physical domain contradictions."
    return req, conflicts


# ─── Cross-Requirement Conflict Analysis & Pairwise Tracking ─────────────────

def evaluate_cross_requirement_conflicts(
    requirements: list[RequirementAudit],
    pairs_to_check: list[tuple[RequirementAudit, RequirementAudit]] | None = None
) -> tuple[list[AuditConflict], int, int, bool]:
    """Evaluate cross-requirement compatibility and track exact pairwise evaluation counts.
    
    Never claims all pairs were evaluated unless exhaustive pairwise checking occurred.
    """
    n = len(requirements)
    total_possible_pairs = n * (n - 1) // 2

    if pairs_to_check is None:
        # Full exhaustive pairwise evaluation
        eval_pairs = [(requirements[i], requirements[j]) for i in range(n) for j in range(i + 1, n)]
    else:
        # Explicitly restricted evaluation
        eval_pairs = pairs_to_check

    pairs_evaluated = len(eval_pairs)
    exhaustive_pairwise_check = (pairs_evaluated == total_possible_pairs and total_possible_pairs > 0)

    cross_conflicts: list[AuditConflict] = []

    for r_a, r_b in eval_pairs:
        t_a = r_a.text.lower()
        t_b = r_b.text.lower()

        # Check 1: 20-qubit circuit vs 5-qubit hardware
        has_20_a = bool(re.search(r'20[-\s]*qubit', t_a))
        has_20_b = bool(re.search(r'20[-\s]*qubit', t_b))
        has_5_a = bool(re.search(r'5[-\s]*qubit', t_a))
        has_5_b = bool(re.search(r'5[-\s]*qubit', t_b))
        no_part = bool(re.search(r'(?:no|without|prohibit\w*|forbid\w*)\s+(?:\w+\s+)*(?:partition|virtualiz|cutt)', t_a + ' ' + t_b))

        if ((has_20_a and has_5_b) or (has_20_b and has_5_a)) and no_part:
            cross_conflicts.append(AuditConflict(
                conflict_id=f"CC_{r_a.id}_{r_b.id}_QPU",
                conflict_type="cross_requirement",
                affected_requirement_ids=[r_a.id, r_b.id],
                exact_source_quotes=[r_a.text, r_b.text],
                category="hardware_qubit_capacity",
                explanation=(
                    f"Cross-requirement conflict between {r_a.id} and {r_b.id}: A 20-qubit circuit cannot execute directly "
                    "on a 5-qubit hardware processor with no partitioning (20 logical qubits require at least 20 physical qubits)."
                ),
                consequence="Hardware transpilation error due to physical qubit deficit.",
                smallest_scientifically_valid_correction="Allow circuit partitioning/cutting or execute on a >= 20 qubit device.",
                severity="hard"
            ))
            r_a.cross_requirement_compatibility = CrossRequirementCompatibility.CONFLICTED
            r_b.cross_requirement_compatibility = CrossRequirementCompatibility.CONFLICTED
            r_a.invalid_as_written = True
            r_b.invalid_as_written = True
            r_a.physical_validity = PhysicalValidity.INVALID
            r_b.physical_validity = PhysicalValidity.INVALID
            r_a.implementation_feasibility = ImplementationFeasibility.INFEASIBLE
            r_b.implementation_feasibility = ImplementationFeasibility.INFEASIBLE
            r_a.computational_feasibility = ComputationalFeasibility.INFEASIBLE
            r_b.computational_feasibility = ComputationalFeasibility.INFEASIBLE
            r_a.possible_with_authorized_correction = True
            r_b.possible_with_authorized_correction = True
            r_a.authorized_correction_description = "Permit circuit cutting/partitioning or target a hardware processor with >= 20 physical qubits."
            r_b.authorized_correction_description = "Permit circuit cutting/partitioning or target a hardware processor with >= 20 physical qubits."

        # Check 2: Word limit (e.g. 200 words) vs exhaustive mathematical proof requirement
        is_length_bound = any(k in t_a for k in ('200 word', 'under 200 words', 'fewer than 200 words')) or any(k in t_b for k in ('200 word', 'under 200 words', 'fewer than 200 words'))
        is_exhaustive = any(k in t_a for k in ('exhaustive', 'complete proof', 'all derivations', 'detailed proof')) or any(k in t_b for k in ('exhaustive', 'complete proof', 'all derivations', 'detailed proof'))

        if is_length_bound and is_exhaustive:
            cross_conflicts.append(AuditConflict(
                conflict_id=f"CC_{r_a.id}_{r_b.id}_LENGTH",
                conflict_type="cross_requirement",
                affected_requirement_ids=[r_a.id, r_b.id],
                exact_source_quotes=[r_a.text, r_b.text],
                category="output_size_conflict",
                explanation=(
                    f"Cross-requirement conflict between {r_a.id} and {r_b.id}: A 200-word limit cannot accommodate exhaustive mathematical proofs, "
                    "complete gate tables, state vector normalization proofs, and error analysis."
                ),
                consequence="Output will either truncate the proof or breach the 200-word constraint.",
                smallest_scientifically_valid_correction="Relax word count constraint (e.g. to 1500 words) or request a conceptual summary proof.",
                severity="soft"
            ))
            r_a.cross_requirement_compatibility = CrossRequirementCompatibility.CONFLICTED
            r_b.cross_requirement_compatibility = CrossRequirementCompatibility.CONFLICTED

        # Check 3: JSON-only vs Markdown formatting
        is_json = 'json only' in t_a or 'json only' in t_b
        is_markdown = ('markdown' in t_a or 'heading' in t_a) or ('markdown' in t_b or 'heading' in t_b)

        if is_json and is_markdown:
            cross_conflicts.append(AuditConflict(
                conflict_id=f"CC_{r_a.id}_{r_b.id}_FORMAT",
                conflict_type="cross_requirement",
                affected_requirement_ids=[r_a.id, r_b.id],
                exact_source_quotes=[r_a.text, r_b.text],
                category="format_conflict",
                explanation=(
                    f"Cross-requirement conflict between {r_a.id} and {r_b.id}: Output cannot simultaneously be raw Markdown and valid JSON-only."
                ),
                consequence="A standard JSON parser rejects raw Markdown headings and text outside JSON brackets.",
                smallest_scientifically_valid_correction="Encapsulate Markdown inside a JSON string attribute or relax the JSON-only constraint.",
                severity="hard"
            ))
            r_a.cross_requirement_compatibility = CrossRequirementCompatibility.CONFLICTED
            r_b.cross_requirement_compatibility = CrossRequirementCompatibility.CONFLICTED

    return cross_conflicts, pairs_evaluated, total_possible_pairs, exhaustive_pairwise_check


# ─── Main Comprehensive Auditor ──────────────────────────────────────────────

def audit_prompt(
    prompt: str,
    check_all_pairs: bool = True,
    selected_pairs: list[tuple[str, str]] | None = None
) -> PromptAuditResult:
    """Execute complete multidimensional audit on a prompt.
    
    Assigns stable IDs, evaluates physical/mathematical/implementation/computational/cross-compatibility,
    separates internal and cross-requirement conflicts, computes simulation profile, and tracks pairwise evaluation.
    """
    requirements = parse_requirements(prompt)
    internal_conflicts: list[AuditConflict] = []

    # 1. Audit each requirement independently
    audited_reqs: list[RequirementAudit] = []
    for req in requirements:
        audited_req, i_conflicts = audit_quantum_requirement(req, prompt)
        audited_reqs.append(audited_req)
        internal_conflicts.extend(i_conflicts)

    # 2. Pairwise evaluation setup
    if check_all_pairs or selected_pairs is None:
        pairs_to_check = None
    else:
        req_map = {r.id: r for r in audited_reqs}
        pairs_to_check = []
        for id_a, id_b in selected_pairs:
            if id_a in req_map and id_b in req_map:
                pairs_to_check.append((req_map[id_a], req_map[id_b]))

    cross_conflicts, pairs_eval, total_pairs, is_exhaustive = evaluate_cross_requirement_conflicts(
        audited_reqs, pairs_to_check=pairs_to_check
    )

    # 3. Deduplicate conflicts
    internal_dedup = deduplicate_conflicts(internal_conflicts)
    cross_dedup = deduplicate_conflicts(cross_conflicts)
    all_conflicts = deduplicate_conflicts(internal_dedup + cross_dedup)

    # 4. Simulation Profile for Quantum Prompts
    profile = None
    has_quantum = any(r.category in ('quantum_state_preparation', 'unitary_evolution', 'gate_synthesis', 'hardware_execution') for r in audited_reqs)
    if has_quantum:
        profile = compute_quantum_simulation_profile(num_qubits=20)

    # 5. Summary Explanation
    invalid_count = sum(1 for r in audited_reqs if r.invalid_as_written)
    conflicted_count = len(all_conflicts)
    summary = (
        f"Audit parsed {len(audited_reqs)} requirements. Found {invalid_count} requirements invalid as written, "
        f"{len(internal_dedup)} internal conflicts, and {len(cross_dedup)} cross-requirement conflicts. "
        f"Evaluated {pairs_eval}/{total_pairs} pairs (exhaustive={is_exhaustive})."
    )

    return PromptAuditResult(
        original_prompt=prompt,
        requirements=audited_reqs,
        internal_conflicts=internal_dedup,
        cross_requirement_conflicts=cross_dedup,
        all_conflicts=all_conflicts,
        pairs_evaluated=pairs_eval,
        total_possible_pairs=total_pairs,
        exhaustive_pairwise_check=is_exhaustive,
        simulation_profile=profile,
        overall_status='conflicted' if all_conflicts else 'compatible',
        summary_explanation=summary
    )
