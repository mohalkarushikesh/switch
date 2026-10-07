# Oryza Authentication Service

## Overview
The Authentication Service handles user registration, login, session management, and authorization for the Oryza platform.

## Features
- User registration and login
- JWT-based authentication (access & refresh tokens)
- Two-factor authentication (2FA) support
- Password reset via email
- Email verification
- Session management
- Role-based access control (RBAC)
- OAuth integration (Google, Facebook - coming soon)

## Requirements
- Python 3.11+
- PostgreSQL 15+
- Redis (optional, for session storage)

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Variables
Copy `env.example` to `.env` and update the values:
```bash
cp env.example .env
```

### 3. Database Setup
Make sure PostgreSQL is running and the database is created:
```sql
CREATE DATABASE oryza_db;
```

Run migrations:
```bash
alembic upgrade head
```

### 4. Run the Service
```bash
python -m src.main
```

Or with uvicorn:
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout current session

### User Profile
- `GET /api/v1/auth/me` - Get current user profile
- `PUT /api/v1/auth/me` - Update user profile

### Password Management
- `POST /api/v1/auth/change-password` - Change password
- `POST /api/v1/auth/forgot-password` - Request password reset
- `POST /api/v1/auth/reset-password` - Reset password with token

### Two-Factor Authentication
- `POST /api/v1/auth/2fa/enable` - Enable 2FA
- `POST /api/v1/auth/2fa/verify` - Verify 2FA token
- `POST /api/v1/auth/2fa/disable` - Disable 2FA

### Session Management
- `GET /api/v1/auth/sessions` - Get all active sessions
- `DELETE /api/v1/auth/sessions/{id}` - Revoke specific session
- `POST /api/v1/auth/sessions/revoke-all` - Revoke all sessions

### Email Verification
- `POST /api/v1/auth/verify-email/{token}` - Verify email address

## Docker

### Build
```bash
docker build -t oryza-auth-service .
```

### Run
```bash
docker run -p 8001:8001 --env-file .env oryza-auth-service
```

## Testing
```bash
pytest tests/
```

## API Documentation
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## Security Features
- Password hashing with bcrypt
- JWT tokens with expiration
- Rate limiting on sensitive endpoints
- Email verification for new accounts
- 2FA support with TOTP
- Session tracking and management
- CORS configuration

## User Roles
- `USER` - Default role for regular users
- `PREMIUM` - Premium users with additional features
- `ADVISOR` - Financial advisors with special permissions
- `ADMIN` - System administrators with full access

## Error Handling
The service returns standardized error responses:
```json
{
  "detail": "Error message",
  "type": "error_type"
}
```

## Development
For development with auto-reload:
```bash
ENV=development uvicorn src.main:app --reload
``` 