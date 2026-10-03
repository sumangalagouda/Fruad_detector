from flask import Blueprint, request
from pydantic import ValidationError
from app.schemas.case import CaseCreateRequest, AccountCreateRequest
from app.services.case_service import CaseService
from app.services.audit_service import log_audit_event
from app.utils.responses import api_success, api_error
from flask_jwt_extended import jwt_required, get_jwt_identity

case_bp = Blueprint("cases", __name__, url_prefix="/api/cases")


@case_bp.route("", methods=["POST"])
@jwt_required()
def create_case():
    user_id = get_jwt_identity()
    try:
        data = request.get_json() or {}
        req = CaseCreateRequest(**data)
        case = CaseService.create_case(
            user_id=user_id,
            title=req.title,
            person_data=req.person.model_dump(),
            description=req.description,
            priority=req.priority,
        )
        log_audit_event(action="CREATE_CASE", user_id=user_id, case_id=case.case_id, details={"case_number": case.case_number})
        return api_success(data={"case": case.to_dict()}, message="Case created successfully.", status_code=201)
    except ValidationError as ve:
        return api_error("Validation error", code="VALIDATION_ERROR", status_code=422, details=ve.errors())
    except Exception as e:
        return api_error(f"Failed to create case: {str(e)}", code="SERVER_ERROR", status_code=500)


@case_bp.route("", methods=["GET"])
@jwt_required()
def list_cases():
    user_id = get_jwt_identity()
    status = request.args.get("status")
    cases = CaseService.list_cases(user_id=user_id, status=status)
    return api_success(data={"cases": [c.to_dict() for c in cases]})


@case_bp.route("/<case_id>", methods=["GET"])
@jwt_required()
def get_case(case_id):
    case = CaseService.get_case(case_id)
    if not case:
        return api_error("Case not found.", code="NOT_FOUND", status_code=404)
    return api_success(data={"case": case.to_dict()})


@case_bp.route("/<case_id>", methods=["PUT"])
@jwt_required()
def update_case(case_id):
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    case = CaseService.update_case(
        case_id=case_id,
        title=data.get("title"),
        description=data.get("description"),
        status=data.get("status"),
        priority=data.get("priority"),
    )
    if not case:
        return api_error("Case not found.", code="NOT_FOUND", status_code=404)
    log_audit_event(action="UPDATE_CASE", user_id=user_id, case_id=case_id)
    return api_success(data={"case": case.to_dict()}, message="Case updated successfully.")


@case_bp.route("/<case_id>", methods=["DELETE"])
@jwt_required()
def delete_case(case_id):
    user_id = get_jwt_identity()
    success = CaseService.delete_case(case_id)
    if not success:
        return api_error("Case not found.", code="NOT_FOUND", status_code=404)
    log_audit_event(action="DELETE_CASE", user_id=user_id, case_id=case_id)
    return api_success(message="Case deleted successfully.")


@case_bp.route("/<case_id>/accounts", methods=["GET"])
@jwt_required()
def get_accounts(case_id):
    accounts = CaseService.get_case_accounts(case_id)
    return api_success(data={"accounts": [a.to_dict() for a in accounts]})


@case_bp.route("/<case_id>/accounts", methods=["POST"])
@jwt_required()
def add_account(case_id):
    user_id = get_jwt_identity()
    try:
        data = request.get_json() or {}
        req = AccountCreateRequest(**data)
        account = CaseService.add_account_to_case(
            case_id=case_id,
            bank_name=req.bank_name,
            account_number=req.account_number,
            account_holder=req.account_holder,
            account_type=req.account_type,
            currency=req.currency,
            branch=req.branch,
        )
        log_audit_event(action="ADD_ACCOUNT", user_id=user_id, case_id=case_id, details={"account_id": account.account_id})
        return api_success(data={"account": account.to_dict()}, message="Account added successfully.", status_code=201)
    except ValidationError as ve:
        return api_error("Validation error", code="VALIDATION_ERROR", status_code=422, details=ve.errors())
    except ValueError as ve:
        return api_error(str(ve), code="BAD_REQUEST", status_code=400)
    except Exception as e:
        return api_error(f"Failed to add account: {str(e)}", code="SERVER_ERROR", status_code=500)
