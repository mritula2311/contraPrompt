#!/bin/bash
# Project PE-11: Export Tuned LoRA Adapters to TensorRT-LLM Engine

CHECKPOINT_DIR="checkpoints/pe11_lora"
TRT_OUTPUT_DIR="./trt_engines/pe11_consistency_checker"

echo "=== Converting NeMo/HuggingFace LoRA checkpoint to TensorRT-LLM ==="
python3 -m tensorrt_llm.commands.build \
    --checkpoint_dir $CHECKPOINT_DIR \
    --output_dir $TRT_OUTPUT_DIR \
    --gemm_plugin auto \
    --max_batch_size 64 \
    --max_input_len 2048 \
    --max_output_len 512 \
    --lora_plugin auto \
    --lora_dir $CHECKPOINT_DIR/lora_weights

echo "TensorRT-LLM engine built successfully in $TRT_OUTPUT_DIR"
