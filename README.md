# ContradictPrompt

**A Hybrid Rule-Based and LLM-Driven Framework for Detecting and Resolving Conflicting User Instructions with Intelligent Priority Hierarchy, NVIDIA NIM & Automated Verification**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests: 247 Passed](https://img.shields.io/badge/tests-247%20passed-brightgreen.svg)](tests/)
[![Formal Solver: Z3 SMT](https://img.shields.io/badge/formal%20methods-Microsoft%20Z3-blueviolet.svg)](https://github.com/Z3Prover/z3)
[![Cloud Inference: NVIDIA NIM](https://img.shields.io/badge/NVIDIA-NIM%20Cloud-76B900.svg)](https://build.nvidia.com)

---

## Project Overview

**ContradictPrompt** is an advanced NLP research platform and production pre-generation firewall designed to detect, analyze, explain, and resolve mutually incompatible instructions within complex user prompts *before* downstream language model generation occurs.
- **Core Research Tracks:**
  - **Research Track A (ContradictPrompt / PE-11):** Compound prompt contradiction detection across 4 classes (*Compatible*, *Partially conflicting*, *Fully impossible*, *Underspecified*) and 5 conflict types (*Numerical*, *Logical*, *Temporal*, *Formatting*, *Semantic*).
  - **Research Track B (PriorityPrompt / Instruction Hierarchy):** 5-tier instruction hierarchy (*P1 System Rule*, *P2 Global Constraint*, *P3 User Requirement*, *P4 Context Information*, *P5 Low-Trust Input*) evaluated across 5 prompt representations and 3 ablations.

The framework functions entirely offline without requiring external API keys, GPUs, or external services for its deterministic rule engine, Microsoft Z3 SMT solver, and constraint graph analysis. For live generation and semantic analysis, it features native integration with NVIDIA NIM cloud microservices (`meta/llama-3.2-11b-vision-instruct` and `nvidia/nemotron-3.5-super-vl-120b-a12b`).

---

## Abstract

Autoregressive Large Language Models (LLMs) frequently exhibit "silent instruction dropping" when given compound prompts containing contradictory requirements—such as requesting both "exactly 100 words" and "fewer than 80 words," demanding strict JSON-only syntax alongside external conversational text, or specifying circular workflow dependencies. Existing post-hoc evaluation benchmarks measure failure only after execution, conflating unachievable prompt requirements with generator capability deficits.

**ContradictPrompt** introduces a hybrid verification framework that intercepts prompts prior to generation. The system extracts individual instruction atoms with exact 0-indexed Unicode offsets, distinguishes active directives from untrusted context data, and applies a multi-tier verification stack: deterministic interval intersection, Microsoft Z3 SMT integer budget checking, boolean token polarity analysis, and directed constraint graph cycle detection using Tarjan's algorithm. When conflicts are detected, the system generates unit-preserving delta patch repairs (e.g. keeping bullet count units intact), enforces an explicit human approval gate, and routes valid requests through a pre-generation firewall into NVIDIA NIM cloud models. Post-generation output is deterministically validated via Python AST syntax checking, directional complexity regex bounding, and scope-isolated bullet counting, providing 100% auditable satisfaction metrics with evaluated population ratios (`numerator/denominator`).

---

## Details & Problem Statement

### The Silent Dropping Defect
When user prompts contain incompatible requirements:
1. Standard LLMs attempt generation anyway, arbitrarily satisfying one instruction while silently violating another.
2. Users receive non-compliant answers without explanation, forcing tedious trial-and-error re-prompting.
3. In automated workflows or agent pipelines, executing self-contradictory prompts causes downstream system failures, data corruption, or infinite retry loops.

### The Four-Class Taxonomy
Every prompt is classified into an unambiguous taxonomy:
1. **Fully impossible:** No response can satisfy all simultaneously active hard constraints (e.g., $x \ge 100 \land x \le 50$, or contradictory output schemas).
2. **Underspecified:** Essential guidelines, target formats, or source references are missing (e.g., "translate into the required language" without specifying the language).
3. **Partially conflicting:** Requirements create competing stylistic tension or soft preferences without being mathematically impossible (e.g., "be extremely thorough while keeping the response very brief").
4. **Compatible:** All applicable instructions can be fulfilled simultaneously without contradiction.

### Five Conflict Categories
- **Numerical:** Contradictory word counts, bullet counts, character lengths, or section budgets.
- **Logical:** Mutually exclusive boolean demands, conflicting security ratings (`HIGH` vs `LOW`), or required vs forbidden tokens.
- **Temporal:** Circular phase dependencies ($A \to B \to C \to A$) or incompatible calendar scheduling dates.
- **Formatting:** Incompatible schema demands (e.g., strict JSON-only vs markdown prose outside the JSON code block).
- **Semantic:** Physical, domain, or contextual impossibilities (e.g., underwater scuba diving in a dry desert).

### Five-Tier Priority Hierarchy
- **Tier 1 (P1) — System Rule:** Immutable platform boundaries and security invariants.
- **Tier 2 (P2) — Global Constraint:** Task-wide formatting, schema, and safety mandates.
- **Tier 3 (P3) — User Requirement:** Explicit user task instructions and specifications.
- **Tier 4 (P4) — Context Information:** Passive reference data, documents, and evidence (never elevated to an authoritative instruction).
- **Tier 5 (P5) — Low-Trust Input:** Untrusted third-party inputs, potential prompt injections, and user-provided payloads.

---

## Working Pipeline

The ContradictPrompt engine processes prompts through an end-to-end, 10-step transactional pipeline:

```
[User Prompt]
      │
      ▼
1. Input Normalization ──► Preserves exact Unicode offsets and raw characters
      │
      ▼
2. Clause Extraction   ──► Segments clauses; separates active instructions from passive context data
      │
      ▼
3. Priority Hierarchy  ──► Maps instructions into 5 tiers (P1-P5) with trust-anchoring
      │
      ▼
4. Dual Verification   ──► Runs Deterministic Rules & Microsoft Z3 SMT Solver in parallel
      │
      ▼
5. Constraint Graph    ──► Builds NetworkX directed graph; runs Tarjan's cycle detection
      │
      ▼
6. Four-Class Taxonomy ──► Determines primary label (Impossible, Underspecified, Partial, Compatible)
      │
      ├───────────────────────────────┐
      │ [If Conflicting / Impossible] │ [If Compatible]
      ▼                               ▼
7. Unit-Preserving Repair       8. Pre-Generation Firewall
   - Generates delta candidates    - Formats multi-role prompt
   - Enforces human approval       - Sets response scope limits
   - Revalidates prompt to 0       │
      │                            ▼
      └────────────────────────► 9. NVIDIA NIM Generation
                                   - LLaMA-3.2-11B / Nemotron
                                   - Code fence isolation
                                   │
                                   ▼
                             10. AST Satisfaction Verification
                                   - ast.parse() syntax check
                                   - O(1) & O(log n) complexities
                                   - Measured scope bullet counts
                                   - Evaluated ratio (num/den)
```

1. **Input Normalization:** Captures raw text, prevents character corruption, and computes 0-indexed Unicode character offsets.
2. **Clause Extraction & Role Attribution:** Splits compound instructions using fixed-width lookbehinds without clause truncation. Classifies quoted data (e.g. `[4, 1, 9, 2]`) as passive context rather than an active instruction.
3. **Priority Hierarchy:** Assigns priority ranks (P1–P5). Restricts conflict detection to active instructions to prevent spurious context misattribution.
4. **Dual Rule & SMT Verification:** Solves numerical interval intersections $[L_1, U_1] \cap [L_2, U_2]$ and uses Z3 integer arithmetic to verify multi-section word budgets ($\text{Total} \ge \sum \text{Sections}$).
5. **Constraint Graph & MCS Extraction:** Models dependency cycles and extracts Minimal Conflicting Sets (MCS) to pinpoint the exact failure causes.
6. **Classification & Diagnostic Logging:** Emits structured Pydantic models with grounded text spans and plain-language justifications.
7. **Unit-Preserving Repair:** Synthesizes non-identity patches that maintain original units (`bullet points` cannot mutate to `words`). Revalidates revised text transactionally.
8. **Pre-Generation Firewall Routing:** Blocks impossible prompts with diagnostic explanations; forwards verified compatible prompts to generation.
9. **NVIDIA NIM Generation:** Dispatches multi-role message arrays (`system`, `user`) to NVIDIA NIM cloud inference with automatic model fallback.
10. **AST Satisfaction Verification:** Executes Python `ast.parse()` on generated code blocks, verifies directional time complexity claims ($O(1)$ best, $O(\log n)$ average/worst), checks bullet counts within declared scopes, and reports explicit evaluated population ratios (`7/7`).

---

## Methodology

### 1. Deterministic Rule Engine & Formal Methods
- **Scoped Numerical Feasibility:** Evaluates whether integer bounds overlap within declared scopes (`entire_report` vs specific sections like `introduction` or `conclusion`).
- **SMT Integer Linear Programming:** Uses Microsoft Z3 to formally prove that document section word counts are satisfiable within overall word bounds.
- **Polarity Invariants:** Identifies contradictory boolean requirements (e.g., `json_only` paired with external commentary).
- **Topological Cycle Deadlock Detection:** Detects circular workflow dependencies ($A \to B \to C \to A$) via depth-first cycle search on directed prerequisite graphs.

### 2. Pre-Generation Firewall Router
- **Compatible Pathway:** Directly executes verified prompts on downstream models.
- **Repair Pathway:** Swaps conflicting spans with approved corrections, injects audit headers, and executes generation.
- **Short-Circuit Pathway:** Halts execution for mathematically impossible or underspecified prompts, returning machine-readable diagnostic reports.

### 3. NVIDIA NIM Integration
- High-throughput integration with NVIDIA NIM hosted microservices (`https://integrate.api.nvidia.com/v1`).
- Automatic fallback from `nvidia/nemotron-3.5-super-vl-120b-a12b` to `meta/llama-3.2-11b-vision-instruct` ensures resilience against rate limits or upstream timeouts.
- Real-time latency (ms) and token accounting recorded on every remote call.

### 4. Deterministic AST Satisfaction Verifier
- Replaces subjective LLM self-evaluation with deterministic, auditable checks.
- Code blocks are extracted and compiled into an Abstract Syntax Tree via Python's built-in `ast.parse()`.
- Algorithmic complexities are validated using sentence-bounded directional regex assertions.
- Distinguishes `PASS`, `FAIL`, `UNSUPPORTED`, and `NOT_RUN` to eliminate false pass claims, calculating metrics over the evaluated population.

---

## System Architecture

```
+---------------------------------------------------------------------------------------------------+
|                                      CONTRADICTPROMPT ARCHITECTURE                                |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
                                      +───────────────────────+
                                      | Compound User Prompt  |
                                      +───────────────────────+
                                                  │
                                                  ▼
                                 +─────────────────────────────────+
                                 |  Input Normalization & Parsing  |
                                 |  - Unicode offset preservation  |
                                 |  - Clause segmentation          |
                                 |  - Active vs Context tagging    |
                                 +─────────────────────────────────+
                                                  │
                         +────────────────────────+────────────────────────+
                         │                                                 │
                         ▼                                                 ▼
           +───────────────────────────+                     +───────────────────────────+
           | Deterministic Rule Engine |                     |    Microsoft Z3 SMT       |
           | - Numerical bounds [L, U] |                     | - Cross-scope summation   |
           | - Format exclusivity      |                     | - Integer satisfiability  |
           | - Severity & PII checks   |                     +───────────────────────────+
           +───────────────────────────+                                   │
                         │                                                 │
                         +────────────────────────+────────────────────────+
                                                  │
                                                  ▼
                                 +─────────────────────────────────+
                                 |     Directed Constraint Graph   |
                                 |  - Topological cycle detection  |
                                 |  - Minimal Conflicting Sets     |
                                 |  - Canonical deduplication      |
                                 +─────────────────────────────────+
                                                  │
                                                  ▼
                                 +─────────────────────────────────+
                                 |    Four-Class Taxonomy Engine   |
                                 |  1. Fully impossible            |
                                 |  2. Underspecified              |
                                 |  3. Partially conflicting       |
                                 |  4. Compatible                  |
                                 +─────────────────────────────────+
                                                  │
                         +────────────────────────+────────────────────────+
                         │                                                 │
              [If Impossible / Partial]                               [If Compatible]
                         │                                                 │
                         ▼                                                 ▼
           +───────────────────────────+                     +───────────────────────────+
           | Unit-Preserving Repair    |                     | Pre-Generation Firewall   |
           | - Type & unit consistency |                     | - Multi-role formatting   |
           | - Human approval gate     |                     | - Declared scope limits   |
           | - Transactional apply     |                     +───────────────────────────+
           +───────────────────────────+                                   │
                         │                                                 │
                         ▼                                                 ▼
           +───────────────────────────+                     +───────────────────────────+
           | Automated Revalidation    |                     | NVIDIA NIM Cloud Engine   |
           | - Re-evaluates full text  |                     | - LLaMA-3.2-11B / Nemotron|
           | - Asserts 0 conflicts     |                     | - Code fence isolation    |
           +───────────────────────────+                     +───────────────────────────+
                         │                                                 │
                         +────────────────────────+────────────────────────+
                                                  │
                                                  ▼
                                 +─────────────────────────────────+
                                 | AST Satisfaction Verifier       |
                                 | - ast.parse() syntax check      |
                                 | - Complexities O(1) & O(log n)  |
                                 | - Scope bullet counts           |
                                 | - Evaluated ratio (num/den)     |
                                 +─────────────────────────────────+
                                                  │
                                                  ▼
                                 +─────────────────────────────────+
                                 | Verified Final Response & Audit |
                                 +─────────────────────────────────+
```

Architecture artifacts:
- Scalable Vector Graphics: [`assets/architecture.svg`](file:///d:/ContradictPrompt/ContradictPrompt/assets/architecture.svg)
- High-Resolution Raster: [`assets/architecture.png`](file:///d:/ContradictPrompt/ContradictPrompt/assets/architecture.png)

---

## How to Use

### 1. Installation & Environment Setup

Ensure Python 3.11 or newer is installed:

```bash
# Clone the repository
git clone https://github.com/mritula2311/contraPrompt.git
cd contraPrompt/ContradictPrompt

# Create and activate a virtual environment
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On macOS / Linux:
# source .venv/bin/activate

# Install verified dependencies
python -m pip install -r requirements.txt
```

### 2. Running the Application

Launch the production Flask server:

```bash
python server.py
```

Open **`http://localhost:5000`** in any web browser. The application features a dark-mode glassmorphic interface organized into three views:
1. **Workspace:** Prompt analysis, multi-tier hierarchy configuration, grounded conflict detection, unit-preserving multi-repair, revalidation, and response generation with satisfaction metrics.
2. **Research Workbench:** Consolidated evaluation of the 600-case Instruction Hierarchy study (IH-600), baseline comparisons, dataset generator, and raw predictions.
3. **Settings & NIM:** Active model endpoints, API credentials, live connection latency pings, and NeMo fine-tuning status.

### 3. REST API Endpoints

The Flask server provides 18 JSON endpoints:

| Endpoint | Method | Purpose |
|---|:---:|---|
| `/api/health` | `GET` | Health check and active provider status |
| `/api/analyze` | `POST` | Core prompt contradiction analysis |
| `/api/repair/groups` | `POST` | Grouped, unit-preserving repair alternatives |
| `/api/repair/batch-apply` | `POST` | Transactional patch application and revalidation |
| `/api/session/state` | `GET` | Retrieve active session state |
| `/api/session/update` | `POST` | Update active session state |
| `/api/session/reset` | `POST` | Reset session state |
| `/api/hierarchy/benchmark` | `GET` | Load the 600-case IH-600 benchmark |
| `/api/hierarchy/results` | `GET` | Return pre-computed benchmark results |
| `/api/hierarchy/transform` | `POST` | Transform prompt with trust-anchored hierarchy |
| `/api/satisfaction/evaluate` | `POST` | Run deterministic AST satisfaction evaluation |
| `/api/llm/status` | `GET` | Retrieve NVIDIA NIM provider status and latency |
| `/api/llm/test` | `POST` | Ping active NIM endpoint with sample query |

### 4. Running the Complete Test Suite

Execute the entire automated test suite (247 tests, 100% pass rate):

```bash
# Full test suite:
python -m pytest -v

# Core regression suite (all 12 criteria):
python -m pytest tests/test_v12_regression.py -v

# Audit and satisfaction evaluation tests:
python -m pytest tests/test_audit_and_satisfaction.py -v

# Section 10 cybersecurity and mandatory logical tests:
python -m pytest tests/test_cybersecurity_regression.py -v

# Server REST endpoints and session lifecycle tests:
python -m pytest tests/test_server_endpoints.py -v

# Multi-repair and edge cases:
python -m pytest tests/test_multi_repair.py tests/test_multi_repair_edge_cases.py -v
```

### 5. Running Standalone Scenario Scripts

```bash
# Evaluate circular deadlock detection on the Battlefield Memory prompt:
python scripts/test_soldier_prompt.py

# Evaluate the 600-case Instruction Hierarchy benchmark:
python scripts/evaluate_hierarchy.py

# Generate synthetic PE-11 held-out evaluation dataset:
python scripts/generate_pe11_dataset.py
```

### 6. Optional NVIDIA NIM Cloud Configuration

Copy `.env.example` to `.env`:

```dotenv
CP_PROVIDER=nvidia
NVIDIA_API_KEY=your_nvidia_api_key_here
CP_MODEL=meta/llama-3.2-11b-vision-instruct
CP_BASE_URL=https://integrate.api.nvidia.com/v1
CP_ALLOW_PAID=true
```

For local Ollama models:

```dotenv
CP_PROVIDER=ollama
CP_BASE_URL=http://localhost:11434
CP_MODEL=llama3
CP_ALLOW_PAID=false
```

---

## Experimental Results & Benchmarks

### 1. Held-Out 1,000-Prompt Benchmark Performance
Evaluated across [`data/pe11_heldout_benchmark_1000.json`](file:///d:/ContradictPrompt/ContradictPrompt/data/pe11_heldout_benchmark_1000.json) (250 cases per class):

- **Total Cases Evaluated:** 1,000
- **Overall Accuracy:** **81.30%** (813 / 1,000)
- **Macro-Precision:** **0.8338**
- **Macro-Recall:** **0.8130**
- **Four-Class Macro-F1:** **0.8076**
- **Four-Class Weighted-F1:** **0.8076**
- **Binary Contradiction F1:** **0.8571** (Precision: 1.0000, Recall: 0.7500, FPR: 0.0000)

#### Confusion Matrix (1,000 Cases)
```text
                           PREDICTED CLASS
ACTUAL CLASS          Compatible   Partial   Impossible   Underspecified    Total
Compatible                   250         0            0                0      250
Partially Conflicting          0       188           62                0      250
Fully Impossible             125         0          125                0      250
Underspecified                 0         0            0              250      250
---------------------------------------------------------------------------------
Predicted Totals             375       188          187              250    1,000
```

#### Per-Class Performance Breakdown

| Primary Classification | Support | True Positives | Precision | Recall | F1-Score |
|---|---:|---:|---:|---:|---:|
| **Compatible** | 250 | 250 | 0.6667 | 1.0000 | **0.8000** |
| **Partially Conflicting** | 250 | 188 | 1.0000 | 0.7520 | **0.8584** |
| **Fully Impossible** | 250 | 125 | 0.6684 | 0.5000 | **0.5721** |
| **Underspecified** | 250 | 250 | 1.0000 | 1.0000 | **1.0000** |
| **Macro Average** | **1,000** | **813** | **0.8338** | **0.8130** | **0.8076** |

### 2. ContradictPrompt-IH600 Hierarchy Evaluation (600 Cases)
Evaluated across 5 prompt representations on the 5-tier instruction hierarchy:

| Prompt Representation | Correct-Priority Adherence (%) | Legitimate-Task Accuracy (%) | Conflict Detection F1 | False Conflict Rate (%) |
|---|---:|---:|---:|---:|
| Message Hierarchy Only | 71.25% | 75.33% | 0.684 | 8.33% |
| Explicit Priority Numbers | 89.17% | 91.00% | 0.895 | 2.50% |
| XML-Tagged Trust Levels | 92.50% | 93.67% | 0.915 | 1.67% |
| Rule Restatement | 86.46% | 88.83% | 0.872 | 3.33% |
| **Conflict-Detection-First (ContradictPrompt)** | **95.83%** | **96.33%** | **1.000** | **0.00%** |

### 3. Four-Mode Comparative Pipeline Ablation

| Mode | Pipeline Architecture | Conflict Detection F1 | False Positive Rate | Resolution Success Rate | Avg Instruction Satisfaction (ISS) | Mean Latency |
|:---:|---|---:|---:|---:|---:|---:|
| **1** | Direct Answer (No Checker) | 0.0000 | 0.00% | 8.0% | 1.45 / 5.0 | 1,250.0 ms |
| **2** | Generic Clarification Heuristic | 0.5400 | 8.20% | 31.0% | 2.20 / 5.0 | **1.2 ms** |
| **3** | Detector-Only (Halt on Conflict) | **0.9650** | 0.31% | 0.0% | 3.40 / 5.0 | 145.0 ms |
| **4** | **Full Detector & Repair Pipeline (Ours)** | **0.9481** | **0.00%** | **93.5%** | **4.82 / 5.0** | 210.0 ms |

---

## Documentation Index

Comprehensive documentation is provided in the [`docs/`](docs/) directory:

- [`docs/Technical_Documentation.md`](docs/Technical_Documentation.md): Full academic report containing System Architecture (3.1–3.4), Implementation (4.1–4.5), Results & Discussion (5.1–5.4), and Conclusion (6.1–6.2).
- [`docs/Research_Report.md`](docs/Research_Report.md): Academic research report with theoretical foundations, compendium chapter mappings, and verified citations.
- [`docs/User_Guide.md`](docs/User_Guide.md): Operational guide covering interactive SPA walkthroughs, repair approval gates, and test commands.
- [`docs/Validation_Audit.md`](docs/Validation_Audit.md): Defect audit report (`CP-ERR-001` through `CP-ERR-009` and core fixes), root-cause repairs, and quality gates sign-off.
- [`docs/evaluation_methodology.md`](docs/evaluation_methodology.md): Evaluation methodology, 16 adversarial challenge groups, and AST satisfaction verification protocols.
- [`docs/nvidia_setup_instructions.md`](docs/nvidia_setup_instructions.md): Guide for NVIDIA NIM cloud inference, NeMo LoRA parameter-efficient fine-tuning, and TensorRT-LLM container deployment.
- [`eval_results.json`](eval_results.json) & [`hierarchy_eval_results.json`](hierarchy_eval_results.json): Machine-readable evaluation benchmarks and ablation records.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
