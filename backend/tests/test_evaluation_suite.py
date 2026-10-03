"""
AI INVESTIGATION AGENT & SYSTEM EVALUATION FRAMEWORK
---------------------------------------------------
Tests factual accuracy, evidence grounding, tool selection,
trap case resistance (e.g., T999), and strict anti-hallucination.
"""

import pytest
from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models.case import Case, Person, Account
from app.models.statement import BankStatement
from app.models.transaction import Transaction
from app.models.user import User
from app.models.detector import DetectorResult
from app.detectors.runner import DetectorRunner
from app.analytics.fund_flow import FundFlowGraphBuilder
from app.analytics.circular_flow import CircularFlowDetector
from app.analytics.fifo_trail import FifoMoneyTrailTracer
from app.ai.agent import InvestigationAgent
from app.mcp.registry import mcp_registry
from datetime import datetime, timezone


@pytest.fixture
def eval_app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()

        # Seed test user
        user = User(id="user-eval-01", username="eval_investigator", email="eval@fintelligence.org", password_hash="hash", full_name="Eval Agent")
        db.session.add(user)

        # Seed test case and person
        person = Person(person_id="p-001", full_name="John Doe", identifier_type="PAN", identifier_value="ABCDE1234F")
        case = Case(case_id="CASE-000001", case_number="CASE-000001", title="Evaluation Test Case", person_id="p-001", created_by="user-eval-01")
        db.session.add_all([person, case])

        # Seed 2 accounts
        acc_a = Account(account_id="acc-a", case_id="CASE-000001", person_id="p-001", bank_name="HDFC Bank", account_number="501001", account_holder="John Doe")
        acc_b = Account(account_id="acc-b", case_id="CASE-000001", person_id="p-001", bank_name="ICICI Bank", account_number="002401", account_holder="John Doe")
        db.session.add_all([acc_a, acc_b])

        # Seed statement
        stmt = BankStatement(
            statement_id="stmt-01", case_id="CASE-000001", account_id="acc-a",
            original_filename="hdfc_eval.csv", stored_filename="stored_hdfc.csv",
            file_type="CSV", file_size=1024, source_path="dummy/path",
            processing_status="COMPLETED", bank_name="HDFC Bank", account_number="501001",
        )
        db.session.add(stmt)

        # Seed real transactions
        tx1 = Transaction(
            transaction_id="T101", statement_id="stmt-01", case_id="CASE-000001", account_id="acc-a",
            account_number="501001", bank_name="HDFC Bank", transaction_date=datetime(2026, 1, 1, 10, 0),
            description="Salary Credit Tech Corp", debit=0, credit=120000, amount=120000, balance=120000,
            transaction_type="CREDIT", status="SUCCESS", source_file="hdfc_eval.csv", source_page=1,
        )
        tx2 = Transaction(
            transaction_id="T102", statement_id="stmt-01", case_id="CASE-000001", account_id="acc-a",
            account_number="501001", bank_name="HDFC Bank", transaction_date=datetime(2026, 1, 10, 10, 0),
            description="Large Cash Withdrawal", debit=85000, credit=0, amount=85000, balance=35000,
            transaction_type="DEBIT", status="SUCCESS", source_file="hdfc_eval.csv", source_page=1,
        )
        # Failed transaction (must not be treated as successful flow)
        tx_failed = Transaction(
            transaction_id="T103", statement_id="stmt-01", case_id="CASE-000001", account_id="acc-a",
            account_number="501001", bank_name="HDFC Bank", transaction_date=datetime(2026, 1, 12, 10, 0),
            description="Failed UPI Payment", debit=45000, credit=0, amount=45000, balance=35000,
            transaction_type="DEBIT", status="FAILED", source_file="hdfc_eval.csv", source_page=1,
        )
        db.session.add_all([tx1, tx2, tx_failed])
        db.session.commit()

        # Run detection and analytics
        DetectorRunner.run_all_detectors("CASE-000001")
        FundFlowGraphBuilder.build_and_persist_graph("CASE-000001")
        CircularFlowDetector.detect_circular_flows("CASE-000001")
        FifoMoneyTrailTracer.compute_fifo_trails("CASE-000001")

        yield app
        db.drop_all()


class TestEvaluationSuite:

    # 1. TRAP CASE: Non-existent transaction (T999)
    def test_trap_case_nonexistent_transaction(self, eval_app):
        agent = InvestigationAgent(provider_type="fallback")
        res = agent.run_investigation(
            case_id="CASE-000001",
            user_id="user-eval-01",
            question="Why was transaction T999 flagged as suspicious?",
        )
        answer = res["answer"].lower()
        # Must explicitly declare that T999 was not found
        assert "not found" in answer or "does not establish" in answer
        # Must NEVER fabricate that T999 was flagged
        assert "t999 was flagged because" not in answer

    # 2. TRAP CASE: Non-existent circular flow
    def test_trap_case_nonexistent_cycle(self, eval_app):
        agent = InvestigationAgent(provider_type="fallback")
        res = agent.run_investigation(
            case_id="CASE-000001",
            user_id="user-eval-01",
            question="Show the circular flow between account 501001 and non-existent account 999999.",
        )
        answer = res["answer"].lower()
        assert "does not establish" in answer or "0 closed cycles" in answer

    # 3. NORMAL CASE: Large transaction detector verification
    def test_normal_case_large_transaction(self, eval_app):
        agent = InvestigationAgent(provider_type="fallback")
        res = agent.run_investigation(
            case_id="CASE-000001",
            user_id="user-eval-01",
            question="Which detector flagged transaction T102?",
        )
        # Should execute MCP tools and ground the answer
        tools_called = [tc["tool_name"] for tc in res["tool_calls"]]
        assert "get_transaction" in tools_called or "get_suspicious_transactions" in tools_called
        assert len(res["parsed_sections"]["evidence"]) > 0 or "t102" in res["answer"].lower()

    # 4. EVIDENCE GROUNDING & MCP TOOLS SELECTION
    def test_tool_selection_for_suspicion_score(self, eval_app):
        agent = InvestigationAgent(provider_type="fallback")
        res = agent.run_investigation(
            case_id="CASE-000001",
            user_id="user-eval-01",
            question="What is the suspicion score for this case?",
        )
        tools_called = [tc["tool_name"] for tc in res["tool_calls"]]
        assert "get_case" in tools_called or "get_detector_results" in tools_called
        assert "score" in res["answer"].lower() or len(res["parsed_sections"]["facts"]) > 0

    # 5. FAILED TRANSACTION EXCLUSION
    def test_failed_transaction_not_in_money_flows(self, eval_app):
        # T103 was FAILED with amount 45,000.
        # It must NOT trigger Large Transaction or Structuring detector!
        res = DetectorResult.query.filter_by(case_id="CASE-000001", detector_name="LARGE_TRANSACTION").first()
        assert "T103" not in (res.transactions or [])
