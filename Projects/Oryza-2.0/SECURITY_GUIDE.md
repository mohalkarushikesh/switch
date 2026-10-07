# Oryza Platform Security Guide

## Overview

This guide outlines the security measures implemented in the Oryza platform and best practices for deployment.

## Security Features Implemented

### 1. Authentication & Authorization

- **JWT-based authentication** with expiring tokens
- **Secure password handling** (hashed, never stored in plain text)
- **Role-based access control** (RBAC) ready
- **Session management** with automatic expiry

### 2. API Security

- **CORS configuration** restricting origins
- **Rate limiting** to prevent abuse
- **Request validation** using Pydantic models
- **SQL injection prevention** through parameterized queries
- **XSS protection** via content sanitization

### 3. Data Protection

- **Encryption at rest** (database level)
- **Encryption in transit** (HTTPS in production)
- **Sensitive data masking** in logs
- **PII data protection** compliance

### 4. Infrastructure Security

- **Environment variables** for secrets
- **No hardcoded credentials**
- **Secure WebSocket connections**
- **Docker security best practices**

## Production Deployment Checklist

### 1. Environment Configuration

```bash
# Never commit these to version control
SECRET_KEY=<generate-strong-random-key>
DATABASE_URL=<use-connection-pooling>
REDIS_URL=<use-ssl-connection>
```

### 2. HTTPS Configuration

```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

### 3. Database Security

```sql
-- Create read-only user for analytics
CREATE USER 'oryza_read'@'%' IDENTIFIED BY 'strong_password';
GRANT SELECT ON oryza.* TO 'oryza_read'@'%';

-- Enable audit logging
SET GLOBAL general_log = 'ON';
```

### 4. API Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60 per minute"]
)

@app.get("/api/v1/portfolio")
@limiter.limit("120 per minute")
async def get_portfolio():
    pass
```

### 5. Input Validation

```python
from pydantic import BaseModel, validator

class OrderRequest(BaseModel):
    symbol: str
    quantity: float
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if not v.isalnum():
            raise ValueError('Invalid symbol')
        return v.upper()
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0 or v > 10000:
            raise ValueError('Invalid quantity')
        return v
```

## Security Headers

Add these headers to all responses:

```python
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

## Monitoring & Logging

### 1. Security Events to Log

- Failed login attempts
- Unusual trading patterns
- API rate limit violations
- Database query anomalies
- WebSocket connection issues

### 2. Alerting Rules

```python
# Alert on multiple failed logins
if failed_login_count > 5:
    send_security_alert("Multiple failed login attempts", user_email)

# Alert on large transactions
if transaction_amount > user.daily_limit:
    send_security_alert("Large transaction attempted", transaction_details)
```

### 3. Audit Trail

```python
@app.middleware("http")
async def audit_trail(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    
    audit_log = {
        "timestamp": datetime.now().isoformat(),
        "user_id": get_user_id(request),
        "endpoint": request.url.path,
        "method": request.method,
        "status_code": response.status_code,
        "response_time": time.time() - start_time
    }
    
    await save_audit_log(audit_log)
    return response
```

## Vulnerability Management

### 1. Dependency Scanning

```bash
# Python dependencies
pip install safety
safety check

# JavaScript dependencies
npm audit
npm audit fix
```

### 2. Code Scanning

```bash
# Python security scanning
pip install bandit
bandit -r backend/

# JavaScript security scanning
npm install -g eslint-plugin-security
eslint --ext .js,.jsx,.ts,.tsx frontend/
```

### 3. Container Scanning

```bash
# Scan Docker images
docker scan oryza-backend:latest
docker scan oryza-frontend:latest
```

## Incident Response Plan

### 1. Detection
- Monitor logs for anomalies
- Set up alerts for security events
- Regular security audits

### 2. Response
- Isolate affected systems
- Revoke compromised tokens
- Patch vulnerabilities
- Notify affected users

### 3. Recovery
- Restore from secure backups
- Update security measures
- Document lessons learned

## Compliance Considerations

### 1. Data Privacy (GDPR/CCPA)
- User consent for data collection
- Right to data deletion
- Data portability
- Privacy policy implementation

### 2. Financial Regulations
- KYC/AML compliance
- Transaction monitoring
- Regulatory reporting
- Data retention policies

### 3. Security Standards
- ISO 27001 alignment
- OWASP Top 10 mitigation
- PCI DSS for payments
- SOC 2 compliance ready

## Security Testing

### 1. Penetration Testing
```bash
# API security testing
python3 -m pytest tests/security/test_api_security.py

# Frontend security testing
npm run test:security
```

### 2. Load Testing
```bash
# Test rate limiting
locust -f tests/load/rate_limit_test.py

# Test DDoS protection
hping3 -S -p 443 --flood oryza.ai
```

## Backup & Recovery

### 1. Database Backups
```bash
# Automated daily backups
0 2 * * * pg_dump oryza > /backup/oryza_$(date +\%Y\%m\%d).sql

# Encrypted backup storage
gpg --encrypt --recipient backup@oryza.ai oryza_backup.sql
```

### 2. Disaster Recovery
- Multi-region deployment
- Automated failover
- Regular recovery drills
- <30 minute RTO

## Security Contacts

- Security Team: security@oryza.ai
- Bug Bounty: bugbounty@oryza.ai
- Emergency: +91-XXXXXXXXXX

## Regular Security Tasks

### Daily
- [ ] Review security alerts
- [ ] Check failed login attempts
- [ ] Monitor API rate limits

### Weekly
- [ ] Review access logs
- [ ] Update security patches
- [ ] Scan for vulnerabilities

### Monthly
- [ ] Security audit
- [ ] Penetration testing
- [ ] Update security documentation

### Quarterly
- [ ] Full security review
- [ ] Compliance audit
- [ ] Disaster recovery drill

---

**Remember**: Security is not a one-time task but an ongoing process. Stay vigilant and keep the platform secure! 