"""Aggregate live results and adjudicated human scores with explicit denominators."""
import argparse,json,math
from pathlib import Path
import pandas as pd
from sklearn.metrics import accuracy_score,f1_score,classification_report,confusion_matrix
from contradictprompt.models import Label
LABELS=[x.value for x in Label]
def score(directory):
    path=Path(directory); raw=[json.loads(x) for x in (path/'raw.jsonl').read_text().splitlines()]
    ratings=pd.read_csv(path/'human_ratings.csv').fillna('')
    if ratings.run_id.duplicated().any(): raise ValueError('Use one adjudicated rating per run_id.')
    rating_map={r['run_id']:r for r in ratings.to_dict('records')}; result=[]; type_rows=[]
    for (method,detector),group in pd.DataFrame(raw).groupby(['method','detector']):
        rows=group.to_dict('records'); good=[r for r in rows if r['status']=='completed']
        item={'method':method,'detector':detector,'attempted':len(rows),'completed':len(good),
              'latency_median_ms':group.latency_ms.median(),'latency_p95_ms':group.latency_ms.quantile(.95),'model_calls':int(group.model_calls.sum())}
        for field in ['input_tokens','output_tokens']: item[field]=int(group[field].sum()) if group[field].notna().all() else None
        labeled=[]
        for r in good:
            pred=r.get('predicted_label')
            if not isinstance(pred,str) or pred not in LABELS: pred=rating_map.get(r['run_id'],{}).get('predicted_label')
            if pred in LABELS: labeled.append((r,pred))
        for typ in sorted({r['type'] for r,pred in labeled}):
            pairs=[(r,pred) for r,pred in labeled if r['type']==typ]
            type_rows.append({'method':method,'detector':detector,'type':typ,'n':len(pairs),
              'accuracy':accuracy_score([r['truth'] for r,pred in pairs],[pred for r,pred in pairs]),
              'macro_f1':f1_score([r['truth'] for r,pred in pairs],[pred for r,pred in pairs],labels=LABELS,average='macro',zero_division=0)})
        if labeled:
            y=[r['truth'] for r,pred in labeled]; predictions=[pred for r,pred in labeled]
            detail={'classification_report':classification_report(y,predictions,labels=LABELS,output_dict=True,zero_division=0),
                    'confusion_matrix':confusion_matrix(y,predictions,labels=LABELS).tolist(),'labels':LABELS}
            (path/(method+'_'+detector+'_classification.json')).write_text(json.dumps(detail,indent=2))
        item['classification_n']=len(labeled)
        item['accuracy']=accuracy_score([r['truth'] for r,p in labeled],[p for r,p in labeled]) if labeled else None
        item['macro_f1']=f1_score([r['truth'] for r,p in labeled],[p for r,p in labeled],labels=LABELS,average='macro',zero_division=0) if labeled else None
        item['conflict_f1']=f1_score([r['truth'] in ('Partially conflicting','Fully impossible') for r,p in labeled],[p in ('Partially conflicting','Fully impossible') for r,p in labeled],zero_division=0) if labeled else None
        for metric,field,eligible in [
          ('unnecessary_clarification_rate','asked_clarification',lambda r:r['truth']=='Compatible'),
          ('successful_resolution_rate','resolved',lambda r:r['truth'] in ('Partially conflicting','Fully impossible')),
          ('final_instruction_satisfaction','instruction_satisfaction',lambda r:True),
          ('original_instruction_satisfaction','original_instruction_satisfaction',lambda r:True),
          ('task_completion_rate','task_completed',lambda r:True)]:
            vals=[]
            for r in good:
                rating=rating_map.get(r['run_id'],{})
                if not eligible(r) or not rating.get('reviewer') or rating.get(field,'')=='': continue
                v=float(rating[field])
                if not 0<=v<=1: raise ValueError(f'{field} must be between 0 and 1')
                if field=='resolved' and v==1 and str(rating.get('intent_preserved')) not in ('1','1.0'): raise ValueError('Successful resolution requires intent_preserved=1')
                vals.append(v)
            item[metric]=sum(vals)/len(vals) if vals else None; item[metric+'_n']=len(vals)
        result.append(item)
    pd.DataFrame(type_rows).to_csv(path/'scored_by_type.csv',index=False)
    pd.DataFrame(result).to_csv(path/'scored_metrics.csv',index=False)
    (path/'scored_metrics.json').write_text(json.dumps(result,indent=2,default=float)); return result
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('directory'); a=p.parse_args(); print(json.dumps(score(a.directory),indent=2))
