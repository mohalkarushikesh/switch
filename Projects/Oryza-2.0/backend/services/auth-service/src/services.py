"""
Authentication Service - Business Logic
"""
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from .models import (
    User, UserSession, PasswordResetToken, UserAuthProvider,
    UserCreate, UserLogin, UserUpdate, UserResponse,
    TokenData, Enable2FAResponse
)
from .auth import (
    verify_password, get_password_hash, create_token_pair,
    generate_password_reset_token, generate_email_verification_token,
    generate_backup_codes, decode_token, validate_token_type
)
from .email import send_verification_email, send_password_reset_email


class AuthService:
    """Authentication service for user management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if email or username already exists
        existing_user = await self.db.execute(
            select(User).where(
                or_(User.email == user_data.email, User.username == user_data.username)
            )
        )
        if existing_user.scalar_one_or_none():
            if existing_user.scalar_one_or_none().email == user_data.email:
                raise ValueError("Email already registered")
            else:
                raise ValueError("Username already taken")
        
        # Create new user
        user = User(
            id=uuid.uuid4(),
            email=user_data.email,
            username=user_data.username,
            password_hash=get_password_hash(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        # Send verification email
        await self._send_verification_email(user)
        
        return user
    
    async def authenticate_user(self, login_data: UserLogin) -> tuple[User, TokenData]:
        """Authenticate user and return tokens"""
        # Find user by email or username
        user_query = await self.db.execute(
            select(User).where(
                or_(User.email == login_data.username, User.username == login_data.username)
            )
        )
        user = user_query.scalar_one_or_none()
        
        if not user:
            raise ValueError("Invalid credentials")
        
        if not user.is_active:
            raise ValueError("Account is deactivated")
        
        if not verify_password(login_data.password, user.password_hash):
            raise ValueError("Invalid credentials")
        
        # Check 2FA if enabled
        if user.two_factor_enabled:
            if not login_data.two_factor_token:
                raise ValueError("2FA token required")
            
            if not user.verify_2fa_token(login_data.two_factor_token):
                raise ValueError("Invalid 2FA token")
        
        # Create tokens
        tokens = create_token_pair(
            user_id=str(user.id),
            email=user.email,
            role=user.role.value
        )
        
        # Create session
        session = UserSession(
            id=uuid.uuid4(),
            user_id=user.id,
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_at=datetime.utcnow() + timedelta(days=7),
            user_agent=login_data.user_agent if hasattr(login_data, 'user_agent') else None,
            ip_address=login_data.ip_address if hasattr(login_data, 'ip_address') else None
        )
        
        self.db.add(session)
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        
        await self.db.commit()
        
        token_data = TokenData(
            **tokens,
            user=UserResponse.model_validate(user)
        )
        
        return user, token_data
    
    async def refresh_access_token(self, refresh_token: str) -> TokenData:
        """Refresh access token using refresh token"""
        # Validate refresh token
        try:
            payload = validate_token_type(refresh_token, "refresh")
        except ValueError:
            raise ValueError("Invalid refresh token")
        
        # Find session
        session_query = await self.db.execute(
            select(UserSession).where(
                UserSession.refresh_token == refresh_token
            ).options(selectinload(UserSession.user))
        )
        session = session_query.scalar_one_or_none()
        
        if not session or session.is_revoked or session.is_expired:
            raise ValueError("Invalid or expired refresh token")
        
        # Create new tokens
        tokens = create_token_pair(
            user_id=str(session.user.id),
            email=session.user.email,
            role=session.user.role.value
        )
        
        # Update session
        session.access_token = tokens["access_token"]
        session.refresh_token = tokens["refresh_token"]
        session.last_activity = datetime.utcnow()
        
        await self.db.commit()
        
        return TokenData(
            **tokens,
            user=UserResponse.model_validate(session.user)
        )
    
    async def logout(self, access_token: str):
        """Logout user by revoking session"""
        # Find session
        session_query = await self.db.execute(
            select(UserSession).where(
                UserSession.access_token == access_token
            )
        )
        session = session_query.scalar_one_or_none()
        
        if session:
            session.revoked_at = datetime.utcnow()
            await self.db.commit()
    
    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID"""
        user_query = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return user_query.scalar_one_or_none()
    
    async def update_user(self, user_id: uuid.UUID, update_data: UserUpdate) -> User:
        """Update user information"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Update fields
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def change_password(self, user_id: uuid.UUID, current_password: str, new_password: str):
        """Change user password"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        if not verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")
        
        user.password_hash = get_password_hash(new_password)
        await self.db.commit()
    
    async def request_password_reset(self, email: str):
        """Request password reset"""
        user_query = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = user_query.scalar_one_or_none()
        
        if not user:
            # Don't reveal if email exists
            return
        
        # Create reset token
        token = PasswordResetToken(
            id=uuid.uuid4(),
            user_id=user.id,
            token=generate_password_reset_token(),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        self.db.add(token)
        await self.db.commit()
        
        # Send email
        await send_password_reset_email(user.email, token.token)
    
    async def reset_password(self, token: str, new_password: str):
        """Reset password using token"""
        token_query = await self.db.execute(
            select(PasswordResetToken).where(
                and_(
                    PasswordResetToken.token == token,
                    PasswordResetToken.used_at.is_(None),
                    PasswordResetToken.expires_at > datetime.utcnow()
                )
            ).options(selectinload(PasswordResetToken.user))
        )
        reset_token = token_query.scalar_one_or_none()
        
        if not reset_token:
            raise ValueError("Invalid or expired reset token")
        
        # Update password
        user = await self.get_user_by_id(reset_token.user_id)
        user.password_hash = get_password_hash(new_password)
        
        # Mark token as used
        reset_token.used_at = datetime.utcnow()
        
        await self.db.commit()
    
    async def enable_2fa(self, user_id: uuid.UUID) -> Enable2FAResponse:
        """Enable 2FA for user"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        if user.two_factor_enabled:
            raise ValueError("2FA is already enabled")
        
        # Generate secret and backup codes
        secret = user.generate_2fa_secret()
        backup_codes = generate_backup_codes()
        
        # Store backup codes (you might want to hash these)
        # For now, we'll just enable 2FA
        user.two_factor_enabled = True
        
        await self.db.commit()
        
        return Enable2FAResponse(
            secret=secret,
            qr_code_uri=user.get_2fa_uri(),
            backup_codes=backup_codes
        )
    
    async def disable_2fa(self, user_id: uuid.UUID, password: str):
        """Disable 2FA for user"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        if not verify_password(password, user.password_hash):
            raise ValueError("Invalid password")
        
        user.two_factor_enabled = False
        user.two_factor_secret = None
        
        await self.db.commit()
    
    async def get_user_sessions(self, user_id: uuid.UUID) -> List[UserSession]:
        """Get all active sessions for user"""
        sessions_query = await self.db.execute(
            select(UserSession).where(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.revoked_at.is_(None),
                    UserSession.expires_at > datetime.utcnow()
                )
            ).order_by(UserSession.created_at.desc())
        )
        return sessions_query.scalars().all()
    
    async def revoke_session(self, user_id: uuid.UUID, session_id: uuid.UUID):
        """Revoke a specific session"""
        session_query = await self.db.execute(
            select(UserSession).where(
                and_(
                    UserSession.id == session_id,
                    UserSession.user_id == user_id
                )
            )
        )
        session = session_query.scalar_one_or_none()
        
        if session:
            session.revoked_at = datetime.utcnow()
            await self.db.commit()
    
    async def revoke_all_sessions(self, user_id: uuid.UUID, except_current: Optional[str] = None):
        """Revoke all sessions except current"""
        query = select(UserSession).where(
            and_(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None)
            )
        )
        
        if except_current:
            query = query.where(UserSession.access_token != except_current)
        
        sessions_query = await self.db.execute(query)
        sessions = sessions_query.scalars().all()
        
        for session in sessions:
            session.revoked_at = datetime.utcnow()
        
        await self.db.commit()
    
    async def verify_email(self, token: str):
        """Verify user email"""
        # This would involve checking an email verification token
        # For now, simplified implementation
        pass
    
    async def _send_verification_email(self, user: User):
        """Send email verification"""
        token = generate_email_verification_token()
        # Store token and send email
        await send_verification_email(user.email, token) 