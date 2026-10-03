"""
DATABASE SEEDING SCRIPT
-----------------------
Creates default investigator account:
Username: investigator
Password: password123
Uploads and processes the 4 synthetic bank statements into CASE-000001.
Runs all 8 detectors, builds fund flow graph, circular flows, layering, and FIFO trail.
"""

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.case import Case, Person, Account
from app.services.auth_service import AuthService
from app.services.statement_service import StatementService
from app.detectors.runner import DetectorRunner
from app.analytics.fund_flow import FundFlowGraphBuilder
from app.analytics.circular_flow import CircularFlowDetector
from app.analytics.layering import LayeringChainDetector
from app.analytics.fifo_trail import FifoMoneyTrailTracer
from app.ai.report_generator import InvestigationReportGenerator
from sample_data.generate_synthetic_data import generate_all_sample_statements
from werkzeug.datastructures import FileStorage
import os


def seed():
    app = create_app()
    with app.app_context():
        print("1. Seeding User...")
        user = User.query.filter_by(username="investigator").first()
        if not user:
            user, token = AuthService.register_user(
                username="investigator",
                email="investigator@fintelligence.org",
                password="password123",
                full_name="Chief Inspector Sarah Connor",
                role="investigator",
            )
            print("   Created user 'investigator' with password 'password123'")
        else:
            print("   User 'investigator' already exists.")

        print("2. Generating synthetic statements...")
        paths = generate_all_sample_statements()

        print("3. Creating Case & Subject Person...")
        case = Case.query.filter_by(case_number="CASE-000001").first()
        if not case:
            person = Person(
                full_name="John Doe",
                identifier_type="PAN",
                identifier_value="ABCDE1234F",
                address="742 Evergreen Terrace, Sector 4, Financial District",
                phone="+91 98765 43210",
                email="john.doe@syntheticmail.test",
                notes="Subject of multi-bank financial intelligence inquiry regarding rapid corporate dispersals and reciprocal cycling.",
            )
            db.session.add(person)
            db.session.flush()

            case = Case(
                case_id="case-000001-uuid",
                case_number="CASE-000001",
                title="Investigation: John Doe Multi-Account Dispersals",
                description="Holistic examination of 4 bank statements (HDFC, ICICI, Axis, SBI) to uncover cross-account structuring, pass-through conduits, and closed loop fund circulation.",
                priority="HIGH",
                status="ACTIVE",
                person_id=person.person_id,
                created_by=user.id,
            )
            db.session.add(case)
            db.session.commit()
            print("   Created CASE-000001 for John Doe.")
        else:
            print("   CASE-000001 already exists.")

        print("4. Uploading & Processing Bank Statements...")
        for p in paths:
            filename = os.path.basename(p)
            with open(p, "rb") as f:
                file_storage = FileStorage(stream=f, filename=filename, content_type="application/octet-stream")
                stmt = StatementService.process_statement_upload(case_id=case.case_id, uploaded_file=file_storage)
                print(f"   Processed {filename}: {stmt.processing_status}, Transactions: {stmt.transactions.count()}")

        print("5. Running 8 Financial Crime Detectors & Suspicion Scoring...")
        analysis = DetectorRunner.run_all_detectors(case_id=case.case_id)
        print(f"   Calculated Suspicion Score: {analysis['suspicion_score']}/100")

        print("6. Building Fund Flow Graph...")
        graph = FundFlowGraphBuilder.build_and_persist_graph(case_id=case.case_id)
        print(f"   Graph: {graph['node_count']} nodes, {graph['edge_count']} edges.")

        print("7. Detecting Circular Flows...")
        cycles = CircularFlowDetector.detect_circular_flows(case_id=case.case_id)
        print(f"   Identified {len(cycles)} circular flow pattern(s).")

        print("8. Detecting Layering Chains...")
        chains = LayeringChainDetector.detect_layering_chains(case_id=case.case_id)
        print(f"   Identified {len(chains)} layering chain(s).")

        print("9. Tracing FIFO Money Trails...")
        trails = FifoMoneyTrailTracer.compute_fifo_trails(case_id=case.case_id)
        print(f"   Allocated {len(trails)} FIFO money trail links.")

        print("10. Generating Initial 17-Section Report...")
        report = InvestigationReportGenerator.generate_case_report(case_id=case.case_id, user_id=user.id)
        print(f"   Generated Report: '{report.title}' ({report.report_id})")

        print("\nSeeding completed successfully! System is primed with rich multi-statement case data.")


if __name__ == "__main__":
    seed()
