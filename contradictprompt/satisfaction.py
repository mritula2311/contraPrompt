"""Partial response checker. Unsupported requirements remain unscored, never passed."""
import json
import re
from .extraction import extract

def _reject_nonfinite(value):
    raise ValueError(f'Non-standard JSON constant: {value}')

def check_response(prompt: str,answer: str) -> dict:
    checks=[]; unsupported=[]
    for i in extract(prompt):
        ok=None; measured=None
        if i.scope!='response' or i.soft:
            unsupported.append(i.id); continue
        if i.kind=='numerical' and i.key in ('word','sentence','paragraph','bullet point'):
            if i.key=='word': measured=len(re.findall(r"\b[\w]+(?:['’-][\w]+)*\b",answer))
            elif i.key=='sentence': measured=len([s for s in re.split(r'[.!?]+(?:\s|$)',answer) if s.strip()])
            elif i.key=='paragraph': measured=len([s for s in re.split(r'\n\s*\n',answer) if s.strip()])
            else: measured=len(re.findall(r'^\s*[-*+]\s+\S',answer,re.M))
            ok=(i.lower is None or measured>=i.lower) and (i.upper is None or measured<=i.upper)
        elif i.key=='bullets':
            measured=bool(re.search(r'^\s*[-*+]\s+\S',answer,re.M)); ok=measured==(i.value=='require')
        elif i.key.startswith('token:'):
            measured=bool(re.search(r'(?<!\w)'+re.escape(i.key[6:])+r'(?!\w)',answer,re.I)); ok=measured==(i.value=='require')
        elif i.key=='json_only':
            try: json.loads(answer,parse_constant=_reject_nonfinite); ok=True
            except (ValueError,TypeError): ok=False
        if ok is None: unsupported.append(i.id)
        else: checks.append({'instruction_id':i.id,'text':i.text,'passed':bool(ok),'measured':measured})
    return {'checks':checks,'unsupported_ids':unsupported,'supported_fraction':len(checks)/max(len(checks)+len(unsupported),1),
            'supported_satisfaction':sum(c['passed'] for c in checks)/len(checks) if checks else None,
            'all_supported_pass':all(c['passed'] for c in checks) if checks else None,
            'full_satisfaction':None,
            'note':'Full semantic/task completion requires independent human review. Token/format checks alone do not establish it.'}
