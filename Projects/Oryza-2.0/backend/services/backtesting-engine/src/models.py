"""
Data models for Backtesting Engine Service
"""
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
import uuid


class StrategyType(str, Enum):
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    MOMENTUM = "momentum"
    ARBITRAGE = "arbitrage"
    MARKET_MAKING = "market_making"
    PAIRS_TRADING = "pairs_trading"
    MACHINE_LEARNING = "machine_learning"
    CUSTOM = "custom"


class StrategyStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"
    DEPRECATED = "deprecated"


class BacktestStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TradeType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    SHORT = "short"
    COVER = "cover"


class TradeStatus(str, Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class PositionStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    PARTIALLY_CLOSED = "partially_closed"


class SignalType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    EXIT = "exit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class DataFrequency(str, Enum):
    TICK = "tick"
    SECOND_1 = "1s"
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAILY = "1d"
    WEEKLY = "1w"
    MONTHLY = "1mo"


class Strategy(BaseModel):
    """Trading strategy definition"""
    strategy_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    
    # Basic info
    name: str
    description: str
    strategy_type: StrategyType
    
    # Strategy code/configuration
    code: Optional[str] = None  # Python code for custom strategies
    parameters: Dict[str, Any] = {}  # Strategy parameters
    
    # Trading rules
    entry_rules: Dict[str, Any] = {}
    exit_rules: Dict[str, Any] = {}
    risk_rules: Dict[str, Any] = {}
    
    # Position sizing
    position_sizing: Dict[str, Any] = {
        "method": "fixed",  # fixed, percent, kelly, risk_parity
        "value": 1000  # Amount or percentage
    }
    
    # Risk management
    stop_loss: Optional[float] = None  # Percentage
    take_profit: Optional[float] = None  # Percentage
    max_positions: int = 1
    max_exposure: Optional[Decimal] = None
    
    # Markets
    symbols: List[str] = []
    asset_classes: List[str] = []
    
    # Status
    status: StrategyStatus = StrategyStatus.DRAFT
    
    # Performance tracking
    backtest_count: int = 0
    avg_return: Optional[float] = None
    avg_sharpe: Optional[float] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @validator('parameters')
    def validate_parameters(cls, v, values):
        # Ensure required parameters based on strategy type
        strategy_type = values.get('strategy_type')
        
        if strategy_type == StrategyType.TREND_FOLLOWING:
            required = ["fast_period", "slow_period"]
        elif strategy_type == StrategyType.MEAN_REVERSION:
            required = ["lookback_period", "entry_threshold", "exit_threshold"]
        elif strategy_type == StrategyType.MOMENTUM:
            required = ["momentum_period", "entry_percentile"]
        else:
            required = []
            
        for param in required:
            if param not in v:
                raise ValueError(f"Missing required parameter: {param}")
                
        return v


class BacktestConfig(BaseModel):
    """Backtest configuration"""
    strategy_id: str
    
    # Time period
    start_date: date
    end_date: date
    
    # Data settings
    symbols: List[str]
    data_frequency: DataFrequency = DataFrequency.DAILY
    
    # Capital settings
    initial_capital: Decimal = Decimal("100000")
    currency: str = "USD"
    
    # Execution settings
    commission: Decimal = Decimal("0.001")  # 0.1%
    slippage: Decimal = Decimal("0.0005")  # 0.05%
    
    # Risk settings
    max_positions: Optional[int] = None
    max_exposure: Optional[Decimal] = None
    margin_requirement: float = 1.0  # 1.0 = no leverage
    
    # Features
    use_stops: bool = True
    reinvest_profits: bool = True
    
    # Advanced settings
    warm_up_period: int = 0  # Bars to skip at start
    random_seed: Optional[int] = None  # For reproducibility
    
    @validator('end_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError("End date must be after start date")
        return v


class Backtest(BaseModel):
    """Backtest instance"""
    backtest_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    strategy_id: str
    
    # Configuration
    config: BacktestConfig
    
    # Status
    status: BacktestStatus = BacktestStatus.CREATED
    progress: float = 0.0  # 0-100
    current_date: Optional[date] = None
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    
    # Results summary
    total_return: Optional[float] = None
    total_trades: Optional[int] = None
    winning_trades: Optional[int] = None
    losing_trades: Optional[int] = None
    
    # Error handling
    error_message: Optional[str] = None
    warnings: List[str] = []
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)


class Trade(BaseModel):
    """Executed trade in backtest"""
    trade_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    backtest_id: str
    
    # Trade details
    symbol: str
    trade_type: TradeType
    quantity: Decimal
    price: Decimal
    
    # Execution
    executed_at: datetime
    status: TradeStatus = TradeStatus.EXECUTED
    
    # Costs
    commission: Decimal
    slippage: Decimal
    total_cost: Decimal
    
    # Position tracking
    position_id: Optional[str] = None
    is_entry: bool = True  # Entry or exit trade
    
    # P&L (for exit trades)
    realized_pnl: Optional[Decimal] = None
    pnl_percentage: Optional[float] = None
    
    # Signal that triggered trade
    signal_id: Optional[str] = None
    signal_strength: Optional[float] = None
    
    # Market conditions
    market_price: Decimal  # Price before slippage
    spread: Optional[Decimal] = None
    volume: Optional[Decimal] = None


class Position(BaseModel):
    """Open position tracking"""
    position_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    backtest_id: str
    
    # Position details
    symbol: str
    quantity: Decimal  # Positive for long, negative for short
    entry_price: Decimal
    current_price: Decimal
    
    # Status
    status: PositionStatus = PositionStatus.OPEN
    
    # Timing
    opened_at: datetime
    closed_at: Optional[datetime] = None
    holding_period_days: Optional[int] = None
    
    # P&L
    unrealized_pnl: Decimal
    realized_pnl: Decimal = Decimal("0")
    total_pnl: Decimal
    pnl_percentage: float
    
    # Risk metrics
    max_profit: Decimal = Decimal("0")
    max_loss: Decimal = Decimal("0")
    current_risk: Decimal
    
    # Stop/target levels
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    
    # Trades
    entry_trade_id: str
    exit_trade_ids: List[str] = []


class Signal(BaseModel):
    """Trading signal generated by strategy"""
    signal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    backtest_id: str
    
    # Signal details
    symbol: str
    signal_type: SignalType
    strength: float = Field(ge=0, le=1)  # 0-1 confidence
    
    # Timing
    generated_at: datetime
    valid_until: Optional[datetime] = None
    
    # Price levels
    current_price: Decimal
    target_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    
    # Indicators that triggered signal
    indicators: Dict[str, float] = {}
    
    # Execution
    was_executed: bool = False
    execution_trade_id: Optional[str] = None
    
    # Metadata
    reason: str  # Human-readable reason
    metadata: Dict[str, Any] = {}


class MarketData(BaseModel):
    """Historical market data point"""
    symbol: str
    timestamp: datetime
    
    # OHLCV data
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    
    # Additional data
    vwap: Optional[Decimal] = None
    trade_count: Optional[int] = None
    
    # Bid/Ask (for more granular data)
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    bid_size: Optional[Decimal] = None
    ask_size: Optional[Decimal] = None
    
    @validator('high')
    def validate_high(cls, v, values):
        if 'low' in values and v < values['low']:
            raise ValueError("High must be >= low")
        return v


class Portfolio(BaseModel):
    """Portfolio state at a point in time"""
    backtest_id: str
    timestamp: datetime
    
    # Capital
    cash: Decimal
    positions_value: Decimal
    total_value: Decimal
    
    # Positions
    positions: List[Position] = []
    position_count: int
    
    # Exposure
    gross_exposure: Decimal
    net_exposure: Decimal
    leverage: float
    
    # P&L
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    total_pnl: Decimal
    
    # Daily metrics
    daily_return: Optional[float] = None
    daily_pnl: Optional[Decimal] = None


class PortfolioSnapshot(BaseModel):
    """Simplified portfolio snapshot for charting"""
    timestamp: datetime
    total_value: Decimal
    cash: Decimal
    positions_value: Decimal
    pnl: Decimal
    daily_return: Optional[float] = None
    drawdown: Optional[float] = None


class BacktestResult(BaseModel):
    """Complete backtest results"""
    backtest_id: str
    strategy_id: str
    
    # Summary statistics
    total_return: float
    annual_return: float
    total_pnl: Decimal
    
    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    avg_win: Decimal
    avg_loss: Decimal
    profit_factor: float
    expectancy: Decimal
    
    # Risk metrics
    max_drawdown: float
    max_drawdown_duration_days: int
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    
    # Additional metrics
    avg_trade_duration_days: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    
    # Best/worst trades
    best_trade: Optional[Trade] = None
    worst_trade: Optional[Trade] = None
    
    # Monthly returns
    monthly_returns: Dict[str, float] = {}
    
    # Execution quality
    total_commission: Decimal
    total_slippage: Decimal
    
    # Portfolio metrics
    final_portfolio_value: Decimal
    peak_portfolio_value: Decimal
    
    # Time metrics
    time_in_market: float  # Percentage
    longest_holding_period_days: int
    
    # Export data
    equity_curve: List[PortfolioSnapshot] = []
    trade_list: List[Trade] = []


class PerformanceMetrics(BaseModel):
    """Detailed performance metrics"""
    backtest_id: str
    
    # Returns
    total_return: float
    annual_return: float
    monthly_return: float
    daily_return: float
    
    # Volatility
    annual_volatility: float
    monthly_volatility: float
    daily_volatility: float
    downside_volatility: float
    
    # Risk-adjusted returns
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    information_ratio: Optional[float] = None
    
    # Risk metrics
    max_drawdown: float
    avg_drawdown: float
    drawdown_duration: int
    var_95: float  # Value at Risk
    cvar_95: float  # Conditional VaR
    
    # Trade metrics
    win_rate: float
    profit_factor: float
    expectancy: Decimal
    avg_win_loss_ratio: float
    
    # Statistical measures
    skewness: float
    kurtosis: float
    
    # Stability metrics
    stability_r_squared: float  # R² of equity curve
    tail_ratio: float  # Ratio of 95th percentile to 5th percentile
    
    # Recovery metrics
    recovery_factor: float  # Total return / max drawdown
    
    calculated_at: datetime = Field(default_factory=datetime.now)


class DrawdownAnalysis(BaseModel):
    """Drawdown analysis results"""
    backtest_id: str
    
    # Current drawdown
    current_drawdown: float
    current_drawdown_start: Optional[date] = None
    current_drawdown_days: int = 0
    
    # Maximum drawdown
    max_drawdown: float
    max_drawdown_start: date
    max_drawdown_end: date
    max_drawdown_recovery: Optional[date] = None
    max_drawdown_days: int
    
    # Top drawdowns
    top_5_drawdowns: List[Dict[str, Any]] = []
    
    # Statistics
    avg_drawdown: float
    avg_drawdown_days: int
    total_drawdown_periods: int
    
    # Recovery
    avg_recovery_days: int
    longest_recovery_days: int
    
    # Underwater curve
    underwater_curve: List[Dict[str, Any]] = []  # timestamp -> drawdown %


class RiskMetrics(BaseModel):
    """Risk analysis metrics"""
    backtest_id: str
    
    # Volatility measures
    daily_volatility: float
    annual_volatility: float
    downside_deviation: float
    upside_deviation: float
    
    # Tail risk
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float
    
    # Drawdown risk
    max_drawdown: float
    avg_drawdown: float
    drawdown_frequency: float  # Drawdowns per year
    
    # Greeks (if applicable)
    beta: Optional[float] = None
    alpha: Optional[float] = None
    
    # Correlation
    correlation_to_market: Optional[float] = None
    
    # Risk ratios
    gain_to_pain_ratio: float
    omega_ratio: float
    
    # Kelly criterion
    kelly_fraction: float
    
    # Risk-adjusted metrics
    risk_adjusted_return: float
    
    calculated_at: datetime = Field(default_factory=datetime.now) 