from flask import jsonify
from typing import Any, Optional


def api_success(data: Any = None, message: str = "Success", status_code: int = 200):
    """
    Standard Success Response Format:
    {
        "success": true,
        "data": {...},
        "message": "..."
    }
    """
    payload = {
        "success": True,
        "data": data if data is not None else {},
        "message": message,
    }
    return jsonify(payload), status_code


def api_error(message: str, code: str = "ERROR", status_code: int = 400, details: Optional[Any] = None):
    """
    Standard Error Response Format:
    {
        "success": false,
        "error": {
            "code": "...",
            "message": "...",
            "details": ...
        }
    }
    """
    err_dict = {
        "code": code,
        "message": message,
    }
    if details is not None:
        err_dict["details"] = details

    payload = {
        "success": False,
        "error": err_dict,
    }
    return jsonify(payload), status_code
