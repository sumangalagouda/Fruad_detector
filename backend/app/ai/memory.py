import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.extensions import db
from app.models.investigation import Investigation, InvestigationMessage, InvestigationToolCall


class InvestigationMemory:
    @staticmethod
    def get_or_create_session(case_id: str, user_id: str, investigation_id: Optional[str] = None) -> Investigation:
        if investigation_id:
            inv = Investigation.query.filter_by(investigation_id=investigation_id, case_id=case_id).first()
            if inv:
                return inv

        # Create new session
        inv = Investigation(
            case_id=case_id,
            user_id=user_id,
            title=f"Session {datetime.now(timezone.utc).strftime('%b %d, %H:%M')}",
            status="ACTIVE",
        )
        db.session.add(inv)
        db.session.commit()
        return inv

    @staticmethod
    def get_chat_history(investigation_id: str, limit: int = 20) -> List[Dict[str, str]]:
        """Retrieve chronological chat history for LLM context."""
        msgs = InvestigationMessage.query.filter_by(investigation_id=investigation_id).order_by(
            InvestigationMessage.created_at.asc()
        ).limit(limit).all()

        history = []
        for m in msgs:
            history.append({"role": m.sender, "content": m.response_text or m.user_question})
        return history

    @staticmethod
    def save_interaction(
        investigation_id: str,
        user_question: str,
        response_text: str,
        tool_records: List[Dict[str, Any]],
        parsed_sections: Dict[str, Any] = None,
    ) -> InvestigationMessage:
        sections = parsed_sections or {}

        # Save assistant message record
        msg = InvestigationMessage(
            investigation_id=investigation_id,
            sender="assistant",
            user_question=user_question,
            response_text=response_text,
            facts=sections.get("facts", []),
            detected_patterns=sections.get("detected_patterns", []),
            evidence_items=sections.get("evidence", []),
            interpretations=sections.get("interpretation", []),
            limitations=sections.get("limitations", []),
            next_steps=sections.get("next_steps", []),
        )
        db.session.add(msg)
        db.session.flush()

        # Save tool calls
        for tr in tool_records:
            tc_model = InvestigationToolCall(
                investigation_id=investigation_id,
                message_id=msg.message_id,
                tool_name=tr.get("tool_name"),
                tool_arguments=tr.get("arguments"),
                tool_results=tr.get("result"),
                status=tr.get("status", "SUCCESS"),
                duration_ms=tr.get("duration_ms", 0),
            )
            db.session.add(tc_model)

        db.session.commit()
        return msg
