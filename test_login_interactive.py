#!/usr/bin/env python3
"""
Instagram Login Interativo - Versão com Modo Normal e 2FA Interativo
Abertura em modo normal + solicitação interativa de código 2FA
"""

import time
import os
import sys
import logging
import threading
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
        logging.FileHandler('test_instagram_interactive.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class InstagramInteractiveBot:
    """Bot interativo do Instagram com modo normal e 2FA"""
    
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.driver = None
        self.wait = None
        self.two_factor_code = None
        self.code_event = threading.Event()
        
    def setup_driver(self) -> bool:
        """Setup Chrome WebDriver em modo normal (visível)"""
        try:
            chrome_options = Options()
            
            # MODO NORMAL - Browser visível
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Configurações para melhor experiência visual
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            
            # Tentar usar webdriver-manager primeiro
            if WEBDRIVER_MANAGER_AVAILABLE:
                try:
                    logger.info("🔧 Configurando ChromeDriver automaticamente...")
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                except Exception as e:
                    logger.warning(f"webdriver-manager falhou: {e}")
                    logger.info("Tentando método manual...")
                    self.driver = webdriver.Chrome(options=chrome_options)
            else:
                logger.info("Usando ChromeDriver manual...")
                self.driver = webdriver.Chrome(options=chrome_options)
            
            # Anti-detecção básica
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.wait = WebDriverWait(self.driver, 20)
            
            logger.info("Chrome aberto em MODO NORMAL (visível)")
            logger.info("Você pode ver o navegador funcionando!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Falha ao configurar WebDriver: {e}")
            return False
    
    def open_new_tab_if_needed(self):
        """Abre nova aba se o navegador já estiver em uso"""
        try:
            # Verificar se existem outras abas abertas
            if len(self.driver.window_handles) > 1:
                logger.info("🔄 Detectadas múltiplas abas, abrindo nova aba...")
                self.driver.execute_script("window.open('');")
                self.driver.switch_to.window(self.driver.window_handles[-1])
            else:
                logger.info("📱 Usando aba atual")
        except Exception as e:
            logger.warning(f"Erro ao gerenciar abas: {e}")
    
    def login_to_instagram(self) -> bool:
        """Realizar login no Instagram com interface interativa"""
        try:
            self.open_new_tab_if_needed()
            
            logger.info("🌍 Abrindo Instagram...")
            self.driver.get("https://www.instagram.com/")
            time.sleep(5)
            
            # Aguardar formulário de login
            try:
                username_field = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "username"))
                )
                logger.info("✅ Campo de usuário/email encontrado")
            except TimeoutException:
                logger.error("❌ Timeout: Campo de usuário/email não encontrado")
                return False
            
            # Encontrar campo de senha
            try:
                password_field = self.driver.find_element(By.NAME, "password")
                logger.info("✅ Campo de senha encontrado")
            except NoSuchElementException:
                logger.error("❌ Campo de senha não encontrado")
                return False
            
            # Inserir credenciais com feedback visual
            logger.info(f"📧 Inserindo email: {self.email}")
            username_field.clear()
            time.sleep(1)
            
            # Digitação mais natural
            for char in self.email:
                username_field.send_keys(char)
                time.sleep(0.05)
            
            logger.info("🔒 Inserindo senha...")
            password_field.clear()
            time.sleep(1)
            
            for char in self.password:
                password_field.send_keys(char)
                time.sleep(0.05)
            
            # Encontrar e clicar no botão de login
            try:
                login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                logger.info("🎯 Clicando no botão de login...")
                
                # Scroll para garantir que o botão está visível
                self.driver.execute_script("arguments[0].scrollIntoView();", login_button)
                time.sleep(1)
                
                login_button.click()
            except NoSuchElementException:
                # Tentar encontrar por texto
                login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Log in') or contains(text(), 'Entrar')]")
                login_button.click()
            
            logger.info("📤 Credenciais enviadas, aguardando resposta do Instagram...")
            time.sleep(10)
            
            return self.check_login_result()
            
        except Exception as e:
            logger.error(f"❌ Erro durante login: {e}")
            return False
    
    def request_2fa_code_interactive(self) -> str:
        """Solicita código 2FA do usuário de forma interativa"""
        print("\n" + "="*60)
        print("🔐 AUTENTICAÇÃO DE DOIS FATORES (2FA) NECESSÁRIA")
        print("="*60)
        print("📱 O Instagram enviou um código de verificação para:")
        print("   • Seu telefone (SMS)")
        print("   • Seu app autenticador (Google Authenticator, etc.)")
        print("   • Seu email cadastrado")
        print("\n🔍 Verifique suas notificações e insira o código de 6 dígitos:")
        print("-"*60)
        
        def get_code_input():
            """Thread para capturar input do usuário"""
            try:
                while True:
                    code = input("Digite o código 2FA (6 dígitos): ").strip()
                    if len(code) == 6 and code.isdigit():
                        self.two_factor_code = code
                        self.code_event.set()
                        print(f"✅ Código {code} recebido! Enviando para Instagram...")
                        break
                    else:
                        print("❌ Código inválido! Deve ter exatamente 6 dígitos numéricos.")
            except Exception as e:
                logger.error(f"Erro na captura do código: {e}")
                self.code_event.set()
        
        # Iniciar thread para captura do código
        input_thread = threading.Thread(target=get_code_input, daemon=True)
        input_thread.start()
        
        # Aguardar código por 2 minutos
        logger.info("⏳ Aguardando código 2FA... (tempo limite: 2 minutos)")
        code_received = self.code_event.wait(timeout=120)
        
        if code_received and self.two_factor_code:
            return self.two_factor_code
        else:
            print("\n⏰ Tempo limite atingido! (2 minutos)")
            logger.warning("Timeout: Código 2FA não fornecido dentro do tempo limite")
            return None
    
    def handle_2fa_interactive(self) -> bool:
        """Gerencia 2FA de forma interativa"""
        try:
            logger.info("🔐 2FA detectado - iniciando processo interativo...")
            
            # Solicitar código ao usuário
            verification_code = self.request_2fa_code_interactive()
            
            if not verification_code:
                logger.error("❌ Código 2FA não fornecido")
                return False
            
            # Encontrar campo de código 2FA
            try:
                code_field = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "verificationCode"))
                )
                logger.info("✅ Campo de código 2FA encontrado")
            except TimeoutException:
                # Tentar outros seletores
                try:
                    code_field = self.driver.find_element(By.XPATH, "//input[@aria-label='Security code']")
                except NoSuchElementException:
                    logger.error("❌ Campo de código 2FA não encontrado")
                    return False
            
            # Inserir código com feedback visual
            logger.info(f"📝 Inserindo código 2FA: {verification_code}")
            code_field.clear()
            time.sleep(1)
            
            # Digitação natural do código
            for digit in verification_code:
                code_field.send_keys(digit)
                time.sleep(0.2)
            
            # Submeter código
            code_field.send_keys(Keys.RETURN)
            logger.info("📤 Código 2FA enviado!")
            
            # Aguardar processamento
            time.sleep(10)
            
            # Verificar se 2FA foi aceito
            current_url = self.driver.current_url
            if "two_factor" not in current_url and "instagram.com" in current_url:
                logger.info("🎉 2FA aceito com sucesso!")
                return True
            else:
                logger.error("❌ Código 2FA rejeitado ou erro no processo")
                return False
            
        except Exception as e:
            logger.error(f"❌ Erro durante 2FA: {e}")
            return False
    
    def check_login_result(self) -> bool:
        """Verificar resultado do login com detecção aprimorada"""
        try:
            current_url = self.driver.current_url
            logger.info(f"🌐 URL atual: {current_url}")
            
            # Verificar se login foi bem-sucedido diretamente
            if "instagram.com" in current_url and "accounts/login" not in current_url and "two_factor" not in current_url:
                logger.info("🎉 Login realizado com sucesso!")
                return True
            
            # Verificar se 2FA é necessário
            if "two_factor" in current_url or self.check_for_2fa_elements():
                logger.info("🔐 2FA necessário - iniciando processo interativo...")
                return self.handle_2fa_interactive()
            
            # Verificar erros de credenciais
            if self.check_for_credential_error():
                logger.error("❌ Credenciais incorretas detectadas")
                return False
            
            # Verificar problemas com conta
            if self.check_for_account_issues():
                logger.error("❌ Problema com a conta detectado")
                return False
            
            logger.warning("⚠️ Status de login indeterminado")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar resultado do login: {e}")
            return False
    
    def check_for_2fa_elements(self) -> bool:
        """Verificar elementos 2FA na página"""
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
        """Executar teste completo interativo"""
        try:
            print("\n" + "="*70)
            print("🤖 INSTAGRAM LOGIN BOT - MODO INTERATIVO")
            print("="*70)
            print(f"📧 Email: {self.email}")
            print("🔍 Modo: Navegador Visível (Normal)")
            print("🔐 2FA: Solicitação Interativa")
            print("="*70)
            
            # Setup do driver
            if not self.setup_driver():
                logger.error("❌ Falha ao configurar WebDriver")
                return False
            
            # Realizar login
            success = self.login_to_instagram()
            
            if success:
                print("\n" + "🎉"*20)
                print("✅ LOGIN REALIZADO COM SUCESSO!")
                print("🎉"*20)
                print("🌐 Você está logado no Instagram!")
                print("🔍 Verifique o navegador para confirmar")
                print("⏳ Mantendo sessão aberta por 60 segundos...")
                time.sleep(60)
            else:
                print("\n" + "❌"*20)
                print("❌ FALHA NO LOGIN")
                print("❌"*20)
                print("🔍 Verifique as credenciais e tente novamente")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erro durante execução do teste: {e}")
            return False
        
        finally:
            # Cleanup com confirmação
            print("\n🔄 Finalizando sessão...")
            if self.driver:
                try:
                    print("🗂️ Fechando navegador...")
                    self.driver.quit()
                    print("✅ Navegador fechado com sucesso")
                except Exception as e:
                    print(f"⚠️ Erro ao fechar navegador: {e}")

def main():
    """Função principal interativa"""
    # Credenciais do usuário
    EMAIL = "eltons.souz@gmail.com"
    PASSWORD = "Mami210912!"
    
    print("🤖 Instagram Login Bot - Versão Interativa")
    print("⚠️ Pressione Ctrl+C para interromper a qualquer momento")
    print("🌐 O navegador abrirá em modo NORMAL (visível)")
    
    bot = InstagramInteractiveBot(EMAIL, PASSWORD)
    
    try:
        success = bot.run_test()
        
        if success:
            print("\n🎊 Teste completado com sucesso!")
            sys.exit(0)
        else:
            print("\n💥 Teste falhou!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Teste interrompido pelo usuário")
        if bot.driver:
            bot.driver.quit()
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()