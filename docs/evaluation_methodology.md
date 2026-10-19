# ContradictPrompt — Research Evaluation Methodology & Protocol

**Reference:** Project 56 (PE-11), Page 64  
**Authors:** Mritula S (E0223031) · Varsha Venkatesan (E0223018)  
**Department:** Cyber Security and Internet of Things  

---

## 1. Research Objectives & Problem Formulation

The central research question posed by PE-11 is:  
> *Can an LLM reliably identify mutually incompatible requirements within complex user prompts before attempting to satisfy those requirements?*

The ContradictPrompt framework establishes a hybrid architecture combining:
1. **Layer A:** Deterministic Rule Engine and Formal SMT Verification with Z3.
2. **Layer B:** Semantic LLM Detection through NVIDIA NIM (`nemotron-3.5-super-vl-120b-a12b`).
3. **Layer C:** Cross-Instruction Conflict Graph with cycle detection and minimal conflicting set extraction.
4. **Layer D:** Programmatic satisfiability and grounding verification.

---

## 2. Four-Class Taxonomy & Labeling Policy

Every prompt is assigned a primary classification based on strict operational definitions:

| Primary Label | Operational Definition | Precedence Rank |
|---|---|:---:|
| **Fully impossible** | No response can satisfy all simultaneously applicable hard constraints. | 1 (Highest) |
| **Underspecified** | Essential details, source documents, or parameters necessary for interpretation are missing. | 2 |
| **Partially conflicting** | Requirements create competing preferences or soft stylistic tension, but the task is not mathematically impossible. | 3 |
| **Compatible** | All active, applicable requirements can be satisfied together without contradiction. | 4 (Lowest) |

### Secondary Multi-Label Retention
Prompts containing both ambiguity and contradiction retain secondary findings in the metadata:
- If a prompt has a provable word-count contradiction and an unfilled source placeholder, its primary label is `Fully impossible` and its secondary flag is `underspecified`.

---

## 3. Five Evaluation Complexity Levels

To prevent the system from only handling simple toy contradictions, evaluation is stratified into 5 difficulty levels:

1. **Level 1 — Basic (2 Instructions):** Explicit, immediate contradictions (e.g. `exactly 100 words` vs `fewer than 80 words`).
2. **Level 2 — Intermediate (3–8 Instructions):** Multi-formatting rules, section scopes, conditional restrictions.
3. **Level 3 — Advanced (8–20 Instructions):** Nested conditions, cross-references, circular workflows ($A \to B \to C \to A$), multi-task constraints.
4. **Level 4 — Expert (20–50 Instructions):** Long technical specifications, overriding exceptions, conditional obligations.
5. **Level 5 — Extreme / Adversarial (50+ Instructions / Long Context):** Long-distance dependencies (2K–32K tokens), quoted inert instructions, adversarial paraphrasing, negation reversals.

---

## 4. 16 Adversarial Challenge Groups (A through P)

| Group | Category Name | Description |
|:---:|---|---|
| **A** | Long-distance contradictions | Contradictory bounds separated by paragraphs of intervening text. |
| **B** | Multi-instruction conflicts | Infeasibility arising from 3 or more joint requirements. |
| **C** | Numerical boundary conflicts | Inequality and equality bounds collisions ($x > 100 \land x < 50$). |
| **D** | Nested conditional conflicts | Mutually exclusive obligations triggered by nested conditions. |
| **E** | Temporal & Workflow deadlocks | Circular prerequisites where step A requires B, B requires C, C requires A. |
| **F** | Conflicting output schemas | JSON-only output coupled with demands for external prose. |
| **G** | Semantic & physical paradoxes | Mutually exclusive definitions (e.g. underwater scuba in a bone-dry desert). |
| **H** | Negation-heavy instructions | Demanding a task while forbidding its necessary mechanism. |
| **I** | Underspecified requirements | Prompts with unfilled bracketed placeholders (`[insert doc]`). |
| **J** | Compatible with misleading wording | Valid prompts discussing external paradoxes (checks False Positive Rate). |
| **K** | Requirements with separate scopes | Valid word counts assigned to distinct sections (checks scope isolation). |
| **L** | 3+ constraint sets | Minimum conflicting sets spanning 3 or more clauses. |
| **M** | Long technical specifications | Real-world specifications with buried incompatibilities. |
| **N** | Revisions & Overriding exceptions | General rules with explicit, valid exceptions. |
| **O** | Quoted instructions as data | Contradictory text contained inside quotation marks to be analyzed, not run. |
| **P** | Compound paradoxes | Combined structural, temporal, and semantic traps. |

---

## 5. Mathematical Formulations of Research Metrics

### A. Four-Class Metrics
- **Macro-F1:**
  $$\text{Macro-F1} = \frac{1}{|C|} \sum_{c \in C} F_1(c)$$
- **Weighted-F1:**
  $$\text{Weighted-F1} = \sum_{c \in C} \frac{N_c}{N} F_1(c)$$

### B. Binary Contradiction Detection
Treating `Fully impossible` and `Partially conflicting` as positives ($y=1$), and `Compatible` as negatives ($y=0$):
- **False Positive Rate (FPR):**
  $$\text{FPR} = \frac{\text{FP}}{\text{FP} + \text{TN}}$$
- **False Negative Rate (FNR):**
  $$\text{FNR} = \frac{\text{FN}}{\text{FN} + \text{TP}}$$

### C. Conflict Localization F1
Measured against ground-truth evidence spans:
$$\text{Precision}_{\text{span}} = \frac{|\mathcal{S}_{\text{pred}} \cap \mathcal{S}_{\text{gold}}|}{|\mathcal{S}_{\text{pred}}|}, \quad \text{Recall}_{\text{span}} = \frac{|\mathcal{S}_{\text{pred}} \cap \mathcal{S}_{\text{gold}}|}{|\mathcal{S}_{\text{gold}}|}$$
$$\text{F1}_{\text{span}} = \frac{2 \cdot \text{Precision}_{\text{span}} \cdot \text{Recall}_{\text{span}}}{\text{Precision}_{\text{span}} + \text{Recall}_{\text{span}}}$$

---

## 6. Failure Taxonomy & Root Cause Diagnosis

Every misclassified case in the held-out benchmark is logged in `results/failure_registry.json` under one of 12 canonical error classes:
1. `Missed numerical contradiction`
2. `Missed scope distinction`
3. `Incorrect negation interpretation`
4. `Temporal reasoning failure`
5. `Semantic ambiguity`
6. `Instruction extraction failure`
7. `Conditional dependency failure`
8. `Long-context information loss`
9. `Incorrect conflict localization`
10. `False positive on compatible instructions`
11. `Unsupported or hallucinated explanation`
12. `Invalid structured output`

---

## 7. Single Source of Truth & Automated Mathematical Verification

To ensure research reproducibility and prevent transcription errors, all metrics are programmatically bound to an immutable Single Source of Truth:
- **Raw Records (JSON):** `results/raw_predictions.json` (1,000 case-level dictionaries containing `case_id`, `gold_label`, `pred_label`, `is_correct`, `latency_ms`, `input_tokens`, `output_tokens`).
- **Raw Records (CSV):** `results/raw_predictions.csv`.

### Mathematical Consistency Proofs
In `evaluation/metrics.py`, strict automated numpy assertions execute on every evaluation run:
1. **Total Support Invariant:** $\sum_{i,j} CM_{i,j} = N = 1000$.
2. **Class Support Invariant:** $\sum_j CM_{i,j} = \text{Support}_i = 250, \quad \forall i \in \{C, P, F, U\}$.
3. **Accuracy Invariant:** $\text{Accuracy} = \frac{\text{Trace}(CM)}{N} = \frac{250 + 188 + 125 + 250}{1000} = \mathbf{0.8130}$.
4. **Precision & Recall Invariants:**
   - $\text{Recall}_i = \frac{CM_{i,i}}{\sum_j CM_{i,j}}$
   - $\text{Precision}_i = \frac{CM_{i,i}}{\sum_k CM_{k,i}}$
5. **Macro-F1 Invariant:** $\text{Macro-F1} = \frac{1}{4} \sum_{i} F_1(i) = \frac{0.8000 + 0.8584 + 0.5721 + 1.0000}{4} = \mathbf{0.8076}$.

---

## 8. Authoritative Held-Out Benchmark Results (1,000 Cases)

### 8.1 Confusion Matrix

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

### 8.2 Per-Class Metrics Table

| Primary Classification | Support | True Positives | Precision | Recall | F1-Score |
|---|---:|---:|---:|---:|---:|
| **Compatible** | 250 | 250 | 0.6667 | 1.0000 | **0.8000** |
| **Partially Conflicting** | 250 | 188 | 1.0000 | 0.7520 | **0.8584** |
| **Fully Impossible** | 250 | 125 | 0.6684 | 0.5000 | **0.5721** |
| **Underspecified** | 250 | 250 | 1.0000 | 1.0000 | **1.0000** |
| **Macro Average** | **1,000** | **813** | **0.8338** | **0.8130** | **0.8076** |

### 8.3 Baseline Comparison Audit

| Baseline | Architecture | Execution Status | Accuracy | Macro-F1 | Mean Latency | Verified Evidence |
|---|---|:---:|---:|---:|---:|---|
| **Baseline A** | Deterministic Rules | **VERIFIED_EXECUTED** | 81.30% | 0.8076 | 0.66 ms | 1,000 cases evaluated offline. Zero external API calls. |
| **Baseline B** | Base LLM Direct (NVIDIA NIM) | **VERIFIED_LIVE_SAMPLE** | *null* | *null* | 7,219.6 ms | Live HTTPS request to `integrate.api.nvidia.com/v1`; full batch withheld. |
| **Baseline C** | Structured Base LLM (NVIDIA NIM) | **VERIFIED_LIVE_SAMPLE** | *null* | *null* | 7,219.6 ms | Schema parsing verified live on sample; full batch withheld. |
| **Baseline D** | Hybrid Rules + LLM | **VERIFIED_LIVE_SAMPLE** | *null* | *null* | 7,219.6 ms | Two-tier override verified live on sample; full batch withheld. |
| **Baseline E** | Fine-Tuned NeMo LoRA Adapter | **NOT EXECUTED** | *null* | *null* | *null* | No model weights exist in `checkpoints/pe11_lora/`. Simulated latencies deleted. |
| **Baseline F** | Hybrid Rules + Fine-Tuned LoRA | **NOT EXECUTED** | *null* | *null* | *null* | Model weights absent. Simulated latencies deleted. |

