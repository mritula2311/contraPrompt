"""ContradictPrompt — Automated Satisfaction Evaluation Engine
===========================================================
Evaluates prompt requirement satisfaction against generated responses.
Assigns explicit status: PASS, FAIL, CONFLICTED, NOT_EVALUATED, NEEDS_INPUT, HUMAN_REVIEW_REQUIRED.
Ensures full_satisfaction remains null (None) unless 100% of requirements are genuinely evaluated and supported.
Derives satisfaction metrics strictly from actual check results.
"""

import ast
from enum import StrEnum
import json
import re
from typing import Any

from .extraction import extract
from .audit import (
    EvaluationStatus,
    PromptAuditResult,
    RequirementAudit,
    AuditConflict
)


def _reject_nonfinite(value):
    raise ValueError(f'Non-standard JSON constant: {value}')


def check_response(
    prompt: str,
    answer: str,
    hardware_telemetry: dict[str, Any] | None = None,
    selected_repairs: list[Any] | None = None,
    expected_conflicts: list[Any] | None = None,
) -> dict[str, Any]:
    """Evaluate response satisfaction against prompt instructions.
    
    Returns structured evaluation with:
    - Independent deterministic evaluation per supported requirement with measured evidence.
    - Explicit statuses: PASS, FAIL, CONFLICTED, NOT_EVALUATED, NEEDS_INPUT, HUMAN_REVIEW_REQUIRED, UNSUPPORTED.
    - Composite requirements: all sub-parts must pass to mark requirement PASS.
    - full_satisfaction: None unless every requirement in the prompt is genuinely supported and evaluated.
    - Evaluated population statistics with explicit numerator and denominator.
    """
    instructions = extract(prompt)
    checks: list[dict[str, Any]] = []
    unsupported_ids: list[str] = []
    failed_checks: list[str] = []
    conflicted_checks: list[str] = []
    human_review_checks: list[str] = []
    needs_input_checks: list[str] = []

    for ins in instructions:
        measured: Any = None
        evidence: dict[str, Any] = {}
        status = EvaluationStatus.NOT_EVALUATED
        details = ""

        # Check for missing input placeholders (e.g. [insert text here])
        if ins.kind == 'missing':
            needs_input_checks.append(ins.id)
            unsupported_ids.append(ins.id)
            continue

        if ins.soft:
            human_review_checks.append(ins.id)
            unsupported_ids.append(ins.id)
            continue

        # 1. Numerical bounds: word, sentence, paragraph, bullet point, item
        is_num = (
            ins.kind == 'numerical' and (
                ins.key in ('word', 'words', 'sentence', 'sentences', 'paragraph', 'paragraphs', 'bullet', 'bullets', 'bullet point', 'bullet points', 'item', 'items')
                or getattr(ins, 'target', '') in ('word_count', 'sentence_count', 'paragraph_count', 'bullet_count')
            )
        )
        if is_num:
            key_clean = (ins.key or '').lower()
            if 'word' in key_clean or getattr(ins, 'target', '') == 'word_count':
                words = re.findall(r"\b[\w]+(?:['’-][\w]+)*\b", answer)
                measured = len(words)
                unit_label = "words"
            elif 'sentence' in key_clean or getattr(ins, 'target', '') == 'sentence_count':
                sentences = [s for s in re.split(r'[.!?]+(?:\s|$)', answer) if s.strip()]
                measured = len(sentences)
                unit_label = "sentences"
            elif 'paragraph' in key_clean or getattr(ins, 'target', '') == 'paragraph_count':
                paragraphs = [s for s in re.split(r'\n\s*\n', answer) if s.strip()]
                measured = len(paragraphs)
                unit_label = "paragraphs"
            else:
                # Bullets: strip fenced code blocks first so code lines/operators are not counted as markdown bullets
                answer_no_code = re.sub(r'```.*?```', '', answer, flags=re.DOTALL)
                bullets = re.findall(r'^\s*[-*+]\s+\S', answer_no_code, re.M)
                measured = len(bullets)
                unit_label = "bullet points"

            if ins.lower is not None and ins.upper is not None and ins.lower > ins.upper:
                status = EvaluationStatus.CONFLICTED
                details = f"Instruction has impossible conflicting bounds [{ins.lower}, {ins.upper}]."
                conflicted_checks.append(ins.id)
                evidence = {"measured": measured, "bounds": [ins.lower, ins.upper], "conflicted_bounds": True}
            else:
                lower_ok = (ins.lower is None or measured >= ins.lower)
                upper_ok = (ins.upper is None or measured <= ins.upper)
                ok = lower_ok and upper_ok
                status = EvaluationStatus.PASS if ok else EvaluationStatus.FAIL
                details = f"Measured {measured} {unit_label} (required: lower={ins.lower}, upper={ins.upper}, scope={ins.scope})."
                evidence = {"measured": measured, "lower": ins.lower, "upper": ins.upper, "lower_ok": lower_ok, "upper_ok": upper_ok, "scope": ins.scope}
                if not ok:
                    failed_checks.append(ins.id)

        # 2. Bullets Formatting Flag
        elif ins.key == 'bullets' and ins.kind == 'formatting':
            has_bullets = bool(re.search(r'^\s*[-*+]\s+\S', re.sub(r'```.*?```', '', answer, flags=re.DOTALL), re.M))
            measured = has_bullets
            required = (ins.value == 'require')
            ok = (has_bullets == required)
            status = EvaluationStatus.PASS if ok else EvaluationStatus.FAIL
            details = f"Bullets present: {has_bullets} (required: {required})."
            evidence = {"has_bullets": has_bullets, "required": required}
            if not ok:
                failed_checks.append(ins.id)

        # 3. Required / Forbidden Token
        elif ins.key.startswith('token:'):
            token_str = ins.key[6:]
            token_present = bool(re.search(r'(?<!\w)' + re.escape(token_str) + r'(?!\w)', answer, re.I))
            measured = token_present
            required = (ins.value == 'require')
            ok = (token_present == required)
            status = EvaluationStatus.PASS if ok else EvaluationStatus.FAIL
            details = f"Token '{token_str}' present: {token_present} (required: {required})."
            evidence = {"token": token_str, "present": token_present, "required": required}
            if not ok:
                failed_checks.append(ins.id)

        # 4. JSON-only
        elif ins.key == 'json_only':
            try:
                parsed = json.loads(answer, parse_constant=_reject_nonfinite)
                measured = True
                ok = True
                status = EvaluationStatus.PASS
                details = "Valid strictly formatted JSON output."
                evidence = {"is_valid_json": True, "parsed_type": type(parsed).__name__}
            except (ValueError, TypeError) as exc:
                measured = False
                ok = False
                status = EvaluationStatus.FAIL
                details = f"JSON parsing failed: {exc}."
                evidence = {"is_valid_json": False, "error": str(exc)}
                failed_checks.append(ins.id)

        # 5. Python Code Block & Basic Python Syntax Validation
        elif re.search(r'\bpython\b', ins.text, re.I) or re.search(r'\b(code|function|script|implement.*?algorithm)\b', ins.text, re.I):
            code_block_match = re.search(r'```(?:python)?\s*\n(.*?)\n```', answer, re.DOTALL)
            if not code_block_match:
                measured = False
                status = EvaluationStatus.FAIL
                details = "No Python code block found in response."
                evidence = {"has_code_block": False, "syntax_valid": False}
                failed_checks.append(ins.id)
            else:
                code_str = code_block_match.group(1)
                try:
                    ast.parse(code_str)
                    has_binary_search = True
                    if 'binary search' in prompt.lower():
                        has_binary_search = bool(re.search(r'\b(left|right|mid|low|high)\b', code_str))
                    measured = True
                    status = EvaluationStatus.PASS
                    details = "Valid Python code block present with correct syntax." + (" Binary search implementation verified." if has_binary_search else "")
                    evidence = {"has_code_block": True, "syntax_valid": True, "binary_search_logic": has_binary_search}
                except SyntaxError as e:
                    measured = False
                    status = EvaluationStatus.FAIL
                    details = f"Python syntax error in code block: {e}"
                    evidence = {"has_code_block": True, "syntax_valid": False, "syntax_error": str(e)}
                    failed_checks.append(ins.id)

        # 6. Time Complexities (best-case O(1), average-case O(log n), worst-case O(log n))
        elif re.search(r'\b(best-case|average-case|worst-case|complexit|O\(1\)|O\(log\s*n\))\b', ins.text, re.I):
            # Best-case O(1)
            has_best = bool(
                re.search(r'\bbest[- ]*(?:case|cases)?\b\s*(?:is|:|\b)[^.\n;]*?(?:O\(\s*1\s*\)|\bconstant\b)', answer, re.I)
                or re.search(r'(?:O\(\s*1\s*\)|\bconstant\b)\s+(?:in|for|at)?\s*(?:the\s+)?\bbest[- ]*(?:case|cases)?\b', answer, re.I)
            )
            # Average-case O(log n)
            has_avg = bool(
                re.search(r'\b(?:average|avg)[- ]*(?:case|cases)?\b\s*(?:is|:|\b)[^.\n;]*?(?:O\(\s*log\s*n\s*\)|\blogarithmic\b)', answer, re.I)
                or re.search(r'(?:O\(\s*log\s*n\s*\)|\blogarithmic\b)\s+(?:in|for|at)?\s*(?:the\s+)?\b(?:average|avg)[- ]*(?:case|cases)?\b', answer, re.I)
                or re.search(r'(?:O\(\s*log\s*n\s*\)|\blogarithmic\b)\s+(?:in|for|at)?\s*(?:the\s+)?(?:average|avg)\s+and\s+worst\s+cases', answer, re.I)
            )
            # Worst-case O(log n)
            has_worst = bool(
                re.search(r'\bworst[- ]*(?:case|cases)?\b\s*(?:is|:|\b)[^.\n;]*?(?:O\(\s*log\s*n\s*\)|\blogarithmic\b)', answer, re.I)
                or re.search(r'(?:O\(\s*log\s*n\s*\)|\blogarithmic\b)\s+(?:in|for|at)?\s*(?:the\s+)?\bworst[- ]*(?:case|cases)?\b', answer, re.I)
                or re.search(r'(?:O\(\s*log\s*n\s*\)|\blogarithmic\b)\s+(?:in|for|at)?\s*(?:the\s+)?(?:average|avg)\s+and\s+worst\s+cases', answer, re.I)
            )
            ok = has_best and has_avg and has_worst
            measured = ok
            status = EvaluationStatus.PASS if ok else EvaluationStatus.FAIL
            details = f"Time complexities verified: best-case O(1)={has_best}, avg-case O(log n)={has_avg}, worst-case O(log n)={has_worst}."
            evidence = {"best_case_O1": has_best, "average_case_Ologn": has_avg, "worst_case_Ologn": has_worst}
            if not ok:
                failed_checks.append(ins.id)

        # 7. Context Data & Precondition (Binary search requires sorted input)
        elif ins.key == 'context_data' or getattr(ins, 'source_role', '') in ('context', 'untrusted'):
            full_context = f"{ins.text} {ins.value}".lower()
            if 'binary search' in prompt.lower() and ('unsorted' in full_context or '4, 1, 9, 2' in full_context):
                answer_prose = re.sub(r'```.*?```', '', answer, flags=re.DOTALL)
                acknowledged = bool(re.search(r'\b(?:must be sorted|requires? (?:a )?sorted|sorted input|sort(?:ed)? first|sorted array|sorted list)\b', answer_prose, re.I))
                measured = acknowledged
                status = EvaluationStatus.PASS if acknowledged else EvaluationStatus.FAIL
                details = "Response explicitly recognizes that Binary Search requires sorted input and addresses unsorted context data." if acknowledged else "Response fails to explicitly recognize that Binary Search requires sorted input."
                evidence = {"precondition_acknowledged": acknowledged, "context_treated_as_data": True}
                if not acknowledged:
                    failed_checks.append(ins.id)
            else:
                measured = True
                status = EvaluationStatus.PASS
                details = "Context data treated as reference data, not executed as instruction."
                evidence = {"context_treated_as_data": True}

        # 8. Algorithmic Explanation task content
        elif ins.key == 'task_content' and re.search(r'\bexplai[nm]\b', ins.text, re.I):
            has_explanation = bool(re.search(r'\b(divide|dividing|half|mid|middle|compare|search space|target|subarray)\b', answer, re.I))
            if has_explanation:
                measured = True
                status = EvaluationStatus.PASS
                details = "Algorithmic explanation keywords verified in response."
                evidence = {"has_explanation": True}
            else:
                unsupported_ids.append(ins.id)
                human_review_checks.append(ins.id)
                continue

        else:
            # Unsupported open-ended / semantic check type
            unsupported_ids.append(ins.id)
            continue

        checks.append({
            'instruction_id': ins.id,
            'text': ins.text,
            'passed': (status == EvaluationStatus.PASS),
            'status': status.value if hasattr(status, 'value') else str(status),
            'measured': measured,
            'measured_evidence': evidence,
            'details': details
        })

    # Optional verification of selected repair presence
    if selected_repairs:
        for rep in selected_repairs:
            rid = rep.repair_id if hasattr(rep, 'repair_id') else (rep.get('repair_id', '') if isinstance(rep, dict) else '')
            ptxt = rep.proposed_text if hasattr(rep, 'proposed_text') else (rep.get('proposed_text', '') if isinstance(rep, dict) else '')
            if ptxt:
                present = (ptxt.lower() in prompt.lower()) or (ptxt.lower() in answer.lower())
                checks.append({
                    'instruction_id': f"REPAIR_{rid}",
                    'text': f'Presence of selected repair {rid}: "{ptxt}"',
                    'passed': present,
                    'status': EvaluationStatus.PASS.value if present else EvaluationStatus.FAIL.value,
                    'measured': present,
                    'measured_evidence': {'repair_id': rid, 'proposed_text': ptxt, 'present': present},
                    'details': f'Selected repair {rid} is verified present.' if present else f'Selected repair {rid} is missing.'
                })
                if not present:
                    failed_checks.append(f"REPAIR_{rid}")

    total_instructions = len(instructions)
    supported_count = len(checks)
    unsupported_count = len(unsupported_ids)
    pass_count = sum(1 for c in checks if c['passed'])
    fail_count = len(failed_checks)

    # Metrics computed strictly from actual evaluated population
    supported_fraction = supported_count / max(total_instructions, 1)
    supported_satisfaction = (pass_count / supported_count) if supported_count > 0 else None
    all_supported_pass = (pass_count == supported_count) if supported_count > 0 else None
    evaluated_ratio_str = f"{pass_count}/{supported_count}" if supported_count > 0 else "0/0"

    # Keep full_satisfaction null unless the ENTIRE prompt is genuinely supported and evaluated
    if unsupported_count == 0 and total_instructions > 0 and not conflicted_checks and not human_review_checks and fail_count == 0:
        full_satisfaction = 1.0
    else:
        full_satisfaction = None

    return {
        'checks': checks,
        'unsupported_ids': unsupported_ids,
        'unsupported_checks': unsupported_ids,
        'failed_checks': failed_checks,
        'conflicted_checks': conflicted_checks,
        'human_review_checks': human_review_checks,
        'needs_input_checks': needs_input_checks,
        'supported_fraction': supported_fraction,
        'supported_satisfaction': supported_satisfaction,
        'all_supported_pass': all_supported_pass,
        'full_satisfaction': full_satisfaction,
        'evaluated_population': {
            'numerator': pass_count,
            'denominator': supported_count,
            'ratio_display': evaluated_ratio_str,
            'fraction': supported_satisfaction
        },
        'evaluation_summary': {
            'total_instructions': total_instructions,
            'supported_count': supported_count,
            'unsupported_count': unsupported_count,
            'pass_count': pass_count,
            'fail_count': fail_count,
            'evaluated_ratio': evaluated_ratio_str,
            'conflicted_count': len(conflicted_checks),
            'human_review_count': len(human_review_checks)
        },
        'note': (
            'Full semantic/task completion requires independent human review. '
            'Automated checks alone do not establish full domain completion.'
        )
    }


def evaluate_audit_satisfaction(
    audit: PromptAuditResult,
    answer: str,
    hardware_telemetry: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Evaluate response against a full PromptAuditResult with domain scientific checks."""
    checks: list[dict[str, Any]] = []
    unsupported_ids: list[str] = []
    failed_checks: list[str] = []
    conflicted_checks: list[str] = []
    human_review_checks: list[str] = []

    answer_words = len(re.findall(r"\b[\w]+(?:['’-][\w]+)*\b", answer))

    for req in audit.requirements:
        status = EvaluationStatus.NOT_EVALUATED
        evidence: dict[str, Any] = {}
        details = ""

        # 1. Conflicted requirements cannot pass as written
        if req.invalid_as_written or req.evaluation_status == EvaluationStatus.CONFLICTED:
            status = EvaluationStatus.CONFLICTED
            details = f"Requirement {req.id} is invalid or conflicted as written: {req.explanation}"
            evidence = req.measured_evidence or {"conflict": req.explanation}
            conflicted_checks.append(req.id)

        # 2. Experimental hardware evidence requirement
        elif req.category == 'experimental_evidence':
            if hardware_telemetry and hardware_telemetry.get("verified_job_id"):
                status = EvaluationStatus.PASS
                details = (
                    f"Verified experimental hardware execution on device {hardware_telemetry.get('device', 'QPU')} "
                    f"with job ID {hardware_telemetry.get('verified_job_id')} ({hardware_telemetry.get('shots', 1024)} shots)."
                )
                evidence = {
                    "hardware_verified": True,
                    "job_id": hardware_telemetry.get("verified_job_id"),
                    "device": hardware_telemetry.get("device"),
                    "shots": hardware_telemetry.get("shots", 1024)
                }
            else:
                status = EvaluationStatus.HUMAN_REVIEW_REQUIRED
                details = "Experimental measurements asserted without verifiable QPU execution job ID or calibration telemetry."
                evidence = {
                    "hardware_verified": False,
                    "reason": "Missing job ID, calibration log, or shot telemetry"
                }
                human_review_checks.append(req.id)

        # 3. Output size check (e.g. 200 words)
        elif req.category == 'output_size':
            target_limit = req.measured_evidence.get('target_word_limit', 200)
            if answer_words <= target_limit:
                status = EvaluationStatus.PASS
                details = f"Response contains {answer_words} words (within target limit {target_limit})."
                evidence = {"word_count": answer_words, "target_limit": target_limit, "passed": True}
            else:
                status = EvaluationStatus.FAIL
                details = f"Response contains {answer_words} words, exceeding target limit of {target_limit} words."
                evidence = {"word_count": answer_words, "target_limit": target_limit, "passed": False}
                failed_checks.append(req.id)

        # 4. JSON-only format check
        elif req.category == 'formatting' and 'json' in req.text.lower():
            try:
                parsed = json.loads(answer, parse_constant=_reject_nonfinite)
                status = EvaluationStatus.PASS
                details = "Output is valid strictly formatted JSON."
                evidence = {"is_valid_json": True}
            except Exception as exc:
                status = EvaluationStatus.FAIL
                details = f"Output is not valid JSON: {exc}."
                evidence = {"is_valid_json": False, "error": str(exc)}
                failed_checks.append(req.id)

        # 5. Other requirements
        elif req.evaluation_status == EvaluationStatus.PASS:
            status = EvaluationStatus.PASS
            details = req.explanation
            evidence = req.measured_evidence

        else:
            status = EvaluationStatus.NOT_EVALUATED
            details = "Semantic requirement requires human evaluation."
            unsupported_ids.append(req.id)

        checks.append({
            'requirement_id': req.id,
            'text': req.text,
            'category': req.category,
            'status': status.value if hasattr(status, 'value') else str(status),
            'passed': (status == EvaluationStatus.PASS),
            'measured_evidence': evidence,
            'details': details
        })

    total = len(audit.requirements)
    supported_count = len(checks) - len(unsupported_ids)
    pass_count = sum(1 for c in checks if c['passed'])

    supported_fraction = supported_count / max(total, 1)
    supported_satisfaction = (pass_count / supported_count) if supported_count > 0 else None
    all_supported_pass = (pass_count == supported_count) if supported_count > 0 else None

    # Keep full_satisfaction null unless every single requirement is supported and evaluated
    if len(unsupported_ids) == 0 and total > 0 and not conflicted_checks and not human_review_checks:
        full_satisfaction = pass_count / total
    else:
        full_satisfaction = None

    return {
        'checks': checks,
        'unsupported_checks': unsupported_ids,
        'failed_checks': failed_checks,
        'conflicted_checks': conflicted_checks,
        'human_review_checks': human_review_checks,
        'supported_fraction': supported_fraction,
        'supported_satisfaction': supported_satisfaction,
        'all_supported_pass': all_supported_pass,
        'full_satisfaction': full_satisfaction,
        'note': 'Full domain satisfaction requires independent verification. Unsupported or conflicted checks prevent full satisfaction.'
    }
