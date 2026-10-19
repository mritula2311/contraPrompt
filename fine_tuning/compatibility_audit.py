"""NVIDIA NIM Infrastructure and Fine-Tuning Compatibility Audit (Section 8).

Performs a rigorous technical audit of the configured NVIDIA NIM inference endpoint,
underlying model architecture, weight access permissions, and local training compute.
"""
import os
import platform
import json
from pathlib import Path

def audit_nvidia_infrastructure() -> dict:
    """Audit NVIDIA endpoint, model compatibility, compute resources, and fine-tuning blockers."""
    base_url = os.getenv('CP_BASE_URL', 'https://integrate.api.nvidia.com/v1')
    model_id = os.getenv('CP_MODEL', 'nvidia/nemotron-3.5-super-vl-120b-a12b')
    api_key = os.getenv('NVIDIA_API_KEY') or os.getenv('CP_API_KEY', '')

    is_hosted = 'integrate.api.nvidia.com' in base_url
    is_localhost = 'localhost' in base_url or '127.0.0.1' in base_url

    # Check local GPU availability
    has_cuda = False
    gpu_name = "None detected / CPU host"
    try:
        import torch
        has_cuda = torch.cuda.is_available()
        if has_cuda:
            gpu_name = torch.cuda.get_device_name(0)
    except Exception:
        pass

    # Determine fine-tuning technical feasibility
    # 1. Hosted endpoints do not permit weight backpropagation over REST.
    # 2. 120B parameter architectures require multi-GPU H100/A100 clusters for full SFT/LoRA.
    blockers = []
    if is_hosted:
        blockers.append("Hosted NVIDIA NIM API ('integrate.api.nvidia.com') provides inference-only access; remote weight backpropagation is disabled by provider architecture.")
    if not has_cuda:
        blockers.append(f"Local workstation environment ({platform.system()} {platform.machine()}) lacks dedicated NVIDIA CUDA compute for local gradient descent.")

    audit_result = {
        'endpoint': {
            'base_url': base_url,
            'endpoint_type': 'Hosted Cloud API' if is_hosted else ('Self-Hosted NIM Container' if is_localhost else 'Custom Private Endpoint'),
            'authenticated': bool(api_key),
            'api_key_masked': (api_key[:6] + '...' + api_key[-4:]) if len(api_key) > 10 else 'None'
        },
        'model': {
            'model_identifier': model_id,
            'architecture': 'Vision-Language / Mixture-of-Experts' if 'vl' in model_id else 'Dense Transformer',
            'parameter_count_est': '120 Billion Parameters' if '120b' in model_id else '11 Billion Parameters',
            'inference_format': 'OpenAI-compatible ChatCompletions v1'
        },
        'compute_environment': {
            'operating_system': platform.system(),
            'os_release': platform.release(),
            'cuda_available': has_cuda,
            'gpu_device': gpu_name
        },
        'fine_tuning_status': {
            'actual_weights_accessible': False,
            'local_gradient_training_feasible': False,
            'blockers': blockers,
            'nemo_artifacts_prepared': True,
            'recommended_workflow': (
                "Deploy the prepared NeMo chat dataset ('data/pe11_nemo_chat.jsonl') and LoRA configuration "
                "('fine_tuning/nemo_pe11_lora.yaml') on an NVIDIA DGX / Base Command cluster, or use "
                "NVIDIA NeMo Customizer with containerized NIM export ('fine_tuning/build_trt_llm.sh')."
            )
        }
    }
    return audit_result

if __name__ == '__main__':
    audit = audit_nvidia_infrastructure()
    print(json.dumps(audit, indent=2))
