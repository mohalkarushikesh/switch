"""
Oryza Platform - Interactive Demo Walkthrough
This script demonstrates the key features of the test environment
"""
import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class OryazDemo:
    def __init__(self):
        self.api_base = "http://localhost:8889"
        self.web_base = "http://localhost:8080"
        
    def print_section(self, title: str):
        """Print a formatted section header"""
        print("\n" + "="*60)
        print(f"🎯 {title}")
        print("="*60)
        
    def check_services(self):
        """Check if services are running"""
        self.print_section("Checking Platform Status")
        
        services = [
            ("Web Dashboard", self.web_base),
            ("Test API", self.api_base),
        ]
        
        all_good = True
        for name, url in services:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    print(f"✅ {name} is running at {url}")
                else:
                    print(f"❌ {name} returned status {response.status_code}")
                    all_good = False
            except:
                print(f"❌ {name} is not responding at {url}")
                all_good = False
                
        if not all_good:
            print("\n⚠️  Please start the services first:")
            print("   cd backend")
            print("   python main_app_test.py")
            return False
            
        return True
        
    def show_stocks(self):
        """Demo: View stock prices"""
        self.print_section("Stock Market Data")
        
        try:
            response = requests.get(f"{self.api_base}/stocks")
            data = response.json()
            
            print("\n📊 Current Stock Prices:\n")
            print(f"{'Symbol':<8} {'Company':<25} {'Price':>10} {'Change':>10}")
            print("-" * 55)
            
            for stock in data['stocks'][:5]:
                change_sign = "+" if stock['change'] >= 0 else ""
                print(f"{stock['symbol']:<8} {stock['name']:<25} ${stock['price']:>9.2f} {change_sign}{stock['change']:>9.2f}%")
                
        except Exception as e:
            print(f"Error fetching stocks: {e}")
            
    def show_news(self):
        """Demo: View news with sentiment"""
        self.print_section("Financial News & Sentiment")
        
        try:
            response = requests.get(f"{self.api_base}/news")
            data = response.json()
            
            print("\n📰 Latest News:\n")
            
            for item in data['news'][:3]:
                sentiment_emoji = {
                    "positive": "📈",
                    "negative": "📉",
                    "neutral": "➖"
                }.get(item['sentiment'], "❓")
                
                print(f"{sentiment_emoji} {item['title']}")
                print(f"   Source: {item['source']} | Sentiment: {item['sentiment'].upper()}")
                print(f"   {item['summary']}")
                print()
                
        except Exception as e:
            print(f"Error fetching news: {e}")
            
    def show_market_overview(self):
        """Demo: Market indices and sectors"""
        self.print_section("Market Overview")
        
        try:
            response = requests.get(f"{self.api_base}/market")
            data = response.json()
            
            print("\n📈 Market Indices:\n")
            indices = data['indices']
            
            for index, info in indices.items():
                change_sign = "+" if info['change_percent'] >= 0 else ""
                print(f"{index:<10} {info['value']:>10.2f} {change_sign}{info['change_percent']*100:>6.2f}%")
                
            print("\n🏢 Sector Performance:\n")
            for sector, info in data['sectors'].items():
                change = info['change']
                bar = "█" * int(abs(change) * 5)
                color = "🟢" if change >= 0 else "🔴"
                print(f"{color} {sector:<15} {change:>6.2f}% {bar}")
                
        except Exception as e:
            print(f"Error fetching market data: {e}")
            
    def test_database(self):
        """Demo: Database status"""
        self.print_section("Database Status")
        
        try:
            response = requests.get(f"{self.api_base}/test-db")
            data = response.json()
            
            print(f"\n🗄️  Database: {data['database']}")
            print(f"📁 Location: {data['path']}")
            print(f"👥 Test Users: {data['user_count']}")
            print(f"\n📊 Tables:")
            for table in data['tables']:
                print(f"   - {table}")
                
        except Exception as e:
            print(f"Error checking database: {e}")
            
    def simulate_portfolio_analysis(self):
        """Demo: Simulate portfolio analysis"""
        self.print_section("Portfolio Analysis Simulation")
        
        print("\n🤖 Analyzing portfolio for: Test User")
        print("💼 Portfolio Value: $50,000")
        print("📊 Holdings: AAPL (30%), MSFT (25%), GOOGL (20%), Cash (25%)")
        
        time.sleep(1)  # Simulate processing
        
        print("\n📈 Analysis Results:")
        print("   • Risk Score: 5.2/10 (Moderate)")
        print("   • Expected Return: 12.5% annually")
        print("   • Sharpe Ratio: 1.34")
        
        print("\n💡 Recommendations:")
        print("   1. Consider diversifying into international markets")
        print("   2. Your tech allocation is high (75%), consider rebalancing")
        print("   3. Add defensive stocks for market downturns")
        
    def interactive_menu(self):
        """Interactive menu for exploration"""
        while True:
            self.print_section("Oryza Platform Demo Menu")
            print("\n1. 📊 View Stock Prices")
            print("2. 📰 Check Financial News")
            print("3. 📈 Market Overview")
            print("4. 🗄️  Database Status")
            print("5. 💼 Portfolio Analysis (Simulation)")
            print("6. 🌐 Open Web Dashboard")
            print("7. 📚 API Documentation")
            print("8. 🔄 Run All Demos")
            print("9. ❌ Exit")
            
            choice = input("\nSelect an option (1-9): ").strip()
            
            if choice == "1":
                self.show_stocks()
            elif choice == "2":
                self.show_news()
            elif choice == "3":
                self.show_market_overview()
            elif choice == "4":
                self.test_database()
            elif choice == "5":
                self.simulate_portfolio_analysis()
            elif choice == "6":
                print(f"\n🌐 Opening {self.web_base} in your browser...")
                import webbrowser
                webbrowser.open(self.web_base)
            elif choice == "7":
                print(f"\n📚 Opening API docs at {self.api_base}/docs...")
                import webbrowser
                webbrowser.open(f"{self.api_base}/docs")
            elif choice == "8":
                self.run_all_demos()
            elif choice == "9":
                print("\n👋 Thanks for exploring Oryza!")
                break
            else:
                print("\n❌ Invalid choice. Please try again.")
                
            if choice != "9":
                input("\nPress Enter to continue...")
                
    def run_all_demos(self):
        """Run all demos in sequence"""
        demos = [
            self.show_stocks,
            self.show_news,
            self.show_market_overview,
            self.test_database,
            self.simulate_portfolio_analysis
        ]
        
        for demo in demos:
            demo()
            time.sleep(2)
            
def main():
    print("🏦 Welcome to Oryza Financial Platform Demo!")
    print("=" * 60)
    
    demo = OryazDemo()
    
    # Check if services are running
    if not demo.check_services():
        return
        
    # Run interactive menu
    demo.interactive_menu()

if __name__ == "__main__":
    main() 