"""
Database Module
Handles SQLite database operations for storing trade history and bot data
"""

import sqlite3
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import json

logger = logging.getLogger(__name__)


class TradingDatabase:
    """Handles database operations for the trading bot"""
    
    def __init__(self, db_path: str = "./data/trading_bot.db"):
        self.db_path = db_path
        self.logger = logging.getLogger("database")
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create trades table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        order_type TEXT NOT NULL,
                        quantity REAL NOT NULL,
                        price REAL NOT NULL,
                        total_amount REAL NOT NULL,
                        strategy TEXT NOT NULL,
                        confidence REAL,
                        reason TEXT,
                        order_id TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        executed_at TIMESTAMP,
                        metadata TEXT
                    )
                ''')
                
                # Create portfolio_snapshots table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        total_value REAL NOT NULL,
                        buying_power REAL NOT NULL,
                        positions_count INTEGER DEFAULT 0,
                        day_change REAL DEFAULT 0,
                        day_change_percent REAL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata TEXT
                    )
                ''')
                
                # Create strategy_performance table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS strategy_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        strategy_name TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        signal_type TEXT NOT NULL,
                        confidence REAL,
                        executed BOOLEAN DEFAULT FALSE,
                        profit_loss REAL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata TEXT
                    )
                ''')
                
                # Create bot_logs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS bot_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        level TEXT NOT NULL,
                        message TEXT NOT NULL,
                        module TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata TEXT
                    )
                ''')
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def log_trade(self, symbol: str, order_type: str, quantity: float, price: float, 
                  strategy: str, confidence: float = None, reason: str = None, 
                  order_id: str = None, metadata: Dict = None) -> int:
        """
        Log a trade to the database
        
        Returns:
            Trade ID
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                total_amount = quantity * price
                metadata_json = json.dumps(metadata) if metadata else None
                
                cursor.execute('''
                    INSERT INTO trades (symbol, order_type, quantity, price, total_amount, 
                                      strategy, confidence, reason, order_id, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (symbol, order_type, quantity, price, total_amount, strategy, 
                      confidence, reason, order_id, metadata_json))
                
                trade_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"Logged trade: {order_type} {quantity} {symbol} @ ${price}")
                return trade_id
                
        except Exception as e:
            self.logger.error(f"Error logging trade: {str(e)}")
            raise
    
    def update_trade_status(self, trade_id: int, status: str, executed_at: datetime = None, 
                           order_id: str = None):
        """Update trade status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if executed_at is None:
                    executed_at = datetime.now()
                
                cursor.execute('''
                    UPDATE trades 
                    SET status = ?, executed_at = ?, order_id = COALESCE(?, order_id)
                    WHERE id = ?
                ''', (status, executed_at, order_id, trade_id))
                
                conn.commit()
                self.logger.info(f"Updated trade {trade_id} status to {status}")
                
        except Exception as e:
            self.logger.error(f"Error updating trade status: {str(e)}")
            raise
    
    def log_portfolio_snapshot(self, total_value: float, buying_power: float, 
                              positions_count: int = 0, day_change: float = 0, 
                              day_change_percent: float = 0, metadata: Dict = None):
        """Log portfolio snapshot"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                metadata_json = json.dumps(metadata) if metadata else None
                
                cursor.execute('''
                    INSERT INTO portfolio_snapshots (total_value, buying_power, positions_count,
                                                   day_change, day_change_percent, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (total_value, buying_power, positions_count, day_change, 
                      day_change_percent, metadata_json))
                
                conn.commit()
                self.logger.debug("Portfolio snapshot logged")
                
        except Exception as e:
            self.logger.error(f"Error logging portfolio snapshot: {str(e)}")
    
    def log_strategy_signal(self, strategy_name: str, symbol: str, signal_type: str, 
                           confidence: float = None, executed: bool = False, 
                           metadata: Dict = None):
        """Log strategy signal"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                metadata_json = json.dumps(metadata) if metadata else None
                
                cursor.execute('''
                    INSERT INTO strategy_performance (strategy_name, symbol, signal_type,
                                                    confidence, executed, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (strategy_name, symbol, signal_type, confidence, executed, metadata_json))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error logging strategy signal: {str(e)}")
    
    def get_recent_trades(self, limit: int = 50) -> List[Dict]:
        """Get recent trades"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM trades 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (limit,))
                
                columns = [description[0] for description in cursor.description]
                trades = []
                
                for row in cursor.fetchall():
                    trade = dict(zip(columns, row))
                    if trade['metadata']:
                        trade['metadata'] = json.loads(trade['metadata'])
                    trades.append(trade)
                
                return trades
                
        except Exception as e:
            self.logger.error(f"Error getting recent trades: {str(e)}")
            return []
    
    def get_portfolio_history(self, days: int = 30) -> List[Dict]:
        """Get portfolio history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM portfolio_snapshots 
                    WHERE created_at >= datetime('now', '-{} days')
                    ORDER BY created_at DESC
                '''.format(days))
                
                columns = [description[0] for description in cursor.description]
                snapshots = []
                
                for row in cursor.fetchall():
                    snapshot = dict(zip(columns, row))
                    if snapshot['metadata']:
                        snapshot['metadata'] = json.loads(snapshot['metadata'])
                    snapshots.append(snapshot)
                
                return snapshots
                
        except Exception as e:
            self.logger.error(f"Error getting portfolio history: {str(e)}")
            return []
    
    def get_strategy_performance(self, strategy_name: str = None, days: int = 30) -> List[Dict]:
        """Get strategy performance data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if strategy_name:
                    cursor.execute('''
                        SELECT * FROM strategy_performance 
                        WHERE strategy_name = ? AND created_at >= datetime('now', '-{} days')
                        ORDER BY created_at DESC
                    '''.format(days), (strategy_name,))
                else:
                    cursor.execute('''
                        SELECT * FROM strategy_performance 
                        WHERE created_at >= datetime('now', '-{} days')
                        ORDER BY created_at DESC
                    '''.format(days))
                
                columns = [description[0] for description in cursor.description]
                performance = []
                
                for row in cursor.fetchall():
                    perf = dict(zip(columns, row))
                    if perf['metadata']:
                        perf['metadata'] = json.loads(perf['metadata'])
                    performance.append(perf)
                
                return performance
                
        except Exception as e:
            self.logger.error(f"Error getting strategy performance: {str(e)}")
            return []