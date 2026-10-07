"""
Test script to verify database operations
"""
from database import UserDB, init_database

def test_database():
    print("Testing database operations...")
    
    # Test 1: Create a new user
    print("\n1. Testing user registration...")
    try:
        new_user = UserDB.create_user(
            email="newuser@example.com",
            password="password123",
            first_name="New",
            last_name="User",
            phone="+91 12345 67890"
        )
        print(f"✓ User created: {new_user['email']}")
    except ValueError as e:
        print(f"  User already exists: {e}")
    
    # Test 2: Verify login
    print("\n2. Testing user login...")
    user = UserDB.verify_user("test@oryza.com", "test@123")
    if user:
        print(f"✓ Login successful for: {user['email']}")
        print(f"  User ID: {user['id']}")
        print(f"  Name: {user['firstName']} {user['lastName']}")
    else:
        print("✗ Login failed")
    
    # Test 3: Get user portfolio
    print("\n3. Testing portfolio retrieval...")
    if user:
        portfolio = UserDB.get_user_portfolio(user['id'])
        print(f"✓ Portfolio retrieved:")
        print(f"  Total Value: ₹{portfolio['totalValue']:,.2f}")
        print(f"  Holdings: {len(portfolio['holdings'])} stocks")
        for holding in portfolio['holdings']:
            print(f"    - {holding['symbol']}: {holding['quantity']} shares @ ₹{holding['currentPrice']}")
    
    # Test 4: Wrong password
    print("\n4. Testing wrong password...")
    wrong_login = UserDB.verify_user("test@oryza.com", "wrong_password")
    if not wrong_login:
        print("✓ Correctly rejected invalid password")
    
    # Test 5: Non-existent user
    print("\n5. Testing non-existent user...")
    no_user = UserDB.get_user_by_email("notfound@example.com")
    if not no_user:
        print("✓ Correctly returned None for non-existent user")
    
    print("\n✅ All database tests completed!")

if __name__ == "__main__":
    test_database() 