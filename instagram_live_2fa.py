#!/usr/bin/env python3
"""
Instagram Bot - Login Interativo com 2FA em Tempo Real
Você pode digitar o código 2FA quando solicitado
"""

import time
import os
import sys
import logging
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog
import re
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
        logging.FileHandler('instagram_live_2fa.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class InstagramLive2FA:
    """Instagram bot com entrada interativa de 2FA"""
    
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
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
            
            logger.info("Chrome configurado - navegador visível")
            return True
            
        except Exception as e:
            logger.error(f"Erro no WebDriver: {e}")
            return False
    
    def play_alert(self):
        """Som de alerta"""
        try:
            if SOUND_AVAILABLE:
                winsound.Beep(1000, 500)
        except:
            pass
    
    def show_popup_alert(self):
        """Popup de alerta"""
        try:
            def popup():
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                messagebox.showwarning("Instagram 2FA", 
                    "CÓDIGO 2FA NECESSÁRIO!\n\nVerifique seu telefone ou app autenticador.")
                root.destroy()
            threading.Thread(target=popup, daemon=True).start()
        except:
            pass
    
    def get_2fa_code(self) -> str:
        """Solicita código 2FA do usuário"""
        print("\n" + "="*60)
        print("AUTENTICAÇÃO DE DUAS ETAPAS NECESSÁRIA")
        print("="*60)
        print("O Instagram enviou um código de verificação!")
        print("Verifique:")
        print("• SMS no seu telefone")
        print("• App autenticador (Google Authenticator, Authy, etc.)")
        print("• Email de backup")
        print("="*60)
        
        # Notificações
        self.play_alert()
        self.show_popup_alert()
        
        # Solicitar código
        attempts = 0
        max_attempts = 3
        
        while attempts < max_attempts:
            print(f"\nTentativa {attempts + 1}/{max_attempts}")
            print("Formatos aceitos: 123456, 123-456, 123 456")
            
            try:
                if attempts == 0:
                    print("Digite o código OU pressione ENTER para interface gráfica:")
                
                code = input("Código 2FA: ").strip()
                
                # Interface gráfica
                if not code and attempts == 0:
                    code = self.get_code_gui()
                    if code:
                        print(f"Código recebido: {code}")
                
                if not code:
                    print("Nenhum código fornecido!")
                    attempts += 1
                    continue
                
                # Validar
                clean_code = re.sub(r'[^\d]', '', code)
                
                if len(clean_code) != 6:
                    print(f"Código deve ter 6 dígitos (você digitou {len(clean_code)})")
                    attempts += 1
                    continue
                
                if clean_code in ["000000", "123456"] or len(set(clean_code)) == 1:
                    print("Código inválido - digite o código real")
                    attempts += 1
                    continue
                
                # Confirmar
                print(f"Código: {clean_code[:3]}-{clean_code[3:]}")
                confirm = input("Confirma? (ENTER=sim): ").strip()
                if not confirm or confirm.lower().startswith(('s', 'y')):
                    return clean_code
                
            except (EOFError, KeyboardInterrupt):
                print("\nCancelado pelo usuário")
                return None
            
            attempts += 1
        
        print("Máximo de tentativas atingido")
        return None
    
    def get_code_gui(self) -> str:
        """Interface gráfica para código"""
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            code = simpledialog.askstring(
                "Instagram 2FA",
                "Digite o código de 6 dígitos:",
                parent=root
            )
            
            root.destroy()
            return code.strip() if code else ""
        except:
            return ""
    
    def login_to_instagram(self) -> bool:
        """Login completo"""
        try:
            logger.info("Abrindo Instagram...")
            self.driver.get("https://www.instagram.com/")
            time.sleep(5)
            
            # Login básico
            username_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            password_field = self.driver.find_element(By.NAME, "password")
            
            logger.info(f"Inserindo: {self.email}")
            username_field.send_keys(self.email)
            password_field.send_keys(self.password)
            
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            time.sleep(10)
            return self.check_result()
            
        except Exception as e:
            logger.error(f"Erro no login: {e}")
            return False
    
    def check_result(self) -> bool:
        """Verifica resultado do login"""
        try:
            url = self.driver.current_url
            logger.info(f"URL: {url}")
            
            # Sucesso direto
            if "instagram.com" in url and "accounts/login" not in url and "two_factor" not in url:
                print("\nLOGIN REALIZADO COM SUCESSO!")
                return True
            
            # 2FA necessário
            if "two_factor" in url:
                return self.handle_2fa()
            
            # Erro
            print("Falha no login")
            return False
            
        except Exception as e:
            logger.error(f"Erro na verificação: {e}")
            return False
    
    def handle_2fa(self) -> bool:
        """Processo 2FA"""
        try:
            logger.info("2FA detectado")
            
            # Solicitar código
            code = self.get_2fa_code()
            if not code:
                return False
            
            # Inserir código
            try:
                code_field = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "verificationCode"))
                )
            except:
                code_field = self.driver.find_element(By.XPATH, "//input[@aria-label='Security code']")
            
            print("Inserindo código...")
            code_field.clear()
            for digit in code:
                code_field.send_keys(digit)
                time.sleep(0.1)
            
            code_field.send_keys(Keys.RETURN)
            print("Código enviado!")
            
            time.sleep(10)
            
            # Verificar resultado
            url = self.driver.current_url
            if "two_factor" not in url:
                print("\n2FA ACEITO - LOGIN COMPLETO!")
                if SOUND_AVAILABLE:
                    try:
                        winsound.Beep(1000, 200)
                        winsound.Beep(1500, 300)
                    except:
                        pass
                return True
            else:
                print("Código rejeitado")
                retry = input("Tentar novamente? (s/n): ").strip().lower()
                if retry.startswith('s'):
                    return self.handle_2fa()
                return False
                
        except Exception as e:
            logger.error(f"Erro no 2FA: {e}")
            return False
    
    def run(self) -> bool:
        """Executa bot"""
        try:
            print("\n" + "="*60)
            print("INSTAGRAM LOGIN INTERATIVO COM 2FA")
            print("="*60)
            print(f"Email: {self.email}")
            print("Recursos:")
            print("• Navegador visível")
            print("• Entrada interativa de código 2FA")
            print("• Interface gráfica opcional")
            print("• Notificações sonoras")
            print("• Múltiplas tentativas")
            print("="*60)
            
            if not self.setup_driver():
                return False
            
            success = self.login_to_instagram()
            
            if success:
                print("\n" + "="*40)
                print("SUCESSO! VOCÊ ESTÁ LOGADO!")
                print("="*40)
                print("Mantendo sessão por 2 minutos...")
                time.sleep(120)
            
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
    
    print("Instagram Bot - Login Interativo com 2FA")
    print("Você pode inserir o código quando solicitado")
    print("Pressione Ctrl+C para cancelar")
    
    bot = InstagramLive2FA(EMAIL, PASSWORD)
    
    try:
        success = bot.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nCancelado pelo usuário")
        sys.exit(130)

if __name__ == "__main__":
    main()