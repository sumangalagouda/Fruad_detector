from flask import Blueprint, request
from app.analytics.fund_flow import FundFlowGraphBuilder
from app.analytics.circular_flow import CircularFlowDetector
from app.analytics.layering import LayeringChainDetector
from app.analytics.fifo_trail import FifoMoneyTrailTracer
from app.models.graph import FundFlowEdge, CircularFlow, LayeringChain, MoneyTrail
from app.utils.responses import api_success, api_error
from flask_jwt_extended import jwt_required

graph_bp = Blueprint("graph", __name__, url_prefix="/api")


@graph_bp.route("/cases/<case_id>/fund-flow", methods=["GET"])
@jwt_required()
def get_case_fund_flow(case_id):
    recalculate = request.args.get("refresh", "false").lower() == "true"
    edges = FundFlowEdge.query.filter_by(case_id=case_id).all()

    if not edges or recalculate:
        graph_data = FundFlowGraphBuilder.build_and_persist_graph(case_id)
        return api_success(data=graph_data)

    # Return existing persisted graph
    nodes_set = set()
    edges_list = []
    for e in edges:
        nodes_set.add(e.source_account)
        nodes_set.add(e.destination_account)
        edges_list.append(e.to_dict())

    nodes_list = [{"id": n, "label": n} for n in nodes_set]
    return api_success(data={"nodes": nodes_list, "edges": edges_list})


@graph_bp.route("/cases/<case_id>/circular-flows", methods=["GET"])
@jwt_required()
def get_case_circular_flows(case_id):
    recalculate = request.args.get("refresh", "false").lower() == "true"
    flows = CircularFlow.query.filter_by(case_id=case_id).all()

    if not flows or recalculate:
        # ensure edges exist first
        if not FundFlowEdge.query.filter_by(case_id=case_id).first():
            FundFlowGraphBuilder.build_and_persist_graph(case_id)
        res = CircularFlowDetector.detect_circular_flows(case_id)
        return api_success(data={"circular_flows": res})

    return api_success(data={"circular_flows": [f.to_dict() for f in flows]})


@graph_bp.route("/cases/<case_id>/layering", methods=["GET"])
@jwt_required()
def get_case_layering(case_id):
    recalculate = request.args.get("refresh", "false").lower() == "true"
    chains = LayeringChain.query.filter_by(case_id=case_id).all()

    if not chains or recalculate:
        if not FundFlowEdge.query.filter_by(case_id=case_id).first():
            FundFlowGraphBuilder.build_and_persist_graph(case_id)
        res = LayeringChainDetector.detect_layering_chains(case_id)
        return api_success(data={"layering_chains": res})

    return api_success(data={"layering_chains": [c.to_dict() for c in chains]})


@graph_bp.route("/cases/<case_id>/money-trail", methods=["GET"])
@jwt_required()
def get_case_money_trail(case_id):
    tx_id = request.args.get("transaction_id")
    recalculate = request.args.get("refresh", "false").lower() == "true"

    if tx_id:
        detail = FifoMoneyTrailTracer.get_trail_for_transaction(case_id, tx_id)
        return api_success(data=detail)

    trails = MoneyTrail.query.filter_by(case_id=case_id).all()
    if not trails or recalculate:
        res = FifoMoneyTrailTracer.compute_fifo_trails(case_id)
        return api_success(data={"money_trails": res})

    return api_success(data={"money_trails": [t.to_dict() for t in trails]})
