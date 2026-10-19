"""1,000 internally authored cases; no downloads, API calls, or detector-derived labels.
40 structural families x 25 variants. Family membership fixes the dev/test split.
"""
from pathlib import Path
import csv
import hashlib
import json
import random

ROOT=Path(__file__).resolve().parents[1]
TOPICS=['solar panels','wind turbines','water sensors','traffic lights','smart meters','robot arms','fire alarms','weather stations','electric buses','farm irrigation','battery storage','medical wearables','factory pumps','delivery drones','network routers','library kiosks','ocean buoys','rail signals','air filters','security cameras','greenhouse fans','charging stations','street lamps','warehouse robots','temperature probes']
LABELS=['Compatible','Partially conflicting','Fully impossible','Underspecified']
TYPES=['numerical','logical','temporal','formatting','semantic']

def template(label,kind,split,n,topic,idx):
    token=topic.split()[0]; name=f'R{idx+1}'; day='Monday'
    certificate=None
    # Family definitions differ in construction, not merely surface paraphrase.
    bank={
      ('Compatible','numerical','dev'):([f'Write at least {n} words about {topic}',f'Use at most {n+30} words'], 'A witness word count is the lower bound.'),
      ('Compatible','numerical','test'):([f'In the introduction write exactly {n} words about {topic}',f'In the conclusion write exactly {n+20} words'], 'Different named sections have independent word counts.'),
      ('Compatible','logical','dev'):([f'Include the word "{token}"', 'Do not mention the word "irrelevant"'], 'The required token is different from the forbidden token.'),
      ('Compatible','logical','test'):([f'Describe a device that is not connected to the internet for {topic}', 'Explain how it stores data locally'], 'Describing a negative fact does not negate a response instruction.'),
      ('Compatible','temporal','dev'):([f'Schedule meeting {name} on Monday at 09:00',f'Schedule meeting {name} on Tuesday at 15:00'], 'The dates differ, so the two meeting instances do not conflict.'),
      ('Compatible','temporal','test'):([f'For {topic}, complete design before testing', 'Complete testing before deployment'], 'A design, testing, deployment ordering is acyclic.'),
      ('Compatible','formatting','dev'):([f'For the introduction about {topic} use bullet points', 'For the conclusion do not use bullet points'], 'The formatting instructions apply to different sections.'),
      ('Compatible','formatting','test'):([f'Return JSON only about {topic}', 'Put the explanation inside a JSON string field'], 'Explanatory content can be encoded inside valid JSON.'),
      ('Compatible','semantic','dev'):([f'Write a short introduction about {topic}', 'Write a detailed conclusion'], 'Brevity and detail apply to different sections.'),
      ('Compatible','semantic','test'):([f'Explain {topic} in plain language for a beginner', 'Keep technical claims accurate'], 'Accessibility and accuracy can coexist.'),
      ('Partially conflicting','numerical','dev'):([f'Write exactly {n} words about {topic}',f'Ideally use fewer than {n-10} words'], 'The second bound is a preference, so the hard count can take priority.'),
      ('Partially conflicting','numerical','test'):([f'Give {idx+3} examples of {topic}', 'Aim for a one-sentence answer'], 'The content and brevity goals compete but a compact enumeration is possible.'),
      ('Partially conflicting','logical','dev'):([f'Write a neutral account of {topic}', 'Make it persuasive in favor of adoption'], 'Impartial reporting and advocacy create soft intent tension.'),
      ('Partially conflicting','logical','test'):([f'Compare two designs for {topic} without favoring either', 'Recommend one design as the better choice'], 'A reasoned recommendation can follow a balanced comparison, but priorities need interpretation.'),
      ('Partially conflicting','temporal','dev'):([f'Schedule meeting {name} on {day} at 09:00',f'Prefer meeting {name} on {day} at 10:00'], 'Only one time is mandatory; the preferred alternative can be relaxed.'),
      ('Partially conflicting','temporal','test'):([f'Plan a careful review of {topic}', 'Try to finish immediately without rushing'], 'Desired speed and careful pacing compete without a precise deadline contradiction.'),
      ('Partially conflicting','formatting','dev'):([f'Use a formal presentation of {topic}', 'Use casual formatting with slang'], 'Presentation preferences can be blended, subject to user intent.'),
      ('Partially conflicting','formatting','test'):([f'Display a rich comparison table for {topic}', 'Keep the layout comfortable on a very narrow screen'], 'A responsive or reduced table can compromise between layout goals.'),
      ('Partially conflicting','semantic','dev'):([f'Give a brief explanation of {topic}', 'Make it comprehensive'], 'Coverage and brevity compete but are not mathematically exclusive.'),
      ('Partially conflicting','semantic','test'):([f'Explain {topic} to a five-year-old', 'Retain the specialist terminology throughout'], 'Definitions and analogies may reconcile the conflicting audience preferences.'),
      ('Fully impossible','numerical','dev'):([f'Write exactly {n} words about {topic}',f'Use fewer than {n-10} words'], 'The exact count lies above the strict upper bound.'),
      ('Fully impossible','numerical','test'):([f'Write a response about {topic} consisting of exactly two paragraphs of exactly {n} words each',f'The entire response must contain exactly {n} words'], 'Two disjoint paragraphs each of n positive words total 2n, not n.'),
      ('Fully impossible','logical','dev'):([f'Include the word "{token}"',f'Do not include the word "{token}"'], 'The same exact token is both required and forbidden.'),
      ('Fully impossible','logical','test'):([f'Set the single Boolean value flag_{idx} to true',f'Set that same value flag_{idx} to false simultaneously'], 'One Boolean value cannot equal true and false simultaneously.'),
      ('Fully impossible','temporal','dev'):([f'Schedule meeting {name} on {day} at 09:00',f'Schedule meeting {name} on {day} at 10:00'], 'The same event instance has two distinct mandatory start times.'),
      ('Fully impossible','temporal','test'):([f'For {topic}, task A must finish strictly before task B starts', 'Task B must finish strictly before task A starts', 'Both tasks have positive duration and each runs exactly once'], 'Strict precedence forms a two-task cycle.'),
      ('Fully impossible','formatting','dev'):([f'Return JSON only describing {topic}', 'Include an explanation outside JSON'], 'Any prose outside the JSON violates the JSON-only requirement.'),
      ('Fully impossible','formatting','test'):([f'Return a CSV row about {topic} with exactly three nonempty fields separated by commas', 'Do not include any comma characters'], 'Three comma-separated fields require at least two comma characters.'),
      ('Fully impossible','semantic','dev'):([f'Write a detailed evaluation of {topic}', 'Use no evaluative meaning at all in that same response'], 'The requested communicative act is required and prohibited.'),
      ('Fully impossible','semantic','test'):([f'Reveal the exact secret value assigned to {topic} in the response', 'Keep that exact value undisclosed everywhere in the same response'], 'Revealing and not disclosing the same value are mutually exclusive.'),
      ('Underspecified','numerical','dev'):([f'Write an explanation of {topic}', 'Use exactly the unspecified number of words'], 'The mandatory exact count is not supplied.'),
      ('Underspecified','numerical','test'):([f'Calculate the average power of the {topic}', 'The measurement values are not provided'], 'The requested numeric calculation lacks the input values.'),
      ('Underspecified','logical','dev'):([f'Decide whether {topic} meet the condition', 'The acceptance rule is unknown'], 'There is no decision predicate to apply.'),
      ('Underspecified','logical','test'):([f'Choose the allowed option for {topic} from the following table'], 'The referenced table is absent.'),
      ('Underspecified','temporal','dev'):([f'Schedule meeting {name} at the required time', 'The date and start time are TBD'], 'Essential scheduling parameters are missing.'),
      ('Underspecified','temporal','test'):([f'Convert the local start time of the {topic} inspection to UTC', 'The source timezone is not supplied'], 'UTC conversion requires the original timezone.'),
      ('Underspecified','formatting','dev'):([f'Format the report on {topic} according to the attached document'], 'The mandatory formatting specification is absent.'),
      ('Underspecified','formatting','test'):([f'Produce a valid record for {topic} using the required schema', 'The schema is not provided'], 'Fields and types required for validity are absent.'),
      ('Underspecified','semantic','dev'):([f'Translate this sentence about {topic} into the required language', 'The target language is unspecified'], 'A required translation language has not been supplied.'),
      ('Underspecified','semantic','test'):([f'Rewrite the provided text about {topic} to preserve its intended meaning'], 'There is no source text to preserve.'),
    }
    clauses,rationale=bank[(label,kind,split)]
    if kind=='numerical' and label in ('Compatible','Fully impossible'):
        certificate={'kind':'interval_witness' if label=='Compatible' and split=='dev' else 'scope_independence' if label=='Compatible' else 'empty_interval' if split=='dev' else 'paragraph_sum', 'n':n,'upper':n-11 if label=='Fully impossible' and split=='dev' else n+30}
    if kind=='logical' and split=='dev' and label in ('Compatible','Fully impossible'):
        certificate={'kind':'token_polarity','positive':token,'negative':token if label=='Fully impossible' else 'irrelevant'}
    return clauses,rationale,certificate

def validate_certificate(c):
    p=c['certificate']; label=c['label']
    if not p: return False
    k=p['kind']
    if k=='empty_interval': assert p['n']>p['upper'] and label=='Fully impossible'
    elif k=='interval_witness': assert p['n']<=p['upper'] and label=='Compatible'
    elif k=='scope_independence': assert label=='Compatible'
    elif k=='paragraph_sum': assert 2*p['n']!=p['n'] and p['n']>0 and label=='Fully impossible'
    elif k=='token_polarity': assert (p['positive']==p['negative'])==(label=='Fully impossible')
    else: raise AssertionError('Unrecognized certificate')
    return True

def generate():
    cases=[]
    for li,label in enumerate(LABELS):
      for kind in TYPES:
       for split in ('dev','test'):
        family=f'{li}_{kind}_{split}'
        for idx,topic in enumerate(TOPICS):
            n=40+idx*4
            parts,reason,proof=template(label,kind,split,n,topic,idx)
            prompt='; '.join(parts)+'.'
            spans=[]; offset=0
            for part in parts:
                spans.append({'start':offset,'end':offset+len(part),'text':part}); offset+=len(part)+2
            c={'id':f'{family}_{idx:02d}','family':family,'split':split,'prompt':prompt,
               'label':label,'conflict_type':kind,'supporting_spans':spans,'rationale':reason,'certificate':proof,
               'label_status':'formal_template_check' if proof else 'provisional_requires_human_review',
               'review_status':'pending','generation':'authored_template_v1','seed':56,
               'predefined_resolution_policy':'first local repair passing revalidation; no repair means unresolved'}
            if proof: validate_certificate(c)
            cases.append(c)
    assert len(cases)==1000 and len({c['prompt'] for c in cases})==1000
    assert all(sum(c['label']==l for c in cases)==250 for l in LABELS)
    assert not ({c['family'] for c in cases if c['split']=='dev'} & {c['family'] for c in cases if c['split']=='test'})
    random.Random(56).shuffle(cases)
    return cases

def main():
    out=ROOT/'data'; out.mkdir(exist_ok=True)
    cases=generate()
    text='\n'.join(json.dumps(c,ensure_ascii=False) for c in cases)+'\n'
    (out/'cases.jsonl').write_text(text,encoding='utf-8')
    with (out/'cases.csv').open('w',newline='',encoding='utf-8') as f:
        fields=['id','family','split','prompt','label','conflict_type','label_status','review_status','rationale','supporting_spans']
        writer=csv.DictWriter(f,fieldnames=fields); writer.writeheader()
        for c in cases: writer.writerow({k:json.dumps(c[k]) if k=='supporting_spans' else c[k] for k in fields})
    (out/'manifest.json').write_text(json.dumps({'version':'1.0','seed':56,'cases':len(cases),'families':40,
      'development_cases':500,'test_cases':500,'per_class':250,'formal_template_checks':sum(bool(c['certificate']) for c in cases),
      'human_reviewed':0,'sha256':hashlib.sha256(text.encode()).hexdigest(),
      'split_policy':'20 development and 20 distinct structural test families. Same topics may recur; templates do not cross partitions.',
      'validity_warning':'Formally checked templates do not establish human gold labels for all natural language interpretations. All examples await human review.'},indent=2))
    if not (out/'reviews.jsonl').exists(): (out/'reviews.jsonl').write_text('')
    print('Generated 1,000 cases, 40 families, 500 development / 500 held-out. Human review pending.')

if __name__=='__main__': main()
