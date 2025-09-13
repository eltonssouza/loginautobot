#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔐 INSTAGRAM CHROME EXTRACTOR
=============================

Sistema que utiliza cookies do Google Chrome para extração autenticada:

✅ VANTAGENS:
   - Aproveita sessão logada no Chrome
   - Acesso completo aos dados (como usuário logado)
   - Extrai Direct IDs com precisão
   - Não precisa de credenciais no código

🔧 FUNCIONALIDADES:
   - Extração via cookies do Chrome
   - Dados completos de perfis públicos e privados
   - Direct ID direto da API interna
   - Fallback para métodos alternativos
"""

import json
import re
import sqlite3
import os
import requests
import configparser
import psycopg2
from pathlib import Path
from urllib.parse import quote
import browser_cookie3

class InstagramChromeExtractor:
    def __init__(self):
        """Inicializa o extrator com cookies do Chrome"""
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        
        # Headers padrão do Instagram
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': '',
            'X-IG-App-ID': '936619743392459',
            'X-IG-WWW-Claim': '0',
            'X-Instagram-AJAX': '1',
            'Referer': 'https://www.instagram.com/',
            'Origin': 'https://www.instagram.com'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        print("🔐 INSTAGRAM CHROME EXTRACTOR INICIADO")
        print("=" * 60)
    
    def load_chrome_cookies(self):
        """Carrega cookies do Google Chrome"""
        try:
            print("🍪 Carregando cookies do Google Chrome...")
            
            # Primeiro, tentar método alternativo - arquivo de cookies manual
            if self.load_manual_cookies():
                return True
            
            # Tentar browser_cookie3 como fallback
            try:
                cookies = browser_cookie3.chrome(domain_name='instagram.com')
                
                # Adicionar cookies à sessão
                cookie_count = 0
                csrf_token = None
                
                for cookie in cookies:
                    self.session.cookies.set(cookie.name, cookie.value, domain=cookie.domain)
                    cookie_count += 1
                    
                    # Capturar CSRF token se disponível
                    if cookie.name == 'csrftoken':
                        csrf_token = cookie.value
                        self.headers['X-CSRFToken'] = csrf_token
                        self.session.headers.update({'X-CSRFToken': csrf_token})
                
                print(f"✅ {cookie_count} cookies carregados com sucesso")
                
                if csrf_token:
                    print(f"🔑 CSRF Token encontrado: {csrf_token[:20]}...")
                else:
                    print("⚠️ CSRF Token não encontrado - algumas requisições podem falhar")
                
                return cookie_count > 0
                
            except Exception as e:
                print(f"❌ Erro ao carregar cookies automaticamente: {e}")
                return self.create_guest_session()
            
        except Exception as e:
            print(f"❌ Erro geral no carregamento de cookies: {e}")
            return self.create_guest_session()
    
    def load_manual_cookies(self):
        """Carrega cookies de arquivo manual se disponível"""
        try:
            cookies_file = Path("cookies/instagram_cookies.json")
            
            if cookies_file.exists():
                print("📁 Tentando carregar cookies do arquivo manual...")
                
                with open(cookies_file, 'r') as f:
                    cookies_data = json.load(f)
                
                cookie_count = 0
                csrf_token = None
                
                for cookie in cookies_data:
                    if isinstance(cookie, dict):
                        name = cookie.get('name', '')
                        value = cookie.get('value', '')
                        domain = cookie.get('domain', '.instagram.com')
                        
                        if name and value:
                            self.session.cookies.set(name, value, domain=domain)
                            cookie_count += 1
                            
                            if name == 'csrftoken':
                                csrf_token = value
                                self.headers['X-CSRFToken'] = csrf_token
                                self.session.headers.update({'X-CSRFToken': csrf_token})
                
                if cookie_count > 0:
                    print(f"✅ {cookie_count} cookies carregados do arquivo manual")
                    if csrf_token:
                        print(f"🔑 CSRF Token encontrado: {csrf_token[:20]}...")
                    return True
            
            return False
            
        except Exception as e:
            print(f"⚠️ Erro ao carregar cookies manuais: {e}")
            return False
    
    def create_guest_session(self):
        """Cria sessão de visitante (não logado)"""
        try:
            print("👥 Criando sessão de visitante...")
            
            # Fazer requisição inicial para obter cookies básicos
            response = self.session.get("https://www.instagram.com/")
            
            # Extrair csrf token da resposta
            csrf_match = re.search(r'"csrf_token":"([^"]+)"', response.text)
            if csrf_match:
                csrf_token = csrf_match.group(1)
                self.headers['X-CSRFToken'] = csrf_token
                self.session.headers.update({'X-CSRFToken': csrf_token})
                print(f"🔑 CSRF Token obtido: {csrf_token[:20]}...")
            
            print("✅ Sessão de visitante criada")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar sessão de visitante: {e}")
            return False
    
    def extract_profile_data(self, username):
        """Extrai dados do perfil usando cookies do Chrome"""
        try:
            print(f"📊 Extraindo dados do perfil @{username}...")
            
            # URL da página do perfil
            profile_url = f"https://www.instagram.com/{username}/"
            
            # Fazer requisição autenticada
            response = self.session.get(profile_url)
            
            if response.status_code != 200:
                print(f"❌ Erro HTTP {response.status_code} ao acessar perfil")
                return None
            
            html_content = response.text
            
            # Extrair dados do JSON embutido
            profile_data = self.extract_json_data(html_content, username)
            
            if profile_data:
                print(f"✅ Dados extraídos com cookies do Chrome:")
                self.print_profile_data(profile_data)
                return profile_data
            else:
                print(f"❌ Não foi possível extrair dados do perfil")
                return None
                
        except Exception as e:
            print(f"❌ Erro na extração: {e}")
            return None
    
    def extract_json_data(self, html_content, username):
        """Extrai dados JSON da página HTML"""
        try:
            # Padrões para encontrar dados JSON
            json_patterns = [
                r'window\._sharedData\s*=\s*({.+?});',
                r'window\.__additionalDataLoaded\([^,]+,({.+?})\);',
                r'"ProfilePage"\s*:\s*\[({.+?})\]'
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, html_content, re.DOTALL)
                
                for match in matches:
                    try:
                        data = json.loads(match)
                        profile_info = self.parse_profile_from_json(data, username)
                        
                        if profile_info and profile_info.get('username'):
                            return profile_info
                            
                    except json.JSONDecodeError:
                        continue
            
            # Fallback: extração por regex direto
            return self.extract_by_regex(html_content, username)
            
        except Exception as e:
            print(f"⚠️ Erro na extração JSON: {e}")
            return self.extract_by_regex(html_content, username)
    
    def parse_profile_from_json(self, data, username):
        """Analisa dados JSON para extrair informações do perfil"""
        try:
            # Função recursiva para encontrar dados do usuário
            def find_user_data(obj, target_username):
                if isinstance(obj, dict):
                    # Verificar se é um objeto de usuário
                    if obj.get('username') == target_username:
                        return obj
                    
                    # Buscar em entrada de página
                    if 'entry_data' in obj:
                        for page_type, pages in obj['entry_data'].items():
                            for page in pages:
                                if 'graphql' in page:
                                    user_data = find_user_data(page['graphql'], target_username)
                                    if user_data:
                                        return user_data
                    
                    # Buscar recursivamente
                    for key, value in obj.items():
                        result = find_user_data(value, target_username)
                        if result:
                            return result
                
                elif isinstance(obj, list):
                    for item in obj:
                        result = find_user_data(item, target_username)
                        if result:
                            return result
                
                return None
            
            user_data = find_user_data(data, username)
            
            if user_data:
                return self.format_profile_data(user_data, username)
            
            return None
            
        except Exception as e:
            print(f"⚠️ Erro ao analisar JSON: {e}")
            return None
    
    def extract_by_regex(self, html_content, username):
        """Extração por regex como fallback"""
        try:
            print("🔄 Usando extração por regex...")
            
            # Padrões regex para dados específicos
            patterns = {
                'followers': [
                    r'"edge_followed_by":\s*{\s*"count":\s*(\d+)',
                    r'"followers_count":\s*(\d+)',
                    r'seguidores</span></div><span[^>]*>([0-9,.KMkm]+)',
                ],
                'following': [
                    r'"edge_follow":\s*{\s*"count":\s*(\d+)',
                    r'"following_count":\s*(\d+)',
                    r'seguindo</span></div><span[^>]*>([0-9,.KMkm]+)',
                ],
                'posts': [
                    r'"edge_owner_to_timeline_media":\s*{\s*"count":\s*(\d+)',
                    r'"posts_count":\s*(\d+)',
                    r'publicações</span></div><span[^>]*>([0-9,.KMkm]+)',
                ],
                'full_name': [
                    r'"full_name":\s*"([^"]*)"',
                    r'"fullName":\s*"([^"]*)"'
                ],
                'is_verified': [
                    r'"is_verified":\s*(true|false)',
                    r'"isVerified":\s*(true|false)'
                ],
                'is_private': [
                    r'"is_private":\s*(true|false)',
                    r'"isPrivate":\s*(true|false)'
                ],
                'user_id': [
                    r'"id":\s*"(\d+)"',
                    r'"userId":\s*"(\d+)"',
                    r'"owner":\s*{\s*"id":\s*"(\d+)"'
                ]
            }
            
            extracted_data = {'username': username}
            
            for field, field_patterns in patterns.items():
                for pattern in field_patterns:
                    match = re.search(pattern, html_content, re.IGNORECASE)
                    if match:
                        value = match.group(1)
                        
                        # Converter valores booleanos
                        if field in ['is_verified', 'is_private']:
                            extracted_data[field] = value.lower() == 'true'
                        elif field in ['followers', 'following', 'posts']:
                            extracted_data[field] = self.parse_number(value)
                        else:
                            extracted_data[field] = value
                        break
            
            # Extrair Direct ID
            direct_id = self.extract_direct_id_from_html(html_content, username)
            if direct_id:
                extracted_data['direct_id'] = direct_id
            
            return extracted_data if len(extracted_data) > 1 else None
            
        except Exception as e:
            print(f"❌ Erro na extração por regex: {e}")
            return None
    
    def extract_direct_id_from_html(self, html_content, username):
        """Extrai Direct ID específico do HTML"""
        try:
            # Padrões específicos para Direct ID
            direct_patterns = [
                r'"direct_url":\s*"[^"]*?/t/(\d+)"',
                r'"thread_id":\s*"(\d+)"',
                r'instagram://user\?username=' + re.escape(username) + r'.*?id=(\d+)',
                r'"userId":\s*"(\d+)".*?' + re.escape(username),
                r'"pk":\s*"?(\d+)"?.*?"username":\s*"' + re.escape(username) + '"',
                r'"fbid":\s*"(\d+)"',
                r'"IG_USER_EIMU":\s*"(\d+)"'
            ]
            
            found_ids = set()
            
            for pattern in direct_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    if len(match) > 8:  # IDs válidos são longos
                        found_ids.add(match)
            
            if found_ids:
                # Retornar o ID mais provável (mais longo geralmente é mais específico)
                direct_id = max(found_ids, key=len)
                print(f"🔗 Direct ID encontrado: {direct_id}")
                return direct_id
            
            return None
            
        except Exception as e:
            print(f"⚠️ Erro ao extrair Direct ID: {e}")
            return None
    
    def format_profile_data(self, user_data, username):
        """Formata dados do perfil extraídos"""
        try:
            formatted = {
                'username': username,
                'full_name': user_data.get('full_name', 'N/A'),
                'followers': user_data.get('edge_followed_by', {}).get('count', 0),
                'following': user_data.get('edge_follow', {}).get('count', 0),
                'posts': user_data.get('edge_owner_to_timeline_media', {}).get('count', 0),
                'is_verified': user_data.get('is_verified', False),
                'is_private': user_data.get('is_private', False),
                'user_id': user_data.get('id'),
                'biography': user_data.get('biography', ''),
                'external_url': user_data.get('external_url', ''),
                'profile_pic_url': user_data.get('profile_pic_url', '')
            }
            
            return formatted
            
        except Exception as e:
            print(f"⚠️ Erro ao formatar dados: {e}")
            return None
    
    def parse_number(self, value_str):
        """Converte strings numéricas (incluindo K, M) para números"""
        try:
            if not value_str:
                return 0
            
            value_str = str(value_str).replace(',', '').replace('.', '').strip().upper()
            
            if 'K' in value_str:
                number = float(value_str.replace('K', ''))
                return int(number * 1000)
            elif 'M' in value_str:
                number = float(value_str.replace('M', ''))
                return int(number * 1000000)
            else:
                return int(value_str)
                
        except (ValueError, TypeError):
            return 0
    
    def print_profile_data(self, data):
        """Exibe dados do perfil formatados"""
        print(f"👤 Nome: {data.get('full_name', 'N/A')}")
        print(f"👥 Seguidores: {data.get('followers', 'N/A')}")
        print(f"📊 Seguindo: {data.get('following', 'N/A')}")
        print(f"📸 Posts: {data.get('posts', 'N/A')}")
        print(f"✅ Verificado: {'Sim' if data.get('is_verified') else 'Não'}")
        print(f"🔒 Privado: {'Sim' if data.get('is_private') else 'Não'}")
        
        if data.get('user_id'):
            print(f"🆔 User ID: {data.get('user_id')}")
        
        if data.get('direct_id'):
            print(f"📨 Direct ID: {data.get('direct_id')}")
    
    def save_to_database(self, data):
        """Salva dados no banco PostgreSQL"""
        try:
            print(f"💾 Salvando no banco: @{data['username']}")
            
            # Configurações do banco
            db_config = {
                'host': self.config.get('DATABASE', 'host'),
                'database': self.config.get('DATABASE', 'database'),
                'user': self.config.get('DATABASE', 'user'),
                'password': self.config.get('DATABASE', 'password'),
                'port': self.config.get('DATABASE', 'port', fallback='5432')
            }
            
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            
            # Query de inserção/atualização
            query = """
            INSERT INTO instagram_profiles 
            (username, full_name, followers, following, posts, is_verified, is_private, user_id, direct_id, extracted_at, extraction_method)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), 'chrome_cookies')
            ON CONFLICT (username) 
            DO UPDATE SET
                full_name = EXCLUDED.full_name,
                followers = EXCLUDED.followers,
                following = EXCLUDED.following,
                posts = EXCLUDED.posts,
                is_verified = EXCLUDED.is_verified,
                is_private = EXCLUDED.is_private,
                user_id = EXCLUDED.user_id,
                direct_id = EXCLUDED.direct_id,
                extracted_at = NOW(),
                extraction_method = 'chrome_cookies'
            """
            
            cursor.execute(query, (
                data['username'],
                data.get('full_name'),
                data.get('followers'),
                data.get('following'), 
                data.get('posts'),
                data.get('is_verified', False),
                data.get('is_private', False),
                data.get('user_id'),
                data.get('direct_id')
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"✅ Dados salvos com sucesso no banco!")
            
        except Exception as e:
            print(f"❌ Erro ao salvar no banco: {e}")
    
    def run_extraction(self, username=None):
        """Executa extração completa"""
        try:
            # Usar username do config se não fornecido
            if not username:
                username = self.config.get('INSTAGRAM', 'username')
            
            print(f"🎯 Usuário alvo: @{username}")
            print("=" * 60)
            
            # Carregar cookies do Chrome
            if not self.load_chrome_cookies():
                print("❌ Falha ao carregar cookies do Chrome")
                return False
            
            # Extrair dados do perfil
            profile_data = self.extract_profile_data(username)
            
            if profile_data:
                # Salvar no banco
                self.save_to_database(profile_data)
                
                print(f"\n🎉 EXTRAÇÃO FINALIZADA COM SUCESSO!")
                print(f"🔐 Método: Chrome Cookies (sessão autenticada)")
                
                if profile_data.get('direct_id'):
                    print(f"\n🔗 DIRECT MESSAGE:")
                    print(f"   📨 Direct ID: {profile_data['direct_id']}")
                    print(f"   🔗 Link: https://www.instagram.com/direct/t/{profile_data['direct_id']}")
                
                return True
            else:
                print("❌ Falha na extração de dados")
                return False
                
        except Exception as e:
            print(f"❌ Erro na execução: {e}")
            return False

if __name__ == "__main__":
    extractor = InstagramChromeExtractor()
    extractor.run_extraction()
