# User Guide & Operational Walkthrough

## ContradictPrompt: A Hybrid Rule-Based and LLM-Driven Framework for Detecting and Resolving Conflicting User Instructions

**Authors:** Mritula S — E0223031 | Varsha Venkatesan — E0223018  
**Department:** Department of Cyber Security and Internet of Things  
**Project Reference:** Research Project 56 (PE-11), Project Compendium, PDF Page 64  
**Release:** Version 12 Production Release  
**Verified Test Suite:** 247 passing automated tests (100% pass rate)

---

## 1. Quick Start & Application Launch

### 1.1 Environment Setup
1. Open a terminal (PowerShell on Windows, bash/zsh on macOS/Linux) inside the `ContradictPrompt` directory:
   ```bash
   cd ContradictPrompt
   ```
2. Verify that Python 3.11 or newer is installed:
   ```bash
   python --version
   ```
3. Create and activate a dedicated virtual environment:
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .venv\Scripts\Activate.ps1
   # macOS / Linux:
   # source .venv/bin/activate
   ```
4. Install the verified project dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```

### 1.2 Starting the Application
ContradictPrompt provides two interfaces:

#### Primary Production Interface (Flask REST API + Glassmorphic SPA)
Launch the primary server:
```bash
python server.py
```
Open **`http://localhost:5000`** in any web browser.  
The interface features a dark-mode, responsive single-page application with vector iconography, animated badges, interactive constraint graph visualization, and real-time NVIDIA NIM diagnostics.

#### Backward-Compatible Legacy Interface (Streamlit)
To launch the original research prototype interface:
```bash
python -m streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.

---

## 2. Walkthrough: Prompt Analysis & Contradiction Detection

1. **Navigate to Prompt Analyzer:** Select **Prompt Analyzer** from the top navigation bar.
2. **Enter a Test Prompt:** Enter or choose one of the pre-loaded benchmark prompts from the dropdown:
   - **Numerical Impossibility:**  
     `"Write exactly 100 words, but ensure the response has fewer than 80 words."`  
     *Result:* **Fully impossible**. The system highlights the conflicting spans (`"exactly 100 words"` vs `"fewer than 80 words"`), displays the empty interval intersection $[100, 100] \cap [0, 79] = \emptyset$, and renders the directed conflict graph.
   - **Compatible Section Scopes:**  
     `"Write a 100-word introduction and a 50-word conclusion."`  
     *Result:* **Compatible**. The system scopes `introduction` and `conclusion` separately, confirming no cross-section interference.
   - **Underspecified Requirement:**  
     `"Prepare the report using the required format."`  
     *Result:* **Underspecified**. The system detects that the format specification is missing and prompts: `"Please specify the required format or template guidelines."`
   - **Soft Preference Tension:**  
     `"Provide a very detailed explanation while keeping it extremely brief."`  
     *Result:* **Partially conflicting**. Highlights the stylistic tension between brevity and exhaustive depth.
3. **Inspect the Output:**
   - **Classification Badge:** Color-coded status badge with primary classification and secondary multi-label flags.
   - **Extracted Instruction Table:** Lists ID, original text, scope, kind, extracted bounds, and polarity.
   - **Constraint Graph:** Visualizes nodes (instructions) and edges (conflicts/dependencies).

---

## 3. Walkthrough: Prompt Repair & Revalidation Workflow

1. **Trigger Repair:** When a prompt is classified as `Fully impossible` or `Partially conflicting`, navigate to the **Prompt Repair** section.
2. **Review Repair Alternatives:** The repair engine presents non-identity delta candidates:
   - For numerical conflicts: Aligns the upper and lower bounds to a mutually satisfiable interval.
   - For temporal conflicts: Re-orders prerequisite phases or aligns dates.
   - For formatting conflicts: Resolves conflicting schema demands (e.g., Markdown prose vs strict JSON).
3. **Load into Editor:** Click **Load into Editor** on the preferred candidate.
4. **Human Approval Gate:**
   - Review or further modify the proposed prompt in the interactive editor.
   - Check the mandatory checkbox: `[x] I approve this exact edited prompt for revalidation`.
   - Click **Approve and Revalidate**.
5. **Revalidation:** The system immediately re-analyzes the approved prompt. Generation is strictly unlocked only when the revalidated prompt achieves a `Compatible` assessment.

---

## 4. Walkthrough: NVIDIA NIM Cloud Inference Integration

ContradictPrompt features first-class integration with NVIDIA NIM (OpenAI-compatible cloud inference API):
- **Default Cloud Endpoint:** `https://integrate.api.nvidia.com/v1`
- **Default Cloud Model:** `nvidia/nemotron-3.5-super-vl-120b-a12b`
- **Fallback Cloud Model:** `meta/llama-3.2-11b-vision-instruct`

### 4.1 Configuring NVIDIA NIM
Create or edit your `.env` file in the project root:
```dotenv
CP_PROVIDER=nvidia
NVIDIA_API_KEY=your_nvidia_api_key_here
CP_MODEL=nvidia/nemotron-3.5-super-vl-120b-a12b
CP_BASE_URL=https://integrate.api.nvidia.com/v1
```

### 4.2 Diagnostic & Operational Endpoints
- **Check Status:**
  ```bash
  curl http://localhost:5000/api/llm/status
  ```
  Returns provider health, active model ID, temperature, and masked API key.
- **Live Test Ping:**
  ```bash
  curl -X POST http://localhost:5000/api/llm/test
  ```
  Sends a lightweight verification request to NVIDIA NIM, returning actual measured latency in milliseconds and token counts.
- **Generate Response:**
  Once a repaired prompt is revalidated and approved, use the **Response Generator** section to execute the prompt against NVIDIA NIM and inspect post-generation instruction compliance.

---

## 5. Walkthrough: Research Evaluation & Benchmarks

Navigate to the **Research Evaluation** section or use the command line:

### 5.1 Reproducing the 1,000-Prompt Held-Out Benchmark
Execute the complete benchmark runner:
```bash
python -m scripts.run_advanced_research_eval
```
This script:
1. Generates a balanced 1,000-prompt held-out benchmark across 16 adversarial challenge groups and 5 complexity levels (250 cases per class).
2. Evaluates the detector across all 1,000 cases.
3. Automatically serializes the **Single Source of Truth** records:
   - [`results/raw_predictions.json`](file:///d:/ContradictPrompt/ContradictPrompt/results/raw_predictions.json)
   - [`results/raw_predictions.csv`](file:///d:/ContradictPrompt/ContradictPrompt/results/raw_predictions.csv)
4. Asserts 100% mathematical consistency between the confusion matrix and classification metrics.
5. Emits the verified research evaluation report ([`results/adversarial_evaluation_results.json`](file:///d:/ContradictPrompt/ContradictPrompt/results/adversarial_evaluation_results.json)):
   - **Overall Accuracy:** **81.30%** (813 / 1,000)
   - **Four-Class Macro-F1:** **0.8076**
   - **Binary Contradiction F1:** **0.8571**

### 5.2 Downloading Raw Prediction Records
You can download the raw prediction records directly via HTTP:
```bash
# JSON raw records
curl http://localhost:5000/api/evaluation/raw

# CSV export
curl http://localhost:5000/api/evaluation/raw/csv -o raw_predictions.csv
```

---

## 6. Running Automated Tests

To execute the entire automated regression and unit test suite:
```bash
# Full test suite (247 tests, 100% pass rate):
python -m pytest -v

# Run v12 core regression suite (all 12 P0-P5 tests):
python -m pytest tests/test_v12_regression.py -v

# Run audit and satisfaction evaluation tests:
python -m pytest tests/test_audit_and_satisfaction.py -v

# Run strict Pydantic v2 schema contract tests:
python -m pytest tests/test_schema_contracts.py -v

# Run Section 10 cybersecurity and mandatory logical tests:
python -m pytest tests/test_cybersecurity_regression.py -v

# Run automated mathematical consistency tests:
python -m pytest tests/test_adversarial_levels.py -k test_evaluation_metrics_mathematical_consistency -v
```

---

## 7. Troubleshooting & FAQs

- **Q: Why does the system say "LLM Offline / Rules Mode"?**  
  *A:* If `NVIDIA_API_KEY` is not set or network access is unavailable, the application gracefully operates in offline deterministic rules mode. This ensures full functionality without requiring an external API key.
- **Q: What does "Extra inputs are not permitted" mean?**  
  *A:* This error occurred in earlier versions when `constraint_graph` was sent to a Pydantic model with `extra='forbid'`. In Release 2.0.0, formal `GraphNode`, `GraphEdge`, and `ConstraintGraphData` models are defined and fully validated.
- **Q: Can the prompt repair engine discard my instructions?**  
  *A:* No. The repair engine only generates targeted delta patches for conflicting spans and guarantees non-identity replacements. All edits require explicit user approval before revalidation.
