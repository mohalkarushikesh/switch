"""
Backtesting Engine - Test trading strategies with historical data
"""
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime, timedelta, date
from decimal import Decimal
import json

# Import from shared modules
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from shared.config.settings import get_settings
from shared.database.connection import init_databases, close_databases, get_db, get_redis
from shared.database.models import User
from shared.utils.logger import ServiceLogger
from shared.utils.auth import get_current_verified_user

# Import backtesting modules
from .backtesting_engine import BacktestingEngine
from .strategy_runner import StrategyRunner
from .data_manager import DataManager
from .performance_analyzer import PerformanceAnalyzer
from .models import (
    Strategy, StrategyType, StrategyStatus,
    Backtest, BacktestConfig, BacktestStatus,
    BacktestResult, PerformanceMetrics,
    Trade, TradeType, TradeStatus,
    Position, PositionStatus,
    MarketData, DataFrequency,
    Signal, SignalType,
    Portfolio, PortfolioSnapshot,
    DrawdownAnalysis, RiskMetrics
)

settings = get_settings()
backtest_logger = ServiceLogger("backtesting-engine")
logger = backtest_logger.get_logger()

# Global instances
backtesting_engine = None
strategy_runner = None
data_manager = None
performance_analyzer = None

# WebSocket connections for live updates
websocket_clients = {}  # backtest_id -> WebSocket


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global backtesting_engine, strategy_runner, data_manager, performance_analyzer
    
    # Startup
    logger.info("Starting Backtesting Engine Service")
    await init_databases()
    
    # Initialize components
    data_manager = DataManager()
    performance_analyzer = PerformanceAnalyzer()
    strategy_runner = StrategyRunner(data_manager)
    backtesting_engine = BacktestingEngine(strategy_runner, data_manager, performance_analyzer)
    
    await asyncio.gather(
        data_manager.initialize(),
        performance_analyzer.initialize(),
        strategy_runner.initialize(),
        backtesting_engine.initialize()
    )
    
    logger.info("Backtesting Engine Service initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Backtesting Engine Service")
    await backtesting_engine.shutdown()
    await close_databases()


# Create FastAPI app
app = FastAPI(
    title="Backtesting Engine Service",
    description="Test trading strategies with historical data",
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
        "service": "Backtesting Engine",
        "version": "1.0.0",
        "status": "operational",
        "capabilities": [
            "Strategy backtesting",
            "Historical data management",
            "Performance analysis",
            "Risk metrics calculation",
            "Trade simulation",
            "Portfolio tracking",
            "Real-time progress updates",
            "Multi-asset support"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "components": {
            "backtesting_engine": "ready" if backtesting_engine else "not initialized",
            "strategy_runner": "ready" if strategy_runner else "not initialized",
            "data_manager": "ready" if data_manager else "not initialized",
            "performance_analyzer": "ready" if performance_analyzer else "not initialized"
        },
        "active_backtests": backtesting_engine.get_active_count() if backtesting_engine else 0
    }


@app.get("/strategies", response_model=List[Strategy])
async def get_strategies(
    strategy_type: Optional[StrategyType] = None,
    status: Optional[StrategyStatus] = None,
    current_user: User = Depends(get_current_verified_user)
):
    """Get available strategies"""
    try:
        strategies = await backtesting_engine.get_strategies(
            user_id=str(current_user.id),
            strategy_type=strategy_type,
            status=status
        )
        
        return strategies
        
    except Exception as e:
        logger.error(f"Error fetching strategies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch strategies: {str(e)}"
        )


@app.post("/strategies", response_model=Strategy)
async def create_strategy(
    strategy: Strategy,
    current_user: User = Depends(get_current_verified_user)
):
    """Create a new strategy"""
    try:
        # Set owner
        strategy.user_id = str(current_user.id)
        
        created_strategy = await backtesting_engine.create_strategy(strategy)
        
        return created_strategy
        
    except Exception as e:
        logger.error(f"Error creating strategy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create strategy: {str(e)}"
        )


@app.get("/strategies/{strategy_id}", response_model=Strategy)
async def get_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_verified_user)
):
    """Get strategy details"""
    try:
        strategy = await backtesting_engine.get_strategy(
            strategy_id=strategy_id,
            user_id=str(current_user.id)
        )
        
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found"
            )
            
        return strategy
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching strategy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch strategy: {str(e)}"
        )


@app.put("/strategies/{strategy_id}")
async def update_strategy(
    strategy_id: str,
    updates: Dict[str, Any],
    current_user: User = Depends(get_current_verified_user)
):
    """Update strategy"""
    try:
        success = await backtesting_engine.update_strategy(
            strategy_id=strategy_id,
            user_id=str(current_user.id),
            updates=updates
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found"
            )
            
        return {"status": "success", "strategy_id": strategy_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating strategy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update strategy: {str(e)}"
        )


@app.delete("/strategies/{strategy_id}")
async def delete_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_verified_user)
):
    """Delete strategy"""
    try:
        success = await backtesting_engine.delete_strategy(
            strategy_id=strategy_id,
            user_id=str(current_user.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found"
            )
            
        return {"status": "success", "message": "Strategy deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting strategy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete strategy: {str(e)}"
        )


@app.post("/backtests", response_model=Backtest)
async def create_backtest(
    config: BacktestConfig,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_verified_user)
):
    """Create and start a backtest"""
    try:
        # Create backtest
        backtest = await backtesting_engine.create_backtest(
            user_id=str(current_user.id),
            config=config
        )
        
        # Start backtest in background
        background_tasks.add_task(
            backtesting_engine.run_backtest,
            backtest.backtest_id
        )
        
        return backtest
        
    except Exception as e:
        logger.error(f"Error creating backtest: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create backtest: {str(e)}"
        )


@app.get("/backtests", response_model=List[Backtest])
async def get_backtests(
    strategy_id: Optional[str] = None,
    status: Optional[BacktestStatus] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_verified_user)
):
    """Get user's backtests"""
    try:
        backtests = await backtesting_engine.get_backtests(
            user_id=str(current_user.id),
            strategy_id=strategy_id,
            status=status,
            limit=limit
        )
        
        return backtests
        
    except Exception as e:
        logger.error(f"Error fetching backtests: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch backtests: {str(e)}"
        )


@app.get("/backtests/{backtest_id}", response_model=Backtest)
async def get_backtest(
    backtest_id: str,
    current_user: User = Depends(get_current_verified_user)
):
    """Get backtest details"""
    try:
        backtest = await backtesting_engine.get_backtest(
            backtest_id=backtest_id,
            user_id=str(current_user.id)
        )
        
        if not backtest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backtest not found"
            )
            
        return backtest
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching backtest: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch backtest: {str(e)}"
        )


@app.get("/backtests/{backtest_id}/results", response_model=BacktestResult)
async def get_backtest_results(
    backtest_id: str,
    current_user: User = Depends(get_current_verified_user)
):
    """Get backtest results"""
    try:
        results = await backtesting_engine.get_backtest_results(
            backtest_id=backtest_id,
            user_id=str(current_user.id)
        )
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Results not found"
            )
            
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch results: {str(e)}"
        )


@app.get("/backtests/{backtest_id}/trades", response_model=List[Trade])
async def get_backtest_trades(
    backtest_id: str,
    limit: int = 100,
    current_user: User = Depends(get_current_verified_user)
):
    """Get trades from backtest"""
    try:
        trades = await backtesting_engine.get_backtest_trades(
            backtest_id=backtest_id,
            user_id=str(current_user.id),
            limit=limit
        )
        
        return trades
        
    except Exception as e:
        logger.error(f"Error fetching trades: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trades: {str(e)}"
        )


@app.get("/backtests/{backtest_id}/performance", response_model=PerformanceMetrics)
async def get_backtest_performance(
    backtest_id: str,
    current_user: User = Depends(get_current_verified_user)
):
    """Get detailed performance metrics"""
    try:
        metrics = await performance_analyzer.calculate_metrics(
            backtest_id=backtest_id,
            user_id=str(current_user.id)
        )
        
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Performance data not found"
            )
            
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating performance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate performance: {str(e)}"
        )


@app.get("/backtests/{backtest_id}/portfolio", response_model=List[PortfolioSnapshot])
async def get_portfolio_history(
    backtest_id: str,
    frequency: str = "daily",  # daily, hourly, all
    current_user: User = Depends(get_current_verified_user)
):
    """Get portfolio value history"""
    try:
        snapshots = await backtesting_engine.get_portfolio_history(
            backtest_id=backtest_id,
            user_id=str(current_user.id),
            frequency=frequency
        )
        
        return snapshots
        
    except Exception as e:
        logger.error(f"Error fetching portfolio history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch portfolio history: {str(e)}"
        )


@app.post("/backtests/{backtest_id}/stop")
async def stop_backtest(
    backtest_id: str,
    current_user: User = Depends(get_current_verified_user)
):
    """Stop a running backtest"""
    try:
        success = await backtesting_engine.stop_backtest(
            backtest_id=backtest_id,
            user_id=str(current_user.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backtest not found or already stopped"
            )
            
        return {"status": "success", "message": "Backtest stopped"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping backtest: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop backtest: {str(e)}"
        )


@app.get("/data/symbols")
async def get_available_symbols(
    asset_class: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get available symbols for backtesting"""
    try:
        symbols = await data_manager.get_available_symbols(asset_class)
        
        return symbols
        
    except Exception as e:
        logger.error(f"Error fetching symbols: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch symbols: {str(e)}"
        )


@app.get("/data/timeframes")
async def get_available_timeframes() -> List[str]:
    """Get available data timeframes"""
    return [f.value for f in DataFrequency]


@app.get("/data/date-range/{symbol}")
async def get_data_date_range(symbol: str) -> Dict[str, Any]:
    """Get available date range for a symbol"""
    try:
        date_range = await data_manager.get_symbol_date_range(symbol)
        
        return date_range
        
    except Exception as e:
        logger.error(f"Error fetching date range: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch date range: {str(e)}"
        )


@app.post("/data/upload")
async def upload_market_data(
    symbol: str,
    data: List[MarketData],
    current_user: User = Depends(get_current_verified_user)
):
    """Upload custom market data"""
    try:
        # Check permissions
        if "data_provider" not in current_user.roles and "admin" not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Data provider role required"
            )
            
        success = await data_manager.upload_data(symbol, data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to upload data"
            )
            
        return {
            "status": "success",
            "message": f"Uploaded {len(data)} data points for {symbol}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload data: {str(e)}"
        )


@app.websocket("/ws/{backtest_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    backtest_id: str
):
    """WebSocket endpoint for real-time backtest updates"""
    await websocket.accept()
    websocket_clients[backtest_id] = websocket
    
    try:
        # Send initial status
        backtest = await backtesting_engine.get_backtest(backtest_id)
        if backtest:
            await websocket.send_json({
                "type": "status",
                "data": {
                    "status": backtest.status,
                    "progress": backtest.progress,
                    "current_date": backtest.current_date.isoformat() if backtest.current_date else None
                }
            })
            
        # Keep connection alive
        while True:
            # Receive messages (ping/pong)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        del websocket_clients[backtest_id]
        logger.info(f"WebSocket disconnected for backtest {backtest_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        if backtest_id in websocket_clients:
            del websocket_clients[backtest_id]


async def send_backtest_update(backtest_id: str, update: Dict[str, Any]):
    """Send update to WebSocket client"""
    if backtest_id in websocket_clients:
        try:
            await websocket_clients[backtest_id].send_json(update)
        except:
            # Client disconnected
            del websocket_clients[backtest_id]


@app.get("/strategies/templates")
async def get_strategy_templates() -> List[Dict[str, Any]]:
    """Get pre-built strategy templates"""
    try:
        templates = await strategy_runner.get_strategy_templates()
        
        return templates
        
    except Exception as e:
        logger.error(f"Error fetching templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch templates: {str(e)}"
        )


@app.post("/strategies/validate")
async def validate_strategy(
    strategy: Strategy,
    current_user: User = Depends(get_current_verified_user)
) -> Dict[str, Any]:
    """Validate strategy code"""
    try:
        validation = await strategy_runner.validate_strategy(strategy)
        
        return validation
        
    except Exception as e:
        logger.error(f"Error validating strategy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate strategy: {str(e)}"
        )


@app.get("/backtests/{backtest_id}/signals", response_model=List[Signal])
async def get_backtest_signals(
    backtest_id: str,
    signal_type: Optional[SignalType] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_verified_user)
):
    """Get signals generated during backtest"""
    try:
        signals = await backtesting_engine.get_backtest_signals(
            backtest_id=backtest_id,
            user_id=str(current_user.id),
            signal_type=signal_type,
            limit=limit
        )
        
        return signals
        
    except Exception as e:
        logger.error(f"Error fetching signals: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch signals: {str(e)}"
        )


@app.get("/backtests/{backtest_id}/drawdown", response_model=DrawdownAnalysis)
async def get_drawdown_analysis(
    backtest_id: str,
    current_user: User = Depends(get_current_verified_user)
):
    """Get drawdown analysis"""
    try:
        analysis = await performance_analyzer.analyze_drawdowns(
            backtest_id=backtest_id,
            user_id=str(current_user.id)
        )
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
            
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing drawdowns: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze drawdowns: {str(e)}"
        )


@app.get("/backtests/{backtest_id}/risk", response_model=RiskMetrics)
async def get_risk_analysis(
    backtest_id: str,
    current_user: User = Depends(get_current_verified_user)
):
    """Get risk metrics analysis"""
    try:
        metrics = await performance_analyzer.analyze_risk(
            backtest_id=backtest_id,
            user_id=str(current_user.id)
        )
        
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Risk analysis not found"
            )
            
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing risk: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze risk: {str(e)}"
        )


@app.post("/backtests/compare")
async def compare_backtests(
    backtest_ids: List[str],
    current_user: User = Depends(get_current_verified_user)
) -> Dict[str, Any]:
    """Compare multiple backtest results"""
    try:
        if len(backtest_ids) < 2 or len(backtest_ids) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please provide 2-5 backtest IDs for comparison"
            )
            
        comparison = await performance_analyzer.compare_backtests(
            backtest_ids=backtest_ids,
            user_id=str(current_user.id)
        )
        
        return comparison
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing backtests: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare backtests: {str(e)}"
        )


@app.post("/backtests/{backtest_id}/export")
async def export_backtest_results(
    backtest_id: str,
    format: str = "json",  # json, csv, excel
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_verified_user)
):
    """Export backtest results"""
    try:
        # Queue export task
        export_id = f"export_{datetime.now().timestamp()}"
        
        background_tasks.add_task(
            backtesting_engine.export_results,
            backtest_id,
            export_id,
            format,
            str(current_user.id)
        )
        
        return {
            "status": "processing",
            "export_id": export_id,
            "message": "Export is being prepared"
        }
        
    except Exception as e:
        logger.error(f"Error exporting results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export results: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8018,
        reload=True
    ) 