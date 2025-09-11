#!/usr/bin/env python3
"""
Instagram Login Test com Email - Versão Atualizada
Teste com email: eltons.souz@gmail.com
"""

import time
import os
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_instagram_email_login.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class InstagramEmailTestBot:
    """Bot de teste para Instagram usando email"""
    
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.driver = None
        self.wait = None
        
    def setup_driver(self) -> bool:
        """Setup Chrome WebDriver com gerenciamento automático"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Tentar usar webdriver-manager primeiro
            if WEBDRIVER_MANAGER_AVAILABLE:
                try:
                    logger.info("Usando webdriver-manager para ChromeDriver...")
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                except Exception as e:
                    logger.warning(f"webdriver-manager falhou: {e}")
                    logger.info("Tentando método manual...")
                    self.driver = webdriver.Chrome(options=chrome_options)
            else:
                logger.info("webdriver-manager não disponível, usando método manual...")
                self.driver = webdriver.Chrome(options=chrome_options)
            
            # Anti-detecção
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            
            self.wait = WebDriverWait(self.driver, 20)
            
            logger.info("Chrome WebDriver configurado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Falha ao configurar WebDriver: {e}")
            return False
    
    def login_to_instagram(self) -> bool:
        """Realizar login no Instagram com email"""
        try:
            logger.info("Abrindo Instagram...")
            self.driver.get("https://www.instagram.com/")
            time.sleep(5)
            
            # Aguardar formulário de login
            try:
                username_field = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "username"))
                )
                logger.info("Campo de usuário/email encontrado")
            except TimeoutException:
                logger.error("Timeout: Campo de usuário/email não encontrado")
                return False
            
            # Encontrar campo de senha
            try:
                password_field = self.driver.find_element(By.NAME, "password")
                logger.info("Campo de senha encontrado")
            except NoSuchElementException:
                logger.error("Campo de senha não encontrado")
                return False
            
            # Limpar e inserir credenciais
            logger.info(f"Inserindo email: {self.email}")
            username_field.clear()
            time.sleep(1)
            username_field.send_keys(self.email)
            
            logger.info("Inserindo senha...")
            password_field.clear()
            time.sleep(1)
            password_field.send_keys(self.password)
            
            # Encontrar e clicar no botão de login
            try:
                login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                logger.info("Botão de login encontrado, clicando...")
                login_button.click()
            except NoSuchElementException:
                # Tentar encontrar por texto
                login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Log in') or contains(text(), 'Entrar')]")
                login_button.click()
            
            logger.info("Credenciais enviadas, aguardando resposta...")
            time.sleep(10)
            
            return self.check_login_result()
            
        except Exception as e:
            logger.error(f"Erro durante login: {e}")
            return False
    
    def check_login_result(self) -> bool:
        """Verificar resultado do login"""
        try:
            current_url = self.driver.current_url
            logger.info(f"URL atual: {current_url}")
            
            # Verificar se login foi bem-sucedido
            if "instagram.com" in current_url and "accounts/login" not in current_url:
                logger.info("Login realizado com sucesso!")
                
                # Verificar se chegou na página inicial
                if "instagram.com/" == current_url or "instagram.com" in current_url:
                    logger.info("Redirecionado para página principal")
                return True
            
            # Verificar se 2FA é necessário
            if self.check_for_2fa():
                logger.warning("2FA detectado - código de verificação necessário")
                logger.info("Aguardando inserção manual do código 2FA...")
                
                # Aguardar 2 minutos para inserção manual
                time.sleep(120)
                
                # Verificar novamente após 2FA
                current_url = self.driver.current_url
                if "instagram.com" in current_url and "accounts/login" not in current_url:
                    logger.info("Login com 2FA realizado com sucesso!")
                    return True
                else:
                    logger.error("2FA falhou ou expirou")
                    return False
            
            # Verificar erros de credenciais
            if self.check_for_credential_error():
                logger.error("Credenciais incorretas detectadas")
                return False
            
            # Verificar se conta foi bloqueada/suspensa
            if self.check_for_account_issues():
                logger.error("Problema com a conta detectado")
                return False
            
            logger.warning("Status de login indeterminado")
            return False
            
        except Exception as e:
            logger.error(f"Erro ao verificar resultado do login: {e}")
            return False
    
    def check_for_2fa(self) -> bool:
        """Verificar se 2FA é necessário"""
        try:
            two_factor_selectors = [
                "//input[@name='verificationCode']",
                "//input[@aria-label='Security code']",
                "//input[@placeholder='Security code']",
                "//*[contains(text(), 'Enter the 6-digit code')]",
                "//*[contains(text(), 'We sent you a code')]",
                "//*[contains(text(), 'Two-factor authentication')]"
            ]
            
            for selector in two_factor_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element.is_displayed():
                        return True
                except NoSuchElementException:
                    continue
            
            return False
        except Exception:
            return False
    
    def check_for_credential_error(self) -> bool:
        """Verificar erro de credenciais"""
        try:
            error_selectors = [
                "//*[contains(text(), 'Sorry, your password was incorrect')]",
                "//*[contains(text(), 'incorrect')]",
                "//*[contains(text(), 'senha estava incorreta')]",
                "//*[contains(text(), 'The username you entered')]",
                "//*[contains(text(), 'user does not exist')]",
                "//*[contains(text(), 'Please check your username')]",
                "//div[@role='alert']"
            ]
            
            for selector in error_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element.is_displayed():
                        logger.error(f"Erro detectado: {element.text}")
                        return True
                except NoSuchElementException:
                    continue
            
            return False
        except Exception:
            return False
    
    def check_for_account_issues(self) -> bool:
        """Verificar problemas com a conta"""
        try:
            issue_selectors = [
                "//*[contains(text(), 'account has been disabled')]",
                "//*[contains(text(), 'temporarily locked')]",
                "//*[contains(text(), 'suspended')]",
                "//*[contains(text(), 'We restrict certain activity')]",
                "//*[contains(text(), 'unusual activity')]"
            ]
            
            for selector in issue_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element.is_displayed():
                        logger.error(f"Problema com conta: {element.text}")
                        return True
                except NoSuchElementException:
                    continue
            
            return False
        except Exception:
            return False
    
    def run_test(self) -> bool:
        """Executar teste completo"""
        try:
            logger.info("=== TESTE DE LOGIN INSTAGRAM COM EMAIL ===")
            logger.info(f"Email: {self.email}")
            
            # Setup do driver
            if not self.setup_driver():
                logger.error("Falha ao configurar WebDriver")
                return False
            
            # Realizar login
            success = self.login_to_instagram()
            
            if success:
                logger.info("TESTE CONCLUÍDO COM SUCESSO!")
                logger.info("Mantendo browser aberto por 30 segundos para inspeção...")
                time.sleep(30)
            else:
                logger.error("TESTE FALHOU")
            
            return success
            
        except Exception as e:
            logger.error(f"Erro durante execução do teste: {e}")
            return False
        
        finally:
            # Cleanup
            logger.info("Fechando browser...")
            if self.driver:
                self.driver.quit()

def main():
    """Função principal de teste"""
    # Credenciais fornecidas pelo usuário
    EMAIL = "eltons.souz@gmail.com"
    PASSWORD = "Mami210912!"
    
    logger.info("Instagram Email Login Test Bot")
    logger.info("Pressione Ctrl+C para interromper a qualquer momento")
    
    bot = InstagramEmailTestBot(EMAIL, PASSWORD)
    
    try:
        success = bot.run_test()
        
        if success:
            logger.info("Teste completado com sucesso!")
            sys.exit(0)
        else:
            logger.error("Teste falhou!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Teste interrompido pelo usuário")
        if bot.driver:
            bot.driver.quit()
        sys.exit(130)
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()