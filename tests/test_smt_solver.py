"""Unit tests for Z3 SMT formal constraint verification (Layer A)."""
import pytest
from contradictprompt.models import Instruction
from contradictprompt.solver import SMTVerifier

def test_smt_numerical_unsat():
    """Verify that contradictory numerical bounds are detected as unsat with correct instruction IDs."""
    verifier = SMTVerifier()
    i1 = Instruction(id='I1', start=0, end=17, text='exact 100 words', normalized='exact 100',
                     kind='numerical', key='word_count', lower=100, upper=100, scope='response')
    i2 = Instruction(id='I2', start=18, end=35, text='fewer than 80 words', normalized='<80',
                     kind='numerical', key='word_count', lower=None, upper=79, scope='response')
    
    conflicts = verifier.verify_numerical_and_boolean([i1, i2])
    assert len(conflicts) == 1
    assert set(conflicts[0].instruction_ids) == {'I1', 'I2'}
    assert conflicts[0].severity == 'hard'
    assert 'SMT Unsatisfiable' in conflicts[0].explanation

def test_smt_scope_isolation():
    """Verify that conflicting numbers across different scopes are NOT considered contradictory."""
    verifier = SMTVerifier()
    i1 = Instruction(id='I1', start=0, end=25, text='Executive Summary: 50 words', normalized='50 words',
                     kind='numerical', key='word_count', lower=50, upper=50, scope='summary')
    i2 = Instruction(id='I2', start=26, end=50, text='Detailed Plan: 500 words', normalized='500 words',
                     kind='numerical', key='word_count', lower=500, upper=500, scope='body')
    
    conflicts = verifier.verify_numerical_and_boolean([i1, i2])
    assert len(conflicts) == 0

def test_smt_boolean_formatting():
    """Verify contradictory boolean formatting flags in the same scope."""
    verifier = SMTVerifier()
    i1 = Instruction(id='I1', start=0, end=15, text='use bullet points', normalized='bullets: true',
                     kind='formatting', key='bullets', value='require', scope='response')
    i2 = Instruction(id='I2', start=16, end=35, text='do not use bullets', normalized='bullets: false',
                     kind='formatting', key='bullets', value='forbidden', scope='response')
    
    conflicts = verifier.verify_numerical_and_boolean([i1, i2])
    assert len(conflicts) == 1
    assert set(conflicts[0].instruction_ids) == {'I1', 'I2'}
