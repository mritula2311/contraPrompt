"""Adversarial and Multi-Level Complexity Unit Tests (Section 4 & 13)."""
import pytest
from contradictprompt import analyze, Label

def test_level_1_basic():
    """Level 1: Explicit 2-instruction contradiction."""
    prompt = "Write exactly 100 words. Keep the length fewer than 80 words."
    res = analyze(prompt, mode='rules')
    assert res.label == Label.IMPOSSIBLE
    assert any(c.kind == 'numerical' for c in res.conflicts)

def test_level_2_intermediate():
    """Level 2: Separate scopes should be compatible."""
    prompt = (
        "Create a two-part marketing brief. "
        "In the Executive Summary section, use fewer than 50 words. "
        "In the Campaign Strategy section, provide a detailed plan of at least 300 words. "
        "Ensure both sections are clearly labeled."
    )
    res = analyze(prompt, mode='rules')
    # Should not confuse different section word counts
    assert res.label != Label.IMPOSSIBLE

def test_level_3_circular_dependency():
    """Level 3: Circular workflow dependency."""
    prompt = (
        "Phase A cannot be written until Phase B is fully finalized, "
        "Phase B is structurally dependent on the outcome of Phase C, "
        "and Phase C cannot begin execution until the tragic conclusion in Phase A is completely detailed."
    )
    res = analyze(prompt, mode='rules')
    assert res.label == Label.IMPOSSIBLE
    assert any('Circular dependency' in c.explanation for c in res.conflicts)

def test_level_4_quoted_instructions():
    """Level 4: Quoted instructions treated as inert data, not active constraints."""
    prompt = (
        "Analyze the following student prompt submission for grammar errors: "
        "\"Write a 500-word essay in exactly two words.\" "
        "Do not attempt to write the student's essay; simply evaluate the grammatical correctness of their sentence."
    )
    res = analyze(prompt, mode='rules')
    # The contradictory instructions inside the quote must not trigger an impossible label
    assert res.label != Label.IMPOSSIBLE

def test_level_5_complex_compatible():
    """Level 5: Highly complex prompt with multiple valid sections and guidelines."""
    prompt = (
        "Draft a comprehensive technical architecture proposal for an enterprise IoT platform. "
        "Include five core architectural pillars: Edge Data Acquisition, MQTT Ingestion Gateways, "
        "Time-Series Storage, ML Anomaly Inference, and Role-Based Dashboard Visualization. "
        "For each pillar, outline required protocols, security ciphers, and high-availability failover mechanisms. "
        "Use formal engineering terminology and clear Markdown headers for each pillar. "
        "Provide concrete data schemas for device telemetry packets in JSON format. "
        "Ensure all encryption complies with TLS 1.3 standards."
    )
    res = analyze(prompt, mode='rules')
    assert res.label == Label.COMPATIBLE


def test_evaluation_metrics_mathematical_consistency():
    """Verify that raw predictions and aggregated evaluation results agree mathematically."""
    import json
    import numpy as np
    from pathlib import Path
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
    from contradictprompt import Label

    root = Path(__file__).resolve().parent.parent
    raw_file = root / 'results' / 'raw_predictions.json'
    adv_file = root / 'results' / 'adversarial_evaluation_results.json'

    assert raw_file.exists(), "raw_predictions.json must exist as Single Source of Truth"
    assert adv_file.exists(), "adversarial_evaluation_results.json must exist"

    raw_preds = json.loads(raw_file.read_text(encoding='utf-8'))
    assert len(raw_preds) == 1000, f"Expected 1,000 cases, found {len(raw_preds)}"

    labels = ['Compatible', 'Partially conflicting', 'Fully impossible', 'Underspecified']
    y_true = [p['gold_label'] for p in raw_preds]
    y_pred = [p['pred_label'] for p in raw_preds]

    # Check balanced support
    for l in labels:
        assert y_true.count(l) == 250, f"Class {l} support is {y_true.count(l)}, expected 250"

    # Compute raw metrics
    acc = accuracy_score(y_true, y_pred)
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(y_true, y_pred, labels=labels, average='macro', zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    adv_data = json.loads(adv_file.read_text(encoding='utf-8'))
    adv_metrics = adv_data['overall_metrics']['classification']

    # Mathematical consistency assertions
    assert abs(adv_metrics['accuracy'] - acc) < 1e-4
    assert abs(adv_metrics['macro_f1'] - f1_macro) < 1e-4
    assert adv_metrics['confusion_matrix']['matrix'] == cm.tolist()

    # Confusion matrix mathematical assertions
    assert cm.sum() == 1000
    for idx, l in enumerate(labels):
        assert cm[idx, :].sum() == 250
        tp = cm[idx, idx]
        expected_rec = tp / 250.0
        assert abs(adv_metrics['per_class'][l]['recall'] - expected_rec) < 1e-4
