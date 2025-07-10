"""
RSI (Relative Strength Index) Strategy
Uses RSI to identify overbought and oversold conditions
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from .base_strategy import BaseStrategy, TradeSignal, OrderType


class RSIStrategy(BaseStrategy):
    """
    RSI-based trading strategy
    
    Buy when RSI < oversold_threshold (typically 30)
    Sell when RSI > overbought_threshold (typically 70)
    Hold otherwise
    """
    
    def __init__(self, period: int = 14, oversold_threshold: float = 30, overbought_threshold: float = 70):
        super().__init__("RSI_Strategy")
        self.period = period
        self.oversold_threshold = oversold_threshold
        self.overbought_threshold = overbought_threshold
    
    def calculate_rsi(self, prices: list) -> float:
        """
        Calculate RSI for the given price series
        
        Args:
            prices: List of historical prices
            
        Returns:
            RSI value (0-100)
        """
        if len(prices) < self.period + 1:
            return 50.0  # Neutral RSI if insufficient data
        
        # Convert to pandas Series
        price_series = pd.Series(prices)
        
        # Calculate price changes
        delta = price_series.diff()
        
        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        # Calculate average gains and losses
        avg_gains = gains.rolling(window=self.period).mean()
        avg_losses = losses.rolling(window=self.period).mean()
        
        # Calculate RS and RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1]
    
    def analyze(self, symbol: str, data: Dict[str, Any]) -> TradeSignal:
        """
        Analyze price data using RSI strategy
        
        Args:
            symbol: Stock symbol
            data: Dictionary containing 'prices' (list of historical prices)
            
        Returns:
            TradeSignal with buy/sell/hold recommendation
        """
        if not self.validate_data(data):
            return TradeSignal(OrderType.HOLD, 0.0, "Insufficient data")
        
        prices = data['prices']
        
        if len(prices) < self.period + 1:
            return TradeSignal(
                OrderType.HOLD,
                0.0,
                f"Insufficient price history. Need {self.period + 1} periods, got {len(prices)}"
            )
        
        # Calculate RSI
        rsi = self.calculate_rsi(prices)
        
        # Generate signal based on RSI
        if rsi < self.oversold_threshold:
            # Oversold condition - potential buy signal
            confidence = (self.oversold_threshold - rsi) / self.oversold_threshold
            confidence = min(confidence, 1.0)
            return TradeSignal(
                OrderType.BUY,
                confidence,
                f"RSI ({rsi:.2f}) indicates oversold condition (< {self.oversold_threshold})",
                {
                    'rsi': rsi,
                    'current_price': prices[-1],
                    'oversold_threshold': self.oversold_threshold,
                    'overbought_threshold': self.overbought_threshold
                }
            )
        elif rsi > self.overbought_threshold:
            # Overbought condition - potential sell signal
            confidence = (rsi - self.overbought_threshold) / (100 - self.overbought_threshold)
            confidence = min(confidence, 1.0)
            return TradeSignal(
                OrderType.SELL,
                confidence,
                f"RSI ({rsi:.2f}) indicates overbought condition (> {self.overbought_threshold})",
                {
                    'rsi': rsi,
                    'current_price': prices[-1],
                    'oversold_threshold': self.oversold_threshold,
                    'overbought_threshold': self.overbought_threshold
                }
            )
        else:
            # Neutral zone
            return TradeSignal(
                OrderType.HOLD,
                0.5,
                f"RSI ({rsi:.2f}) in neutral zone ({self.oversold_threshold}-{self.overbought_threshold})",
                {
                    'rsi': rsi,
                    'current_price': prices[-1],
                    'oversold_threshold': self.oversold_threshold,
                    'overbought_threshold': self.overbought_threshold
                }
            )
    
    def get_required_data(self) -> list:
        """Return required data fields"""
        return ['prices']