#!/usr/bin/env python3
"""
Instagram Bot com Sistema Avançado de Notificação 2FA
Múltiplas formas de avisar o usuário sobre autenticação de duas etapas
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
    import winsound  # Para notificações sonoras no Windows
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('instagram_2fa_notifier.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TwoFactorNotifier:
    """Sistema avançado de notificações para 2FA"""
    
    @staticmethod
    def play_alert_sound():
        """Toca som de alerta para chamar atenção"""
        try:
            if SOUND_AVAILABLE and platform.system() == "Windows":
                # Som de alerta do Windows
                winsound.Beep(1000, 500)  # 1000Hz por 500ms
                time.sleep(0.3)
                winsound.Beep(1500, 500)  # 1500Hz por 500ms
                time.sleep(0.3)
                winsound.Beep(2000, 800)  # 2000Hz por 800ms
            elif platform.system() == "Darwin":  # macOS
                os.system("afplay /System/Library/Sounds/Glass.aiff")
            elif platform.system() == "Linux":
                os.system("pactl load-module module-sine frequency=1000 &")
                time.sleep(0.5)
                os.system("pactl unload-module module-sine")
        except Exception as e:
            logger.warning(f"Não foi possível tocar som de alerta: {e}")
    
    @staticmethod
    def show_popup_notification(message: str, title: str = "Instagram 2FA"):
        """Mostra popup de notificação"""
        try:
            root = tk.Tk()
            root.withdraw()  # Esconde janela principal
            root.attributes('-topmost', True)  # Sempre no topo
            
            messagebox.showwarning(title, message)
            root.destroy()
        except Exception as e:
            logger.warning(f"Erro ao mostrar popup: {e}")
    
    @staticmethod
    def show_system_notification(message: str, title: str = "Instagram 2FA"):
        """Mostra notificação do sistema operacional"""
        try:
            if platform.system() == "Windows":
                subprocess.run([
                    "powershell", "-Command",
                    f'Add-Type -AssemblyName System.Windows.Forms; '
                    f'$notify = New-Object System.Windows.Forms.NotifyIcon; '
                    f'$notify.Icon = [System.Drawing.SystemIcons]::Information; '
                    f'$notify.BalloonTipTitle = "{title}"; '
                    f'$notify.BalloonTipText = "{message}"; '
                    f'$notify.Visible = $true; '
                    f'$notify.ShowBalloonTip(5000)'
                ], capture_output=True)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run([
                    "osascript", "-e",
                    f'display notification "{message}" with title "{title}"'
                ])
            elif platform.system() == "Linux":
                subprocess.run(["notify-send", title, message])
        except Exception as e:
            logger.warning(f"Erro ao mostrar notificação do sistema: {e}")
    
    @staticmethod
    def flash_console():
        """Pisca o console para chamar atenção"""
        try:
            for i in range(5):
                print("\n" + "="*80)
                print(">>> ATENÇÃO: CÓDIGO 2FA NECESSÁRIO! <<<".center(80))
                print("="*80 + "\n")
                time.sleep(0.5)
                # Limpar as linhas (funciona em alguns terminais)
                if platform.system() != "Windows":
                    print("\033[2J\033[H", end="")
        except Exception as e:
            logger.warning(f"Erro ao piscar console: {e}")

class InstagramAdvanced2FA:
    """Instagram bot com sistema avançado de notificação 2FA"""
    
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.driver = None
        self.wait = None
        self.notifier = TwoFactorNotifier()
        
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
    
    def notify_user_2fa_required(self):
        """Sistema completo de notificação 2FA"""
        logger.info("=== INICIANDO NOTIFICAÇÕES 2FA ===")
        
        # 1. Som de alerta
        self.notifier.play_alert_sound()
        
        # 2. Flash no console
        self.notifier.flash_console()
        
        # 3. Popup de notificação
        popup_thread = threading.Thread(
            target=self.notifier.show_popup_notification,
            args=("Instagram está solicitando código de verificação 2FA!\n"
                  "Verifique seu telefone ou app autenticador.\n"
                  "Digite o código de 6 dígitos quando solicitado.",),
            daemon=True
        )
        popup_thread.start()
        
        # 4. Notificação do sistema
        system_thread = threading.Thread(
            target=self.notifier.show_system_notification,
            args=("Código 2FA necessário! Verifique seu telefone.",),
            daemon=True
        )
        system_thread.start()
        
        # 5. Console destacado
        print("\n" + "#"*80)
        print("#### ATENÇÃO: AUTENTICAÇÃO DE DUAS ETAPAS NECESSÁRIA ####".center(80))
        print("#"*80)
        print("📱 O Instagram enviou um código de verificação para:")
        print("   • Seu telefone (SMS)")
        print("   • Seu app autenticador (Google Authenticator, Authy, etc.)")
        print("   • Seu email backup")
        print("\n🔔 NOTIFICAÇÕES ENVIADAS:")
        print("   ✓ Som de alerta tocado")
        print("   ✓ Popup de notificação exibido")
        print("   ✓ Notificação do sistema enviada")
        print("\n⏰ Você tem 2 minutos para inserir o código!")
        print("#"*80 + "\n")
    
    def get_2fa_code_with_timeout(self) -> str:
        """Solicita código 2FA com timeout e múltiplas tentativas"""
        code_received = threading.Event()
        user_code = [None]  # Lista para permitir modificação na thread
        
        def get_code_input():
            """Thread para capturar código do usuário"""
            try:
                attempts = 0
                max_attempts = 3
                
                while attempts < max_attempts and not code_received.is_set():
                    print(f"\n📝 TENTATIVA {attempts + 1}/{max_attempts}")
                    print("="*50)
                    
                    try:
                        code = input("Digite o código 2FA (6 dígitos): ").strip()
                        
                        # Validação do código
                        if len(code) == 6 and code.isdigit():
                            user_code[0] = code
                            code_received.set()
                            print(f"✅ Código {code} recebido! Enviando para Instagram...")
                            # Som de confirmação
                            if SOUND_AVAILABLE and platform.system() == "Windows":
                                winsound.Beep(800, 200)
                                winsound.Beep(1000, 200)
                            break
                        else:
                            print("❌ Código inválido!")
                            print("   • Deve ter exatamente 6 dígitos")
                            print("   • Apenas números são aceitos")
                            print("   • Exemplo: 123456")
                            attempts += 1
                            
                            if attempts < max_attempts:
                                print(f"\n🔄 Tente novamente... ({max_attempts - attempts} tentativas restantes)")
                                # Som de erro
                                if SOUND_AVAILABLE and platform.system() == "Windows":
                                    winsound.Beep(300, 300)
                            
                    except EOFError:
                        logger.error("EOF detectado - entrada interrompida")
                        break
                    except KeyboardInterrupt:
                        logger.info("Operação cancelada pelo usuário")
                        break
                
                if attempts >= max_attempts:
                    print("\n❌ Máximo de tentativas atingido!")
                    code_received.set()
                    
            except Exception as e:
                logger.error(f"Erro na captura do código: {e}")
                code_received.set()
        
        # Iniciar thread de captura
        input_thread = threading.Thread(target=get_code_input, daemon=True)
        input_thread.start()
        
        # Contador visual de tempo
        def show_countdown():
            """Mostra countdown visual"""
            for remaining in range(120, 0, -1):
                if code_received.is_set():
                    break
                
                mins, secs = divmod(remaining, 60)
                print(f"\r⏰ Tempo restante: {mins:02d}:{secs:02d} ", end="", flush=True)
                time.sleep(1)
            
            if not code_received.is_set():
                print("\n\n⏰ TEMPO ESGOTADO! (2 minutos)")
                code_received.set()
        
        # Iniciar countdown em thread separada
        countdown_thread = threading.Thread(target=show_countdown, daemon=True)
        countdown_thread.start()
        
        # Aguardar código ou timeout
        code_received.wait(timeout=125)  # 5 segundos extras para segurança
        
        return user_code[0]
    
    def login_to_instagram(self) -> bool:
        """Login completo com sistema avançado de 2FA"""
        try:
            logger.info("Abrindo Instagram...")
            self.driver.get("https://www.instagram.com/")
            time.sleep(5)
            
            # Login básico
            username_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            password_field = self.driver.find_element(By.NAME, "password")
            
            logger.info(f"Inserindo credenciais para: {self.email}")
            username_field.send_keys(self.email)
            password_field.send_keys(self.password)
            
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            time.sleep(10)
            
            return self.check_login_result()
            
        except Exception as e:
            logger.error(f"Erro durante login: {e}")
            return False
    
    def handle_2fa_process(self) -> bool:
        """Processo completo de 2FA com notificações"""
        try:
            logger.info("2FA detectado - iniciando processo avançado...")
            
            # Notificar usuário de todas as formas possíveis
            self.notify_user_2fa_required()
            
            # Solicitar código com sistema avançado
            verification_code = self.get_2fa_code_with_timeout()
            
            if not verification_code:
                logger.error("Código 2FA não fornecido ou tempo esgotado")
                return False
            
            # Inserir código no Instagram
            try:
                code_field = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "verificationCode"))
                )
            except TimeoutException:
                code_field = self.driver.find_element(By.XPATH, "//input[@aria-label='Security code']")
            
            logger.info(f"Inserindo código 2FA: {verification_code}")
            code_field.clear()
            code_field.send_keys(verification_code)
            code_field.send_keys(Keys.RETURN)
            
            time.sleep(10)
            
            # Verificar resultado
            current_url = self.driver.current_url
            if "two_factor" not in current_url and "instagram.com" in current_url:
                print("\n🎉 2FA ACEITO COM SUCESSO!")
                # Som de sucesso
                if SOUND_AVAILABLE and platform.system() == "Windows":
                    for freq in [523, 659, 784, 1047]:  # Acorde C maior
                        winsound.Beep(freq, 200)
                return True
            else:
                print("\n❌ Código 2FA rejeitado!")
                return False
                
        except Exception as e:
            logger.error(f"Erro durante processo 2FA: {e}")
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
            print("\n" + "="*80)
            print("INSTAGRAM BOT COM NOTIFICAÇÕES 2FA AVANÇADAS")
            print("="*80)
            print(f"Email: {self.email}")
            print("Recursos:")
            print("  ✓ Notificações sonoras")
            print("  ✓ Popups de alerta")
            print("  ✓ Notificações do sistema")
            print("  ✓ Countdown visual")
            print("  ✓ Múltiplas tentativas")
            print("="*80)
            
            if not self.setup_driver():
                return False
            
            success = self.login_to_instagram()
            
            if success:
                print("\n" + "🎉"*30)
                print("LOGIN REALIZADO COM SUCESSO!")
                print("🎉"*30)
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
    
    print("Instagram Bot com Sistema Avançado de Notificação 2FA")
    print("Pressione Ctrl+C para cancelar")
    
    bot = InstagramAdvanced2FA(EMAIL, PASSWORD)
    
    try:
        success = bot.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário")
        sys.exit(130)

if __name__ == "__main__":
    main()