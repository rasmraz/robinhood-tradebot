"""
Web Dashboard for Trading Bot
Provides a web interface to monitor and control the trading bot
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_cors import CORS

logger = logging.getLogger(__name__)


class TradingDashboard:
    """Web dashboard for the trading bot"""
    
    def __init__(self, trading_bot, config):
        self.trading_bot = trading_bot
        self.config = config
        self.app = Flask(__name__, template_folder='templates', static_folder='static')
        self.app.secret_key = config.get('flask_secret_key', 'your-secret-key-here')
        
        # Enable CORS for all routes
        CORS(self.app, origins="*")
        
        self.setup_routes()
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page"""
            return render_template('dashboard.html')
        
        @self.app.route('/api/status')
        def get_status():
            """Get bot status"""
            return jsonify({
                'is_running': self.trading_bot.is_running,
                'is_authenticated': self.trading_bot.auth.is_authenticated,
                'active_strategies': self.trading_bot.active_strategies,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/portfolio')
        def get_portfolio():
            """Get portfolio summary"""
            portfolio = self.trading_bot.get_portfolio_summary()
            return jsonify(portfolio)
        
        @self.app.route('/api/trades')
        def get_trades():
            """Get recent trades"""
            limit = request.args.get('limit', 50, type=int)
            trades = self.trading_bot.get_trade_history(limit)
            return jsonify(trades)
        
        @self.app.route('/api/analyze/<symbol>')
        def analyze_symbol(symbol):
            """Analyze a specific symbol"""
            try:
                signals = self.trading_bot.analyze_symbol(symbol.upper())
                final_signal = self.trading_bot.make_trading_decision(signals)
                
                return jsonify({
                    'symbol': symbol.upper(),
                    'signals': {
                        name: {
                            'order_type': signal.order_type.value,
                            'confidence': signal.confidence,
                            'reason': signal.reason,
                            'data': signal.data
                        } for name, signal in signals.items()
                    },
                    'final_signal': {
                        'order_type': final_signal.order_type.value,
                        'confidence': final_signal.confidence,
                        'reason': final_signal.reason
                    },
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/trade', methods=['POST'])
        def execute_trade():
            """Execute a manual trade"""
            try:
                data = request.get_json()
                symbol = data.get('symbol', '').upper()
                order_type = data.get('order_type', '').lower()
                amount = float(data.get('amount', 0))
                
                if not symbol or not order_type or amount <= 0:
                    return jsonify({'error': 'Invalid trade parameters'}), 400
                
                # Create a manual signal
                from ..strategies.base_strategy import TradeSignal, OrderType
                
                if order_type == 'buy':
                    signal = TradeSignal(OrderType.BUY, 1.0, "Manual trade")
                elif order_type == 'sell':
                    signal = TradeSignal(OrderType.SELL, 1.0, "Manual trade")
                else:
                    return jsonify({'error': 'Invalid order type'}), 400
                
                success = self.trading_bot.execute_trade(symbol, signal, amount)
                
                return jsonify({
                    'success': success,
                    'message': f"Trade {'executed' if success else 'failed'}"
                })
                
            except Exception as e:
                logger.error(f"Error executing manual trade: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/risk')
        def get_risk_metrics():
            """Get risk management metrics"""
            try:
                # Basic risk metrics
                portfolio = self.trading_bot.get_portfolio_summary()
                risk_metrics = {
                    'buying_power': portfolio.get('buying_power', 0),
                    'total_value': portfolio.get('total_value', 0),
                    'positions': portfolio.get('positions', 0),
                    'day_change': portfolio.get('day_change', 0),
                    'max_positions': self.config.get('max_positions', 5),
                    'default_trade_amount': self.trading_bot.default_trade_amount
                }
                return jsonify(risk_metrics)
            except Exception as e:
                logger.error(f"Error getting risk metrics: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/start', methods=['POST'])
        def start_bot():
            """Start the trading bot"""
            try:
                if self.trading_bot.start():
                    return jsonify({'success': True, 'message': 'Bot started successfully'})
                else:
                    return jsonify({'success': False, 'message': 'Failed to start bot'}), 500
            except Exception as e:
                logger.error(f"Error starting bot: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/stop', methods=['POST'])
        def stop_bot():
            """Stop the trading bot"""
            try:
                self.trading_bot.stop()
                return jsonify({'success': True, 'message': 'Bot stopped successfully'})
            except Exception as e:
                logger.error(f"Error stopping bot: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/config')
        def get_config():
            """Get bot configuration (sanitized)"""
            safe_config = {
                'active_strategies': self.trading_bot.active_strategies,
                'default_trade_amount': self.trading_bot.default_trade_amount,
                'min_confidence': self.config.get('min_confidence', 0.6),
                'max_positions': self.config.get('max_positions', 5),
                'risk_percentage': self.config.get('risk_percentage', 2.0)
            }
            return jsonify(safe_config)
        
        @self.app.route('/api/config', methods=['POST'])
        def update_config():
            """Update bot configuration"""
            try:
                data = request.get_json()
                
                # Update allowed configuration parameters
                if 'active_strategies' in data:
                    self.trading_bot.active_strategies = data['active_strategies']
                
                if 'default_trade_amount' in data:
                    self.trading_bot.default_trade_amount = float(data['default_trade_amount'])
                
                if 'min_confidence' in data:
                    self.config['min_confidence'] = float(data['min_confidence'])
                
                return jsonify({'success': True, 'message': 'Configuration updated'})
                
            except Exception as e:
                logger.error(f"Error updating config: {str(e)}")
                return jsonify({'error': str(e)}), 500
    
    def run(self, host='0.0.0.0', port=None, debug=False):
        """Run the Flask application"""
        port = port or int(self.config.get('flask_port', 12000))
        logger.info(f"Starting web dashboard on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)