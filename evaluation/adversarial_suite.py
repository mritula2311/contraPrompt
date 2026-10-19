"""Adversarial and Challenge Evaluation Suite (Section 13).

Evaluates the detector across 16 specialized adversarial challenge groups (A through P)
and 5 complexity levels (L1 through L5) to measure robustness against edge cases.
"""
from typing import Sequence
from contradictprompt import analyze
from .dataset_generator import generate_evaluation_benchmark, ADVERSARIAL_GROUPS, COMPLEXITY_LEVELS
from .metrics import calculate_comprehensive_metrics

class AdversarialChallengeSuite:
    """Independent challenge suite evaluating edge cases and adversarial attacks."""

    def __init__(self, cases: list[dict] | None = None):
        self.cases = cases or generate_evaluation_benchmark(target_count=320)

    def run_suite(self, mode: str = 'rules', client=None) -> dict:
        """Execute the entire adversarial challenge benchmark and aggregate group statistics."""
        predictions = []

        for case in self.cases:
            prompt = case['prompt']
            gold_label = case['gold_label']

            res = analyze(prompt, mode=mode, client=client)
            pred_spans = [i.text for i in res.instructions if any(i.id in c.instruction_ids for c in res.conflicts)]

            predictions.append({
                'case_id': case['case_id'],
                'prompt': prompt,
                'group': case['group'],
                'level': case['level'],
                'conflict_kind': case.get('conflict_kind', 'other'),
                'gold_label': gold_label,
                'pred_label': res.label.value,
                'latency_ms': res.latency_ms,
                'input_tokens': res.usage.input_tokens if mode != 'rules' else 0,
                'output_tokens': res.usage.output_tokens if mode != 'rules' else 0,
                'gold_spans': case.get('conflicting_spans', []),
                'pred_spans': pred_spans,
                'conflicts_found': len(res.conflicts)
            })

        overall_metrics = calculate_comprehensive_metrics(predictions)

        # Compute per-group adversarial breakdown
        group_results = {}
        for grp_key, grp_name in ADVERSARIAL_GROUPS.items():
            grp_preds = [p for p in predictions if p['group'] == grp_key]
            if grp_preds:
                correct = sum(1 for p in grp_preds if p['gold_label'] == p['pred_label'])
                group_results[grp_key] = {
                    'group_name': grp_name,
                    'total_cases': len(grp_preds),
                    'correct': correct,
                    'accuracy': round(correct / len(grp_preds), 4),
                    'mean_latency_ms': round(sum(p['latency_ms'] for p in grp_preds) / len(grp_preds), 2)
                }

        return {
            'overall': overall_metrics,
            'groups': group_results,
            'predictions': predictions
        }
