from typing import Dict, Any
from app.mcp.registry import mcp_registry
from app.evidence.service import EvidenceService


@mcp_registry.register(
    name="get_case",
    description="Retrieve high-level case details, subject person, and pre-calculated suspicion score.",
    input_schema={
        "type": "object",
        "properties": {
            "case_id": {"type": "string", "description": "The unique ID of the investigation case."}
        },
        "required": ["case_id"],
    },
)
def handle_get_case(args: Dict[str, Any]) -> Dict[str, Any]:
    case_id = args["case_id"]
    case_data = EvidenceService.get_case_evidence(case_id)
    if not case_data:
        return {"found": False, "message": f"Case with ID '{case_id}' was not found in evidence records."}
    return {"found": True, "case": case_data}


@mcp_registry.register(
    name="get_person",
    description="Retrieve personal and identity details of the person under investigation.",
    input_schema={
        "type": "object",
        "properties": {
            "case_id": {"type": "string", "description": "Case ID."}
        },
        "required": ["case_id"],
    },
)
def handle_get_person(args: Dict[str, Any]) -> Dict[str, Any]:
    person = EvidenceService.get_person_evidence(args["case_id"])
    if not person:
        return {"found": False, "message": "No person record found for this case."}
    return {"found": True, "person": person}


@mcp_registry.register(
    name="get_accounts",
    description="Retrieve all bank accounts associated with the person in this case, across multiple banks.",
    input_schema={
        "type": "object",
        "properties": {
            "case_id": {"type": "string", "description": "Case ID."}
        },
        "required": ["case_id"],
    },
)
def handle_get_accounts(args: Dict[str, Any]) -> Dict[str, Any]:
    accounts = EvidenceService.get_accounts_evidence(args["case_id"])
    return {"case_id": args["case_id"], "accounts_count": len(accounts), "accounts": accounts}


@mcp_registry.register(
    name="get_statements",
    description="Retrieve all uploaded bank statements, file metadata, and extraction provenance for the case.",
    input_schema={
        "type": "object",
        "properties": {
            "case_id": {"type": "string", "description": "Case ID."}
        },
        "required": ["case_id"],
    },
)
def handle_get_statements(args: Dict[str, Any]) -> Dict[str, Any]:
    stmts = EvidenceService.get_statements_evidence(args["case_id"])
    return {"case_id": args["case_id"], "statements_count": len(stmts), "statements": stmts}


@mcp_registry.register(
    name="get_statement",
    description="Retrieve details and extraction method for a specific bank statement.",
    input_schema={
        "type": "object",
        "properties": {
            "case_id": {"type": "string", "description": "Case ID."},
            "statement_id": {"type": "string", "description": "Statement ID."}
        },
        "required": ["case_id", "statement_id"],
    },
)
def handle_get_statement(args: Dict[str, Any]) -> Dict[str, Any]:
    stmt = EvidenceService.get_statement_evidence(args["case_id"], args["statement_id"])
    if not stmt:
        return {"found": False, "message": f"Statement {args['statement_id']} not found."}
    return {"found": True, "statement": stmt}


@mcp_registry.register(
    name="get_transactions",
    description="Retrieve a paginated list of canonical transactions for the case.",
    input_schema={
        "type": "object",
        "properties": {
            "case_id": {"type": "string", "description": "Case ID."},
            "account_id": {"type": "string", "description": "Optional account ID filter."},
            "limit": {"type": "integer", "description": "Number of transactions to fetch (default 50)."},
            "offset": {"type": "integer", "description": "Pagination offset."}
        },
        "required": ["case_id"],
    },
)
def handle_get_transactions(args: Dict[str, Any]) -> Dict[str, Any]:
    txs = EvidenceService.get_transactions_evidence(
        case_id=args["case_id"],
        account_id=args.get("account_id"),
        limit=int(args.get("limit", 50)),
        offset=int(args.get("offset", 0)),
    )
    return {"case_id": args["case_id"], "count": len(txs), "transactions": txs}


@mcp_registry.register(
    name="get_transaction",
    description="Retrieve full canonical details, provenance, and validation status of a single transaction by ID.",
    input_schema={
        "type": "object",
        "properties": {
            "case_id": {"type": "string", "description": "Case ID."},
            "transaction_id": {"type": "string", "description": "Transaction ID."}
        },
        "required": ["case_id", "transaction_id"],
    },
)
def handle_get_transaction(args: Dict[str, Any]) -> Dict[str, Any]:
    tx = EvidenceService.get_transaction_evidence(args["case_id"], args["transaction_id"])
    if not tx:
        return {"found": False, "message": f"Transaction {args['transaction_id']} was not found in the available case evidence."}
    return {"found": True, "transaction": tx}


@mcp_registry.register(
    name="search_transactions",
    description="Search transactions matching criteria such as min_amount, max_amount, text query, status, or type.",
    input_schema={
        "type": "object",
        "properties": {
            "case_id": {"type": "string", "description": "Case ID."},
            "query": {"type": "string", "description": "Search term in description or counterparty."},
            "min_amount": {"type": "number", "description": "Minimum transaction amount."},
            "max_amount": {"type": "number", "description": "Maximum transaction amount."},
            "status": {"type": "string", "description": "Filter by status (SUCCESS, FAILED, PENDING, etc.)."},
            "transaction_type": {"type": "string", "description": "DEBIT or CREDIT."},
            "limit": {"type": "integer", "description": "Max results to return (default 50)."}
        },
        "required": ["case_id"],
    },
)
def handle_search_transactions(args: Dict[str, Any]) -> Dict[str, Any]:
    txs = EvidenceService.search_transactions_evidence(
        case_id=args["case_id"],
        query=args.get("query"),
        min_amount=float(args["min_amount"]) if "min_amount" in args and args["min_amount"] is not None else None,
        max_amount=float(args["max_amount"]) if "max_amount" in args and args["max_amount"] is not None else None,
        status=args.get("status"),
        transaction_type=args.get("transaction_type"),
        limit=int(args.get("limit", 50)),
    )
    return {"case_id": args["case_id"], "count": len(txs), "transactions": txs}


@mcp_registry.register(
    name="search_statements",
    description="Search across statements for specific keywords or notes.",
    input_schema={
        "type": "object",
        "properties": {
            "case_id": {"type": "string", "description": "Case ID."},
            "query": {"type": "string", "description": "Keyword to match."}
        },
        "required": ["case_id", "query"],
    },
)
def handle_search_statements(args: Dict[str, Any]) -> Dict[str, Any]:
    query = args["query"].lower()
    stmts = EvidenceService.get_statements_evidence(args["case_id"])
    matched = [s for s in stmts if query in (s.get("bank_name") or "").lower() or query in (s.get("original_filename") or "").lower()]
    return {"case_id": args["case_id"], "count": len(matched), "statements": matched}


@mcp_registry.register(
    name="get_suspicious_transactions",
    description="Retrieve all transactions flagged as suspicious by the deterministic detectors.",
    input_schema={
        "type": "object",
        "properties": {
            "case_id": {"type": "string", "description": "Case ID."},
            "detector": {"type": "string", "description": "Optional detector name filter (e.g., LARGE_TRANSACTION, STRUCTURING)."}
        },
        "required": ["case_id"],
    },
)
def handle_get_suspicious_transactions(args: Dict[str, Any]) -> Dict[str, Any]:
    txs = EvidenceService.get_suspicious_transactions_evidence(args["case_id"], detector=args.get("detector"))
    return {"case_id": args["case_id"], "count": len(txs), "suspicious_transactions": txs}


@mcp_registry.register(
    name="get_detector_results",
    description="Retrieve the output, trigger state, severity, metrics, and evidence of the 8 deterministic crime detectors.",
    input_schema={
        "type": "object",
        "properties": {
            "case_id": {"type": "string", "description": "Case ID."}
        },
        "required": ["case_id"],
    },
)
def handle_get_detector_results(args: Dict[str, Any]) -> Dict[str, Any]:
    results = EvidenceService.get_detector_results_evidence(args["case_id"])
    return {"case_id": args["case_id"], "detector_results": results}


@mcp_registry.register(
    name="get_detector_result",
    description="Retrieve the detailed result of a single specific detector (e.g. STRUCTURING, LARGE_TRANSACTION).",
    input_schema={
        "type": "object",
        "properties": {
            "case_id": {"type": "string", "description": "Case ID."},
            "detector_name": {"type": "string", "description": "Name of the detector."}
        },
        "required": ["case_id", "detector_name"],
    },
)
def handle_get_detector_result(args: Dict[str, Any]) -> Dict[str, Any]:
    res = EvidenceService.get_detector_results_evidence(args["case_id"], detector_name=args["detector_name"])
    if not res:
        return {"found": False, "message": f"No detector result was found for '{args['detector_name']}'."}
    return {"found": True, "detector_result": res[0]}


@mcp_registry.register(
    name="get_related_transactions",
    description="Retrieve transactions sharing the same counterparty, account, or reference.",
    input_schema={
        "type": "object",
        "properties": {
            "case_id": {"type": "string", "description": "Case ID."},
            "counterparty_name": {"type": "string", "description": "Counterparty name to find related flows for."}
        },
        "required": ["case_id", "counterparty_name"],
    },
)
def handle_get_related_transactions(args: Dict[str, Any]) -> Dict[str, Any]:
    txs = EvidenceService.search_transactions_evidence(args["case_id"], query=args["counterparty_name"])
    return {"case_id": args["case_id"], "count": len(txs), "related_transactions": txs}


@mcp_registry.register(
    name="get_fund_flow",
    description="Retrieve the aggregated fund flow graph showing money movements between accounts and external entities.",
    input_schema={
        "type": "object",
        "properties": {
            "case_id": {"type": "string", "description": "Case ID."}
        },
        "required": ["case_id"],
    },
)
def handle_get_fund_flow(args: Dict[str, Any]) -> Dict[str, Any]:
    return EvidenceService.get_fund_flow_evidence(args["case_id"])


@mcp_registry.register(
    name="get_circular_flows",
    description="Retrieve detected circular fund flow cycles (A -> B -> C -> A) with evidence.",
    input_schema={
        "type": "object",
        "properties": {
            "case_id": {"type": "string", "description": "Case ID."}
        },
        "required": ["case_id"],
    },
)
def handle_get_circular_flows(args: Dict[str, Any]) -> Dict[str, Any]:
    flows = EvidenceService.get_circular_flows_evidence(args["case_id"])
    return {"case_id": args["case_id"], "circular_flows_count": len(flows), "circular_flows": flows}


@mcp_registry.register(
    name="get_layering_chains",
    description="Retrieve detected multi-hop layering chains (A -> B -> C -> D) with evidence.",
    input_schema={
        "type": "object",
        "properties": {
            "case_id": {"type": "string", "description": "Case ID."}
        },
        "required": ["case_id"],
    },
)
def handle_get_layering_chains(args: Dict[str, Any]) -> Dict[str, Any]:
    chains = EvidenceService.get_layering_chains_evidence(args["case_id"])
    return {"case_id": args["case_id"], "layering_chains_count": len(chains), "layering_chains": chains}


@mcp_registry.register(
    name="get_money_trail",
    description="Retrieve FIFO fund trail allocations tracing inflows to subsequent outflows.",
    input_schema={
        "type": "object",
        "properties": {
            "case_id": {"type": "string", "description": "Case ID."},
            "transaction_id": {"type": "string", "description": "Optional transaction ID to trace."}
        },
        "required": ["case_id"],
    },
)
def handle_get_money_trail(args: Dict[str, Any]) -> Dict[str, Any]:
    return EvidenceService.get_money_trail_evidence(args["case_id"], transaction_id=args.get("transaction_id"))


@mcp_registry.register(
    name="get_investigation_history",
    description="Retrieve previous investigative Q&A sessions and findings for this case.",
    input_schema={
        "type": "object",
        "properties": {
            "case_id": {"type": "string", "description": "Case ID."}
        },
        "required": ["case_id"],
    },
)
def handle_get_investigation_history(args: Dict[str, Any]) -> Dict[str, Any]:
    history = EvidenceService.get_investigation_history_evidence(args["case_id"])
    return {"case_id": args["case_id"], "sessions_count": len(history), "history": history}
