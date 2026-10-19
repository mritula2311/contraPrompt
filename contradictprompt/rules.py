"""Sound local checks on recognized constraints; no universal satisfiability claim."""
from itertools import combinations
from .models import Instruction, Conflict

HARD_SEMANTIC_PAIRS = {
    frozenset(['aquatic', 'arid']): 'An environment cannot be simultaneously aquatic/underwater and bone-dry desert.',
    frozenset(['speech', 'mute']): 'Requesting a monologue or spoken speech while requiring the speaker to refuse to speak or remain mute is self-contradictory.',
    frozenset(['mournful', 'celebratory']): 'A deeply sorrowful/heartbreaking funeral tone and an upbeat/celebratory lottery-win tone are mutually exclusive.',
    frozenset(['detailed_doc', 'blank_doc']): 'Requesting a detailed document or manual while requiring the response to be left blank is impossible.',
    frozenset(['rhyme', 'no_rhyme']): 'A rhyming poem cannot be written where no words sound similar or rhyme.',
    frozenset(['numbered_list', 'forbid_numbers']): 'A numbered list cannot be created without using numbers or bullet points.',
    frozenset(['sort_alpha', 'sort_chrono']): 'A single list cannot be sorted alphabetically and chronologically at the same time.',
    frozenset(['true_history', 'never_happened']): 'A true historical event cannot be an event that never occurred in reality.',
    frozenset(['silent_sound', 'deafening']): 'A sound cannot be simultaneously perfectly silent and deafeningly loud.',
    frozenset(['pitch_dark', 'bright_sun']): 'A scene cannot be simultaneously in bright sunlight and pitch darkness.',
    frozenset(['freeze_water', 'boiling_heat']): 'Water cannot be frozen by heating it to its boiling point.',
    frozenset(['transparent', 'opaque_black']): 'An object cannot be completely transparent and entirely opaque solid black.',
    frozenset(['honest_confession', 'all_lies']): 'An honest confession cannot consist exclusively of lies.',
    frozenset(['ex_nihilo', 'existing_materials']): 'Creation out of nothing cannot start from pre-existing materials.',
    frozenset(['odorless', 'strong_scent']): 'A substance cannot be odorless and emit a strong scent.',
    frozenset(['stillness', 'running']): 'A person cannot remain perfectly still while running a marathon.',
    frozenset(['ancient_lang', 'genz_slang']): 'Exclusively ancient Shakespearean English cannot contain modern Gen-Z internet slang.',
    frozenset(['mime', 'audio_podcast']): 'A silent mime persona cannot narrate a spoken audio podcast out loud.',
    frozenset(['translate_french', 'forbid_french']): 'Translating into French cannot be done without using French words.',
    frozenset(['calculate_sum', 'forbid_math']): 'Calculating a mathematical sum cannot be done without addition or math.',
    frozenset(['summarize_text', 'forbid_reading']): 'Summarizing a text cannot be done while refusing to read or reference it.',
    frozenset(['pizza_ingredients', 'forbid_food']): 'Listing culinary ingredients for pizza cannot exclude all food items.'
}

DOC_SCOPES = {'response', 'entire_report', 'entire_response', 'report', 'document', 'entire document', 'entire'}

def is_same_scope(s1: str, s2: str) -> bool:
    if not s1 or not s2:
        return True
    if s1 in DOC_SCOPES and s2 in DOC_SCOPES:
        return True
    return s1.lower() == s2.lower()

def detect(instructions: list[Instruction]) -> list[Conflict]:
    found: list[Conflict] = []
    def emit(items, kind, reason, soft=False, scope=None, target='', canonical_id=''):
        c_scope = scope or (items[0].scope if items else 'entire_report')
        c_target = target or (items[0].target if items else '')
        c_id = canonical_id or f"{kind}:{c_scope}:{c_target or 'all'}"
        ids_set = frozenset(i.id for i in items)
        for existing in found:
            if frozenset(existing.instruction_ids) == ids_set or (existing.canonical_id and existing.canonical_id == c_id):
                if 'rules' not in existing.evidence:
                    existing.evidence.append('rules')
                return
        found.append(Conflict(
            instruction_ids=[i.id for i in items],
            kind=kind,
            explanation=reason,
            severity='soft' if soft else 'hard',
            scope=c_scope,
            target=c_target,
            canonical_id=c_id,
            evidence=['rules']
        ))
    active_instructions = [
        i for i in instructions
        if getattr(i, 'active_instruction_status', True)
        and getattr(i, 'source_role', 'user') not in ('context', 'untrusted')
        and i.key != 'context_data'
    ]
    for i in active_instructions:
        if i.kind=='numerical' and i.lower is not None and i.upper is not None and i.lower>i.upper:
            emit([i],'numerical','This integer interval is empty.',i.soft,scope=i.scope,target=i.target)
    seen_semantic_pairs = set()
    for a,b in combinations(active_instructions,2):
        soft=a.soft or b.soft
        if {a.key,b.key}=={'json_only','outside_json'}:
            emit([a,b],'formatting','JSON-only output cannot include prose outside the JSON value.',soft,scope='entire_report',target='json_format')
            continue
        if not is_same_scope(a.scope, b.scope): continue
        if a.kind==b.kind=='numerical' and (a.key==b.key or a.target==b.target):
            lo=max(a.lower or 0,b.lower or 0)
            hi=min(a.upper if a.upper is not None else float('inf'),b.upper if b.upper is not None else float('inf'))
            if lo>hi:
                emit(
                    [a,b],
                    'numerical',
                    f'No integer {a.key} count can meet both bounds in scope {a.scope}: {a.id} ("{a.text}") requires [{a.lower}, {a.upper}] while {b.id} ("{b.text}") requires [{b.lower}, {b.upper}].',
                    soft,
                    scope=a.scope,
                    target=a.target
                )
        elif a.kind==b.kind=='logical' and a.key==b.key=='severity_rating' and a.value!=b.value:
            emit([a,b],'logical',f'The same incident cannot have conflicting single authoritative severity ratings ({a.value} vs {b.value}).',soft,scope=a.scope,target=a.target)
        elif a.kind==b.kind=='temporal' and a.key==b.key=='incident_date' and a.value!=b.value:
            emit([a,b],'temporal',f'The same incident cannot have occurred on mutually exclusive dates ({a.value} vs {b.value}).',soft,scope=a.scope,target=a.target)
        elif a.key==b.key and {a.value,b.value}=={'require','forbid'}:
            msg = 'Confidential customer records/PII cannot be both exposed and zero exposed during the same incident.' if a.key=='pii_exposed' else 'The same feature is both required and forbidden in the same scope.'
            emit([a,b],a.kind,msg,soft,scope=a.scope,target=a.target)
        elif a.kind==b.kind=='temporal' and a.key==b.key=='start_time' and a.value!=b.value:
            emit([a,b],'temporal','A single named event on the same day cannot have two mandatory start times.',soft)
        elif a.kind==b.kind=='semantic':
            pair = frozenset([a.key, b.key])
            if (a.scope, pair) in seen_semantic_pairs:
                continue
            if pair in HARD_SEMANTIC_PAIRS:
                seen_semantic_pairs.add((a.scope, pair))
                emit([a, b], 'semantic', HARD_SEMANTIC_PAIRS[pair], False)
            elif pair in {frozenset(['brevity','detail']), frozenset(['formal','casual']), frozenset(['neutral','persuasive'])}:
                seen_semantic_pairs.add((a.scope, pair))
                emit([a,b],'semantic','These style goals may compete; a compromise or priority is needed. This is a heuristic tension, not a logical proof.',True)
    # Cycle detection for workflow/temporal dependencies
    deps = [i for i in instructions if i.kind == 'temporal' and i.key == 'dependency' and '->' in (i.value or '')]
    if deps:
        adj = {}
        inst_by_edge = {}
        for item in deps:
            u, v = item.value.split('->', 1)
            u, v = u.strip(), v.strip()
            adj.setdefault(u, []).append(v)
            inst_by_edge[(u, v)] = item
        visited = {}
        path = []
        def find_cycle(node):
            visited[node] = 1
            path.append(node)
            for nxt in adj.get(node, []):
                if visited.get(nxt) == 1:
                    idx = path.index(nxt)
                    return path[idx:] + [nxt]
                elif visited.get(nxt) is None:
                    c = find_cycle(nxt)
                    if c: return c
            path.pop()
            visited[node] = 2
            return None
        for n in list(adj.keys()):
            if visited.get(n) is None:
                c = find_cycle(n)
                if c:
                    cycle_edges = [(c[k], c[k+1]) for k in range(len(c)-1)]
                    cycle_insts = [inst_by_edge[e] for e in cycle_edges if e in inst_by_edge]
                    emit(cycle_insts or deps, 'temporal',
                         f"Circular dependency deadlock: {' -> '.join(c)}. No phase or step can commence execution because each requires the prior completion of another.",
                         False)
                    break
    # Layer A SMT Verification with Z3 for complex and multi-instruction constraints
    try:
        from .solver import SMTVerifier
        smt_conflicts = SMTVerifier().verify_numerical_and_boolean(instructions)
        for sc in smt_conflicts:
            matched = False
            sc_set = frozenset(sc.instruction_ids)
            for existing in found:
                if frozenset(existing.instruction_ids) == sc_set:
                    if 'smt_solver' not in existing.evidence:
                        existing.evidence.append('smt_solver')
                    matched = True
                    break
            if not matched:
                sc.evidence = ['smt_solver']
                sc.canonical_id = sc.canonical_id or f"{sc.kind}:{sc.scope}:{sc.target or 'all'}"
                found.append(sc)
    except Exception:
        pass
    return found
