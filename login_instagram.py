#!/usr/bin/env python3
"""
Instagram Login Automation Bot - Python Version
Converts AutoIt script to Python using Selenium and modern libraries
Author: Python Automation Master Agent
"""

import time
import os
import sys
import logging
import getpass
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import psycopg2
from psycopg2 import Error, sql
import pyautogui
import pyperclip

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('instagram_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    host: str = "localhost"
    port: int = 5432
    database: str = "wwinst_social_media_manager_dev"
    username: str = "wwinst_root"
    password: str = "Adorigram190120!"
    
@dataclass
class InstagramCredentials:
    """Instagram account credentials"""
    id_conta: int
    login: str
    senha: str
    segunda_etapa: str
    segundo_fator: int

@dataclass
class RobotStatus:
    """Robot status information"""
    id_robo: int
    status: str
    id_usuario: int

class DatabaseManager:
    """Handles PostgreSQL database operations"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection: Optional[psycopg2.extensions.connection] = None
        
    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password
            )
            self.connection.autocommit = True
            logger.info("PostgreSQL connection established successfully")
            return True
        except Error as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            logger.info("PostgreSQL connection closed")
    
    def get_robot_status(self, robot_name: str) -> Optional[RobotStatus]:
        """Get robot status from database"""
        try:
            cursor = self.connection.cursor()
            query = "SELECT id, status, id_usuario FROM robo WHERE nome_acc = %s"
            cursor.execute(query, (robot_name,))
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return RobotStatus(id_robo=result[0], status=result[1], id_usuario=result[2])
            return None
        except Error as e:
            logger.error(f"Error getting robot status: {e}")
            return None
    
    def get_instagram_credentials(self, id_robo: int) -> Optional[InstagramCredentials]:
        """Get Instagram credentials from database"""
        try:
            cursor = self.connection.cursor()
            query = "SELECT id, login, senha, segunda_etapa, segundo_fator FROM autentica_instagram WHERE id_robo = %s"
            cursor.execute(query, (id_robo,))
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return InstagramCredentials(
                    id_conta=result[0],
                    login=result[1],
                    senha=result[2],
                    segunda_etapa=result[3],
                    segundo_fator=result[4]
                )
            return None
        except Error as e:
            logger.error(f"Error getting Instagram credentials: {e}")
            return None
    
    def update_segundo_fator(self, id_conta: int, segundo_fator: int):
        """Update segundo_fator status"""
        try:
            cursor = self.connection.cursor()
            query = "UPDATE autentica_instagram SET segundo_fator = %s WHERE id = %s"
            cursor.execute(query, (segundo_fator, id_conta))
            cursor.close()
            logger.info(f"Updated segundo_fator to {segundo_fator} for account {id_conta}")
        except Error as e:
            logger.error(f"Error updating segundo_fator: {e}")

class InstagramBot:
    """Instagram automation bot"""
    
    def __init__(self):
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self.db_manager = DatabaseManager(DatabaseConfig())
        self.robot_name = getpass.getuser()
        
        # Color constants for pixel detection
        self.COLOR_BLACK = (0, 0, 0)
        self.COLOR_WHITE = (255, 255, 255)
        self.COLOR_BLUE = (74, 115, 233)  # Instagram blue
        self.COLOR_LIGHT_BLUE = (129, 168, 255)
        self.COLOR_BABY_BLUE = (149, 215, 255)
        
    def setup_driver(self) -> bool:
        """Setup Chrome WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Use default Chrome installation
            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            if os.path.exists(chrome_path):
                chrome_options.binary_location = chrome_path
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 10)
            
            logger.info("Chrome WebDriver setup successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to setup WebDriver: {e}")
            return False
    
    def get_pixel_color(self, x: int, y: int) -> Tuple[int, int, int]:
        """Get pixel color at coordinates"""
        try:
            return pyautogui.pixel(x, y)
        except Exception as e:
            logger.error(f"Error getting pixel color: {e}")
            return (0, 0, 0)
    
    def wait_for_robot_availability(self) -> Optional[RobotStatus]:
        """Wait for robot to become available"""
        logger.info("Waiting for robot availability...")
        
        while True:
            robot_status = self.db_manager.get_robot_status(self.robot_name)
            if not robot_status:
                logger.error("Failed to get robot status")
                return None
                
            if robot_status.status == 'Livre':
                logger.info("Robot is available")
                return robot_status
            elif robot_status.status == 'Erro':
                logger.error("Robot status is Error")
                return None
            else:
                logger.info(f"Robot status: {robot_status.status}. Waiting...")
                time.sleep(5)
    
    def wait_for_credentials_ready(self, id_robo: int) -> Optional[InstagramCredentials]:
        """Wait for Instagram credentials to be ready"""
        logger.info("Waiting for credentials...")
        
        while True:
            credentials = self.db_manager.get_instagram_credentials(id_robo)
            if not credentials:
                logger.error("Failed to get Instagram credentials")
                return None
            
            if credentials.segundo_fator == 8:
                continue
            elif credentials.segundo_fator == 5:
                logger.info("Credentials are ready")
                return credentials
            else:
                logger.info("Credentials are ready")
                return credentials
    
    def login_to_instagram(self, credentials: InstagramCredentials) -> bool:
        """Perform Instagram login"""
        try:
            logger.info("Opening Instagram...")
            self.driver.get("https://www.instagram.com/")
            time.sleep(3)
            
            # Wait for login form
            username_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            password_field = self.driver.find_element(By.NAME, "password")
            
            # Clear and enter credentials
            username_field.clear()
            username_field.send_keys(credentials.login)
            
            password_field.clear()
            password_field.send_keys(credentials.senha)
            
            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            logger.info("Login credentials submitted")
            time.sleep(10)
            
            return self.handle_post_login(credentials)
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def handle_post_login(self, credentials: InstagramCredentials) -> bool:
        """Handle post-login scenarios (2FA, errors, etc.)"""
        try:
            # Check for various post-login states
            current_url = self.driver.current_url
            
            # Check if login was successful
            if "instagram.com" in current_url and "accounts/login" not in current_url:
                logger.info("Login successful!")
                self.db_manager.update_segundo_fator(credentials.id_conta, 5)
                return True
            
            # Check for 2FA requirement
            if self.check_for_2fa():
                return self.handle_2fa(credentials)
            
            # Check for incorrect password
            if self.check_for_password_error():
                logger.warning("Incorrect password detected")
                self.db_manager.update_segundo_fator(credentials.id_conta, 3)
                return self.retry_login(credentials)
            
            return False
            
        except Exception as e:
            logger.error(f"Post-login handling failed: {e}")
            return False
    
    def check_for_2fa(self) -> bool:
        """Check if 2FA is required"""
        try:
            # Look for 2FA elements
            two_factor_elements = [
                "//input[@name='verificationCode']",
                "//input[@aria-label='Security code']",
                "//*[contains(text(), 'Enter the 6-digit code')]"
            ]
            
            for element in two_factor_elements:
                try:
                    self.driver.find_element(By.XPATH, element)
                    return True
                except NoSuchElementException:
                    continue
            
            return False
        except Exception:
            return False
    
    def check_for_password_error(self) -> bool:
        """Check for password error"""
        try:
            error_elements = [
                "//*[contains(text(), 'Sorry, your password was incorrect')]",
                "//*[contains(text(), 'incorrect')]",
                "//div[@role='alert']"
            ]
            
            for element in error_elements:
                try:
                    self.driver.find_element(By.XPATH, element)
                    return True
                except NoSuchElementException:
                    continue
            
            return False
        except Exception:
            return False
    
    def handle_2fa(self, credentials: InstagramCredentials) -> bool:
        """Handle 2FA authentication"""
        logger.info("2FA detected. Waiting for code...")
        self.db_manager.update_segundo_fator(credentials.id_conta, 2)
        
        # Wait for user to provide 2FA code in database
        max_attempts = 12  # 2 minutes wait
        for attempt in range(max_attempts):
            time.sleep(10)
            updated_credentials = self.db_manager.get_instagram_credentials(credentials.id_conta)
            
            if updated_credentials and updated_credentials.segundo_fator == 4:
                # Code provided, enter it
                try:
                    code_input = self.driver.find_element(By.NAME, "verificationCode")
                    code_input.clear()
                    code_input.send_keys(updated_credentials.segunda_etapa)
                    code_input.send_keys(Keys.RETURN)
                    
                    self.db_manager.update_segundo_fator(credentials.id_conta, 2)
                    time.sleep(30)
                    
                    # Check if login was successful
                    if "instagram.com" in self.driver.current_url and "accounts/login" not in self.driver.current_url:
                        logger.info("2FA login successful!")
                        self.db_manager.update_segundo_fator(credentials.id_conta, 5)
                        return True
                        
                except Exception as e:
                    logger.error(f"Error entering 2FA code: {e}")
        
        logger.error("2FA timeout or failed")
        self.db_manager.update_segundo_fator(credentials.id_conta, 6)
        return False
    
    def retry_login(self, credentials: InstagramCredentials) -> bool:
        """Retry login with updated credentials"""
        max_retries = 3
        
        for retry in range(max_retries):
            logger.info(f"Login retry {retry + 1}/{max_retries}")
            
            # Get updated credentials
            time.sleep(30)
            updated_credentials = self.db_manager.get_instagram_credentials(credentials.id_conta)
            
            if updated_credentials and updated_credentials.segundo_fator == 1:
                # Try login again
                try:
                    username_field = self.driver.find_element(By.NAME, "username")
                    password_field = self.driver.find_element(By.NAME, "password")
                    
                    username_field.clear()
                    username_field.send_keys(updated_credentials.login)
                    
                    password_field.clear()
                    password_field.send_keys(updated_credentials.senha)
                    
                    login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                    login_button.click()
                    
                    time.sleep(10)
                    
                    if self.handle_post_login(updated_credentials):
                        return True
                        
                except Exception as e:
                    logger.error(f"Retry login failed: {e}")
        
        logger.error("All login retries failed")
        self.db_manager.update_segundo_fator(credentials.id_conta, 7)
        return False
    
    def run(self) -> bool:
        """Main execution method"""
        try:
            # Connect to database
            if not self.db_manager.connect():
                return False
            
            # Wait for robot availability
            robot_status = self.wait_for_robot_availability()
            if not robot_status:
                return False
            
            # Wait for credentials
            credentials = self.wait_for_credentials_ready(robot_status.id_robo)
            if not credentials:
                return False
            
            # Setup browser
            if not self.setup_driver():
                return False
            
            # Perform login
            success = self.login_to_instagram(credentials)
            
            if success:
                logger.info("Instagram login completed successfully")
                
                # Keep browser open for a while (equivalent to original script)
                time.sleep(10)
                
            return success
            
        except Exception as e:
            logger.error(f"Bot execution failed: {e}")
            return False
        
        finally:
            # Cleanup
            if self.driver:
                self.driver.quit()
            self.db_manager.disconnect()

def main():
    """Main entry point"""
    logger.info("Starting Instagram Login Bot")
    
    bot = InstagramBot()
    success = bot.run()
    
    if success:
        logger.info("Bot completed successfully")
        sys.exit(0)
    else:
        logger.error("Bot failed")
        sys.exit(1)

if __name__ == "__main__":
    main()