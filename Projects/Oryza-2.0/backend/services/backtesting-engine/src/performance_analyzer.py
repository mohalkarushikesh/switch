"""
Performance Analyzer - Analyzes backtest performance metrics
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
import logging
from decimal import Decimal
import numpy as np
import pandas as pd
from scipy import stats

from .models import (
    PerformanceMetrics, DrawdownAnalysis, RiskMetrics,
    BacktestResult, PortfolioSnapshot
)


class PerformanceAnalyzer:
    """
    Analyzes backtest performance and risk metrics
    """
    
    def __init__(self):
        self.logger = logging.getLogger("performance_analyzer")
        
        # Cache for computed metrics
        self.metrics_cache = {}  # backtest_id -> metrics
        self.drawdown_cache = {}  # backtest_id -> drawdown analysis
        self.risk_cache = {}  # backtest_id -> risk metrics
        
    async def initialize(self):
        """Initialize performance analyzer"""
        self.logger.info("Initializing Performance Analyzer")
        
    async def calculate_metrics(
        self,
        backtest_id: str,
        user_id: Optional[str] = None
    ) -> Optional[PerformanceMetrics]:
        """Calculate comprehensive performance metrics"""
        # Check cache
        if backtest_id in self.metrics_cache:
            return self.metrics_cache[backtest_id]
            
        # Get backtest data
        from .backtesting_engine import backtesting_engine
        
        backtest = await backtesting_engine.get_backtest(backtest_id, user_id)
        if not backtest:
            return None
            
        portfolio_history = await backtesting_engine.get_portfolio_history(backtest_id, user_id)
        if not portfolio_history:
            return None
            
        trades = await backtesting_engine.get_backtest_trades(backtest_id, user_id, limit=10000)
        
        # Calculate returns series
        returns = self._calculate_returns_series(portfolio_history)
        
        if len(returns) < 2:
            return None
            
        # Calculate basic return metrics
        total_return = float((portfolio_history[-1].total_value - backtest.config.initial_capital) / 
                           backtest.config.initial_capital * 100)
        
        days = (backtest.config.end_date - backtest.config.start_date).days
        annual_return = ((1 + total_return / 100) ** (365 / days) - 1) * 100 if days > 0 else 0
        
        # Calculate volatility
        daily_volatility = float(returns.std())
        annual_volatility = daily_volatility * np.sqrt(252)
        monthly_volatility = daily_volatility * np.sqrt(21)
        
        # Downside volatility (Sortino)
        downside_returns = returns[returns < 0]
        downside_volatility = float(downside_returns.std()) * np.sqrt(252) if len(downside_returns) > 0 else 0
        
        # Risk-adjusted returns
        risk_free_rate = 0.02  # 2% annual
        daily_rf = risk_free_rate / 252
        
        excess_returns = returns - daily_rf
        sharpe_ratio = float(excess_returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
        
        sortino_ratio = float((annual_return - risk_free_rate) / downside_volatility) if downside_volatility > 0 else 0
        
        # Calmar ratio (return / max drawdown)
        drawdown_analysis = await self.analyze_drawdowns(backtest_id, user_id)
        max_drawdown = drawdown_analysis.max_drawdown if drawdown_analysis else 0
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # VaR and CVaR
        var_95 = float(np.percentile(returns, 5))
        cvar_95 = float(returns[returns <= var_95].mean()) if len(returns[returns <= var_95]) > 0 else var_95
        
        # Trade metrics
        exit_trades = [t for t in trades if not t.is_entry and t.realized_pnl is not None]
        winning_trades = [t for t in exit_trades if t.realized_pnl > 0]
        losing_trades = [t for t in exit_trades if t.realized_pnl < 0]
        
        win_rate = len(winning_trades) / len(exit_trades) if exit_trades else 0
        
        avg_win = sum(t.realized_pnl for t in winning_trades) / len(winning_trades) if winning_trades else Decimal("0")
        avg_loss = sum(t.realized_pnl for t in losing_trades) / len(losing_trades) if losing_trades else Decimal("0")
        
        profit_factor = abs(sum(t.realized_pnl for t in winning_trades) / sum(t.realized_pnl for t in losing_trades)) if losing_trades else 0
        
        expectancy = (avg_win * Decimal(str(win_rate)) + avg_loss * Decimal(str(1 - win_rate))) if exit_trades else Decimal("0")
        
        avg_win_loss_ratio = float(avg_win / abs(avg_loss)) if avg_loss != 0 else 0
        
        # Statistical measures
        skewness = float(stats.skew(returns))
        kurtosis = float(stats.kurtosis(returns))
        
        # Stability (R-squared of equity curve)
        x = np.arange(len(portfolio_history))
        y = [float(s.total_value) for s in portfolio_history]
        
        if len(x) > 1:
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            stability_r_squared = r_value ** 2
        else:
            stability_r_squared = 0
            
        # Tail ratio
        percentile_95 = float(np.percentile(returns, 95))
        percentile_5 = float(np.percentile(returns, 5))
        tail_ratio = abs(percentile_95 / percentile_5) if percentile_5 != 0 else 0
        
        # Recovery factor
        recovery_factor = total_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        metrics = PerformanceMetrics(
            backtest_id=backtest_id,
            total_return=total_return,
            annual_return=annual_return,
            monthly_return=annual_return / 12,
            daily_return=total_return / days if days > 0 else 0,
            annual_volatility=annual_volatility,
            monthly_volatility=monthly_volatility,
            daily_volatility=daily_volatility,
            downside_volatility=downside_volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            information_ratio=None,  # Would need benchmark
            max_drawdown=max_drawdown,
            avg_drawdown=drawdown_analysis.avg_drawdown if drawdown_analysis else 0,
            drawdown_duration=drawdown_analysis.max_drawdown_days if drawdown_analysis else 0,
            var_95=var_95,
            cvar_95=cvar_95,
            win_rate=win_rate,
            profit_factor=profit_factor,
            expectancy=expectancy,
            avg_win_loss_ratio=avg_win_loss_ratio,
            skewness=skewness,
            kurtosis=kurtosis,
            stability_r_squared=stability_r_squared,
            tail_ratio=tail_ratio,
            recovery_factor=recovery_factor
        )
        
        # Cache result
        self.metrics_cache[backtest_id] = metrics
        
        return metrics
        
    def _calculate_returns_series(
        self,
        portfolio_history: List[PortfolioSnapshot]
    ) -> pd.Series:
        """Calculate returns series from portfolio history"""
        values = []
        dates = []
        
        for snapshot in portfolio_history:
            values.append(float(snapshot.total_value))
            dates.append(snapshot.timestamp.date())
            
        if len(values) < 2:
            return pd.Series()
            
        series = pd.Series(values, index=dates)
        returns = series.pct_change().dropna()
        
        return returns
        
    async def analyze_drawdowns(
        self,
        backtest_id: str,
        user_id: Optional[str] = None
    ) -> Optional[DrawdownAnalysis]:
        """Analyze drawdown characteristics"""
        # Check cache
        if backtest_id in self.drawdown_cache:
            return self.drawdown_cache[backtest_id]
            
        # Get portfolio history
        from .backtesting_engine import backtesting_engine
        
        portfolio_history = await backtesting_engine.get_portfolio_history(backtest_id, user_id)
        if not portfolio_history:
            return None
            
        # Calculate drawdown series
        values = [float(s.total_value) for s in portfolio_history]
        dates = [s.timestamp.date() for s in portfolio_history]
        
        # Calculate running maximum
        running_max = pd.Series(values).expanding().max()
        
        # Calculate drawdown percentage
        drawdown_series = (pd.Series(values) - running_max) / running_max * 100
        
        # Find drawdown periods
        drawdown_periods = []
        in_drawdown = False
        current_period = None
        
        for i, dd in enumerate(drawdown_series):
            if dd < 0 and not in_drawdown:
                # Start of drawdown
                in_drawdown = True
                current_period = {
                    "start_idx": i,
                    "start_date": dates[i],
                    "peak_value": values[i-1] if i > 0 else values[i]
                }
            elif dd >= 0 and in_drawdown:
                # End of drawdown
                in_drawdown = False
                if current_period:
                    # Find the trough
                    trough_idx = current_period["start_idx"] + drawdown_series[current_period["start_idx"]:i].idxmin() - current_period["start_idx"]
                    
                    current_period.update({
                        "end_idx": i,
                        "end_date": dates[i],
                        "trough_idx": trough_idx,
                        "trough_date": dates[trough_idx],
                        "trough_value": values[trough_idx],
                        "recovery_date": dates[i],
                        "max_drawdown": float(drawdown_series[trough_idx]),
                        "duration_days": (dates[i] - current_period["start_date"]).days
                    })
                    drawdown_periods.append(current_period)
                    
        # Handle ongoing drawdown
        if in_drawdown and current_period:
            trough_idx = current_period["start_idx"] + drawdown_series[current_period["start_idx"]:].idxmin() - current_period["start_idx"]
            current_period.update({
                "end_idx": len(values) - 1,
                "end_date": dates[-1],
                "trough_idx": trough_idx,
                "trough_date": dates[trough_idx],
                "trough_value": values[trough_idx],
                "recovery_date": None,
                "max_drawdown": float(drawdown_series[trough_idx]),
                "duration_days": (dates[-1] - current_period["start_date"]).days
            })
            drawdown_periods.append(current_period)
            
        # Find maximum drawdown
        if drawdown_periods:
            max_dd_period = max(drawdown_periods, key=lambda x: abs(x["max_drawdown"]))
        else:
            max_dd_period = None
            
        # Calculate statistics
        current_drawdown = float(drawdown_series.iloc[-1]) if len(drawdown_series) > 0 else 0
        
        analysis = DrawdownAnalysis(
            backtest_id=backtest_id,
            current_drawdown=current_drawdown,
            current_drawdown_start=dates[-1] if current_drawdown < 0 else None,
            current_drawdown_days=0,  # Would calculate
            max_drawdown=max_dd_period["max_drawdown"] if max_dd_period else 0,
            max_drawdown_start=max_dd_period["start_date"] if max_dd_period else dates[0],
            max_drawdown_end=max_dd_period["trough_date"] if max_dd_period else dates[0],
            max_drawdown_recovery=max_dd_period["recovery_date"] if max_dd_period else None,
            max_drawdown_days=max_dd_period["duration_days"] if max_dd_period else 0,
            top_5_drawdowns=[
                {
                    "rank": i + 1,
                    "drawdown": dd["max_drawdown"],
                    "start": dd["start_date"].isoformat(),
                    "end": dd["trough_date"].isoformat(),
                    "duration_days": dd["duration_days"]
                }
                for i, dd in enumerate(sorted(drawdown_periods, key=lambda x: abs(x["max_drawdown"]), reverse=True)[:5])
            ],
            avg_drawdown=float(drawdown_series[drawdown_series < 0].mean()) if len(drawdown_series[drawdown_series < 0]) > 0 else 0,
            avg_drawdown_days=sum(dd["duration_days"] for dd in drawdown_periods) / len(drawdown_periods) if drawdown_periods else 0,
            total_drawdown_periods=len(drawdown_periods),
            avg_recovery_days=sum(dd["duration_days"] for dd in drawdown_periods if dd.get("recovery_date")) / 
                           len([dd for dd in drawdown_periods if dd.get("recovery_date")]) if drawdown_periods else 0,
            longest_recovery_days=max((dd["duration_days"] for dd in drawdown_periods if dd.get("recovery_date")), default=0),
            underwater_curve=[
                {"date": date.isoformat(), "drawdown": float(dd)}
                for date, dd in zip(dates, drawdown_series)
            ]
        )
        
        # Cache result
        self.drawdown_cache[backtest_id] = analysis
        
        return analysis
        
    async def analyze_risk(
        self,
        backtest_id: str,
        user_id: Optional[str] = None
    ) -> Optional[RiskMetrics]:
        """Analyze risk metrics"""
        # Check cache
        if backtest_id in self.risk_cache:
            return self.risk_cache[backtest_id]
            
        # Get data
        from .backtesting_engine import backtesting_engine
        
        portfolio_history = await backtesting_engine.get_portfolio_history(backtest_id, user_id)
        if not portfolio_history:
            return None
            
        # Calculate returns
        returns = self._calculate_returns_series(portfolio_history)
        
        if len(returns) < 2:
            return None
            
        # Volatility measures
        daily_volatility = float(returns.std())
        annual_volatility = daily_volatility * np.sqrt(252)
        
        # Separate positive and negative returns
        positive_returns = returns[returns > 0]
        negative_returns = returns[returns < 0]
        
        downside_deviation = float(negative_returns.std()) * np.sqrt(252) if len(negative_returns) > 0 else 0
        upside_deviation = float(positive_returns.std()) * np.sqrt(252) if len(positive_returns) > 0 else 0
        
        # VaR and CVaR
        var_95 = float(np.percentile(returns, 5))
        var_99 = float(np.percentile(returns, 1))
        cvar_95 = float(returns[returns <= var_95].mean()) if len(returns[returns <= var_95]) > 0 else var_95
        cvar_99 = float(returns[returns <= var_99].mean()) if len(returns[returns <= var_99]) > 0 else var_99
        
        # Drawdown analysis
        drawdown_analysis = await self.analyze_drawdowns(backtest_id, user_id)
        
        # Calculate gain to pain ratio
        total_return = float((portfolio_history[-1].total_value - portfolio_history[0].total_value) / 
                           portfolio_history[0].total_value)
        gain_to_pain = total_return / abs(drawdown_analysis.max_drawdown) if drawdown_analysis and drawdown_analysis.max_drawdown != 0 else 0
        
        # Omega ratio (probability weighted ratio of gains vs losses)
        threshold = 0  # Can be adjusted
        gains = returns[returns > threshold] - threshold
        losses = threshold - returns[returns <= threshold]
        
        omega_ratio = float(gains.sum() / losses.sum()) if losses.sum() > 0 else float('inf')
        
        # Kelly fraction (optimal bet size)
        win_rate = len(positive_returns) / len(returns) if len(returns) > 0 else 0
        avg_win = positive_returns.mean() if len(positive_returns) > 0 else 0
        avg_loss = abs(negative_returns.mean()) if len(negative_returns) > 0 else 0
        
        if avg_loss > 0:
            kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win if avg_win > 0 else 0
        else:
            kelly_fraction = 1.0 if win_rate > 0 else 0
            
        kelly_fraction = max(0, min(1, kelly_fraction))  # Bound between 0 and 1
        
        # Risk-adjusted return
        risk_adjusted_return = total_return / annual_volatility if annual_volatility > 0 else 0
        
        risk_metrics = RiskMetrics(
            backtest_id=backtest_id,
            daily_volatility=daily_volatility,
            annual_volatility=annual_volatility,
            downside_deviation=downside_deviation,
            upside_deviation=upside_deviation,
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            cvar_99=cvar_99,
            max_drawdown=drawdown_analysis.max_drawdown if drawdown_analysis else 0,
            avg_drawdown=drawdown_analysis.avg_drawdown if drawdown_analysis else 0,
            drawdown_frequency=drawdown_analysis.total_drawdown_periods / (len(portfolio_history) / 252) if drawdown_analysis and len(portfolio_history) > 252 else 0,
            beta=None,  # Would need market data
            alpha=None,  # Would need market data
            correlation_to_market=None,  # Would need market data
            gain_to_pain_ratio=gain_to_pain,
            omega_ratio=omega_ratio,
            kelly_fraction=kelly_fraction,
            risk_adjusted_return=risk_adjusted_return
        )
        
        # Cache result
        self.risk_cache[backtest_id] = risk_metrics
        
        return risk_metrics
        
    async def compare_backtests(
        self,
        backtest_ids: List[str],
        user_id: str
    ) -> Dict[str, Any]:
        """Compare multiple backtest results"""
        comparisons = {}
        
        for backtest_id in backtest_ids:
            metrics = await self.calculate_metrics(backtest_id, user_id)
            
            if metrics:
                comparisons[backtest_id] = {
                    "total_return": metrics.total_return,
                    "annual_return": metrics.annual_return,
                    "volatility": metrics.annual_volatility,
                    "sharpe_ratio": metrics.sharpe_ratio,
                    "max_drawdown": metrics.max_drawdown,
                    "win_rate": metrics.win_rate,
                    "profit_factor": metrics.profit_factor
                }
                
        if not comparisons:
            return {}
            
        # Calculate rankings
        metrics_to_rank = ["total_return", "annual_return", "sharpe_ratio", "profit_factor", "win_rate"]
        metrics_to_rank_inverse = ["volatility", "max_drawdown"]  # Lower is better
        
        rankings = {metric: {} for metric in metrics_to_rank + metrics_to_rank_inverse}
        
        for metric in metrics_to_rank:
            sorted_ids = sorted(comparisons.keys(), key=lambda x: comparisons[x][metric], reverse=True)
            for rank, backtest_id in enumerate(sorted_ids, 1):
                rankings[metric][backtest_id] = rank
                
        for metric in metrics_to_rank_inverse:
            sorted_ids = sorted(comparisons.keys(), key=lambda x: comparisons[x][metric])
            for rank, backtest_id in enumerate(sorted_ids, 1):
                rankings[metric][backtest_id] = rank
                
        # Calculate overall score
        overall_scores = {}
        for backtest_id in backtest_ids:
            scores = [rankings[metric].get(backtest_id, len(backtest_ids)) for metric in rankings]
            overall_scores[backtest_id] = sum(scores) / len(scores)
            
        # Sort by overall score (lower is better)
        best_backtest = min(overall_scores.keys(), key=lambda x: overall_scores[x])
        
        return {
            "backtests": comparisons,
            "rankings": rankings,
            "overall_scores": overall_scores,
            "best_backtest": best_backtest,
            "comparison_metrics": {
                "best_return": max(comparisons.values(), key=lambda x: x["total_return"]),
                "best_sharpe": max(comparisons.values(), key=lambda x: x["sharpe_ratio"]),
                "lowest_risk": min(comparisons.values(), key=lambda x: x["volatility"])
            }
        } 