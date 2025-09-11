#!/usr/bin/env python3
"""
Instagram Bot - Login com Código 2FA Pre-definido
Insere automaticamente o código 2FA fornecido
"""

import time
import sys
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

try:
    import winsound
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('instagram_with_code.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class InstagramWithCode:
    """Instagram bot com código 2FA pré-definido"""
    
    def __init__(self, email: str, password: str, two_fa_code: str):
        self.email = email
        self.password = password
        self.two_fa_code = two_fa_code
        self.driver = None
        self.wait = None
        
    def setup_driver(self) -> bool:
        """Setup Chrome WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            if WEBDRIVER_MANAGER_AVAILABLE:
                try:
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                except Exception:
                    self.driver = webdriver.Chrome(options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
            
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 20)
            
            logger.info("Chrome configurado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro no WebDriver: {e}")
            return False
    
    def play_success_sound(self):
        """Som de sucesso"""
        try:
            if SOUND_AVAILABLE:
                winsound.Beep(1000, 200)
                winsound.Beep(1200, 200)
                winsound.Beep(1500, 300)
        except:
            pass
    
    def login_to_instagram(self) -> bool:
        """Login completo com código 2FA"""
        try:
            logger.info("Abrindo Instagram...")
            self.driver.get("https://www.instagram.com/")
            time.sleep(5)
            
            # Login básico
            username_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            password_field = self.driver.find_element(By.NAME, "password")
            
            logger.info(f"Inserindo credenciais: {self.email}")
            username_field.send_keys(self.email)
            password_field.send_keys(self.password)
            
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            time.sleep(10)
            return self.check_login_result()
            
        except Exception as e:
            logger.error(f"Erro no login: {e}")
            return False
    
    def check_login_result(self) -> bool:
        """Verifica resultado do login"""
        try:
            url = self.driver.current_url
            logger.info(f"URL atual: {url}")
            
            # Sucesso direto
            if "instagram.com" in url and "accounts/login" not in url and "two_factor" not in url:
                print("LOGIN REALIZADO COM SUCESSO!")
                self.play_success_sound()
                return True
            
            # 2FA necessário
            if "two_factor" in url:
                return self.handle_2fa()
            
            print("Falha no login")
            return False
            
        except Exception as e:
            logger.error(f"Erro na verificação: {e}")
            return False
    
    def handle_2fa(self) -> bool:
        """Processo 2FA com código pré-definido"""
        try:
            logger.info("2FA detectado - usando código fornecido")
            print(f"Inserindo código 2FA: {self.two_fa_code}")
            
            # Encontrar campo de código
            code_field = None
            selectors = [
                (By.NAME, "verificationCode"),
                (By.XPATH, "//input[@aria-label='Security code']"),
                (By.XPATH, "//input[@placeholder='Security code']")
            ]
            
            for by_method, selector in selectors:
                try:
                    code_field = self.wait.until(EC.presence_of_element_located((by_method, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not code_field:
                logger.error("Campo de código 2FA não encontrado")
                return False
            
            # Inserir código
            code_field.clear()
            time.sleep(0.5)
            
            # Inserir dígito por dígito
            for digit in self.two_fa_code:
                code_field.send_keys(digit)
                time.sleep(0.2)
            
            # Enviar
            code_field.send_keys(Keys.RETURN)
            logger.info("Código 2FA enviado")
            
            time.sleep(15)
            
            # Verificar resultado
            url = self.driver.current_url
            
            if "two_factor" not in url and "instagram.com" in url:
                print("2FA ACEITO - LOGIN COMPLETO!")
                print("Você está oficialmente logado no Instagram!")
                self.play_success_sound()
                return True
            else:
                print("Código 2FA rejeitado ou expirado")
                return False
                
        except Exception as e:
            logger.error(f"Erro no 2FA: {e}")
            return False
    
    def run(self) -> bool:
        """Executa o bot"""
        try:
            print("="*60)
            print("INSTAGRAM LOGIN COM CÓDIGO 2FA")
            print("="*60)
            print(f"Email: {self.email}")
            print(f"Código 2FA: {self.two_fa_code}")
            print("="*60)
            
            if not self.setup_driver():
                return False
            
            success = self.login_to_instagram()
            
            if success:
                print("\n" + "="*50)
                print("SUCESSO TOTAL - VOCÊ ESTÁ LOGADO!")
                print("="*50)
                print("Mantendo sessão ativa por 2 minutos...")
                time.sleep(120)
            else:
                print("\nFalha no login")
            
            return success
            
        except Exception as e:
            logger.error(f"Erro: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """Função principal"""
    EMAIL = "eltons.souz@gmail.com"
    PASSWORD = "Mami210912!"
    TWO_FA_CODE = "422024"  # Código fornecido pelo usuário
    
    print("Instagram Bot - Login Automático com 2FA")
    print(f"Usando código: {TWO_FA_CODE}")
    
    bot = InstagramWithCode(EMAIL, PASSWORD, TWO_FA_CODE)
    
    try:
        success = bot.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("Cancelado")
        sys.exit(130)

if __name__ == "__main__":
    main()