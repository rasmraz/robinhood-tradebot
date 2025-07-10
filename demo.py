#!/usr/bin/env python3
"""
Demo mode for Robinhood Trading Bot
Runs without real authentication for testing and demonstration
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.web.dashboard import TradingDashboard

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class DemoAuth:
    """Demo authentication object"""
    def __init__(self):
        self.is_authenticated = True

class DemoTradingBot:
    """Demo trading bot that simulates functionality without real trading"""
    
    def __init__(self, config):
        self.config = config
        self.is_running = False
        self.active_strategies = ['sma', 'rsi']
        self.default_trade_amount = config.get('default_trade_amount', 100.0)
        self.auth = DemoAuth()
        
        # Demo data
        self.demo_portfolio = {
            'total_value': 10000.0,
            'buying_power': 2500.0,
            'day_change': 150.0,
            'positions': 3
        }
        
        self.demo_trades = [
            {
                'id': 1,
                'symbol': 'AAPL',
                'order_type': 'buy',
                'quantity': 5.0,
                'price': 200.0,
                'total_amount': 1000.0,
                'strategy': 'sma',
                'confidence': 0.75,
                'reason': 'Demo trade - SMA crossover',
                'created_at': '2025-07-10T10:30:00',
                'status': 'executed'
            },
            {
                'id': 2,
                'symbol': 'GOOGL',
                'order_type': 'sell',
                'quantity': 2.0,
                'price': 150.0,
                'total_amount': 300.0,
                'strategy': 'rsi',
                'confidence': 0.68,
                'reason': 'Demo trade - RSI overbought',
                'created_at': '2025-07-10T11:15:00',
                'status': 'executed'
            }
        ]
    
    def start(self):
        """Start the demo bot"""
        logger.info("Starting demo trading bot...")
        self.is_running = True
        return True
    
    def stop(self):
        """Stop the demo bot"""
        logger.info("Stopping demo trading bot...")
        self.is_running = False
    
    def get_portfolio_summary(self):
        """Get demo portfolio summary"""
        return self.demo_portfolio
    
    def get_trade_history(self, limit=50):
        """Get demo trade history"""
        return self.demo_trades[:limit]
    
    def analyze_symbol(self, symbol):
        """Demo symbol analysis"""
        import random
        from src.strategies.base_strategy import TradeSignal, OrderType
        
        # Generate demo signals
        signals = {}
        
        # SMA signal
        sma_action = random.choice([OrderType.BUY, OrderType.SELL, OrderType.HOLD])
        sma_confidence = random.uniform(0.5, 0.9)
        sma_reason = f"Demo SMA analysis for {symbol}"
        signals['sma'] = TradeSignal(sma_action, sma_confidence, sma_reason)
        
        # RSI signal
        rsi_action = random.choice([OrderType.BUY, OrderType.SELL, OrderType.HOLD])
        rsi_confidence = random.uniform(0.5, 0.9)
        rsi_reason = f"Demo RSI analysis for {symbol}"
        signals['rsi'] = TradeSignal(rsi_action, rsi_confidence, rsi_reason)
        
        return signals
    
    def make_trading_decision(self, signals):
        """Make demo trading decision"""
        from src.strategies.base_strategy import TradeSignal, OrderType
        
        if not signals:
            return TradeSignal(OrderType.HOLD, 0.0, "No signals available")
        
        # Simple consensus logic for demo
        buy_votes = sum(1 for signal in signals.values() if signal.order_type == OrderType.BUY)
        sell_votes = sum(1 for signal in signals.values() if signal.order_type == OrderType.SELL)
        
        if buy_votes > sell_votes:
            avg_confidence = sum(signal.confidence for signal in signals.values() if signal.order_type == OrderType.BUY) / buy_votes
            return TradeSignal(OrderType.BUY, avg_confidence, f"Demo buy consensus ({buy_votes} votes)")
        elif sell_votes > buy_votes:
            avg_confidence = sum(signal.confidence for signal in signals.values() if signal.order_type == OrderType.SELL) / sell_votes
            return TradeSignal(OrderType.SELL, avg_confidence, f"Demo sell consensus ({sell_votes} votes)")
        else:
            return TradeSignal(OrderType.HOLD, 0.5, "Demo neutral consensus")
    
    def execute_trade(self, symbol, signal, amount=None):
        """Execute demo trade"""
        logger.info(f"Demo trade executed: {signal.order_type.value} {symbol} for ${amount or self.default_trade_amount}")
        
        # Add to demo trades
        new_trade = {
            'id': len(self.demo_trades) + 1,
            'symbol': symbol,
            'order_type': signal.order_type.value,
            'quantity': (amount or self.default_trade_amount) / 200.0,  # Assume $200 per share
            'price': 200.0,
            'total_amount': amount or self.default_trade_amount,
            'strategy': 'manual',
            'confidence': signal.confidence,
            'reason': signal.reason,
            'created_at': '2025-07-10T12:00:00',
            'status': 'executed'
        }
        self.demo_trades.insert(0, new_trade)
        
        return True

def main():
    """Main demo application entry point"""
    logger.info("Starting Robinhood Trading Bot - DEMO MODE")
    
    # Load configuration
    config = {
        'database_path': './data/demo_trading_bot.db',
        'default_trade_amount': float(os.getenv('DEFAULT_TRADE_AMOUNT', 100.0)),
        'risk_percentage': float(os.getenv('RISK_PERCENTAGE', 2.0)),
        'max_positions': int(os.getenv('MAX_POSITIONS', 5)),
        'min_confidence': 0.6,
        'active_strategies': ['sma', 'rsi'],
        'flask_secret_key': os.getenv('FLASK_SECRET_KEY', 'demo-secret-key'),
        'flask_port': int(os.getenv('FLASK_PORT', 12001))
    }
    
    # Initialize demo trading bot
    bot = DemoTradingBot(config)
    
    try:
        # Run web dashboard
        logger.info("Starting demo web dashboard")
        dashboard = TradingDashboard(bot, config)
        
        print("\n" + "="*60)
        print("🤖 ROBINHOOD TRADING BOT - DEMO MODE")
        print("="*60)
        print(f"📊 Web Dashboard: http://localhost:{config['flask_port']}")
        print("⚠️  This is a DEMO - No real trading will occur!")
        print("⚠️  All data is simulated for demonstration purposes")
        print("="*60)
        print("Press Ctrl+C to stop the demo")
        print("="*60 + "\n")
        
        dashboard.run(host='0.0.0.0', port=config['flask_port'], debug=False)
        
    except KeyboardInterrupt:
        logger.info("Demo stopped by user")
    except Exception as e:
        logger.error(f"Demo error: {str(e)}")
        return 1
    finally:
        bot.stop()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())