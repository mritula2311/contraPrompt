"""Run with: python -m streamlit run app.py"""
from pathlib import Path
import html
import json
import streamlit as st
import pandas as pd
from contradictprompt import analyze, Label
from contradictprompt.llm import LLMClient, ProviderError
from contradictprompt.repair import suggestions, approve_and_revalidate, generate_validated
from contradictprompt.satisfaction import check_response
from contradictprompt.history import record,read
from contradictprompt.review import submit_review,load_reviews

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='ContradictPrompt',page_icon='↔',layout='wide')
st.markdown('''<style>.block-container{max-width:1150px;padding-top:2rem}h1{letter-spacing:-.03em}mark{background:#ffe1a3;color:#17212e;padding:2px;border-radius:3px}</style>''',unsafe_allow_html=True)
page=st.sidebar.radio('Workspace',['Home','Prompt Analyzer','Prompt Repair','Response Generator','Research Evaluation','About'])
mode=st.sidebar.selectbox('Detector',['rules','hybrid','llm'],help='Rules works offline. Hybrid and LLM call the configured provider when you analyze.')
save_history=st.sidebar.checkbox('Save prompts in local history',value=False)
st.sidebar.caption('English research prototype · No model training')

def save_event(event,payload):
    if save_history: record(str(ROOT/'data/history.sqlite3'),event,payload)

def highlighted(result):
    ids={v for c in result.conflicts for v in c.instruction_ids}
    spans=sorted((i.start,i.end) for i in result.instructions if i.id in ids)
    merged=[]
    for a,b in spans:
        if merged and a<=merged[-1][1]: merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
        else: merged.append((a,b))
    chunks=[]; pos=0
    for a,b in merged:
        chunks.extend([html.escape(result.original[pos:a]),'<mark>'+html.escape(result.original[a:b])+'</mark>']); pos=b
    chunks.append(html.escape(result.original[pos:]))
    return '<div style="white-space:pre-wrap;line-height:1.8">'+''.join(chunks)+'</div>'

def display(result):
    st.subheader(result.label.value)
    st.write(result.explanation)
    st.markdown(highlighted(result),unsafe_allow_html=True)
    for c in result.conflicts: st.write(f'**{c.kind.title()} · {c.severity} · {", ".join(c.instruction_ids)}** — {c.explanation}')
    for q in result.clarification_questions: st.info(q)
    with st.expander('Extracted instructions',expanded=True):
        st.dataframe(pd.DataFrame([i.model_dump() for i in result.instructions]),hide_index=True,width='stretch')
    for warning in result.warnings: st.warning(warning)
    st.caption(f'{result.latency_ms:.1f} ms · {result.usage.calls} model calls · semantic analysis: {result.semantic_checked}')
    st.download_button('Export analysis JSON',result.model_dump_json(indent=2),'analysis.json','application/json',key='export_'+page)

if page=='Home':
    st.title('ContradictPrompt')
    st.write('Check whether instructions can coexist before asking an AI to follow them.')
    st.markdown('**A hybrid rule-based and LLM-driven framework for detecting and resolving conflicting user instructions**')
    st.write('Analyze a prompt, inspect its conflicting requirements, approve a small correction, and revalidate before generating a response.')
    st.table(pd.DataFrame({'Category':['Compatible','Partially conflicting','Fully impossible','Underspecified'],
        'Meaning':['Requirements appear jointly satisfiable','Soft goals compete; a compromise may work','Hard requirements cannot all hold in the same scope','Essential input is missing']}))
    st.info('Start in Prompt Analyzer. Offline analysis is available immediately. Model calls require configuration and remote-call authorization.')
    st.code('Write exactly 100 words, but use fewer than 80 words.',language=None)
elif page=='Prompt Analyzer':
    st.title('Prompt Analyzer')
    prompt=st.text_area('Original prompt',value='Write exactly 100 words, but use fewer than 80 words.',height=170,key='input_prompt')
    if st.button('Analyze',type='primary'):
        st.session_state.pop('validated',None); st.session_state.pop('response',None)
        try:
            with st.spinner('Checking instructions…'): result=analyze(prompt,mode)
            st.session_state['analysis']=result
            st.session_state.pop('repair_edit',None)
            st.session_state.pop('recheck',None)
            st.session_state.pop('repair_approval',None)
            save_event('analysis',result.model_dump(mode='json'))
            if result.label==Label.COMPATIBLE: st.session_state['validated']=result
        except (ValueError,ProviderError) as e: st.error(str(e)); st.session_state.pop('analysis',None)
    if 'analysis' in st.session_state:
        result=st.session_state.analysis
        if prompt!=result.original:
            st.session_state.pop('validated',None)
            st.info('The input has changed. Analyze again to validate this version.')
        display(result)
elif page=='Prompt Repair':
    st.title('Prompt Repair')
    if 'analysis' not in st.session_state: st.info('Analyze a prompt first.')
    else:
        result=st.session_state.analysis
        st.write('Original prompt'); st.code(result.original,language=None)
        for q in result.clarification_questions: st.info(q+' Add that information in the edited prompt below.')
        options=suggestions(result)
        if options:
            index=st.selectbox('Proposed local edit',range(len(options)),format_func=lambda i:options[i].description)
            st.code(options[index].prompt,language=None)
            if st.button('Load this correction into editor'):
                st.session_state.repair_edit=options[index].prompt
                st.session_state.pop('validated',None)
        if 'repair_edit' not in st.session_state: st.session_state.repair_edit=result.original
        edited=st.text_area('Edited prompt',height=170,key='repair_edit')
        if st.session_state.get('validated') and edited!=st.session_state.validated.original:
            st.session_state.pop('validated',None)
        if st.session_state.get('recheck') and edited!=st.session_state.recheck.original:
            st.session_state.pop('recheck',None)
        approved=st.checkbox('I approve this exact edited prompt',key='repair_approval')
        if st.button('Approve and revalidate',type='primary'):
            st.session_state.pop('validated',None); st.session_state.pop('response',None)
            try:
                checked=approve_and_revalidate(edited,approved,mode)
                st.session_state['recheck']=checked
                save_event('repair_approved',{'original':result.original,'edited':edited,'classification':checked.label.value})
                if checked.label==Label.COMPATIBLE: st.session_state.validated=checked
            except (ValueError,ProviderError) as e: st.error(str(e))
        if 'recheck' in st.session_state: display(st.session_state.recheck)
elif page=='Response Generator':
    st.title('Response Generator')
    result=st.session_state.get('validated')
    # Any subsequent edit invalidates the exact validated snapshot until rechecked.
    if result and 'repair_edit' in st.session_state and st.session_state.repair_edit!=result.original: result=None
    if not result: st.info('Analyze a compatible prompt or approve and revalidate a correction first.')
    else:
        st.code(result.original,language=None)
        st.warning('Prompt validation and answer quality are separate. Offline validation checks only supported patterns.')
        approved=st.checkbox('I approve sending this exact prompt to the configured model')
        if st.button('Generate response',type='primary'):
            try:
                answer,usage=generate_validated(result,LLMClient(),approved)
                st.session_state.response=(answer,usage.model_dump(),result.original)
                save_event('response',{'prompt':result.original,'answer':answer,'usage':usage.model_dump()})
            except (ValueError,ProviderError) as e: st.error(str(e))
        if 'response' in st.session_state:
            answer,usage,executed=st.session_state.response
            if executed==result.original:
                st.write(answer); st.json(usage)
                st.json(check_response(executed,answer))
                st.download_button('Download response',answer,'response.txt')
elif page=='Research Evaluation':
    st.title('Research Evaluation')
    st.info('Bundled numbers are actual offline measurements against synthetic provisional labels. LLM baselines and human review remain separate.')
    tab1,tab2,tab3=st.tabs(['Results','Case review','Experiment guide'])
    with tab1:
        files=sorted((ROOT/'results').glob('*/metrics.json'))
        if files:
            selected=st.selectbox('Saved evaluation',files,format_func=lambda p:str(p.parent.name))
            metrics=json.loads(selected.read_text())
            c1,c2,c3=st.columns(3)
            c1.metric('Accuracy',f"{metrics['accuracy']:.1%}"); c2.metric('Macro-F1',f"{metrics['macro_f1']:.3f}"); c3.metric('Conflict F1',f"{metrics['conflict_f1']:.3f}")
            st.json(metrics)
            for name in ['confusion_matrix.png','by_type.png']:
                if (selected.parent/name).exists(): st.image(str(selected.parent/name))
            for name in ['predictions.csv','metrics.json','by_type.csv']:
                p=selected.parent/name
                if p.exists(): st.download_button('Download '+name,p.read_bytes(),name,key='dl_'+name)
        else: st.info('Run python -m scripts.evaluate --split dev to produce results.')
        if st.button('Run offline development evaluation'):
            from scripts.evaluate import run
            run('dev',ROOT/'results'/'rules_dev')
            st.success('Development evaluation saved. Reload this section to view it.')
        live=sorted((ROOT/'results').glob('live_*/summary.csv'))
        if live:
            for p in live:
                st.subheader(p.parent.name)
                scored=p.parent/'scored_metrics.csv'
                if scored.exists():
                    st.dataframe(pd.read_csv(scored),hide_index=True)
                    st.download_button('Export scored metrics',scored.read_bytes(),scored.name,key=str(scored))
                st.dataframe(pd.read_csv(p),hide_index=True)
                st.download_button('Export live summary',p.read_bytes(),p.name,key=str(p))
    with tab2:
        source=ROOT/'data/cases.jsonl'
        if source.exists():
            cases=[json.loads(s) for s in source.read_text().splitlines()]
            split=st.selectbox('Review partition',['dev','test'])
            if split=='test': st.warning('Keep final test cases hidden during detector development. Review after freezing the detector.')
            cases=[c for c in cases if c['split']==split]
            selected_id=st.selectbox('Case ID',[c['id'] for c in cases])
            case=next(c for c in cases if c['id']==selected_id)
            st.write(case['prompt'])
            st.caption('Assign your label independently before inspecting template rationale.')
            with st.form('review_form'):
                reviewer=st.text_input('Reviewer name')
                label=st.selectbox('Your label',[x.value for x in Label])
                reason=st.text_area('Rationale')
                corrected=st.text_area('Optional corrected prompt')
                stage=st.selectbox('Review stage',['independent','adjudicated'])
                if st.form_submit_button('Save review'):
                    try:
                        submit_review(ROOT/'data/reviews.jsonl',case['id'],reviewer,label,reason,corrected,stage)
                        st.success('Review saved with timestamp.')
                    except ValueError as e: st.error(str(e))
            with st.expander('Template label and rationale (inspect after independent labeling)'): st.json(case)
            reviews=load_reviews(ROOT/'data/reviews.jsonl')
            st.write(f'{len(reviews)} recorded review decisions')
            if reviews: st.download_button('Export review log','\n'.join(json.dumps(x) for x in reviews),'reviews.jsonl')
    with tab3:
        st.code('python -m scripts.generate_corpus\npython -m scripts.evaluate --split dev\npython -m scripts.evaluate --split test\npython -m scripts.run_experiments --limit 20 --authorize-model-calls',language='bash')
        st.write('Four methods: direct answer, generic clarification, detection, detection + approved repair. Three ablations: rules, LLM, hybrid. Live runner stores raw outputs and usage, and exports a human-rating worksheet.')
        st.write('Successful resolution and full instruction satisfaction need independent ratings. Empty metrics mean unmeasured, not zero.')
    if save_history:
        with st.expander('Local application history'): st.dataframe(pd.DataFrame(read(str(ROOT/'data/history.sqlite3'))),hide_index=True)
elif page=='About':
    st.title('About the project')
    st.write('Research question: Can an LLM detect mutually incompatible requirements before trying to execute them?')
    st.write('Primary specification: Research Project 56, PE-11, Project Compendium, PDF page 64.')
    st.table(pd.DataFrame({'Student':['Mritula S — E0223031','Varsha Venkatesan — E0223018'],
       'Workstream':['Detection and AI engine','Application and research evaluation']}))
    st.write('Department: Cyber Security and Internet of Things')
    st.write('The implementation uses deterministic interval and polarity checks plus optional structured LLM analysis. Repairs require approval. No custom training, RAG or external benchmark data is required.')
    st.warning('Limitations: finite English patterns, incomplete scope/conditional reasoning, synthetic template bias, provisional semantic labels, and model-dependent semantic judgments. Do not interpret a clean offline result as a universal proof.')
