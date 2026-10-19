# ContradictPrompt — NVIDIA NIM Setup & NeMo Customization Guide

This document describes how to configure, test, and deploy NVIDIA technologies in ContradictPrompt, including NVIDIA NIM Cloud Inference, local TensorRT-LLM engines, and NVIDIA NeMo Supervised Fine-Tuning (SFT / LoRA).

---

## 1. NVIDIA NIM Cloud Inference Setup

ContradictPrompt natively integrates with NVIDIA NIM (Inference Microservices) hosted at `https://integrate.api.nvidia.com/v1`.

### A. Environment Configuration
Create or edit your `.env` file in the project root:

```dotenv
CP_PROVIDER=nvidia_nim
CP_BASE_URL=https://integrate.api.nvidia.com/v1
CP_MODEL=nvidia/nemotron-3.5-super-vl-120b-a12b
NVIDIA_API_KEY=your_nvidia_api_key_here
CP_ALLOW_PAID=true
```

### B. Supported NVIDIA NIM Models
- `nvidia/nemotron-3.5-super-vl-120b-a12b` (Default Primary Model)
- `meta/llama-3.2-11b-vision-instruct` (High-Speed Fallback)
- `mistralai/mistral-large-2-instruct`

### C. Live Endpoint Diagnostics
You can ping and verify the active NVIDIA NIM connection via the REST API or UI:

```bash
# Ping NVIDIA NIM health
curl http://localhost:5000/api/llm/status

# Execute a live test ping
curl -X POST http://localhost:5000/api/llm/test -H "Content-Type: application/json"
```

### D. Generation & Satisfaction Verification with NIM
When a prompt is repaired and approved, generation can be executed directly via NVIDIA NIM:
- Automatically formats user requests with multi-role message arrays (`system`, `user`).
- Incorporates declared scope instructions (e.g., bullet limits across entire response).
- Evaluates the generated output against deterministic satisfaction checks (AST syntax validation, $O(1)$ and $O(\log n)$ complexities, sorted input acknowledgement).

---

## 2. NVIDIA NeMo Parameter-Efficient Fine-Tuning (LoRA)

ContradictPrompt provides a complete NeMo customization pipeline to adapt foundation models specifically for instruction contradiction detection.

### A. Dataset Synthesis
Generate 3,000 training, 400 validation, and 1,000 held-out evaluation examples formatted for NeMo:

```bash
python -m fine_tuning.prepare_nemo_data
```

This creates:
- `data/nemo_train_3000.jsonl`
- `data/nemo_val_400.jsonl`
- `data/nemo_test_1000.jsonl`

### B. NeMo Training Launch
On an NVIDIA DGX / CUDA-enabled GPU host with the NeMo Framework container:

```bash
python -m fine_tuning.train_nemo_lora
```

The configuration is specified in `fine_tuning/nemo_pe11_lora.yaml`:
- **LoRA Rank ($r$):** 16
- **Scaling Factor ($\alpha$):** 32
- **Target Modules:** `q_proj`, `k_proj`, `v_proj`, `out_proj`
- **Precision:** BF16
- **Optimizer:** Fused Adam ($lr = 10^{-4}$)

---

## 3. Compiling to TensorRT-LLM Engine

To achieve sub-millisecond inference speeds with your fine-tuned LoRA weights:

```bash
chmod +x fine_tuning/build_trt_llm.sh
./fine_tuning/build_trt_llm.sh
```

This compiles the adapter into `trt_engines/pe11_consistency_checker`.

---

## 4. Deploying Self-Hosted NIM Container

Launch the compiled model via Docker Compose:

```bash
docker compose -f docker-compose.nim.yml up -d
```

Update your `.env` to route inference locally:

```dotenv
CP_PROVIDER=openai_compatible
CP_BASE_URL=http://localhost:8000/v1
CP_MODEL=pe11-contradictprompt-lora
```
