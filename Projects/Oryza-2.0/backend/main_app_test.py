"""
Oryza Main Application - Test Version
Launches simplified services that work with SQLite and mock data
"""
import asyncio
import subprocess
import sys
import os
from pathlib import Path
import signal
from typing import List, Dict
import time
import threading

# Set test environment variables
os.environ["USE_MOCK_DATA"] = "true"
os.environ["USE_MEMORY_CACHE"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///backend/test_oryza.db"
os.environ["DISABLE_EXTERNAL_APIS"] = "true"
os.environ["APP_ENV"] = "test"

# Services that are test-ready
TEST_READY_SERVICES = {
    "web-interface": {
        "name": "Web Dashboard",
        "port": 8080,
        "script": "web_interface.py",
        "description": "Main web interface"
    },
    "simple-api": {
        "name": "Simple Test API",
        "port": 8889,  # Changed from 8888 to avoid conflicts
        "script": "simple_test_api.py",
        "description": "Basic API with mock data",
        "args": ["--port", "8889"]  # Pass custom port
    }
}

class TestApplication:
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.running = False
        
    def check_port(self, port: int) -> bool:
        """Check if a port is available"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                return result != 0  # True if port is available
        except:
            return False
            
    def output_reader(self, proc, service_name):
        """Read output from subprocess"""
        try:
            for line in iter(proc.stdout.readline, ''):
                if line:
                    print(f"[{service_name}] {line.strip()}")
                    
            for line in iter(proc.stderr.readline, ''):
                if line:
                    print(f"[{service_name} ERROR] {line.strip()}")
        except:
            pass
        
    def start_service(self, service_id: str, service_info: dict):
        """Start a single service"""
        port = service_info['port']
        
        # Check if port is available
        if not self.check_port(port):
            print(f"❌ Port {port} is already in use. Please free the port or change it.")
            print(f"   You can check what's using port {port} with:")
            print(f"   netstat -an | findstr {port}")
            return
            
        print(f"🚀 Starting {service_info['name']} on port {port}...")
        
        # Build command
        cmd = [sys.executable, service_info['script']]
        if 'args' in service_info:
            cmd.extend(service_info['args'])
        
        try:
            # For simple_test_api, modify the port in the script temporarily
            if service_id == "simple-api":
                # Run with modified port
                process = subprocess.Popen(
                    [sys.executable, "-c", f"""
import sys
sys.path.insert(0, '.')
# Modify the port
import simple_test_api
simple_test_api.uvicorn.run(simple_test_api.app, host="0.0.0.0", port={port})
"""],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
            else:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
            
            self.processes[service_id] = process
            
            # Start output readers in separate threads
            threading.Thread(
                target=self.output_reader,
                args=(process, service_info['name']),
                daemon=True
            ).start()
            
            # Give service time to start
            time.sleep(2)
            
            # Check if process is still running
            if process.poll() is None:
                print(f"✅ {service_info['name']} started successfully (PID: {process.pid})")
            else:
                print(f"❌ {service_info['name']} failed to start")
                # Read any error output
                stdout, stderr = process.communicate()
                if stdout:
                    print(f"Output: {stdout}")
                if stderr:
                    print(f"Error: {stderr}")
            
        except Exception as e:
            print(f"❌ Failed to start {service_info['name']}: {str(e)}")
            
    def stop_all_services(self):
        """Stop all running services"""
        print("\n🛑 Stopping all services...")
        
        for service_id, process in self.processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ Stopped {TEST_READY_SERVICES[service_id]['name']}")
            except:
                process.kill()
                
        self.processes.clear()
        
    def run(self):
        """Run the main application"""
        print("=" * 60)
        print("🏗️  Oryza Platform - Test Environment")
        print("=" * 60)
        print("\n📋 Available Services:")
        
        for service_id, info in TEST_READY_SERVICES.items():
            print(f"  - {info['name']}: http://localhost:{info['port']}")
            print(f"    {info['description']}")
            
        print("\n🚀 Starting services...\n")
        
        # Start all test-ready services
        for service_id, service_info in TEST_READY_SERVICES.items():
            self.start_service(service_id, service_info)
            
        print("\n" + "=" * 60)
        
        # Check how many services started successfully
        running_count = sum(1 for p in self.processes.values() if p.poll() is None)
        
        if running_count == 0:
            print("❌ No services started successfully!")
            print("\nCommon issues:")
            print("1. Ports already in use - kill existing processes")
            print("2. Missing dependencies - check error messages above")
            return
        else:
            print(f"✅ {running_count} services started successfully!")
            
        print("=" * 60)
        print("\n📌 Main Dashboard: http://localhost:8080/")
        print("📌 Service URLs:")
        print("  - Web Interface: http://localhost:8080/")
        print("  - Test API: http://localhost:8889/")
        print("  - API Docs: http://localhost:8889/docs")
        print("\n⚡ Press Ctrl+C to stop all services")
        print("=" * 60)
        
        # Keep running until interrupted
        try:
            self.running = True
            while self.running:
                # Check if any process has died
                for service_id, process in list(self.processes.items()):
                    if process.poll() is not None:
                        print(f"\n⚠️  {TEST_READY_SERVICES[service_id]['name']} stopped unexpectedly (exit code: {process.poll()})")
                        del self.processes[service_id]
                        
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n👋 Shutting down Oryza...")
            self.stop_all_services()
            print("\n✅ Oryza stopped successfully")
            
def main():
    """Main entry point"""
    # Check if we're in the backend directory
    if not Path("simple_test_api.py").exists():
        print("❌ Please run this script from the backend directory:")
        print("   cd backend")
        print("   python main_app_test.py")
        return
        
    # Check if test environment is set up
    if not Path("test_oryza.db").exists():
        print("❌ Test database not found. Please run setup first:")
        print("   python setup_test_environment.py")
        return
        
    # Run the application
    app = TestApplication()
    app.run()

if __name__ == "__main__":
    main() 