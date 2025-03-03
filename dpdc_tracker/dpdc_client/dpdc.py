import os
import json
import re
import time
import asyncio
import logging
import requests
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright
from django.conf import settings

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('dpdc_api')

class DPDCClient:
    def __init__(self, token=None, auto_extract=True):
        self.token = token
        self.base_url = "https://amiapp.dpdc.org.bd"
        self.login_url = f"{self.base_url}/login"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "tenantCode": "DPDC",
            "Origin": "https://amiapp.dpdc.org.bd",
            "Referer": "https://amiapp.dpdc.org.bd/quick-pay"
        })
        
        # If token is provided, update headers
        if self.token:
            self._update_auth_headers()
            
    def _update_auth_headers(self):
        """Update session headers with authentication token"""
        # Check if token is a JSON string and extract access_token
        try:
            token_data = json.loads(self.token)
            if isinstance(token_data, dict) and 'access_token' in token_data:
                actual_token = token_data['access_token']
            else:
                actual_token = self.token
        except (json.JSONDecodeError, TypeError):
            actual_token = self.token
            
        # Update session headers with token
        self.session.headers.update({
            "accessToken": actual_token,
            "Authorization": f"Bearer {actual_token}"
        })
    
    async def extract_token(self, token_file="auth_token.txt"):
        """Extract the auth token by visiting the site with Playwright"""
        logger.info("Attempting to extract authentication token using Playwright...")
        token = None
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Navigate to the site
                await page.goto(self.login_url)
                logger.info("Navigated to login page")
                
                # Wait for the page to load completely
                await page.wait_for_load_state("networkidle")
                
                # Wait a bit to allow any auto-login or token generation to happen
                await asyncio.sleep(3)
                
                # Check if token exists in localStorage
                token = await page.evaluate("localStorage.getItem('authbearer')")
                
                if token:
                    logger.info("Found authbearer token in localStorage!")
                    
                    # Save token to file
                    with open(token_file, "w") as f:
                        f.write(token)
                    logger.info(f"Token saved to {token_file}")
                    
                    # Update the client token
                    self.token = token
                    self._update_auth_headers()
                else:
                    logger.info("No authbearer token found in localStorage")
                    
                    # Check all localStorage items
                    all_storage = await page.evaluate("Object.keys(localStorage)")
                    if all_storage:
                        logger.info("Available localStorage keys:")
                        logger.info(str(all_storage))
                        
                        # Try to retrieve any values that might contain 'token'
                        for key in all_storage:
                            value = await page.evaluate(f"localStorage.getItem('{key}')")
                            if 'token' in key.lower() or ('token' in str(value).lower() if value else False):
                                logger.info(f"Found potential token in key: {key}")
                                token = value
                                
                                # Save this potential token
                                with open(f"{key}_token.txt", "w") as f:
                                    f.write(value)
                                logger.info(f"Token saved to {key}_token.txt")
                    
                    # Take a screenshot to help with debugging
                    await page.screenshot(path="login_page.png")
                    logger.info("Screenshot saved to login_page.png")
            except Exception as e:
                logger.error(f"Error during token extraction: {e}")
                await page.screenshot(path="error_page.png")
                logger.info("Error screenshot saved to error_page.png")
            finally:
                await browser.close()
        
        return token
            
    def get_balance(self, customer_number=None, retry_on_error=True):
        """Get balance information using the token"""
        if not customer_number:
            customer_number = getattr(settings, "DPDC_CUSTOMER_NUMBER", "35067784")

        if not self.token:
            logger.error("No token available")
            return None

        url = f"{self.base_url}/usage/usage-service"

        payload = {
            "query": f"""query{{ postBalanceDetails(input :{{
                customerNumber:"{customer_number}",tenantCode:"DPDC"       
            }} ) {{  accountId customerName customerClass mobileNumber emailId  accountType balanceRemaining connectionStatus customerType minRecharge}}}}"""
        }

        try:
            logger.info("Making balance API request...")
            response = self.session.post(url, json=payload)

            if response.status_code == 200:
                result = response.json()
                if "data" in result and "postBalanceDetails" in result["data"]:
                    balance_info = result["data"]["postBalanceDetails"]
                    logger.info(f"Balance: {balance_info['balanceRemaining']}")
                    return balance_info
                elif "errors" in result and retry_on_error:
                    logger.error("API returned errors but status code was 200")
                    logger.error(f"Errors: {result['errors']}")
                    return None

            # Handle error - token might be expired
            if retry_on_error:
                logger.error(f"API request failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                logger.warning("Token might be expired. Will try to get a new token.")
                return None
            else:
                logger.error(f"API request failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error making API request: {e}")
            return None

async def get_balance_info(customer_number=None, token_file="auth_token.txt"):
    """Helper function to get balance info with automatic token refresh if needed"""
    # First check if there's a saved token
    token = None
    token_refreshed = False
    
    try:
        with open(token_file, "r") as f:
            token = f.read().strip()
        logger.info(f"Using saved token from {token_file}")
    except FileNotFoundError:
        logger.info("No saved token found, will extract a new one")
    
    # Create client
    dpdc = DPDCClient(token=token)
    
    # First try with existing token if available
    if token:
        balance_info = dpdc.get_balance(customer_number, retry_on_error=False)
        
        # If balance check fails, the token might be expired
        if not balance_info:
            logger.warning("Failed to get balance with saved token. Token might be expired.")
            logger.info("Will extract a new token...")
            token = None
    
    # If no token or token didn't work, extract a new one
    if not token:
        # Extract the token
        token = await dpdc.extract_token(token_file)
        token_refreshed = True
        
        if token:
            logger.info("Token extraction successful!")
            # Update client with new token
            dpdc.token = token
            dpdc._update_auth_headers()
        else:
            logger.error("Failed to extract authentication token")
            return None
    
    # Try to get balance info with new or existing token
    balance_info = dpdc.get_balance(customer_number)
    
    # If still failing after token refresh, try one more time with a fresh token
    if not balance_info and not token_refreshed:
        logger.warning("Still failing with existing token. Will force a new token extraction.")
        # Force a new token extraction
        token = await dpdc.extract_token(token_file)
        
        if token:
            logger.info("Token extraction successful on retry!")
            # Update client with new token
            dpdc.token = token
            dpdc._update_auth_headers()
            
            # Try one more time with the fresh token
            balance_info = dpdc.get_balance(customer_number, retry_on_error=False)
    
    return balance_info