"""
Order Manager - Manages order lifecycle and execution
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from decimal import Decimal
import uuid

from .models import (
    Order, OrderStatus, OrderType, OrderSide,
    ExecutionReport, ExecutionType, Trade,
    OrderRoutingDecision
)


class OrderManager:
    """
    Manages order lifecycle from submission to execution
    """
    
    def __init__(self):
        self.logger = logging.getLogger("order_manager")
        self.orders = {}  # order_id -> Order
        self.order_queue = asyncio.Queue()
        self.execution_reports = {}  # order_id -> List[ExecutionReport]
        self.is_processing = False
        
    async def initialize(self):
        """Initialize order manager"""
        self.logger.info("Initializing Order Manager")
        # In production, connect to order database and recovery
        
    async def submit_order(self, order: Order) -> Order:
        """Submit a new order"""
        # Store order
        self.orders[order.order_id] = order
        
        # Initialize execution reports
        self.execution_reports[order.order_id] = []
        
        # Update status
        order.status = OrderStatus.SUBMITTED
        order.submitted_at = datetime.now()
        
        # Create new order execution report
        exec_report = ExecutionReport(
            order_id=order.order_id,
            exec_type=ExecutionType.NEW,
            symbol=order.symbol,
            side=order.side,
            leaves_quantity=order.quantity,
            order_status=order.status,
            broker=order.broker or "SMART",
            text="Order submitted"
        )
        
        self.execution_reports[order.order_id].append(exec_report)
        
        self.logger.info(f"Order {order.order_id} submitted: {order.symbol} {order.side} {order.quantity}")
        
        return order
        
    async def submit_batch_orders(self, orders: List[Order]) -> List[Order]:
        """Submit multiple orders"""
        submitted_orders = []
        
        for order in orders:
            try:
                submitted = await self.submit_order(order)
                submitted_orders.append(submitted)
            except Exception as e:
                self.logger.error(f"Failed to submit order: {str(e)}")
                
        return submitted_orders
        
    async def execute_order(self, order: Order):
        """Execute an order (send to broker)"""
        try:
            # Queue for execution
            await self.order_queue.put(order)
            
        except Exception as e:
            self.logger.error(f"Error queuing order {order.order_id}: {str(e)}")
            await self._reject_order(order, str(e))
            
    async def process_orders(self):
        """Process order queue"""
        self.is_processing = True
        self.logger.info("Started order processing")
        
        while self.is_processing:
            try:
                # Get order from queue
                order = await asyncio.wait_for(
                    self.order_queue.get(),
                    timeout=1.0
                )
                
                # Process order
                await self._process_single_order(order)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error processing orders: {str(e)}")
                
    async def _process_single_order(self, order: Order):
        """Process a single order"""
        try:
            # Make routing decision
            routing_decision = await self._make_routing_decision(order)
            
            # Update order with selected broker
            if not order.broker:
                order.broker = routing_decision.selected_broker
                
            # Send to broker (simulated)
            await self._send_to_broker(order)
            
        except Exception as e:
            self.logger.error(f"Error processing order {order.order_id}: {str(e)}")
            await self._reject_order(order, str(e))
            
    async def _make_routing_decision(self, order: Order) -> OrderRoutingDecision:
        """Decide which broker to route order to"""
        # In production, implement smart order routing
        # For now, simple logic
        
        decision = OrderRoutingDecision(
            order_id=order.order_id,
            selected_broker=order.broker or "DEFAULT_BROKER",
            routing_reason="Best execution"
        )
        
        # Score brokers (mock)
        decision.broker_scores = {
            "DEFAULT_BROKER": 0.95,
            "BROKER_B": 0.85,
            "BROKER_C": 0.75
        }
        
        return decision
        
    async def _send_to_broker(self, order: Order):
        """Send order to broker"""
        # In production, actual broker API call
        # For now, simulate execution
        
        # Update status
        order.status = OrderStatus.ACCEPTED
        order.broker_order_id = f"BROKER_{uuid.uuid4().hex[:8]}"
        
        # Create accepted execution report
        exec_report = ExecutionReport(
            order_id=order.order_id,
            exec_type=ExecutionType.NEW,
            symbol=order.symbol,
            side=order.side,
            leaves_quantity=order.quantity,
            order_status=order.status,
            broker=order.broker,
            broker_exec_id=order.broker_order_id,
            text="Order accepted by broker"
        )
        
        self.execution_reports[order.order_id].append(exec_report)
        
        # Simulate execution after delay
        if order.order_type == OrderType.MARKET:
            await asyncio.sleep(0.1)  # Fast execution
            await self._simulate_fill(order)
        else:
            # Limit orders may take longer
            asyncio.create_task(self._monitor_limit_order(order))
            
    async def _simulate_fill(self, order: Order):
        """Simulate order fill"""
        # In production, this comes from broker events
        
        # Simulate price
        if order.order_type == OrderType.MARKET:
            fill_price = Decimal("100.50")  # Mock market price
        else:
            fill_price = order.price
            
        # Create fill execution report
        exec_report = ExecutionReport(
            order_id=order.order_id,
            exec_type=ExecutionType.FILL,
            symbol=order.symbol,
            side=order.side,
            last_quantity=order.quantity,
            last_price=fill_price,
            cumulative_quantity=order.quantity,
            leaves_quantity=Decimal("0"),
            avg_price=fill_price,
            order_status=OrderStatus.FILLED,
            broker=order.broker,
            broker_exec_id=f"EXEC_{uuid.uuid4().hex[:8]}",
            commission=Decimal("1.00"),
            text="Order filled"
        )
        
        self.execution_reports[order.order_id].append(exec_report)
        
        # Update order
        order.update_fill(order.quantity, fill_price)
        order.commission = exec_report.commission
        
        # Create trade record
        trade = Trade(
            order_id=order.order_id,
            execution_id=exec_report.execution_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            commission=exec_report.commission,
            net_amount=self._calculate_net_amount(
                order.side, order.quantity, fill_price, exec_report.commission
            ),
            settlement_date=datetime.now() + timedelta(days=2),  # T+2
            broker=order.broker,
            broker_trade_id=exec_report.broker_exec_id,
            executed_at=datetime.now()
        )
        
        # In production, save trade and trigger settlement
        
        self.logger.info(
            f"Order {order.order_id} filled: "
            f"{order.quantity} @ {fill_price}"
        )
        
    async def _monitor_limit_order(self, order: Order):
        """Monitor limit order for execution"""
        # In production, this would monitor market prices
        # For simulation, execute after random delay
        
        await asyncio.sleep(5)  # Simulate market movement
        
        # Check if order still active
        if order.status in [OrderStatus.ACCEPTED, OrderStatus.PARTIALLY_FILLED]:
            # Simulate fill
            await self._simulate_fill(order)
            
    async def _reject_order(self, order: Order, reason: str):
        """Reject an order"""
        order.status = OrderStatus.REJECTED
        
        # Create rejection execution report
        exec_report = ExecutionReport(
            order_id=order.order_id,
            exec_type=ExecutionType.REJECTED,
            symbol=order.symbol,
            side=order.side,
            leaves_quantity=order.quantity,
            order_status=order.status,
            broker=order.broker or "SYSTEM",
            text=f"Order rejected: {reason}"
        )
        
        self.execution_reports[order.order_id].append(exec_report)
        
        self.logger.warning(f"Order {order.order_id} rejected: {reason}")
        
    def _calculate_net_amount(
        self,
        side: OrderSide,
        quantity: Decimal,
        price: Decimal,
        commission: Decimal
    ) -> Decimal:
        """Calculate net amount for trade"""
        gross_amount = quantity * price
        
        if side == OrderSide.BUY:
            # For buys, add commission to cost
            return gross_amount + commission
        else:
            # For sells, subtract commission from proceeds
            return gross_amount - commission
            
    async def cancel_order(self, order_id: str, user_id: str) -> bool:
        """Cancel an order"""
        order = self.orders.get(order_id)
        
        if not order or order.user_id != user_id:
            return False
            
        # Check if order can be cancelled
        if order.status not in [
            OrderStatus.PENDING,
            OrderStatus.SUBMITTED,
            OrderStatus.ACCEPTED,
            OrderStatus.PARTIALLY_FILLED
        ]:
            return False
            
        # In production, send cancel to broker
        # For now, just update status
        
        order.status = OrderStatus.CANCELLED
        order.cancelled_at = datetime.now()
        
        # Create cancellation execution report
        exec_report = ExecutionReport(
            order_id=order.order_id,
            exec_type=ExecutionType.CANCELLED,
            symbol=order.symbol,
            side=order.side,
            cumulative_quantity=order.filled_quantity,
            leaves_quantity=Decimal("0"),
            order_status=order.status,
            broker=order.broker,
            text="Order cancelled by user"
        )
        
        self.execution_reports[order.order_id].append(exec_report)
        
        self.logger.info(f"Order {order_id} cancelled")
        return True
        
    async def modify_order(
        self,
        order_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Order]:
        """Modify an existing order"""
        order = self.orders.get(order_id)
        
        if not order or order.user_id != user_id:
            return None
            
        # Check if order can be modified
        if order.status not in [OrderStatus.SUBMITTED, OrderStatus.ACCEPTED]:
            return None
            
        # In production, send modification to broker
        # For now, update local order
        
        for field, value in updates.items():
            if hasattr(order, field):
                setattr(order, field, value)
                
        order.updated_at = datetime.now()
        
        # Create replace execution report
        exec_report = ExecutionReport(
            order_id=order.order_id,
            exec_type=ExecutionType.REPLACED,
            symbol=order.symbol,
            side=order.side,
            cumulative_quantity=order.filled_quantity,
            leaves_quantity=order.remaining_quantity,
            order_status=order.status,
            broker=order.broker,
            text=f"Order modified: {updates}"
        )
        
        self.execution_reports[order.order_id].append(exec_report)
        
        self.logger.info(f"Order {order_id} modified: {updates}")
        return order
        
    async def get_order(self, order_id: str, user_id: str) -> Optional[Order]:
        """Get order details"""
        order = self.orders.get(order_id)
        
        if order and order.user_id == user_id:
            return order
            
        return None
        
    async def get_user_orders(
        self,
        user_id: str,
        status: Optional[OrderStatus] = None,
        symbol: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Order]:
        """Get user's orders"""
        # Filter orders
        user_orders = [
            order for order in self.orders.values()
            if order.user_id == user_id
        ]
        
        if status:
            user_orders = [o for o in user_orders if o.status == status]
            
        if symbol:
            user_orders = [o for o in user_orders if o.symbol == symbol]
            
        # Sort by created_at descending
        user_orders.sort(key=lambda o: o.created_at, reverse=True)
        
        # Apply pagination
        return user_orders[offset:offset + limit]
        
    async def get_executions(
        self,
        user_id: str,
        since: datetime,
        symbol: Optional[str] = None
    ) -> List[ExecutionReport]:
        """Get execution reports"""
        executions = []
        
        for order_id, reports in self.execution_reports.items():
            order = self.orders.get(order_id)
            
            if order and order.user_id == user_id:
                for report in reports:
                    if report.transact_time >= since:
                        if not symbol or report.symbol == symbol:
                            executions.append(report)
                            
        # Sort by time descending
        executions.sort(key=lambda e: e.transact_time, reverse=True)
        
        return executions
        
    async def shutdown(self):
        """Shutdown order manager"""
        self.is_processing = False
        
        # Cancel pending orders
        for order in self.orders.values():
            if order.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED]:
                await self.cancel_order(order.order_id, order.user_id)
                
        self.logger.info("Order Manager shutdown complete") 