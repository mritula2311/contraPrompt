"""Failure Analysis and Failure Registry Engine (Section 16).

Analyzes misclassified evaluation cases, diagnoses failure mechanisms, groups them into
canonical root cause taxonomies, and maintains `results/failure_registry.json`.
"""
import json
from pathlib import Path
from typing import Sequence

FAILURE_CATEGORIES = [
    'Missed numerical contradiction',
    'Missed scope distinction',
    'Incorrect negation interpretation',
    'Temporal reasoning failure',
    'Semantic ambiguity',
    'Instruction extraction failure',
    'Conditional dependency failure',
    'Long-context information loss',
    'Incorrect conflict localization',
    'False positive on compatible instructions',
    'Unsupported or hallucinated explanation',
    'Invalid structured output'
]

def analyze_failures(predictions: Sequence[dict], output_path: Path | None = None) -> list[dict]:
    """Diagnose misclassified cases and export structured failure registry."""
    failure_registry = []

    for item in predictions:
        gold = item.get('gold_label')
        pred = item.get('pred_label')

        if gold != pred:
            # Diagnose root cause based on conflict kind and ground truth
            kind = item.get('conflict_kind', 'other')
            level = item.get('level', 'L2')

            if gold == 'Compatible' and pred in ('Fully impossible', 'Partially conflicting'):
                root_cause = 'False positive on compatible instructions'
                corrective_action = 'Improve scope separation and recognize conditional exceptions before asserting conflicts.'
            elif kind == 'numerical':
                root_cause = 'Missed numerical contradiction'
                corrective_action = 'Verify interval arithmetic and SMT bounds across all global and local targets.'
            elif kind == 'temporal':
                root_cause = 'Temporal reasoning failure'
                corrective_action = 'Enhance prerequisite dependency graph parser and cycle detection.'
            elif kind == 'missing':
                root_cause = 'Instruction extraction failure'
                corrective_action = 'Add detection patterns for unfulfilled bracketed placeholders and omitted arguments.'
            elif kind == 'semantic':
                root_cause = 'Semantic ambiguity'
                corrective_action = 'Expand pairwise semantic paradox definitions and employ hybrid LLM verification.'
            elif level in ('L4', 'L5'):
                root_cause = 'Long-context information loss'
                corrective_action = 'Implement hierarchical chunking and global constraint synthesis.'
            else:
                root_cause = 'Conditional dependency failure'
                corrective_action = 'Parse antecedent conditional triggers and exceptions prior to conflict scoring.'

            failure_entry = {
                'case_id': item.get('case_id', 'UNKNOWN'),
                'prompt': item.get('prompt', ''),
                'gold_label': gold,
                'pred_label': pred,
                'conflict_kind': kind,
                'level': level,
                'root_cause': root_cause,
                'failed_component': 'rules' if item.get('mode') == 'rules' else 'hybrid',
                'corrective_action': corrective_action
            }
            failure_registry.append(failure_entry)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_failures': len(failure_registry),
                'failures_by_category': {
                    cat: sum(1 for f in failure_registry if f['root_cause'] == cat)
                    for cat in FAILURE_CATEGORIES
                },
                'registry': failure_registry
            }, f, indent=2)

    return failure_registry
