import time
import re
from typing import Dict, Any, List, Optional
from flask import current_app
from app.ai.providers.base import LLMProvider, ToolCallRequest
from app.ai.providers.ollama import OllamaProvider
from app.ai.providers.claude import ClaudeProvider
from app.ai.providers.fallback import DeterministicInvestigationEngine
from app.ai.prompt import SYSTEM_INVESTIGATION_PROMPT
from app.ai.memory import InvestigationMemory
from app.mcp.registry import mcp_registry
import app.mcp.tools  # Register all MCP tools
from app.services.audit_service import log_audit_event
from app.utils.logger import logger


class InvestigationAgent:
    def __init__(self, provider_type: Optional[str] = None):
        self.provider = self._init_provider(provider_type)

    def _init_provider(self, provider_type: Optional[str] = None) -> LLMProvider:
        cfg = current_app.config if current_app else {}
        selected = (provider_type or cfg.get("LLM_PROVIDER", "ollama")).lower()

        if selected == "claude" and cfg.get("ANTHROPIC_API_KEY"):
            return ClaudeProvider(api_key=cfg.get("ANTHROPIC_API_KEY"), model=cfg.get("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"))
        elif selected == "ollama":
            ollama = OllamaProvider(
                base_url=cfg.get("OLLAMA_BASE_URL", "http://localhost:11434"),
                model=cfg.get("OLLAMA_MODEL", "llama3:8b"),
            )
            if ollama.check_health():
                return ollama
            logger.info("Ollama is not responding; defaulting to local DeterministicInvestigationEngine.")
            return DeterministicInvestigationEngine()

        return DeterministicInvestigationEngine()

    def run_investigation(
        self,
        case_id: str,
        user_id: str,
        question: str,
        investigation_id: Optional[str] = None,
        max_tool_iterations: int = 4,
    ) -> Dict[str, Any]:
        """
        Execute full autonomous agent reasoning loop:
        1. Context retrieval & memory lookup
        2. Dynamic tool selection via MCP registry
        3. Multi-turn tool execution & evidence accumulation
        4. Synthesize grounded answer
        5. Persist interaction & audit trail
        """
        # Retrieve or create session
        session = InvestigationMemory.get_or_create_session(case_id, user_id, investigation_id)
        chat_history = InvestigationMemory.get_chat_history(session.investigation_id, limit=6)

        mcp_tools = [t.to_mcp_format() for t in mcp_registry.list_tools()]

        # Prepare messages
        messages = list(chat_history)
        # Inject case context into user question if not present
        full_query = f"Case ID: {case_id}\nInvestigator Question: {question}"
        messages.append({"role": "user", "content": full_query})

        tool_execution_records = []
        final_answer = ""

        # Agent Reasoning Loop
        iteration = 0
        while iteration < max_tool_iterations:
            iteration += 1
            try:
                llm_response = self.provider.generate_with_tools(
                    messages=messages,
                    tools=mcp_tools,
                    system_prompt=SYSTEM_INVESTIGATION_PROMPT,
                )
            except Exception as e:
                logger.warning(f"Primary provider generation error: {e}. Switching to deterministic engine.")
                fallback = DeterministicInvestigationEngine()
                llm_response = fallback.generate_with_tools(
                    messages=messages,
                    tools=mcp_tools,
                    system_prompt=SYSTEM_INVESTIGATION_PROMPT,
                )

            # If the model requested tool calls, execute them
            if llm_response.tool_calls:
                for tc in llm_response.tool_calls:
                    # Enforce case_id parameter to guarantee case-level scoping
                    args = dict(tc.arguments or {})
                    args["case_id"] = case_id

                    t_start = time.time()
                    try:
                        tool_result = mcp_registry.execute(tc.name, args)
                        duration = int((time.time() - t_start) * 1000)
                        tool_status = "SUCCESS"
                    except Exception as t_err:
                        tool_result = {"error": str(t_err)}
                        duration = int((time.time() - t_start) * 1000)
                        tool_status = "ERROR"

                    tool_execution_records.append({
                        "tool_name": tc.name,
                        "arguments": args,
                        "result": tool_result,
                        "status": tool_status,
                        "duration_ms": duration,
                    })

                    # Append tool result into context
                    messages.append({
                        "role": "tool",
                        "name": tc.name,
                        "content": str(tool_result),
                        "result": tool_result,
                    })
            else:
                # No more tools needed, model produced final response
                final_answer = llm_response.content
                break

        if not final_answer:
            # Fallback synthesis if max iterations reached
            fallback = DeterministicInvestigationEngine()
            final_res = fallback.generate_with_tools(messages=messages, tools=mcp_tools)
            final_answer = final_res.content

        # Parse structured sections
        parsed_sections = self._parse_structured_response(final_answer)

        # Persist interaction into investigation memory
        msg = InvestigationMemory.save_interaction(
            investigation_id=session.investigation_id,
            user_question=question,
            response_text=final_answer,
            tool_records=tool_execution_records,
            parsed_sections=parsed_sections,
        )

        log_audit_event(
            action="AI_INVESTIGATION_QUERY",
            user_id=user_id,
            case_id=case_id,
            details={"investigation_id": session.investigation_id, "question": question, "tools_count": len(tool_execution_records)},
        )

        return {
            "investigation_id": session.investigation_id,
            "message_id": msg.message_id,
            "question": question,
            "answer": final_answer,
            "parsed_sections": parsed_sections,
            "tool_calls": tool_execution_records,
        }

    def _parse_structured_response(self, text: str) -> Dict[str, Any]:
        """Parse structured sections: ANSWER, FACTS, DETECTED PATTERNS, EVIDENCE, INTERPRETATION, LIMITATIONS, NEXT STEPS."""
        sections = {
            "answer": "",
            "facts": [],
            "detected_patterns": [],
            "evidence": [],
            "interpretation": [],
            "limitations": [],
            "next_steps": [],
        }

        current_key = "answer"
        for line in text.splitlines():
            line_str = line.strip()
            upper_line = line_str.upper()

            if upper_line.startswith("ANSWER"):
                current_key = "answer"
                continue
            elif upper_line.startswith("FACTS"):
                current_key = "facts"
                continue
            elif upper_line.startswith("DETECTED PATTERNS"):
                current_key = "detected_patterns"
                continue
            elif upper_line.startswith("EVIDENCE"):
                current_key = "evidence"
                continue
            elif upper_line.startswith("INTERPRETATION"):
                current_key = "interpretation"
                continue
            elif upper_line.startswith("LIMITATIONS"):
                current_key = "limitations"
                continue
            elif upper_line.startswith("NEXT INVESTIGATION STEPS") or upper_line.startswith("NEXT STEPS"):
                current_key = "next_steps"
                continue

            if not line_str:
                continue

            if current_key == "answer":
                sections["answer"] += (line_str + " ")
            else:
                clean_item = re.sub(r"^[-*•\d.]+\s*", "", line_str)
                if clean_item:
                    sections[current_key].append(clean_item)

        sections["answer"] = sections["answer"].strip()
        return sections
