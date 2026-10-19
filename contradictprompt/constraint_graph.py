"""Cross-Instruction Conflict Graph (Layer C).

Represents instructions as nodes and their interactions (conflicting, dependent,
conditional, compatible, uncertain) as typed edges. Analyzes complex multi-instruction
cliques and extracts minimal conflicting sets.
"""
from typing import Literal, Sequence
from .models import Instruction, Conflict

RelationType = Literal['compatible', 'conflicting', 'dependent', 'conditional', 'uncertain']

class GraphEdge:
    def __init__(self, source_id: str, target_id: str, relation: RelationType, description: str = ''):
        self.source_id = source_id
        self.target_id = target_id
        self.relation = relation
        self.description = description

    def to_dict(self) -> dict:
        return {
            'source': self.source_id,
            'target': self.target_id,
            'relation': self.relation,
            'description': self.description
        }

class ConstraintGraph:
    """Directed graph representing cross-instruction dependencies and conflicts."""

    def __init__(self):
        self.nodes: dict[str, Instruction] = {}
        self.edges: list[GraphEdge] = []
        self.adjacency: dict[str, list[tuple[str, RelationType, str]]] = {}

    def add_node(self, instruction: Instruction) -> None:
        self.nodes[instruction.id] = instruction
        if instruction.id not in self.adjacency:
            self.adjacency[instruction.id] = []

    def add_edge(self, source_id: str, target_id: str, relation: RelationType, description: str = '') -> None:
        if source_id not in self.nodes or target_id not in self.nodes:
            return
        edge = GraphEdge(source_id, target_id, relation, description)
        self.edges.append(edge)
        self.adjacency.setdefault(source_id, []).append((target_id, relation, description))

    @classmethod
    def build(cls, instructions: Sequence[Instruction], conflicts: Sequence[Conflict]) -> 'ConstraintGraph':
        """Construct the constraint graph from extracted instructions and detected conflicts."""
        graph = cls()
        for ins in instructions:
            graph.add_node(ins)

        # 1. Map existing explicit conflicts into 'conflicting' edges
        for conflict in conflicts:
            ids = conflict.instruction_ids
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    graph.add_edge(ids[i], ids[j], 'conflicting', conflict.explanation)
                    graph.add_edge(ids[j], ids[i], 'conflicting', conflict.explanation)

        # 2. Map dependencies into 'dependent' edges
        for ins in instructions:
            if ins.key == 'dependency' and '->' in ins.value:
                # Value format: 'Phase A->Phase B'
                try:
                    src_phase, tgt_phase = ins.value.split('->', 1)
                    src_phase, tgt_phase = src_phase.strip(), tgt_phase.strip()
                    # Find instructions matching these phases
                    src_nodes = [i.id for i in instructions if src_phase.lower() in i.text.lower() and i.id != ins.id]
                    tgt_nodes = [i.id for i in instructions if tgt_phase.lower() in i.text.lower() and i.id != ins.id]
                    for s_id in src_nodes:
                        for t_id in tgt_nodes:
                            graph.add_edge(s_id, t_id, 'dependent', f"{src_phase} depends on {tgt_phase}")
                except Exception:
                    pass

        # 3. Map conditional requirements into 'conditional' edges
        for ins in instructions:
            if ins.condition:
                for other in instructions:
                    if other.id != ins.id and ins.condition.lower() in other.text.lower():
                        graph.add_edge(ins.id, other.id, 'conditional', f"Condition: {ins.condition}")

        return graph

    def detect_cycles(self) -> list[list[str]]:
        """Detect circular dependencies using DFS on 'dependent' edges."""
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node: str, path: list[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor, relation, _ in self.adjacency.get(node, []):
                if relation == 'dependent':
                    if neighbor not in visited:
                        dfs(neighbor, path)
                    elif neighbor in rec_stack:
                        cycle_start = path.index(neighbor)
                        cycle = path[cycle_start:] + [neighbor]
                        cycles.append(cycle)

            rec_stack.remove(node)
            path.pop()

        for node_id in self.nodes:
            if node_id not in visited:
                dfs(node_id, [])

        return cycles

    def find_minimal_conflicting_sets(self) -> list[list[str]]:
        """Extract minimal conflicting sets of instruction IDs."""
        minimal_sets: list[list[str]] = []

        # Find connected components of conflicting subgraphs
        conflicting_edges = [e for e in self.edges if e.relation == 'conflicting']
        seen_pairs = set()

        for edge in conflicting_edges:
            pair = tuple(sorted([edge.source_id, edge.target_id]))
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                minimal_sets.append(list(pair))

        return minimal_sets

    def to_dict(self) -> dict:
        """Serialize graph to JSON-compatible dictionary for UI visualization."""
        return {
            'nodes': [
                {
                    'id': ins.id,
                    'text': ins.text,
                    'kind': ins.kind,
                    'scope': ins.scope,
                    'normalized': ins.normalized
                }
                for ins in self.nodes.values()
            ],
            'edges': [e.to_dict() for e in self.edges]
        }
