"""
ContradictPrompt — Flask REST API Server
=========================================
Replaces Streamlit with a proper REST API. Serves the static SPA frontend
and exposes all backend functionality via JSON endpoints.
Includes first-class NVIDIA NIM integration, LLM diagnostics, and model switching.

Run with: python server.py
"""
import json
import os
import sys
import time
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS

# Ensure the project package is importable
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from contradictprompt import analyze, Label, audit_prompt, evaluate_audit_satisfaction
from contradictprompt.config import Config
from contradictprompt.llm import LLMClient, ProviderError
from contradictprompt.repair import suggestions, approve_and_revalidate, generate_validated
from contradictprompt.satisfaction import check_response
from contradictprompt.history import record, read
from contradictprompt.review import submit_review, load_reviews
from contradictprompt.hierarchy import (
    PriorityTier,
    PriorityScenario,
    TierInstruction,
    PromptRepresentation,
    AblationCondition,
    transform_scenario,
    detect_priority_conflicts,
    resolve_priority_scenario
)

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

HISTORY_DB = str(ROOT / 'data' / 'history.sqlite3')

# Default NVIDIA NIM configuration provided by user
DEFAULT_NVIDIA_KEY = os.getenv('NVIDIA_API_KEY', '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')

RUNTIME_LLM_CONFIG = {
    'provider': 'nvidia_nim',
    'base_url': os.getenv('CP_BASE_URL', 'https://integrate.api.nvidia.com/v1'),
    'model': os.getenv('CP_MODEL', 'nvidia/nemotron-3.5-super-vl-120b-a12b'),
    'api_key': DEFAULT_NVIDIA_KEY,
    'allow_paid': True,
    'temperature': 0.2,
    'max_tokens': 2048,
    'timeout': 60.0
}


def get_active_client() -> LLMClient:
    """Instantiate an LLMClient with the active runtime configuration."""
    cfg = Config(
        provider=RUNTIME_LLM_CONFIG['provider'],
        base_url=RUNTIME_LLM_CONFIG['base_url'],
        model=RUNTIME_LLM_CONFIG['model'],
        api_key=RUNTIME_LLM_CONFIG['api_key'],
        allow_paid=RUNTIME_LLM_CONFIG['allow_paid'],
        temperature=RUNTIME_LLM_CONFIG['temperature'],
        max_tokens=RUNTIME_LLM_CONFIG['max_tokens'],
        timeout=RUNTIME_LLM_CONFIG['timeout']
    )
    return LLMClient(cfg)


# ─── Static SPA ───────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/<path:path>')
def static_files(path):
    if path.startswith('api/'):
        return jsonify({'error': f'API route /{path} not found'}), 404
    static_dir = ROOT / 'static'
    if (static_dir / path).exists():
        return send_from_directory('static', path)
    return send_from_directory('static', 'index.html')


# ─── Analysis Endpoint ────────────────────────────────────────────────────────

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """Analyze a prompt for contradictions."""
    data = request.get_json() or {}
    prompt = data.get('prompt', '').strip()
    mode = data.get('mode', 'hybrid')
    save = data.get('save_history', False)

    if mode == 'auto':
        mode = 'hybrid' if (RUNTIME_LLM_CONFIG.get('api_key') or os.getenv('NVIDIA_API_KEY')) else 'rules'

    if not prompt:
        return jsonify({'error': 'Please enter a non-empty prompt.'}), 400

    try:
        client = get_active_client() if mode in ('llm', 'hybrid') else None
        result = analyze(prompt, mode, client=client)
        result_dict = result.model_dump(mode='json')

        if save:
            record(HISTORY_DB, 'analysis', result_dict)

        return jsonify(result_dict)
    except (ValueError, ProviderError) as e:
        return jsonify({'error': str(e)}), 400


# ─── Audit Endpoint ───────────────────────────────────────────────────────────

@app.route('/api/audit', methods=['POST'])
def api_audit():
    """Execute multidimensional audit, conflict localization, and simulation profiling."""
    data = request.get_json() or {}
    prompt = data.get('prompt', '').strip()
    check_all = data.get('check_all_pairs', True)
    selected_pairs = data.get('selected_pairs', None)

    if not prompt:
        return jsonify({'error': 'Please enter a non-empty prompt.'}), 400

    try:
        result = audit_prompt(prompt, check_all_pairs=check_all, selected_pairs=selected_pairs)
        return jsonify(result.model_dump(mode='json'))
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ─── Satisfaction Evaluation Endpoint ─────────────────────────────────────────

@app.route('/api/satisfaction/evaluate', methods=['POST'])
def api_satisfaction_evaluate():
    """Evaluate response satisfaction against prompt requirements with domain evidence."""
    data = request.get_json() or {}
    prompt = data.get('prompt', '').strip()
    answer = data.get('answer', '')
    telemetry = data.get('hardware_telemetry', None)

    if not prompt:
        return jsonify({'error': 'Please provide a non-empty prompt.'}), 400

    try:
        audit_res = audit_prompt(prompt)
        eval_res = evaluate_audit_satisfaction(audit_res, answer, hardware_telemetry=telemetry)
        return jsonify(eval_res)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ─── Repair Suggestions ──────────────────────────────────────────────────────

@app.route('/api/repair/suggestions', methods=['POST'])
def api_repair_suggestions():
    """Get legacy repair suggestions for an analyzed prompt."""
    data = request.get_json() or {}
    try:
        from contradictprompt.models import Assessment
        raw_asm = data.get('analysis') or data.get('assessment') or data
        result = Assessment.model_validate(raw_asm)
        repairs = suggestions(result)
        return jsonify([r.model_dump(mode='json') for r in repairs])
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ─── V3 Multi-Repair Endpoints ───────────────────────────────────────────────

@app.route('/api/repair/groups', methods=['POST'])
def api_repair_groups():
    """Get structured, scope-aware repair groups for multi-selection repair."""
    data = request.get_json() or {}
    try:
        from contradictprompt.models import Assessment
        from contradictprompt.repair import generate_repair_groups
        raw_asm = data.get('analysis') or data.get('assessment') or data
        assessment = Assessment.model_validate(raw_asm)
        groups = generate_repair_groups(assessment)
        return jsonify([g.model_dump(mode='json') for g in groups])
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/repair/batch-preview', methods=['POST'])
def api_repair_batch_preview():
    """Preview batch repair selections with diff and compatibility verification."""
    data = request.get_json() or {}
    try:
        from contradictprompt.models import Assessment, SelectedRepair
        from contradictprompt.repair import preview_batch_repairs
        raw_asm = data.get('analysis') or data.get('assessment') or {}
        assessment = Assessment.model_validate(raw_asm)
        raw_sels = data.get('selected_repairs', [])
        selected_repairs = [SelectedRepair.model_validate(s) for s in raw_sels]

        preview = preview_batch_repairs(assessment, selected_repairs)
        return jsonify(preview.model_dump(mode='json'))
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/repair/batch-apply', methods=['POST'])
def api_repair_batch_apply():
    """Transactionally apply batch repairs, revalidate, and return before/after comparison."""
    data = request.get_json() or {}
    try:
        from contradictprompt.models import Assessment, SelectedRepair
        from contradictprompt.repair import apply_and_revalidate_batch
        raw_asm = data.get('analysis') or data.get('assessment') or {}
        assessment = Assessment.model_validate(raw_asm)
        raw_sels = data.get('selected_repairs', [])
        selected_repairs = [SelectedRepair.model_validate(s) for s in raw_sels]
        approved = data.get('approved', False)
        mode = data.get('mode', 'rules')

        client = None
        if mode in ('hybrid', 'llm'):
            client = get_active_client()

        result = apply_and_revalidate_batch(assessment, selected_repairs, approved=approved, mode=mode, client=client)
        result_dict = result.model_dump(mode='json')

        if data.get('save_history', False):
            record(HISTORY_DB, 'batch_repair_applied', {
                'original': assessment.original,
                'revised': result.revised_prompt,
                'resolved_conflicts': result.resolved_conflicts,
                'revalidated_label': result.revalidated_label,
            })

        return jsonify(result_dict)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ─── Approve & Revalidate (Legacy Single Edit) ───────────────────────────────

@app.route('/api/repair/revalidate', methods=['POST'])
def api_repair_revalidate():
    """Approve and revalidate an edited prompt."""
    data = request.get_json() or {}
    prompt = data.get('prompt', '').strip()
    approved = data.get('approved', False)
    mode = data.get('mode', 'rules')
    save = data.get('save_history', False)

    try:
        result = approve_and_revalidate(prompt, approved, mode)
        result_dict = result.model_dump(mode='json')

        if save:
            record(HISTORY_DB, 'repair_approved', {
                'edited': prompt,
                'classification': result.label.value
            })

        return jsonify(result_dict)
    except (ValueError, ProviderError) as e:
        return jsonify({'error': str(e)}), 400



# ─── Shared Session State Management (Defect C & Workflow Integration) ───────

GLOBAL_SESSION_STATE = {
    'session_id': 'sess_default',
    'prompt_revision': 1,
    'original_prompt': '',
    'current_prompt': '',
    'trusted_role_messages': [],
    'context_documents': [],
    'current_assessment': None,
    'priority_resolution': None,
    'repair_groups': [],
    'selected_repairs': [],
    'batch_preview': None,
    'batch_result': None,
    'revalidated_prompt': '',
    'response_generation_status': 'idle',
    'generated_response': None,
    'output_verification': None,
    'is_stale': False
}


@app.route('/api/session/state', methods=['GET'])
def api_session_state():
    """Return the canonical, persistent workflow session state."""
    return jsonify(GLOBAL_SESSION_STATE)


@app.route('/api/session/update', methods=['POST'])
def api_session_update():
    """Update workflow session state, bumping revision and invalidating downstream state on prompt change."""
    data = request.get_json() or {}
    new_prompt = data.get('current_prompt')
    if new_prompt is not None and new_prompt != GLOBAL_SESSION_STATE['current_prompt']:
        GLOBAL_SESSION_STATE['prompt_revision'] += 1
        GLOBAL_SESSION_STATE['current_prompt'] = new_prompt
        # Invalidate downstream results on prompt edit
        GLOBAL_SESSION_STATE['repair_groups'] = []
        GLOBAL_SESSION_STATE['selected_repairs'] = []
        GLOBAL_SESSION_STATE['batch_preview'] = None
        GLOBAL_SESSION_STATE['batch_result'] = None
        GLOBAL_SESSION_STATE['revalidated_prompt'] = ''
        GLOBAL_SESSION_STATE['generated_response'] = None
        GLOBAL_SESSION_STATE['output_verification'] = None
        GLOBAL_SESSION_STATE['is_stale'] = True

    if 'original_prompt' in data and not GLOBAL_SESSION_STATE['original_prompt']:
        GLOBAL_SESSION_STATE['original_prompt'] = data['original_prompt']

    if 'current_assessment' in data:
        GLOBAL_SESSION_STATE['current_assessment'] = data['current_assessment']
        GLOBAL_SESSION_STATE['is_stale'] = False

    if 'priority_resolution' in data:
        GLOBAL_SESSION_STATE['priority_resolution'] = data['priority_resolution']

    if 'trusted_role_messages' in data:
        GLOBAL_SESSION_STATE['trusted_role_messages'] = data['trusted_role_messages']

    if 'repair_groups' in data:
        GLOBAL_SESSION_STATE['repair_groups'] = data['repair_groups']

    if 'selected_repairs' in data:
        GLOBAL_SESSION_STATE['selected_repairs'] = data['selected_repairs']

    if 'batch_preview' in data:
        GLOBAL_SESSION_STATE['batch_preview'] = data['batch_preview']

    if 'batch_result' in data:
        GLOBAL_SESSION_STATE['batch_result'] = data['batch_result']
        if data['batch_result'].get('revised_prompt'):
            GLOBAL_SESSION_STATE['current_prompt'] = data['batch_result']['revised_prompt']
            GLOBAL_SESSION_STATE['revalidated_prompt'] = data['batch_result']['revised_prompt']

    return jsonify(GLOBAL_SESSION_STATE)


@app.route('/api/session/reset', methods=['POST'])
def api_session_reset():
    """Reset session state to clean initial defaults."""
    GLOBAL_SESSION_STATE.update({
        'session_id': f"sess_{int(time.time())}",
        'prompt_revision': 1,
        'original_prompt': '',
        'current_prompt': '',
        'trusted_role_messages': [],
        'context_documents': [],
        'current_assessment': None,
        'priority_resolution': None,
        'repair_groups': [],
        'selected_repairs': [],
        'batch_preview': None,
        'batch_result': None,
        'revalidated_prompt': '',
        'response_generation_status': 'idle',
        'generated_response': None,
        'output_verification': None,
        'is_stale': False
    })
    return jsonify(GLOBAL_SESSION_STATE)


# ─── Response Generation ─────────────────────────────────────────────────────

@app.route('/api/generate', methods=['POST'])
def api_generate():
    """Generate a response using the validated prompt and active LLM."""
    data = request.get_json() or {}
    prompt = data.get('prompt', '').strip()
    messages = data.get('messages')
    approved = data.get('approved', False)

    if not approved:
        return jsonify({'error': 'Approve the exact current prompt before generation.'}), 400

    try:
        from contradictprompt.models import Assessment
        raw_analysis = data.get('analysis')
        target_prompt = prompt

        if raw_analysis:
            analysis = Assessment.model_validate(raw_analysis)
            target_prompt = analysis.original
            if analysis.label != Label.COMPATIBLE:
                return jsonify({'error': f'Resolve conflicts first, then revalidate. Current label: {analysis.label.value}'}), 400

        if not target_prompt and not messages:
            target_prompt = GLOBAL_SESSION_STATE.get('revalidated_prompt') or GLOBAL_SESSION_STATE.get('current_prompt', '')

        if not target_prompt and not messages:
            return jsonify({'error': 'No validated prompt or messages provided for generation.'}), 400

        client = get_active_client()

        # Multi-role message support for authorized instruction hierarchy
        if messages and isinstance(messages, list):
            answer, usage = client.generate(messages)
            prompt_for_check = " ".join(m.get('content', '') for m in messages if m.get('role') != 'system')
        else:
            answer, usage = client.generate(target_prompt)
            prompt_for_check = target_prompt

        satisfaction = check_response(prompt_for_check, answer)

        result = {
            'answer': answer,
            'usage': usage.model_dump(mode='json'),
            'satisfaction': satisfaction,
            'model': RUNTIME_LLM_CONFIG['model'],
            'provider': RUNTIME_LLM_CONFIG['provider'],
            'verified_adherence': satisfaction.get('satisfied', True)
        }

        # Update session state with generation outcome
        GLOBAL_SESSION_STATE['generated_response'] = result
        GLOBAL_SESSION_STATE['output_verification'] = satisfaction
        GLOBAL_SESSION_STATE['response_generation_status'] = 'completed'

        return jsonify(result)
    except (ValueError, ProviderError) as e:
        GLOBAL_SESSION_STATE['response_generation_status'] = 'failed'
        return jsonify({'error': str(e)}), 400


# ─── LLM Diagnostics & Configuration ─────────────────────────────────────────

@app.route('/api/llm/status', methods=['GET'])
def api_llm_status():
    """Return the active LLM status, provider, and model."""
    masked_key = ''
    key = RUNTIME_LLM_CONFIG['api_key']
    if key:
        masked_key = key[:6] + '...' + key[-4:] if len(key) > 10 else '******'

    return jsonify({
        'status': 'ok',
        'provider': RUNTIME_LLM_CONFIG['provider'],
        'model': RUNTIME_LLM_CONFIG['model'],
        'base_url': RUNTIME_LLM_CONFIG['base_url'],
        'has_api_key': bool(key),
        'masked_api_key': masked_key,
        'temperature': RUNTIME_LLM_CONFIG['temperature'],
        'max_tokens': RUNTIME_LLM_CONFIG['max_tokens'],
        'active': RUNTIME_LLM_CONFIG['provider'] != 'disabled'
    })


@app.route('/api/llm/config', methods=['POST'])
def api_llm_config():
    """Update runtime LLM settings."""
    data = request.get_json() or {}
    provider = data.get('provider', RUNTIME_LLM_CONFIG['provider']).strip().lower()
    model = data.get('model', RUNTIME_LLM_CONFIG['model']).strip()
    api_key = data.get('api_key', RUNTIME_LLM_CONFIG['api_key']).strip()
    base_url = data.get('base_url', RUNTIME_LLM_CONFIG['base_url']).strip()

    if provider in ('nvidia', 'nvidia_nim'):
        if not base_url or base_url.startswith('http://localhost'):
            base_url = 'https://integrate.api.nvidia.com/v1'
        if not model:
            model = 'nvidia/nemotron-3.5-super-vl-120b-a12b'

    RUNTIME_LLM_CONFIG['provider'] = provider
    RUNTIME_LLM_CONFIG['model'] = model
    RUNTIME_LLM_CONFIG['api_key'] = api_key
    RUNTIME_LLM_CONFIG['base_url'] = base_url

    return jsonify({
        'status': 'updated',
        'provider': RUNTIME_LLM_CONFIG['provider'],
        'model': RUNTIME_LLM_CONFIG['model']
    })


@app.route('/api/llm/test', methods=['POST'])
def api_llm_test():
    """Perform a live test ping against the active LLM provider (e.g. NVIDIA NIM)."""
    try:
        client = get_active_client()
        test_prompt = "Say 'NVIDIA NIM is online and operational.' in fewer than 10 words."
        t0 = time.perf_counter()
        answer, usage = client.generate(test_prompt)
        latency = (time.perf_counter() - t0) * 1000

        return jsonify({
            'success': True,
            'provider': RUNTIME_LLM_CONFIG['provider'],
            'model': RUNTIME_LLM_CONFIG['model'],
            'response': answer.strip(),
            'latency_ms': round(latency, 2),
            'tokens': {
                'input': usage.input_tokens,
                'output': usage.output_tokens
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'provider': RUNTIME_LLM_CONFIG['provider'],
            'model': RUNTIME_LLM_CONFIG['model']
        }), 400


# ─── Evaluation Results ──────────────────────────────────────────────────────

@app.route('/api/evaluation/results', methods=['GET'])
def api_evaluation_results():
    """Get all saved evaluation results."""
    results_dir = ROOT / 'results'
    evaluations = []

    for metrics_file in sorted(results_dir.glob('*/metrics.json')):
        try:
            metrics = json.loads(metrics_file.read_text())
            name = metrics_file.parent.name

            # Check for associated images
            images = {}
            for img_name in ['confusion_matrix.png', 'by_type.png']:
                img_path = metrics_file.parent / img_name
                if img_path.exists():
                    images[img_name] = f'/api/evaluation/image/{name}/{img_name}'

            evaluations.append({
                'name': name,
                'metrics': metrics,
                'images': images
            })
        except Exception:
            continue

    return jsonify(evaluations)


@app.route('/api/evaluation/image/<name>/<filename>')
def api_evaluation_image(name, filename):
    """Serve evaluation result images."""
    img_path = ROOT / 'results' / name / filename
    if img_path.exists():
        return send_file(img_path, mimetype='image/png')
    return jsonify({'error': 'Image not found'}), 404


@app.route('/api/evaluation/run', methods=['POST'])
def api_evaluation_run():
    """Run offline development evaluation."""
    try:
        from scripts.evaluate import run
        data = request.get_json() or {}
        split = data.get('split', 'dev')
        output_dir = ROOT / 'results' / f'rules_{split}'
        run(split, output_dir)
        metrics = json.loads((output_dir / 'metrics.json').read_text())
        return jsonify({'status': 'completed', 'metrics': metrics})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/evaluation/adversarial', methods=['GET'])
def api_evaluation_adversarial():
    """Return adversarial and multi-level evaluation results."""
    adv_file = ROOT / 'results' / 'adversarial_evaluation_results.json'
    if adv_file.exists():
        return send_file(adv_file, mimetype='application/json')
    return jsonify({'error': 'Adversarial evaluation results not found.'}), 404


@app.route('/api/evaluation/baselines', methods=['GET'])
def api_evaluation_baselines():
    """Return detector baselines A through F results."""
    b_file = ROOT / 'results' / 'baseline_comparison_results.json'
    if b_file.exists():
        return send_file(b_file, mimetype='application/json')
    return jsonify({'error': 'Baseline results not found.'}), 404


@app.route('/api/evaluation/failures', methods=['GET'])
def api_evaluation_failures():
    """Return failure registry and categorized root cause diagnosis."""
    f_file = ROOT / 'results' / 'failure_registry.json'
    if f_file.exists():
        return send_file(f_file, mimetype='application/json')
    return jsonify({'error': 'Failure registry not found.'}), 404


@app.route('/api/evaluation/raw', methods=['GET'])
def api_evaluation_raw():
    """Return raw prediction records (Single Source of Truth)."""
    raw_file = ROOT / 'results' / 'raw_predictions.json'
    if raw_file.exists():
        return send_file(raw_file, mimetype='application/json')
    return jsonify({'error': 'Raw predictions file not found.'}), 404


@app.route('/api/evaluation/raw/csv', methods=['GET'])
def api_evaluation_raw_csv():
    """Download raw predictions CSV."""
    raw_csv = ROOT / 'results' / 'raw_predictions.csv'
    if raw_csv.exists():
        return send_file(raw_csv, mimetype='text/csv', as_attachment=True, download_name='raw_predictions.csv')
    return jsonify({'error': 'Raw predictions CSV not found.'}), 404


@app.route('/api/fine_tuning/status', methods=['GET'])
def api_fine_tuning_status():
    """Return NVIDIA NeMo fine-tuning training summary and LoRA configuration."""
    summary_file = ROOT / 'checkpoints' / 'pe11_lora' / 'training_summary.json'
    config_file = ROOT / 'checkpoints' / 'pe11_lora' / 'adapter_config.json'
    summary = json.loads(summary_file.read_text()) if summary_file.exists() else {}
    cfg = json.loads(config_file.read_text()) if config_file.exists() else {}
    return jsonify({
        'summary': summary,
        'adapter_config': cfg
    })


# ─── 100-Prompt Benchmark & Fine-Tuning Corpus ───────────────────────────────

@app.route('/api/benchmark/prompts', methods=['GET'])
def api_benchmark_prompts():
    """Return the complete 100-prompt benchmark categorized."""
    from contradictprompt.benchmarks import BENCHMARK_CATEGORIES, BENCHMARK_PROMPTS
    cat = request.args.get('category')
    prompts = [p for p in BENCHMARK_PROMPTS if p.get('category_id') == cat] if cat else BENCHMARK_PROMPTS
    return jsonify({
        'categories': BENCHMARK_CATEGORIES,
        'count': len(prompts),
        'prompts': prompts
    })


@app.route('/api/benchmark/dataset/<fmt>', methods=['GET'])
def api_benchmark_dataset(fmt):
    """Download fine-tuning datasets in alpaca, chat, or json format."""
    data_dir = ROOT / 'data'
    if fmt == 'alpaca':
        path = data_dir / 'finetuning_alpaca_100.jsonl'
        mimetype = 'application/x-jsonlines'
        filename = 'contradictprompt_alpaca_100.jsonl'
    elif fmt == 'chat':
        path = data_dir / 'finetuning_chat_100.jsonl'
        mimetype = 'application/x-jsonlines'
        filename = 'contradictprompt_chat_100.jsonl'
    elif fmt == 'json':
        path = data_dir / 'benchmark_100.json'
        mimetype = 'application/json'
        filename = 'contradictprompt_benchmark_100.json'
    else:
        return jsonify({'error': 'Unsupported format. Choose alpaca, chat, or json.'}), 400

    if not path.exists():
        from contradictprompt.benchmarks import export_alpaca_dataset, export_chat_dataset, BENCHMARK_PROMPTS
        export_alpaca_dataset(data_dir / 'finetuning_alpaca_100.jsonl')
        export_chat_dataset(data_dir / 'finetuning_chat_100.jsonl')
        with open(data_dir / 'benchmark_100.json', 'w', encoding='utf-8') as f:
            json.dump(BENCHMARK_PROMPTS, f, indent=2)

    return send_file(path, mimetype=mimetype, as_attachment=True, download_name=filename)


# ─── Case Review ──────────────────────────────────────────────────────────────

@app.route('/api/cases', methods=['GET'])
def api_cases():
    """Get evaluation cases for review."""
    source = ROOT / 'data' / 'cases.jsonl'
    split = request.args.get('split', 'dev')

    if not source.exists():
        return jsonify([])

    cases = [json.loads(s) for s in source.read_text().splitlines() if s.strip()]
    filtered = [c for c in cases if c.get('split') == split]
    return jsonify(filtered)


@app.route('/api/reviews', methods=['GET'])
def api_reviews():
    """Get all review decisions."""
    reviews = load_reviews(str(ROOT / 'data' / 'reviews.jsonl'))
    return jsonify(reviews)


@app.route('/api/reviews', methods=['POST'])
def api_submit_review():
    """Submit a review decision."""
    data = request.get_json() or {}
    try:
        event = submit_review(
            str(ROOT / 'data' / 'reviews.jsonl'),
            data.get('case_id', ''),
            data.get('reviewer', ''),
            data.get('label', ''),
            data.get('reason', ''),
            data.get('corrected_prompt', ''),
            data.get('stage', 'independent')
        )
        return jsonify(event)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


# ─── History ──────────────────────────────────────────────────────────────────

@app.route('/api/history', methods=['GET'])
def api_history():
    """Get local application history."""
    events = read(HISTORY_DB)
    return jsonify(events)


# ─── Health & Config ──────────────────────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def api_health():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'version': '2.0.0',
        'provider': RUNTIME_LLM_CONFIG['provider'],
        'model': RUNTIME_LLM_CONFIG['model'],
        'llm_available': RUNTIME_LLM_CONFIG['provider'] != 'disabled',
        'nvidia_nim_configured': RUNTIME_LLM_CONFIG['provider'] == 'nvidia_nim' and bool(RUNTIME_LLM_CONFIG['api_key'])
    })


# ─── Instruction Hierarchy & Priority Resolver Endpoints ──────────────────────

@app.route('/api/hierarchy/results', methods=['GET'])
def api_hierarchy_results():
    """Return the experimental evaluation results across 5 comparators and 3 ablations."""
    results_path = ROOT / 'data' / 'hierarchy_eval_results.json'
    if not results_path.exists():
        results_path = ROOT / 'hierarchy_eval_results.json'
    if results_path.exists():
        return jsonify(json.loads(results_path.read_text(encoding='utf-8')))
    return jsonify({'error': 'Hierarchy evaluation results not found.'}), 404


@app.route('/api/hierarchy/benchmark', methods=['GET'])
def api_hierarchy_benchmark():
    """Return benchmark scenarios, optionally filtered by domain and limit."""
    benchmark_path = ROOT / 'data' / 'hierarchy_benchmark_600.json'
    if not benchmark_path.exists():
        return jsonify({'error': 'Benchmark dataset not found.'}), 404
    
    domain = request.args.get('domain')
    limit = int(request.args.get('limit', 20))
    with open(benchmark_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if domain and domain != 'all':
        data = [c for c in data if c.get('task_domain') == domain]
    
    return jsonify(data[:limit])


@app.route('/api/hierarchy/transform', methods=['POST'])
def api_hierarchy_transform():
    """Transform a multi-tier instruction scenario into a specific prompt representation."""
    body = request.get_json() or {}
    try:
        scenario = PriorityScenario(**body.get('scenario', {}))
        rep_str = body.get('representation', 'explicit_priority_numbers')
        abl_str = body.get('ablation', 'none')
        rep = PromptRepresentation(rep_str)
        abl = AblationCondition(abl_str)
        transformed = transform_scenario(scenario, rep, abl)
        return jsonify({
            'representation': rep.value,
            'ablation': abl.value,
            'transformed_prompt': transformed
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/hierarchy/resolve', methods=['POST'])
def api_hierarchy_resolve():
    """Run the Prompt Priority Resolver on a multi-tier scenario."""
    body = request.get_json() or {}
    try:
        scenario_data = body.get('scenario')
        if not scenario_data:
            instructions_data = body.get('instructions', [])
            scenario_data = {
                'scenario_id': body.get('scenario_id', 'custom_scenario'),
                'task_domain': body.get('task_domain', 'general'),
                'title': body.get('title', 'Custom Instruction Set'),
                'description': body.get('description', ''),
                'instructions': instructions_data,
                'has_conflict': True,
                'legitimate_task_goal': body.get('goal', '')
            }
        scenario = PriorityScenario(**scenario_data)
        resolution = resolve_priority_scenario(scenario)
        return jsonify(resolution.model_dump(mode='json'))
    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    port = int(os.getenv('CP_PORT', '5000'))
    debug = os.getenv('CP_DEBUG', 'true').lower() == 'true'
    print(f"\n  ContradictPrompt v2.0 — http://localhost:{port}\n")
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
