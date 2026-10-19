"""Project PE-11: Production Pre-Generation Firewall Router
==========================================================
Executes dynamic routing based on prompt contradiction analysis:
- compatible             -> Pass directly to primary generation NIM model.
- partially_conflicting  -> Swap in repaired_prompt, flag notification header, execute generation.
- fully_impossible       -> Short-circuit execution and return detailed diagnostic report.
- underspecified         -> Short-circuit execution and request required context.
"""

from typing import Literal
from pydantic import BaseModel, Field

from .nvidia_nim_client import NvidiaNIMClient
from .prompt_checker import PromptChecker, PromptConsistencyResult


class RoutingOutcome(BaseModel):
    action: Literal["execute_original", "execute_repaired", "short_circuit"]
    status: Literal["passed", "repaired_and_executed", "blocked"]
    executed_prompt: str | None = None
    notification_header: str | None = None
    generation_response: str | None = None
    diagnostic_report: dict | None = None
    consistency_result: PromptConsistencyResult


class PromptFirewallRouter:
    """Pre-generation firewall router protecting downstream LLM tasks."""

    def __init__(
        self,
        checker: PromptChecker | None = None,
        generator_client: NvidiaNIMClient | None = None
    ):
        self.checker = checker or PromptChecker()
        self.generator_client = generator_client or NvidiaNIMClient()

    def process_and_route(self, prompt: str) -> RoutingOutcome:
        """Analyze prompt and route according to PE-11 policy."""
        check_result = self.checker.check(prompt)
        label = check_result.conflict_label

        # ─── PATH 1: COMPATIBLE ──────────────────────────────────────────────────
        if label == "compatible":
            # Pass directly to primary generation NIM model
            gen_resp = self.generator_client.chat_completion([
                {"role": "user", "content": prompt}
            ])
            return RoutingOutcome(
                action="execute_original",
                status="passed",
                executed_prompt=prompt,
                notification_header=None,
                generation_response=gen_resp.content,
                diagnostic_report=None,
                consistency_result=check_result
            )

        # ─── PATH 2: PARTIALLY CONFLICTING ──────────────────────────────────────
        elif label == "partially_conflicting":
            # Swap in repaired_prompt, attach notification header, execute generation
            repaired = check_result.repaired_prompt or prompt
            header = (
                f"[FIREWALL NOTIFICATION] Soft conflict detected ({check_result.conflict_category}). "
                f"Resolved with optimized prompt: '{repaired}'."
            )
            gen_resp = self.generator_client.chat_completion([
                {"role": "user", "content": repaired}
            ])
            return RoutingOutcome(
                action="execute_repaired",
                status="repaired_and_executed",
                executed_prompt=repaired,
                notification_header=header,
                generation_response=gen_resp.content,
                diagnostic_report=None,
                consistency_result=check_result
            )

        # ─── PATH 3: FULLY IMPOSSIBLE / UNDERSPECIFIED ──────────────────────────
        else:
            # Short-circuit execution and return detailed diagnostic report
            diagnostic = {
                "blocked": True,
                "reason": "Hard contradiction or missing context prevented safe execution.",
                "conflict_label": check_result.conflict_label,
                "conflict_category": check_result.conflict_category,
                "explanation": check_result.explanation,
                "suggested_repair": check_result.repaired_prompt,
                "action_required": "Please review the diagnostic explanation and approve a corrected prompt before executing."
            }
            return RoutingOutcome(
                action="short_circuit",
                status="blocked",
                executed_prompt=None,
                notification_header=f"[FIREWALL BLOCKED] {check_result.conflict_label.upper()}: {check_result.explanation}",
                generation_response=None,
                diagnostic_report=diagnostic,
                consistency_result=check_result
            )
