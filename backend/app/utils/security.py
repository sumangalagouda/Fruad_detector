from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from app.utils.responses import api_error


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)


def role_required(*allowed_roles):
    """Decorator to require specific user roles."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            role = claims.get("role", "investigator")
            if role not in allowed_roles:
                return api_error("Insufficient permissions for this action.", code="FORBIDDEN", status_code=403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_current_user_id() -> str:
    """Helper to extract user ID from active JWT request."""
    verify_jwt_in_request()
    return str(get_jwt_identity())
