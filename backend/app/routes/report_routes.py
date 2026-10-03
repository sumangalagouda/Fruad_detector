from flask import Blueprint, request
from app.ai.report_generator import InvestigationReportGenerator
from app.models.report import InvestigationReport
from app.extensions import db
from app.services.audit_service import log_audit_event
from app.utils.responses import api_success, api_error
from flask_jwt_extended import jwt_required, get_jwt_identity

report_bp = Blueprint("reports", __name__, url_prefix="/api")


@report_bp.route("/cases/<case_id>/reports", methods=["POST"])
@jwt_required()
def generate_report(case_id):
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    title = data.get("title")
    try:
        report = InvestigationReportGenerator.generate_case_report(case_id=case_id, user_id=user_id, title=title)
        log_audit_event(
            action="GENERATE_REPORT",
            user_id=user_id,
            case_id=case_id,
            details={"report_id": report.report_id, "title": report.title}
        )
        return api_success(data={"report": report.to_dict()}, message="Investigation report generated successfully.", status_code=201)
    except ValueError as ve:
        return api_error(str(ve), code="NOT_FOUND", status_code=404)
    except Exception as e:
        return api_error(f"Failed to generate report: {str(e)}", code="SERVER_ERROR", status_code=500)


@report_bp.route("/cases/<case_id>/reports", methods=["GET"])
@jwt_required()
def list_case_reports(case_id):
    reports = InvestigationReport.query.filter_by(case_id=case_id).order_by(InvestigationReport.generated_at.desc()).all()
    return api_success(data={"reports": [r.to_dict() for r in reports]})


@report_bp.route("/reports/<report_id>", methods=["GET"])
@jwt_required()
def get_report(report_id):
    report = db.session.get(InvestigationReport, report_id)
    if not report:
        return api_error("Report not found.", code="NOT_FOUND", status_code=404)
    return api_success(data={"report": report.to_dict()})
