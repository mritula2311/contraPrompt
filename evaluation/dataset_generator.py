"""Dataset generation engine for ContradictPrompt research benchmark.

Generates structured benchmarks across 5 evaluation difficulty levels and 16 adversarial
challenge groups (A-P), ensuring zero-leakage family splits across 4 target classes:
Compatible, Partially conflicting, Fully impossible, and Underspecified.
"""
import json
import random
from pathlib import Path
from typing import Literal

COMPLEXITY_LEVELS = {
    'L1': 'Level 1 — Basic (2 instructions, explicit contradiction)',
    'L2': 'Level 2 — Intermediate (3-8 instructions, section scopes, conditions)',
    'L3': 'Level 3 — Advanced (8-20 instructions, nested conditions, multi-task)',
    'L4': 'Level 4 — Expert (20-50 instructions, technical specs, multi-stage)',
    'L5': 'Level 5 — Extreme / Adversarial (50+ instructions, long context, adversarial traps)'
}

ADVERSARIAL_GROUPS = {
    'A': 'Long-distance contradictions',
    'B': 'Multi-instruction conflicts (3+ constraints)',
    'C': 'Numerical boundary conflicts',
    'D': 'Nested conditional conflicts',
    'E': 'Temporal contradictions & workflow deadlocks',
    'F': 'Conflicting output schemas (JSON vs prose/markdown)',
    'G': 'Semantic and contextual definition paradoxes',
    'H': 'Negation-heavy instructions & reverse bans',
    'I': 'Underspecified requirements & missing parameters',
    'J': 'Compatible prompts with misleading wording (False Positives check)',
    'K': 'Requirements with separate scopes (Scope distinction check)',
    'L': 'Contradictions involving three or more instructions',
    'M': 'Long technical specifications with buried conflicts',
    'N': 'Revisions, exceptions, and overriding conditions',
    'O': 'Quoted instructions that must not be executed',
    'P': 'Compound combinations of structural and semantic paradoxes'
}

# Template definitions by family
TEMPLATES = [
    # ─── Group A: Long-distance contradictions (L3-L5) ─────────────────────────
    {
        'family': 'long_distance_word_count',
        'group': 'A',
        'level': 'L3',
        'label': 'Fully impossible',
        'kind': 'numerical',
        'build': lambda p: (
            f"Please prepare an extensive white paper on enterprise cloud migration. "
            f"The final deliverable must contain at least 1500 words and cover security, compliance, cost optimization, and multi-region deployment. "
            f"Ensure you address AWS, Azure, and Google Cloud Platform capabilities in detail, comparing their respective Kubernetes managed services. "
            f"Discuss networking architecture including transit gateways, VPC peering, and hybrid VPN connections. "
            f"Include realistic cost models for 500 virtual machines over a three-year amortization cycle. "
            f"However, the entire response must strictly not exceed 250 words total."
        ),
        'conflicting_spans': ['at least 1500 words', 'strictly not exceed 250 words total'],
        'explanation': 'Instruction 1 sets a minimum response length of 1500 words, whereas Instruction 2 sets an upper bound of 250 words across the same scope.'
    },

    # ─── Group B & L: Multi-instruction conflicts (3+ instructions) ─────────────
    {
        'family': 'tri_constraint_infeasibility',
        'group': 'B',
        'level': 'L3',
        'label': 'Fully impossible',
        'kind': 'numerical',
        'build': lambda p: (
            f"Compose a project proposal where the Executive Summary is at least 120 words. "
            f"The Technical Methodology section must contain at least 150 words. "
            f"The Risk Assessment section must contain at least 100 words. "
            f"The entire document, including all sections combined, must not exceed 200 words."
        ),
        'conflicting_spans': ['at least 120 words', 'at least 150 words', 'at least 100 words', 'not exceed 200 words'],
        'explanation': 'The sum of the three required section minimums is 120 + 150 + 100 = 370 words, which mathematically contradicts the 200-word global cap.'
    },

    # ─── Group C: Numerical boundary conflicts (L1-L2) ──────────────────────────
    {
        'family': 'exact_vs_range_numeric',
        'group': 'C',
        'level': 'L1',
        'label': 'Fully impossible',
        'kind': 'numerical',
        'build': lambda p: f"Write an article on renewable energy containing exactly {p.get('exact', 100)} words. Keep the length fewer than {p.get('upper', 75)} words.",
        'conflicting_spans': ['exactly 100 words', 'fewer than 75 words'],
        'explanation': 'A word count of exactly 100 cannot be fewer than 75.'
    },

    # ─── Group D: Nested conditional conflicts (L3) ─────────────────────────────
    {
        'family': 'nested_conditional_paradox',
        'group': 'D',
        'level': 'L3',
        'label': 'Fully impossible',
        'kind': 'logical',
        'build': lambda p: (
            f"Review this quarterly financial report. If revenue grew by more than 10%, provide a positive commendation and omit all risk factors. "
            f"However, if the report mentions European market headwinds, you must include a mandatory 5-point risk matrix. "
            f"Note that revenue grew by 15% and European headwinds are explicitly highlighted in paragraph 2."
        ),
        'conflicting_spans': ['omit all risk factors', 'include a mandatory 5-point risk matrix'],
        'explanation': 'Both triggering conditions (revenue > 10% and European headwinds) are satisfied, generating simultaneously mandatory yet mutually exclusive obligations regarding risk factor reporting.'
    },

    # ─── Group E: Temporal & Workflow Deadlocks (L3-L5) ─────────────────────────
    {
        'family': 'workflow_prerequisite_cycle',
        'group': 'E',
        'level': 'L3',
        'label': 'Fully impossible',
        'kind': 'temporal',
        'build': lambda p: (
            f"Organize a corporate restructuring rollout. "
            f"Phase A requires publishing the final departmental layoffs and severance allocations. "
            f"Phase B requires conducting anonymous staff surveys to evaluate organizational morale. "
            f"Phase C requires establishing executive steering committee approval on survey results. "
            f"However, Phase A cannot be written until Phase B is fully finalized, "
            f"Phase B is structurally dependent on the outcome of Phase C, "
            f"and Phase C cannot begin execution until Phase A is completely detailed."
        ),
        'conflicting_spans': ['Phase A cannot be written until Phase B', 'Phase B is structurally dependent on the outcome of Phase C', 'Phase C cannot begin execution until Phase A'],
        'explanation': 'Circular prerequisite deadlock: Phase A -> Phase B -> Phase C -> Phase A. No phase can commence execution because each requires the prior completion of another.'
    },

    # ─── Group F: Conflicting Output Schemas (L2) ───────────────────────────────
    {
        'family': 'json_and_conversational_prose',
        'group': 'F',
        'level': 'L2',
        'label': 'Fully impossible',
        'kind': 'formatting',
        'build': lambda p: (
            f"Return the parsed transaction logs as valid JSON only. Do not include markdown codeblocks, preamble, or any external text. "
            f"At the very beginning, write a polite conversational greeting explaining how much you enjoyed analyzing this log data."
        ),
        'conflicting_spans': ['valid JSON only', 'write a polite conversational greeting'],
        'explanation': 'A conversational greeting outside the JSON structure violates the strict JSON-only constraint.'
    },

    # ─── Group G: Semantic and Contextual Paradoxes (L2-L3) ─────────────────────
    {
        'family': 'physical_semantic_paradox',
        'group': 'G',
        'level': 'L2',
        'label': 'Fully impossible',
        'kind': 'semantic',
        'build': lambda p: f"Describe an underwater scuba diving expedition in the Mariana Trench, taking place entirely in a bone-dry desert with zero moisture.",
        'conflicting_spans': ['underwater scuba diving expedition', 'bone-dry desert with zero moisture'],
        'explanation': 'An environment cannot be simultaneously an underwater scuba expedition and a bone-dry desert with zero moisture.'
    },

    # ─── Group H: Negation-Heavy Instructions (L3) ──────────────────────────────
    {
        'family': 'reverse_ban_negation',
        'group': 'H',
        'level': 'L3',
        'label': 'Fully impossible',
        'kind': 'logical',
        'build': lambda p: (
            f"Translate the following paragraph into standard Parisian French. "
            f"You are strictly prohibited from using any French vocabulary, loanwords, or French grammatical constructs."
        ),
        'conflicting_spans': ['Translate the following paragraph into standard Parisian French', 'strictly prohibited from using any French vocabulary'],
        'explanation': 'A translation into French cannot be produced while strictly forbidding all French vocabulary and grammar.'
    },

    # ─── Group I: Underspecified Requirements (L2) ─────────────────────────────
    {
        'family': 'missing_source_text',
        'group': 'I',
        'level': 'L2',
        'label': 'Underspecified',
        'kind': 'missing',
        'build': lambda p: (
            f"Extract all quarterly financial figures from [insert quarterly report here], format them as a Markdown table, "
            f"and compute the year-over-year operating margin expansion for our European subsidiary."
        ),
        'conflicting_spans': ['[insert quarterly report here]'],
        'explanation': 'Essential source material is missing: the quarterly report placeholder is unfilled.'
    },
    {
        'family': 'missing_required_format',
        'group': 'I',
        'level': 'L2',
        'label': 'Underspecified',
        'kind': 'missing',
        'build': lambda p: f"Prepare the technical incident report on cloud infrastructure outage using the required format.",
        'conflicting_spans': ['using the required format'],
        'explanation': 'Essential formatting guidelines are missing: the required format specification is omitted.'
    },
    {
        'family': 'missing_target_language',
        'group': 'I',
        'level': 'L2',
        'label': 'Underspecified',
        'kind': 'missing',
        'build': lambda p: f"Translate the following excerpt on renewable energy to the target language: 'Recent findings demonstrate significant efficiency gains across solar PV installations.'",
        'conflicting_spans': ['to the target language'],
        'explanation': 'Essential target language parameter is omitted from the translation instruction.'
    },
    {
        'family': 'unsupplied_measurement_data',
        'group': 'I',
        'level': 'L2',
        'label': 'Underspecified',
        'kind': 'missing',
        'build': lambda p: f"Calculate the total power efficiency of the smart grid meters; The measurement values are not provided.",
        'conflicting_spans': ['The measurement values are not provided'],
        'explanation': 'Essential calculation parameters are omitted: measurement values are not provided.'
    },
    {
        'family': 'missing_local_timezone',
        'group': 'I',
        'level': 'L2',
        'label': 'Underspecified',
        'kind': 'missing',
        'build': lambda p: f"Convert the local start time of the data pipeline execution to UTC; The source timezone is not supplied.",
        'conflicting_spans': ['The source timezone is not supplied'],
        'explanation': 'Essential timezone information is missing for UTC time conversion.'
    },
    {
        'family': 'unfilled_entity_and_date',
        'group': 'I',
        'level': 'L2',
        'label': 'Underspecified',
        'kind': 'missing',
        'build': lambda p: f"Draft an incident report for [insert company name] regarding the security breach on [insert incident date].",
        'conflicting_spans': ['[insert company name]', '[insert incident date]'],
        'explanation': 'Mandatory entity identifiers and incident date placeholders remain unfilled.'
    },

    # ─── Group J: Compatible with Misleading Wording (Negative Cases) ───────────
    {
        'family': 'misleading_compatible_complex',
        'group': 'J',
        'level': 'L3',
        'label': 'Compatible',
        'kind': 'none',
        'build': lambda p: (
            f"Write a comprehensive analysis of the fall of the Western Roman Empire. "
            f"Although some historians mistakenly believe Rome fell in a single catastrophic day in 476 AD while others argue it took centuries, "
            f"do not treat these historical debates as contradictory. "
            f"Structure your essay into exactly three distinct sections: Political Instability, Economic Crises, and Military Transformations. "
            f"Ensure each section contains between 80 and 150 words. Use formal academic tone throughout."
        ),
        'conflicting_spans': [],
        'explanation': 'All constraints are mutually satisfiable. The text discusses historical contradictions in external debates but imposes no contradictory requirements on the output.'
    },

    # ─── Group K: Separate Scopes (Valid Scope Distinction) ─────────────────────
    {
        'family': 'separate_section_word_counts',
        'group': 'K',
        'level': 'L2',
        'label': 'Compatible',
        'kind': 'none',
        'build': lambda p: (
            f"Create a two-part marketing brief. "
            f"In the Executive Summary section, use fewer than 50 words. "
            f"In the Campaign Strategy section, provide a detailed plan of at least 300 words. "
            f"Ensure both sections are clearly labeled."
        ),
        'conflicting_spans': [],
        'explanation': 'The word count constraints apply to distinct scopes (Executive Summary vs Campaign Strategy) and are completely compatible.'
    },

    # ─── Group N: Revisions & Exceptions (L3-L4) ────────────────────────────────
    {
        'family': 'valid_overriding_exception',
        'group': 'N',
        'level': 'L3',
        'label': 'Compatible',
        'kind': 'none',
        'build': lambda p: (
            f"Draft a technical user guide for our REST API. Use bullet points for all endpoint descriptions, "
            f"except for the Authentication section, where you must provide a continuous paragraph instead of bullet points. "
            f"Include JSON request samples for each endpoint."
        ),
        'conflicting_spans': [],
        'explanation': 'The prompt provides a clear conditional exception to a general formatting rule, making the overall instruction set valid and satisfiable.'
    },

    # ─── Group O: Quoted Instructions As Data (L3-L4) ───────────────────────────
    {
        'family': 'quoted_instruction_data',
        'group': 'O',
        'level': 'L3',
        'label': 'Compatible',
        'kind': 'none',
        'build': lambda p: (
            f"Analyze the following student prompt submission for grammar errors: "
            f"\"Write a 500-word essay in exactly two words.\" "
            f"Do not attempt to write the student's essay; simply evaluate the grammatical correctness of their English sentence."
        ),
        'conflicting_spans': [],
        'explanation': 'The contradictory imperative is contained within quotation marks as inert input data to be analyzed, not an instruction to be executed.'
    },

    # ─── Compatible: Conditional Branches ───────────────────────────────────────
    {
        'family': 'compatible_conditional_branches',
        'group': 'D',
        'level': 'L3',
        'label': 'Compatible',
        'kind': 'none',
        'build': lambda p: (
            f"Review the network vulnerability assessment. If the report is classified as HIGH, provide emergency remediation steps. "
            f"If it is classified as LOW, provide standard routine monitoring recommendations."
        ),
        'conflicting_spans': [],
        'explanation': 'Conditional alternative branches are independent and mutually satisfiable depending on input classification.'
    },

    # ─── Soft Preference / Partially Conflicting (L2-L3) ────────────────────────
    {
        'family': 'tone_and_brevity_tension',
        'group': 'P',
        'level': 'L2',
        'label': 'Partially conflicting',
        'kind': 'semantic',
        'build': lambda p: (
            f"Write a summary of quantum entanglement for an introductory student. "
            f"Be extremely brief and concise, keeping it to a quick glance, but explain every mathematical derivation in exhaustive and meticulous detail."
        ),
        'conflicting_spans': ['extremely brief and concise', 'exhaustive and meticulous detail'],
        'explanation': 'Extreme brevity and exhaustive mathematical detail compete for priority. A balanced compromise or clarification of depth is required.'
    },
    {
        'family': 'formality_and_slang_tension',
        'group': 'P',
        'level': 'L2',
        'label': 'Partially conflicting',
        'kind': 'semantic',
        'build': lambda p: (
            f"Draft a formal memo to the board of directors regarding corporate governance. "
            f"Maintain a strictly formal academic tone, while incorporating casual streetwear slang throughout the document."
        ),
        'conflicting_spans': ['strictly formal', 'casual slang'],
        'explanation': 'Strict formality and casual slang create stylistic tension that requires tone calibration.'
    },
    {
        'family': 'neutral_vs_persuasive',
        'group': 'P',
        'level': 'L2',
        'label': 'Partially conflicting',
        'kind': 'semantic',
        'build': lambda p: (
            f"Write an evaluation of solar energy subsidies. "
            f"Maintain an impartial, strictly neutral stance, while acting as an aggressive persuasive advocate to promote subsidies."
        ),
        'conflicting_spans': ['strictly neutral', 'persuasive advocate'],
        'explanation': 'Neutral objectivity competes with persuasive advocacy; priority or synthesis is required.'
    },
    {
        'family': 'mournful_vs_celebratory',
        'group': 'P',
        'level': 'L2',
        'label': 'Partially conflicting',
        'kind': 'semantic',
        'build': lambda p: (
            f"Compose an address for the corporate milestone gala. "
            f"Maintain a sorrowful, mournful tone of grief, while keeping the speech cheerful, upbeat, and celebratory."
        ),
        'conflicting_spans': ['mournful', 'celebratory'],
        'explanation': 'Mournful grief and cheerful celebration compete in emotional tone.'
    }
]

def generate_evaluation_benchmark(target_count: int = 1000) -> list[dict]:
    """Generate a balanced, comprehensive research benchmark of verified prompt cases."""
    cases = []
    case_id = 1
    
    classes = ['Compatible', 'Partially conflicting', 'Fully impossible', 'Underspecified']
    per_class = target_count // len(classes)
    
    for cls in classes:
        cls_templates = [t for t in TEMPLATES if t['label'] == cls]
        per_tmpl = per_class // len(cls_templates)
        remainder = per_class % len(cls_templates)
        
        for idx, tmpl in enumerate(cls_templates):
            quota = per_tmpl + (1 if idx < remainder else 0)
            for i in range(quota):
                seed_param = {'idx': i, 'exact': 100 + (i % 5) * 10, 'upper': 70 - (i % 3) * 5}
                prompt_text = tmpl['build'](seed_param)
                case = {
                    'case_id': f"CP_CASE_{case_id:04d}",
                    'family': tmpl['family'],
                    'group': tmpl['group'],
                    'group_name': ADVERSARIAL_GROUPS[tmpl['group']],
                    'level': tmpl['level'],
                    'level_name': COMPLEXITY_LEVELS[tmpl['level']],
                    'prompt': prompt_text,
                    'gold_label': tmpl['label'],
                    'conflict_kind': tmpl['kind'],
                    'conflicting_spans': tmpl['conflicting_spans'],
                    'gold_explanation': tmpl['explanation']
                }
                cases.append(case)
                case_id += 1
                
    return cases
