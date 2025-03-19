import os
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from infrastructure.config import get_config


class WhatsAppAuth:
    """WhatsApp Web authentication handler"""
    
    def __init__(self, headless=None, session_dir=None):
        config = get_config()
        self.headless = headless if headless is not None else config.getboolean("WhatsApp", "headless", fallback=True)
        self.session_dir = session_dir or config.get("WhatsApp", "session_dir", fallback="./whatsapp-session")
        self.driver = None
    
    def create_driver(self):
        """Create and configure Chrome WebDriver"""
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--window-size=1280,800")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Use persistent session
        session_path = Path(self.session_dir).absolute()
        session_path.mkdir(exist_ok=True)
        options.add_argument(f"user-data-dir={session_path}")
        
        try:
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            return self.driver
        except Exception as e:
            print(f"Error creating Chrome driver: {e}")
            # Fallback to local chromedriver
            self.driver = webdriver.Chrome(options=options)
            return self.driver
    
    def is_authenticated(self):
        """Check if WhatsApp Web is authenticated"""
        print("Checking if WhatsApp is authenticated...")
        self.driver = self.create_driver()
        
        try:
            self.driver.get("https://web.whatsapp.com/")
            
            # Wait for page to load
            print("Waiting for page to load (10 seconds)...")
            time.sleep(10)
            
            # Take screenshot for debugging
            os.makedirs("logs", exist_ok=True)
            self.driver.save_screenshot("logs/whatsapp_current.png")
            print("Current page screenshot saved as logs/whatsapp_current.png")
            
            # Check if authenticated (side panel exists)
            side_panel = self.driver.find_elements(By.ID, "side")
            if side_panel:
                print("✓ WhatsApp is authenticated! Side panel found.")
                return True
            
            # Check for QR code
            qr_code = self.driver.find_elements(By.CSS_SELECTOR, "canvas[aria-label='Scan me!'], canvas[aria-label='Scan this code on your phone to log in']")
            if qr_code:
                print("× WhatsApp needs authentication - QR code found.")
                os.makedirs("logs", exist_ok=True)
                qr_code[0].screenshot("logs/whatsapp_qr.png")
                print("QR code saved as logs/whatsapp_qr.png")
                return False
            
            # Look for any canvas that might be the QR code
            any_canvas = self.driver.find_elements(By.TAG_NAME, "canvas")
            if any_canvas:
                print("× Found a canvas element that might be the QR code.")
                os.makedirs("logs", exist_ok=True)
                any_canvas[0].screenshot("logs/whatsapp_qr_alt.png")
                print("Possible QR code saved as logs/whatsapp_qr_alt.png")
                return False
            
            # If we get here, we're not sure what state we're in
            print("? Uncertain authentication state - no QR code or side panel found.")
            return False
            
        except Exception as e:
            print(f"Error checking authentication: {e}")
            os.makedirs("logs", exist_ok=True)
            self.driver.save_screenshot("logs/auth_error.png")
            print("Error screenshot saved as logs/auth_error.png")
            return False
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def wait_for_authentication(self, timeout_minutes=5):
        """Wait for user to authenticate with QR code"""
        self.driver = self.create_driver()
        
        try:
            self.driver.get("https://web.whatsapp.com/")
            print(f"Please scan the QR code to authenticate (timeout: {timeout_minutes} minutes)")
            
            # Check for side panel indicating authentication
            wait = WebDriverWait(self.driver, timeout_minutes * 60)
            wait.until(EC.presence_of_element_located((By.ID, "side")))
            
            print("✓ Successfully authenticated with WhatsApp!")
            return True
        except Exception as e:
            print(f"Authentication failed or timed out: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None