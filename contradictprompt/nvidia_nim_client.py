"""Project PE-11: Production NVIDIA NIM Client Wrapper
=====================================================
Handles dynamic streaming and batch requests via NVIDIA NIM microservices
and NVIDIA AI Foundation Cloud endpoints with resilient fallback.
"""

import os
import time
import requests
from typing import Generator, Any
from pydantic import BaseModel, Field


class NIMUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0


class NIMResponse(BaseModel):
    content: str
    reasoning: str | None = None
    model: str
    usage: NIMUsage
    success: bool = True


class NvidiaNIMClient:
    """Production client for NVIDIA NIM and AI Foundation Endpoints."""

    DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"
    DEFAULT_MODEL = "nvidia/nemotron-3.5-super-vl-120b-a12b"
    FALLBACK_MODEL = "meta/llama-3.2-11b-vision-instruct"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        timeout: float = 30.0
    ):
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY") or os.getenv("NVAPI_KEY") or "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"
        self.base_url = (base_url or os.getenv("NIM_BASE_URL") or self.DEFAULT_BASE_URL).rstrip("/")
        self.model = model or os.getenv("NIM_MODEL") or self.DEFAULT_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        json_mode: bool = False,
        stream: bool = False
    ) -> NIMResponse:
        """Execute chat completion against NVIDIA NIM."""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": stream
        }

        # Handle reasoning model settings
        if "nemotron" in self.model:
            payload["chat_template_kwargs"] = {"enable_thinking": False}

        if json_mode and "nemotron" not in self.model:
            payload["response_format"] = {"type": "json_object"}

        start_time = time.perf_counter()
        try:
            resp = requests.post(
                url,
                json=payload,
                headers=self._headers(),
                timeout=self.timeout
            )
            resp.raise_for_status()
            data = resp.json()

            choice = data["choices"][0]
            msg = choice.get("message", {})
            content = msg.get("content") or ""
            reasoning = msg.get("reasoning_content")

            # Fallback for models outputting to reasoning_content
            if not content and reasoning:
                content = reasoning

            usage_raw = data.get("usage", {})
            latency = (time.perf_counter() - start_time) * 1000

            usage = NIMUsage(
                prompt_tokens=usage_raw.get("prompt_tokens", 0),
                completion_tokens=usage_raw.get("completion_tokens", 0),
                total_tokens=usage_raw.get("total_tokens", 0),
                latency_ms=round(latency, 2)
            )

            return NIMResponse(
                content=content.strip(),
                reasoning=reasoning,
                model=data.get("model", self.model),
                usage=usage,
                success=True
            )

        except Exception as exc:
            # Automatic fallback to secondary high-availability model if primary fails
            if self.model != self.FALLBACK_MODEL:
                print(f"[NIM Fallback] Switching from {self.model} to {self.FALLBACK_MODEL} due to: {exc}")
                original_model = self.model
                self.model = self.FALLBACK_MODEL
                try:
                    res = self.chat_completion(messages, json_mode, stream)
                    self.model = original_model
                    return res
                except Exception as inner_exc:
                    self.model = original_model
                    raise RuntimeError(f"NVIDIA NIM failed on both primary and fallback models: {inner_exc}") from exc
            raise RuntimeError(f"NVIDIA NIM API Error: {exc}") from exc

    def stream_completion(
        self,
        messages: list[dict[str, str]]
    ) -> Generator[str, None, None]:
        """Stream chunks from NVIDIA NIM."""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True
        }
        if "nemotron" in self.model:
            payload["chat_template_kwargs"] = {"enable_thinking": False}

        resp = requests.post(url, json=payload, headers=self._headers(), stream=True, timeout=self.timeout)
        resp.raise_for_status()

        for line in resp.iter_lines():
            if line:
                line_str = line.decode("utf-8")
                if line_str.startswith("data: ") and line_str != "data: [DONE]":
                    try:
                        chunk_json = json.loads(line_str[6:])
                        delta = chunk_json["choices"][0].get("delta", {})
                        chunk_text = delta.get("content") or delta.get("reasoning_content") or ""
                        if chunk_text:
                            yield chunk_text
                    except json.JSONDecodeError:
                        continue
