from app.extensions import db
from app.models.audit import AuditLog
from app.utils.logger import logger
from flask import request


def log_audit_event(
    action: str,
    user_id: str = None,
    case_id: str = None,
    tool: str = None,
    tool_arguments: dict = None,
    result_status: str = "SUCCESS",
    details: dict = None,
):
    """
    Persist an audit log entry.
    Strictly sanitizes arguments to ensure secrets/passwords are never logged.
    """
    try:
        sanitized_args = None
        if tool_arguments:
            sanitized_args = {}
            for k, v in tool_arguments.items():
                if any(sec in k.lower() for sec in ["pass", "secret", "token", "key", "auth"]):
                    sanitized_args[k] = "[REDACTED]"
                else:
                    sanitized_args[k] = v

        ip = None
        if request:
            try:
                ip = request.remote_addr
            except Exception:
                pass

        audit_entry = AuditLog(
            user_id=user_id,
            case_id=case_id,
            action=action,
            tool=tool,
            tool_arguments=sanitized_args,
            result_status=result_status,
            ip_address=ip,
            details=details,
        )
        db.session.add(audit_entry)
        db.session.commit()
    except Exception as e:
        logger.error(f"Failed to record audit event: {e}")
        db.session.rollback()
