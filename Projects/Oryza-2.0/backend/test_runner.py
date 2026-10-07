"""
Test runner for Oryza services
Runs services with SQLite and mock data instead of external dependencies
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from test_config import SERVICE_PORTS, DATABASE_URL, USE_MOCK_DATA

def set_test_environment():
    """Set environment variables for testing"""
    # Override database URL to use SQLite
    os.environ["DATABASE_URL"] = DATABASE_URL
    
    # Disable Redis
    os.environ["REDIS_URL"] = ""
    os.environ["USE_MEMORY_CACHE"] = "true"
    
    # Enable mock data
    os.environ["USE_MOCK_DATA"] = "true"
    os.environ["APP_ENV"] = "test"
    
    # Disable external APIs
    os.environ["DISABLE_EXTERNAL_APIS"] = "true"
    
    print(f"✅ Test environment configured")
    print(f"   Database: {DATABASE_URL}")
    print(f"   Mock data: Enabled")
    print(f"   External APIs: Disabled")

def run_service(service_name):
    """Run a specific service"""
    if service_name not in SERVICE_PORTS:
        print(f"❌ Unknown service: {service_name}")
        print(f"Available services: {', '.join(SERVICE_PORTS.keys())}")
        return
    
    port = SERVICE_PORTS[service_name]
    service_dir = Path(__file__).parent / "services" / service_name
    
    if not service_dir.exists():
        print(f"❌ Service directory not found: {service_dir}")
        return
    
    # Set test environment
    set_test_environment()
    
    print(f"\n🚀 Starting {service_name} on port {port}...")
    print("=" * 50)
    
    # Change to service directory
    os.chdir(service_dir)
    
    # Run the service
    cmd = [
        sys.executable,
        "-m", "uvicorn",
        "src.main:app",
        "--host", "0.0.0.0",
        "--port", str(port),
        "--reload"
    ]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print(f"\n✅ {service_name} stopped")

def run_minimal_test():
    """Run a minimal test of core services"""
    print("🧪 Running minimal test setup...")
    
    # First, ensure test environment is set up
    setup_script = Path(__file__).parent / "setup_test_environment.py"
    if setup_script.exists():
        print("Setting up test database and mock data...")
        subprocess.run([sys.executable, str(setup_script)])
    
    # Test a simple service
    print("\n📊 Testing Advisory Engine...")
    
    # Import and test basic functionality
    set_test_environment()
    
    try:
        # Test database connection with SQLite
        import sqlite3
        db_path = DATABASE_URL.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"✅ Database tables: {[t[0] for t in tables]}")
        
        # Check users
        cursor.execute("SELECT COUNT(*) FROM users;")
        user_count = cursor.fetchone()[0]
        print(f"✅ Test users: {user_count}")
        
        conn.close()
        
        # Test mock data
        from test_config import MOCK_DATA_SOURCES
        for name, path in MOCK_DATA_SOURCES.items():
            if path.exists():
                print(f"✅ Mock data found: {name}")
            else:
                print(f"❌ Mock data missing: {name}")
        
        print("\n✅ Basic test passed! You can now run individual services.")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run Oryza services in test mode")
    parser.add_argument("service", nargs="?", help="Service name to run")
    parser.add_argument("--list", action="store_true", help="List available services")
    parser.add_argument("--test", action="store_true", help="Run minimal test")
    
    args = parser.parse_args()
    
    if args.list:
        print("Available services:")
        for service, port in SERVICE_PORTS.items():
            print(f"  - {service:<25} (port {port})")
    elif args.test:
        run_minimal_test()
    elif args.service:
        run_service(args.service)
    else:
        print("Oryza Test Runner")
        print("=" * 50)
        print("\nUsage:")
        print("  python test_runner.py --test           # Run minimal test")
        print("  python test_runner.py --list           # List services")
        print("  python test_runner.py <service-name>   # Run a service")
        print("\nExample:")
        print("  python test_runner.py advisory-engine")

if __name__ == "__main__":
    main() 