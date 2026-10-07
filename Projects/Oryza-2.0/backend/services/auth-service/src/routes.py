"""
Authentication API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import JSONResponse
from typing import List

from .models import (
    UserCreate, UserLogin, UserResponse, TokenData,
    RefreshTokenRequest, ChangePasswordRequest,
    ForgotPasswordRequest, ResetPasswordRequest,
    Enable2FAResponse, Verify2FARequest, SessionResponse,
    UserUpdate, UserOAuthLogin
)
from .dependencies import (
    get_auth_service, CurrentUser, VerifiedUser,
    AdminUser, OptionalUser
)
from .services import AuthService


router = APIRouter()


@router.post("/register", response_model=TokenData, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user"""
    try:
        user = await auth_service.create_user(user_data)
        _, token_data = await auth_service.authenticate_user(
            UserLogin(username=user.email, password=user_data.password)
        )
        return token_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenData)
async def login(
    request: Request,
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login user and return tokens"""
    # Add user agent and IP for session tracking
    login_data.user_agent = request.headers.get("User-Agent")
    login_data.ip_address = request.client.host if request.client else None
    
    try:
        user, token_data = await auth_service.authenticate_user(login_data)
        return token_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/refresh", response_model=TokenData)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Refresh access token"""
    try:
        token_data = await auth_service.refresh_access_token(refresh_data.refresh_token)
        return token_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Logout current session"""
    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        await auth_service.logout(token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: CurrentUser):
    """Get current user profile"""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_profile(
    update_data: UserUpdate,
    current_user: CurrentUser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Update current user profile"""
    try:
        user = await auth_service.update_user(current_user.id, update_data)
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: CurrentUser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Change user password"""
    try:
        await auth_service.change_password(
            current_user.id,
            password_data.current_password,
            password_data.new_password
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
async def forgot_password(
    forgot_data: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Request password reset"""
    await auth_service.request_password_reset(forgot_data.email)
    # Always return success to prevent email enumeration
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    reset_data: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Reset password with token"""
    try:
        await auth_service.reset_password(reset_data.token, reset_data.new_password)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/2fa/enable", response_model=Enable2FAResponse)
async def enable_2fa(
    current_user: VerifiedUser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Enable 2FA for current user"""
    try:
        return await auth_service.enable_2fa(current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/2fa/verify", status_code=status.HTTP_204_NO_CONTENT)
async def verify_2fa(
    verify_data: Verify2FARequest,
    current_user: CurrentUser
):
    """Verify 2FA token"""
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled"
        )
    
    if not current_user.verify_2fa_token(verify_data.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 2FA token"
        )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/2fa/disable", status_code=status.HTTP_204_NO_CONTENT)
async def disable_2fa(
    password: str,
    current_user: CurrentUser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Disable 2FA for current user"""
    try:
        await auth_service.disable_2fa(current_user.id, password)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/sessions", response_model=List[SessionResponse])
async def get_sessions(
    current_user: CurrentUser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get all active sessions for current user"""
    sessions = await auth_service.get_user_sessions(current_user.id)
    return [SessionResponse.model_validate(session) for session in sessions]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    session_id: str,
    current_user: CurrentUser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Revoke a specific session"""
    await auth_service.revoke_session(current_user.id, session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/sessions/revoke-all", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_all_sessions(
    request: Request,
    current_user: CurrentUser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Revoke all sessions except current"""
    authorization = request.headers.get("Authorization", "")
    current_token = None
    if authorization.startswith("Bearer "):
        current_token = authorization.split(" ")[1]
    
    await auth_service.revoke_all_sessions(current_user.id, except_current=current_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/verify-email/{token}", status_code=status.HTTP_204_NO_CONTENT)
async def verify_email(
    token: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Verify email with token"""
    try:
        await auth_service.verify_email(token)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# OAuth routes (simplified for now)
@router.post("/oauth/{provider}/login", response_model=TokenData)
async def oauth_login(
    provider: str,
    oauth_data: UserOAuthLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """OAuth login"""
    # This would integrate with actual OAuth providers
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="OAuth login not implemented yet"
    )


# Admin routes
@router.get("/admin/users", response_model=List[UserResponse])
async def list_users(
    admin_user: AdminUser,
    auth_service: AuthService = Depends(get_auth_service),
    skip: int = 0,
    limit: int = 100
):
    """List all users (admin only)"""
    # This would implement pagination and filtering
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User listing not implemented yet"
    )


@router.delete("/admin/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    admin_user: AdminUser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Delete a user (admin only)"""
    # This would implement user deletion
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User deletion not implemented yet"
    ) 