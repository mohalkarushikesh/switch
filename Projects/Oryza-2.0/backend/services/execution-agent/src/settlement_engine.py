"""
Settlement Engine - Manages trade settlement and clearing
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from decimal import Decimal

from .models import (
    Trade, Settlement, SettlementStatus,
    OrderSide
)


class SettlementEngine:
    """
    Manages trade settlement and clearing processes
    """
    
    def __init__(self):
        self.logger = logging.getLogger("settlement_engine")
        self.settlements = {}  # settlement_id -> Settlement
        self.settlement_queue = asyncio.Queue()
        self.is_processing = False
        
    async def initialize(self):
        """Initialize settlement engine"""
        self.logger.info("Initializing Settlement Engine")
        # In production, connect to settlement systems
        
    async def create_settlement(self, trade: Trade) -> Settlement:
        """Create a settlement record for a trade"""
        settlement = Settlement(
            trade_id=trade.trade_id,
            user_id=trade.order_id[:36],  # Extract user_id (mock)
            symbol=trade.symbol,
            side=trade.side,
            quantity=trade.quantity,
            amount=trade.net_amount,
            trade_date=trade.executed_at,
            settlement_date=trade.settlement_date,
            broker=trade.broker,
            broker_reference=trade.broker_trade_id
        )
        
        # Store settlement
        self.settlements[settlement.settlement_id] = settlement
        
        # Queue for processing
        await self.settlement_queue.put(settlement)
        
        self.logger.info(
            f"Created settlement {settlement.settlement_id} "
            f"for trade {trade.trade_id}"
        )
        
        return settlement
        
    async def process_settlements(self):
        """Process settlement queue"""
        self.is_processing = True
        self.logger.info("Started settlement processing")
        
        while self.is_processing:
            try:
                # Get settlements to process
                settlements_to_process = []
                
                # Check for settlements due today
                today = datetime.now().date()
                
                for settlement in self.settlements.values():
                    if (settlement.status == SettlementStatus.PENDING and
                        settlement.settlement_date.date() <= today):
                        settlements_to_process.append(settlement)
                        
                # Process settlements
                for settlement in settlements_to_process:
                    await self._process_single_settlement(settlement)
                    
                # Also process new settlements from queue
                try:
                    settlement = await asyncio.wait_for(
                        self.settlement_queue.get(),
                        timeout=5.0
                    )
                    
                    if settlement.settlement_date.date() <= today:
                        await self._process_single_settlement(settlement)
                        
                except asyncio.TimeoutError:
                    pass
                    
                # Wait before next cycle
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error processing settlements: {str(e)}")
                await asyncio.sleep(60)
                
    async def _process_single_settlement(self, settlement: Settlement):
        """Process a single settlement"""
        try:
            self.logger.info(f"Processing settlement {settlement.settlement_id}")
            
            # Update status
            settlement.status = SettlementStatus.PROCESSING
            
            # Simulate settlement process
            # In production, this would involve:
            # 1. Verify trade details
            # 2. Check account balances
            # 3. Process with clearing house
            # 4. Update positions
            # 5. Update cash balances
            
            # For now, simulate processing
            await asyncio.sleep(1)
            
            # Mock settlement logic
            if settlement.side == OrderSide.BUY:
                # Debit cash, credit securities
                await self._process_buy_settlement(settlement)
            else:
                # Credit cash, debit securities
                await self._process_sell_settlement(settlement)
                
            # Mark as completed
            settlement.status = SettlementStatus.COMPLETED
            settlement.completed_at = datetime.now()
            
            self.logger.info(
                f"Settlement {settlement.settlement_id} completed successfully"
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to process settlement {settlement.settlement_id}: {str(e)}"
            )
            
            settlement.status = SettlementStatus.FAILED
            settlement.error_message = str(e)
            settlement.retry_count += 1
            
            # Retry if under limit
            if settlement.retry_count < 3:
                settlement.status = SettlementStatus.PENDING
                await asyncio.sleep(300)  # Retry after 5 minutes
                
    async def _process_buy_settlement(self, settlement: Settlement):
        """Process buy side settlement"""
        # In production:
        # 1. Verify sufficient cash balance
        # 2. Debit cash account
        # 3. Credit securities to account
        # 4. Update position records
        
        self.logger.info(
            f"Processing BUY settlement: "
            f"{settlement.quantity} {settlement.symbol} "
            f"for ${settlement.amount}"
        )
        
        # Mock processing
        await asyncio.sleep(0.5)
        
    async def _process_sell_settlement(self, settlement: Settlement):
        """Process sell side settlement"""
        # In production:
        # 1. Verify sufficient security balance
        # 2. Debit securities from account
        # 3. Credit cash account
        # 4. Update position records
        
        self.logger.info(
            f"Processing SELL settlement: "
            f"{settlement.quantity} {settlement.symbol} "
            f"for ${settlement.amount}"
        )
        
        # Mock processing
        await asyncio.sleep(0.5)
        
    async def get_user_settlements(
        self,
        user_id: str,
        status: Optional[SettlementStatus] = None,
        since: Optional[datetime] = None
    ) -> List[Settlement]:
        """Get user's settlements"""
        settlements = []
        
        for settlement in self.settlements.values():
            if settlement.user_id == user_id:
                if status and settlement.status != status:
                    continue
                    
                if since and settlement.trade_date < since:
                    continue
                    
                settlements.append(settlement)
                
        # Sort by trade date descending
        settlements.sort(key=lambda s: s.trade_date, reverse=True)
        
        return settlements
        
    async def get_pending_settlements(self) -> List[Settlement]:
        """Get all pending settlements"""
        return [
            s for s in self.settlements.values()
            if s.status == SettlementStatus.PENDING
        ]
        
    async def cancel_settlement(
        self,
        settlement_id: str,
        reason: str
    ) -> bool:
        """Cancel a settlement"""
        settlement = self.settlements.get(settlement_id)
        
        if not settlement:
            return False
            
        if settlement.status != SettlementStatus.PENDING:
            return False
            
        settlement.status = SettlementStatus.CANCELLED
        settlement.error_message = f"Cancelled: {reason}"
        
        self.logger.info(f"Settlement {settlement_id} cancelled: {reason}")
        
        return True
        
    async def get_settlement_summary(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get settlement summary for user"""
        since = datetime.now() - timedelta(days=days)
        settlements = await self.get_user_settlements(user_id, since=since)
        
        # Calculate summary
        total_buy_amount = Decimal("0")
        total_sell_amount = Decimal("0")
        pending_count = 0
        completed_count = 0
        failed_count = 0
        
        for settlement in settlements:
            if settlement.side == OrderSide.BUY:
                total_buy_amount += settlement.amount
            else:
                total_sell_amount += settlement.amount
                
            if settlement.status == SettlementStatus.PENDING:
                pending_count += 1
            elif settlement.status == SettlementStatus.COMPLETED:
                completed_count += 1
            elif settlement.status == SettlementStatus.FAILED:
                failed_count += 1
                
        return {
            "period_days": days,
            "total_settlements": len(settlements),
            "total_buy_amount": total_buy_amount,
            "total_sell_amount": total_sell_amount,
            "net_amount": total_sell_amount - total_buy_amount,
            "pending_count": pending_count,
            "completed_count": completed_count,
            "failed_count": failed_count,
            "success_rate": completed_count / len(settlements) if settlements else 0
        }
        
    async def reconcile_settlements(self, date: datetime.date):
        """Reconcile settlements for a given date"""
        # In production, this would:
        # 1. Compare internal records with broker records
        # 2. Identify discrepancies
        # 3. Generate reconciliation report
        # 4. Flag issues for manual review
        
        self.logger.info(f"Running settlement reconciliation for {date}")
        
        settlements_for_date = [
            s for s in self.settlements.values()
            if s.settlement_date.date() == date
        ]
        
        # Mock reconciliation
        discrepancies = []
        
        for settlement in settlements_for_date:
            # Simulate random discrepancy
            import random
            if random.random() < 0.05:  # 5% discrepancy rate
                discrepancies.append({
                    "settlement_id": settlement.settlement_id,
                    "type": "amount_mismatch",
                    "internal_amount": settlement.amount,
                    "broker_amount": settlement.amount + Decimal("0.01")
                })
                
        if discrepancies:
            self.logger.warning(
                f"Found {len(discrepancies)} discrepancies in reconciliation"
            )
        else:
            self.logger.info("Reconciliation completed successfully")
            
        return {
            "date": date,
            "total_settlements": len(settlements_for_date),
            "discrepancies": discrepancies,
            "status": "completed"
        } 