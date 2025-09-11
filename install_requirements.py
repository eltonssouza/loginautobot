#!/usr/bin/env python3
"""
Script de instalação de dependências para teste Instagram
"""

import subprocess
import sys
import os

def install_package(package):
    """Instalar pacote via pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} instalado com sucesso")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Erro ao instalar {package}")
        return False

def check_chromedriver():
    """Verificar se ChromeDriver está disponível"""
    try:
        result = subprocess.run(["chromedriver", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ ChromeDriver encontrado: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("⚠️ ChromeDriver não encontrado no PATH")
    print("Baixe em: https://chromedriver.chromium.org/")
    print("Ou instale via: pip install webdriver-manager")
    return False

def main():
    """Instalar todas as dependências necessárias"""
    print("=== INSTALAÇÃO DE DEPENDÊNCIAS ===")
    
    # Lista de pacotes necessários
    packages = [
        "selenium",
        "webdriver-manager",  # Para gerenciar ChromeDriver automaticamente
    ]
    
    # Instalar pacotes
    all_success = True
    for package in packages:
        if not install_package(package):
            all_success = False
    
    # Verificar ChromeDriver
    check_chromedriver()
    
    if all_success:
        print("\n✅ Todas as dependências foram instaladas!")
        print("Execute: python test_login_instagram.py")
    else:
        print("\n❌ Algumas dependências falharam!")
        print("Execute manualmente: pip install selenium webdriver-manager")

if __name__ == "__main__":
    main()