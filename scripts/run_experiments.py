"""Authorized A-D experiments and ablations. Offline evaluation never calls this module."""
import argparse,json,time,hashlib
from pathlib import Path
import pandas as pd
from contradictprompt import analyze,Label
from contradictprompt.llm import LLMClient,ProviderError
from contradictprompt.config import Config
from contradictprompt.repair import suggestions
from contradictprompt.satisfaction import check_response
ROOT=Path(__file__).resolve().parents[1]

def run(limit=20,split='test',authorize=False,output=None):
    if not authorize: raise ValueError('No calls made. Pass --authorize-model-calls after approving model usage.')
    config=Config.from_env(); client=LLMClient(config); client._check()
    out=Path(output or ROOT/'results'/('live_'+time.strftime('%Y%m%d_%H%M%S',time.gmtime())))
    out.mkdir(parents=True,exist_ok=False)
    raw=(ROOT/'data/cases.jsonl').read_bytes()
    cases=[json.loads(s) for s in raw.decode().splitlines() if s.strip()]
    cases=[c for c in cases if c['split']==split][:limit]
    (out/'manifest.json').write_text(json.dumps({'dataset_sha256':hashlib.sha256(raw).hexdigest(),'split':split,'n':len(cases),
        'provider':config.provider,'model':config.model,'temperature':config.temperature,'max_tokens':config.max_tokens,
        'repair_policy':'First local proposal reclassified Compatible; explicitly authorized by evaluation policy.',
        'human_metrics':'Unmeasured until independent ratings are imported.'},indent=2))
    rows=[]; ratings=[]
    methods=['A_direct','B_generic_clarification','C_detection','D_detection_repair']
    for case in cases:
      for method,detector in [(m,'hybrid') for m in methods]+[('ablation',m) for m in ['rules','llm','hybrid']]:
        key=f"{case['id']}::{method}::{detector}"
        row={'run_id':key,'case_id':case['id'],'truth':case['label'],'type':case['conflict_type'],
             'method':method,'detector':detector,'status':'completed','original':case['prompt'],
             'predicted_label':None,'answer':None,'executed_prompt':None,'repair_selected':None}
        begin=time.perf_counter(); offset=len(client.records)
        try:
            if method in ('A_direct','B_generic_clarification'):
                system='Follow the user instructions.'
                if method=='B_generic_clarification': system+=' Ask a concise clarification question when the prompt is unclear or conflicting.'
                row['answer'],_=client.chat(system,case['prompt']); row['executed_prompt']=case['prompt']
            else:
                assessment=analyze(case['prompt'],detector,client)
                if detector!='rules' and not assessment.semantic_checked: raise ProviderError('Hybrid fallback is not scored as a completed hybrid result.')
                row['analysis']=assessment.model_dump(mode='json'); row['predicted_label']=assessment.label.value
                if method=='D_detection_repair' and assessment.label in (Label.IMPOSSIBLE,Label.PARTIAL):
                    for fix in suggestions(assessment):
                        recheck=analyze(fix.prompt,detector,client)
                        if detector!='rules' and not recheck.semantic_checked: raise ProviderError('Repair model validation failed.')
                        if recheck.label==Label.COMPATIBLE:
                            row['repair_selected']=fix.model_dump(); assessment=recheck; break
                if method!='ablation' and assessment.label==Label.COMPATIBLE:
                    row['executed_prompt']=assessment.original
                    row['answer'],_=client.chat('Follow the user instructions.',assessment.original)
                elif method!='ablation': row['clarification']=assessment.clarification_questions or ['Which conflicting requirement should take priority?']
            if row['answer'] is not None:
                row['supported_checks']=check_response(row['executed_prompt'],row['answer'])
                row['original_supported_checks']=check_response(case['prompt'],row['answer'])
        except (ProviderError,ValueError) as exc: row['status']='failed'; row['error']=str(exc)
        usages=client.records[offset:]; row['latency_ms']=(time.perf_counter()-begin)*1000; row['model_calls']=len(usages)
        for name in ['input_tokens','output_tokens']:
            values=[getattr(u,name) for u in usages]
            row[name]=sum(values) if values and all(v is not None for v in values) else None
        rows.append(row)
        with (out/'raw.jsonl').open('a') as f: f.write(json.dumps(row,ensure_ascii=False)+'\n')
        if method!='ablation': ratings.append({'run_id':key,'reviewer':'','predicted_label':'','asked_clarification':'','resolved':'','intent_preserved':'','instruction_satisfaction':'','original_instruction_satisfaction':'','task_completed':'','notes':''})
    fields=['run_id','case_id','truth','type','method','detector','status','predicted_label','latency_ms','model_calls','input_tokens','output_tokens']
    pd.DataFrame([{k:r.get(k) for k in fields} for r in rows]).to_csv(out/'summary.csv',index=False)
    pd.DataFrame(ratings).to_csv(out/'human_ratings.csv',index=False)
    print(out); return out

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--limit',type=int,default=20); p.add_argument('--split',choices=['dev','test'],default='test'); p.add_argument('--authorize-model-calls',action='store_true'); p.add_argument('--output')
    a=p.parse_args()
    if not 1<=a.limit<=1000: p.error('--limit must be 1..1000')
    try: run(a.limit,a.split,a.authorize_model_calls,a.output)
    except (ValueError,ProviderError) as e: p.exit(2,str(e)+'\n')
