import networkx as nx
from collections import defaultdict
from typing import Dict, Any, List
from app.extensions import db
from app.models.case import Account
from app.models.transaction import Transaction
from app.models.graph import FundFlowEdge
from app.utils.logger import logger


class FundFlowGraphBuilder:
    @staticmethod
    def build_and_persist_graph(case_id: str) -> Dict[str, Any]:
        """
        Build a directed fund flow graph using NetworkX.
        Nodes: Accounts and counterparty entities.
        Edges: Real transaction evidence with amounts, dates, and transaction counts.
        """
        # Clear existing edges for case
        FundFlowEdge.query.filter_by(case_id=case_id).delete()

        # Fetch only successful or unreversed transactions
        transactions = Transaction.query.filter(
            Transaction.case_id == case_id,
            ~Transaction.status.in_(["FAILED", "REVERSED", "RETURNED"]),
        ).all()

        G = nx.DiGraph()
        # Aggregated edge storage: (source, target) -> {amount, count, tx_ids, dates}
        edges_agg = defaultdict(lambda: {
            "total_amount": 0.0,
            "count": 0,
            "tx_ids": [],
            "dates": [],
        })

        # Track accounts in case
        case_accounts = {a.account_number: a for a in Account.query.filter_by(case_id=case_id).all()}

        for tx in transactions:
            acc_num = tx.account_number
            cp = tx.counterparty_name or tx.counterparty_account or "UNKNOWN_COUNTERPARTY"

            # Node metadata
            if acc_num not in G:
                G.add_node(acc_num, type="CASE_ACCOUNT", bank=tx.bank_name, label=f"{tx.bank_name} ({acc_num[-4:] if len(acc_num)>=4 else acc_num})")
            if cp not in G:
                G.add_node(cp, type="COUNTERPARTY", bank=tx.counterparty_bank or "External", label=cp)

            if tx.transaction_type == "DEBIT":
                # Money moves from this account to counterparty
                src = acc_num
                dst = cp
            else:
                # Money moves from counterparty to this account
                src = cp
                dst = acc_num

            e = edges_agg[(src, dst)]
            e["total_amount"] += tx.amount
            e["count"] += 1
            e["tx_ids"].append(tx.transaction_id)
            if tx.transaction_date:
                e["dates"].append(tx.transaction_date)

        # Persist edges and build graph response
        graph_nodes = []
        for n, data in G.nodes(data=True):
            graph_nodes.append({
                "id": n,
                "label": data.get("label", n),
                "type": data.get("type", "UNKNOWN"),
                "bank": data.get("bank", "Unknown"),
            })

        graph_edges = []
        for (src, dst), e_info in edges_agg.items():
            first_d = min(e_info["dates"]) if e_info["dates"] else None
            last_d = max(e_info["dates"]) if e_info["dates"] else None

            edge_model = FundFlowEdge(
                case_id=case_id,
                source_account=src,
                destination_account=dst,
                total_amount=round(e_info["total_amount"], 2),
                transaction_count=e_info["count"],
                transaction_ids=e_info["tx_ids"],
                first_date=first_d,
                last_date=last_d,
            )
            db.session.add(edge_model)

            graph_edges.append({
                "source": src,
                "target": dst,
                "total_amount": round(e_info["total_amount"], 2),
                "transaction_count": e_info["count"],
                "transaction_ids": e_info["tx_ids"],
                "first_date": first_d.isoformat() if first_d else None,
                "last_date": last_d.isoformat() if last_d else None,
            })

        db.session.commit()
        logger.info(f"Built fund flow graph for case {case_id}: {len(graph_nodes)} nodes, {len(graph_edges)} edges.")

        return {
            "case_id": case_id,
            "nodes": graph_nodes,
            "edges": graph_edges,
            "node_count": len(graph_nodes),
            "edge_count": len(graph_edges),
        }
