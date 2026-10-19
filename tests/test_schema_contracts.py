"""
Pydantic v2 Schema Contract Test Suite
======================================
Strict verification of all data models:
- Assessment
- Instruction
- Conflict
- Usage
- GraphNode, GraphEdge, ConstraintGraphData
- Patch, Repair
- LLMAnalysis
- StrictModel ConfigDict(extra='forbid') enforcement
"""
import pytest
from pydantic import ValidationError
from contradictprompt import Label
from contradictprompt.models import (
    Instruction, Conflict, Usage, GraphNode, GraphEdge,
    ConstraintGraphData, Assessment, Patch, Repair, LLMAnalysis
)

# ─── Instruction Schema Tests ───────────────────────────────────

def test_instruction_valid():
    ins = Instruction(
        id="I1", start=0, end=10, text="Write poem", normalized="action: poem",
        scope="response", kind="semantic", key="genre", value="poem"
    )
    assert ins.id == "I1"
    assert ins.start == 0
    assert ins.end == 10
    assert ins.source == "rule"
    assert ins.constraint_type == "semantic"

def test_instruction_missing_required_fields():
    with pytest.raises(ValidationError):
        Instruction(start=0, end=10, text="foo")  # Missing id, normalized, kind

def test_instruction_unexpected_extra_forbidden():
    with pytest.raises(ValidationError, match="extra_forbidden"):
        Instruction(
            id="I1", start=0, end=10, text="foo", normalized="foo",
            kind="semantic", unexpected_extra_field="disallowed"
        )

def test_instruction_invalid_span_order():
    with pytest.raises(ValidationError, match="End must be after start"):
        Instruction(
            id="I1", start=10, end=5, text="foo", normalized="foo", kind="semantic"
        )

def test_instruction_serialization_roundtrip():
    ins = Instruction(
        id="I1", start=5, end=20, text="exactly 5 words", normalized="word: [5, 5]",
        scope="body", kind="numerical", key="word", lower=5, upper=5, soft=False
    )
    dumped = ins.model_dump(mode="json")
    loaded = Instruction.model_validate(dumped)
    assert loaded == ins

# ─── Conflict Schema Tests ──────────────────────────────────────

def test_conflict_valid():
    c = Conflict(
        instruction_ids=["I1", "I2"], kind="numerical",
        explanation="Mutually exclusive bounds", severity="hard"
    )
    assert c.kind == "numerical"
    assert c.severity == "hard"
    assert c.source == "rule"

def test_conflict_invalid_kind():
    with pytest.raises(ValidationError):
        Conflict(instruction_ids=["I1"], kind="invalid_kind", explanation="foo", severity="hard")

def test_conflict_invalid_severity():
    with pytest.raises(ValidationError):
        Conflict(instruction_ids=["I1"], kind="logical", explanation="foo", severity="critical")

def test_conflict_empty_instruction_ids():
    with pytest.raises(ValidationError):
        Conflict(instruction_ids=[], kind="logical", explanation="foo", severity="hard")

# ─── ConstraintGraph Schema Tests ───────────────────────────────

def test_constraint_graph_data_valid():
    node1 = GraphNode(id="I1", text="5 words", kind="numerical", scope="response")
    node2 = GraphNode(id="I2", text="10 words", kind="numerical", scope="response")
    edge = GraphEdge(source="I1", target="I2", relation="conflicting", description="conflict")
    graph = ConstraintGraphData(nodes=[node1, node2], edges=[edge])
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1

def test_constraint_graph_extra_forbidden():
    with pytest.raises(ValidationError, match="extra_forbidden"):
        ConstraintGraphData(nodes=[], edges=[], random_field=123)

# ─── Assessment Schema Tests ────────────────────────────────────

def test_assessment_valid():
    prompt = "Write 5 words. Write 10 words."
    i1 = Instruction(id="I1", start=0, end=13, text="Write 5 words", normalized="w: 5", kind="numerical")
    i2 = Instruction(id="I2", start=15, end=29, text="Write 10 words", normalized="w: 10", kind="numerical")
    c1 = Conflict(instruction_ids=["I1", "I2"], kind="numerical", explanation="mismatch", severity="hard")
    node1 = GraphNode(id="I1", text=i1.text, kind=i1.kind, scope=i1.scope)
    node2 = GraphNode(id="I2", text=i2.text, kind=i2.kind, scope=i2.scope)
    edge = GraphEdge(source="I1", target="I2", relation="conflicting")
    graph = ConstraintGraphData(nodes=[node1, node2], edges=[edge])

    asm = Assessment(
        original=prompt,
        normalized=prompt,
        label=Label.IMPOSSIBLE,
        instructions=[i1, i2],
        conflicts=[c1],
        explanation="Contradiction",
        constraint_graph=graph
    )
    assert asm.label == Label.IMPOSSIBLE
    assert asm.constraint_graph is not None
    assert len(asm.constraint_graph.edges) == 1

def test_assessment_ungrounded_instruction_raises():
    with pytest.raises(ValidationError, match="not grounded"):
        Instruction_bad = Instruction(id="I1", start=0, end=5, text="wrong text", normalized="w", kind="semantic")
        Assessment(
            original="Real prompt here",
            normalized="Real prompt here",
            label=Label.COMPATIBLE,
            instructions=[Instruction_bad],
            conflicts=[],
            explanation="fine"
        )

def test_assessment_unknown_conflict_id_raises():
    prompt = "Write 5 words."
    i1 = Instruction(id="I1", start=0, end=13, text="Write 5 words", normalized="w", kind="semantic")
    c_bad = Conflict(instruction_ids=["I1", "I999"], kind="semantic", explanation="bad", severity="soft")
    with pytest.raises(ValidationError, match="Unknown conflict instruction ID"):
        Assessment(
            original=prompt,
            normalized=prompt,
            label=Label.PARTIAL,
            instructions=[i1],
            conflicts=[c_bad],
            explanation="bad"
        )

def test_assessment_serialization_and_deserialization_roundtrip():
    prompt = "Hello world."
    i1 = Instruction(id="I1", start=0, end=5, text="Hello", normalized="k: v", kind="other")
    asm = Assessment(
        original=prompt,
        normalized=prompt,
        label=Label.COMPATIBLE,
        instructions=[i1],
        conflicts=[],
        explanation="Valid",
        constraint_graph=ConstraintGraphData(
            nodes=[GraphNode(id="I1", text="Hello", kind="other")],
            edges=[]
        )
    )
    dumped = asm.model_dump(mode="json")
    assert "constraint_graph" in dumped
    reloaded = Assessment.model_validate(dumped)
    assert reloaded.original == asm.original
    assert reloaded.constraint_graph.nodes[0].id == "I1"

# ─── Patch & Repair Schema Tests ────────────────────────────────

def test_repair_model_valid():
    p = Patch(start=0, end=5, replacement="Hi", removed_text="Hello")
    r = Repair(id="R1", description="Replace Hello with Hi", prompt="Hi world.", patch=p)
    assert r.id == "R1"
    assert r.requires_approval is True
    assert r.patch.replacement == "Hi"

def test_repair_extra_forbidden():
    p = Patch(start=0, end=5, replacement="Hi", removed_text="Hello")
    with pytest.raises(ValidationError, match="extra_forbidden"):
        Repair(id="R1", description="desc", prompt="p", patch=p, unauthorized_field="bad")

# ─── LLMAnalysis Schema Tests ───────────────────────────────────

def test_llm_analysis_valid():
    i1 = Instruction(id="I1", start=0, end=4, text="Test", normalized="k: v", kind="semantic", source="llm")
    c1 = Conflict(instruction_ids=["I1"], kind="semantic", explanation="why", severity="hard", source="llm")
    analysis = LLMAnalysis(
        instructions=[i1],
        label=Label.IMPOSSIBLE,
        conflicts=[c1],
        clarification_questions=[],
        explanation="LLM detected contradiction"
    )
    assert analysis.label == Label.IMPOSSIBLE
    assert analysis.instructions[0].source == "llm"
