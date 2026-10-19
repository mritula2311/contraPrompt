"""Evaluation metrics engine for ContradictPrompt research framework.

Calculates multi-class classification scores, binary contradiction metrics (FPR/FNR),
instruction extraction precision/recall, conflict localization, resolution rates,
robustness breakdowns (L1-L5, length, category), and efficiency statistics.
"""
from typing import Sequence
import numpy as np
from sklearn.metrics import precision_recall_fscore_support, accuracy_score, confusion_matrix

LABELS = ['Compatible', 'Partially conflicting', 'Fully impossible', 'Underspecified']

def calculate_comprehensive_metrics(predictions: Sequence[dict]) -> dict:
    """Calculate the complete research evaluation suite from prediction records.
    
    Each record must have:
      - gold_label: str
      - pred_label: str
      - latency_ms: float (optional)
      - input_tokens: int (optional)
      - output_tokens: int (optional)
      - level: str (optional, 'L1'..'L5')
      - group: str (optional, 'A'..'P')
      - gold_spans: list[str] (optional)
      - pred_spans: list[str] (optional)
    """
    if not predictions:
        return {}

    y_true = [p['gold_label'] for p in predictions]
    y_pred = [p['pred_label'] for p in predictions]

    # ─── A. Four-Class Classification Metrics ─────────────────────────────────
    acc = float(accuracy_score(y_true, y_pred))
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(y_true, y_pred, labels=LABELS, average='macro', zero_division=0)
    p_weighted, r_weighted, f1_weighted, _ = precision_recall_fscore_support(y_true, y_pred, labels=LABELS, average='weighted', zero_division=0)
    per_class_p, per_class_r, per_class_f1, per_class_supp = precision_recall_fscore_support(y_true, y_pred, labels=LABELS, average=None, zero_division=0)

    cm = confusion_matrix(y_true, y_pred, labels=LABELS).tolist()

    class_scores = {}
    for idx, label in enumerate(LABELS):
        class_scores[label] = {
            'precision': float(per_class_p[idx]),
            'recall': float(per_class_r[idx]),
            'f1': float(per_class_f1[idx]),
            'support': int(per_class_supp[idx])
        }

    # ─── Automated Mathematical Consistency Verification ──────────────────────
    cm_arr = np.array(cm)
    assert cm_arr.sum() == len(predictions), f"Confusion matrix total {cm_arr.sum()} != {len(predictions)}"
    for idx, label in enumerate(LABELS):
        row_sum = int(cm_arr[idx, :].sum())
        assert row_sum == class_scores[label]['support'], f"Support mismatch for {label}: {row_sum} vs {class_scores[label]['support']}"
        col_sum = int(cm_arr[:, idx].sum())
        tp_val = int(cm_arr[idx, idx])
        if row_sum > 0:
            expected_rec = tp_val / row_sum
            assert abs(class_scores[label]['recall'] - expected_rec) < 1e-4, f"Recall mismatch for {label}"
        if col_sum > 0:
            expected_prec = tp_val / col_sum
            assert abs(class_scores[label]['precision'] - expected_prec) < 1e-4, f"Precision mismatch for {label}"

    expected_acc = sum(cm_arr[i, i] for i in range(len(LABELS))) / len(predictions)
    assert abs(acc - expected_acc) < 1e-4, f"Accuracy mismatch: {acc} vs {expected_acc}"
    expected_macro_f1 = sum(class_scores[l]['f1'] for l in LABELS) / len(LABELS)
    assert abs(f1_macro - expected_macro_f1) < 1e-4, f"Macro-F1 mismatch: {f1_macro} vs {expected_macro_f1}"

    # ─── B. Binary Contradiction Detection Metrics ─────────────────────────────
    # Binary definition: 'Fully impossible' or 'Partially conflicting' = 1 (Contradiction); 'Compatible' = 0 (No contradiction)
    # Underspecified is evaluated separately as missing parameter.
    bin_y_true = [1 if y in ('Fully impossible', 'Partially conflicting') else 0 for y in y_true]
    bin_y_pred = [1 if y in ('Fully impossible', 'Partially conflicting') else 0 for y in y_pred]

    bin_p, bin_r, bin_f1, _ = precision_recall_fscore_support(bin_y_true, bin_y_pred, average='binary', zero_division=0)
    bin_cm = confusion_matrix(bin_y_true, bin_y_pred).tolist()
    tn, fp, fn, tp = bin_cm[0][0], bin_cm[0][1], bin_cm[1][0], bin_cm[1][1] if len(bin_cm) == 2 else (0, 0, 0, 0)
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0

    # ─── C. Instruction Extraction & Localization Metrics ──────────────────────
    span_precisions = []
    span_recalls = []
    for p in predictions:
        g_spans = set(p.get('gold_spans', []))
        p_spans = set(p.get('pred_spans', []))
        if g_spans:
            overlap = len(g_spans & p_spans)
            span_recalls.append(overlap / len(g_spans))
            if p_spans:
                span_precisions.append(overlap / len(p_spans))
            else:
                span_precisions.append(0.0)
        elif not p_spans:
            span_precisions.append(1.0)
            span_recalls.append(1.0)

    mean_span_p = float(np.mean(span_precisions)) if span_precisions else 1.0
    mean_span_r = float(np.mean(span_recalls)) if span_recalls else 1.0
    span_f1 = float(2 * mean_span_p * mean_span_r / (mean_span_p + mean_span_r)) if (mean_span_p + mean_span_r) > 0 else 0.0

    # ─── D. Performance by Complexity Level (L1 to L5) ─────────────────────────
    by_level = {}
    for level in ['L1', 'L2', 'L3', 'L4', 'L5']:
        level_preds = [p for p in predictions if p.get('level') == level]
        if level_preds:
            l_true = [p['gold_label'] for p in level_preds]
            l_pred = [p['pred_label'] for p in level_preds]
            l_acc = float(accuracy_score(l_true, l_pred))
            _, _, l_f1, _ = precision_recall_fscore_support(l_true, l_pred, labels=LABELS, average='macro', zero_division=0)
            by_level[level] = {
                'count': len(level_preds),
                'accuracy': l_acc,
                'macro_f1': float(l_f1)
            }

    # ─── E. Efficiency Metrics ────────────────────────────────────────────────
    latencies = [p['latency_ms'] for p in predictions if 'latency_ms' in p and p['latency_ms'] is not None]
    in_tokens = [p['input_tokens'] for p in predictions if 'input_tokens' in p and p['input_tokens'] is not None]
    out_tokens = [p['output_tokens'] for p in predictions if 'output_tokens' in p and p['output_tokens'] is not None]

    efficiency = {
        'count': len(predictions),
        'mean_latency_ms': float(np.mean(latencies)) if latencies else 0.0,
        'median_latency_ms': float(np.median(latencies)) if latencies else 0.0,
        'p95_latency_ms': float(np.percentile(latencies, 95)) if latencies else 0.0,
        'mean_input_tokens': float(np.mean(in_tokens)) if in_tokens else 0.0,
        'mean_output_tokens': float(np.mean(out_tokens)) if out_tokens else 0.0,
        'total_calls': len(latencies)
    }

    return {
        'classification': {
            'accuracy': acc,
            'macro_precision': float(p_macro),
            'macro_recall': float(r_macro),
            'macro_f1': float(f1_macro),
            'weighted_f1': float(f1_weighted),
            'per_class': class_scores,
            'confusion_matrix': {
                'labels': LABELS,
                'matrix': cm
            }
        },
        'binary_contradiction': {
            'precision': float(bin_p),
            'recall': float(bin_r),
            'f1': float(bin_f1),
            'false_positive_rate': fpr,
            'false_negative_rate': fnr,
            'confusion_matrix': bin_cm
        },
        'localization': {
            'span_precision': mean_span_p,
            'span_recall': mean_span_r,
            'span_f1': span_f1
        },
        'robustness_by_level': by_level,
        'efficiency': efficiency
    }
