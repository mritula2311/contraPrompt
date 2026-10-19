import time
from typing import Literal
from .models import Assessment, Label, Usage
from .preprocessing import normalize
from .extraction import extract
from .rules import detect
from .llm import LLMClient, ProviderError

MAX_PROMPT_CHARS=30000

def analyze(prompt: str,mode: Literal['rules','llm','hybrid']='rules',client: LLMClient | None=None) -> Assessment:
    start=time.perf_counter()
    if mode not in ('rules','llm','hybrid'): raise ValueError('Unknown detector mode')
    if not isinstance(prompt,str) or not prompt.strip(): raise ValueError('Enter a non-empty prompt.')
    if len(prompt)>MAX_PROMPT_CHARS: raise ValueError(f'Prompt is limited to {MAX_PROMPT_CHARS} characters.')
    ins=extract(prompt) if mode!='llm' else []
    conflicts=detect(ins) if mode!='llm' else []
    questions=list(dict.fromkeys(i.value for i in ins if i.kind=='missing'))
    warnings=[]; usage=Usage(); checked=False
    hard=any(c.severity=='hard' for c in conflicts)
    soft=bool(conflicts)
    label=Label.IMPOSSIBLE if hard else Label.UNSPECIFIED if questions else Label.PARTIAL if soft else Label.COMPATIBLE
    explanation={Label.IMPOSSIBLE:'Recognized hard requirements cannot all hold in the same scope.',
        Label.UNSPECIFIED:'An essential source or parameter is missing.',
        Label.PARTIAL:'Preferences compete; choose a priority or approve a compromise.',
        Label.COMPATIBLE:'No conflict was found among recognized requirements.'}[label]
    if mode in ('llm','hybrid'):
        client=client or LLMClient()
        try:
            extra,usage=client.analyze(prompt); checked=True
            if mode=='llm':
                ins=extra.instructions; conflicts=extra.conflicts; label=extra.label
                questions=extra.clarification_questions; explanation=extra.explanation
            else:
                mapping={i.id:'L'+i.id for i in extra.instructions}
                ins += [i.model_copy(update={'id':mapping[i.id]}) for i in extra.instructions]
                conflicts += [c.model_copy(update={'instruction_ids':[mapping[x] for x in c.instruction_ids]}) for c in extra.conflicts]
                questions=list(dict.fromkeys(questions+extra.clarification_questions))
                if hard:
                    if extra.label!=Label.IMPOSSIBLE: warnings.append('LLM disagreed with a verified rule. The deterministic hard conflict takes precedence.')
                elif extra.label==Label.IMPOSSIBLE or (not questions and extra.label==Label.PARTIAL) or (label==Label.COMPATIBLE):
                    label=extra.label; explanation=extra.explanation
                if not hard and label!=Label.IMPOSSIBLE and questions: label=Label.UNSPECIFIED
        except ProviderError as exc:
            if mode=='llm': raise
            warnings.append(str(exc)+' Hybrid fell back to rules; this is not a completed hybrid experiment.')
    if not checked:
        warnings.append('Offline checks cover a limited English grammar. Compatible means no recognized conflict, not proof that arbitrary instructions are satisfiable.')
    if any(i.kind=='other' for i in ins):
        warnings.append('Some free-text or unsupported constraints need semantic or human review.')

    # Layer C: Cross-Instruction Conflict Graph and Minimal Conflicting Sets
    from .constraint_graph import ConstraintGraph
    from .models import ConstraintGraphData
    graph = ConstraintGraph.build(ins, conflicts)
    min_sets = graph.find_minimal_conflicting_sets()
    if not min_sets and conflicts:
        min_sets = [c.instruction_ids for c in conflicts]
    graph_data = ConstraintGraphData.model_validate(graph.to_dict())

    # Secondary multi-label flags preservation
    secondary = []
    if label == Label.IMPOSSIBLE:
        if questions: secondary.append('underspecified')
        if any(c.severity == 'soft' for c in conflicts): secondary.append('partially_conflicting')
    elif label == Label.UNSPECIFIED:
        if conflicts: secondary.append('partially_conflicting' if not hard else 'fully_impossible')
    elif label == Label.PARTIAL:
        if questions: secondary.append('underspecified')

    return Assessment(original=prompt,normalized=normalize(prompt).text,label=label,instructions=ins,
        conflicts=conflicts,clarification_questions=questions,explanation=explanation,warnings=warnings,
        mode=mode,usage=usage,latency_ms=(time.perf_counter()-start)*1000,semantic_checked=checked,
        secondary_flags=secondary,minimal_conflicting_sets=min_sets,constraint_graph=graph_data)
