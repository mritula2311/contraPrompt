"""Public contracts. All spans use half-open Python Unicode character offsets."""
from enum import StrEnum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class Label(StrEnum):
    COMPATIBLE = 'Compatible'
    PARTIAL = 'Partially conflicting'
    IMPOSSIBLE = 'Fully impossible'
    UNSPECIFIED = 'Underspecified'

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

class Instruction(StrictModel):
    id: str
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text: str
    normalized: str
    scope: str = 'response'
    kind: Literal['numerical','logical','temporal','formatting','semantic','missing','other']
    key: str = ''
    value: str = ''
    lower: int | None = None
    upper: int | None = None
    soft: bool = False
    source: Literal['rule','llm'] = 'rule'
    source_role: Literal['system', 'developer', 'user', 'context', 'untrusted'] = 'user'
    experimental_trust_tier: int = 3
    provenance: str = 'user_prompt'
    active_instruction_status: bool = True
    entity: str = ''
    target: str = 'response'
    operator: str | None = None
    minimum: int | None = None
    maximum: int | None = None
    condition: str | None = None
    exceptions: list[str] = Field(default_factory=list)
    negation: bool = False
    temporal_dependency: str | None = None
    constraint_type: str | None = None

    @property
    def instruction_id(self) -> str:
        return self.id

    @model_validator(mode='after')
    def ordered_span(self):
        if self.end <= self.start:
            raise ValueError('End must be after start')
        if not self.constraint_type:
            self.constraint_type = self.kind
        if self.minimum is None and self.lower is not None:
            self.minimum = self.lower
        if self.maximum is None and self.upper is not None:
            self.maximum = self.upper
        if self.lower is None and self.minimum is not None:
            self.lower = self.minimum
        if self.upper is None and self.maximum is not None:
            self.upper = self.maximum
        return self

class Conflict(StrictModel):
    instruction_ids: list[str] = Field(min_length=1)
    kind: Literal['numerical','logical','temporal','formatting','semantic']
    explanation: str = Field(min_length=1)
    severity: Literal['hard','soft']
    source: Literal['rule','llm'] = 'rule'
    scope: str = 'response'
    target: str = ''
    canonical_id: str = ''
    evidence: list[str] = Field(default_factory=list)

class Usage(StrictModel):
    calls: int = 0
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: float = 0

class GraphNode(StrictModel):
    id: str
    text: str
    kind: str
    scope: str = 'response'
    normalized: str = ''

class GraphEdge(StrictModel):
    source: str
    target: str
    relation: Literal['compatible', 'conflicting', 'dependent', 'conditional', 'uncertain']
    description: str = ''

class ConstraintGraphData(StrictModel):
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)

class Assessment(StrictModel):
    original: str
    normalized: str
    label: Label
    instructions: list[Instruction] = Field(default_factory=list)
    conflicts: list[Conflict] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)
    explanation: str
    warnings: list[str] = Field(default_factory=list)
    mode: str = 'rules'
    usage: Usage = Field(default_factory=Usage)
    latency_ms: float = 0
    semantic_checked: bool = False
    secondary_flags: list[str] = Field(default_factory=list)
    minimal_conflicting_sets: list[list[str]] = Field(default_factory=list)
    constraint_graph: ConstraintGraphData | None = None

    @model_validator(mode='after')
    def grounded(self):
        ids = [i.id for i in self.instructions]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate instruction IDs')
        for i in self.instructions:
            if i.end > len(self.original) or self.original[i.start:i.end] != i.text:
                raise ValueError('Instruction span is not grounded in original prompt')
        for c in self.conflicts:
            if not set(c.instruction_ids).issubset(ids):
                raise ValueError('Unknown conflict instruction ID')
        return self

class Patch(StrictModel):
    start: int
    end: int
    replacement: str
    removed_text: str

class Repair(StrictModel):
    id: str
    description: str
    prompt: str
    patch: Patch
    requires_approval: bool = True

class LLMAnalysis(StrictModel):
    instructions: list[Instruction]
    label: Label
    conflicts: list[Conflict]
    clarification_questions: list[str]
    explanation: str


# ─── V3 Intelligent Multi-Repair Contracts ────────────────────────────────────

class RepairOption(StrictModel):
    repair_id: str
    conflict_id: str
    instruction_ids: list[str] = Field(default_factory=list)
    repair_type: str = 'reconcile'
    original_text: str
    proposed_text: str
    target_scope: str = 'response'
    start: int
    end: int
    description: str
    expected_effect: str = ''
    strategy: Literal['deterministic', 'llm_assisted', 'hybrid'] = 'deterministic'
    requires_approval: bool = True


class RepairGroup(StrictModel):
    conflict_id: str
    conflict_type: str
    severity: Literal['hard', 'soft'] = 'hard'
    explanation: str
    instruction_ids: list[str] = Field(default_factory=list)
    scope: str = 'response'
    options: list[RepairOption] = Field(default_factory=list)


class SelectedRepair(StrictModel):
    repair_id: str
    conflict_id: str
    custom_text: str | None = None


class BatchRepairRequest(StrictModel):
    original_prompt: str
    selected_repairs: list[SelectedRepair] = Field(default_factory=list)
    approved: bool = False
    mode: str = 'rules'


class DiffChunk(StrictModel):
    conflict_id: str
    removed_text: str
    added_text: str
    start: int
    end: int


class BatchRepairPreview(StrictModel):
    original_prompt: str
    revised_prompt: str
    applied_repairs: list[RepairOption] = Field(default_factory=list)
    diff_summary: list[DiffChunk] = Field(default_factory=list)
    is_compatible: bool = True
    compatibility_status: str = 'Compatible Batch'
    compatibility_issues: list[str] = Field(default_factory=list)
    predicted_resolved_conflicts: list[str] = Field(default_factory=list)
    remaining_conflicts_count: int = 0
    repairs_selected_count: int = 0
    conflicts_addressed_count: int = 0
    unresolved_count: int = 0


class BatchRepairResult(StrictModel):
    success: bool
    revised_prompt: str
    previous_label: str
    revalidated_label: str
    resolved_conflicts: list[str] = Field(default_factory=list)
    remaining_conflicts: list[str] = Field(default_factory=list)
    new_conflicts: list[str] = Field(default_factory=list)
    preserved_instructions_count: int = 0
    revalidated_assessment: Assessment
    repairs_selected_count: int = 0
    conflicts_addressed_count: int = 0
    compatibility_status: str = 'Compatible Batch'
    edits_applied_count: int = 0
    verified_resolved_count: int = 0
    unresolved_count: int = 0
    revalidation_verified: bool = True


class SessionState(StrictModel):
    session_id: str = 'default_session'
    prompt_revision: int = 1
    original_prompt: str = ''
    current_prompt: str = ''
    trusted_role_messages: list[dict] = Field(default_factory=list)
    context_documents: list[dict] = Field(default_factory=list)
    current_assessment: Assessment | None = None
    priority_resolution: dict | None = None
    repair_groups: list[RepairGroup] = Field(default_factory=list)
    selected_repairs: list[SelectedRepair] = Field(default_factory=list)
    batch_preview: BatchRepairPreview | None = None
    batch_result: BatchRepairResult | None = None
    revalidated_prompt: str = ''
    response_generation_status: str = 'idle'
    generated_response: dict | None = None
    output_verification: dict | None = None
    is_stale: bool = False

