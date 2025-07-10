# Robinhood Trading Bot - Deployment Guide

## 🚀 Quick Start Deployment

### Prerequisites
- Python 3.11+
- Robinhood account with API access
- Docker (optional, for containerized deployment)

### 1. Local Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd robinhood-tradebot

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Robinhood credentials
```

### 2. Configuration

Edit `.env` file with your credentials:

```env
# Robinhood Credentials
ROBINHOOD_USERNAME=your_robinhood_username
ROBINHOOD_PASSWORD=your_robinhood_password
ROBINHOOD_MFA_CODE=your_mfa_secret_key_optional

# Trading Configuration
DEFAULT_TRADE_AMOUNT=100.00
RISK_PERCENTAGE=2.0
MAX_POSITIONS=5

# Web Interface
FLASK_SECRET_KEY=your-secret-key-here
FLASK_PORT=12001

# Database
DATABASE_PATH=./data/trading_bot.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/trading_bot.log
```

### 3. Run the Application

#### Web Dashboard (Recommended)
```bash
python main.py --mode web
```
Access at: http://localhost:12001

#### CLI Mode
```bash
python main.py --mode cli
```

#### Automated Trading
```bash
python main.py --mode auto --symbols AAPL GOOGL MSFT TSLA
```

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Using Docker directly

```bash
# Build image
docker build -t robinhood-tradebot .

# Run container
docker run -d \
  --name robinhood-tradebot \
  -p 12001:12001 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  robinhood-tradebot
```

## ☁️ Cloud Deployment

### AWS EC2 Deployment

1. **Launch EC2 Instance**
   - Ubuntu 22.04 LTS
   - t3.micro or larger
   - Security group: Allow port 12001

2. **Setup Instance**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Docker
   sudo apt install docker.io docker-compose -y
   sudo usermod -aG docker ubuntu
   
   # Clone repository
   git clone <repository-url>
   cd robinhood-tradebot
   
   # Configure environment
   cp .env.example .env
   nano .env  # Edit with your credentials
   
   # Deploy
   docker-compose up -d
   ```

3. **Access Application**
   - Web Dashboard: `http://your-ec2-ip:12001`

### Google Cloud Platform (GCP)

1. **Create Compute Engine Instance**
   ```bash
   gcloud compute instances create robinhood-tradebot \
     --image-family=ubuntu-2204-lts \
     --image-project=ubuntu-os-cloud \
     --machine-type=e2-micro \
     --tags=http-server
   ```

2. **Configure Firewall**
   ```bash
   gcloud compute firewall-rules create allow-tradebot \
     --allow tcp:12001 \
     --source-ranges 0.0.0.0/0 \
     --target-tags http-server
   ```

3. **Deploy Application**
   ```bash
   # SSH to instance
   gcloud compute ssh robinhood-tradebot
   
   # Follow same setup as EC2
   ```

### DigitalOcean Droplet

1. **Create Droplet**
   - Ubuntu 22.04
   - Basic plan ($6/month)
   - Add SSH key

2. **Deploy**
   ```bash
   # SSH to droplet
   ssh root@your-droplet-ip
   
   # Install Docker
   apt update && apt install docker.io docker-compose -y
   
   # Clone and deploy
   git clone <repository-url>
   cd robinhood-tradebot
   cp .env.example .env
   nano .env  # Configure
   docker-compose up -d
   ```

## 🔒 Security Considerations

### Production Security Checklist

- [ ] Use strong, unique passwords
- [ ] Enable MFA on Robinhood account
- [ ] Use environment variables for secrets
- [ ] Configure firewall rules
- [ ] Use HTTPS with reverse proxy
- [ ] Regular security updates
- [ ] Monitor logs for suspicious activity
- [ ] Backup database regularly

### Reverse Proxy Setup (Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:12001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 Monitoring & Maintenance

### Health Checks

```bash
# Check application status
curl http://localhost:12001/api/status

# Check logs
docker-compose logs -f

# Monitor resources
docker stats
```

### Backup Strategy

```bash
# Backup database
cp data/trading_bot.db backups/trading_bot_$(date +%Y%m%d).db

# Backup logs
tar -czf backups/logs_$(date +%Y%m%d).tar.gz logs/

# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
mkdir -p backups
cp data/trading_bot.db backups/trading_bot_$DATE.db
tar -czf backups/logs_$DATE.tar.gz logs/
find backups/ -name "*.db" -mtime +30 -delete
find backups/ -name "*.tar.gz" -mtime +30 -delete
```

### Log Rotation

```bash
# Install logrotate
sudo apt install logrotate

# Configure log rotation
sudo nano /etc/logrotate.d/robinhood-tradebot
```

```
/path/to/robinhood-tradebot/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
}
```

## 🔧 Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify Robinhood credentials
   - Check MFA configuration
   - Ensure account is not locked

2. **Port Already in Use**
   ```bash
   # Find process using port
   sudo lsof -i :12001
   
   # Kill process
   sudo kill -9 <PID>
   
   # Or use different port
   export FLASK_PORT=12002
   ```

3. **Database Errors**
   ```bash
   # Reset database
   rm data/trading_bot.db
   python main.py --mode web  # Will recreate
   ```

4. **Memory Issues**
   ```bash
   # Check memory usage
   free -h
   
   # Restart application
   docker-compose restart
   ```

### Debug Mode

```bash
# Run with debug logging
LOG_LEVEL=DEBUG python main.py --mode web

# Check specific component
python -c "from src.auth.robinhood_auth import RobinhoodAuth; print('Auth OK')"
```

## 📈 Performance Optimization

### Production Deployment

1. **Use Gunicorn**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:12001 main:app
   ```

2. **Database Optimization**
   - Regular VACUUM operations
   - Index optimization
   - Archive old data

3. **Caching**
   - Redis for session storage
   - Cache market data
   - Rate limiting

### Scaling Considerations

- Use load balancer for multiple instances
- Separate database server
- Message queue for trade execution
- Monitoring with Prometheus/Grafana

## 🚨 Important Disclaimers

⚠️ **Risk Warning**: Trading involves substantial risk of loss. This software is for educational purposes only.

⚠️ **No Warranty**: Use at your own risk. Authors are not responsible for financial losses.

⚠️ **Testing**: Always test with small amounts first.

⚠️ **Compliance**: Ensure compliance with local regulations and Robinhood's terms of service.

## 📞 Support

For issues and questions:
1. Check logs for error messages
2. Review configuration
3. Consult documentation
4. Open GitHub issue with details

## 🔄 Updates

```bash
# Update application
git pull origin main
pip install -r requirements.txt
docker-compose down && docker-compose up -d
```

Remember to backup your data before updates!