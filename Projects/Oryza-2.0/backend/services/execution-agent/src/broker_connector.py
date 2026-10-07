"""
Broker Connector - Manages connections to multiple brokers
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from decimal import Decimal
from cryptography.fernet import Fernet
import json

from .models import (
    BrokerAccount, BrokerStatus, BrokerConfig,
    Position, MarketData, OrderBook,
    OrderType, TimeInForce
)


class BrokerConnector:
    """
    Manages connections to multiple brokers
    """
    
    def __init__(self):
        self.logger = logging.getLogger("broker_connector")
        self.brokers = {}  # broker_id -> BrokerInterface
        self.accounts = {}  # user_id -> List[BrokerAccount]
        self.connections = {}  # account_id -> connection
        self.market_data_cache = {}  # symbol -> MarketData
        self.encryption_key = None
        self.is_monitoring = False
        
    async def initialize(self):
        """Initialize broker connector"""
        self.logger.info("Initializing Broker Connector")
        
        # Generate encryption key for credentials
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Initialize broker interfaces
        self.brokers = {
            "MOCK_BROKER": MockBroker(),
            "ALPACA": AlpacaBroker(),
            "INTERACTIVE_BROKERS": IBBroker(),
        }
        
        # Initialize each broker
        for broker_id, broker in self.brokers.items():
            await broker.initialize()
            
    async def get_available_brokers(self) -> List[BrokerConfig]:
        """Get list of available brokers"""
        configs = []
        
        for broker_id, broker in self.brokers.items():
            config = BrokerConfig(
                broker_id=broker_id,
                name=broker.name,
                display_name=broker.display_name,
                supported_order_types=broker.supported_order_types,
                supported_time_in_force=broker.supported_time_in_force,
                supported_asset_classes=broker.supported_asset_classes,
                min_order_size=broker.min_order_size,
                max_order_size=broker.max_order_size,
                supports_fractional=broker.supports_fractional,
                supports_crypto=broker.supports_crypto,
                supports_options=broker.supports_options,
                supports_international=broker.supports_international,
                api_type=broker.api_type,
                requires_oauth=broker.requires_oauth,
                is_active=broker.is_active,
                maintenance_mode=broker.maintenance_mode
            )
            configs.append(config)
            
        return configs
        
    async def connect_broker(
        self,
        user_id: str,
        broker_id: str,
        credentials: str  # Encrypted
    ) -> BrokerAccount:
        """Connect to a broker account"""
        if broker_id not in self.brokers:
            raise ValueError(f"Unknown broker: {broker_id}")
            
        broker = self.brokers[broker_id]
        
        # Create account record
        account = BrokerAccount(
            user_id=user_id,
            broker_id=broker_id,
            broker_account_id="",  # Will be set after connection
            account_type="cash",  # Will be updated
            encrypted_credentials=credentials
        )
        
        try:
            # Decrypt credentials
            decrypted_creds = self.cipher.decrypt(credentials.encode())
            creds_dict = json.loads(decrypted_creds)
            
            # Connect to broker
            connection = await broker.connect(creds_dict)
            
            # Get account info
            account_info = await broker.get_account_info(connection)
            
            # Update account
            account.broker_account_id = account_info["account_id"]
            account.account_type = account_info["account_type"]
            account.status = BrokerStatus.CONNECTED
            account.connected_at = datetime.now()
            account.cash_balance = Decimal(str(account_info.get("cash_balance", 0)))
            account.buying_power = Decimal(str(account_info.get("buying_power", 0)))
            
            # Store connection
            self.connections[account.account_id] = connection
            
            # Store account
            if user_id not in self.accounts:
                self.accounts[user_id] = []
            self.accounts[user_id].append(account)
            
            self.logger.info(f"Connected to {broker_id} for user {user_id}")
            
            return account
            
        except Exception as e:
            self.logger.error(f"Failed to connect to {broker_id}: {str(e)}")
            account.status = BrokerStatus.ERROR
            raise
            
    async def encrypt_credentials(self, credentials: Dict[str, str]) -> str:
        """Encrypt broker credentials"""
        creds_json = json.dumps(credentials)
        encrypted = self.cipher.encrypt(creds_json.encode())
        return encrypted.decode()
        
    async def get_positions(self, user_id: str) -> List[Position]:
        """Get all positions across all brokers"""
        all_positions = []
        
        user_accounts = self.accounts.get(user_id, [])
        
        for account in user_accounts:
            if account.status == BrokerStatus.CONNECTED:
                try:
                    broker = self.brokers[account.broker_id]
                    connection = self.connections.get(account.account_id)
                    
                    if connection:
                        positions = await broker.get_positions(connection)
                        
                        # Convert to Position objects
                        for pos_data in positions:
                            position = Position(
                                user_id=user_id,
                                symbol=pos_data["symbol"],
                                quantity=Decimal(str(pos_data["quantity"])),
                                available_quantity=Decimal(str(pos_data["available_quantity"])),
                                avg_cost=Decimal(str(pos_data["avg_cost"])),
                                market_price=Decimal(str(pos_data["market_price"])),
                                market_value=Decimal(str(pos_data["market_value"])),
                                unrealized_pnl=Decimal(str(pos_data["unrealized_pnl"])),
                                unrealized_pnl_percent=Decimal(str(pos_data["unrealized_pnl_percent"])),
                                realized_pnl=Decimal(str(pos_data.get("realized_pnl", 0))),
                                broker=account.broker_id,
                                account_id=account.account_id,
                                opened_at=pos_data.get("opened_at", datetime.now())
                            )
                            all_positions.append(position)
                            
                except Exception as e:
                    self.logger.error(
                        f"Error fetching positions from {account.broker_id}: {str(e)}"
                    )
                    
        return all_positions
        
    async def get_market_data(self, symbol: str) -> Optional[MarketData]:
        """Get real-time market data"""
        # Check cache first
        cached = self.market_data_cache.get(symbol)
        if cached and (datetime.now() - cached.timestamp).seconds < 5:
            return cached
            
        # Try each broker until we get data
        for broker_id, broker in self.brokers.items():
            if broker.is_active and not broker.maintenance_mode:
                try:
                    data = await broker.get_market_data(symbol)
                    
                    if data:
                        market_data = MarketData(
                            symbol=symbol,
                            bid=Decimal(str(data.get("bid", 0))) if data.get("bid") else None,
                            ask=Decimal(str(data.get("ask", 0))) if data.get("ask") else None,
                            last=Decimal(str(data.get("last", 0))) if data.get("last") else None,
                            open=Decimal(str(data.get("open", 0))) if data.get("open") else None,
                            high=Decimal(str(data.get("high", 0))) if data.get("high") else None,
                            low=Decimal(str(data.get("low", 0))) if data.get("low") else None,
                            close=Decimal(str(data.get("close", 0))) if data.get("close") else None,
                            prev_close=Decimal(str(data.get("prev_close", 0))) if data.get("prev_close") else None,
                            volume=data.get("volume"),
                            bid_size=data.get("bid_size"),
                            ask_size=data.get("ask_size"),
                            change=Decimal(str(data.get("change", 0))) if data.get("change") else None,
                            change_percent=Decimal(str(data.get("change_percent", 0))) if data.get("change_percent") else None,
                            halted=data.get("halted", False),
                            tradeable=data.get("tradeable", True)
                        )
                        
                        # Cache it
                        self.market_data_cache[symbol] = market_data
                        
                        return market_data
                        
                except Exception as e:
                    self.logger.error(
                        f"Error fetching market data from {broker_id}: {str(e)}"
                    )
                    
        return None
        
    async def get_orderbook(self, symbol: str, depth: int = 10) -> Optional[OrderBook]:
        """Get order book data"""
        # Try each broker
        for broker_id, broker in self.brokers.items():
            if broker.is_active and broker.supports_orderbook:
                try:
                    data = await broker.get_orderbook(symbol, depth)
                    
                    if data:
                        orderbook = OrderBook(
                            symbol=symbol,
                            bids=[
                                {"price": Decimal(str(b["price"])), "size": b["size"]}
                                for b in data.get("bids", [])
                            ],
                            asks=[
                                {"price": Decimal(str(a["price"])), "size": a["size"]}
                                for a in data.get("asks", [])
                            ]
                        )
                        
                        # Calculate spread
                        if orderbook.bids and orderbook.asks:
                            best_bid = orderbook.bids[0]["price"]
                            best_ask = orderbook.asks[0]["price"]
                            orderbook.spread = best_ask - best_bid
                            orderbook.spread_percent = (orderbook.spread / best_ask) * 100
                            
                        return orderbook
                        
                except Exception as e:
                    self.logger.error(
                        f"Error fetching orderbook from {broker_id}: {str(e)}"
                    )
                    
        return None
        
    async def get_trading_hours(self, symbol: str) -> Dict[str, Any]:
        """Get trading hours for a symbol"""
        # For now, return standard market hours
        # In production, check with broker
        
        return {
            "pre_market_start": "04:00",
            "pre_market_end": "09:30",
            "regular_start": "09:30",
            "regular_end": "16:00",
            "after_hours_start": "16:00",
            "after_hours_end": "20:00",
            "timezone": "America/New_York"
        }
        
    async def is_market_open(self, symbol: str) -> bool:
        """Check if market is open for trading"""
        # In production, check with broker
        # For now, simple time check
        
        from datetime import time
        import pytz
        
        et = pytz.timezone('America/New_York')
        now_et = datetime.now(et)
        
        # Check if weekday
        if now_et.weekday() >= 5:  # Saturday or Sunday
            return False
            
        # Check time
        current_time = now_et.time()
        market_open = time(9, 30)
        market_close = time(16, 0)
        
        return market_open <= current_time <= market_close
        
    async def get_all_status(self) -> Dict[str, BrokerStatus]:
        """Get status of all brokers"""
        status = {}
        
        for broker_id, broker in self.brokers.items():
            if broker.is_active:
                status[broker_id] = BrokerStatus.CONNECTED
            elif broker.maintenance_mode:
                status[broker_id] = BrokerStatus.MAINTENANCE
            else:
                status[broker_id] = BrokerStatus.DISCONNECTED
                
        return status
        
    async def monitor_connections(self):
        """Monitor broker connections"""
        self.is_monitoring = True
        
        while self.is_monitoring:
            try:
                # Check each connection
                for account_id, connection in self.connections.items():
                    # Find account
                    account = None
                    for user_accounts in self.accounts.values():
                        for acc in user_accounts:
                            if acc.account_id == account_id:
                                account = acc
                                break
                                
                    if account:
                        broker = self.brokers.get(account.broker_id)
                        if broker:
                            # Ping connection
                            is_alive = await broker.ping_connection(connection)
                            
                            if not is_alive:
                                account.status = BrokerStatus.RECONNECTING
                                self.logger.warning(
                                    f"Connection lost to {account.broker_id}"
                                )
                                
                                # Try to reconnect
                                try:
                                    # Decrypt credentials
                                    decrypted = self.cipher.decrypt(
                                        account.encrypted_credentials.encode()
                                    )
                                    creds = json.loads(decrypted)
                                    
                                    # Reconnect
                                    new_connection = await broker.connect(creds)
                                    self.connections[account_id] = new_connection
                                    account.status = BrokerStatus.CONNECTED
                                    
                                    self.logger.info(
                                        f"Reconnected to {account.broker_id}"
                                    )
                                    
                                except Exception as e:
                                    account.status = BrokerStatus.ERROR
                                    self.logger.error(
                                        f"Failed to reconnect: {str(e)}"
                                    )
                                    
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error monitoring connections: {str(e)}")
                await asyncio.sleep(60)
                
    async def shutdown(self):
        """Shutdown broker connector"""
        self.is_monitoring = False
        
        # Disconnect all connections
        for account_id, connection in self.connections.items():
            try:
                # Find broker
                account = None
                for user_accounts in self.accounts.values():
                    for acc in user_accounts:
                        if acc.account_id == account_id:
                            account = acc
                            break
                            
                if account:
                    broker = self.brokers.get(account.broker_id)
                    if broker:
                        await broker.disconnect(connection)
                        
            except Exception as e:
                self.logger.error(f"Error disconnecting: {str(e)}")
                
        self.logger.info("Broker Connector shutdown complete")


# Base Broker Interface
class BrokerInterface:
    """Base interface for broker implementations"""
    
    def __init__(self):
        self.name = "Base Broker"
        self.display_name = "Base Broker"
        self.supported_order_types = [OrderType.MARKET, OrderType.LIMIT]
        self.supported_time_in_force = [TimeInForce.DAY, TimeInForce.GTC]
        self.supported_asset_classes = ["stocks"]
        self.min_order_size = Decimal("1")
        self.max_order_size = Decimal("10000")
        self.supports_fractional = False
        self.supports_crypto = False
        self.supports_options = False
        self.supports_international = False
        self.supports_orderbook = False
        self.api_type = "REST"
        self.requires_oauth = False
        self.is_active = True
        self.maintenance_mode = False
        
    async def initialize(self):
        """Initialize broker"""
        pass
        
    async def connect(self, credentials: Dict[str, str]) -> Any:
        """Connect to broker"""
        raise NotImplementedError
        
    async def disconnect(self, connection: Any):
        """Disconnect from broker"""
        raise NotImplementedError
        
    async def ping_connection(self, connection: Any) -> bool:
        """Check if connection is alive"""
        raise NotImplementedError
        
    async def get_account_info(self, connection: Any) -> Dict[str, Any]:
        """Get account information"""
        raise NotImplementedError
        
    async def get_positions(self, connection: Any) -> List[Dict[str, Any]]:
        """Get positions"""
        raise NotImplementedError
        
    async def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get market data"""
        raise NotImplementedError
        
    async def get_orderbook(self, symbol: str, depth: int) -> Optional[Dict[str, Any]]:
        """Get order book"""
        raise NotImplementedError


# Mock Broker Implementation
class MockBroker(BrokerInterface):
    """Mock broker for testing"""
    
    def __init__(self):
        super().__init__()
        self.name = "mock_broker"
        self.display_name = "Mock Broker (Testing)"
        self.supports_fractional = True
        self.supports_orderbook = True
        
    async def connect(self, credentials: Dict[str, str]) -> Any:
        """Mock connection"""
        return {"session_id": "mock_session_123"}
        
    async def disconnect(self, connection: Any):
        """Mock disconnect"""
        pass
        
    async def ping_connection(self, connection: Any) -> bool:
        """Always alive"""
        return True
        
    async def get_account_info(self, connection: Any) -> Dict[str, Any]:
        """Mock account info"""
        return {
            "account_id": "MOCK123456",
            "account_type": "cash",
            "cash_balance": "10000.00",
            "buying_power": "10000.00"
        }
        
    async def get_positions(self, connection: Any) -> List[Dict[str, Any]]:
        """Mock positions"""
        return [
            {
                "symbol": "AAPL",
                "quantity": "100",
                "available_quantity": "100",
                "avg_cost": "150.00",
                "market_price": "155.00",
                "market_value": "15500.00",
                "unrealized_pnl": "500.00",
                "unrealized_pnl_percent": "3.33",
                "opened_at": datetime.now() - timedelta(days=30)
            }
        ]
        
    async def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Mock market data"""
        import random
        
        base_price = 100.0
        variation = random.uniform(-2, 2)
        
        return {
            "bid": base_price + variation - 0.01,
            "ask": base_price + variation + 0.01,
            "last": base_price + variation,
            "open": base_price,
            "high": base_price + abs(variation) + 1,
            "low": base_price - abs(variation) - 1,
            "close": base_price + variation,
            "prev_close": base_price,
            "volume": random.randint(1000000, 10000000),
            "bid_size": random.randint(100, 1000),
            "ask_size": random.randint(100, 1000),
            "change": variation,
            "change_percent": variation / base_price * 100,
            "tradeable": True
        }
        
    async def get_orderbook(self, symbol: str, depth: int) -> Optional[Dict[str, Any]]:
        """Mock order book"""
        import random
        
        base_price = 100.0
        
        bids = []
        asks = []
        
        for i in range(depth):
            bid_price = base_price - (i + 1) * 0.01
            ask_price = base_price + (i + 1) * 0.01
            
            bids.append({
                "price": bid_price,
                "size": random.randint(100, 5000)
            })
            
            asks.append({
                "price": ask_price,
                "size": random.randint(100, 5000)
            })
            
        return {
            "bids": bids,
            "asks": asks
        }


# Placeholder for real broker implementations
class AlpacaBroker(BrokerInterface):
    """Alpaca broker implementation"""
    
    def __init__(self):
        super().__init__()
        self.name = "alpaca"
        self.display_name = "Alpaca"
        self.supports_fractional = True
        self.supports_crypto = True
        self.is_active = False  # Not implemented yet


class IBBroker(BrokerInterface):
    """Interactive Brokers implementation"""
    
    def __init__(self):
        super().__init__()
        self.name = "interactive_brokers"
        self.display_name = "Interactive Brokers"
        self.supports_options = True
        self.supports_international = True
        self.api_type = "FIX"
        self.is_active = False  # Not implemented yet 