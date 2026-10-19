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

from contradictprompt import analyze, Label
from contradictprompt.config import Config
from contradictprompt.llm import LLMClient, ProviderError
from contradictprompt.repair import suggestions, approve_and_revalidate, generate_validated
from contradictprompt.satisfaction import check_response
from contradictprompt.history import record, read
from contradictprompt.review import submit_review, load_reviews

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


# ─── Repair Suggestions ──────────────────────────────────────────────────────

@app.route('/api/repair/suggestions', methods=['POST'])
def api_repair_suggestions():
    """Get repair suggestions for an analyzed prompt."""
    data = request.get_json() or {}
    try:
        from contradictprompt.models import Assessment
        raw_asm = data.get('analysis') or data.get('assessment') or data
        result = Assessment.model_validate(raw_asm)
        repairs = suggestions(result)
        return jsonify([r.model_dump(mode='json') for r in repairs])
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ─── Approve & Revalidate ────────────────────────────────────────────────────

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


# ─── Response Generation ─────────────────────────────────────────────────────

@app.route('/api/generate', methods=['POST'])
def api_generate():
    """Generate a response using the validated prompt and active LLM."""
    data = request.get_json() or {}
    prompt = data.get('prompt', '').strip()
    approved = data.get('approved', False)

    if not approved:
        return jsonify({'error': 'Approve the exact current prompt before generation.'}), 400

    try:
        from contradictprompt.models import Assessment
        analysis = Assessment.model_validate(data.get('analysis', {}))

        if analysis.label != Label.COMPATIBLE:
            return jsonify({'error': 'Resolve conflicts first, then revalidate.'}), 400

        client = get_active_client()
        answer, usage = client.generate(analysis.original)

        satisfaction = check_response(analysis.original, answer)

        result = {
            'answer': answer,
            'usage': usage.model_dump(mode='json'),
            'satisfaction': satisfaction,
            'model': RUNTIME_LLM_CONFIG['model'],
            'provider': RUNTIME_LLM_CONFIG['provider']
        }
        return jsonify(result)
    except (ValueError, ProviderError) as e:
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


if __name__ == '__main__':
    port = int(os.getenv('CP_PORT', '5000'))
    debug = os.getenv('CP_DEBUG', 'true').lower() == 'true'
    print(f"\n  ContradictPrompt v2.0 — http://localhost:{port}\n")
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
