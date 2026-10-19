#!/bin/bash
# ContradictPrompt PE-11: Export NeMo LoRA Adapters to TensorRT-LLM Engine for NIM Deployment
set -e

CHECKPOINT_DIR="checkpoints/pe11_lora"
TRT_OUTPUT_DIR="./trt_engines/pe11_consistency_checker"

echo "================================================================="
echo "  ContradictPrompt — TensorRT-LLM Engine Compilation for NIM     "
echo "================================================================="

mkdir -p "$TRT_OUTPUT_DIR"

python3 -m tensorrt_llm.commands.build \
    --checkpoint_dir "$CHECKPOINT_DIR" \
    --output_dir "$TRT_OUTPUT_DIR" \
    --gemm_plugin auto \
    --max_batch_size 64 \
    --max_input_len 4096 \
    --max_output_len 1024 \
    --lora_plugin auto \
    --lora_dir "$CHECKPOINT_DIR" \
    --kv_cache_type paged

echo "[+] TensorRT-LLM engine compiled successfully into $TRT_OUTPUT_DIR"
echo "[+] NIM Container can now mount this directory to serve fine-tuned weights."
