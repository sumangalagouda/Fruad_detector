from flask import Blueprint, request
from app.detectors.runner import DetectorRunner
from app.models.detector import DetectorResult, SuspiciousTransaction
from app.services.audit_service import log_audit_event
from app.utils.responses import api_success, api_error
from flask_jwt_extended import jwt_required, get_jwt_identity

detector_bp = Blueprint("detectors", __name__, url_prefix="/api")


@detector_bp.route("/cases/<case_id>/analyze", methods=["POST"])
@jwt_required()
def run_case_analysis(case_id):
    user_id = get_jwt_identity()
    try:
        custom_configs = request.get_json() or {}
        analysis_res = DetectorRunner.run_all_detectors(case_id=case_id, custom_configs=custom_configs)
        log_audit_event(
            action="RUN_DETECTORS",
            user_id=user_id,
            case_id=case_id,
            details={"suspicion_score": analysis_res["suspicion_score"]}
        )
        return api_success(data=analysis_res, message="Financial crime detection analysis completed successfully.")
    except ValueError as ve:
        return api_error(str(ve), code="NOT_FOUND", status_code=404)
    except Exception as e:
        return api_error(f"Analysis failed: {str(e)}", code="SERVER_ERROR", status_code=500)


@detector_bp.route("/cases/<case_id>/detectors", methods=["GET"])
@jwt_required()
def get_case_detectors(case_id):
    results = DetectorResult.query.filter_by(case_id=case_id).all()
    return api_success(data={"detector_results": [r.to_dict() for r in results]})


@detector_bp.route("/cases/<case_id>/suspicious-transactions", methods=["GET"])
@jwt_required()
def get_case_suspicious_transactions(case_id):
    detector_filter = request.args.get("detector")
    q = SuspiciousTransaction.query.filter_by(case_id=case_id)
    if detector_filter:
        q = q.filter_by(detector_name=detector_filter.upper())
    items = q.order_by(SuspiciousTransaction.flagged_at.desc()).all()
    return api_success(data={"suspicious_transactions": [item.to_dict() for item in items]})
