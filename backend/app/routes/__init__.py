from app.routes.auth_routes import auth_bp
from app.routes.case_routes import case_bp
from app.routes.statement_routes import statement_bp
from app.routes.transaction_routes import transaction_bp
from app.routes.detector_routes import detector_bp
from app.routes.graph_routes import graph_bp
from app.routes.ai_routes import ai_bp
from app.routes.report_routes import report_bp
from app.routes.audit_routes import audit_bp
from app.mcp.server import mcp_bp

__all__ = [
    "auth_bp",
    "case_bp",
    "statement_bp",
    "transaction_bp",
    "detector_bp",
    "graph_bp",
    "ai_bp",
    "report_bp",
    "audit_bp",
    "mcp_bp",
]
