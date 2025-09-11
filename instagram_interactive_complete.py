#!/usr/bin/env python3
"""
Instagram Bot - Sistema Interativo Completo
Permite ao usuário inserir código 2FA e completa o login automaticamente
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
        logging.FileHandler('instagram_interactive.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class InstagramInteractiveBot:
    """Instagram bot interativo completo"""
    
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
            
            logger.info("Chrome configurado com sucesso - modo visível")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao configurar WebDriver: {e}")
            return False
    
    def play_notification_sound(self):
        """Toca som de notificação"""
        try:
            if SOUND_AVAILABLE and platform.system() == "Windows":
                # Som de notificação mais suave
                winsound.Beep(800, 300)
                time.sleep(0.2)
                winsound.Beep(1000, 300)
        except Exception:
            pass
    
    def show_notification_popup(self, message: str):
        """Mostra popup de notificação"""
        try:
            def show_popup():
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                messagebox.showinfo("Instagram 2FA", message)
                root.destroy()
            
            threading.Thread(target=show_popup, daemon=True).start()
        except Exception:
            pass
    
    def notify_2fa_required(self):
        """Notifica que 2FA é necessário"""
        print("\n" + "="*70)
        print("🔐 AUTENTICAÇÃO DE DUAS ETAPAS DETECTADA 🔐".center(70))
        print("="*70)
        print("📱 O Instagram enviou um código de verificação!")
        print("🔍 Verifique:")
        print("   • SMS no seu telefone")
        print("   • App autenticador (Google Authenticator, Authy, etc.)")
        print("   • Email de backup")
        print("="*70)
        
        # Som de notificação
        self.play_notification_sound()
        
        # Popup de notificação
        self.show_notification_popup(
            "🔐 Instagram 2FA Necessário!\n\n"
            "Verifique seu telefone ou app autenticador\n"
            "para o código de 6 dígitos."
        )
    
    def get_2fa_code_from_user(self) -> str:
        """Solicita código 2FA do usuário com validação"""
        print("\n📝 INSERÇÃO DO CÓDIGO 2FA")
        print("="*50)
        print("💡 Formatos aceitos:")
        print("   • 123456")
        print("   • 123-456")
        print("   • 123 456")
        print("="*50)
        
        max_attempts = 3
        
        for attempt in range(max_attempts):
            print(f"\n🔢 Tentativa {attempt + 1}/{max_attempts}")
            
            try:
                # Oferece opção de GUI no primeiro attempt
                if attempt == 0:
                    print("💻 Digite o código abaixo OU pressione ENTER para interface gráfica:")
                
                user_input = input("🔐 Código 2FA: ").strip()
                
                # Se usuário pressionou apenas ENTER, abrir GUI
                if not user_input and attempt == 0:
                    print("🖥️ Abrindo interface gráfica...")
                    user_input = self.get_code_via_gui()
                    if user_input:
                        print(f"✅ Código recebido via interface: {user_input}")
                
                if not user_input:
                    print("❌ Nenhum código fornecido!")
                    continue
                
                # Validar e limpar código
                cleaned_code = re.sub(r'[^\d]', '', user_input)
                
                if len(cleaned_code) != 6:
                    print(f"❌ Código deve ter 6 dígitos (você digitou {len(cleaned_code)})")
                    continue
                
                if not cleaned_code.isdigit():
                    print("❌ Código deve conter apenas números")
                    continue
                
                # Verificar códigos óbvios
                if cleaned_code in ["000000", "123456"]:
                    print("❌ Código inválido - digite o código real do Instagram")
                    continue
                
                if len(set(cleaned_code)) == 1:
                    print("❌ Código não pode ser uma sequência repetida")
                    continue
                
                # Confirmação
                formatted_code = f"{cleaned_code[:3]}-{cleaned_code[3:]}"
                print(f"✅ Código válido recebido: {formatted_code}")
                
                confirm = input("📤 Confirma o envio? (ENTER=sim, n=não): ").strip().lower()
                if confirm == "" or confirm.startswith('s') or confirm.startswith('y'):
                    print("🚀 Enviando código para Instagram...")
                    return cleaned_code
                else:
                    print("🔄 Código cancelado, tente novamente")
                    continue
                
            except (EOFError, KeyboardInterrupt):
                print("\n⚠️ Entrada cancelada")
                return None
        
        print(f"\n❌ Máximo de {max_attempts} tentativas atingido")
        return None
    
    def get_code_via_gui(self) -> str:
        """Solicita código via interface gráfica"""
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            code = simpledialog.askstring(
                "Instagram 2FA",
                "Digite o código de verificação de 6 dígitos:\n\n"
                "Formatos aceitos:\n"
                "• 123456\n"
                "• 123-456\n"
                "• 123 456",
                parent=root
            )
            
            root.destroy()
            return code.strip() if code else ""
            
        except Exception:
            return ""
    
    def login_to_instagram(self) -> bool:
        """Login completo no Instagram"""
        try:
            logger.info("🌐 Abrindo Instagram...")
            self.driver.get("https://www.instagram.com/")
            time.sleep(5)
            
            # Encontrar campos de login
            try:
                username_field = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "username"))
                )
                password_field = self.driver.find_element(By.NAME, "password")
                logger.info("✅ Campos de login encontrados")
            except TimeoutException:
                logger.error("❌ Campos de login não encontrados")
                return False
            
            # Inserir credenciais
            logger.info(f"📧 Inserindo email: {self.email}")
            username_field.clear()
            username_field.send_keys(self.email)
            
            logger.info("🔒 Inserindo senha...")
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Clicar no botão de login
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            logger.info("🎯 Clicando no botão de login...")
            login_button.click()
            
            time.sleep(10)
            
            return self.handle_login_result()
            
        except Exception as e:
            logger.error(f"❌ Erro durante login: {e}")
            return False
    
    def handle_login_result(self) -> bool:
        """Gerencia resultado do login"""
        try:
            current_url = self.driver.current_url
            logger.info(f"🌐 URL atual: {current_url}")
            
            # Verificar se login foi bem-sucedido diretamente
            if self.is_login_successful(current_url):
                print("\n🎉 LOGIN REALIZADO COM SUCESSO!")
                print("✅ Você está logado no Instagram!")
                return True
            
            # Verificar se 2FA é necessário
            if "two_factor" in current_url or self.check_2fa_elements():
                return self.handle_2fa_process()
            
            # Verificar erros
            error_msg = self.check_for_errors()
            if error_msg:
                print(f"\n❌ Erro detectado: {error_msg}")
                return False
            
            print("\n⚠️ Status de login indeterminado")
            print(f"URL: {current_url}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar resultado: {e}")
            return False
    
    def is_login_successful(self, url: str) -> bool:
        """Verifica se login foi bem-sucedido"""
        success_indicators = [
            "instagram.com/" == url,
            "instagram.com" in url and "accounts/login" not in url and "two_factor" not in url
        ]
        return any(success_indicators)
    
    def check_2fa_elements(self) -> bool:
        """Verifica se há elementos de 2FA na página"""
        selectors = [
            "//input[@name='verificationCode']",
            "//input[@aria-label='Security code']",
            "//*[contains(text(), 'Enter the 6-digit code')]",
            "//*[contains(text(), 'We sent you a code')]"
        ]
        
        for selector in selectors:
            try:
                element = self.driver.find_element(By.XPATH, selector)
                if element.is_displayed():
                    return True
            except NoSuchElementException:
                continue
        
        return False
    
    def check_for_errors(self) -> str:
        """Verifica se há erros de login"""
        error_selectors = [
            "//*[contains(text(), 'Sorry, your password was incorrect')]",
            "//*[contains(text(), 'incorrect')]",
            "//*[contains(text(), 'The username you entered')]",
            "//div[@role='alert']"
        ]
        
        for selector in error_selectors:
            try:
                element = self.driver.find_element(By.XPATH, selector)
                if element.is_displayed():
                    return element.text
            except NoSuchElementException:
                continue
        
        return ""
    
    def handle_2fa_process(self) -> bool:
        """Processa autenticação de duas etapas"""
        try:
            logger.info("🔐 2FA detectado - iniciando processo interativo")
            
            # Notificar usuário
            self.notify_2fa_required()
            
            # Solicitar código
            verification_code = self.get_2fa_code_from_user()
            
            if not verification_code:
                print("❌ Código 2FA não fornecido - cancelando login")
                return False
            
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
                    logger.info("✅ Campo de código 2FA encontrado")
                    break
                except TimeoutException:
                    continue
            
            if not code_field:
                logger.error("❌ Campo de código 2FA não encontrado")
                return False
            
            # Inserir código
            logger.info("📝 Inserindo código 2FA...")
            code_field.clear()
            time.sleep(0.5)
            
            # Inserir dígito por dígito para simular entrada humana
            for digit in verification_code:
                code_field.send_keys(digit)
                time.sleep(0.2)
            
            # Enviar código
            code_field.send_keys(Keys.RETURN)
            logger.info("✅ Código 2FA enviado!")
            
            print("⏳ Aguardando verificação do Instagram...")
            time.sleep(15)
            
            # Verificar resultado do 2FA
            current_url = self.driver.current_url
            
            if self.is_login_successful(current_url):
                print("\n🎊 2FA ACEITO - LOGIN COMPLETO!")
                print("✅ Você está oficialmente logado no Instagram!")
                
                # Som de sucesso
                if SOUND_AVAILABLE and platform.system() == "Windows":
                    try:
                        winsound.Beep(1000, 200)
                        winsound.Beep(1200, 200)
                        winsound.Beep(1500, 300)
                    except:
                        pass
                
                return True
            elif "two_factor" in current_url:
                print("\n❌ Código 2FA rejeitado pelo Instagram")
                print("💡 Possíveis causas:")
                print("   • Código expirado")
                print("   • Código já utilizado")
                print("   • Código incorreto")
                
                # Tentar novamente
                retry = input("\n🔄 Tentar novamente? (s/n): ").strip().lower()
                if retry.startswith('s') or retry.startswith('y'):
                    return self.handle_2fa_process()
                
                return False
            else:
                print(f"\n⚠️ Status inesperado após 2FA: {current_url}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro durante processo 2FA: {e}")
            return False
    
    def run(self) -> bool:
        """Executa o bot completo"""
        try:
            print("\n" + "="*80)
            print("🤖 INSTAGRAM BOT INTERATIVO COMPLETO 🤖".center(80))
            print("="*80)
            print(f"📧 Email: {self.email}")
            print("🔧 Recursos:")
            print("   ✅ Navegador visível")
            print("   ✅ Notificações sonoras e visuais")
            print("   ✅ Entrada interativa de código 2FA")
            print("   ✅ Interface gráfica opcional")
            print("   ✅ Validação robusta de código")
            print("   ✅ Múltiplas tentativas")
            print("   ✅ Confirmação antes do envio")
            print("="*80)
            print("🚀 Iniciando processo de login...")
            
            # Setup
            if not self.setup_driver():
                return False
            
            # Login
            success = self.login_to_instagram()
            
            if success:
                print("\n" + "🎉"*35)
                print("🎉 SUCESSO TOTAL - VOCÊ ESTÁ LOGADO! 🎉".center(70))
                print("🎉"*35)
                print("🌐 Verifique o navegador para confirmar")
                print("⏳ Mantendo sessão ativa por 2 minutos para você explorar...")
                time.sleep(120)  # 2 minutos para o usuário usar
            else:
                print("\n" + "❌"*25)
                print("❌ LOGIN FALHOU ❌".center(50))
                print("❌"*25)
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erro na execução: {e}")
            return False
        finally:
            print("\n🔄 Finalizando sessão...")
            if self.driver:
                self.driver.quit()
                print("✅ Navegador fechado")

def main():
    """Função principal"""
    EMAIL = "eltons.souz@gmail.com"
    PASSWORD = "Mami210912!"
    
    print("🤖 Instagram Bot Interativo Completo")
    print("💬 Permite inserção de código 2FA em tempo real")
    print("⚠️ Pressione Ctrl+C para cancelar a qualquer momento")
    
    bot = InstagramInteractiveBot(EMAIL, PASSWORD)
    
    try:
        success = bot.run()
        print(f"\n🏁 Processo finalizado - {'Sucesso' if success else 'Falha'}")
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Operação cancelada pelo usuário")
        print("👋 Até a próxima!")
        sys.exit(130)
        
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()