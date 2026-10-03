from flask import Blueprint, request, jsonify
from app.mcp.registry import mcp_registry
import app.mcp.tools  # Ensure all tools are registered
from app.utils.responses import api_success, api_error
from app.services.audit_service import log_audit_event
from flask_jwt_extended import jwt_required, get_jwt_identity

mcp_bp = Blueprint("mcp", __name__, url_prefix="/api/mcp")


@mcp_bp.route("/tools", methods=["GET"])
@jwt_required()
def list_mcp_tools():
    """List all available MCP tools in standard format."""
    tools = [t.to_mcp_format() for t in mcp_registry.list_tools()]
    return api_success(data={"tools": tools})


@mcp_bp.route("/tools/execute", methods=["POST"])
@jwt_required()
def execute_mcp_tool():
    """Execute an MCP tool by name."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    tool_name = data.get("tool_name")
    arguments = data.get("arguments", {})

    if not tool_name:
        return api_error("Missing 'tool_name' in request body.", code="BAD_REQUEST", status_code=400)

    try:
        result = mcp_registry.execute(tool_name, arguments)
        log_audit_event(
            action="EXECUTE_MCP_TOOL",
            user_id=user_id,
            case_id=arguments.get("case_id"),
            tool=tool_name,
            tool_arguments=arguments,
            result_status="SUCCESS",
        )
        return api_success(data={"tool": tool_name, "result": result})
    except ValueError as ve:
        return api_error(str(ve), code="NOT_FOUND", status_code=404)
    except Exception as e:
        log_audit_event(
            action="EXECUTE_MCP_TOOL",
            user_id=user_id,
            case_id=arguments.get("case_id"),
            tool=tool_name,
            tool_arguments=arguments,
            result_status="ERROR",
            details={"error": str(e)},
        )
        return api_error(f"Error executing MCP tool {tool_name}: {str(e)}", code="TOOL_EXECUTION_ERROR", status_code=500)
