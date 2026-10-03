import networkx as nx
from typing import List, Dict, Any
from app.extensions import db
from app.models.graph import LayeringChain, LayeringChainTransaction, FundFlowEdge
from app.utils.logger import logger


class LayeringChainDetector:
    MIN_HOPS = 3  # At least 3 hops (A -> B -> C -> D)
    MAX_HOPS = 6

    @classmethod
    def detect_layering_chains(cls, case_id: str) -> List[Dict[str, Any]]:
        """
        Detect multi-hop transit chains (e.g., A -> B -> C -> D) used to obscure fund origins.
        """
        LayeringChain.query.filter_by(case_id=case_id).delete()

        edges = FundFlowEdge.query.filter_by(case_id=case_id).all()
        G = nx.DiGraph()
        edge_data_map = {}

        for e in edges:
            G.add_edge(e.source_account, e.destination_account, weight=e.total_amount, tx_ids=e.transaction_ids)
            edge_data_map[(e.source_account, e.destination_account)] = e

        chains_detected = []
        visited_paths = set()

        # Perform DFS path exploration
        for source in G.nodes():
            for target in G.nodes():
                if source == target:
                    continue
                try:
                    # Find all simple paths between source and target
                    paths = nx.all_simple_paths(G, source=source, target=target, cutoff=cls.MAX_HOPS)
                    for path in paths:
                        hops = len(path) - 1
                        if hops >= cls.MIN_HOPS:
                            path_tuple = tuple(path)
                            if path_tuple in visited_paths:
                                continue
                            visited_paths.add(path_tuple)

                            # Gather chain metrics
                            chain_amounts = []
                            chain_tx_ids = []
                            dates = []

                            for i in range(len(path) - 1):
                                u = path[i]
                                v = path[i + 1]
                                e_obj = edge_data_map.get((u, v))
                                if e_obj:
                                    chain_amounts.append(e_obj.total_amount)
                                    if e_obj.transaction_ids:
                                        chain_tx_ids.extend(e_obj.transaction_ids)
                                    if e_obj.first_date:
                                        dates.append(e_obj.first_date)
                                    if e_obj.last_date:
                                        dates.append(e_obj.last_date)

                            flow_amount = min(chain_amounts) if chain_amounts else 0.0
                            start_date = min(dates) if dates else None
                            end_date = max(dates) if dates else None
                            duration_hours = (
                                round((end_date - start_date).total_seconds() / 3600.0, 1)
                                if start_date and end_date
                                else 0.0
                            )

                            risk = "HIGH" if hops >= 4 or flow_amount >= 100000 else "MEDIUM"
                            summary = (
                                f"Identified a {hops}-hop transit chain: {' -> '.join(path)} "
                                f"transferring an estimated bottleneck volume of ₹{flow_amount:,.2f} "
                                f"over {duration_hours} hours. Consistent with layered fund routing."
                            )

                            chain_model = LayeringChain(
                                case_id=case_id,
                                chain_path=path,
                                hops_count=hops,
                                total_amount=round(flow_amount, 2),
                                start_date=start_date,
                                end_date=end_date,
                                duration_hours=duration_hours,
                                risk_level=risk,
                                evidence_summary=summary,
                            )
                            db.session.add(chain_model)
                            db.session.flush()

                            for seq, tx_id in enumerate(chain_tx_ids[:25]):
                                db.session.add(
                                    LayeringChainTransaction(
                                        layering_chain_id=chain_model.id,
                                        transaction_id=tx_id,
                                        sequence_order=seq + 1,
                                    )
                                )
                            chains_detected.append(chain_model)

                except Exception as path_err:
                    continue

        db.session.commit()
        logger.info(f"Identified {len(chains_detected)} layering chains for case {case_id}.")
        return [c.to_dict() for c in chains_detected]
