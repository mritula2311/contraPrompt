import json,pytest
from contradictprompt import analyze,Label
from contradictprompt.config import Config
from contradictprompt.llm import LLMClient,ProviderError
from contradictprompt.models import Instruction,LLMAnalysis,Usage
class FakeClient:
    def analyze(self,prompt):
        i=Instruction(id='I1',start=0,end=len(prompt),text=prompt,normalized='mock',kind='other',source='llm')
        return LLMAnalysis(instructions=[i],label=Label.COMPATIBLE,conflicts=[],clarification_questions=[],explanation='Mock result.'),Usage(calls=1,input_tokens=10,output_tokens=5)
def test_hard_rule_overrides_llm_disagreement():
    r=analyze('Write exactly 100 words; use fewer than 80 words.','hybrid',FakeClient())
    assert r.label==Label.IMPOSSIBLE and r.semantic_checked and any('disagreed' in w for w in r.warnings)
def test_llm_only_ablation():
    r=analyze('Write exactly 100 words; use fewer than 80 words.','llm',FakeClient())
    assert r.label==Label.COMPATIBLE and not r.conflicts
def test_disabled_provider():
    with pytest.raises(ProviderError): LLMClient(Config()).generate('Hello')
@pytest.mark.parametrize('url',['https://example.com/v1','http://example.com/v1'])
def test_remote_authorization_gate(url):
    with pytest.raises(ProviderError): LLMClient(Config(provider='openai_compatible',base_url=url,model='test')).generate('Hello')
def test_hybrid_fallback_is_disclosed():
    r=analyze('Write a summary.','hybrid',LLMClient(Config()))
    assert not r.semantic_checked and any('fell back' in x for x in r.warnings)
@pytest.mark.parametrize('raw',['not json','{"label":"Compatible"}',json.dumps({'instructions':[], 'label':'Fully impossible','conflicts':[], 'clarification_questions':[],'explanation':'No evidence'})])
def test_structured_validation(monkeypatch,raw):
    c=LLMClient(); monkeypatch.setattr(c,'chat',lambda *a,**kw:(raw,Usage(calls=1)))
    with pytest.raises(ProviderError): c.analyze('Write a summary.')
def test_hallucinated_span_rejected(monkeypatch):
    c=LLMClient(); d=FakeClient().analyze('Write a summary.')[0].model_dump(mode='json'); d['instructions'][0]['text']='invented'
    monkeypatch.setattr(c,'chat',lambda *a,**kw:(json.dumps(d),Usage()))
    with pytest.raises(ProviderError): c.analyze('Write a summary.')
@pytest.mark.parametrize('provider,payload',[
 ('ollama',{'message':{'content':'Hello'},'prompt_eval_count':3,'eval_count':1}),
 ('openai_compatible',{'choices':[{'message':{'content':'Hello'}}],'usage':{'prompt_tokens':3,'completion_tokens':1}})])
def test_provider_transport_mock(monkeypatch,provider,payload):
    class Response:
        status_code=200
        def json(self): return payload
    captured={}
    def post(url,**kwargs): captured.update(kwargs); return Response()
    monkeypatch.setattr('contradictprompt.llm.requests.post',post)
    answer,usage=LLMClient(Config(provider=provider,model='mock')).generate('Hi')
    assert answer=='Hello' and usage.input_tokens==3 and usage.output_tokens==1 and captured['allow_redirects'] is False
def test_credentials_not_in_repr(): assert 'secret-value' not in repr(Config(api_key='secret-value'))
