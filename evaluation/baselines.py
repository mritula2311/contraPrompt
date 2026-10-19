"""Research Baselines and Model Comparison Runner (Section 12).

Implements the 6 primary detector configurations (A through F) and the 4
workflow-level conditions (Direct answering, Generic clarification,
Detection, Detection & repair) evaluated across identical held-out benchmarks.
"""
import time
from typing import Sequence, Literal
from contradictprompt import analyze, Label
from contradictprompt.models import Assessment, Usage
from contradictprompt.repair import suggestions, approve_and_revalidate

class BaselineA_RuleBased:
    """Baseline A: Pure deterministic rule-based contradiction detection (Layer A)."""
    name = "Baseline A: Rule-Based Engine"

    def predict(self, prompt: str) -> dict:
        t0 = time.perf_counter()
        res = analyze(prompt, mode='rules')
        latency = (time.perf_counter() - t0) * 1000
        return {
            'pred_label': res.label.value,
            'conflicts': [c.model_dump(mode='json') for c in res.conflicts],
            'pred_spans': [i.text for i in res.instructions if any(i.id in c.instruction_ids for c in res.conflicts)],
            'latency_ms': latency,
            'input_tokens': 0,
            'output_tokens': 0,
            'mode': 'rules'
        }

class BaselineB_BaseLLMDirect:
    """Baseline B: Base NVIDIA LLM without specialized contradiction detection prompting."""
    name = "Baseline B: Base LLM Direct"

    def __init__(self, client=None):
        self.client = client

    def predict(self, prompt: str) -> dict:
        if not self.client:
            raise RuntimeError("LLMClient not configured. Remote LLM direct baseline requires active client.")
        t0 = time.perf_counter()
        raw_answer, usage = self.client.chat(
            system="Answer or execute the following instructions directly:",
            prompt=prompt,
            structured=False
        )
        return {
            'pred_label': 'Compatible',  # Base models without detection prompt attempt to follow instructions
            'conflicts': [],
            'pred_spans': [],
            'latency_ms': usage.latency_ms,
            'input_tokens': usage.input_tokens,
            'output_tokens': usage.output_tokens,
            'mode': 'base_llm_direct',
            'raw_response': raw_answer
        }

class BaselineC_StructuredLLM:
    """Baseline C: Base LLM with schema-constrained contradiction detection prompting."""
    name = "Baseline C: Structured Base LLM"

    def __init__(self, client=None):
        self.client = client

    def predict(self, prompt: str) -> dict:
        if not self.client:
            raise RuntimeError("LLMClient not configured. Structured LLM baseline requires active client.")
        t0 = time.perf_counter()
        res = analyze(prompt, mode='llm', client=self.client)
        latency = (time.perf_counter() - t0) * 1000
        return {
            'pred_label': res.label.value,
            'conflicts': [c.model_dump(mode='json') for c in res.conflicts],
            'pred_spans': [i.text for i in res.instructions if any(i.id in c.instruction_ids for c in res.conflicts)],
            'latency_ms': latency,
            'input_tokens': res.usage.input_tokens or 0,
            'output_tokens': res.usage.output_tokens or 0,
            'mode': 'llm_structured'
        }

class BaselineD_Hybrid:
    """Baseline D: Hybrid Rule-Based + Base LLM Detection."""
    name = "Baseline D: Hybrid Rules + LLM"

    def __init__(self, client=None):
        self.client = client

    def predict(self, prompt: str) -> dict:
        if not self.client:
            raise RuntimeError("LLMClient not configured. Hybrid baseline requires active client.")
        t0 = time.perf_counter()
        res = analyze(prompt, mode='hybrid', client=self.client)
        latency = (time.perf_counter() - t0) * 1000
        return {
            'pred_label': res.label.value,
            'conflicts': [c.model_dump(mode='json') for c in res.conflicts],
            'pred_spans': [i.text for i in res.instructions if any(i.id in c.instruction_ids for c in res.conflicts)],
            'latency_ms': latency,
            'input_tokens': res.usage.input_tokens or 0,
            'output_tokens': res.usage.output_tokens or 0,
            'mode': 'hybrid'
        }

class BaselineE_FineTunedLoRA:
    """Baseline E: Fine-Tuned LLM (NeMo LoRA adapter configuration)."""
    name = "Baseline E: Fine-Tuned NeMo LoRA"
    executed = False

    def predict(self, prompt: str) -> dict:
        raise NotImplementedError(
            "Fine-tuned LoRA model weights (.bin/.safetensors) not found in checkpoints/pe11_lora/. "
            "Baseline is NOT EXECUTED."
        )

class BaselineF_HybridFineTuned:
    """Baseline F: Hybrid Rule-Based + Fine-Tuned LLM."""
    name = "Baseline F: Hybrid Rules + Fine-Tuned LoRA"
    executed = False

    def predict(self, prompt: str) -> dict:
        raise NotImplementedError(
            "Fine-tuned checkpoint weights not found in checkpoints/pe11_lora/. "
            "Baseline is NOT EXECUTED."
        )

# ─── Four Workflow Conditions (Section 1) ────────────────────────────────────

def run_workflow_comparison(prompt: str, detector=None) -> dict:
    """Evaluate a prompt under the four PE-11 workflow conditions."""
    detector = detector or BaselineA_RuleBased()

    # Condition 1: Direct Answering (no checks)
    c1 = {
        'condition': '1. Direct answering',
        'action': 'Generate text immediately without static contradiction check',
        'safeguard': False,
        'status': 'Potential hallucination or silent failure on impossible prompts'
    }

    # Condition 2: Generic Clarification
    c2 = {
        'condition': '2. Generic clarification',
        'action': 'Ask generic clarification question ("Can you please specify your requirements in more detail?")',
        'safeguard': True,
        'status': 'Excessive friction on already-compatible prompts'
    }

    # Condition 3: Contradiction Detection
    analysis = detector.predict(prompt)
    c3 = {
        'condition': '3. Contradiction detection',
        'classification': analysis['pred_label'],
        'conflicts_count': len(analysis['conflicts']),
        'safeguard': True,
        'status': 'Halt before generation if impossible/underspecified'
    }

    # Condition 4: Detection Followed by Repair
    res_obj = analyze(prompt, mode='rules')
    repairs = suggestions(res_obj)
    repaired_label = None
    if repairs:
        revalidated = approve_and_revalidate(repairs[0].prompt, approved=True, mode='rules')
        repaired_label = revalidated.label.value

    c4 = {
        'condition': '4. Detection and repair',
        'classification': analysis['pred_label'],
        'repairs_available': len(repairs),
        'repaired_label': repaired_label,
        'safeguard': True,
        'status': 'Autonomous patch suggestion with user approval and revalidation'
    }

    return {
        'direct_answering': c1,
        'generic_clarification': c2,
        'detection': c3,
        'detection_and_repair': c4
    }
