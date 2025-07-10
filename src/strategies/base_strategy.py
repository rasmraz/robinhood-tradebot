"""
Base Strategy Class
All trading strategies should inherit from this class
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types for trading decisions"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class TradeSignal:
    """Represents a trading signal with confidence and reasoning"""
    
    def __init__(self, order_type: OrderType, confidence: float, reason: str, data: Optional[Dict] = None):
        self.order_type = order_type
        self.confidence = confidence  # 0.0 to 1.0
        self.reason = reason
        self.data = data or {}


class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"strategy.{name}")
    
    @abstractmethod
    def analyze(self, symbol: str, data: Dict[str, Any]) -> TradeSignal:
        """
        Analyze market data and return a trading signal
        
        Args:
            symbol: Stock symbol to analyze
            data: Market data dictionary containing price, volume, etc.
            
        Returns:
            TradeSignal object with recommendation
        """
        pass
    
    @abstractmethod
    def get_required_data(self) -> list:
        """
        Return list of required data fields for this strategy
        
        Returns:
            List of required data field names
        """
        pass
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate that required data is present
        
        Args:
            data: Market data dictionary
            
        Returns:
            True if all required data is present, False otherwise
        """
        required_fields = self.get_required_data()
        for field in required_fields:
            if field not in data or data[field] is None:
                self.logger.error(f"Missing required data field: {field}")
                return False
        return True
    
    def __str__(self):
        return f"Strategy: {self.name}"