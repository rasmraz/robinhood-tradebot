# Robinhood Trading Bot

A sophisticated Python trading bot that uses the Robinhood API to execute automated trades based on multiple technical analysis strategies. Features a modern web dashboard for monitoring and control.

## Features

### 🤖 Trading Strategies
- **Simple Moving Average (SMA)**: Crossover strategy using 50-day and 200-day moving averages
- **RSI Strategy**: Relative Strength Index for identifying overbought/oversold conditions
- **Extensible Framework**: Easy to add custom strategies

### 🛡️ Risk Management
- Position sizing based on portfolio percentage
- Daily loss limits
- Maximum position limits
- Confidence-based trade filtering

### 📊 Web Dashboard
- Real-time portfolio monitoring
- Strategy analysis and backtesting
- Manual trade execution
- Configuration management
- Trade history and performance tracking

### 🔐 Security
- Multi-factor authentication (MFA) support
- Secure credential management
- Environment-based configuration

## Quick Start

### Prerequisites
- Python 3.8+
- Robinhood account
- Docker (optional, for containerized deployment)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/rasmraz/robinhood-tradebot.git
   cd robinhood-tradebot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your Robinhood credentials and preferences
   ```

4. **Run the bot**
   ```bash
   python main.py --mode web
   ```

5. **Access the dashboard**
   Open your browser to `http://localhost:12000`

### Environment Configuration

Create a `.env` file with your settings:

```env
# Robinhood Credentials
ROBINHOOD_USERNAME=your_username
ROBINHOOD_PASSWORD=your_password
ROBINHOOD_MFA_CODE=your_mfa_secret_key  # Optional, for 2FA

# Trading Configuration
DEFAULT_TRADE_AMOUNT=100.00
RISK_PERCENTAGE=2.0
MAX_POSITIONS=5
MIN_CONFIDENCE=0.6

# Symbols to trade (comma-separated)
TRADING_SYMBOLS=AAPL,GOOGL,MSFT,TSLA,AMZN

# Auto-trading (set to true for live trading)
AUTO_TRADE=false

# Web Interface
FLASK_SECRET_KEY=your-secret-key
FLASK_PORT=12000
```

## Usage Modes

### 1. Web Dashboard Mode (Recommended)
```bash
python main.py --mode web
```
- Interactive web interface
- Real-time monitoring
- Manual trade execution
- Configuration management

### 2. Command Line Mode
```bash
python main.py --mode cli --symbols AAPL GOOGL
```
- One-time analysis and trading
- Perfect for testing strategies
- Detailed logging output

### 3. Daemon Mode
```bash
python main.py --mode daemon
```
- Background service
- Scheduled trading during market hours
- Ideal for production deployment

## Docker Deployment

### Using Docker Compose (Recommended)

1. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Start the service**
   ```bash
   docker-compose up -d
   ```

3. **View logs**
   ```bash
   docker-compose logs -f trading-bot
   ```

### Using Docker directly

```bash
# Build the image
docker build -t robinhood-tradebot .

# Run the container
docker run -d \
  --name trading-bot \
  -p 12000:12000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  robinhood-tradebot
```

## Trading Strategies

### Simple Moving Average (SMA)
- **Buy Signal**: 50-day MA crosses above 200-day MA
- **Sell Signal**: 50-day MA crosses below 200-day MA
- **Parameters**: Configurable window sizes and threshold

### RSI Strategy
- **Buy Signal**: RSI < 30 (oversold)
- **Sell Signal**: RSI > 70 (overbought)
- **Parameters**: Configurable period and thresholds

### Adding Custom Strategies

1. Create a new strategy class inheriting from `BaseStrategy`:

```python
from src.strategies.base_strategy import BaseStrategy, TradeSignal, OrderType

class MyCustomStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("My_Custom_Strategy")
    
    def analyze(self, symbol: str, data: dict) -> TradeSignal:
        # Your analysis logic here
        return TradeSignal(OrderType.BUY, 0.8, "Custom signal reason")
    
    def get_required_data(self) -> list:
        return ['prices', 'volumes']
```

2. Register the strategy in `TradingBot.__init__()`:

```python
self.strategies['custom'] = MyCustomStrategy()
```

## Risk Management

The bot includes comprehensive risk management features:

- **Position Sizing**: Automatically calculates position sizes based on portfolio percentage
- **Daily Loss Limits**: Stops trading when daily losses exceed threshold
- **Maximum Positions**: Limits the number of concurrent positions
- **Confidence Filtering**: Only executes trades above minimum confidence threshold

## API Endpoints

The web dashboard exposes a REST API:

- `GET /api/status` - Bot status and configuration
- `GET /api/portfolio` - Portfolio summary
- `GET /api/trades` - Trade history
- `GET /api/analyze/{symbol}` - Analyze specific symbol
- `POST /api/trade` - Execute manual trade
- `GET /api/risk` - Risk management metrics
- `POST /api/start` - Start the bot
- `POST /api/stop` - Stop the bot

## Database Schema

The bot uses SQLite to store:
- **trades**: All executed trades with timestamps and outcomes
- **portfolio_snapshots**: Historical portfolio values
- **strategy_performance**: Strategy-specific performance metrics

## Logging

Comprehensive logging is available:
- **File Logging**: All activities logged to `./logs/trading_bot.log`
- **Console Logging**: Real-time output during execution
- **Log Levels**: Configurable (DEBUG, INFO, WARNING, ERROR)

## Security Considerations

⚠️ **Important Security Notes**:

1. **Never commit credentials** to version control
2. **Use MFA** when possible for additional security
3. **Start with paper trading** to test strategies
4. **Monitor positions** regularly
5. **Set appropriate risk limits**

## Disclaimer

⚠️ **Trading Disclaimer**:

This software is for educational and research purposes only. Trading stocks involves substantial risk of loss and is not suitable for all investors. Past performance does not guarantee future results. The authors are not responsible for any financial losses incurred through the use of this software.

**Always**:
- Test strategies thoroughly before live trading
- Start with small amounts
- Monitor your positions regularly
- Understand the risks involved

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: Report bugs and request features via GitHub Issues
- **Documentation**: Check the wiki for detailed documentation
- **Community**: Join discussions in GitHub Discussions

## Acknowledgments

- [robin-stocks](https://github.com/jmfernandes/robin-stocks) - Robinhood API wrapper
- [yfinance](https://github.com/ranaroussi/yfinance) - Yahoo Finance data
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Bootstrap](https://getbootstrap.com/) - UI framework
