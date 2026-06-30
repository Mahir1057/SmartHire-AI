from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, generate_secure_token, get_password_hash, hash_token, verify_password
from app.models.user import PasswordResetToken, RefreshToken, User
from app.repositories.user_repository import TokenRepository, UserRepository
from app.schemas.auth import PasswordResetCreated, TokenPair
from app.schemas.user import UserCreate


class AuthService:
    def __init__(self, db: Session) -> None:
        self.users = UserRepository(db)
        self.tokens = TokenRepository(db)

    def register(self, payload: UserCreate) -> User:
        if self.users.get_by_email(payload.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

        user = User(
            fullname=payload.fullname,
            email=payload.email.lower(),
            hashed_password=get_password_hash(payload.password),
            role=payload.role,
        )
        return self.users.create(user)

    def login(self, email: str, password: str) -> TokenPair:
        user = self.users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")
        return self._issue_token_pair(user)

    def refresh(self, refresh_token: str) -> TokenPair:
        stored_token = self.tokens.get_refresh_token(hash_token(refresh_token))
        if not self._is_refresh_token_valid(stored_token):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        self.tokens.revoke_refresh_token(stored_token)
        return self._issue_token_pair(stored_token.user)

    def logout(self, refresh_token: str) -> None:
        stored_token = self.tokens.get_refresh_token(hash_token(refresh_token))
        if stored_token is not None and stored_token.revoked_at is None:
            self.tokens.revoke_refresh_token(stored_token)

    def forgot_password(self, email: str) -> PasswordResetCreated:
        user = self.users.get_by_email(email)
        if user is None:
            return PasswordResetCreated(message="If the email exists, a password reset link has been generated.")

        raw_token = generate_secure_token()
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(UTC) + timedelta(minutes=settings.password_reset_token_expire_minutes),
        )
        self.tokens.create_password_reset_token(reset_token)

        exposed_token = raw_token if settings.environment in {"local", "test"} else None
        return PasswordResetCreated(
            message="If the email exists, a password reset link has been generated.",
            reset_token=exposed_token,
        )

    def reset_password(self, token: str, new_password: str) -> None:
        stored_token = self.tokens.get_password_reset_token(hash_token(token))
        now = datetime.now(UTC)
        if stored_token is None or stored_token.used_at is not None or self._as_utc(stored_token.expires_at) <= now:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired password reset token")

        self.users.update_password(stored_token.user, get_password_hash(new_password))
        self.tokens.mark_password_reset_used(stored_token)

    def _issue_token_pair(self, user: User) -> TokenPair:
        refresh_token = generate_secure_token()
        stored_token = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
        )
        self.tokens.create_refresh_token(stored_token)
        return TokenPair(access_token=create_access_token(str(user.id)), refresh_token=refresh_token)

    @staticmethod
    def _is_refresh_token_valid(token: RefreshToken | None) -> bool:
        return token is not None and token.revoked_at is None and AuthService._as_utc(token.expires_at) > datetime.now(UTC)

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
