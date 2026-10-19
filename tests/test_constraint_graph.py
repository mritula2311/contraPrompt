"""Unit tests for Layer C Cross-Instruction Constraint Graph."""
import pytest
from contradictprompt.models import Instruction, Conflict
from contradictprompt.constraint_graph import ConstraintGraph

def test_graph_cycle_detection():
    """Verify that circular workflow dependencies are accurately identified."""
    i1 = Instruction(id='I1', start=0, end=10, text='Phase A', normalized='Phase A', kind='temporal',
                     key='dependency', value='Phase A->Phase B')
    i2 = Instruction(id='I2', start=11, end=21, text='Phase B', normalized='Phase B', kind='temporal',
                     key='dependency', value='Phase B->Phase C')
    i3 = Instruction(id='I3', start=22, end=32, text='Phase C', normalized='Phase C', kind='temporal',
                     key='dependency', value='Phase C->Phase A')

    graph = ConstraintGraph()
    graph.add_node(i1)
    graph.add_node(i2)
    graph.add_node(i3)
    graph.add_edge('I1', 'I2', 'dependent')
    graph.add_edge('I2', 'I3', 'dependent')
    graph.add_edge('I3', 'I1', 'dependent')

    cycles = graph.detect_cycles()
    assert len(cycles) >= 1
    # Check that cycle loops back to start
    assert cycles[0][0] == cycles[0][-1]

def test_graph_minimal_conflicting_sets():
    """Verify that minimal conflicting sets are isolated."""
    i1 = Instruction(id='I1', start=0, end=10, text='words: 100', normalized='100 words', kind='numerical')
    i2 = Instruction(id='I2', start=11, end=20, text='words: 50', normalized='50 words', kind='numerical')
    i3 = Instruction(id='I3', start=21, end=35, text='formal tone', normalized='formal', kind='semantic')

    c1 = Conflict(instruction_ids=['I1', 'I2'], kind='numerical', explanation='Bounds conflict', severity='hard')

    graph = ConstraintGraph.build([i1, i2, i3], [c1])
    min_sets = graph.find_minimal_conflicting_sets()
    assert len(min_sets) == 1
    assert set(min_sets[0]) == {'I1', 'I2'}
