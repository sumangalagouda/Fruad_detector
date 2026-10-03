from flask import Blueprint, request
from app.models.audit import AuditLog
from app.utils.responses import api_success
from flask_jwt_extended import jwt_required

audit_bp = Blueprint("audit", __name__, url_prefix="/api")


@audit_bp.route("/cases/<case_id>/audit-logs", methods=["GET"])
@jwt_required()
def get_case_audit_logs(case_id):
    limit = int(request.args.get("limit", 100))
    logs = AuditLog.query.filter_by(case_id=case_id).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return api_success(data={"audit_logs": [l.to_dict() for l in logs]})


@audit_bp.route("/audit-logs", methods=["GET"])
@jwt_required()
def get_all_audit_logs():
    limit = int(request.args.get("limit", 100))
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return api_success(data={"audit_logs": [l.to_dict() for l in logs]})
