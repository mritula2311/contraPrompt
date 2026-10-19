from pathlib import Path
import pytest
from contradictprompt.history import record,read
from contradictprompt.review import submit_review,load_reviews,effective_labels
from scripts.generate_corpus import generate,validate_certificate
from scripts.run_experiments import run
ROOT=Path(__file__).resolve().parents[1]
def test_corpus_independence_and_grounding():
    cases=generate()
    assert len(cases)==1000 and len({c['prompt'] for c in cases})==1000
    assert all(sum(c['label']==label for c in cases)==250 for label in {c['label'] for c in cases})
    assert not ({c['family'] for c in cases if c['split']=='dev'} & {c['family'] for c in cases if c['split']=='test'})
    for c in cases:
        for s in c['supporting_spans']: assert c['prompt'][s['start']:s['end']]==s['text']
        if c['certificate']: assert validate_certificate(c)
    assert all(c['review_status']=='pending' for c in cases)
def test_history_sql_safety(tmp_path):
    path=str(tmp_path/'h.sqlite3'); record(path,"analysis'); DROP TABLE events; --",{'prompt':'local'})
    assert len(read(path))==1
def test_review_audit(tmp_path):
    p=tmp_path/'reviews.jsonl'; submit_review(p,'C1','Reviewer A','Compatible','Scopes differ')
    submit_review(p,'C1','Adjudicator','Underspecified','Missing source',stage='adjudicated')
    rows=load_reviews(p); assert len(rows)==2 and effective_labels([{'id':'C1','label':'Compatible'}],rows)['C1']=='Underspecified'
def test_no_live_calls_without_authorization():
    with pytest.raises(ValueError): run(authorize=False)
@pytest.mark.parametrize('page',['Home','Prompt Analyzer','Prompt Repair','Response Generator','Research Evaluation','About'])
def test_app_pages(page):
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run(); app.sidebar.radio[0].set_value(page).run()
    assert not app.exception

def test_app_analyze_repair_revalidate():
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run(); app.sidebar.radio[0].set_value('Prompt Analyzer').run()
    app.button[0].click().run(); assert app.session_state.analysis.label.value=='Fully impossible'
    app.sidebar.radio[0].set_value('Prompt Repair').run(); app.button[0].click().run()
    app.checkbox(key='repair_approval').check().run()
    next(b for b in app.button if b.label=='Approve and revalidate').click().run()
    assert app.session_state.validated.label.value=='Compatible'
    app.sidebar.radio[0].set_value('Response Generator').run(); app.checkbox[0].check().run(); app.button[0].click().run()
    assert any('disabled' in e.value.lower() for e in app.error) and not app.exception
