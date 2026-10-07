"""
SQLite database setup for Oryza demo
"""
import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any
import bcrypt
import uuid
from contextlib import contextmanager

# Database file path
DB_PATH = "oryza_demo.db"

# SQL schema
CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    phone TEXT,
    is_active BOOLEAN DEFAULT 1,
    is_verified BOOLEAN DEFAULT 0,
    two_factor_enabled BOOLEAN DEFAULT 0,
    two_factor_secret TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    profile_data TEXT,
    settings_data TEXT
);
"""

CREATE_SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
"""

CREATE_PORTFOLIOS_TABLE = """
CREATE TABLE IF NOT EXISTS portfolios (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    value REAL DEFAULT 0,
    holdings TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
"""

CREATE_TRANSACTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    portfolio_id TEXT,
    type TEXT NOT NULL,
    symbol TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    total_amount REAL NOT NULL,
    status TEXT DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)
);
"""

@contextmanager
def get_db():
    """Get database connection context manager"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Initialize database with tables"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute(CREATE_USERS_TABLE)
        cursor.execute(CREATE_SESSIONS_TABLE)
        cursor.execute(CREATE_PORTFOLIOS_TABLE)
        cursor.execute(CREATE_TRANSACTIONS_TABLE)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);")
        
        conn.commit()
        
        # Insert demo user if not exists
        cursor.execute("SELECT id FROM users WHERE email = ?", ("test@oryza.com",))
        if not cursor.fetchone():
            demo_user_id = str(uuid.uuid4())
            password_hash = bcrypt.hashpw("test@123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            cursor.execute("""
                INSERT INTO users (id, email, username, password_hash, first_name, last_name, phone, is_verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (demo_user_id, "test@oryza.com", "testuser", password_hash, "Test", "User", "+91 98765 43210", 1))
            
            # Create demo portfolio
            portfolio_id = str(uuid.uuid4())
            holdings = json.dumps([
                {"symbol": "RELIANCE", "quantity": 50, "avgPrice": 2350.00, "currentPrice": 2456.50},
                {"symbol": "TCS", "quantity": 25, "avgPrice": 3600.00, "currentPrice": 3567.80},
                {"symbol": "INFY", "quantity": 100, "avgPrice": 1400.00, "currentPrice": 1432.15},
                {"symbol": "HDFC", "quantity": 40, "avgPrice": 1550.00, "currentPrice": 1625.40}
            ])
            
            cursor.execute("""
                INSERT INTO portfolios (id, user_id, name, value, holdings)
                VALUES (?, ?, ?, ?, ?)
            """, (portfolio_id, demo_user_id, "Main Portfolio", 300000, holdings))
            
            conn.commit()

class UserDB:
    """User database operations"""
    
    @staticmethod
    def create_user(email: str, password: str, first_name: str, last_name: str, phone: Optional[str] = None) -> Dict[str, Any]:
        """Create a new user"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                raise ValueError("Email already registered")
            
            # Create user
            user_id = str(uuid.uuid4())
            username = email.split('@')[0] + str(uuid.uuid4())[:4]
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            cursor.execute("""
                INSERT INTO users (id, email, username, password_hash, first_name, last_name, phone)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, email, username, password_hash, first_name, last_name, phone))
            
            # Create default portfolio
            portfolio_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO portfolios (id, user_id, name, value)
                VALUES (?, ?, ?, ?)
            """, (portfolio_id, user_id, "Main Portfolio", 0))
            
            conn.commit()
            
            return {
                "id": user_id,
                "email": email,
                "username": username,
                "firstName": first_name,
                "lastName": last_name,
                "phone": phone
            }
    
    @staticmethod
    def verify_user(email: str, password: str) -> Optional[Dict[str, Any]]:
        """Verify user credentials"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, email, username, password_hash, first_name, last_name, 
                       phone, is_active, is_verified, two_factor_enabled, last_login
                FROM users WHERE email = ?
            """, (email,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Check password
            if not bcrypt.checkpw(password.encode('utf-8'), row['password_hash'].encode('utf-8')):
                return None
            
            if not row['is_active']:
                raise ValueError("Account is deactivated")
            
            # Update last login
            cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", 
                         (datetime.utcnow().isoformat(), row['id']))
            conn.commit()
            
            return {
                "id": row['id'],
                "email": row['email'],
                "username": row['username'],
                "firstName": row['first_name'],
                "lastName": row['last_name'],
                "phone": row['phone'],
                "isActive": row['is_active'],
                "isVerified": row['is_verified'],
                "twoFactorEnabled": row['two_factor_enabled'],
                "lastLogin": row['last_login']
            }
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, email, username, first_name, last_name, phone, 
                       is_active, is_verified, two_factor_enabled, created_at
                FROM users WHERE email = ?
            """, (email,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                "id": row['id'],
                "email": row['email'],
                "username": row['username'],
                "firstName": row['first_name'],
                "lastName": row['last_name'],
                "phone": row['phone'],
                "isActive": row['is_active'],
                "isVerified": row['is_verified'],
                "twoFactorEnabled": row['two_factor_enabled'],
                "createdAt": row['created_at']
            }
    
    @staticmethod
    def update_user_profile(user_id: str, profile_data: Dict[str, Any]) -> bool:
        """Update user profile"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Update basic fields
            if 'personalInfo' in profile_data:
                info = profile_data['personalInfo']
                cursor.execute("""
                    UPDATE users 
                    SET first_name = ?, last_name = ?, phone = ?
                    WHERE id = ?
                """, (info.get('firstName'), info.get('lastName'), 
                     info.get('phone'), user_id))
            
            # Store full profile as JSON
            cursor.execute("""
                UPDATE users SET profile_data = ? WHERE id = ?
            """, (json.dumps(profile_data), user_id))
            
            conn.commit()
            return True
    
    @staticmethod
    def update_user_settings(user_id: str, settings: Dict[str, Any]) -> bool:
        """Update user settings"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users SET settings_data = ? WHERE id = ?
            """, (json.dumps(settings), user_id))
            
            conn.commit()
            return True
    
    @staticmethod
    def get_user_portfolio(user_id: str) -> Dict[str, Any]:
        """Get user's portfolio"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, value, holdings, updated_at
                FROM portfolios WHERE user_id = ?
                ORDER BY created_at DESC LIMIT 1
            """, (user_id,))
            
            row = cursor.fetchone()
            if not row:
                return {
                    "totalValue": 0,
                    "holdings": [],
                    "performance": {"dayChange": 0, "totalReturn": 0}
                }
            
            holdings = json.loads(row['holdings']) if row['holdings'] else []
            
            # Calculate total value
            total_value = sum(h['quantity'] * h['currentPrice'] for h in holdings)
            
            return {
                "id": row['id'],
                "name": row['name'],
                "totalValue": total_value,
                "holdings": holdings,
                "performance": {
                    "dayChange": 2.5,
                    "totalReturn": 12.8
                },
                "updatedAt": row['updated_at']
            }
    
    @staticmethod
    def add_transaction(user_id: str, transaction: Dict[str, Any]) -> bool:
        """Add a transaction"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get user's portfolio
            cursor.execute("SELECT id FROM portfolios WHERE user_id = ? LIMIT 1", (user_id,))
            portfolio = cursor.fetchone()
            if not portfolio:
                return False
            
            transaction_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO transactions (id, user_id, portfolio_id, type, symbol, quantity, price, total_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (transaction_id, user_id, portfolio['id'], transaction['type'], 
                 transaction['symbol'], transaction['quantity'], transaction['price'],
                 transaction['quantity'] * transaction['price']))
            
            conn.commit()
            return True

# Initialize database on module import
init_database() 