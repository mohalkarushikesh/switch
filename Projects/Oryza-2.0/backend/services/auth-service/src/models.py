"""
Authentication Service Models
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from enum import Enum

from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr, Field, ConfigDict, validator
import pyotp

Base = declarative_base()


# Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    ADVISOR = "advisor"
    PREMIUM = "premium"


class AuthProvider(str, Enum):
    LOCAL = "local"
    GOOGLE = "google"
    GITHUB = "github"
    LINKEDIN = "linkedin"


# Database Models
class User(Base):
    __tablename__ = "users"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth users
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    role = Column(SQLEnum(UserRole), default=UserRole.USER)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255))
    email_verified_at = Column(DateTime)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    auth_providers = relationship("UserAuthProvider", back_populates="user")
    sessions = relationship("UserSession", back_populates="user")
    
    def generate_2fa_secret(self) -> str:
        """Generate a new 2FA secret"""
        secret = pyotp.random_base32()
        self.two_factor_secret = secret
        return secret
    
    def get_2fa_uri(self, app_name: str = "Oryza") -> str:
        """Get 2FA QR code URI"""
        if not self.two_factor_secret:
            raise ValueError("2FA secret not set")
        totp = pyotp.TOTP(self.two_factor_secret)
        return totp.provisioning_uri(name=self.email, issuer_name=app_name)
    
    def verify_2fa_token(self, token: str) -> bool:
        """Verify 2FA token"""
        if not self.two_factor_secret:
            return False
        totp = pyotp.TOTP(self.two_factor_secret)
        return totp.verify(token, valid_window=1)


class UserAuthProvider(Base):
    __tablename__ = "user_auth_providers"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    provider = Column(SQLEnum(AuthProvider), nullable=False)
    provider_user_id = Column(String(255), nullable=False)
    provider_email = Column(String(255))
    provider_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="auth_providers")


class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    access_token = Column(String(500), unique=True, nullable=False)
    refresh_token = Column(String(500), unique=True, nullable=False)
    user_agent = Column(String(500))
    ip_address = Column(String(45))
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


# Pydantic Models for API
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v


class UserLogin(BaseModel):
    username: str  # Can be email or username
    password: str
    two_factor_token: Optional[str] = None


class UserOAuthLogin(BaseModel):
    provider: AuthProvider
    code: str
    state: Optional[str] = None


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    email: str
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    role: UserRole
    is_verified: bool
    is_active: bool
    two_factor_enabled: bool
    created_at: datetime
    last_login_at: Optional[datetime]


class TokenData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class Enable2FAResponse(BaseModel):
    secret: str
    qr_code_uri: str
    backup_codes: list[str]


class Verify2FARequest(BaseModel):
    token: str


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_agent: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    last_activity: datetime
    is_current: bool = False 