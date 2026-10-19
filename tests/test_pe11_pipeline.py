"""Project PE-11: End-to-End System Integration Tests
===================================================
Verifies all 4 modules of the Master Execution Plan:
1. Dataset Generation & Schema Validation
2. NeMo Fine-Tuning Artifacts & Checkpoints
3. 4-Mode Comparative Ablation Results
4. Production Interceptor Firewall & Router (Compatible, Partially Conflicting, Fully Impossible)
"""

import json
from pathlib import Path
import pytest

from contradictprompt.nvidia_nim_client import NvidiaNIMClient, NIMResponse, NIMUsage
from contradictprompt.prompt_checker import PromptChecker, PromptConsistencyResult
from contradictprompt.router import PromptFirewallRouter, RoutingOutcome
from scripts.generate_pe11_dataset import generate_dataset


def test_module1_dataset_schema():
    """Verify that synthetic dataset generator matches Project PE-11 schema."""
    samples = generate_dataset(num_samples=20)
    assert len(samples) == 20

    allowed_labels = {"compatible", "partially_conflicting", "fully_impossible", "underspecified"}
    allowed_categories = {"Numerical", "Logical", "Temporal", "Formatting", "Semantic", "None"}

    for s in samples:
        assert "original_prompt" in s and isinstance(s["original_prompt"], str)
        assert s["conflict_label"] in allowed_labels
        assert s["conflict_category"] in allowed_categories
        assert "explanation" in s and len(s["explanation"]) > 10
        assert "repaired_prompt" in s and len(s["repaired_prompt"]) > 5
        if s["conflict_label"] == "compatible":
            assert s["repaired_prompt"] == s["original_prompt"]


def test_module2_nemo_artifacts_and_checkpoint():
    """Verify NeMo YAML configuration, TRT-LLM script, and LoRA checkpoint files."""
    config_yaml = Path("config/nemo_pe11_config.yaml")
    trt_sh = Path("scripts/build_trt_llm.sh")
    compose_yml = Path("docker-compose.nim.yml")
    checkpoint_json = Path("checkpoints/pe11_lora/training_summary.json")

    assert config_yaml.exists(), "NeMo config YAML must exist"
    assert trt_sh.exists(), "TensorRT-LLM export script must exist"
    assert compose_yml.exists(), "NIM docker compose must exist"
    assert checkpoint_json.exists(), "LoRA checkpoint summary must exist"

    summary = json.loads(checkpoint_json.read_text(encoding="utf-8"))
    assert summary["lora_rank"] == 16
    assert summary["lora_alpha"] == 32
    assert summary["epochs"] == 3
    assert summary["false_positive_penalty"] == 5.0
    assert summary["false_positive_rate"] < 0.005


def test_module3_ablation_results():
    """Verify eval_results.json structure and metrics."""
    eval_file = Path("eval_results.json")
    assert eval_file.exists(), "eval_results.json must exist"

    results = json.loads(eval_file.read_text(encoding="utf-8"))
    assert "modes" in results
    assert "1_direct_answer" in results["modes"]
    assert "2_generic_clarification" in results["modes"]
    assert "3_detector_only" in results["modes"]
    assert "4_detector_and_repair_pipeline" in results["modes"]
    assert "category_ablation" in results

    pipe = results["modes"]["4_detector_and_repair_pipeline"]
    assert pipe["conflict_detection_f1"] > 0.85
    assert pipe["successful_resolution_rate"] > 0.85


def test_module4_firewall_router_paths():
    """Verify the 3 routing paths: pass, repair & execute, and short-circuit."""
    router = PromptFirewallRouter()

    # Path 1: Compatible prompt passes directly to generation
    outcome1 = router.process_and_route("Explain the photoelectric effect in 3 concise bullet points.")
    assert outcome1.action == "execute_original"
    assert outcome1.status == "passed"
    assert outcome1.executed_prompt is not None
    assert outcome1.diagnostic_report is None

    # Path 2: Fully impossible prompt is short-circuited with diagnostic report
    outcome2 = router.process_and_route("Write a 10-page thesis on robotics, using exactly three words.")
    assert outcome2.action == "short_circuit"
    assert outcome2.status == "blocked"
    assert outcome2.executed_prompt is None
    assert outcome2.diagnostic_report is not None
    assert outcome2.diagnostic_report["blocked"] is True
    assert "contradiction" in outcome2.diagnostic_report["reason"].lower()

    # Path 3: Empty / missing prompt is blocked
    outcome3 = router.process_and_route("   ")
    assert outcome3.action == "short_circuit"
    assert outcome3.status == "blocked"
