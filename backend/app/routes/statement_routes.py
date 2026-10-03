from flask import Blueprint, request
from app.services.statement_service import StatementService
from app.services.audit_service import log_audit_event
from app.utils.responses import api_success, api_error
from flask_jwt_extended import jwt_required, get_jwt_identity

statement_bp = Blueprint("statements", __name__, url_prefix="/api")


@statement_bp.route("/cases/<case_id>/statements/upload", methods=["POST"])
@jwt_required()
def upload_statements(case_id):
    user_id = get_jwt_identity()

    if "files" not in request.files and "file" not in request.files:
        return api_error("No file provided in form field 'file' or 'files'.", code="BAD_REQUEST", status_code=400)

    uploaded_files = request.files.getlist("files")
    if not uploaded_files:
        uploaded_files = [request.files["file"]]

    account_id = request.form.get("account_id")

    results = []
    for f in uploaded_files:
        if f.filename == "":
            continue
        try:
            stmt = StatementService.process_statement_upload(
                case_id=case_id,
                uploaded_file=f,
                account_id=account_id,
            )
            results.append(stmt.to_dict())
            log_audit_event(
                action="UPLOAD_STATEMENT",
                user_id=user_id,
                case_id=case_id,
                details={"statement_id": stmt.statement_id, "filename": stmt.original_filename}
            )
        except Exception as e:
            return api_error(f"Failed to process file {f.filename}: {str(e)}", code="PROCESSING_ERROR", status_code=500)

    return api_success(
        data={"statements": results},
        message=f"Successfully processed {len(results)} statement(s).",
        status_code=201,
    )


@statement_bp.route("/cases/<case_id>/statements", methods=["GET"])
@jwt_required()
def list_case_statements(case_id):
    stmts = StatementService.get_statements_for_case(case_id)
    return api_success(data={"statements": [s.to_dict() for s in stmts]})


@statement_bp.route("/statements/<statement_id>", methods=["GET"])
@jwt_required()
def get_statement(statement_id):
    stmt = StatementService.get_statement_by_id(statement_id)
    if not stmt:
        return api_error("Statement not found.", code="NOT_FOUND", status_code=404)
    return api_success(data={"statement": stmt.to_dict()})
