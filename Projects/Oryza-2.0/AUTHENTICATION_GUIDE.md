# Authentication & User Management Guide

## Overview
The Oryza platform now features a complete authentication system with SQLite database storage for user registration, login, and data persistence.

---

## 🔐 Features Implemented

### 1. **User Registration**
- New users can register with email, password, and personal details
- Passwords are securely hashed using bcrypt
- Each user gets a unique ID and username
- Default portfolio created for new users

### 2. **User Login**
- Email and password authentication
- JWT token generation for session management
- Last login timestamp tracking
- Invalid credentials properly handled

### 3. **Data Persistence**
- SQLite database stores all user information
- User profiles and settings saved to database
- Portfolio and transaction history maintained
- All data persists between sessions

### 4. **Security Features**
- Bcrypt password hashing (salt rounds: 12)
- JWT tokens with 30-minute expiration
- Secure password change with current password verification
- Account deactivation support

---

## 📁 Database Schema

### Users Table
```sql
- id (UUID)
- email (unique)
- username (unique) 
- password_hash
- first_name
- last_name
- phone
- is_active
- is_verified
- two_factor_enabled
- created_at
- last_login
- profile_data (JSON)
- settings_data (JSON)
```

### Portfolios Table
```sql
- id (UUID)
- user_id (FK)
- name
- value
- holdings (JSON)
- created_at
- updated_at
```

### Transactions Table
```sql
- id (UUID)
- user_id (FK)
- portfolio_id (FK)
- type (buy/sell)
- symbol
- quantity
- price
- total_amount
- status
- created_at
```

---

## 🚀 Setup Instructions

### 1. Install Dependencies
```bash
cd backend
pip install bcrypt PyJWT
```

Or run the setup script:
```bash
backend\setup_auth.bat
```

### 2. Database Location
The SQLite database file `oryza_demo.db` is created automatically in the backend directory.

### 3. Test Credentials
- **Email**: test@oryza.com
- **Password**: test@123

---

## 🔧 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/change-password` - Change password

### Profile Management
- `GET /api/v1/profile` - Get user profile
- `PUT /api/v1/profile` - Update profile
- `GET /api/v1/profile/download-data` - Download user data
- `DELETE /api/v1/profile/delete` - Delete account

### Settings
- `GET /api/v1/settings` - Get user settings
- `PUT /api/v1/settings` - Update settings

---

## 💻 Usage Examples

### Register New User
```javascript
const response = await fetch('http://localhost:8889/api/v1/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'securepassword',
    firstName: 'John',
    lastName: 'Doe'
  })
});

const { access_token, user } = await response.json();
```

### Login
```javascript
const response = await fetch('http://localhost:8889/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'securepassword'
  })
});

const { access_token } = await response.json();
```

### Authenticated Requests
```javascript
const response = await fetch('http://localhost:8889/api/v1/portfolio', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});
```

---

## 🔍 Testing the System

Run the test script to verify everything is working:
```bash
cd backend
python test_database.py
```

Expected output:
```
Testing database operations...

1. Testing user registration...
✓ User created: newuser@example.com

2. Testing user login...
✓ Login successful for: test@oryza.com
  User ID: [uuid]
  Name: Test User

3. Testing portfolio retrieval...
✓ Portfolio retrieved:
  Total Value: ₹300,000.00
  Holdings: 4 stocks

4. Testing wrong password...
✓ Correctly rejected invalid password

5. Testing non-existent user...
✓ Correctly returned None for non-existent user

✅ All database tests completed!
```

---

## 🛡️ Security Considerations

1. **Password Requirements**
   - Minimum 8 characters
   - Stored as bcrypt hash, never plain text

2. **Token Security**
   - JWT tokens expire after 30 minutes
   - Tokens contain minimal user information
   - Secret key should be environment variable in production

3. **Database Security**
   - SQL injection protection via parameterized queries
   - User input validation
   - Proper error handling without exposing sensitive info

---

## 📊 Data Migration

If you have existing mock users, they won't be migrated automatically. New users must register through the proper flow. The demo user (test@oryza.com) is created automatically.

---

## 🚧 Future Enhancements

- Email verification
- Password reset via email
- Two-factor authentication (2FA)
- OAuth integration (Google, GitHub)
- Session management
- Rate limiting
- Audit logs

---

## ❓ Troubleshooting

### "Email already registered" error
- The email is already in the database
- Use a different email or login with existing credentials

### "Invalid credentials" error
- Check email and password are correct
- Ensure the user has registered
- Password is case-sensitive

### Database not found
- Run the backend server once to create the database
- Check file permissions in the backend directory

### Token expired
- Login again to get a new token
- Implement token refresh in the frontend 