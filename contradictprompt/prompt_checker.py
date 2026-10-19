"""Project PE-11: Production Prompt Consistency Checker
======================================================
Loads NVIDIA NIM / fine-tuned checkpoints to perform structured pre-generation
contradiction detection and intent-preserving prompt repair.
"""

import json
import time
from typing import Literal
from pydantic import BaseModel, Field

from .nvidia_nim_client import NvidiaNIMClient
from .rules import detect, HARD_SEMANTIC_PAIRS
from .extraction import extract


class PromptConsistencyResult(BaseModel):
    original_prompt: str
    conflict_label: Literal["compatible", "partially_conflicting", "fully_impossible", "underspecified"]
    conflict_category: Literal["Numerical", "Logical", "Temporal", "Formatting", "Semantic", "None"]
    explanation: str
    repaired_prompt: str
    is_safe_to_execute: bool = False
    latency_ms: float = 0.0


CHECKER_SYSTEM_PROMPT = """You are Project PE-11's Prompt Consistency Firewall.
Analyze the user prompt for internal contradictions, impossible constraints, and structural paradoxes across 5 dimensions:
1. Numerical: boundary collisions, exact counts vs bounds, array length paradoxes.
2. Logical: mutually exclusive assertions, boolean inversions, input-output negations.
3. Temporal: chronological inversions, prerequisite cycles, sequential dependency traps.
4. Formatting: clashing structured specs (e.g. JSON-only + prose outside JSON).
5. Semantic: clashing personas, contradictory stylistic constraints, opposing physical/domain perspectives.

Respond with a strictly formatted JSON object adhering to this schema:
{
  "conflict_label": "compatible" | "partially_conflicting" | "fully_impossible" | "underspecified",
  "conflict_category": "Numerical" | "Logical" | "Temporal" | "Formatting" | "Semantic" | "None",
  "explanation": "Chain-of-thought breakdown detailing the exact contradiction mechanism",
  "repaired_prompt": "Logically sound rewrite maximizing user intent (identical to original if compatible)"
}"""


class PromptChecker:
    """Pre-generation firewall checking prompts before execution."""

    def __init__(self, client: NvidiaNIMClient | None = None):
        self.client = client or NvidiaNIMClient()

    def check(self, prompt: str, force_llm: bool = False) -> PromptConsistencyResult:
        """Analyze prompt consistency via NVIDIA NIM with deterministic rule-based verification."""
        start_time = time.perf_counter()
        clean_prompt = prompt.strip()

        if not clean_prompt:
            return PromptConsistencyResult(
                original_prompt=prompt,
                conflict_label="underspecified",
                conflict_category="Logical",
                explanation="The supplied prompt is empty or contains only whitespace.",
                repaired_prompt="",
                is_safe_to_execute=False,
                latency_ms=0.1
            )

        # 1. Deterministic Rule Guardrail Check
        ins = extract(clean_prompt)
        rule_conflicts = detect(ins)
        has_hard_conflict = any(c.severity == "hard" for c in rule_conflicts)
        has_soft_conflict = bool(rule_conflicts)

        # Fast-path: If deterministic rule proves impossibility, return immediately (<1ms)
        if has_hard_conflict and not force_llm:
            c = rule_conflicts[0]
            elapsed = (time.perf_counter() - start_time) * 1000
            cat_name = c.kind.capitalize() if c.kind in {"numerical", "formatting", "temporal", "semantic"} else "Logical"
            return PromptConsistencyResult(
                original_prompt=clean_prompt,
                conflict_label="fully_impossible",
                conflict_category=cat_name,
                explanation=f"Deterministic Rule Precedence: {c.explanation}",
                repaired_prompt=f"Please resolve contradictory instructions: {c.explanation}",
                is_safe_to_execute=False,
                latency_ms=round(elapsed, 2)
            )

        # 2. Invoke NVIDIA NIM for Semantic & Deep Paradox Analysis
        messages = [
            {"role": "system", "content": CHECKER_SYSTEM_PROMPT},
            {"role": "user", "content": clean_prompt}
        ]

        try:
            resp = self.client.chat_completion(messages, json_mode=True)
            raw = resp.content.strip()

            # Clean markdown JSON wraps
            if raw.startswith("```"):
                raw = raw.strip("`")
                if raw.startswith("json"):
                    raw = raw[4:].strip()

            s_idx = raw.find("{")
            e_idx = raw.rfind("}")
            if s_idx != -1 and e_idx != -1 and e_idx > s_idx:
                raw = raw[s_idx:e_idx+1]

            data = json.loads(raw)

            label = data.get("conflict_label", "compatible").lower()
            category = data.get("conflict_category", "None")
            explanation = data.get("explanation", "No conflict identified.")
            repaired = data.get("repaired_prompt", clean_prompt)

            # Enforce deterministic rule precedence
            if has_hard_conflict:
                label = "fully_impossible"
                if category == "None":
                    category = rule_conflicts[0].kind.capitalize()
                explanation = f"Deterministic Rule Conflict: {rule_conflicts[0].explanation} (NIM CoT: {explanation})"

            # Heavy regularizer against false positives: if no rule conflicts exist
            # and no missing tags exist, preserve compatible classification
            if not has_hard_conflict and not has_soft_conflict and not any(i.kind == 'missing' for i in ins):
                if label in ("partially_conflicting", "underspecified"):
                    if "missing" not in explanation.lower() and "contradiction" not in explanation.lower() and "cannot" not in explanation.lower():
                        label = "compatible"
                        category = "None"

            # Standardize labels
            valid_labels = {"compatible", "partially_conflicting", "fully_impossible", "underspecified"}
            if label not in valid_labels:
                label = "fully_impossible" if has_hard_conflict else "compatible"

            valid_cats = {"Numerical", "Logical", "Temporal", "Formatting", "Semantic", "None"}
            if category not in valid_cats:
                category = "None" if label == "compatible" else "Semantic"

            elapsed = (time.perf_counter() - start_time) * 1000

            return PromptConsistencyResult(
                original_prompt=clean_prompt,
                conflict_label=label,
                conflict_category=category,
                explanation=explanation,
                repaired_prompt=repaired,
                is_safe_to_execute=(label == "compatible"),
                latency_ms=round(elapsed, 2)
            )

        except Exception as exc:
            # Resilient fallback to deterministic rule engine if API is interrupted
            elapsed = (time.perf_counter() - start_time) * 1000
            if has_hard_conflict:
                c = rule_conflicts[0]
                return PromptConsistencyResult(
                    original_prompt=clean_prompt,
                    conflict_label="fully_impossible",
                    conflict_category=c.kind.capitalize() if c.kind in {"numerical", "formatting", "temporal", "semantic"} else "Logical",
                    explanation=f"Deterministic Rule Precedence: {c.explanation}",
                    repaired_prompt=f"Please resolve conflicting instructions: {c.explanation}",
                    is_safe_to_execute=False,
                    latency_ms=round(elapsed, 2)
                )
            elif has_soft_conflict:
                c = rule_conflicts[0]
                return PromptConsistencyResult(
                    original_prompt=clean_prompt,
                    conflict_label="partially_conflicting",
                    conflict_category=c.kind.capitalize() if c.kind in {"numerical", "formatting", "temporal", "semantic"} else "Semantic",
                    explanation=f"Style Tension: {c.explanation}",
                    repaired_prompt=clean_prompt,
                    is_safe_to_execute=False,
                    latency_ms=round(elapsed, 2)
                )
            else:
                return PromptConsistencyResult(
                    original_prompt=clean_prompt,
                    conflict_label="compatible",
                    conflict_category="None",
                    explanation="No recognized contradiction found in prompt rules.",
                    repaired_prompt=clean_prompt,
                    is_safe_to_execute=True,
                    latency_ms=round(elapsed, 2)
                )
