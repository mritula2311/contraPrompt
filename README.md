# ContradictPrompt

**A Hybrid Rule-Based and LLM-Driven Framework for Detecting and Resolving Conflicting User Instructions**

Mritula S - E0223031 · Varsha Venkatesan - E0223018  
Department of Cyber Security and Internet of Things

Working research prototype based on Project 56 (PE-11), uploaded Project Compendium, PDF page 64. English prompts only. Python 3.11+. No training, GPU, external benchmark or API key is required for offline operation.

## Quick start

```bash
cd ContradictPrompt
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux instead:
# source .venv/bin/activate
python -m pip install -r requirements.txt
python server.py
```

Open http://localhost:5000 in your browser. The app starts with a premium dark-mode single-page interface powered by a Flask REST API (`server.py`). The six sections are Home, Prompt Analyzer, Prompt Repair, Response Generator, Research Evaluation, and About.

> **v2.0 Architecture:** The frontend is a modern vanilla HTML/CSS/JS single-page application with glassmorphism design and zero emoticons (clean SVG vector iconography), served by a Flask REST API (`server.py`). It features first-class **NVIDIA NIM** cloud inference integration (`nvidia/nemotron-3.5-super-vl-120b-a12b`, `meta/llama-3.2-11b-vision-instruct`, etc.) with live ping diagnostics, hybrid conflict detection, and validated response generation. The original Streamlit interface (`app.py`) is preserved for backward compatibility.

### NVIDIA NIM Integration

ContradictPrompt natively supports NVIDIA NIM (OpenAI-compatible cloud API):
- **Base URL:** `https://integrate.api.nvidia.com/v1`
- **Default Model:** `nvidia/nemotron-3.5-super-vl-120b-a12b`
- **API Key:** Set via `NVIDIA_API_KEY` or `CP_API_KEY` in `.env` or system environment.
- **Endpoints:**
  - `GET /api/llm/status`: Checks active provider, model, latency, and status.
  - `POST /api/llm/test`: Live test ping against the configured NVIDIA NIM model.
  - `POST /api/llm/config`: Dynamically switch models or providers.
  - `POST /api/analyze`: Multi-mode contradiction analysis (rules, hybrid, LLM).
  - `POST /api/generate`: Model response generation for approved compatible prompts.

## What is implemented

- Exact original-character evidence spans and a separate whitespace-normalized display copy.
- Scoped numerical intervals, required/forbidden tokens and formats, JSON-only checks, named-event start times, missing-input patterns, and heuristic preference tension.
- Four-class results with explanations, confidence limitations, structured exports and conflict highlighting.
- Configurable Ollama or OpenAI-compatible HTTP adapter; Pydantic validates model output and evidence. Deterministic hard conflicts override a disagreeing model.
- Explicit repair alternatives, manual editing, approval and revalidation before optional generation.
- Partial response-satisfaction checks, separately labeled from prompt validation.
- Optional SQLite history, corpus review/adjudication log, metrics dashboard, CSV/JSON exports.
- 1,000 synthetic cases in 40 template families, 250 per class; 500 development and 500 structural held-out cases.
- Four A-D experiment implementations and rules/LLM/hybrid ablation runner, with authorization gates and independent human-rating worksheet.

## Actual validation and limitations

See `results/tests.xml` for the executed pytest evidence: **191 tests, zero failures, zero errors** (100% pass rate).

### Benchmark Evaluation (1,000-Prompt Balanced Held-Out Corpus)
Evaluated on `data/pe11_heldout_benchmark_1000.json` (250 cases per class):
- **Total Prompts Evaluated:** 1,000
- **Total Correct:** 813 / 1,000
- **Overall Accuracy:** 81.30% (813 / 1,000)
- **Macro-Precision:** 0.8338
- **Macro-Recall:** 0.8130
- **Four-Class Macro-F1:** 0.8076
- **Binary Contradiction F1:** 0.8571
- **Single Source of Truth:** `results/raw_predictions.json` and `results/raw_predictions.csv`
- **Detailed metrics:** Recorded in `results/adversarial_evaluation_results.json`

## Reproduce

```bash
# Execute the complete automated test suite (191 tests):
python -m pytest -q

# Run schema contract tests:
python -m pytest tests/test_schema_contracts.py -q

# Run Section 10 cybersecurity and mandatory logical tests:
python -m pytest tests/test_cybersecurity_regression.py -q

# Run held-out evaluation:
python -m scripts.generate_pe11_dataset
python -m evaluation.adversarial_evaluation
```

`requirements-tested.txt` records the direct dependency versions used in this environment. Python 3.11+ executed the delivered test suite.

## Optional LLM configuration

Copy `.env.example` to `.env`. For NVIDIA NIM cloud inference:

```dotenv
CP_PROVIDER=nvidia
NVIDIA_API_KEY=your_nvidia_api_key_here
CP_MODEL=nvidia/nemotron-3.5-super-vl-120b-a12b
CP_BASE_URL=https://integrate.api.nvidia.com/v1
```

For Ollama local inference:

```dotenv
CP_PROVIDER=ollama
CP_BASE_URL=http://localhost:11434
CP_MODEL=your-installed-model-name
CP_ALLOW_PAID=false
```

Remote calls require explicit authorization followed by `CP_ALLOW_PAID=true`. Keep `.env` private.

## Documentation

- `docs/Technical_Documentation.md`: Architecture, module contracts, algorithms, formal schemas, and empirical results.
- `docs/Research_Report.md`: Academic research report, theoretical foundation, hybrid NLP methods, and verified references.
- `docs/User_Guide.md`: Application user guide, interactive SPA walkthrough, prompt repair approval gate, and NVIDIA NIM setup.
- `docs/Validation_Audit.md`: Comprehensive Release 2.0.0 defect audit (CP-ERR-001–CP-ERR-009), root-cause repairs, and quality gates sign-off.
- `docs/evaluation_methodology.md`: Research evaluation methodology, 16 adversarial challenge groups, and mathematical consistency proofs.
- `docs/nvidia_setup_instructions.md`: NVIDIA NIM cloud inference, NeMo LoRA fine-tuning, and TensorRT-LLM deployment guide.
- `assets/architecture.svg` and `.png`: Exact system architecture diagrams.
- `server.py`: Flask REST API server (v2.0 backend).
- `static/`: Modern SPA frontend with dark-mode glassmorphism UI.

This package is a local application. It is not deployed to a public server.

## Release 2.0.0 Production-Readiness Audit

This release completes the comprehensive end-to-end audit, defect repair, and production verification:
1. **Schema Contract Fix**: Resolved Pydantic v2 `extra_forbidden` error on `Assessment.constraint_graph` by defining formal `GraphNode`, `GraphEdge`, and `ConstraintGraphData` models with strict validation (`extra='forbid'`).
2. **Instruction Extraction**: Fixed list marker chopping (e.g. `1.`, `2.`), preserved full scopes across multi-word section headers, isolated quoted prompt injections, and filtered out non-instruction structural headings.
3. **Multi-Domain Contradiction Engine**: Added domain rules for temporal conflicts (`incident_date`), categorical security severities (`severity_rating`), and privacy requirements (`pii_exposed`), alongside SMT Z3 constraint budget cross-checks.
4. **Repair Engine**: Eliminated identity replacements, implemented domain-aware repairs for temporal, categorical, and privacy constraints, and verified user approval gatekeeping.
5. **NVIDIA NIM Integration**: Normalized source attribution, error reporting, token accounting, and live connectivity diagnostics.
6. **Verification Evidence**: 191 automated tests passing with 0 failures; 1,000 held-out benchmark cases evaluated with genuine measured metrics.
