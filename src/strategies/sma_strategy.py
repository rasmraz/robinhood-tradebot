"""
Simple Moving Average (SMA) Strategy
Compares short-term and long-term moving averages to generate signals
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from .base_strategy import BaseStrategy, TradeSignal, OrderType


class SMAStrategy(BaseStrategy):
    """
    Simple Moving Average crossover strategy
    
    Buy when short MA > long MA
    Sell when short MA < long MA
    Hold when they are equal or close
    """
    
    def __init__(self, short_window: int = 50, long_window: int = 200, threshold: float = 0.01):
        super().__init__("SMA_Strategy")
        self.short_window = short_window
        self.long_window = long_window
        self.threshold = threshold  # Minimum percentage difference to trigger signal
    
    def analyze(self, symbol: str, data: Dict[str, Any]) -> TradeSignal:
        """
        Analyze price data using SMA crossover strategy
        
        Args:
            symbol: Stock symbol
            data: Dictionary containing 'prices' (list of historical prices)
            
        Returns:
            TradeSignal with buy/sell/hold recommendation
        """
        if not self.validate_data(data):
            return TradeSignal(OrderType.HOLD, 0.0, "Insufficient data")
        
        prices = data['prices']
        
        if len(prices) < self.long_window:
            return TradeSignal(
                OrderType.HOLD, 
                0.0, 
                f"Insufficient price history. Need {self.long_window} periods, got {len(prices)}"
            )
        
        # Convert to pandas Series for easier calculation
        price_series = pd.Series(prices)
        
        # Calculate moving averages
        short_ma = price_series.rolling(window=self.short_window).mean().iloc[-1]
        long_ma = price_series.rolling(window=self.long_window).mean().iloc[-1]
        
        # Calculate percentage difference
        pct_diff = (short_ma - long_ma) / long_ma
        
        # Generate signal
        if pct_diff > self.threshold:
            confidence = min(abs(pct_diff) * 10, 1.0)  # Scale confidence
            return TradeSignal(
                OrderType.BUY,
                confidence,
                f"Short MA ({short_ma:.2f}) > Long MA ({long_ma:.2f}) by {pct_diff*100:.2f}%",
                {
                    'short_ma': short_ma,
                    'long_ma': long_ma,
                    'pct_diff': pct_diff,
                    'current_price': prices[-1]
                }
            )
        elif pct_diff < -self.threshold:
            confidence = min(abs(pct_diff) * 10, 1.0)
            return TradeSignal(
                OrderType.SELL,
                confidence,
                f"Short MA ({short_ma:.2f}) < Long MA ({long_ma:.2f}) by {pct_diff*100:.2f}%",
                {
                    'short_ma': short_ma,
                    'long_ma': long_ma,
                    'pct_diff': pct_diff,
                    'current_price': prices[-1]
                }
            )
        else:
            return TradeSignal(
                OrderType.HOLD,
                0.5,
                f"MAs are close. Short MA: {short_ma:.2f}, Long MA: {long_ma:.2f}",
                {
                    'short_ma': short_ma,
                    'long_ma': long_ma,
                    'pct_diff': pct_diff,
                    'current_price': prices[-1]
                }
            )
    
    def get_required_data(self) -> list:
        """Return required data fields"""
        return ['prices']