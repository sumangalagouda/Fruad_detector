import requests
import json
from typing import List, Dict, Any, Optional
from app.ai.providers.base import LLMProvider, LLMResponse, ToolCallRequest
from app.utils.logger import logger


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3:8b", timeout: int = 45):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def check_health(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return resp.status_code == 200
        except Exception:
            return False

    def generate(self, prompt: str, system_prompt: str = None) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            if resp.status_code == 200:
                return resp.json().get("response", "")
            logger.warning(f"Ollama returned HTTP {resp.status_code}: {resp.text}")
            raise RuntimeError(f"Ollama generation failed with status {resp.status_code}")
        except Exception as e:
            logger.warning(f"Ollama connection error: {e}")
            raise e

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        system_prompt: str = None,
    ) -> LLMResponse:
        url = f"{self.base_url}/api/chat"

        # Format messages for Ollama chat endpoint
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        for m in messages:
            formatted_messages.append({
                "role": m.get("role", "user"),
                "content": m.get("content", ""),
            })

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "stream": False,
        }

        # Ollama supports tools parameter in modern versions
        if tools:
            payload["tools"] = tools

        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                msg = data.get("message", {})
                content = msg.get("content", "")
                tool_calls = []

                if "tool_calls" in msg and msg["tool_calls"]:
                    for tc in msg["tool_calls"]:
                        fn = tc.get("function", {})
                        tool_calls.append(
                            ToolCallRequest(
                                name=fn.get("name"),
                                arguments=fn.get("arguments", {}),
                            )
                        )

                return LLMResponse(content=content, tool_calls=tool_calls, raw_response=data)
            else:
                raise RuntimeError(f"Ollama chat error: {resp.text}")
        except Exception as e:
            logger.warning(f"Ollama error: {e}")
            raise e
