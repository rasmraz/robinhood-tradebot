"""
Risk Management Module
Implements risk controls and position sizing
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import robin_stocks.robinhood as rh

logger = logging.getLogger(__name__)


class RiskManager:
    """Manages trading risk and position sizing"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_position_size = float(config.get('max_position_size', 1000.0))
        self.max_daily_loss = float(config.get('max_daily_loss', 500.0))
        self.max_positions = int(config.get('max_positions', 5))
        self.risk_percentage = float(config.get('risk_percentage', 2.0))  # % of portfolio per trade
        
        self.daily_loss = 0.0
        self.last_reset_date = datetime.now().date()
    
    def reset_daily_counters(self):
        """Reset daily loss counter if new day"""
        current_date = datetime.now().date()
        if current_date > self.last_reset_date:
            self.daily_loss = 0.0
            self.last_reset_date = current_date
            logger.info("Daily risk counters reset")
    
    def can_trade(self, symbol: str, order_type: str, amount: float) -> bool:
        """
        Check if trade is allowed based on risk rules
        
        Args:
            symbol: Stock symbol
            order_type: 'buy' or 'sell'
            amount: Trade amount in dollars
            
        Returns:
            True if trade is allowed, False otherwise
        """
        self.reset_daily_counters()
        
        # Check daily loss limit
        if self.daily_loss >= self.max_daily_loss:
            logger.warning(f"Daily loss limit reached: ${self.daily_loss:.2f} >= ${self.max_daily_loss:.2f}")
            return False
        
        # Check position size limit
        if amount > self.max_position_size:
            logger.warning(f"Position size too large: ${amount:.2f} > ${self.max_position_size:.2f}")
            return False
        
        # Check maximum positions limit (for buy orders)
        if order_type.lower() == 'buy':
            try:
                positions = rh.account.get_open_stock_positions()
                current_positions = len(positions) if positions else 0
                
                if current_positions >= self.max_positions:
                    logger.warning(f"Maximum positions limit reached: {current_positions} >= {self.max_positions}")
                    return False
            except Exception as e:
                logger.error(f"Error checking positions: {str(e)}")
                return False
        
        # Check portfolio percentage risk
        try:
            portfolio = rh.profiles.load_portfolio_profile()
            if portfolio:
                total_value = float(portfolio.get('total_return_today', 0))
                if total_value > 0:
                    risk_amount = total_value * (self.risk_percentage / 100)
                    if amount > risk_amount:
                        logger.warning(f"Trade amount exceeds risk percentage: ${amount:.2f} > ${risk_amount:.2f}")
                        return False
        except Exception as e:
            logger.warning(f"Could not check portfolio risk: {str(e)}")
        
        return True
    
    def calculate_position_size(self, symbol: str, confidence: float, current_price: float) -> float:
        """
        Calculate appropriate position size based on confidence and risk rules
        
        Args:
            symbol: Stock symbol
            confidence: Strategy confidence (0.0 to 1.0)
            current_price: Current stock price
            
        Returns:
            Recommended position size in dollars
        """
        try:
            # Get portfolio value
            portfolio = rh.profiles.load_portfolio_profile()
            if not portfolio:
                return self.config.get('default_trade_amount', 100.0)
            
            total_value = float(portfolio.get('total_return_today', 0))
            if total_value <= 0:
                return self.config.get('default_trade_amount', 100.0)
            
            # Base position size on portfolio percentage
            base_amount = total_value * (self.risk_percentage / 100)
            
            # Adjust based on confidence
            confidence_multiplier = 0.5 + (confidence * 0.5)  # 0.5 to 1.0 range
            adjusted_amount = base_amount * confidence_multiplier
            
            # Apply limits
            adjusted_amount = min(adjusted_amount, self.max_position_size)
            adjusted_amount = max(adjusted_amount, 10.0)  # Minimum trade amount
            
            logger.debug(f"Calculated position size for {symbol}: ${adjusted_amount:.2f} (confidence: {confidence:.2f})")
            return adjusted_amount
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return self.config.get('default_trade_amount', 100.0)
    
    def update_daily_loss(self, loss_amount: float):
        """Update daily loss tracker"""
        self.reset_daily_counters()
        self.daily_loss += loss_amount
        logger.info(f"Daily loss updated: ${self.daily_loss:.2f}")
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """Get current risk metrics"""
        self.reset_daily_counters()
        
        try:
            positions = rh.account.get_open_stock_positions()
            current_positions = len(positions) if positions else 0
        except:
            current_positions = 0
        
        return {
            'daily_loss': self.daily_loss,
            'max_daily_loss': self.max_daily_loss,
            'daily_loss_remaining': max(0, self.max_daily_loss - self.daily_loss),
            'current_positions': current_positions,
            'max_positions': self.max_positions,
            'positions_remaining': max(0, self.max_positions - current_positions),
            'max_position_size': self.max_position_size,
            'risk_percentage': self.risk_percentage
        }