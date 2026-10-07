"""
Execution Agent - Broker integration and trade execution
"""
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal

# Import from shared modules
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from shared.config.settings import get_settings
from shared.database.connection import init_databases, close_databases, get_db, get_redis
from shared.database.models import User, Portfolio, Transaction
from shared.utils.logger import trading_logger
from shared.utils.auth import get_current_verified_user, get_current_kyc_verified_user

# Import execution modules
from .order_manager import OrderManager
from .broker_connector import BrokerConnector
from .risk_validator import RiskValidator
from .settlement_engine import SettlementEngine
from .models import (
    Order, OrderRequest, OrderResponse, OrderStatus,
    OrderType, OrderSide, TimeInForce, ExecutionReport,
    Position, PositionUpdate, BrokerAccount,
    MarketData, OrderBook, Trade, Settlement,
    RiskCheck, RiskValidation, BrokerStatus
)

settings = get_settings()
logger = trading_logger.get_logger()

# Global instances
order_manager = None
broker_connector = None
risk_validator = None
settlement_engine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global order_manager, broker_connector, risk_validator, settlement_engine
    
    # Startup
    logger.info("Starting Execution Agent Service")
    await init_databases()
    
    # Initialize components
    order_manager = OrderManager()
    broker_connector = BrokerConnector()
    risk_validator = RiskValidator()
    settlement_engine = SettlementEngine()
    
    await asyncio.gather(
        order_manager.initialize(),
        broker_connector.initialize(),
        risk_validator.initialize(),
        settlement_engine.initialize()
    )
    
    # Start background workers
    asyncio.create_task(order_manager.process_orders())
    asyncio.create_task(broker_connector.monitor_connections())
    asyncio.create_task(settlement_engine.process_settlements())
    
    logger.info("Execution Agent Service initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Execution Agent Service")
    await order_manager.shutdown()
    await broker_connector.shutdown()
    await close_databases()


# Create FastAPI app
app = FastAPI(
    title="Execution Agent Service",
    description="Handle order execution and broker integration",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Execution Agent",
        "version": "1.0.0",
        "status": "operational",
        "capabilities": [
            "Multi-broker integration",
            "Smart order routing",
            "Risk validation",
            "Real-time execution",
            "Settlement processing",
            "Position tracking"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    broker_status = await broker_connector.get_all_status() if broker_connector else {}
    
    return {
        "status": "healthy",
        "components": {
            "order_manager": "ready" if order_manager else "not initialized",
            "broker_connector": "ready" if broker_connector else "not initialized",
            "risk_validator": "ready" if risk_validator else "not initialized",
            "settlement_engine": "ready" if settlement_engine else "not initialized"
        },
        "brokers": broker_status
    }


@app.post("/orders", response_model=OrderResponse)
async def place_order(
    request: OrderRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_kyc_verified_user),
    db = Depends(get_db)
):
    """
    Place a new order
    
    Requires KYC verification for real trading
    """
    try:
        # Create order object
        order = Order(
            user_id=str(current_user.id),
            symbol=request.symbol,
            side=request.side,
            order_type=request.order_type,
            quantity=request.quantity,
            price=request.price,
            stop_price=request.stop_price,
            time_in_force=request.time_in_force,
            broker=request.broker,
            metadata=request.metadata
        )
        
        # Validate risk
        risk_check = await risk_validator.validate_order(order, current_user)
        if not risk_check.passed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Risk check failed: {risk_check.reason}"
            )
            
        # Submit order
        submitted_order = await order_manager.submit_order(order)
        
        # Queue for execution
        background_tasks.add_task(
            order_manager.execute_order,
            submitted_order
        )
        
        return OrderResponse(
            order_id=submitted_order.order_id,
            status=submitted_order.status,
            created_at=submitted_order.created_at,
            symbol=submitted_order.symbol,
            side=submitted_order.side,
            order_type=submitted_order.order_type,
            quantity=submitted_order.quantity,
            price=submitted_order.price
        )
        
    except Exception as e:
        logger.error(f"Error placing order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to place order: {str(e)}"
        )


@app.get("/orders")
async def get_orders(
    status: Optional[OrderStatus] = None,
    symbol: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_verified_user)
):
    """Get user's orders"""
    try:
        orders = await order_manager.get_user_orders(
            user_id=str(current_user.id),
            status=status,
            symbol=symbol,
            limit=limit,
            offset=offset
        )
        
        return {
            "orders": orders,
            "total": len(orders)
        }
        
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch orders: {str(e)}"
        )


@app.get("/orders/{order_id}")
async def get_order_details(
    order_id: str,
    current_user: User = Depends(get_current_verified_user)
):
    """Get order details"""
    try:
        order = await order_manager.get_order(order_id, str(current_user.id))
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
            
        return order
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch order: {str(e)}"
        )


@app.delete("/orders/{order_id}")
async def cancel_order(
    order_id: str,
    current_user: User = Depends(get_current_verified_user)
):
    """Cancel an order"""
    try:
        success = await order_manager.cancel_order(
            order_id=order_id,
            user_id=str(current_user.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order cannot be cancelled"
            )
            
        return {"status": "cancelled", "order_id": order_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel order: {str(e)}"
        )


@app.put("/orders/{order_id}")
async def modify_order(
    order_id: str,
    updates: Dict[str, Any],
    current_user: User = Depends(get_current_verified_user)
):
    """Modify an existing order"""
    try:
        # Validate updates
        allowed_updates = ["quantity", "price", "stop_price"]
        invalid_fields = set(updates.keys()) - set(allowed_updates)
        
        if invalid_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot modify fields: {invalid_fields}"
            )
            
        # Modify order
        modified_order = await order_manager.modify_order(
            order_id=order_id,
            user_id=str(current_user.id),
            updates=updates
        )
        
        if not modified_order:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order cannot be modified"
            )
            
        return modified_order
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error modifying order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to modify order: {str(e)}"
        )


@app.get("/positions")
async def get_positions(
    current_user: User = Depends(get_current_verified_user)
):
    """Get current positions"""
    try:
        positions = await broker_connector.get_positions(
            user_id=str(current_user.id)
        )
        
        # Calculate metrics
        total_value = sum(p.market_value for p in positions)
        total_pnl = sum(p.unrealized_pnl for p in positions)
        
        return {
            "positions": positions,
            "summary": {
                "total_positions": len(positions),
                "total_value": total_value,
                "total_unrealized_pnl": total_pnl,
                "updated_at": datetime.now()
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching positions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch positions: {str(e)}"
        )


@app.get("/executions")
async def get_executions(
    days: int = 7,
    symbol: Optional[str] = None,
    current_user: User = Depends(get_current_verified_user)
):
    """Get execution history"""
    try:
        since = datetime.now() - timedelta(days=days)
        
        executions = await order_manager.get_executions(
            user_id=str(current_user.id),
            since=since,
            symbol=symbol
        )
        
        return {
            "executions": executions,
            "total": len(executions),
            "period_days": days
        }
        
    except Exception as e:
        logger.error(f"Error fetching executions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch executions: {str(e)}"
        )


@app.post("/orders/validate")
async def validate_order(
    request: OrderRequest,
    current_user: User = Depends(get_current_verified_user)
) -> RiskValidation:
    """Validate an order before submission"""
    try:
        # Create order for validation
        order = Order(
            user_id=str(current_user.id),
            symbol=request.symbol,
            side=request.side,
            order_type=request.order_type,
            quantity=request.quantity,
            price=request.price,
            stop_price=request.stop_price,
            time_in_force=request.time_in_force,
            broker=request.broker
        )
        
        # Run risk checks
        validation = await risk_validator.validate_order(order, current_user)
        
        return validation
        
    except Exception as e:
        logger.error(f"Error validating order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate order: {str(e)}"
        )


@app.get("/market-data/{symbol}")
async def get_market_data(
    symbol: str,
    current_user: User = Depends(get_current_verified_user)
) -> MarketData:
    """Get real-time market data"""
    try:
        market_data = await broker_connector.get_market_data(symbol)
        
        if not market_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Market data not available for {symbol}"
            )
            
        return market_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching market data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch market data: {str(e)}"
        )


@app.get("/orderbook/{symbol}")
async def get_orderbook(
    symbol: str,
    depth: int = 10,
    current_user: User = Depends(get_current_verified_user)
) -> OrderBook:
    """Get order book data"""
    try:
        orderbook = await broker_connector.get_orderbook(symbol, depth)
        
        if not orderbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order book not available for {symbol}"
            )
            
        return orderbook
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order book: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch order book: {str(e)}"
        )


@app.get("/brokers")
async def get_available_brokers(
    current_user: User = Depends(get_current_verified_user)
):
    """Get available brokers and their status"""
    try:
        brokers = await broker_connector.get_available_brokers()
        
        return {
            "brokers": brokers,
            "total": len(brokers)
        }
        
    except Exception as e:
        logger.error(f"Error fetching brokers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch brokers: {str(e)}"
        )


@app.post("/brokers/{broker_id}/connect")
async def connect_broker(
    broker_id: str,
    credentials: Dict[str, str],
    current_user: User = Depends(get_current_kyc_verified_user)
):
    """Connect to a broker account"""
    try:
        # Validate and encrypt credentials
        encrypted_creds = await broker_connector.encrypt_credentials(
            credentials
        )
        
        # Connect to broker
        account = await broker_connector.connect_broker(
            user_id=str(current_user.id),
            broker_id=broker_id,
            credentials=encrypted_creds
        )
        
        return {
            "status": "connected",
            "account": {
                "broker_id": account.broker_id,
                "account_id": account.account_id,
                "account_type": account.account_type,
                "created_at": account.created_at
            }
        }
        
    except Exception as e:
        logger.error(f"Error connecting broker: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect broker: {str(e)}"
        )


@app.get("/settlements")
async def get_settlements(
    status: Optional[str] = None,
    days: int = 30,
    current_user: User = Depends(get_current_verified_user)
):
    """Get settlement history"""
    try:
        since = datetime.now() - timedelta(days=days)
        
        settlements = await settlement_engine.get_user_settlements(
            user_id=str(current_user.id),
            status=status,
            since=since
        )
        
        return {
            "settlements": settlements,
            "total": len(settlements),
            "period_days": days
        }
        
    except Exception as e:
        logger.error(f"Error fetching settlements: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch settlements: {str(e)}"
        )


@app.get("/trading-hours/{symbol}")
async def get_trading_hours(
    symbol: str,
    current_user: User = Depends(get_current_verified_user)
):
    """Get trading hours for a symbol"""
    try:
        hours = await broker_connector.get_trading_hours(symbol)
        
        return {
            "symbol": symbol,
            "trading_hours": hours,
            "is_open": await broker_connector.is_market_open(symbol),
            "next_open": hours.get("next_open"),
            "next_close": hours.get("next_close")
        }
        
    except Exception as e:
        logger.error(f"Error fetching trading hours: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trading hours: {str(e)}"
        )


@app.post("/orders/batch")
async def place_batch_orders(
    orders: List[OrderRequest],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_kyc_verified_user)
):
    """Place multiple orders at once"""
    try:
        if len(orders) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 orders per batch"
            )
            
        # Validate all orders first
        validated_orders = []
        for order_req in orders:
            order = Order(
                user_id=str(current_user.id),
                symbol=order_req.symbol,
                side=order_req.side,
                order_type=order_req.order_type,
                quantity=order_req.quantity,
                price=order_req.price,
                broker=order_req.broker
            )
            
            risk_check = await risk_validator.validate_order(order, current_user)
            if not risk_check.passed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Risk check failed for {order.symbol}: {risk_check.reason}"
                )
                
            validated_orders.append(order)
            
        # Submit all orders
        submitted_orders = await order_manager.submit_batch_orders(validated_orders)
        
        # Queue for execution
        for order in submitted_orders:
            background_tasks.add_task(order_manager.execute_order, order)
            
        return {
            "status": "submitted",
            "orders": [
                {
                    "order_id": o.order_id,
                    "symbol": o.symbol,
                    "status": o.status.value
                }
                for o in submitted_orders
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error placing batch orders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to place batch orders: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8008,
        reload=True
    )
