# Technical Documentation

## ContradictPrompt: A Hybrid Rule-Based and LLM-Driven Framework for Detecting and Resolving Conflicting User Instructions

**Authors:** Mritula S — E0223031 | Varsha Venkatesan — E0223018  
**Department:** Department of Cyber Security and Internet of Things  
**Project Reference:** Research Project 56 (PE-11), Project Compendium, PDF Page 64  
**Release:** Version 2.0.0 Production Readiness Audit  
**Verified Test Suite:** 191 passing automated tests (100% pass rate)

---

## 1. Problem and Objectives

ContradictPrompt performs deep static instruction analysis on complex natural-language user prompts *before* text generation occurs. The framework:
1. Accepts compound user prompts containing nested, conditional, and multi-domain requirements.
2. Extracts individual instruction atoms with precise original character offsets and attributed scopes.
3. Identifies numerical, formatting, temporal, logical, and semantic contradictions across global and section scopes.
4. Distinguishes genuine impossibilities from compatible requirements, separate section constraints, and underspecified inputs.
5. Classifies prompts into a strict four-class taxonomy: **Compatible**, **Partially Conflicting**, **Fully Impossible**, or **Underspecified**.
6. Constructs a formal **Constraint Graph** and identifies **Minimal Conflicting Sets**.
7. Explains detected conflicts with grounded evidence spans and plain-language rationales.
8. Generates non-identity, minimal repair candidates for user review and approval.
9. Enforces an explicit human-in-the-loop approval gate before revalidating corrected prompts.
10. Optionally generates responses using an approved, validated prompt via NVIDIA NIM cloud inference or local models.
11. Records empirical research evaluation metrics anchored to an immutable Single Source of Truth.

---

## 2. System Architecture & Module Map

The architecture integrates four distinct verification layers:
- **Layer A (Deterministic Rule Engine & SMT Solver):** Scoped numerical interval verification, keyword polarity, format exclusivity, and Z3 SMT cross-scope budget summation.
- **Layer B (Semantic LLM Detection & NVIDIA NIM):** Schema-constrained prompt analysis using NVIDIA NIM (`nvidia/nemotron-3.5-super-vl-120b-a12b`), with graceful fallback and audit logging.
- **Layer C (Constraint Graph & Minimal Conflicting Sets):** Directed graph modeling of instruction dependencies and conflict cycles.
- **Layer D (Programmatic Verification & Gated Repair):** Delta patch generation, user approval gatekeeping, and revalidation.

| Subsystem / Module | File Path | Implementation & Contract Details |
|---|---|---|
| **Input & Normalization** | `contradictprompt/preprocessing.py` | Immutable original preservation; separate whitespace-normalized display copy; exact character offset mapping. |
| **Instruction Extraction** | `contradictprompt/extraction.py` | Regex & heuristic parser with clause segmentation; fixed-width lookbehinds; multi-word section scope attribution; structural heading & list marker isolation. |
| **Deterministic Rules** | `contradictprompt/rules.py` | Pairwise and multi-constraint checks: numerical intervals, boolean token polarity, formatting exclusivity, temporal ordering, security severity levels, PII exposure. |
| **SMT Constraint Solver** | `contradictprompt/solver.py` | Microsoft Z3 SMT solver integration; integer arithmetic feasibility; cross-scope summation checks (`total >= sum(sections)`). |
| **Constraint Graph** | `contradictprompt/constraint_graph.py` | NetworkX-based graph construction; directed edge dependency tracking; cycle detection; minimal conflicting set extraction. |
| **LLM Provider Adapter** | `contradictprompt/llm.py` | HTTP client for NVIDIA NIM (`integrate.api.nvidia.com/v1`) and Ollama; strict Pydantic structured output validation; token accounting; latency profiling; graceful offline fallback. |
| **Core Analysis Engine** | `contradictprompt/engine.py` | Orchestration pipeline; four-class classification precedence; secondary multi-label flag assignment; deterministic override enforcement. |
| **Prompt Repair Engine** | `contradictprompt/repair.py` | Domain-aware delta patch generation (numerical bounds, formatting, dates, severities, PII); non-identity replacement guarantee; approval gatekeeping. |
| **Response Generation** | `contradictprompt/satisfaction.py` | Execution of approved compatible prompts; post-generation instruction compliance checking (word counts, tokens, JSON parseability). |
| **REST API Server** | `server.py` | Production Flask REST server; 14 JSON endpoints; CORS enabled; raw prediction export endpoints. |
| **Web Frontend (SPA)** | `static/index.html`, `app.js`, `style.css` | Modern vanilla JavaScript/CSS single-page application; glassmorphic dark-mode design; interactive graph rendering; zero external framework dependencies. |
| **Legacy Frontend** | `app.py` | Preserved Streamlit interface for backward compatibility. |
| **Evaluation Suite** | `evaluation/` & `scripts/` | 16 adversarial challenge groups (A-P); 5 complexity levels (L1-L5); scikit-learn automated mathematical consistency validation; Single Source of Truth export. |

---

## 3. Data Contracts & Pydantic v2 Models

All shared schemas are implemented as strict Pydantic v2 models with `model_config = ConfigDict(extra='forbid')` to guarantee strict schema adherence:

### 3.1 Instruction Model (`contradictprompt/models.py`)
```python
class Instruction(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str                          # Unique identifier (e.g., 'I1', 'I2')
    text: str                        # Exact original character substring
    start: int                       # Half-open 0-indexed Unicode start offset
    end: int                         # Half-open 0-indexed Unicode end offset
    normalized: str                  # Canonical representation of requirement
    scope: str                       # Target scope ('response', 'introduction', etc.)
    kind: Literal['numerical', 'logical', 'temporal', 'formatting', 'semantic', 'missing', 'other']
    key: str                         # Feature key ('words', 'format', 'bullets', etc.)
    value: str                       # Target value ('json_only', 'require', etc.)
    lower: int | None = None         # Closed integer lower bound
    upper: int | None = None         # Closed integer upper bound
    preference: bool = False         # True if soft heuristic preference
    source: Literal['rule', 'llm'] = 'rule'
```

### 3.2 Conflict Model
```python
class Conflict(BaseModel):
    model_config = ConfigDict(extra='forbid')
    instruction_ids: list[str]       # Conflicting instruction IDs
    kind: Literal['numerical', 'logical', 'temporal', 'formatting', 'semantic', 'other']
    severity: Literal['hard', 'soft']# 'hard' -> Fully impossible; 'soft' -> Partially conflicting
    explanation: str                 # Detailed plain-language justification
    spans: list[str]                 # Exact text spans involved
```

### 3.3 Constraint Graph Models
```python
class GraphNode(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str
    label: str
    kind: str
    scope: str

class GraphEdge(BaseModel):
    model_config = ConfigDict(extra='forbid')
    source: str
    target: str
    type: str                        # 'conflicts_with' | 'depends_on'
    severity: str | None = None

class ConstraintGraphData(BaseModel):
    model_config = ConfigDict(extra='forbid')
    nodes: list[GraphNode]
    edges: list[GraphEdge]
```

### 3.4 Assessment Model (Analysis Result)
```python
class Assessment(BaseModel):
    model_config = ConfigDict(extra='forbid')
    original: str
    normalized: str
    label: Label                     # Compatible | Partially conflicting | Fully impossible | Underspecified
    instructions: list[Instruction]
    conflicts: list[Conflict]
    clarification_questions: list[str]
    explanation: str
    warnings: list[str]
    mode: Literal['rules', 'llm', 'hybrid']
    usage: Usage
    latency_ms: float
    semantic_checked: bool
    secondary_flags: list[str] = Field(default_factory=list)
    minimal_conflicting_sets: list[list[str]] = Field(default_factory=list)
    constraint_graph: ConstraintGraphData | None = None
```

---

## 4. Algorithmic Implementation Details

### 4.1 Clause Segmentation & Token Splitting
- Instruction extraction uses regex clause segmentation with fixed-width lookbehinds: `(?<!\s\d\.)(?<!\s\d\d\.)`.
- Prevents numbered list markers (e.g. `1.`, `2.`, `A.`) from being incorrectly chopped into isolated, broken instructions.
- Section titles and Markdown headings (`# Header`) are identified by `is_structural_or_boilerplate()` and excluded from instruction sets.
- Quoted log blocks (`"..."` / `'...'`) are treated as inert payload evidence and isolated from active prompt imperatives to prevent prompt injection.

### 4.2 Multi-Word Scope Isolation
- Scopes are extracted using case-insensitive boundaries supporting multi-word section headers: `(introduction|conclusion|executive summary|recommendations|methodology|...)`.
- Normalized via `clean_scope()`. Independent section constraints do not cross-pollinate, eliminating false-positive conflicts across sections.

### 4.3 Deterministic SMT Verification (Z3)
- For numerical word budgets, constraints are translated into Z3 integer variables.
- Cross-scope budget summation ensures that if the prompt specifies a total word limit alongside section minimums, Z3 evaluates the joint assertion:
  $$\text{total\_var} \ge \sum \text{sec\_vars}$$
- If the sum of section minimums exceeds the global maximum, an SMT cross-scope conflict is raised.

### 4.4 Multi-Domain Contradiction Detection
- **Numerical:** Disjoint interval boundaries ($[\text{lower}_1, \text{upper}_1] \cap [\text{lower}_2, \text{upper}_2] = \emptyset$).
- **Formatting:** `json_only` output coupled with external conversational prose or Markdown headers.
- **Temporal:** Circular prerequisite deadlocks ($A \to B \to C \to A$) and conflicting exclusive calendar dates.
- **Logical / Security:** Mutually exclusive severity ratings (`HIGH` vs `LOW`) and contradictory PII mandates (`require` vs `forbid`).
- **Missing Context:** Unspecified formats, missing target languages in translation tasks, and unfilled placeholders (`[insert...]`, `TBD`).

### 4.5 Classification Precedence
When multiple conditions exist in a prompt, the engine applies documented deterministic precedence:
$$\mathbf{Fully\ Impossible} \;>\; \mathbf{Underspecified} \;>\; \mathbf{Partially\ Conflicting} \;>\; \mathbf{Compatible}$$
Secondary characteristics are preserved in `secondary_flags` (e.g., an impossible prompt with an unfilled placeholder records `secondary_flags: ['underspecified']`).

---

## 5. NVIDIA NIM Cloud Inference Integration

ContradictPrompt natively integrates NVIDIA NIM cloud inference:
- **Base URL:** `https://integrate.api.nvidia.com/v1`
- **Default Cloud Model:** `nvidia/nemotron-3.5-super-vl-120b-a12b`
- **Fallback Cloud Model:** `meta/llama-3.2-11b-vision-instruct`
- **Authentication:** `NVIDIA_API_KEY` or `CP_API_KEY` loaded via `.env` or system environment.
- **Security:** API keys are automatically masked in diagnostic endpoints (`nvapi-...YVss`); never logged or exported.
- **Diagnostics:**
  - `GET /api/llm/status`: Returns provider status, model ID, latency, and temperature.
  - `POST /api/llm/test`: Live test ping against the configured NVIDIA NIM model.
  - `POST /api/llm/config`: Dynamic switching of model and provider settings.
- **Accounting:** Model invocation count, latency milliseconds, input tokens, and output tokens are accurately tracked on every call.
- **Offline Graceful Fallback:** When remote credentials are absent or network requests fail, the hybrid engine falls back to deterministic rules with an explicit audit warning; it never falsely claims "Hybrid Verified" when running offline.

---

## 6. Empirical Evaluation & Research Results

### 6.1 Single Source of Truth
Evaluation metrics are derived directly from individual case prediction records serialized in:
- JSON: [`results/raw_predictions.json`](file:///d:/ContradictPrompt/ContradictPrompt/results/raw_predictions.json)
- CSV: [`results/raw_predictions.csv`](file:///d:/ContradictPrompt/ContradictPrompt/results/raw_predictions.csv)

Automated numpy/scikit-learn assertions in [`evaluation/metrics.py`](file:///d:/ContradictPrompt/ContradictPrompt/evaluation/metrics.py) mathematically verify that confusion matrix row/column sums, per-class F1, accuracy, and macro-F1 strictly agree.

### 6.2 1,000-Prompt Held-Out Benchmark Performance
Evaluated across [`data/pe11_heldout_benchmark_1000.json`](file:///d:/ContradictPrompt/ContradictPrompt/data/pe11_heldout_benchmark_1000.json) (exactly 250 cases per class):
- **Total Prompts Evaluated:** 1,000
- **Total Correct Predictions:** **813 / 1,000**
- **Overall Accuracy:** **81.30%**
- **Macro-Precision:** **0.8338**
- **Macro-Recall:** **0.8130**
- **Four-Class Macro-F1:** **0.8076**
- **Four-Class Weighted-F1:** **0.8076**
- **Binary Contradiction F1:** **0.8571** (Precision: 1.0000, Recall: 0.7500, FPR: 0.0000, FNR: 0.2500)

### 6.3 Per-Class Performance Breakdown

| Class | Support | TP | FP | FN | Precision | Recall | F1-Score |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Compatible** | 250 | 250 | 125 | 0 | 0.6667 | 1.0000 | **0.8000** |
| **Partially Conflicting** | 250 | 188 | 0 | 62 | 1.0000 | 0.7520 | **0.8584** |
| **Fully Impossible** | 250 | 125 | 62 | 125 | 0.6684 | 0.5000 | **0.5721** |
| **Underspecified** | 250 | 250 | 0 | 0 | 1.0000 | 1.0000 | **1.0000** |
| **Macro Average** | **1,000** | **813** | — | — | **0.8338** | **0.8130** | **0.8076** |

### 6.4 Confusion Matrix

```text
                           PREDICTED
ACTUAL LABEL          Compatible   Partial   Impossible   Underspecified    Total
Compatible                   250         0            0                0      250
Partially Conflicting          0       188           62                0      250
Fully Impossible             125         0          125                0      250
Underspecified                 0         0            0              250      250
---------------------------------------------------------------------------------
Predicted Totals             375       188          187              250    1,000
```

---

## 7. Quality Assurance & Verification

- **Automated Tests:** 191 tests across 14 test suites, passing with 100% success rate in 19.10 seconds.
- **Schema Contracts:** 18 dedicated tests in [`tests/test_schema_contracts.py`](file:///d:/ContradictPrompt/ContradictPrompt/tests/test_schema_contracts.py) verifying strict Pydantic v2 schemas (`extra='forbid'`).
- **Section 10 Regressions:** 7 dedicated regression tests in [`tests/test_cybersecurity_regression.py`](file:///d:/ContradictPrompt/ContradictPrompt/tests/test_cybersecurity_regression.py) verifying all 10 mandatory logical and security test cases.
- **Mathematical Integrity:** [`tests/test_adversarial_levels.py`](file:///d:/ContradictPrompt/ContradictPrompt/tests/test_adversarial_levels.py) asserts that confusion matrix entries and classification reports agree mathematically.
