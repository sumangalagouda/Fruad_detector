from datetime import datetime, timezone
import uuid
from app.extensions import db
from app.models.case import Case, Person, Account
from app.models.user import User


class CaseService:
    @staticmethod
    def generate_case_number():
        count = Case.query.count() + 1
        return f"CASE-{count:06d}"

    @staticmethod
    def create_case(user_id: str, title: str, person_data: dict, description: str = None, priority: str = "MEDIUM"):
        # Create or find Person
        identifier_val = person_data.get("identifier_value")
        person = None
        if identifier_val:
            person = Person.query.filter_by(identifier_value=identifier_val).first()

        if not person:
            dob = None
            if person_data.get("date_of_birth"):
                try:
                    dob = datetime.strptime(person_data["date_of_birth"], "%Y-%m-%d").date()
                except Exception:
                    pass

            person = Person(
                full_name=person_data["full_name"],
                identifier_type=person_data.get("identifier_type"),
                identifier_value=identifier_val,
                date_of_birth=dob,
                address=person_data.get("address"),
                phone=person_data.get("phone"),
                email=person_data.get("email"),
                notes=person_data.get("notes"),
            )
            db.session.add(person)
            db.session.flush()

        case_number = CaseService.generate_case_number()
        case = Case(
            case_number=case_number,
            title=title,
            description=description,
            priority=priority,
            status="ACTIVE",
            person_id=person.person_id,
            created_by=user_id,
            suspicion_score=0.0,
            score_version="v1.0",
            score_breakdown={},
        )
        db.session.add(case)
        db.session.commit()
        return case

    @staticmethod
    def list_cases(user_id: str = None, status: str = None, limit: int = 100):
        query = Case.query
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Case.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_case(case_id: str):
        return db.session.get(Case, case_id)

    @staticmethod
    def update_case(case_id: str, title: str = None, description: str = None, status: str = None, priority: str = None):
        case = db.session.get(Case, case_id)
        if not case:
            return None
        if title is not None:
            case.title = title
        if description is not None:
            case.description = description
        if status is not None:
            case.status = status
        if priority is not None:
            case.priority = priority
        db.session.commit()
        return case

    @staticmethod
    def delete_case(case_id: str):
        case = db.session.get(Case, case_id)
        if not case:
            return False
        db.session.delete(case)
        db.session.commit()
        return True

    @staticmethod
    def add_account_to_case(case_id: str, bank_name: str, account_number: str, account_holder: str = None, account_type: str = "SAVINGS", currency: str = "INR", branch: str = None):
        case = db.session.get(Case, case_id)
        if not case:
            raise ValueError("Case not found.")

        # Check existing account in case
        existing = Account.query.filter_by(case_id=case_id, bank_name=bank_name, account_number=account_number).first()
        if existing:
            return existing

        account = Account(
            case_id=case_id,
            person_id=case.person_id,
            bank_name=bank_name,
            account_number=account_number,
            account_holder=account_holder or case.person.full_name,
            account_type=account_type,
            currency=currency,
            branch=branch,
            status="ACTIVE",
        )
        db.session.add(account)
        db.session.commit()
        return account

    @staticmethod
    def get_case_accounts(case_id: str):
        return Account.query.filter_by(case_id=case_id).all()
