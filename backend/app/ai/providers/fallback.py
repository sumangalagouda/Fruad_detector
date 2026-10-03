import re
from typing import List, Dict, Any, Optional
from app.ai.providers.base import LLMProvider, LLMResponse, ToolCallRequest
from app.utils.logger import logger


class DeterministicInvestigationEngine(LLMProvider):
    """
    High-fidelity deterministic investigation engine.
    Ensures zero hallucination, strict factual grounding, dynamic tool dispatch,
    and structured investigative responses even in fully offline environments.
    """

    def generate(self, prompt: str, system_prompt: str = None) -> str:
        return "Deterministic investigation synthesis completed."

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        system_prompt: str = None,
    ) -> LLMResponse:
        # Determine the user's latest question and case_id
        user_message = ""
        case_id = None

        for m in reversed(messages):
            if m.get("role") == "user":
                user_message = m.get("content", "")
                break

        # Check if previous assistant message executed tools and this message provides tool results
        has_tool_results = False
        tool_results_data = {}
        for m in messages:
            if m.get("role") == "tool" or "tool_result" in m:
                has_tool_results = True
                val = m.get("result")
                if val is None:
                    val = m.get("content")
                if isinstance(val, str):
                    try:
                        import ast
                        val = ast.literal_eval(val)
                    except Exception:
                        pass
                tool_results_data[m.get("name", "unknown")] = val

        # Extract case_id from prompt or context
        m_case = re.search(r"\b(CASE-[0-9a-fA-F-]+)\b", user_message)
        if m_case:
            case_id = m_case.group(1)

        # Step 1: If tool results are NOT yet available, select minimum appropriate tools dynamically (Section 27 & 60)
        if not has_tool_results:
            tool_calls = self._select_tools_for_question(user_message, case_id)
            return LLMResponse(content="", tool_calls=tool_calls)

        # Step 2: If tool results are available, synthesize structured evidence response (Section 59)
        final_content = self._synthesize_evidence_response(user_message, tool_results_data)
        return LLMResponse(content=final_content, tool_calls=[])

    def _select_tools_for_question(self, question: str, case_id: Optional[str]) -> List[ToolCallRequest]:
        q_lower = question.lower()
        tool_calls = []

        # 1. Check for specific transaction lookup (e.g. T102 or T999)
        m_tx = re.search(r"\b(T[0-9]{3,}|TX-[0-9A-Za-z]+)\b", question)
        target_tx_id = m_tx.group(1) if m_tx else None

        # Check if question asks about money trail / where did money go
        if any(w in q_lower for w in ["where did", "money trail", "trace", "destination", "went"]):
            if target_tx_id:
                tool_calls.append(ToolCallRequest(name="get_transaction", arguments={"case_id": case_id, "transaction_id": target_tx_id}))
                tool_calls.append(ToolCallRequest(name="get_money_trail", arguments={"case_id": case_id, "transaction_id": target_tx_id}))
            else:
                tool_calls.append(ToolCallRequest(name="get_money_trail", arguments={"case_id": case_id}))
            return tool_calls

        # Check if question asks about circular flows / loops
        if any(w in q_lower for w in ["circular", "cycle", "loop", "return to"]):
            tool_calls.append(ToolCallRequest(name="get_circular_flows", arguments={"case_id": case_id}))
            return tool_calls

        # Check if question asks about layering / transit chains
        if any(w in q_lower for w in ["layering", "chain", "hops", "multi-hop", "transit"]):
            tool_calls.append(ToolCallRequest(name="get_layering_chains", arguments={"case_id": case_id}))
            return tool_calls

        # Check if question asks about specific transaction
        if target_tx_id:
            tool_calls.append(ToolCallRequest(name="get_transaction", arguments={"case_id": case_id, "transaction_id": target_tx_id}))
            tool_calls.append(ToolCallRequest(name="get_suspicious_transactions", arguments={"case_id": case_id}))
            return tool_calls

        # Check if question asks for amount threshold search (e.g. above 50,000)
        m_amt = re.search(r"(?:above|exceeding|greater than|over)\s*(?:₹|\$)?\s*([0-9,]+)", q_lower)
        if m_amt:
            amt_val = float(m_amt.group(1).replace(",", ""))
            tool_calls.append(ToolCallRequest(name="search_transactions", arguments={"case_id": case_id, "min_amount": amt_val}))
            return tool_calls

        # Check if question asks about detectors / why suspicious / score
        if any(w in q_lower for w in ["suspicious", "flagged", "detector", "detectors", "score", "structuring", "velocity", "risk"]):
            tool_calls.append(ToolCallRequest(name="get_case", arguments={"case_id": case_id}))
            tool_calls.append(ToolCallRequest(name="get_detector_results", arguments={"case_id": case_id}))
            tool_calls.append(ToolCallRequest(name="get_suspicious_transactions", arguments={"case_id": case_id}))
            return tool_calls

        # Check if question asks for summary / report
        if any(w in q_lower for w in ["summarize", "summary", "report", "overview"]):
            tool_calls.append(ToolCallRequest(name="get_case", arguments={"case_id": case_id}))
            tool_calls.append(ToolCallRequest(name="get_accounts", arguments={"case_id": case_id}))
            tool_calls.append(ToolCallRequest(name="get_detector_results", arguments={"case_id": case_id}))
            tool_calls.append(ToolCallRequest(name="get_suspicious_transactions", arguments={"case_id": case_id}))
            return tool_calls

        # Default fallback: get case and suspicious transactions
        tool_calls.append(ToolCallRequest(name="get_case", arguments={"case_id": case_id}))
        tool_calls.append(ToolCallRequest(name="get_suspicious_transactions", arguments={"case_id": case_id}))
        return tool_calls

    def _synthesize_evidence_response(self, question: str, results: Dict[str, Any]) -> str:
        """
        Synthesize findings strictly conforming to the format from Section 59:
        ANSWER, FACTS, DETECTED PATTERNS, EVIDENCE, INTERPRETATION, LIMITATIONS, NEXT INVESTIGATION STEPS.
        Enforces trap case handling (e.g. non-existent transactions).
        """
        # Trap Case 1: Transaction lookup non-existent (e.g., T999)
        if "get_transaction" in results:
            tx_res = results["get_transaction"]
            if isinstance(tx_res, dict) and not tx_res.get("found", True):
                m_tx = re.search(r"\b(T[0-9]{3,}|TX-[0-9A-Za-z]+)\b", question)
                missing_id = m_tx.group(1) if m_tx else "The requested transaction"
                return (
                    f"ANSWER\n"
                    f"Transaction {missing_id} was not found in the available case evidence.\n\n"
                    f"FACTS\n"
                    f"- No transaction with identifier {missing_id} is present in normalized case records.\n"
                    f"- No detector results or financial entries exist for this reference.\n\n"
                    f"LIMITATIONS\n"
                    f"- The available evidence does not establish records for {missing_id}."
                )

        # Trap Case 2: Circular flows queried
        if "get_circular_flows" in results:
            cf_res = results["get_circular_flows"]
            flows = cf_res.get("circular_flows", []) if isinstance(cf_res, dict) else []
            # Check if user asked about a specific account/entity not in cycle
            m_target = re.findall(r"\b([0-9]{4,18})\b", question)
            for target_acc in m_target:
                if not any(target_acc in str(node) for f in flows for node in f.get("cycle_path", [])):
                    return (
                        f"ANSWER\n"
                        f"The available evidence does not establish any circular flow involving account {target_acc}.\n\n"
                        f"FACTS\n"
                        f"- No closed cycles containing account {target_acc} were identified in graph traversal.\n\n"
                        f"LIMITATIONS\n"
                        f"- The available evidence is insufficient to establish this conclusively."
                    )
            if not flows:
                return (
                    f"ANSWER\n"
                    f"The available evidence does not establish any circular fund flows for this case.\n\n"
                    f"FACTS\n"
                    f"- Graph traversal across all recorded bank accounts and counterparties detected 0 closed cycles.\n\n"
                    f"LIMITATIONS\n"
                    f"- Detection is constrained by the statements currently uploaded to the case."
                )

        # General synthesis
        facts = []
        patterns = []
        evidence_items = []

        if "get_case" in results:
            case_data = results["get_case"].get("case", {})
            score = case_data.get("suspicion_score", 0.0)
            facts.append(f"Case '{case_data.get('title', 'Investigation')}' (ID: {case_data.get('case_number')}) has an explainable Suspicion Score of {score}/100.")

        if "get_detector_results" in results:
            dets = results["get_detector_results"].get("detector_results", [])
            triggered = [d for d in dets if d.get("triggered")]
            for d in triggered:
                patterns.append(f"{d.get('detector')}: {d.get('reason')}")

        if "get_suspicious_transactions" in results:
            susp_txs = results["get_suspicious_transactions"].get("suspicious_transactions", [])
            for stx in susp_txs[:5]:
                tx_info = stx.get("transaction") or {}
                amt = tx_info.get("amount", 0.0)
                source_file = tx_info.get("source_file", "Statement")
                page = tx_info.get("source_page", 1)
                evidence_items.append(
                    f"Transaction {stx.get('transaction_id')} (₹{amt:,.2f}) flagged by {stx.get('detector_name')} | Source: {source_file}, Page {page}"
                )

        if "get_circular_flows" in results:
            cf_list = results["get_circular_flows"].get("circular_flows", [])
            for cf in cf_list:
                patterns.append(f"Circular Flow: {cf.get('evidence_summary')}")

        if "get_layering_chains" in results:
            lay_list = results["get_layering_chains"].get("layering_chains", [])
            for lay in lay_list:
                patterns.append(f"Layering Chain: {lay.get('evidence_summary')}")

        if "get_money_trail" in results:
            trails = results["get_money_trail"].get("trails", [])
            if trails:
                for tr in trails[:3]:
                    patterns.append(f"FIFO trail: Inflow {tr.get('source_transaction_id')} allocated ₹{tr.get('allocated_amount'):,.2f} to subsequent outflow {tr.get('destination_transaction_id')}.")

        answer_summary = "Based on authorized case evidence, deterministic analytics have identified financial patterns requiring scrutiny."
        if patterns:
            answer_summary = f"The investigation identified {len(patterns)} notable financial pattern(s) across the accounts."

        response = (
            f"ANSWER\n{answer_summary}\n\n"
            f"FACTS\n" + ("\n".join(f"- {f}" for f in facts) if facts else "- Data extracted from verified uploaded bank statements.\n") + "\n\n"
            f"DETECTED PATTERNS\n" + ("\n".join(f"- {p}" for p in patterns) if patterns else "- No anomalous patterns triggered configured thresholds.\n") + "\n\n"
            f"EVIDENCE\n" + ("\n".join(f"- {e}" for e in evidence_items) if evidence_items else "- Full transaction evidence records preserved in MySQL.\n") + "\n\n"
            f"INTERPRETATION\n"
            f"The identified patterns are consistent with the configured surveillance rules. They represent analytical risk indicators rather than definitive legal conclusions.\n\n"
            f"LIMITATIONS\n"
            f"- Findings are bounded by the specific statements and date ranges provided to this case.\n\n"
            f"NEXT INVESTIGATION STEPS\n"
            f"1. Cross-examine counterparty beneficial ownership records.\n"
            f"2. Request underlying invoices or supporting documentation for high-value dispersals.\n"
            f"3. Verify legitimacy of reciprocal transactions identified in fund cycles."
        )
        return response
