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
    target: str = 'response'
    operator: str | None = None
    condition: str | None = None
    exceptions: list[str] = Field(default_factory=list)
    negation: bool = False
    temporal_dependency: str | None = None
    constraint_type: str | None = None

    @model_validator(mode='after')
    def ordered_span(self):
        if self.end <= self.start:
            raise ValueError('End must be after start')
        if not self.constraint_type:
            self.constraint_type = self.kind
        return self

class Conflict(StrictModel):
    instruction_ids: list[str] = Field(min_length=1)
    kind: Literal['numerical','logical','temporal','formatting','semantic']
    explanation: str = Field(min_length=1)
    severity: Literal['hard','soft']
    source: Literal['rule','llm'] = 'rule'

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
