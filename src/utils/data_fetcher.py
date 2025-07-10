"""
Data Fetcher Module
Handles fetching market data from various sources
"""

import logging
import yfinance as yf
import robin_stocks.robinhood as rh
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DataFetcher:
    """Fetches market data from multiple sources"""
    
    def __init__(self):
        self.logger = logging.getLogger("data_fetcher")
    
    def get_historical_prices(self, symbol: str, period: str = "1y", interval: str = "1d") -> List[float]:
        """
        Get historical prices for a symbol
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            interval: Data interval ('1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')
            
        Returns:
            List of closing prices
        """
        try:
            # Try Yahoo Finance first (more reliable for historical data)
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)
            
            if not hist.empty:
                prices = hist['Close'].tolist()
                self.logger.info(f"Fetched {len(prices)} historical prices for {symbol} from Yahoo Finance")
                return prices
            else:
                self.logger.warning(f"No historical data found for {symbol} on Yahoo Finance")
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return []
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Current price or None if error
        """
        try:
            # Try Robinhood first for real-time data
            quote = rh.stocks.get_latest_price(symbol)
            if quote and len(quote) > 0:
                price = float(quote[0])
                self.logger.debug(f"Current price for {symbol}: ${price}")
                return price
        except Exception as e:
            self.logger.warning(f"Error getting current price from Robinhood for {symbol}: {str(e)}")
        
        try:
            # Fallback to Yahoo Finance
            ticker = yf.Ticker(symbol)
            info = ticker.info
            price = info.get('currentPrice') or info.get('regularMarketPrice')
            if price:
                self.logger.debug(f"Current price for {symbol}: ${price} (Yahoo Finance)")
                return float(price)
        except Exception as e:
            self.logger.error(f"Error getting current price from Yahoo Finance for {symbol}: {str(e)}")
        
        return None
    
    def get_quote_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive quote data for a symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with quote data or None if error
        """
        try:
            # Get data from Robinhood
            quote = rh.stocks.get_quote(symbol)
            if quote:
                return {
                    'symbol': symbol,
                    'last_trade_price': float(quote.get('last_trade_price', 0)),
                    'previous_close': float(quote.get('previous_close', 0)),
                    'ask_price': float(quote.get('ask_price', 0)) if quote.get('ask_price') else None,
                    'bid_price': float(quote.get('bid_price', 0)) if quote.get('bid_price') else None,
                    'ask_size': int(quote.get('ask_size', 0)) if quote.get('ask_size') else None,
                    'bid_size': int(quote.get('bid_size', 0)) if quote.get('bid_size') else None,
                    'volume': int(quote.get('volume', 0)) if quote.get('volume') else None,
                    'updated_at': quote.get('updated_at'),
                    'source': 'robinhood'
                }
        except Exception as e:
            self.logger.warning(f"Error getting quote from Robinhood for {symbol}: {str(e)}")
        
        try:
            # Fallback to Yahoo Finance
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'last_trade_price': info.get('currentPrice') or info.get('regularMarketPrice', 0),
                'previous_close': info.get('previousClose', 0),
                'ask_price': info.get('ask'),
                'bid_price': info.get('bid'),
                'ask_size': info.get('askSize'),
                'bid_size': info.get('bidSize'),
                'volume': info.get('volume'),
                'updated_at': datetime.now().isoformat(),
                'source': 'yahoo_finance'
            }
        except Exception as e:
            self.logger.error(f"Error getting quote from Yahoo Finance for {symbol}: {str(e)}")
        
        return None
    
    def get_market_data(self, symbol: str, days: int = 365) -> Dict[str, Any]:
        """
        Get comprehensive market data for analysis
        
        Args:
            symbol: Stock symbol
            days: Number of days of historical data
            
        Returns:
            Dictionary with market data
        """
        # Determine period based on days
        if days <= 7:
            period = "7d"
        elif days <= 30:
            period = "1mo"
        elif days <= 90:
            period = "3mo"
        elif days <= 180:
            period = "6mo"
        elif days <= 365:
            period = "1y"
        else:
            period = "2y"
        
        # Get historical prices
        prices = self.get_historical_prices(symbol, period=period)
        
        # Get current quote
        quote = self.get_quote_data(symbol)
        
        # Get additional data from Yahoo Finance
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            volumes = hist['Volume'].tolist() if not hist.empty else []
            highs = hist['High'].tolist() if not hist.empty else []
            lows = hist['Low'].tolist() if not hist.empty else []
            opens = hist['Open'].tolist() if not hist.empty else []
            
        except Exception as e:
            self.logger.warning(f"Error getting additional market data for {symbol}: {str(e)}")
            volumes = []
            highs = []
            lows = []
            opens = []
        
        return {
            'symbol': symbol,
            'prices': prices,
            'volumes': volumes,
            'highs': highs,
            'lows': lows,
            'opens': opens,
            'current_quote': quote,
            'data_points': len(prices),
            'fetched_at': datetime.now().isoformat()
        }