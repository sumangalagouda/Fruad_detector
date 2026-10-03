from flask import Blueprint, request
from app.services.transaction_service import TransactionService
from app.utils.responses import api_success, api_error
from flask_jwt_extended import jwt_required

transaction_bp = Blueprint("transactions", __name__, url_prefix="/api")


@transaction_bp.route("/cases/<case_id>/transactions", methods=["GET"])
@jwt_required()
def get_case_transactions(case_id):
    query = request.args.get("query")
    account_id = request.args.get("account_id")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    min_amount = float(request.args.get("min_amount")) if request.args.get("min_amount") else None
    max_amount = float(request.args.get("max_amount")) if request.args.get("max_amount") else None
    tx_type = request.args.get("transaction_type")
    status = request.args.get("status")
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 50))

    result = TransactionService.search_transactions(
        case_id=case_id,
        query=query,
        account_id=account_id,
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        transaction_type=tx_type,
        status=status,
        page=page,
        page_size=page_size,
    )
    return api_success(data=result)


@transaction_bp.route("/cases/<case_id>/transactions/search", methods=["GET", "POST"])
@jwt_required()
def search_case_transactions(case_id):
    data = request.get_json() if request.method == "POST" else request.args
    query = data.get("query")
    account_id = data.get("account_id")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    min_amount = float(data.get("min_amount")) if data.get("min_amount") else None
    max_amount = float(data.get("max_amount")) if data.get("max_amount") else None
    tx_type = data.get("transaction_type")
    status = data.get("status")
    page = int(data.get("page", 1))
    page_size = int(data.get("page_size", 50))

    result = TransactionService.search_transactions(
        case_id=case_id,
        query=query,
        account_id=account_id,
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        transaction_type=tx_type,
        status=status,
        page=page,
        page_size=page_size,
    )
    return api_success(data=result)


@transaction_bp.route("/transactions/<transaction_id>", methods=["GET"])
@jwt_required()
def get_transaction(transaction_id):
    tx = TransactionService.get_transaction(transaction_id)
    if not tx:
        return api_error("Transaction not found.", code="NOT_FOUND", status_code=404)
    return api_success(data={"transaction": tx.to_dict()})
