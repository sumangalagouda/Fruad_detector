import requests
from typing import List, Dict, Any, Optional
from app.ai.providers.base import LLMProvider, LLMResponse, ToolCallRequest
from app.utils.logger import logger


class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022", timeout: int = 45):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.endpoint = "https://api.anthropic.com/v1/messages"

    def generate(self, prompt: str, system_prompt: str = None) -> str:
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is not configured.")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            payload["system"] = system_prompt

        resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=self.timeout)
        if resp.status_code == 200:
            data = resp.json()
            parts = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
            return "".join(parts)
        raise RuntimeError(f"Claude API failed: {resp.text}")

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        system_prompt: str = None,
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is not configured.")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        claude_tools = []
        for t in tools:
            claude_tools.append({
                "name": t.get("name"),
                "description": t.get("description"),
                "input_schema": t.get("inputSchema", {}),
            })

        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": messages,
            "tools": claude_tools,
        }
        if system_prompt:
            payload["system"] = system_prompt

        resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=self.timeout)
        if resp.status_code == 200:
            data = resp.json()
            content_text = ""
            tool_calls = []

            for block in data.get("content", []):
                if block.get("type") == "text":
                    content_text += block.get("text", "")
                elif block.get("type") == "tool_use":
                    tool_calls.append(
                        ToolCallRequest(
                            name=block.get("name"),
                            arguments=block.get("input", {}),
                        )
                    )

            return LLMResponse(content=content_text, tool_calls=tool_calls, raw_response=data)
        raise RuntimeError(f"Claude API tool execution failed: {resp.text}")
