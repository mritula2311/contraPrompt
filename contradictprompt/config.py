from dataclasses import dataclass, field
import os
from dotenv import load_dotenv

@dataclass(frozen=True)
class Config:
    provider: str = 'disabled'
    base_url: str = 'http://localhost:11434'
    model: str = ''
    api_key: str = field(default='', repr=False)
    allow_paid: bool = False
    temperature: float = 0.0
    max_tokens: int = 1200
    timeout: float = 60

    @classmethod
    def from_env(cls):
        load_dotenv()
        prov = os.getenv('CP_PROVIDER', '').strip().lower()
        nv_key = os.getenv('NVIDIA_API_KEY', '').strip()
        cp_key = os.getenv('CP_API_KEY', '').strip()
        api_key = cp_key or nv_key

        if not prov:
            if nv_key:
                prov = 'nvidia_nim'
            else:
                prov = 'disabled'

        if prov in ('nvidia', 'nvidia_nim'):
            base_url = os.getenv('CP_BASE_URL', 'https://integrate.api.nvidia.com/v1').rstrip('/')
            model = os.getenv('CP_MODEL', 'nvidia/nemotron-3.5-super-vl-120b-a12b')
            allow_paid = os.getenv('CP_ALLOW_PAID', 'true').lower() == 'true'
        else:
            base_url = os.getenv('CP_BASE_URL', 'http://localhost:11434').rstrip('/')
            model = os.getenv('CP_MODEL', '')
            allow_paid = os.getenv('CP_ALLOW_PAID', 'false').lower() == 'true'

        return cls(
            provider=prov,
            base_url=base_url,
            model=model,
            api_key=api_key,
            allow_paid=allow_paid,
            temperature=float(os.getenv('CP_TEMPERATURE', '0.2')),
            max_tokens=int(os.getenv('CP_MAX_TOKENS', '2048')),
            timeout=float(os.getenv('CP_TIMEOUT', '60'))
        )
