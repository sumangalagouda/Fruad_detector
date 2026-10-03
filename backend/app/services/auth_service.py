from app.extensions import db
from app.models.user import User
from app.utils.security import hash_password, verify_password
from flask_jwt_extended import create_access_token


class AuthService:
    @staticmethod
    def register_user(username: str, email: str, password: str, full_name: str, role: str = "investigator"):
        if User.query.filter((User.username == username) | (User.email == email)).first():
            raise ValueError("Username or email already exists.")

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role=role,
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()

        token = create_access_token(
            identity=user.id,
            additional_claims={"role": user.role, "username": user.username, "full_name": user.full_name},
        )
        return user, token

    @staticmethod
    def authenticate_user(username: str, password: str):
        user = User.query.filter_by(username=username).first()
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Invalid username or password.")
        if not user.is_active:
            raise PermissionError("User account is deactivated.")

        token = create_access_token(
            identity=user.id,
            additional_claims={"role": user.role, "username": user.username, "full_name": user.full_name},
        )
        return user, token

    @staticmethod
    def get_user_by_id(user_id: str):
        return db.session.get(User, user_id)
