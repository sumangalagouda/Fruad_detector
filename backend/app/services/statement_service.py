import os
import uuid
from datetime import datetime, timezone
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.case import Case, Account
from app.models.statement import BankStatement
from app.models.transaction import Transaction, TransactionValidation
from app.parsers.csv_parser import CsvStatementParser
from app.parsers.excel_parser import ExcelStatementParser
from app.parsers.pdf_parser import PdfStatementParser
from app.parsers.image_parser import ImageStatementParser
from app.parsers.normalizer import TransactionNormalizer
from app.utils.logger import logger
from flask import current_app


class StatementService:
    ALLOWED_EXTENSIONS = {"pdf", "csv", "xlsx", "xls", "png", "jpg", "jpeg"}

    @staticmethod
    def allowed_file(filename: str) -> bool:
        return "." in filename and filename.rsplit(".", 1)[1].lower() in StatementService.ALLOWED_EXTENSIONS

    @staticmethod
    def get_parser_for_ext(ext: str):
        ext = ext.lower()
        if ext == "pdf":
            return PdfStatementParser()
        elif ext == "csv":
            return CsvStatementParser()
        elif ext in ["xlsx", "xls"]:
            return ExcelStatementParser()
        elif ext in ["png", "jpg", "jpeg"]:
            return ImageStatementParser()
        raise ValueError(f"Unsupported file format: .{ext}")

    @staticmethod
    def process_statement_upload(case_id: str, uploaded_file, account_id: str = None) -> BankStatement:
        case = db.session.get(Case, case_id)
        if not case:
            raise ValueError("Case not found.")

        filename = secure_filename(uploaded_file.filename)
        if not StatementService.allowed_file(filename):
            raise ValueError(f"Invalid file type. Supported types: {', '.join(StatementService.ALLOWED_EXTENSIONS)}")

        ext = filename.rsplit(".", 1)[1].lower()
        unique_stored_name = f"{uuid.uuid4().hex}_{filename}"
        upload_dir = current_app.config.get("UPLOAD_FOLDER", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, unique_stored_name)

        uploaded_file.save(file_path)
        file_size = os.path.getsize(file_path)

        statement = BankStatement(
            case_id=case_id,
            account_id=account_id,
            original_filename=filename,
            stored_filename=unique_stored_name,
            file_type=ext.upper(),
            file_size=file_size,
            processing_status="PROCESSING",
            source_path=file_path,
        )
        db.session.add(statement)
        db.session.commit()

        # Execute extraction and normalization pipeline
        try:
            parser = StatementService.get_parser_for_ext(ext)
            parse_result = parser.parse(file_path, filename)

            statement.page_count = max(1, parse_result.page_count)
            statement.extraction_method = parse_result.extraction_method
            statement.bank_name = parse_result.bank_name
            statement.account_number = parse_result.account_number
            statement.account_holder = parse_result.account_holder or case.person.full_name

            # Resolve or create Account
            acc_target = None
            if account_id:
                acc_target = db.session.get(Account, account_id)
            if not acc_target and parse_result.account_number:
                # Find matching account in this case
                acc_target = Account.query.filter_by(
                    case_id=case_id,
                    account_number=parse_result.account_number
                ).first()

            if not acc_target:
                # Create account preserving identity
                acc_target = Account(
                    case_id=case_id,
                    person_id=case.person_id,
                    bank_name=parse_result.bank_name or "Unknown Bank",
                    account_number=parse_result.account_number or f"ACC-{uuid.uuid4().hex[:8].upper()}",
                    account_holder=parse_result.account_holder or case.person.full_name,
                    account_type="SAVINGS",
                    currency="INR",
                    status="ACTIVE",
                )
                db.session.add(acc_target)
                db.session.flush()

            statement.account_id = acc_target.account_id

            # Normalize transactions
            created_transactions = []
            for row in parse_result.transactions:
                canon, val = TransactionNormalizer.normalize_row(
                    row=row,
                    case_id=case_id,
                    statement_id=statement.statement_id,
                    account_id=acc_target.account_id,
                    account_number=acc_target.account_number,
                    account_holder=acc_target.account_holder,
                    bank_name=acc_target.bank_name,
                    source_file=filename,
                )

                tx = Transaction(**canon)
                db.session.add(tx)
                db.session.flush()

                # Add validation record
                v_record = TransactionValidation(
                    transaction_id=tx.transaction_id,
                    case_id=case_id,
                    validation_status=val["validation_status"],
                    issues=val["issues"],
                )
                db.session.add(v_record)
                created_transactions.append(tx)

            statement.processing_status = "NORMALIZED" if created_transactions else "COMPLETED"
            if parse_result.errors:
                statement.processing_error = "; ".join(parse_result.errors[:5])

            db.session.commit()
            logger.info(f"Processed statement {statement.statement_id} with {len(created_transactions)} transactions.")
            return statement

        except Exception as e:
            logger.error(f"Statement processing error for {statement.statement_id}: {e}", exc_info=True)
            statement.processing_status = "FAILED"
            statement.processing_error = str(e)
            db.session.commit()
            return statement

    @staticmethod
    def get_statements_for_case(case_id: str):
        return BankStatement.query.filter_by(case_id=case_id).order_by(BankStatement.upload_timestamp.desc()).all()

    @staticmethod
    def get_statement_by_id(statement_id: str):
        return db.session.get(BankStatement, statement_id)
