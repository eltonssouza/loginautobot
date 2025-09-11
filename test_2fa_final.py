#!/usr/bin/env python3
"""
Instagram Bot - Sistema Completo de 2FA (Versão Final)
Teste funcional com 6 métodos de notificação
"""

import time
import os
import sys
import logging
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog
import subprocess
import platform
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
        logging.FileHandler('test_2fa_final.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CodeValidator:
    """Sistema de validação de códigos 2FA"""
    
    @staticmethod
    def validate_2fa_code(code: str):
        """Valida código 2FA"""
        if not code:
            return False, "Código não pode estar vazio"
        
        # Remover espaços e caracteres especiais
        cleaned_code = re.sub(r'[^\d]', '', code)
        
        # Verificar se tem exatamente 6 dígitos
        if len(cleaned_code) != 6:
            return False, f"Código deve ter 6 dígitos (você digitou {len(cleaned_code)})"
        
        # Verificar se são todos números
        if not cleaned_code.isdigit():
            return False, "Código deve conter apenas números"
        
        # Verificar padrões suspeitos
        if cleaned_code == "000000":
            return False, "Código não pode ser 000000"
        
        if cleaned_code == "123456":
            return False, "Código 123456 parece ser um exemplo, digite o código real"
        
        # Verificar sequências
        if len(set(cleaned_code)) == 1:
            return False, f"Código não pode ser uma sequência repetida ({cleaned_code[0]*6})"
        
        return True, cleaned_code

class TwoFactorNotifier:
    """Sistema de notificações para 2FA"""
    
    @staticmethod
    def play_alert_sound():
        """Som de alerta"""
        try:
            if SOUND_AVAILABLE and platform.system() == "Windows":
                frequencies = [800, 1000, 1200]
                for freq in frequencies:
                    winsound.Beep(freq, 300)
                    time.sleep(0.1)
        except Exception as e:
            logger.warning(f"Erro no som: {e}")
    
    @staticmethod
    def show_popup_notification(message: str, title: str = "Instagram 2FA"):
        """Popup de notificação"""
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            messagebox.showwarning(title, message)
            root.destroy()
        except Exception as e:
            logger.warning(f"Erro no popup: {e}")
    
    @staticmethod
    def show_system_notification(message: str, title: str = "Instagram 2FA"):
        """Notificação do sistema"""
        try:
            if platform.system() == "Windows":
                subprocess.run([
                    "powershell", "-Command",
                    f'Add-Type -AssemblyName System.Windows.Forms; '
                    f'[System.Windows.Forms.MessageBox]::Show("{message}", "{title}")'
                ], capture_output=True)
        except Exception as e:
            logger.warning(f"Erro na notificação: {e}")

class InstagramBot2FA:
    """Instagram bot com sistema completo de 2FA"""
    
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.driver = None
        self.wait = None
        self.notifier = TwoFactorNotifier()
        self.validator = CodeValidator()
        
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
            logger.error(f"Erro ao configurar WebDriver: {e}")
            return False
    
    def notify_all_methods(self):
        """Sistema completo de notificação - 5 métodos"""
        logger.info("=== INICIANDO NOTIFICAÇÕES 2FA ===")
        
        # 1. Som de alerta
        threading.Thread(target=self.notifier.play_alert_sound, daemon=True).start()
        
        # 2. Popup
        threading.Thread(
            target=self.notifier.show_popup_notification,
            args=("CÓDIGO 2FA NECESSÁRIO!\n\nVerifique:\n• Seu telefone (SMS)\n• App autenticador\n• Email backup\n\nVocê tem 2 minutos!",),
            daemon=True
        ).start()
        
        # 3. Notificação do sistema
        threading.Thread(
            target=self.notifier.show_system_notification,
            args=("Código 2FA necessário! Verifique seu telefone.",),
            daemon=True
        ).start()
        
        # 4. Flash no console
        for i in range(3):
            print("\n" + "="*60)
            print(">>> CÓDIGO 2FA NECESSÁRIO AGORA! <<<".center(60))
            print("="*60)
            time.sleep(0.5)
        
        # 5. Console informativo
        print("\nAUTENTICAÇÃO DE DUAS ETAPAS NECESSÁRIA")
        print("="*50)
        print("O Instagram enviou um código para:")
        print("• Seu telefone (SMS)")
        print("• App autenticador (Google Authenticator, etc.)")
        print("• Email backup")
        print("\nNOTIFICAÇÕES ENVIADAS:")
        print("✓ Som de alerta")
        print("✓ Popup de notificação")
        print("✓ Notificação do sistema")
        print("✓ Flash no console")
        print("\nTEMPO LIMITE: 2 minutos")
        print("="*50)
    
    def request_2fa_code_advanced(self) -> str:
        """6. Solicitação avançada de código com validação"""
        print("\nSOLICITAÇÃO DE CÓDIGO 2FA - SISTEMA AVANÇADO")
        print("="*55)
        
        code_received = threading.Event()
        final_code = [None]
        
        def console_input():
            """Handler de entrada via console"""
            try:
                attempts = 0
                max_attempts = 5
                
                while attempts < max_attempts and not code_received.is_set():
                    print(f"\nTENTATIVA {attempts + 1}/{max_attempts}")
                    print("-" * 30)
                    print("FORMATOS ACEITOS:")
                    print("• 123456")
                    print("• 123-456")
                    print("• 123 456")
                    print("-" * 30)
                    
                    try:
                        # Opção GUI no primeiro attempt
                        if attempts == 0:
                            print("Pressione ENTER para interface gráfica ou digite o código:")
                        
                        user_input = input("Código 2FA: ").strip()
                        
                        # GUI se ENTER vazio
                        if not user_input and attempts == 0:
                            print("Abrindo interface gráfica...")
                            try:
                                root = tk.Tk()
                                root.withdraw()
                                root.attributes('-topmost', True)
                                gui_code = simpledialog.askstring(
                                    "Instagram 2FA",
                                    "Digite o código de 6 dígitos:",
                                    parent=root
                                )
                                root.destroy()
                                if gui_code:
                                    user_input = gui_code
                                    print(f"Código recebido via GUI: {gui_code}")
                            except Exception:
                                print("Erro na interface gráfica, use o console")
                        
                        if not user_input:
                            print("Nenhum código fornecido!")
                            attempts += 1
                            continue
                        
                        # Validar código
                        is_valid, result = self.validator.validate_2fa_code(user_input)
                        
                        if is_valid:
                            final_code[0] = result
                            print(f"Código válido: {result}")
                            print("Enviando para Instagram...")
                            
                            # Som de confirmação
                            if SOUND_AVAILABLE and platform.system() == "Windows":
                                winsound.Beep(1000, 200)
                            
                            code_received.set()
                            break
                        else:
                            print(f"ERRO: {result}")
                            attempts += 1
                            
                            if attempts < max_attempts:
                                print(f"Tente novamente ({max_attempts - attempts} restantes)")
                    
                    except (EOFError, KeyboardInterrupt):
                        break
                
                if attempts >= max_attempts:
                    print("Máximo de tentativas atingido!")
                
                code_received.set()
                
            except Exception as e:
                logger.error(f"Erro no input: {e}")
                code_received.set()
        
        def countdown():
            """Countdown visual"""
            for remaining in range(120, 0, -1):
                if code_received.is_set():
                    break
                
                mins, secs = divmod(remaining, 60)
                print(f"\rTempo restante: {mins:02d}:{secs:02d} ", end="", flush=True)
                time.sleep(1)
            
            if not code_received.is_set():
                print("\n\nTEMPO ESGOTADO!")
                code_received.set()
        
        # Iniciar threads
        input_thread = threading.Thread(target=console_input, daemon=True)
        countdown_thread = threading.Thread(target=countdown, daemon=True)
        
        input_thread.start()
        countdown_thread.start()
        
        # Aguardar resultado
        code_received.wait(timeout=125)
        print("\n")
        
        return final_code[0]
    
    def login_to_instagram(self) -> bool:
        """Login com sistema completo de 2FA"""
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
    
    def handle_2fa_process(self) -> bool:
        """Processo completo de 2FA"""
        try:
            logger.info("2FA detectado - iniciando sistema completo")
            
            # Métodos 1-5: Notificar
            self.notify_all_methods()
            
            # Método 6: Solicitar código
            verification_code = self.request_2fa_code_advanced()
            
            if not verification_code:
                logger.error("Código 2FA não fornecido")
                return False
            
            # Inserir no Instagram
            try:
                code_field = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "verificationCode"))
                )
            except TimeoutException:
                code_field = self.driver.find_element(By.XPATH, "//input[@aria-label='Security code']")
            
            logger.info(f"Inserindo código: {verification_code}")
            code_field.clear()
            code_field.send_keys(verification_code)
            code_field.send_keys(Keys.RETURN)
            
            time.sleep(10)
            
            # Verificar resultado
            current_url = self.driver.current_url
            if "two_factor" not in current_url and "instagram.com" in current_url:
                print("\n" + "="*50)
                print("2FA ACEITO COM SUCESSO!")
                print("="*50)
                return True
            else:
                print("Código 2FA rejeitado!")
                return False
                
        except Exception as e:
            logger.error(f"Erro no 2FA: {e}")
            return False
    
    def check_login_result(self) -> bool:
        """Verificar resultado do login"""
        try:
            current_url = self.driver.current_url
            logger.info(f"URL atual: {current_url}")
            
            # Sucesso direto
            if "instagram.com" in current_url and "accounts/login" not in current_url and "two_factor" not in current_url:
                logger.info("Login realizado com sucesso!")
                return True
            
            # 2FA necessário
            if "two_factor" in current_url:
                return self.handle_2fa_process()
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao verificar login: {e}")
            return False
    
    def run(self) -> bool:
        """Executar bot completo"""
        try:
            print("\n" + "="*70)
            print("INSTAGRAM BOT - SISTEMA COMPLETO DE 2FA")
            print("="*70)
            print(f"Email: {self.email}")
            print("Recursos:")
            print("1. Som de alerta")
            print("2. Flash no console") 
            print("3. Popup de notificação")
            print("4. Notificação do sistema")
            print("5. Countdown visual")
            print("6. Solicitação avançada com validação")
            print("="*70)
            
            if not self.setup_driver():
                return False
            
            success = self.login_to_instagram()
            
            if success:
                print("\n" + "="*40)
                print("LOGIN REALIZADO COM SUCESSO!")
                print("="*40)
                print("Mantendo sessão por 60 segundos...")
                time.sleep(60)
            
            return success
            
        except Exception as e:
            logger.error(f"Erro na execução: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """Função principal"""
    EMAIL = "eltons.souz@gmail.com"
    PASSWORD = "Mami210912!"
    
    print("Instagram Bot - Sistema Completo de 2FA")
    print("6 Métodos de Notificação + Validação Avançada")
    print("Pressione Ctrl+C para cancelar")
    
    bot = InstagramBot2FA(EMAIL, PASSWORD)
    
    try:
        success = bot.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário")
        sys.exit(130)

if __name__ == "__main__":
    main()