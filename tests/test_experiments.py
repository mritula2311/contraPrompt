import json
import pytest
from contradictprompt import analyze,Label
from contradictprompt.models import LLMAnalysis,Usage
from scripts.score_live import score
import scripts.run_experiments as experiments

class SimulatedClient:
    """Transport substitute for workflow tests. Never scientific model evidence."""
    def __init__(self,config): self.records=[]
    def _check(self): pass
    def chat(self,*args,**kwargs):
        usage=Usage(calls=1,input_tokens=20,output_tokens=10); self.records.append(usage)
        return 'A simulated response for a workflow test.',usage
    def analyze(self,prompt):
        r=analyze(prompt)
        data={'instructions':[i.model_copy(update={'source':'llm'}) for i in r.instructions],
              'label':r.label,'conflicts':[c.model_copy(update={'source':'llm'}) for c in r.conflicts],
              'clarification_questions':r.clarification_questions,'explanation':r.explanation}
        usage=Usage(calls=1,input_tokens=30,output_tokens=20); self.records.append(usage)
        return LLMAnalysis(**data),usage

def test_full_experiment_pipeline_mock(monkeypatch,tmp_path):
    monkeypatch.setattr(experiments,'LLMClient',SimulatedClient)
    out=experiments.run(limit=2,split='dev',authorize=True,output=tmp_path/'live_test')
    rows=[json.loads(s) for s in (out/'raw.jsonl').read_text().splitlines()]
    assert len(rows)==14 and all(r['status']=='completed' for r in rows)
    assert {r['method'] for r in rows}=={'A_direct','B_generic_clarification','C_detection','D_detection_repair','ablation'}
    metrics=score(out)
    assert len(metrics)==7
    assert all('conflict_f1' in r and 'latency_p95_ms' in r and 'original_instruction_satisfaction_n' in r for r in metrics)
    assert all(r['successful_resolution_rate'] is None for r in metrics)
    assert all(r['final_instruction_satisfaction'] is None for r in metrics)

def test_conditional_and_literal_guard():
    assert analyze('If writing a list, use bullet points; if writing prose, do not use bullet points.').label==Label.COMPATIBLE

def test_stale_prompt_invalidates_generation():
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_file(str(experiments.ROOT/'app.py'),default_timeout=30).run()
    app.sidebar.radio[0].set_value('Prompt Analyzer').run()
    app.text_area[0].set_value('Write a paragraph about solar panels.').run()
    app.button[0].click().run()
    assert app.session_state.validated.label==Label.COMPATIBLE
    app.text_area[0].set_value('Write exactly 100 words; use fewer than 5 words.').run()
    app.sidebar.radio[0].set_value('Response Generator').run()
    assert not app.button
