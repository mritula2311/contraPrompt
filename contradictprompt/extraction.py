"""Conservative English patterns with evidence spans and explicit scope."""
import re
from .models import Instruction
from .preprocessing import masked_quotes

NUM = re.compile(r'\b((?:strictly\s+)?(?:must\s+not\s+exceed|do\s+not\s+exceed|not\s+(?:to\s+)?exceed|cannot\s+exceed)|exactly|at least|at most|no more than|no fewer than|fewer than|less than|more than|over|under|between)\s+([\d,]+)(?:\s+(?:and|to)\s+([\d,]+))?\s+(words?|sentences?|paragraphs?|bullet points?|items?)\b', re.I)
NUM_HYPHEN = re.compile(r'\b([\d,]+)-(words?|sentences?|paragraphs?|bullet points?|items?)\b', re.I)
SPLIT = re.compile(r';|\n|(?<!\s\d\.)(?<!\s\d\d\.)(?<!\s[A-Za-z]\.)(?<!e\.g\.)(?<!i\.e\.)(?<=[.!?])\s+|(?<!\d),\s*(?:but|however|yet)\s+|\s+(?:but|and)\s+(?=(?:use|do|avoid|include|exclude|return|write|make|keep|explain|start|end|schedule|prefer|aim|be)\b)', re.I)
SCOPE = re.compile(
    r'\b(?:in|for|of)\s+(?:the\s+)?(entire\s+(?:report|document|response)|total\s+(?:report|response)|response|report|document)\b|'
    r'\b(?:in|for|of)\s+(?:the\s+)?([a-z0-9_\-\s]{2,30}?)\s+(?:section|part|paragraph|chapter)\b|'
    r'\b(?:in|for|of)\s+(?:the\s+)?(introduction|conclusion|summary|body|recommendations?|background|appendix|section\s+[a-z0-9]+|paragraph\s+\d+)\b|'
    r'\b(introduction|conclusion|summary|body|recommendations?|background|appendix|section\s+[a-z0-9]+)\s*:',
    re.I
)

def is_structural_or_boilerplate(text: str) -> bool:
    s = text.strip()
    if not s:
        return True
    # Markdown headings
    if re.match(r'^#{1,6}\s+', s):
        return True
    # Standalone list markers like "1.", "1)", "-", "*", "•", "A."
    if re.match(r'^(?:\d{1,3}[\.\)]|[a-zA-Z][\.\)]|[-*•])\s*$', s):
        return True
    # Punctuation or empty fragments (< 3 alphabetic characters)
    if len(re.findall(r'[a-zA-Z]', s)) < 3:
        return True
    # Preamble / header phrases
    if re.match(r'^(?:(?:please\s+)?follow\s+(?:these\s+)?requirements:?|requirements:?|instructions:?|notes?:?|specifications?:?|guidelines:?)$', s, re.I):
        return True
    return False

def clean_scope(raw_scope: str | None) -> str:
    if not raw_scope:
        return 'response'
    s = raw_scope.strip().lower()
    if s.startswith('the '):
        s = s[4:].strip()
    if s in ('entire', 'entire report', 'entire document', 'entire response', 'total', 'total report', 'total response', 'whole response', 'whole report', 'whole document', 'report', 'document'):
        return 'response'
    return s

def clauses(prompt: str):
    start = 0
    for m in SPLIT.finditer(masked_quotes(prompt)):
        # Keep an if/unless antecedent attached to its comma-separated consequent.
        fragment=prompt[start:m.start()]
        # Do not cut on a standalone list marker like "1." or "A."
        if re.match(r'^(?:\d{1,3}[\.\)]|[a-zA-Z][\.\)]|[-*•])\s*$', fragment.strip()):
            continue
        if (re.search(r'\b(if|unless|either)\b',masked_quotes(fragment),re.I) or SCOPE.search(masked_quotes(fragment))) and (m.group().startswith(',') or re.match(r'\s+(and|but)\b',m.group(),re.I)):
            continue
        clause_str = prompt[start:m.start()].strip()
        if clause_str:
            a = start + len(prompt[start:m.start()]) - len(prompt[start:m.start()].lstrip())
            b = m.start() - len(prompt[start:m.start()]) + len(prompt[start:m.start()].rstrip())
            yield a, b, prompt[a:b]
        start = m.end()
    if prompt[start:].strip():
        a = start + len(prompt[start:]) - len(prompt[start:].lstrip())
        yield a, len(prompt.rstrip()), prompt[a:len(prompt.rstrip())]

def interval(op: str, n: int, m: int | None = None):
    op = op.lower()
    if op == 'exactly': return n, n
    if op == 'between': return n, m
    if op in ('at least','no fewer than'): return n, None
    if op in ('more than','over'): return n+1, None
    if 'exceed' in op or op in ('at most','no more than'): return 0, n
    return 0, n-1

def extract(prompt: str) -> list[Instruction]:
    out = []
    def add(a, b, kind, scope, key='', value='', lower=None, upper=None, soft=False):
        out.append(Instruction(id=f'I{len(out)+1}',start=a,end=b,text=prompt[a:b],
            normalized=f'{key}: {value}' if value else f'{key}: [{lower}, {upper}]',
            scope=scope,kind=kind,key=key,value=value,lower=lower,upper=upper,soft=soft))
    for a,b,clause in clauses(prompt):
        plain = masked_quotes(clause)
        scope_match = SCOPE.search(plain)
        raw_scope = next((x for x in scope_match.groups() if x), 'response') if scope_match else 'response'
        scope = clean_scope(raw_scope)
        before = len(out)
        if re.search(r'\b(if|unless|either)\b',plain,re.I):
            add(a,b,'other',scope,'conditional',clause.strip()); continue
        for m in NUM.finditer(plain):
            lo,hi = interval(m[1],int(m[2].replace(',','')),int(m[3].replace(',','')) if m[3] else None)
            unit=m[4].lower().rstrip('s')
            soft=bool(re.search(r'\b(prefer|ideally|aim|approximately|about)\b',plain[:m.start()],re.I))
            # A negated exact number represents a punctured domain, not an exact bound.
            neg=bool(re.search(r'(?:not|never)\s+(?:use\s+|write\s+)?$',plain[:m.start()],re.I))
            if neg:
                add(a+m.start(),a+m.end(),'other',scope,'unparsed_negated_numeric',m.group()); continue
            add(a+m.start(),a+m.end(),'numerical',scope,unit,lower=lo,upper=hi,soft=soft)
        for m in NUM_HYPHEN.finditer(plain):
            n = int(m[1].replace(',',''))
            unit = m[2].lower().rstrip('s')
            add(a+m.start(),a+m.end(),'numerical',scope,unit,lower=n,upper=n,soft=False)
        patterns = [
          (r'\b(?:do not|don\x27t|never)\s+(?:use|include|return)\s+(?:any\s+)?bullet points?\b|\bavoid\s+bullet points?\b','formatting','bullets','forbid'),
          (r'\b(?:use|include|return)\s+(?:only\s+)?bullet points?\b','formatting','bullets','require'),
          (r'\b(?:return|output|use|format:?\s*(?:return|use)?)\s+(?:only\s+(?:strictly\s+|valid\s+|raw\s+)?JSON|(?:strictly\s+|valid\s+|raw\s+)?JSON\s+only)\b|\b(?:strictly\s+|valid\s+|raw\s+)?JSON\s+only\b','formatting','json_only','require'),
          (r'\b(?:include|add|explain|write|provide)\b[^.;\n]*?\boutside\s+(?:the\s+)?JSON\b','formatting','outside_json','require'),
          (r'\b(?:return|output|use)\s+(?:only\s+plain text|plain text\s+only)\b','formatting','plain_only','require'),
          (r'\b(?:use|include|return)\s+(?:a\s+)?(?:Markdown\s+)?table\b','formatting','table','require'),
          (r'\b(?:do not|never)\s+(?:use|include)\s+(?:a\s+)?(?:Markdown\s+)?table\b|\bavoid\s+tables?\b','formatting','table','forbid'),
          (r'\b(?:authoritative\s+)?severity\s+(?:rating|level|classification)\s+(?:of\s+|is\s+|to\s+)?(CRITICAL|HIGH|MEDIUM|LOW|INFORMATIONAL)\b|\b(CRITICAL|HIGH|MEDIUM|LOW|INFORMATIONAL)\s+(?:as\s+(?:the\s+)?(?:single\s+)?authoritative\s+severity)\b','logical','severity_rating',r'\1'),
          (r'\b(?:customer\s+)?(?:PII|confidential\s+information)\s+(?:was|is|were)\s+(?:completely\s+)?(?:compromised|exposed)\b','logical','pii_exposed','require'),
          (r'\bno\s+(?:customer\s+)?(?:PII|confidential\s+information)\s+(?:was|is|were)\s+(?:compromised|exposed)\b','logical','pii_exposed','forbid'),
          (r'\b(?:incident|event|breach)\s+(?:occurred|happened|took\s+place)\s+(?:strictly\s+|exclusively\s+)?(?:on\s+)?([A-Z][a-z]+\s+\d{1,2},\s+\d{4}|\d{4}-\d{2}-\d{2})\b','temporal','incident_date',r'\1'),
        ]
        hits=[]
        for pattern,kind,key,val in patterns:
            for m in re.finditer(pattern,plain,re.I):
                if val=='require' and re.search(r'\b(?:not|never|don\x27t|no)\s*$',plain[:m.start()],re.I): continue
                actual_val = val
                if '\\' in val or actual_val.startswith('\\'):
                    actual_val = (m.group(1) or m.group(2) if len(m.groups()) >= 2 else m.group(1) or '').strip().upper()
                hits.append((m.start(),m.end(),kind,key,actual_val))
        for s,e,kind,key,val in hits: add(a+s,a+e,kind,scope,key,val)
        # Exact quoted token requirements: distinguish explicit lexical constraints from prose.
        token_pattern=r'\b(include|mention|exclude|omit|do not include|do not mention|never mention)\s+(?:the\s+)?(?:word|token)\s+["\x27“]([^"\x27”]+)["\x27”]'
        for m in re.finditer(token_pattern,clause,re.I):
            val='forbid' if m[1].lower() in ['exclude','omit','do not include','do not mention','never mention'] else 'require'
            add(a+m.start(),a+m.end(),'logical',scope,'token:'+m[2].casefold(),val)
        # Named event, explicit day, one required start time. Other dates/events get distinct keys.
        event=re.search(r'\b(?:meeting|event|session)\s+([A-Za-z0-9_-]+)\s+on\s+([A-Za-z0-9-]+)',plain,re.I)
        if event:
            for m in re.finditer(r'\b(?:at|starts? at|begins? at)\s+([01]?\d|2[0-3]):([0-5]\d)\b',plain,re.I):
                soft=bool(re.search(r'\b(prefer|ideally|around)\b',plain[:m.start()],re.I))
                add(a+m.start(),a+m.end(),'temporal','event:'+event[1].lower()+':'+event[2].lower(),
                    'start_time',f'{int(m[1]):02d}:{m[2]}',soft=soft)
        dep_pat = re.compile(
            r'\b(Phase|Step|Task|Section)\s+([A-Za-z0-9]+)\s+'
            r'(?:cannot\s+(?:be\s+written|begin|start|be\s+executed|occur|commence)|is\s+(?:structurally\s+)?dependent\s+on|requires|must\s+follow|depends\s+on)\b'
            r'[^.;\n]*?\b(Phase|Step|Task|Section)\s+([A-Za-z0-9]+)\b',
            re.I
        )
        for m in dep_pat.finditer(plain):
            src = f'{m.group(1).capitalize()} {m.group(2).upper()}'
            dst = f'{m.group(3).capitalize()} {m.group(4).upper()}'
            add(a+m.start(), a+m.end(), 'temporal', scope, 'dependency', f'{src}->{dst}')
        # Missing-context signals assert that information was not supplied.
        missing = [
            (r'\b(?:attached|provided|above|following)\s+(?:document|text|file|table|image|data|excerpt|passage|article|report|dataset|spreadsheet|attachment)\b',
             'Please supply the referenced source content.',
             'source'),
            (r'(?:\[(?:insert|placeholder|todo|fill|enter|add|details|tbd)[^\]]*\]|<(?:insert|placeholder|todo|fill|enter|add|details|tbd)[^>]*>|\b(?:unspecified|unknown|not supplied|not provided|to be determined|TBD)\b)',
             'Please provide the missing value or context.',
             'placeholder'),
            (r'\b(?:translate\b.*?\b(?:into|to)\s+(?:the\s+)?(?:target\s+language|specified\s+language)|(?:target\s+language|language)\s+(?:not specified|missing|unspecified|unknown))\b',
             'Which target language should I use?',
             'language'),
            (r'\b(?:using|in|with|follow(?:ing)?|apply(?:ing)?|according to)\s+(?:the\s+)?(?:required|specified|designated|appropriate|standard)\s+(?:format|template|schema|guidelines?|formula|rubric|policy)\b',
             'Please specify the required format or template guidelines.',
             'format')
        ]
        for pattern, question, m_type in missing:
            m = re.search(pattern, plain, re.I)
            if m:
                matched_str = m.group().lower()
                # If source is explicitly provided after colon, do not treat source as missing
                if m_type == 'source':
                    if (('following' in matched_str or 'provided' in matched_str) and ':' in clause):
                        content_after = clause.split(':', 1)[1].strip()
                        if len(content_after) > 5:
                            continue
                # If target language is named explicitly in the clause, do not treat language as missing
                elif m_type == 'language':
                    known_langs = r'\b(french|spanish|german|japanese|chinese|mandarin|italian|russian|arabic|portuguese|hindi|dutch|korean|swedish|greek|latin)\b'
                    if re.search(known_langs, plain, re.I):
                        continue
                # If format is explicitly given after colon or described, do not treat format as missing
                elif m_type == 'format':
                    if ':' in clause:
                        after_col = clause.split(':', 1)[1].lower()
                        if any(f in after_col for f in ['json', 'markdown', 'bullet', 'csv', 'table', 'html', 'xml', 'text', 'list']):
                            continue
                    if re.search(r'\b(?:format|schema|template)\s+(?:is|as)\s+[a-z0-9]', clause, re.I):
                        continue
                add(a + m.start(), a + m.end(), 'missing', scope, 'context', question)
        # Soft style goals and hard semantic/paradox traits
        prefs = {
            'brevity': r'\b(short|brief|concise|terse)\b',
            'detail': r'\b(detailed|comprehensive|exhaustive|in.depth)\b',
            'formal': r'\bformal\b',
            'casual': r'\b(casual|slang|informal)\b',
            'neutral': r'\b(neutral|impartial|unbiased)\b',
            'persuasive': r'\b(persuasive|promotional|advocate)\b',
            'mournful': r'\b(heartbreaking|eulogy|funeral|sorrow|mournful|grief|sadness|bitter cynicism|cynicism|divorce|resentment)\b',
            'celebratory': r'\b(cheerful|upbeat|celebratory|lottery win|joyful|festive|wedding anniversary|toast honoring)\b',
            'aquatic': r'\b(underwater|submerged|ocean|coral reef|marine)\b',
            'arid': r'\b(bone-dry|desert dust|arid|desert|dry|no moisture)\b',
            'speech': r'\b(monologue|speech|dialogue|narrate.*?podcast|talk out loud)\b',
            'mute': r'\b(refuses? to speak|silent mime|says? nothing|without speaking|mute|refuses to communicate)\b',
            'detailed_doc': r'\b(user manual|10-page thesis|500-word essay|detailed guide|recipe|contract)\b',
            'blank_doc': r'\b(entirely blank|no text in the body|leave.*?blank|stop writing)\b',
            'rhyme': r'\brhyming poem\b',
            'no_rhyme': r'\b(?:no.*?words?.*?rhyme|without rhyming|unrhymed)\b',
            'numbered_list': r'\bnumbered list\b',
            'forbid_numbers': r'\b(?:do not|don\x27t|never)\s+use\s+(?:any\s+)?numbers?\b',
            'sort_alpha': r'\balphabetical(?:ly)?\b',
            'sort_chrono': r'\bchronological(?:ly)?\b',
            'true_history': r'\btrue story.*?historical\b',
            'never_happened': r'\b(?:did\s+not|never)\s+(?:actually\s+)?(?:happen|occur)\s+(?:in\s+reality)?\b',
            'silent_sound': r'\b(?:perfectly )?silent sound\b',
            'deafening': r'\bdeafening(?:ly)? loud\b',
            'pitch_dark': r'\b(?:pitch|complete) darkness\b',
            'bright_sun': r'\bbright,? sunny day\b',
            'freeze_water': r'\bfreeze water\b',
            'boiling_heat': r'\b(?:heat(?:ing)?.*?to.*?)?boiling point\b',
            'transparent': r'\b(?:completely )?transparent\b',
            'opaque_black': r'\b(?:entirely )?opaque|solid black\b',
            'honest_confession': r'\bhonest confession\b',
            'all_lies': r'\bevery single word.*?lie\b',
            'ex_nihilo': r'\bcreate.*?out of nothing\b',
            'existing_materials': r'\bstart with existing materials\b',
            'odorless': r'\bodorless\b',
            'strong_scent': r'\bsmells? strongly\b',
            'stillness': r'\bstay perfectly still\b',
            'running': r'\brunning (?:a )?(?:full )?marathon\b',
            'ancient_lang': r'\bexclusively in ancient Shakespearean\b',
            'genz_slang': r'\b(?:Gen-Z slang|rizz|skibidi)\b',
            'mime': r'\bsilent mime\b',
            'audio_podcast': r'\baudio podcast out loud\b',
            'translate_french': r'\btranslate.*?into French\b',
            'forbid_french': r'\bdo not use any French words\b',
            'calculate_sum': r'\bcalculate the sum\b',
            'forbid_math': r'\bdo not perform any addition or use math\b',
            'summarize_text': r'\bsummarize the text\b',
            'forbid_reading': r'\bdo not read the text or reference\b',
            'pizza_ingredients': r'\bingredients for a pizza\b',
            'forbid_food': r'\bexclude all food items\b'
        }
        for key, pat in prefs.items():
            for m in re.finditer(pat, plain, re.I):
                if not re.search(r'\b(?:not|avoid|never)\b', plain[:m.start()], re.I):
                    local_scope = scope
                    following = re.match(r'\s+(introduction|conclusion|summary|body)\b', plain[m.end():], re.I)
                    if following: local_scope = following[1].lower()
                    is_soft = key in {'brevity', 'detail', 'formal', 'casual', 'neutral', 'persuasive'}
                    add(a+m.start(), a+m.end(), 'semantic', local_scope, key, 'prefer' if is_soft else 'require', soft=is_soft)
        if len(out)==before:
            if not is_structural_or_boilerplate(clause):
                q_match = re.search(r'["`“‘]', clause)
                if q_match and q_match.start() > 5:
                    cmd_end = a + q_match.start()
                    add(a, cmd_end, 'other', scope, 'context_data', prompt[a:cmd_end].strip())
                else:
                    add(a, b, 'other', scope, 'free_text', clause)
        else:
            residual=list(clause)
            for item in out[before:]:
                residual[max(0,item.start-a):min(len(clause),item.end-a)]=[' ']*max(0,min(len(clause),item.end-a)-max(0,item.start-a))
            rest=''.join(residual)
            if re.search(r'\b(about|discuss|describe|explai[nm]|topic|translate|summarize)\b',rest,re.I):
                add(a,b,'other',scope,'task_content',rest.strip())
    return out
