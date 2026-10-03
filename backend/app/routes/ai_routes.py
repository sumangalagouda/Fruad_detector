from flask import Blueprint, request
from pydantic import ValidationError
from app.schemas.investigation import InvestigateQuestionRequest, InvestigatorFeedbackRequest
from app.ai.agent import InvestigationAgent
from app.models.investigation import Investigation, InvestigatorFeedback
from app.extensions import db
from app.services.audit_service import log_audit_event
from app.utils.responses import api_success, api_error
from flask_jwt_extended import jwt_required, get_jwt_identity

ai_bp = Blueprint("ai", __name__, url_prefix="/api")


@ai_bp.route("/cases/<case_id>/investigate", methods=["POST"])
@jwt_required()
def investigate(case_id):
    user_id = get_jwt_identity()
    try:
        data = request.get_json() or {}
        req = InvestigateQuestionRequest(**data)
        agent = InvestigationAgent()
        result = agent.run_investigation(
            case_id=case_id,
            user_id=user_id,
            question=req.question,
            investigation_id=req.investigation_id,
        )
        return api_success(data=result, message="Investigation response generated successfully.")
    except ValidationError as ve:
        return api_error("Validation error", code="VALIDATION_ERROR", status_code=422, details=ve.errors())
    except ValueError as ve:
        return api_error(str(ve), code="NOT_FOUND", status_code=404)
    except Exception as e:
        return api_error(f"Investigation failed: {str(e)}", code="SERVER_ERROR", status_code=500)


@ai_bp.route("/cases/<case_id>/investigations", methods=["GET"])
@jwt_required()
def list_investigations(case_id):
    invs = Investigation.query.filter_by(case_id=case_id).order_by(Investigation.created_at.desc()).all()
    return api_success(data={"investigations": [i.to_dict() for i in invs]})


@ai_bp.route("/investigations/<investigation_id>", methods=["GET"])
@jwt_required()
def get_investigation(investigation_id):
    inv = db.session.get(Investigation, investigation_id)
    if not inv:
        return api_error("Investigation session not found.", code="NOT_FOUND", status_code=404)
    return api_success(data={"investigation": inv.to_dict()})


@ai_bp.route("/investigations/<investigation_id>/feedback", methods=["POST"])
@jwt_required()
def submit_feedback(investigation_id):
    user_id = get_jwt_identity()
    try:
        data = request.get_json() or {}
        req = InvestigatorFeedbackRequest(**data)

        inv = db.session.get(Investigation, investigation_id)
        if not inv:
            return api_error("Investigation session not found.", code="NOT_FOUND", status_code=404)

        feedback = InvestigatorFeedback(
            case_id=inv.case_id,
            investigation_id=investigation_id,
            message_id=req.message_id,
            user_id=user_id,
            feedback_type=req.feedback_type,
            comment=req.comment,
        )
        db.session.add(feedback)
        db.session.commit()

        log_audit_event(
            action="INVESTIGATOR_FEEDBACK",
            user_id=user_id,
            case_id=inv.case_id,
            details={"feedback_type": req.feedback_type, "message_id": req.message_id},
        )
        return api_success(data={"feedback": feedback.to_dict()}, message="Feedback recorded successfully.", status_code=201)
    except ValidationError as ve:
        return api_error("Validation error", code="VALIDATION_ERROR", status_code=422, details=ve.errors())
    except Exception as e:
        return api_error(f"Failed to record feedback: {str(e)}", code="SERVER_ERROR", status_code=500)
