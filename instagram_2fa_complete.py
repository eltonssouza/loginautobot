#!/usr/bin/env python3
"""
Instagram Bot com Sistema Completo de 2FA
Inclui 6 métodos de notificação + solicitação avançada de código
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
    import winsound  # Para notificações sonoras no Windows
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('instagram_2fa_complete.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CodeValidator:
    """Sistema avançado de validação de códigos 2FA"""
    
    @staticmethod
    def validate_2fa_code(code: str):
        """
        Valida código 2FA com diferentes formatos aceitos
        Retorna: (is_valid, error_message)
        """
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
    
    @staticmethod
    def format_code_display(code: str) -> str:
        """Formata código para exibição (XXX-XXX)"""
        if len(code) == 6:
            return f"{code[:3]}-{code[3:]}"
        return code

class TwoFactorNotifier:
    """Sistema avançado de notificações para 2FA"""
    
    @staticmethod
    def play_alert_sound():
        """Toca som de alerta para chamar atenção"""
        try:
            if SOUND_AVAILABLE and platform.system() == "Windows":
                # Melodia de alerta mais chamativa
                frequencies = [800, 1000, 1200, 1000, 800]
                for freq in frequencies:
                    winsound.Beep(freq, 300)
                    time.sleep(0.1)
            elif platform.system() == "Darwin":  # macOS
                os.system("afplay /System/Library/Sounds/Glass.aiff")
            elif platform.system() == "Linux":
                os.system("speaker-test -t sine -f 1000 -l 1 &")
        except Exception as e:
            logger.warning(f"Não foi possível tocar som de alerta: {e}")
    
    @staticmethod
    def show_popup_notification(message: str, title: str = "Instagram 2FA"):
        """Mostra popup de notificação"""
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            root.attributes('-toolwindow', True)  # Windows: não aparece na barra de tarefas
            
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
                    f'$notify.ShowBalloonTip(8000)'
                ], capture_output=True)
            elif platform.system() == "Darwin":
                subprocess.run([
                    "osascript", "-e",
                    f'display notification "{message}" with title "{title}" sound name "Glass"'
                ])
            elif platform.system() == "Linux":
                subprocess.run(["notify-send", "-u", "critical", title, message])
        except Exception as e:
            logger.warning(f"Erro ao mostrar notificação do sistema: {e}")
    
    @staticmethod
    def flash_console():
        """Pisca o console para chamar atenção"""
        try:
            for i in range(3):
                print("\n" + "🚨"*40)
                print("🚨 CÓDIGO 2FA NECESSÁRIO AGORA! 🚨".center(80))
                print("🚨"*40 + "\n")
                time.sleep(0.5)
        except Exception as e:
            logger.warning(f"Erro ao piscar console: {e}")

class CodeRequestGUI:
    """Interface gráfica para solicitar código 2FA"""
    
    @staticmethod
    def request_code_gui() -> str:
        """Solicita código através de interface gráfica"""
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            code = simpledialog.askstring(
                "Instagram 2FA",
                "Digite o código de verificação de 6 dígitos:\n\n"
                "Verifique:\n"
                "• SMS no seu telefone\n"
                "• App autenticador\n"
                "• Email backup\n\n"
                "Formato: 123456 ou 123-456",
                parent=root
            )
            
            root.destroy()
            return code if code else ""
            
        except Exception as e:
            logger.warning(f"Erro na interface gráfica: {e}")
            return ""

class InstagramComplete2FA:
    """Instagram bot com sistema completo de 2FA"""
    
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.driver = None
        self.wait = None
        self.notifier = TwoFactorNotifier()
        self.validator = CodeValidator()
        self.gui = CodeRequestGUI()
        
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
        """Sistema completo de notificação 2FA - 5 métodos"""
        logger.info("=== INICIANDO SISTEMA DE NOTIFICAÇÕES 2FA ===")
        
        # 1. Som de alerta
        threading.Thread(target=self.notifier.play_alert_sound, daemon=True).start()
        
        # 2. Flash no console
        threading.Thread(target=self.notifier.flash_console, daemon=True).start()
        
        # 3. Popup de notificação
        threading.Thread(
            target=self.notifier.show_popup_notification,
            args=("🔐 ATENÇÃO: Código 2FA necessário!\n\n"
                  "📱 Verifique seu telefone para SMS\n"
                  "📲 Abra seu app autenticador\n"
                  "📧 Confira seu email backup\n\n"
                  "⏰ Você tem 2 minutos!",),
            daemon=True
        ).start()
        
        # 4. Notificação do sistema
        threading.Thread(
            target=self.notifier.show_system_notification,
            args=("📱 Código 2FA necessário! Verifique seu telefone ou app autenticador.",),
            daemon=True
        ).start()
        
        # 5. Console destacado
        time.sleep(1)  # Aguardar threads iniciarem
        print("\n" + "="*80)
        print("🔐 AUTENTICAÇÃO DE DUAS ETAPAS NECESSÁRIA 🔐".center(80))
        print("="*80)
        print("📱 O Instagram enviou um código de verificação para:")
        print("   • 📞 Seu telefone (SMS)")
        print("   • 📲 Seu app autenticador (Google Authenticator, Authy, etc.)")
        print("   • 📧 Seu email backup")
        print("\n✅ NOTIFICAÇÕES ENVIADAS:")
        print("   🔊 Som de alerta tocado")
        print("   💻 Flash visual no console")
        print("   🪟 Popup de notificação exibido")
        print("   🔔 Notificação do sistema enviada")
        print("\n⏰ TEMPO LIMITE: 2 minutos para inserir o código!")
        print("="*80 + "\n")
    
    def request_2fa_code_advanced(self) -> str:
        """
        6. 📝 Solicitação de código com validação avançada
        Múltiplas opções de entrada + validação robusta
        """
        print("📝 SOLICITAÇÃO DE CÓDIGO 2FA - SISTEMA AVANÇADO")
        print("="*60)
        print("🔧 OPÇÕES DE ENTRADA DISPONÍVEIS:")
        print("   1️⃣ Console (terminal) - Digite aqui")
        print("   2️⃣ Interface gráfica - Janela popup")
        print("   3️⃣ Múltiplas tentativas permitidas")
        print("   4️⃣ Validação automática de formato")
        print("="*60)
        
        code_received = threading.Event()
        final_code = [None]
        
        def console_input_handler():
            """Handler para entrada via console"""
            try:
                attempts = 0
                max_attempts = 5
                
                while attempts < max_attempts and not code_received.is_set():
                    print(f"\n📝 TENTATIVA {attempts + 1}/{max_attempts}")
                    print("-" * 40)
                    print("💡 FORMATOS ACEITOS:")
                    print("   • 123456")
                    print("   • 123-456")
                    print("   • 123 456")
                    print("-" * 40)
                    
                    try:
                        # Opção de interface gráfica
                        if attempts == 0:
                            print("🪟 Pressione ENTER para interface gráfica, ou digite o código:")
                        
                        user_input = input("🔢 Código 2FA: ").strip()
                        
                        # Se usuário apenas pressionou ENTER, abrir GUI
                        if not user_input and attempts == 0:
                            print("🪟 Abrindo interface gráfica...")
                            gui_code = self.gui.request_code_gui()
                            if gui_code:
                                user_input = gui_code
                                print(f"✅ Código recebido via interface gráfica: {self.validator.format_code_display(gui_code)}")
                        
                        if not user_input:
                            print("❌ Nenhum código fornecido!")
                            attempts += 1
                            continue
                        
                        # Validar código
                        is_valid, result = self.validator.validate_2fa_code(user_input)
                        
                        if is_valid:
                            final_code[0] = result
                            formatted_code = self.validator.format_code_display(result)
                            print(f"✅ Código válido recebido: {formatted_code}")
                            print("📤 Enviando para Instagram...")
                            
                            # Som de confirmação
                            if SOUND_AVAILABLE and platform.system() == "Windows":
                                winsound.Beep(800, 150)
                                winsound.Beep(1000, 150)
                                winsound.Beep(1200, 200)
                            
                            code_received.set()
                            break
                        else:
                            print(f"❌ ERRO: {result}")
                            print("🔄 Tente novamente com um código válido")
                            attempts += 1
                            
                            # Som de erro
                            if SOUND_AVAILABLE and platform.system() == "Windows":
                                winsound.Beep(300, 400)
                            
                            if attempts < max_attempts:
                                remaining = max_attempts - attempts
                                print(f"⚠️ {remaining} tentativa(s) restante(s)")
                                time.sleep(1)
                    
                    except EOFError:
                        print("\n💨 Entrada interrompida (EOF)")
                        break
                    except KeyboardInterrupt:
                        print("\n⚠️ Operação cancelada pelo usuário (Ctrl+C)")
                        break
                
                if attempts >= max_attempts:
                    print(f"\n❌ MÁXIMO DE {max_attempts} TENTATIVAS ATINGIDO!")
                    print("🔄 Processo de 2FA falhou")
                
                code_received.set()
                
            except Exception as e:
                logger.error(f"Erro no handler de entrada: {e}")
                code_received.set()
        
        def countdown_display():
            """Display de countdown com informações úteis"""
            total_seconds = 120
            
            for remaining in range(total_seconds, 0, -1):
                if code_received.is_set():
                    break
                
                mins, secs = divmod(remaining, 60)
                
                # Alertas especiais em momentos críticos
                if remaining == 60:
                    print(f"\n⚠️ ATENÇÃO: Apenas 1 minuto restante!")
                    if SOUND_AVAILABLE and platform.system() == "Windows":
                        winsound.Beep(1000, 200)
                elif remaining == 30:
                    print(f"\n🚨 URGENTE: Apenas 30 segundos restantes!")
                    if SOUND_AVAILABLE and platform.system() == "Windows":
                        winsound.Beep(1500, 200)
                elif remaining == 10:
                    print(f"\n🚨 CRÍTICO: Apenas 10 segundos!")
                    if SOUND_AVAILABLE and platform.system() == "Windows":
                        for i in range(3):
                            winsound.Beep(2000, 100)
                            time.sleep(0.1)
                
                # Status bar visual
                progress = "█" * (20 - (remaining * 20 // total_seconds))
                remaining_bars = "░" * (remaining * 20 // total_seconds)
                
                print(f"\r⏰ {mins:02d}:{secs:02d} [{progress}{remaining_bars}] ", end="", flush=True)
                time.sleep(1)
            
            if not code_received.is_set():
                print(f"\n\n⏰ TEMPO ESGOTADO! ({total_seconds//60} minutos)")
                print("❌ Processo de 2FA cancelado por timeout")
                # Som de timeout
                if SOUND_AVAILABLE and platform.system() == "Windows":
                    for i in range(5):
                        winsound.Beep(200, 200)
                        time.sleep(0.1)
                code_received.set()
        
        # Iniciar threads
        input_thread = threading.Thread(target=console_input_handler, daemon=True)
        countdown_thread = threading.Thread(target=countdown_display, daemon=True)
        
        input_thread.start()
        countdown_thread.start()
        
        # Aguardar resultado
        code_received.wait(timeout=125)  # 5 segundos extras de segurança
        
        # Limpar linha do countdown
        print("\n")
        
        if final_code[0]:
            print(f"🎯 CÓDIGO FINAL VALIDADO: {self.validator.format_code_display(final_code[0])}")
        else:
            print("❌ NENHUM CÓDIGO VÁLIDO RECEBIDO")
        
        return final_code[0]
    
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
        """Processo completo de 2FA com todos os 6 métodos"""
        try:
            logger.info("🔐 2FA DETECTADO - INICIANDO SISTEMA COMPLETO")
            
            # Métodos 1-5: Notificar usuário
            self.notify_user_2fa_required()
            
            # Método 6: Solicitar código com validação avançada
            verification_code = self.request_2fa_code_advanced()
            
            if not verification_code:
                logger.error("❌ Código 2FA não fornecido ou inválido")
                return False
            
            # Inserir código no Instagram
            try:
                logger.info("🔍 Procurando campo de código 2FA...")
                code_field = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "verificationCode"))
                )
                logger.info("✅ Campo de código encontrado")
            except TimeoutException:
                try:
                    code_field = self.driver.find_element(By.XPATH, "//input[@aria-label='Security code']")
                    logger.info("✅ Campo alternativo encontrado")
                except NoSuchElementException:
                    logger.error("❌ Campo de código 2FA não encontrado")
                    return False
            
            # Inserir código com animação visual
            logger.info(f"📝 Inserindo código: {self.validator.format_code_display(verification_code)}")
            code_field.clear()
            time.sleep(0.5)
            
            # Inserir dígito por dígito para simular digitação humana
            for digit in verification_code:
                code_field.send_keys(digit)
                time.sleep(0.2)
            
            code_field.send_keys(Keys.RETURN)
            logger.info("✅ Código enviado para Instagram!")
            
            time.sleep(10)
            
            # Verificar resultado
            current_url = self.driver.current_url
            if "two_factor" not in current_url and "instagram.com" in current_url:
                print("\n" + "🎉"*30)
                print("🎉 2FA ACEITO COM SUCESSO! 🎉")
                print("🎉"*30)
                
                # Som de sucesso elaborado
                if SOUND_AVAILABLE and platform.system() == "Windows":
                    success_melody = [523, 659, 784, 1047, 1319]  # C-E-G-C-E
                    for freq in success_melody:
                        winsound.Beep(freq, 200)
                        time.sleep(0.1)
                
                return True
            else:
                print("\n❌ CÓDIGO 2FA REJEITADO PELO INSTAGRAM!")
                print("🔄 Possíveis causas:")
                print("   • Código expirado")
                print("   • Código já usado")
                print("   • Código incorreto")
                print("   • Problemas de conectividade")
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
                logger.info("✅ Login realizado com sucesso!")
                return True
            
            # 2FA necessário
            if "two_factor" in current_url:
                return self.handle_2fa_process()
            
            # Verificar erros
            if "accounts/login" in current_url:
                logger.error("❌ Falha no login - ainda na página de login")
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao verificar login: {e}")
            return False
    
    def run(self) -> bool:
        """Executar bot completo"""
        try:
            print("\n" + "="*90)
            print("🤖 INSTAGRAM BOT COM SISTEMA COMPLETO DE 2FA 🤖".center(90))
            print("="*90)
            print(f"📧 Email: {self.email}")
            print("🔧 RECURSOS IMPLEMENTADOS:")
            print("   1️⃣ 🔊 Notificações sonoras multi-plataforma")
            print("   2️⃣ 💻 Flash visual no console")
            print("   3️⃣ 🪟 Popups de alerta")
            print("   4️⃣ 🔔 Notificações do sistema operacional")
            print("   5️⃣ ⏰ Countdown visual com alertas")
            print("   6️⃣ 📝 Solicitação avançada com validação robusta")
            print("="*90)
            print("🚀 INICIANDO PROCESSO DE LOGIN...")
            print("="*90)
            
            if not self.setup_driver():
                return False
            
            success = self.login_to_instagram()
            
            if success:
                print("\n" + "🎊"*40)
                print("🎊 LOGIN COMPLETO - SUCESSO TOTAL! 🎊".center(80))
                print("🎊"*40)
                print("✅ Você está logado no Instagram!")
                print("🌐 Verifique o navegador para confirmar")
                print("⏳ Mantendo sessão ativa por 60 segundos...")
                print("🎊"*40)
                time.sleep(60)
            else:
                print("\n" + "❌"*40)
                print("❌ FALHA NO LOGIN ❌".center(80))
                print("❌"*40)
                print("🔄 Possíveis soluções:")
                print("   • Verificar credenciais")
                print("   • Tentar novamente em alguns minutos")
                print("   • Verificar conexão com internet")
                print("❌"*40)
            
            return success
            
        except Exception as e:
            logger.error(f"Erro na execução: {e}")
            return False
        finally:
            if self.driver:
                print("🔄 Fechando navegador...")
                self.driver.quit()
                print("✅ Cleanup concluído")

def main():
    """Função principal"""
    EMAIL = "eltons.souz@gmail.com"
    PASSWORD = "Mami210912!"
    
    print("Instagram Bot - Sistema Completo de 2FA")
    print("6 Métodos de Notificação + Validação Avançada")
    print("Pressione Ctrl+C para cancelar a qualquer momento")
    
    bot = InstagramComplete2FA(EMAIL, PASSWORD)
    
    try:
        success = bot.run()
        exit_code = 0 if success else 1
        print(f"\nProcesso finalizado - Código de saída: {exit_code}")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário")
        print("Até logo!")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Erro crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()