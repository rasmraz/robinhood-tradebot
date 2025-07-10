"""
Robinhood Authentication Module
Handles login, MFA, and session management for Robinhood API
"""

import os
import logging
import pyotp
import robin_stocks.robinhood as rh
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class RobinhoodAuth:
    """Handles Robinhood authentication and session management"""
    
    def __init__(self):
        self.username = os.getenv('ROBINHOOD_USERNAME')
        self.password = os.getenv('ROBINHOOD_PASSWORD')
        self.mfa_code = os.getenv('ROBINHOOD_MFA_CODE')
        self.is_authenticated = False
        
    def login(self) -> bool:
        """
        Authenticate with Robinhood
        Returns True if successful, False otherwise
        """
        try:
            if not self.username or not self.password:
                logger.error("Robinhood credentials not found in environment variables")
                return False
            
            # Try login with MFA if available
            if self.mfa_code:
                totp = pyotp.TOTP(self.mfa_code)
                mfa_token = totp.now()
                logger.info("Attempting login with MFA...")
                login_result = rh.login(
                    username=self.username,
                    password=self.password,
                    mfa_code=mfa_token
                )
            else:
                logger.info("Attempting login without MFA...")
                login_result = rh.login(
                    username=self.username,
                    password=self.password
                )
            
            if login_result:
                self.is_authenticated = True
                logger.info("Successfully authenticated with Robinhood")
                return True
            else:
                logger.error("Failed to authenticate with Robinhood")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False
    
    def logout(self) -> None:
        """Logout from Robinhood"""
        try:
            rh.logout()
            self.is_authenticated = False
            logger.info("Successfully logged out from Robinhood")
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get account information"""
        if not self.is_authenticated:
            logger.error("Not authenticated. Please login first.")
            return None
        
        try:
            account_info = rh.profiles.load_account_profile()
            return account_info
        except Exception as e:
            logger.error(f"Error getting account info: {str(e)}")
            return None
    
    def get_portfolio_info(self) -> Optional[Dict[str, Any]]:
        """Get portfolio information"""
        if not self.is_authenticated:
            logger.error("Not authenticated. Please login first.")
            return None
        
        try:
            portfolio_info = rh.profiles.load_portfolio_profile()
            return portfolio_info
        except Exception as e:
            logger.error(f"Error getting portfolio info: {str(e)}")
            return None
    
    def check_authentication(self) -> bool:
        """Check if still authenticated"""
        try:
            # Try to get account info to verify authentication
            account_info = rh.profiles.load_account_profile()
            return account_info is not None
        except:
            self.is_authenticated = False
            return False