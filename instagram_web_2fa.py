#!/usr/bin/env python3
"""
Instagram Bot com Sistema Web 2FA
Bot detecta 2FA → Abre interface web → Usuário insere código → Login continua
"""

import time
import threading
import logging
import json
import webbrowser
from flask import Flask, render_template_string, request, jsonify
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

# Biblioteca de som removida conforme solicitado
SOUND_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Silenciar logs do Flask para interface mais limpa
logging.getLogger('werkzeug').setLevel(logging.ERROR)

class InstagramWeb2FA:
    """Instagram Bot com interface web para 2FA"""
    
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.driver = None
        self.wait = None
        self.flask_app = Flask(__name__)
        self.two_fa_code = None
        self.code_received = threading.Event()
        self.server_thread = None
        
        # Setup Flask routes
        self.setup_flask_routes()
    
    def setup_flask_routes(self):
        """Configura rotas do servidor web"""
        
        @self.flask_app.route('/')
        def index():
            """Página principal com interface 2FA"""
            return render_template_string('''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Instagram 2FA - Sistema Web</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 500px;
            width: 90%;
            animation: fadeIn 0.5s ease-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .instagram-logo {
            font-size: 2.5em;
            font-weight: bold;
            background: linear-gradient(45deg, #f09433 0%,#e6683c 25%,#dc2743 50%,#cc2366 75%,#bc1888 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 20px;
        }
        
        .title {
            color: #333;
            font-size: 1.8em;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            line-height: 1.5;
        }
        
        .status-box {
            background: #e8f5e8;
            border: 2px solid #4CAF50;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 25px;
            color: #2e7d32;
        }
        
        .input-group {
            margin-bottom: 20px;
        }
        
        .input-label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 500;
        }
        
        .code-input {
            width: 100%;
            padding: 15px;
            font-size: 1.2em;
            border: 2px solid #e1e1e1;
            border-radius: 10px;
            text-align: center;
            letter-spacing: 3px;
            transition: all 0.3s ease;
        }
        
        .code-input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 10px rgba(102, 126, 234, 0.3);
        }
        
        .submit-btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 1.1em;
            border-radius: 10px;
            cursor: pointer;
            width: 100%;
            transition: all 0.3s ease;
            font-weight: 600;
        }
        
        .submit-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        
        .submit-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .help-text {
            margin-top: 20px;
            color: #888;
            font-size: 0.9em;
        }
        
        .countdown {
            font-weight: bold;
            color: #dc2743;
        }
        
        .success {
            background: #d4edda;
            border-color: #c3e6cb;
            color: #155724;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
        }
        
        .formats {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-size: 0.9em;
            color: #666;
        }
        
        .continue-btn {
            background: #0095f6;
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            margin-top: 20px;
            width: 100%;
            transition: background 0.3s;
        }
        
        .continue-btn:hover {
            background: #0082d8;
        }
        
        .success-container {
            text-align: center;
            padding: 20px;
            background: #d4edda;
            color: #155724;
            border-radius: 10px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="instagram-logo">Instagram</div>
        <h1 class="title">Autenticacao de Duas Etapas</h1>
        <p class="subtitle">
            Seu login foi detectado! Insira o codigo de verificacao de 6 digitos abaixo.
        </p>
        
        <div class="status-box">
            [LOCK] Sistema detectou 2FA automaticamente<br>
            [PHONE] Verifique seu telefone ou app autenticador
        </div>
        
        <div class="formats">
            <strong>Formatos aceitos:</strong><br>
            • 123456 &nbsp; • 123-456 &nbsp; • 123 456
        </div>
        
        <form id="codeForm">
            <div class="input-group">
                <label class="input-label" for="code">Codigo de Verificacao</label>
                <input 
                    type="text" 
                    id="code" 
                    class="code-input" 
                    placeholder="000000"
                    maxlength="10"
                    autocomplete="off"
                    autofocus
                >
            </div>
            
            <button type="submit" class="submit-btn" id="submitBtn">
                [SEND] Enviar Codigo
            </button>
        </form>
        
        <div class="help-text">
            [TIME] Tempo restante: <span class="countdown" id="countdown">2:00</span><br>
            [TIP] Dica: O codigo expira em alguns minutos
        </div>
        
        <div id="result"></div>
    </div>

    <script>
        // Countdown timer
        let timeLeft = 120; // 2 minutos
        const countdownEl = document.getElementById('countdown');
        
        function updateCountdown() {
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            countdownEl.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            
            if (timeLeft <= 30) {
                countdownEl.style.color = '#dc2743';
                countdownEl.style.fontWeight = 'bold';
            }
            
            if (timeLeft > 0) {
                timeLeft--;
                setTimeout(updateCountdown, 1000);
            } else {
                countdownEl.textContent = 'EXPIRADO';
                document.getElementById('submitBtn').disabled = true;
            }
        }
        
        updateCountdown();
        
        // Form handling
        document.getElementById('codeForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const code = document.getElementById('code').value.trim();
            const submitBtn = document.getElementById('submitBtn');
            const resultDiv = document.getElementById('result');
            
            // Validation
            const cleanCode = code.replace(/[^0-9]/g, '');
            
            if (cleanCode.length !== 6) {
                alert('[ERROR] Codigo deve ter exatamente 6 digitos');
                return;
            }
            
            if (cleanCode === '000000' || cleanCode === '123456') {
                alert('[ERROR] Digite o codigo real do Instagram');
                return;
            }
            
            // Send code
            submitBtn.disabled = true;
            submitBtn.textContent = '[SEND] Enviando...';
            
            try {
                const response = await fetch('/submit_code', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ code: cleanCode })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    resultDiv.innerHTML = `
                        <div class="success-container">
                            <h3>[OK] Codigo Aceito com Sucesso!</h3>
                            <p>Voce foi logado no Instagram!</p>
                            <button class="continue-btn" onclick="window.close(); window.location.href='https://www.instagram.com';">
                                Continuar no Instagram
                            </button>
                        </div>
                    `;
                    submitBtn.style.display = 'none';
                    document.getElementById('codeForm').style.display = 'none';
                } else {
                    resultDiv.innerHTML = `
                        <div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 10px; margin-top: 20px;">
                            [ERROR] ${result.message}
                        </div>
                    `;
                    submitBtn.disabled = false;
                    submitBtn.textContent = '[SEND] Enviar Codigo';
                }
            } catch (error) {
                alert('[ERROR] Erro ao enviar codigo');
                submitBtn.disabled = false;
                submitBtn.textContent = '[SEND] Enviar Codigo';
            }
        });
        
        // Auto-format input
        document.getElementById('code').addEventListener('input', function(e) {
            let value = e.target.value.replace(/[^0-9]/g, '');
            if (value.length > 6) value = value.substring(0, 6);
            e.target.value = value;
        });
    </script>
</body>
</html>
            ''')
        
        @self.flask_app.route('/submit_code', methods=['POST'])
        def submit_code():
            """Recebe código 2FA da interface web"""
            try:
                data = request.get_json()
                code = data.get('code', '').strip()
                
                if len(code) != 6 or not code.isdigit():
                    return jsonify({'success': False, 'message': 'Codigo invalido'})
                
                # Armazenar código e sinalizar
                self.two_fa_code = code
                self.code_received.set()
                
                logger.info(f"Código 2FA recebido via web: {code}")
                return jsonify({'success': True, 'message': 'Codigo recebido'})
                
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)})
    
    def start_web_server(self):
        """Inicia servidor web em thread separada"""
        def run_server():
            self.flask_app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        time.sleep(2)  # Aguardar servidor iniciar
    
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
    
    def open_2fa_interface(self):
        """Abre interface web para inserção de 2FA"""
        try:
            logger.info("Abrindo interface web para 2FA...")
            
            # Som de notificação
            # Som removido conforme solicitado
            
            # Abrir no navegador
            webbrowser.open('http://127.0.0.1:5000')
            
            print("\n" + "="*60)
            print("[WEB] INTERFACE WEB 2FA ABERTA")
            print("="*60)
            print("[PHONE] Uma pagina web foi aberta no seu navegador")
            print("[LOCK] Insira o codigo de 6 digitos na interface")
            print("[TIME] Voce tem 2 minutos para inserir o codigo")
            print("="*60)
            
        except Exception as e:
            logger.error(f"Erro ao abrir interface: {e}")
    
    def wait_for_2fa_code(self) -> str:
        """Aguarda código 2FA via interface web"""
        logger.info("Aguardando código 2FA via interface web...")
        
        # Aguardar até 130 segundos (2min + margem)
        if self.code_received.wait(timeout=130):
            return self.two_fa_code
        else:
            logger.warning("Timeout: Código não recebido em 2 minutos")
            return None
    
    def login_to_instagram(self) -> bool:
        """Login completo no Instagram"""
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
                print("\n🎉 LOGIN REALIZADO COM SUCESSO!")
                return True
            
            # 2FA necessário
            if "two_factor" in url:
                return self.handle_2fa()
            
            print("[ERROR] Falha no login")
            return False
            
        except Exception as e:
            logger.error(f"Erro na verificação: {e}")
            return False
    
    def handle_2fa(self) -> bool:
        """Processo 2FA com interface web"""
        try:
            logger.info("[LOCK] 2FA detectado - iniciando interface web")
            
            # Abrir interface web
            self.open_2fa_interface()
            
            # Aguardar código
            verification_code = self.wait_for_2fa_code()
            
            if not verification_code:
                print("[ERROR] Codigo 2FA nao recebido - timeout")
                return False
            
            # Inserir código no Instagram
            logger.info("[INPUT] Inserindo codigo 2FA no Instagram...")
            
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
                logger.error("[ERROR] Campo de codigo nao encontrado")
                return False
            
            # Inserir código
            code_field.clear()
            time.sleep(0.5)
            
            for digit in verification_code:
                code_field.send_keys(digit)
                time.sleep(0.1)
            
            code_field.send_keys(Keys.RETURN)
            logger.info("[OK] Codigo enviado para Instagram")
            
            time.sleep(5)
            
            # Procurar e clicar no botão azul de confirmação
            try:
                print("[INFO] Procurando botao azul de confirmacao...")
                
                # Múltiplos seletores para o botão azul do Instagram
                button_selectors = [
                    "//button[contains(text(), 'Confirm') or contains(text(), 'Continue') or contains(text(), 'Next')]",
                    "//button[@type='submit'][not(@name)]",
                    "//div[@role='button'][contains(@style, 'background')]",
                    "//button[contains(@style, 'background-color')]",
                    "//div[contains(@class, '_acan')]",  # Classe comum de botões do Instagram
                    "//div[@role='button'][last()]"
                ]
                
                button_clicked = False
                for selector in button_selectors:
                    try:
                        blue_button = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        if blue_button:
                            print(f"[CLICK] Clicando no botao encontrado")
                            blue_button.click()
                            button_clicked = True
                            time.sleep(2)
                            break
                    except TimeoutException:
                        continue
                
                if not button_clicked:
                    print("[WARNING] Botao azul nao encontrado automaticamente")
                    
            except Exception as e:
                print(f"[WARNING] Erro ao procurar botao azul: {e}")
            
            time.sleep(10)
            
            # Verificar resultado
            url = self.driver.current_url
            
            if "two_factor" not in url and "instagram.com" in url:
                print("\n[SUCCESS] 2FA ACEITO - LOGIN COMPLETO!")
                print("[OK] Voce esta oficialmente logado no Instagram!")
                
                # Som de sucesso
                # Som removido conforme solicitado
                
                return True
            else:
                print("[ERROR] Codigo 2FA rejeitado")
                return False
                
        except Exception as e:
            logger.error(f"Erro no 2FA: {e}")
            return False
    
    def run(self) -> bool:
        """Executa o sistema completo"""
        try:
            print("="*70)
            print("INSTAGRAM BOT COM SISTEMA WEB 2FA")
            print("="*70)
            print(f"Email: {self.email}")
            print("Recursos:")
            print("   • Detecção automática de 2FA")
            print("   • Interface web elegante")
            print("   • Input via iFrame/navegador")
            print("   • Servidor local Flask")
            print("   • Comunicação em tempo real")
            print("="*70)
            
            # Iniciar servidor web
            print("[START] Iniciando servidor web...")
            self.start_web_server()
            
            # Setup Chrome
            if not self.setup_driver():
                return False
            
            # Login
            success = self.login_to_instagram()
            
            if success:
                print("\n" + "="*50)
                print("[SUCCESS] SUCESSO TOTAL - SISTEMA WEB FUNCIONOU!")
                print("="*50)
                print("[WEB] Voce esta logado via interface web!")
                print("[INFO] Navegador permanecera aberto para continuar no Instagram")
                print("[INFO] Pressione Ctrl+C para encerrar quando desejar")
                try:
                    while True:
                        time.sleep(10)  # Manter indefinidamente
                except KeyboardInterrupt:
                    print("\n[INFO] Encerrando conforme solicitado...")
            else:
                print("\n[ERROR] Login falhou")
            
            return success
            
        except Exception as e:
            logger.error(f"Erro: {e}")
            return False
        finally:
            # NAO fechar o driver - manter janela aberta conforme solicitado
            print("[INFO] Janela do navegador mantida aberta para continuar no Instagram")

def main():
    """Função principal"""
    EMAIL = "eltons.souz@gmail.com"
    PASSWORD = "Mami210912!"
    
    print("Instagram Bot - Sistema Web 2FA")
    print("Interface web para inserção de código")
    
    bot = InstagramWeb2FA(EMAIL, PASSWORD)
    
    try:
        success = bot.run()
        print(f"\n[FINISH] Finalizado - {'Sucesso' if success else 'Falha'}")
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n[WARNING] Cancelado pelo usuario")
        return 130

if __name__ == "__main__":
    exit(main())