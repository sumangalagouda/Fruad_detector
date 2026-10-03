from flask import Blueprint, request
from pydantic import ValidationError
from app.schemas.auth import RegisterRequest, LoginRequest
from app.services.auth_service import AuthService
from app.services.audit_service import log_audit_event
from app.utils.responses import api_success, api_error
from flask_jwt_extended import jwt_required, get_jwt_identity

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json() or {}
        req = RegisterRequest(**data)
        user, token = AuthService.register_user(
            username=req.username,
            email=req.email,
            password=req.password,
            full_name=req.full_name,
            role=req.role,
        )
        log_audit_event(action="USER_REGISTER", user_id=user.id, details={"username": user.username})
        return api_success(
            data={"user": user.to_dict(), "token": token},
            message="User registered successfully.",
            status_code=201,
        )
    except ValidationError as ve:
        return api_error("Validation error", code="VALIDATION_ERROR", status_code=422, details=ve.errors())
    except ValueError as ve:
        return api_error(str(ve), code="BAD_REQUEST", status_code=400)
    except Exception as e:
        return api_error(f"Registration failed: {str(e)}", code="SERVER_ERROR", status_code=500)


@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json() or {}
        req = LoginRequest(**data)
        user, token = AuthService.authenticate_user(username=req.username, password=req.password)
        log_audit_event(action="USER_LOGIN", user_id=user.id, details={"username": user.username})
        return api_success(
            data={"user": user.to_dict(), "token": token},
            message="Login successful.",
        )
    except ValidationError as ve:
        return api_error("Validation error", code="VALIDATION_ERROR", status_code=422, details=ve.errors())
    except ValueError as ve:
        return api_error(str(ve), code="UNAUTHORIZED", status_code=401)
    except PermissionError as pe:
        return api_error(str(pe), code="FORBIDDEN", status_code=403)
    except Exception as e:
        return api_error(f"Login failed: {str(e)}", code="SERVER_ERROR", status_code=500)


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    user_id = get_jwt_identity()
    log_audit_event(action="USER_LOGOUT", user_id=user_id)
    return api_success(message="Logged out successfully.")


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return api_error("User not found.", code="NOT_FOUND", status_code=404)
    return api_success(data={"user": user.to_dict()})
