from datetime import datetime, timezone
from typing import Dict, Any, List
from app.extensions import db
from app.models.case import Case
from app.models.report import InvestigationReport
from app.evidence.service import EvidenceService
from app.utils.logger import logger


class InvestigationReportGenerator:
    @staticmethod
    def generate_case_report(case_id: str, user_id: str, title: str = None) -> InvestigationReport:
        """
        Generate a comprehensive, evidence-grounded 17-section investigation report.
        Strictly adheres to cautious financial crime reporting and legal standards.
        """
        # Gather authorized evidence
        case_data = EvidenceService.get_case_evidence(case_id)
        if not case_data:
            raise ValueError("Case not found.")

        person_data = EvidenceService.get_person_evidence(case_id) or {}
        statements = EvidenceService.get_statements_evidence(case_id)
        accounts = EvidenceService.get_accounts_evidence(case_id)
        detector_results = EvidenceService.get_detector_results_evidence(case_id)
        suspicious_txs = EvidenceService.get_suspicious_transactions_evidence(case_id)
        fund_flow = EvidenceService.get_fund_flow_evidence(case_id)
        circular_flows = EvidenceService.get_circular_flows_evidence(case_id)
        layering_chains = EvidenceService.get_layering_chains_evidence(case_id)
        money_trails = EvidenceService.get_money_trail_evidence(case_id).get("trails", [])

        # Build 17 Structured Sections
        sections: Dict[str, Any] = {}

        # 1. Case Information
        sections["case_information"] = {
            "case_id": case_data["case_id"],
            "case_number": case_data["case_number"],
            "title": case_data["title"],
            "status": case_data["status"],
            "priority": case_data["priority"],
            "created_at": case_data["created_at"],
        }

        # 2. Person Information
        sections["person_information"] = {
            "full_name": person_data.get("full_name", "Unknown"),
            "identifier_type": person_data.get("identifier_type"),
            "identifier_value": person_data.get("identifier_value"),
            "date_of_birth": person_data.get("date_of_birth"),
            "phone": person_data.get("phone"),
            "email": person_data.get("email"),
        }

        # 3. Statements Analyzed
        sections["statements_analyzed"] = [
            {
                "statement_id": s["statement_id"],
                "filename": s["original_filename"],
                "file_type": s["file_type"],
                "bank_name": s["bank_name"],
                "page_count": s["page_count"],
                "extraction_method": s["extraction_method"],
                "status": s["processing_status"],
            }
            for s in statements
        ]

        # 4. Accounts Analyzed
        sections["accounts_analyzed"] = [
            {
                "account_id": a["account_id"],
                "bank_name": a["bank_name"],
                "account_number": a["account_number"],
                "account_holder": a["account_holder"],
                "account_type": a["account_type"],
                "currency": a["currency"],
            }
            for a in accounts
        ]

        # 5. Suspicion Score
        sections["suspicion_score"] = {
            "score": case_data.get("suspicion_score", 0.0),
            "max_score": 100.0,
            "metric_title": "Suspicion Score (Investigation Risk Indicator)",
            "score_version": case_data.get("score_version", "v1.0"),
            "breakdown": case_data.get("score_breakdown", {}),
            "caveat": "This score indicates rule-based compliance risk, not a scientific probability of fraud.",
        }

        # 6. Detector Summary
        sections["detector_summary"] = [
            {
                "detector": d["detector"],
                "triggered": d["triggered"],
                "severity": d["severity"],
                "reason": d["reason"],
                "flagged_count": len(d.get("transactions", [])),
                "metrics": d.get("metrics", {}),
            }
            for d in detector_results
        ]

        # 7. Suspicious Transactions
        sections["suspicious_transactions"] = [
            {
                "transaction_id": st["transaction_id"],
                "detector": st["detector_name"],
                "severity": st["severity"],
                "reason": st["reason"],
                "amount": st.get("transaction", {}).get("amount", 0.0) if st.get("transaction") else 0.0,
                "date": st.get("transaction", {}).get("transaction_date") if st.get("transaction") else None,
            }
            for st in suspicious_txs
        ]

        # 8. Transaction-Level Evidence
        sections["transaction_level_evidence"] = [
            {
                "transaction_id": st["transaction_id"],
                "source_file": st.get("transaction", {}).get("source_file", "Unknown") if st.get("transaction") else "Unknown",
                "source_page": st.get("transaction", {}).get("source_page", 1) if st.get("transaction") else 1,
                "evidence_data": st.get("evidence_data", {}),
            }
            for st in suspicious_txs[:30]
        ]

        # 9. Fund Flow
        sections["fund_flow"] = {
            "node_count": len(fund_flow.get("nodes", [])),
            "edge_count": len(fund_flow.get("edges", [])),
            "major_edges": sorted(fund_flow.get("edges", []), key=lambda x: x.get("total_amount", 0), reverse=True)[:10],
        }

        # 10. Circular Flows
        sections["circular_flows"] = circular_flows

        # 11. Layering Chains
        sections["layering_chains"] = layering_chains

        # 12. FIFO Money Trail
        sections["fifo_money_trail"] = {
            "total_trails_count": len(money_trails),
            "sample_allocations": money_trails[:10],
            "disclaimer": "FIFO allocation indicates sequential funds absorption according to transaction timing, not physical provenance.",
        }

        # 13. Key Evidence
        key_ev = []
        for d in detector_results:
            if d.get("triggered"):
                key_ev.append(f"{d.get('detector')}: {d.get('reason')}")
        if circular_flows:
            key_ev.append(f"Identified {len(circular_flows)} circular flow pattern(s) across accounts.")
        if layering_chains:
            key_ev.append(f"Identified {len(layering_chains)} multi-hop layering chain(s).")
        sections["key_evidence"] = key_ev

        # 14. Findings
        sections["findings"] = [
            f"The subject maintains {len(accounts)} verified bank account(s) across {len(set(a['bank_name'] for a in accounts))} institution(s).",
            f"Analysis of {len(statements)} statement(s) yielded an overall Suspicion Score of {case_data.get('suspicion_score', 0.0)}/100.",
            f"A total of {len(suspicious_txs)} transaction(s) triggered surveillance flags.",
        ]

        # 15. Missing Evidence
        missing = []
        if not statements:
            missing.append("No statements have been provided for processing.")
        unknown_cps = sum(1 for e in fund_flow.get("edges", []) if "UNKNOWN" in e.get("destination_account", ""))
        if unknown_cps > 0:
            missing.append(f"{unknown_cps} counterparty entities lack confirmed account numbers or KYC verification.")
        sections["missing_evidence"] = missing or ["All requested source statements have been accounted for."]

        # 16. Investigation Limitations
        sections["investigation_limitations"] = [
            "Analysis is restricted strictly to uploaded statements and date windows provided.",
            "Off-book transactions, unbanked cash transfers, and external accounts are not visible.",
            "Surveillance rules indicate behavioral risk patterns; they do not constitute criminal indictment.",
        ]

        # 17. Recommended Next Investigation Steps
        sections["recommended_next_steps"] = [
            "Obtain beneficial ownership details for primary counterparties.",
            "Issue documentation requests for rapid pass-through or structuring transactions.",
            "Request complete statements for counterparties participating in circular flow paths.",
            "Submit finding summary to senior compliance review if score exceeds 50.",
        ]

        # Compile Markdown
        md_lines = [
            f"# FINANCIAL CRIME INVESTIGATION REPORT",
            f"**Case Number:** {case_data['case_number']} | **Date Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"**Subject:** {person_data.get('full_name')} | **Suspicion Score:** {case_data.get('suspicion_score')}/100",
            "",
            "---",
            "",
            "## 1. Case Information",
            f"- **Title:** {case_data['title']}",
            f"- **Status:** {case_data['status']}",
            f"- **Priority:** {case_data['priority']}",
            "",
            "## 2. Person Information",
            f"- **Full Name:** {person_data.get('full_name')}",
            f"- **Identifier:** {person_data.get('identifier_type', 'N/A')}: {person_data.get('identifier_value', 'N/A')}",
            "",
            "## 3. Statements Analyzed",
            f"Total statements processed: {len(statements)}",
        ]
        for s in statements:
            md_lines.append(f"- **{s['original_filename']}** ({s['bank_name']}) - {s['extraction_method']} ({s['page_count']} pages)")

        md_lines.extend([
            "",
            "## 4. Accounts Analyzed",
        ])
        for a in accounts:
            md_lines.append(f"- **{a['bank_name']}** - `{a['account_number']}` ({a['account_type']}, {a['currency']})")

        md_lines.extend([
            "",
            "## 5. Suspicion Score",
            f"**Score:** {case_data.get('suspicion_score')}/100",
            f"> [!NOTE] {sections['suspicion_score']['caveat']}",
            "",
            "## 6. Detector Summary",
        ])
        for d in detector_results:
            status = "TRIGGERED" if d["triggered"] else "CLEAR"
            md_lines.append(f"- **{d['detector']}**: `{status}` ({d['severity']}) — {d['reason']}")

        md_lines.extend([
            "",
            "## 7. Suspicious Transactions",
            f"Total suspicious transactions flagged: {len(suspicious_txs)}",
            "",
            "## 8. Transaction-Level Evidence",
            "Underlying transaction records preserved with page-level provenance in the evidence database.",
            "",
            "## 9. Fund Flow Summary",
            f"Graph contains {len(fund_flow.get('nodes', []))} nodes and {len(fund_flow.get('edges', []))} transfer edges.",
            "",
            "## 10. Circular Flows",
            f"Detected {len(circular_flows)} circular loops.",
        ])
        for cf in circular_flows:
            md_lines.append(f"- {' -> '.join(cf['cycle_path'])} (₹{cf['total_amount']:,.2f}, {cf['duration_days']} days)")

        md_lines.extend([
            "",
            "## 11. Layering Chains",
            f"Detected {len(layering_chains)} multi-hop transit paths.",
        ])
        for lay in layering_chains:
            md_lines.append(f"- {' -> '.join(lay['chain_path'])} ({lay['hops_count']} hops, ₹{lay['total_amount']:,.2f})")

        md_lines.extend([
            "",
            "## 12. FIFO Money Trail",
            f"{sections['fifo_money_trail']['disclaimer']}",
            "",
            "## 13. Key Evidence",
        ])
        for ke in key_ev:
            md_lines.append(f"- {ke}")

        md_lines.extend([
            "",
            "## 14. Findings",
        ])
        for fn in sections["findings"]:
            md_lines.append(f"- {fn}")

        md_lines.extend([
            "",
            "## 15. Missing Evidence",
        ])
        for me in sections["missing_evidence"]:
            md_lines.append(f"- {me}")

        md_lines.extend([
            "",
            "## 16. Investigation Limitations",
        ])
        for lim in sections["investigation_limitations"]:
            md_lines.append(f"- {lim}")

        md_lines.extend([
            "",
            "## 17. Recommended Next Investigation Steps",
        ])
        for nxt in sections["recommended_next_steps"]:
            md_lines.append(f"1. {nxt}")

        full_md = "\n".join(md_lines)

        report = InvestigationReport(
            case_id=case_id,
            user_id=user_id,
            title=title or f"Investigation Report - {case_data['case_number']}",
            status="GENERATED",
            sections_data=sections,
            content_markdown=full_md,
        )
        db.session.add(report)
        db.session.commit()

        logger.info(f"Generated 17-section investigation report {report.report_id} for case {case_id}.")
        return report
