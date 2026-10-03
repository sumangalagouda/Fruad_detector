import networkx as nx
from typing import List, Dict, Any
from app.extensions import db
from app.models.graph import CircularFlow, CircularFlowTransaction, FundFlowEdge
from app.models.transaction import Transaction
from app.utils.logger import logger


class CircularFlowDetector:
    MAX_CYCLE_LENGTH = 5
    HIGH_VALUE_THRESHOLD = 100000.0
    FAST_CYCLE_DAYS = 7.0

    @classmethod
    def detect_circular_flows(cls, case_id: str) -> List[Dict[str, Any]]:
        """
        Detect closed-loop fund circulation patterns (e.g. A -> B -> C -> A) using simple cycles.
        """
        # Clear existing circular flows for re-computation
        CircularFlow.query.filter_by(case_id=case_id).delete()

        # Build graph from stored FundFlowEdges
        edges = FundFlowEdge.query.filter_by(case_id=case_id).all()
        G = nx.DiGraph()

        edge_data_map = {}
        for e in edges:
            G.add_edge(e.source_account, e.destination_account, weight=e.total_amount, tx_ids=e.transaction_ids)
            edge_data_map[(e.source_account, e.destination_account)] = e

        detected_cycles = []
        try:
            # Find simple cycles
            raw_cycles = list(nx.simple_cycles(G))
        except Exception as e:
            logger.error(f"Error finding cycles in graph for case {case_id}: {e}")
            raw_cycles = []

        for cycle in raw_cycles:
            # Only consider cycles between length 2 and MAX_CYCLE_LENGTH
            cycle_len = len(cycle)
            if 2 <= cycle_len <= cls.MAX_CYCLE_LENGTH:
                # Close the loop representation: e.g. ["A", "B", "C", "A"]
                closed_path = cycle + [cycle[0]]

                # Calculate cycle volume and gather transaction evidence
                cycle_amounts = []
                cycle_tx_ids = []
                dates = []

                for k in range(len(closed_path) - 1):
                    src = closed_path[k]
                    dst = closed_path[k + 1]
                    e_obj = edge_data_map.get((src, dst))
                    if e_obj:
                        cycle_amounts.append(e_obj.total_amount)
                        if e_obj.transaction_ids:
                            cycle_tx_ids.extend(e_obj.transaction_ids)
                        if e_obj.first_date:
                            dates.append(e_obj.first_date)
                        if e_obj.last_date:
                            dates.append(e_obj.last_date)

                total_cycle_amount = min(cycle_amounts) if cycle_amounts else 0.0  # bottleneck volume
                duration_days = 0.0
                if dates:
                    min_d = min(dates)
                    max_d = max(dates)
                    duration_days = round((max_d - min_d).total_seconds() / 86400.0, 1)

                risk_level = "MEDIUM"
                if total_cycle_amount >= cls.HIGH_VALUE_THRESHOLD:
                    risk_level = "HIGH"
                if duration_days <= cls.FAST_CYCLE_DAYS and total_cycle_amount >= 50000:
                    risk_level = "CRITICAL"

                summary = (
                    f"Detected closed circular fund movement pattern involving {cycle_len} accounts: "
                    f"{' -> '.join(closed_path)} with estimated circulating volume of ₹{total_cycle_amount:,.2f} "
                    f"spanning {duration_days} days. (Detected financial pattern for investigative review)."
                )

                # Persist in DB
                cf_model = CircularFlow(
                    case_id=case_id,
                    cycle_path=closed_path,
                    length=cycle_len,
                    total_amount=round(total_cycle_amount, 2),
                    duration_days=duration_days,
                    risk_level=risk_level,
                    evidence_summary=summary,
                )
                db.session.add(cf_model)
                db.session.flush()

                # Add ordered transaction links
                for seq, tx_id in enumerate(cycle_tx_ids[:20]):
                    cf_tx = CircularFlowTransaction(
                        circular_flow_id=cf_model.id,
                        transaction_id=tx_id,
                        sequence_order=seq + 1,
                    )
                    db.session.add(cf_tx)

                detected_cycles.append(cf_model)

        db.session.commit()
        logger.info(f"Identified {len(detected_cycles)} circular flow patterns for case {case_id}.")
        return [c.to_dict() for c in detected_cycles]
