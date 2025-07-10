#!/usr/bin/env python3
"""
Robinhood Trading Bot - Main Entry Point
"""

import os
import sys
import logging
import argparse
import schedule
import time
import threading
from datetime import datetime
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.trading_bot import TradingBot
from src.web.dashboard import TradingDashboard

# Load environment variables
load_dotenv()

# Setup logging
def setup_logging():
    """Setup logging configuration"""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_file = os.getenv('LOG_FILE', './logs/trading_bot.log')
    
    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_config():
    """Load configuration from environment variables"""
    return {
        'database_path': os.getenv('DATABASE_PATH', './data/trading_bot.db'),
        'default_trade_amount': float(os.getenv('DEFAULT_TRADE_AMOUNT', '100.0')),
        'risk_percentage': float(os.getenv('RISK_PERCENTAGE', '2.0')),
        'max_positions': int(os.getenv('MAX_POSITIONS', '5')),
        'max_daily_loss': float(os.getenv('MAX_DAILY_LOSS', '500.0')),
        'max_position_size': float(os.getenv('MAX_POSITION_SIZE', '1000.0')),
        'min_confidence': float(os.getenv('MIN_CONFIDENCE', '0.6')),
        'active_strategies': os.getenv('ACTIVE_STRATEGIES', 'sma,rsi').split(','),
        'flask_secret_key': os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here'),
        'flask_port': int(os.getenv('FLASK_PORT', '12000')),
        'trading_symbols': os.getenv('TRADING_SYMBOLS', 'AAPL,GOOGL,MSFT,TSLA,AMZN').split(','),
        'trading_schedule': os.getenv('TRADING_SCHEDULE', '09:30,15:30'),  # Market hours
        'auto_trade': os.getenv('AUTO_TRADE', 'false').lower() == 'true'
    }

def run_scheduled_trading(bot, symbols):
    """Run scheduled trading cycle"""
    logger = logging.getLogger('scheduler')
    
    if not bot.is_running:
        logger.info("Bot is not running, skipping scheduled trading")
        return
    
    logger.info("Running scheduled trading cycle")
    try:
        bot.run_trading_cycle(symbols)
        
        # Log portfolio snapshot
        portfolio = bot.get_portfolio_summary()
        bot.db_manager.log_portfolio_snapshot(portfolio)
        
    except Exception as e:
        logger.error(f"Error in scheduled trading: {str(e)}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Robinhood Trading Bot')
    parser.add_argument('--mode', choices=['web', 'cli', 'daemon'], default='web',
                       help='Run mode: web (dashboard), cli (command line), or daemon (background)')
    parser.add_argument('--symbols', nargs='+', help='Symbols to trade (overrides config)')
    parser.add_argument('--analyze-only', action='store_true', help='Only analyze, do not trade')
    parser.add_argument('--port', type=int, help='Web dashboard port (overrides config)')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger('main')
    
    logger.info("Starting Robinhood Trading Bot")
    
    # Load configuration
    config = load_config()
    
    # Override config with command line arguments
    if args.symbols:
        config['trading_symbols'] = args.symbols
    if args.port:
        config['flask_port'] = args.port
    if args.analyze_only:
        config['auto_trade'] = False
    
    # Create trading bot
    bot = TradingBot(config)
    
    if args.mode == 'web':
        # Web dashboard mode
        logger.info("Starting in web dashboard mode")
        
        # Create dashboard
        dashboard = TradingDashboard(bot, config)
        
        # Start bot if auto_trade is enabled
        if config.get('auto_trade', False):
            if bot.start():
                logger.info("Bot started successfully")
                
                # Schedule trading during market hours
                trading_times = config.get('trading_schedule', '09:30,15:30').split(',')
                for trading_time in trading_times:
                    schedule.every().monday.at(trading_time).do(
                        run_scheduled_trading, bot, config['trading_symbols']
                    )
                    schedule.every().tuesday.at(trading_time).do(
                        run_scheduled_trading, bot, config['trading_symbols']
                    )
                    schedule.every().wednesday.at(trading_time).do(
                        run_scheduled_trading, bot, config['trading_symbols']
                    )
                    schedule.every().thursday.at(trading_time).do(
                        run_scheduled_trading, bot, config['trading_symbols']
                    )
                    schedule.every().friday.at(trading_time).do(
                        run_scheduled_trading, bot, config['trading_symbols']
                    )
                
                # Start scheduler in background thread
                def run_scheduler():
                    while bot.is_running:
                        schedule.run_pending()
                        time.sleep(60)  # Check every minute
                
                scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
                scheduler_thread.start()
                
                logger.info("Scheduled trading enabled")
            else:
                logger.error("Failed to start bot")
        
        # Run web dashboard
        try:
            dashboard.run(host='0.0.0.0', port=config['flask_port'], debug=False)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            bot.stop()
    
    elif args.mode == 'cli':
        # Command line mode
        logger.info("Starting in CLI mode")
        
        if not bot.start():
            logger.error("Failed to start bot")
            return 1
        
        try:
            symbols = config['trading_symbols']
            logger.info(f"Analyzing symbols: {symbols}")
            
            for symbol in symbols:
                logger.info(f"\n--- Analyzing {symbol} ---")
                signals = bot.analyze_symbol(symbol)
                
                if signals:
                    for strategy_name, signal in signals.items():
                        logger.info(f"{strategy_name}: {signal.order_type.value} "
                                  f"(confidence: {signal.confidence:.2f}) - {signal.reason}")
                    
                    final_signal = bot.make_trading_decision(signals)
                    logger.info(f"Final decision: {final_signal.order_type.value} "
                              f"(confidence: {final_signal.confidence:.2f})")
                    
                    if not args.analyze_only and final_signal.confidence >= config['min_confidence']:
                        logger.info("Executing trade...")
                        success = bot.execute_trade(symbol, final_signal)
                        logger.info(f"Trade {'successful' if success else 'failed'}")
                else:
                    logger.warning(f"No signals generated for {symbol}")
        
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            bot.stop()
    
    elif args.mode == 'daemon':
        # Daemon mode (background service)
        logger.info("Starting in daemon mode")
        
        if not bot.start():
            logger.error("Failed to start bot")
            return 1
        
        try:
            # Schedule trading
            symbols = config['trading_symbols']
            trading_times = config.get('trading_schedule', '09:30,15:30').split(',')
            
            for trading_time in trading_times:
                schedule.every().monday.at(trading_time).do(
                    run_scheduled_trading, bot, symbols
                )
                schedule.every().tuesday.at(trading_time).do(
                    run_scheduled_trading, bot, symbols
                )
                schedule.every().wednesday.at(trading_time).do(
                    run_scheduled_trading, bot, symbols
                )
                schedule.every().thursday.at(trading_time).do(
                    run_scheduled_trading, bot, symbols
                )
                schedule.every().friday.at(trading_time).do(
                    run_scheduled_trading, bot, symbols
                )
            
            logger.info(f"Scheduled trading for {symbols} at {trading_times}")
            
            # Run scheduler
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        except KeyboardInterrupt:
            logger.info("Shutting down daemon...")
        finally:
            bot.stop()
    
    logger.info("Trading bot stopped")
    return 0

if __name__ == '__main__':
    sys.exit(main())