"""Regression and acceptance checks added during the extracted-archive audit."""
import json
from pathlib import Path
import pytest
import requests
from contradictprompt import analyze,Label
from contradictprompt.models import Assessment,Instruction,Usage
from contradictprompt.llm import LLMClient,ProviderError
from contradictprompt.config import Config
from contradictprompt.satisfaction import check_response
from scripts.generate_corpus import generate
ROOT=Path(__file__).resolve().parents[1]

def test_evidence_end_cannot_exceed_prompt():
    instruction=Instruction(id='I1',start=0,end=999,text='Hi',normalized='Hi',kind='other')
    with pytest.raises(ValueError):
        Assessment(original='Hi',normalized='Hi',label=Label.COMPATIBLE,instructions=[instruction],explanation='Test')

@pytest.mark.parametrize('label,questions,severity',[
    ('Partially conflicting',[],'hard'),('Underspecified',['What source?'],'hard'),
    ('Partially conflicting',['What source?'],'soft')])
def test_llm_precedence_is_validated(monkeypatch,label,questions,severity):
    instruction=Instruction(id='I1',start=0,end=2,text='Hi',normalized='Hi',kind='other',source='llm')
    raw={'instructions':[instruction.model_dump()], 'label':label,'clarification_questions':questions,
         'conflicts':[{'instruction_ids':['I1'],'kind':'logical','severity':severity,'source':'llm','explanation':'Test evidence'}], 'explanation':'Test'}
    client=LLMClient()
    monkeypatch.setattr(client,'chat',lambda *a,**kw:(json.dumps(raw),Usage()))
    with pytest.raises(ProviderError): client.analyze('Hi')

@pytest.mark.parametrize('answer',['NaN','Infinity','-Infinity','{"value":NaN}'])
def test_nonstandard_json_constants_are_not_valid_json(answer):
    assert check_response('Return JSON only.',answer)['all_supported_pass'] is False

@pytest.mark.parametrize('status',[301,401,429,500])
def test_provider_http_error_is_clear_and_not_retried(monkeypatch,status):
    calls=[]
    class Response: status_code=status
    def post(*a,**kw): calls.append(kw); return Response()
    monkeypatch.setattr('contradictprompt.llm.requests.post',post)
    with pytest.raises(ProviderError,match=f'HTTP {status}'):
        LLMClient(Config(provider='ollama',model='test')).generate('Hello')
    assert len(calls)==1 and calls[0]['allow_redirects'] is False

def test_provider_timeout_is_useful(monkeypatch):
    def post(*a,**kw): raise requests.Timeout('mock timeout')
    monkeypatch.setattr('contradictprompt.llm.requests.post',post)
    with pytest.raises(ProviderError,match='unavailable'):
        LLMClient(Config(provider='ollama',model='test')).generate('Hello')

def test_saved_corpus_matches_reproducible_generator():
    saved=[json.loads(line) for line in (ROOT/'data/cases.jsonl').read_text().splitlines()]
    assert saved==generate()

def test_repair_edit_does_not_show_stale_recheck():
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    app.sidebar.radio[0].set_value('Prompt Analyzer').run(); app.button[0].click().run()
    app.sidebar.radio[0].set_value('Prompt Repair').run(); app.button[0].click().run()
    app.checkbox(key='repair_approval').check().run()
    next(b for b in app.button if b.label=='Approve and revalidate').click().run()
    assert app.session_state.recheck.label==Label.COMPATIBLE
    app.text_area(key='repair_edit').set_value('Write exactly 2 words; use fewer than 1 word.').run()
    assert 'recheck' not in app.session_state and 'validated' not in app.session_state
    assert not app.exception

@pytest.mark.parametrize('prompt',[
    'Use bullet points; do not use bullet points.',
    'Return JSON only; include text outside JSON.',
    'Write exactly 100 words, but use fewer than 80 words.',
    'Schedule event A on Monday at 09:00; schedule event A on Monday at 10:00.'
])
def test_primary_specification_examples(prompt):
    result=analyze(prompt)
    assert result.label==Label.IMPOSSIBLE
    assert all(result.original[i.start:i.end]==i.text for i in result.instructions)
