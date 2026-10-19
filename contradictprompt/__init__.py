"""ContradictPrompt: scoped instruction checking with optional LLM analysis."""
__version__ = '1.0.1'
from .engine import analyze
from .models import Label
from .audit import (
    audit_prompt,
    PromptAuditResult,
    RequirementAudit,
    AuditConflict,
    EvaluationStatus,
    PhysicalValidity,
    MathematicalConsistency,
    ImplementationFeasibility,
    ComputationalFeasibility,
    CrossRequirementCompatibility,
    compute_quantum_simulation_profile,
    deduplicate_conflicts
)
from .satisfaction import check_response, evaluate_audit_satisfaction

__all__ = [
    'analyze',
    'Label',
    'audit_prompt',
    'PromptAuditResult',
    'RequirementAudit',
    'AuditConflict',
    'EvaluationStatus',
    'PhysicalValidity',
    'MathematicalConsistency',
    'ImplementationFeasibility',
    'ComputationalFeasibility',
    'CrossRequirementCompatibility',
    'compute_quantum_simulation_profile',
    'deduplicate_conflicts',
    'check_response',
    'evaluate_audit_satisfaction'
]
