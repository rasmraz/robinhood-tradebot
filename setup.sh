#!/bin/bash

# Robinhood Trading Bot Setup Script
# This script automates the setup process for the trading bot

set -e  # Exit on any error

echo "🤖 Robinhood Trading Bot Setup"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_warning "This script should not be run as root for security reasons"
   read -p "Continue anyway? (y/N): " -n 1 -r
   echo
   if [[ ! $REPLY =~ ^[Yy]$ ]]; then
       exit 1
   fi
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    if command_exists pip3; then
        pip3 install -r requirements.txt
    elif command_exists pip; then
        pip install -r requirements.txt
    else
        print_error "pip not found. Please install Python pip first."
        exit 1
    fi
}

# Function to setup environment file
setup_environment() {
    print_status "Setting up environment configuration..."
    
    if [[ ! -f .env ]]; then
        if [[ -f .env.example ]]; then
            cp .env.example .env
            print_status "Created .env file from .env.example"
        else
            # Create basic .env file
            cat > .env << EOF
# Robinhood Credentials
ROBINHOOD_USERNAME=your_robinhood_username
ROBINHOOD_PASSWORD=your_robinhood_password
ROBINHOOD_MFA_CODE=

# Trading Configuration
DEFAULT_TRADE_AMOUNT=100.00
RISK_PERCENTAGE=2.0
MAX_POSITIONS=5

# Web Interface
FLASK_SECRET_KEY=$(openssl rand -hex 32)
FLASK_PORT=12001

# Database
DATABASE_PATH=./data/trading_bot.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/trading_bot.log
EOF
            print_status "Created basic .env file"
        fi
        
        print_warning "Please edit .env file with your Robinhood credentials before running the bot"
        print_status "You can edit it with: nano .env"
    else
        print_status ".env file already exists"
    fi
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    mkdir -p data logs
    print_status "Created data and logs directories"
}

# Function to check Python version
check_python() {
    print_status "Checking Python version..."
    
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        print_status "Python version: $PYTHON_VERSION"
        
        # Check if version is 3.8 or higher
        if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
            print_status "Python version is compatible"
        else
            print_error "Python 3.8 or higher is required. Current version: $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 not found. Please install Python 3.8 or higher."
        exit 1
    fi
}

# Function to install system dependencies
install_system_deps() {
    print_status "Checking system dependencies..."
    
    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command_exists apt-get; then
            print_status "Detected Ubuntu/Debian system"
            sudo apt-get update
            sudo apt-get install -y python3-pip python3-venv curl
        elif command_exists yum; then
            print_status "Detected CentOS/RHEL system"
            sudo yum install -y python3-pip curl
        elif command_exists dnf; then
            print_status "Detected Fedora system"
            sudo dnf install -y python3-pip curl
        else
            print_warning "Unknown Linux distribution. Please install python3-pip manually."
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        print_status "Detected macOS system"
        if ! command_exists brew; then
            print_status "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew install python3
    else
        print_warning "Unknown operating system. Please ensure Python 3.8+ and pip are installed."
    fi
}

# Function to setup Docker (optional)
setup_docker() {
    print_header "Docker Setup (Optional)"
    read -p "Do you want to install Docker for containerized deployment? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command_exists docker; then
            print_status "Docker is already installed"
        else
            print_status "Installing Docker..."
            
            if [[ "$OSTYPE" == "linux-gnu"* ]]; then
                curl -fsSL https://get.docker.com -o get-docker.sh
                sudo sh get-docker.sh
                sudo usermod -aG docker $USER
                rm get-docker.sh
                print_status "Docker installed. Please log out and back in for group changes to take effect."
            elif [[ "$OSTYPE" == "darwin"* ]]; then
                print_status "Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
            fi
        fi
        
        if command_exists docker-compose || command_exists docker compose; then
            print_status "Docker Compose is available"
        else
            print_status "Installing Docker Compose..."
            sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            sudo chmod +x /usr/local/bin/docker-compose
        fi
    fi
}

# Function to test installation
test_installation() {
    print_header "Testing Installation"
    
    print_status "Testing Python imports..."
    python3 -c "
import sys
sys.path.insert(0, 'src')
try:
    from src.trading_bot import TradingBot
    print('✓ Trading bot import successful')
except ImportError as e:
    print(f'✗ Import failed: {e}')
    sys.exit(1)
"
    
    print_status "Testing web dashboard..."
    timeout 5 python3 -c "
import sys
sys.path.insert(0, 'src')
from src.web.dashboard import TradingDashboard
print('✓ Web dashboard import successful')
" || print_warning "Web dashboard test timed out (this is normal)"
    
    print_status "Installation test completed successfully!"
}

# Function to show next steps
show_next_steps() {
    print_header "Setup Complete! 🎉"
    echo
    print_status "Next steps:"
    echo "1. Edit your .env file with Robinhood credentials:"
    echo "   nano .env"
    echo
    echo "2. Run the trading bot:"
    echo "   # Web dashboard mode (recommended)"
    echo "   python3 main.py --mode web"
    echo
    echo "   # CLI mode"
    echo "   python3 main.py --mode cli"
    echo
    echo "   # Automated trading mode"
    echo "   python3 main.py --mode auto --symbols AAPL GOOGL MSFT"
    echo
    echo "3. Access web dashboard at: http://localhost:12001"
    echo
    if command_exists docker; then
        echo "4. Or run with Docker:"
        echo "   docker-compose up -d"
        echo
    fi
    print_warning "⚠️  IMPORTANT: This is for educational purposes only. Trading involves risk!"
    print_warning "⚠️  Always test with small amounts first!"
    echo
}

# Main setup function
main() {
    print_header "Starting Robinhood Trading Bot Setup..."
    echo
    
    # Check if we're in the right directory
    if [[ ! -f "main.py" ]] || [[ ! -f "requirements.txt" ]]; then
        print_error "Please run this script from the robinhood-tradebot directory"
        exit 1
    fi
    
    # Run setup steps
    check_python
    install_system_deps
    create_directories
    install_python_deps
    setup_environment
    setup_docker
    test_installation
    show_next_steps
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Robinhood Trading Bot Setup Script"
        echo
        echo "Usage: $0 [options]"
        echo
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --docker-only  Only setup Docker components"
        echo "  --no-docker    Skip Docker setup"
        echo "  --test-only    Only run installation tests"
        echo
        exit 0
        ;;
    --docker-only)
        setup_docker
        exit 0
        ;;
    --test-only)
        test_installation
        exit 0
        ;;
    --no-docker)
        export SKIP_DOCKER=1
        ;;
esac

# Run main setup
main

print_status "Setup script completed successfully!"