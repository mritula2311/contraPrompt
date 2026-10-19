"""Append-only independent labels and adjudication; never overwrite generated evidence."""
import json
from datetime import datetime,timezone
from pathlib import Path
from .models import Label

def submit_review(path,case_id,reviewer,label,reason,corrected_prompt='',stage='independent'):
    if not reviewer.strip() or not reason.strip(): raise ValueError('Reviewer name and rationale are required.')
    Label(label)
    if stage not in ('independent','adjudicated'): raise ValueError('Unknown review stage')
    event={'case_id':case_id,'reviewer':reviewer.strip(),'label':str(label),'reason':reason.strip(),
           'corrected_prompt':corrected_prompt,'stage':stage,'timestamp':datetime.now(timezone.utc).isoformat()}
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with open(path,'a',encoding='utf-8') as f: f.write(json.dumps(event,ensure_ascii=False)+'\n')
    return event

def load_reviews(path):
    if not Path(path).exists(): return []
    return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]

def effective_labels(cases,reviews):
    # Only adjudicated labels affect a reviewed evaluation. Prompt corrections require a new corpus version.
    final={r['case_id']:r['label'] for r in reviews if r['stage']=='adjudicated'}
    return {c['id']:final.get(c['id'],c['label']) for c in cases}
