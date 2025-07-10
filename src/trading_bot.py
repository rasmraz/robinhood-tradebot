"""
Main Trading Bot Class
Orchestrates authentication, strategy execution, and trade management
"""

import os
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import robin_stocks.robinhood as rh

from .auth.robinhood_auth import RobinhoodAuth
from .strategies.base_strategy import BaseStrategy, TradeSignal, OrderType
from .strategies.sma_strategy import SMAStrategy
from .strategies.rsi_strategy import RSIStrategy
from .utils.data_fetcher import DataFetcher
from .utils.database import TradingDatabase

logger = logging.getLogger(__name__)


class TradingBot:
    """Main trading bot that manages strategies and executes trades"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.auth = RobinhoodAuth()
        self.data_fetcher = DataFetcher()
        self.database = TradingDatabase(self.config.get('database_path', './data/trading_bot.db'))
        
        # Initialize strategies
        self.strategies = {
            'sma': SMAStrategy(),
            'rsi': RSIStrategy()
        }
        
        self.active_strategies = config.get('active_strategies', ['sma'])
        self.default_trade_amount = float(config.get('default_trade_amount', 100.0))
        self.is_running = False
        
    def start(self) -> bool:
        """Start the trading bot"""
        logger.info("Starting trading bot...")
        
        # Authenticate with Robinhood
        if not self.auth.login():
            logger.error("Failed to authenticate with Robinhood")
            return False
        
        # Database is auto-initialized
        
        self.is_running = True
        logger.info("Trading bot started successfully")
        return True
    
    def stop(self):
        """Stop the trading bot"""
        logger.info("Stopping trading bot...")
        self.is_running = False
        self.auth.logout()
        logger.info("Trading bot stopped")
    
    def analyze_symbol(self, symbol: str) -> Dict[str, TradeSignal]:
        """
        Analyze a symbol using all active strategies
        
        Args:
            symbol: Stock symbol to analyze
            
        Returns:
            Dictionary mapping strategy names to their signals
        """
        signals = {}
        
        # Get market data
        market_data = self.data_fetcher.get_market_data(symbol)
        if not market_data:
            logger.error(f"Failed to get market data for {symbol}")
            return signals
        
        # Run each active strategy
        for strategy_name in self.active_strategies:
            if strategy_name in self.strategies:
                strategy = self.strategies[strategy_name]
                try:
                    signal = strategy.analyze(symbol, market_data)
                    signals[strategy_name] = signal
                    logger.info(f"{strategy_name} signal for {symbol}: {signal.order_type.value} (confidence: {signal.confidence:.2f})")
                except Exception as e:
                    logger.error(f"Error running {strategy_name} strategy for {symbol}: {str(e)}")
        
        return signals
    
    def make_trading_decision(self, signals: Dict[str, TradeSignal]) -> TradeSignal:
        """
        Combine signals from multiple strategies to make final trading decision
        
        Args:
            signals: Dictionary of signals from different strategies
            
        Returns:
            Final trading signal
        """
        if not signals:
            return TradeSignal(OrderType.HOLD, 0.0, "No signals available")
        
        # Simple voting system - can be enhanced
        buy_votes = 0
        sell_votes = 0
        total_confidence = 0.0
        reasons = []
        
        for strategy_name, signal in signals.items():
            if signal.order_type == OrderType.BUY:
                buy_votes += signal.confidence
            elif signal.order_type == OrderType.SELL:
                sell_votes += signal.confidence
            
            total_confidence += signal.confidence
            reasons.append(f"{strategy_name}: {signal.reason}")
        
        # Make decision based on weighted votes
        if buy_votes > sell_votes and buy_votes > 0.5:
            return TradeSignal(
                OrderType.BUY,
                buy_votes / len(signals),
                f"Buy consensus: {'; '.join(reasons)}"
            )
        elif sell_votes > buy_votes and sell_votes > 0.5:
            return TradeSignal(
                OrderType.SELL,
                sell_votes / len(signals),
                f"Sell consensus: {'; '.join(reasons)}"
            )
        else:
            return TradeSignal(
                OrderType.HOLD,
                total_confidence / len(signals),
                f"Hold consensus: {'; '.join(reasons)}"
            )
    
    def execute_trade(self, symbol: str, signal: TradeSignal, amount: Optional[float] = None) -> bool:
        """
        Execute a trade based on the signal
        
        Args:
            symbol: Stock symbol to trade
            signal: Trading signal
            amount: Dollar amount to trade (uses default if None)
            
        Returns:
            True if trade was executed successfully, False otherwise
        """
        if not self.auth.is_authenticated:
            logger.error("Not authenticated with Robinhood")
            return False
        
        if signal.order_type == OrderType.HOLD:
            logger.info(f"Holding position for {symbol}: {signal.reason}")
            return True
        
        trade_amount = amount or self.default_trade_amount
        
        # Basic risk check - can be enhanced
        portfolio = self.get_portfolio_summary()
        if signal.order_type == OrderType.BUY and portfolio.get('buying_power', 0) < trade_amount:
            logger.warning(f"Insufficient buying power for {symbol}: need ${trade_amount}, have ${portfolio.get('buying_power', 0)}")
            return False
        
        try:
            if signal.order_type == OrderType.BUY:
                result = rh.orders.order_buy_fractional_by_price(
                    symbol=symbol,
                    amountInDollars=trade_amount,
                    timeInForce='gfd'  # Good for day
                )
            else:  # SELL
                # Get current position
                position = rh.account.get_positions(symbol)
                if position and float(position[0]['quantity']) > 0:
                    result = rh.orders.order_sell_fractional_by_price(
                        symbol=symbol,
                        amountInDollars=trade_amount,
                        timeInForce='gfd'
                    )
                else:
                    logger.warning(f"No position to sell for {symbol}")
                    return False
            
            if result:
                # Get current price for logging
                current_price = self.data_fetcher.get_current_price(symbol) or 0
                quantity = trade_amount / current_price if current_price > 0 else 0
                
                # Log trade to database
                self.database.log_trade(
                    symbol=symbol,
                    order_type=signal.order_type.value,
                    quantity=quantity,
                    price=current_price,
                    strategy="combined",
                    confidence=signal.confidence,
                    reason=signal.reason,
                    order_id=result.get('id')
                )
                
                logger.info(f"Successfully executed {signal.order_type.value} order for {symbol}: ${trade_amount}")
                return True
            else:
                logger.error(f"Failed to execute {signal.order_type.value} order for {symbol}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing trade for {symbol}: {str(e)}")
            return False
    
    def run_trading_cycle(self, symbols: List[str]):
        """
        Run a complete trading cycle for given symbols
        
        Args:
            symbols: List of stock symbols to analyze and trade
        """
        logger.info(f"Running trading cycle for symbols: {symbols}")
        
        for symbol in symbols:
            try:
                # Analyze symbol
                signals = self.analyze_symbol(symbol)
                
                if not signals:
                    logger.warning(f"No signals generated for {symbol}")
                    continue
                
                # Make trading decision
                final_signal = self.make_trading_decision(signals)
                
                # Execute trade if confidence is high enough
                min_confidence = self.config.get('min_confidence', 0.6)
                if final_signal.confidence >= min_confidence:
                    self.execute_trade(symbol, final_signal)
                else:
                    logger.info(f"Signal confidence too low for {symbol}: {final_signal.confidence:.2f} < {min_confidence}")
                
                # Small delay between symbols
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
                continue
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get current portfolio summary"""
        if not self.auth.is_authenticated:
            return {}
        
        try:
            portfolio = self.auth.get_portfolio_info()
            positions = rh.account.get_open_stock_positions()
            
            return {
                'total_value': portfolio.get('total_return_today', 0),
                'day_change': portfolio.get('total_return_today', 0),
                'positions': len(positions) if positions else 0,
                'buying_power': portfolio.get('withdrawable_amount', 0)
            }
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {str(e)}")
            return {}
    
    def get_trade_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent trade history from database"""
        return self.database.get_recent_trades(limit)