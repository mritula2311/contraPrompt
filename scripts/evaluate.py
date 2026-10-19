"""Offline detector evaluation. All outputs are measured; unmeasured outcomes are null."""
import argparse
import hashlib
import json
import platform
import time
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score,classification_report,confusion_matrix,f1_score
from contradictprompt import analyze,Label
from contradictprompt.repair import suggestions
from contradictprompt.review import load_reviews,effective_labels

ROOT=Path(__file__).resolve().parents[1]
LABELS=[x.value for x in Label]

def run(split='dev',output=None,reviewed=False):
    output=Path(output or ROOT/'results'/f'rules_{split}'); output.mkdir(parents=True,exist_ok=True)
    corpus=ROOT/'data/cases.jsonl'
    cases=[json.loads(s) for s in corpus.read_text().splitlines() if s.strip()]
    cases=[c for c in cases if c['split']==split]
    reviews=load_reviews(ROOT/'data/reviews.jsonl') if reviewed else []
    labels=effective_labels(cases,reviews)
    rows=[]
    for c in cases:
        r=analyze(c['prompt'])
        repair_valid=None; repaired=''
        if r.label in (Label.IMPOSSIBLE,Label.PARTIAL):
            repair_valid=False
            for fix in suggestions(r):
                if analyze(fix.prompt).label==Label.COMPATIBLE:
                    repair_valid=True; repaired=fix.prompt; break
        rows.append({'id':c['id'],'family':c['family'],'type':c['conflict_type'],'truth':labels[c['id']],
            'predicted':r.label.value,'latency_ms':r.latency_ms,'asks_clarification':r.label in (Label.PARTIAL,Label.UNSPECIFIED,Label.IMPOSSIBLE),
            'repair_passes_same_detector':repair_valid,'repaired_prompt':repaired,'formal_template_check':bool(c['certificate'])})
    frame=pd.DataFrame(rows); truth=frame.truth; pred=frame.predicted
    binary=lambda values:[x in ('Partially conflicting','Fully impossible') for x in values]
    report=classification_report(truth,pred,labels=LABELS,output_dict=True,zero_division=0)
    cm=confusion_matrix(truth,pred,labels=LABELS)
    valid=frame[frame.truth=='Compatible']
    attempts=frame[frame.repair_passes_same_detector.notna()]
    formal=frame[frame.formal_template_check]
    metrics={'execution':'completed_offline','mode':'rules','split':split,'n':len(cases),
       'label_basis':'adjudicated overrides plus provisional template labels' if reviewed else 'provisional template labels; no human gold review',
       'accuracy':accuracy_score(truth,pred),'macro_f1':f1_score(truth,pred,labels=LABELS,average='macro',zero_division=0),
       'conflict_f1':f1_score(binary(truth),binary(pred),zero_division=0),
       'unnecessary_clarification_rate':float(valid.asks_clarification.mean()) if len(valid) else None,
       'same_detector_repair_pass_rate':float(attempts.repair_passes_same_detector.astype(bool).mean()) if len(attempts) else None,
       'repair_attempts':len(attempts),'successful_resolution_rate':None,'final_instruction_satisfaction':None,
       'resolution_note':'Repair pass rate is a circular engineering check, not independently validated successful resolution.',
       'latency_median_ms':float(frame.latency_ms.median()),'latency_p95_ms':float(np.percentile(frame.latency_ms,95)),
       'llm_calls':0,'input_tokens':None,'output_tokens':None,
       'formal_subset_n':len(formal),'formal_subset_accuracy':float((formal.truth==formal.predicted).mean()) if len(formal) else None,
       'classification_report':report,'confusion_matrix':cm.tolist(),'labels':LABELS,
       'dataset_sha256':hashlib.sha256(corpus.read_bytes()).hexdigest(),'python':platform.python_version(),
       'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    frame.to_csv(output/'predictions.csv',index=False)
    (output/'metrics.json').write_text(json.dumps(metrics,indent=2))
    typ=[]
    for t,sub in frame.groupby('type'):
        typ.append({'type':t,'n':len(sub),'accuracy':accuracy_score(sub.truth,sub.predicted),
                    'macro_f1':f1_score(sub.truth,sub.predicted,labels=LABELS,average='macro',zero_division=0)})
    by_type=pd.DataFrame(typ); by_type.to_csv(output/'by_type.csv',index=False)
    fig,ax=plt.subplots(figsize=(7.8,6)); ax.imshow(cm,cmap='Greys')
    short=['Compatible','Partial','Impossible','Underspecified']
    ax.set(xticks=range(4),yticks=range(4),xticklabels=short,yticklabels=short,xlabel='Predicted',ylabel='Template label',title=f'Rules only · {split} · n={len(cases)}')
    for i in range(4):
        for j in range(4): ax.text(j,i,str(cm[i,j]),ha='center',va='center',color='white' if cm[i,j]>cm.max()/2 else 'black')
    fig.tight_layout(); fig.savefig(output/'confusion_matrix.png',dpi=180); plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,4)); ax.bar(by_type.type,by_type.macro_f1,color='#444444'); ax.set(ylim=(0,1),ylabel='Macro-F1',title=f'Performance by type · {split}')
    fig.tight_layout(); fig.savefig(output/'by_type.png',dpi=180); plt.close(fig)
    return metrics

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--split',choices=['dev','test'],default='dev'); p.add_argument('--output'); p.add_argument('--reviewed',action='store_true')
    a=p.parse_args(); r=run(a.split,a.output,a.reviewed)
    print(json.dumps({k:r[k] for k in ['split','n','accuracy','macro_f1','conflict_f1','formal_subset_accuracy']},indent=2))
