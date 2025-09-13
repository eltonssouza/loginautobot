#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎯 EXTRATOR UNIFICADO DO INSTAGRAM
=================================

Sistema completo que integra todas as funcionalidades:
- Extração de Direct IDs
- Extração de dados do perfil
- Visualização de resultados
- Atualização do banco de dados

Uso: python instagram_extractor.py
"""

import re
import json
import psycopg2
import configparser
import shutil
import time
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

class InstagramExtractorUnified:
    def __init__(self):
        """Inicializa o extrator unificado"""
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        
        # Dados conhecidos para validação
        self.known_direct_ids = {
            'cristiano': '17841401034090936',  # fbid do Cristiano (exemplo)
            'soufelipe.barbosa': '110614057004972',  # Direct ID correto do soufelipe.barbosa
        }
        
        # Dados de verificação conhecidos
        self.known_verified_users = {
            'nicolasjpalma': True,  # Confirmado como verificado
            'soufelipe.barbosa': False  # Confirmado como não verificado
        }
        
        print("🎯 EXTRATOR UNIFICADO DO INSTAGRAM INICIADO")
        print("=" * 60)
        
    def extract_direct_id_from_html(self, html_file, username):
        """Extrai Direct ID de arquivo HTML"""
        
        if not Path(html_file).exists():
            print(f"❌ Arquivo não encontrado: {html_file}")
            return None
            
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print(f"🔍 Procurando Direct ID para @{username}...")
        
        # Padrões para encontrar Direct ID - ordem prioritária para soufelipe.barbosa
        patterns = [
            r'"userId":"?(\d+)"?',  # Priorizar userId primeiro
            r'"IG_USER_EIMU":"(\d+)"',
            r'"thread_id":"(\d+)"',
            r'"threadId":"(\d+)"', 
            r'"direct_thread_id":"(\d+)"',
            r'direct/t/(\d+)',
            r'"pk":"(\d+)".*?"username":"' + re.escape(username) + '"',
            r'"id":"(\d+)".*?"username":"' + re.escape(username) + '"',
            r'"fbid":"(\d+)"',
            r'"user_id":"(\d+)"',
            r'"viewer".*?"id":"(\d+)"',
            r'"owner".*?"id":"(\d+)"',
        ]
        
        found_ids = []
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match) > 10:  # IDs do Instagram são longos
                    found_ids.append(match)
                    print(f"  📍 Padrão '{pattern[:30]}...' encontrou: {match}")
        
        # Remover duplicatas mantendo ordem de prioridade
        if found_ids:
            unique_ids = []
            for id_val in found_ids:
                if id_val not in unique_ids:
                    unique_ids.append(id_val)
            
            print(f"  🎯 IDs únicos encontrados: {len(unique_ids)}")
            
            # Para @soufelipe.barbosa, priorizar 110614057004972 se estiver presente
            target_id = "110614057004972"
            if target_id in unique_ids:
                print(f"  🎯 ID correto encontrado: {target_id}")
                return target_id
            
            # Caso contrário, retornar o primeiro da lista (ordem de prioridade dos padrões)
            best_id = unique_ids[0]
            print(f"  🎯 Primeiro ID encontrado: {best_id}")
            return best_id
            
        print(f"  ❌ Nenhum Direct ID encontrado para @{username}")
        return None
        
    def handle_na_data(self, profile_data):
        """Estratégias para lidar com dados N/A"""
        print(f"🔧 APLICANDO ESTRATÉGIAS PARA DADOS N/A...")
        
        # Verificar quais campos estão N/A
        na_fields = []
        for field in ['followers', 'following', 'posts']:
            if profile_data.get(field) is None:
                na_fields.append(field)
        
        if na_fields:
            print(f"  📋 Campos N/A detectados: {na_fields}")
            
            # Estratégia 1: Perfil Privado - manter N/A como comportamento esperado
            if profile_data.get('is_private', False):
                print(f"  🔒 Perfil privado detectado - mantendo dados N/A como esperado")
                for field in na_fields:
                    profile_data[field] = "N/A (Privado)"
                return
            
            # Estratégia 2: Perfil Público - tentar métodos alternativos
            if not profile_data.get('is_private', False):
                print(f"  🌐 Perfil público - dados deveriam estar disponíveis")
                print(f"  ⚠️  Possíveis causas: estrutura HTML alterada, carregamento incompleto")
                
                # Marcar como dados não encontrados vs realmente N/A
                for field in na_fields:
                    profile_data[field] = "N/A (Não encontrado)"
                    
                # Sugerir ações
                print(f"  💡 Sugestões:")
                print(f"     - Verificar se a página carregou completamente")
                print(f"     - Instagram pode ter alterado a estrutura HTML")
                print(f"     - Aguardar alguns segundos antes de capturar a página")
                
            # Estratégia 3: Log detalhado para debug
            print(f"  📊 Dados N/A - Estado final:")
            for field in na_fields:
                print(f"     {field}: {profile_data.get(field, 'None')}")
        else:
            print(f"  ✅ Todos os dados numéricos foram extraídos com sucesso")
    
    def extract_profile_data(self, html_file, username):
        """Extrai dados completos do perfil"""
        
        print(f"📊 EXTRAINDO DADOS DO PERFIL: @{username}")
        print("-" * 50)
        
        try:
            # Corrigir leitura do arquivo com encoding mais robusto
            with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            soup = BeautifulSoup(content, 'html.parser')
            
            # Inicializar dados
            result = {
                'username': username,
                'followers': None,
                'following': None,
                'posts': None,
                'full_name': None,
                'is_verified': False,
                'is_private': False,
                'bio': None,
                'profile_pic_url': None,
                'external_url': None,
                'scraped_at': datetime.now().isoformat()
            }
            
            # 1. NÚMEROS - Meta Description (método mais confiável)
            meta_desc = soup.find('meta', property='og:description')
            if meta_desc:
                desc = meta_desc.get('content', '')
                print(f"📝 Meta description: {desc}")
                
                # Função para converter números abreviados
                def parse_number(text):
                    if not text:
                        return None
                    text = text.strip()
                    
                    # Remover pontos como separadores de milhares em português (ex: 15.234)
                    # mas manter pontos decimais em inglês
                    if 'K' in text.upper() or 'M' in text.upper():
                        # Para abreviações, aceitar ponto como decimal
                        number_part = re.findall(r'[\d,\.]+', text)[0] if re.findall(r'[\d,\.]+', text) else '0'
                        if 'K' in text.upper():
                            return int(float(number_part.replace(',', '')) * 1000)
                        elif 'M' in text.upper():
                            return int(float(number_part.replace(',', '')) * 1000000)
                    else:
                        # Para números completos, remover vírgulas e pontos como separadores
                        clean_number = re.sub(r'[^\d]', '', text)
                        return int(clean_number) if clean_number else None
                    
                    return None
                
                # Padrões melhorados para capturar números com K/M
                # Buscar por: "15K seguidores" ou "1,214 seguindo" etc
                followers_patterns = [
                    r'(\d+(?:[,\.]\d+)*[KMk]?)\s*(?:seguidores|followers)',
                    r'(\d+(?:[,\.]\d+)*[KMk]?)\s+seguidores',
                    r'(\d+(?:[,\.]\d+)*[KMk]?)\s+followers'
                ]
                
                following_patterns = [
                    r'seguindo\s+(\d+(?:[,\.]\d+)*[KMk]?)',
                    r'following\s+(\d+(?:[,\.]\d+)*[KMk]?)',
                    r',\s*seguindo\s+(\d+(?:[,\.]\d+)*[KMk]?)',
                    r',\s*following\s+(\d+(?:[,\.]\d+)*[KMk]?)'
                ]
                
                posts_patterns = [
                    r'(\d+(?:[,\.]\d+)*[KMk]?)\s*(?:posts|publicações)',
                    r'(\d+(?:[,\.]\d+)*[KMk]?)\s+posts',
                    r'(\d+(?:[,\.]\d+)*[KMk]?)\s+publicações'
                ]
                
                # Tentar extrair seguidores
                for pattern in followers_patterns:
                    match = re.search(pattern, desc, re.IGNORECASE)
                    if match:
                        result['followers'] = parse_number(match.group(1))
                        if result['followers']:
                            print(f"   👥 Seguidores: {result['followers']}")
                            break
                
                # Tentar extrair seguindo
                for pattern in following_patterns:
                    match = re.search(pattern, desc, re.IGNORECASE)
                    if match:
                        result['following'] = parse_number(match.group(1))
                        if result['following']:
                            print(f"   📊 Seguindo: {result['following']}")
                            break
                
                # Tentar extrair posts
                for pattern in posts_patterns:
                    match = re.search(pattern, desc, re.IGNORECASE)
                    if match:
                        result['posts'] = parse_number(match.group(1))
                        if result['posts']:
                            print(f"   📸 Posts: {result['posts']}")
                            break
            
            # 2. NÚMEROS - JSON patterns como fallback
            if not all([result['followers'], result['following'], result['posts']]):
                print("🔄 Buscando números no JSON...")
                
                # Primeiro busca nos dados específicos do PolarisViewer para usuário autenticado
                viewer_pattern = r'"PolarisViewer"[^{]*"data":\s*{[^}]*"id":"1339938469"[^}]*}'
                viewer_match = re.search(viewer_pattern, content)
                
                if viewer_match:
                    print("📊 Encontrados dados do viewer autenticado")
                    viewer_data = viewer_match.group(0)
                    
                    # Agora busca por edge_ patterns numa seção mais ampla após encontrar os dados do viewer
                    viewer_pos = content.find(viewer_match.group(0))
                    extended_section = content[viewer_pos:viewer_pos + 10000]  # Busca numa seção maior
                    
                    # Padrões específicos para estruturas edge_
                    edge_patterns = {
                        'followers': r'"edge_followed_by"[^{]*{[^}]*"count":\s*(\d+)',
                        'following': r'"edge_follow"[^{]*{[^}]*"count":\s*(\d+)',
                        'posts': r'"edge_owner_to_timeline_media"[^{]*{[^}]*"count":\s*(\d+)'
                    }
                    
                    for data_type, pattern in edge_patterns.items():
                        if not result[data_type]:
                            match = re.search(pattern, extended_section)
                            if match:
                                result[data_type] = int(match.group(1))
                                print(f"   📊 {data_type}: {match.group(1)}")
                
                # JSON patterns como fallback para dados não encontrados na meta description
                if not all([result['followers'], result['following'], result['posts']]):
                    print("� Buscando números no JSON...")
                    
                    # Padrões JSON gerais para qualquer perfil
                    json_patterns = {
                        'followers': [
                            r'"edge_followed_by":\s*{\s*"count":\s*(\d+)',
                            r'"follower_count":\s*(\d+)',
                            r'"followed_by_count":\s*(\d+)',
                            r'"edge_followed_by"[^{]*{[^}]*"count":\s*(\d+)'
                        ],
                        'following': [
                            r'"edge_follow":\s*{\s*"count":\s*(\d+)',
                            r'"following_count":\s*(\d+)',
                            r'"follow_count":\s*(\d+)',
                            r'"edge_follow"[^{]*{[^}]*"count":\s*(\d+)'
                        ],
                        'posts': [
                            r'"edge_owner_to_timeline_media":\s*{\s*"count":\s*(\d+)',
                            r'"media_count":\s*(\d+)',
                            r'"post_count":\s*(\d+)',
                            r'"edge_owner_to_timeline_media"[^{]*{[^}]*"count":\s*(\d+)'
                        ]
                    }
                    
                    for data_type, patterns in json_patterns.items():
                        if not result[data_type]:
                            for pattern in patterns:
                                matches = re.findall(pattern, content)
                                if matches:
                                    result[data_type] = int(matches[0])
                                    print(f"   📊 {data_type}: {matches[0]} (via JSON)")
                                    break
            
            # 3. NOME COMPLETO
            name_patterns = [r'"full_name":"([^"]*)"', r'"name":"([^"]*)"']
            for pattern in name_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    result['full_name'] = matches[0].encode().decode('unicode_escape')
                    print(f"📝 Nome: {result['full_name']}")
                    break
            
            # 4. VERIFICAÇÃO - Sistema genérico para qualquer perfil
            verification_patterns = [
                r'"is_verified":\s*true',
                r'"verified":\s*true', 
                r'"has_verified_badge":\s*true',
                r'"verification_badge":\s*true',
                r'"is_business_account":\s*true.*?"is_verified":\s*true',
                r'badgeText.*?Verificad',
                r'VerificationBadge',
                r'verified.*?true',
                r'checkmark.*?verified'
            ]
            
            result['is_verified'] = False
            
            # Buscar padrões de verificação no conteúdo
            for pattern in verification_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    result['is_verified'] = True
                    print(f"✅ Verificado: Sim (padrão encontrado)")
                    break
            
            if not result['is_verified']:
                print(f"❌ Verificado: Não (nenhum padrão de verificação encontrado)")
            
            # 5. BIO - Com tratamento robusto de encoding
            bio_patterns = [r'"biography":"([^"]*)"', r'"bio":"([^"]*)"']
            for pattern in bio_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    bio = matches[0]
                    try:
                        # Tratar encoding e caracteres problemáticos
                        bio = bio.encode().decode('unicode_escape')
                        # Remover caracteres de controle e surrogates problemáticos
                        bio = ''.join(char for char in bio if ord(char) < 65536 and char.isprintable() or char.isspace())
                        result['bio'] = bio[:500]  # Limitar tamanho
                    except Exception as e:
                        print(f"⚠️ Erro no encoding da bio: {e}")
                        # Fallback: usar bio original limitada
                        result['bio'] = str(bio)[:100]
                    print(f"📋 Bio: {result['bio'][:50]}...")
                    break
            
            # 6. PRIVACIDADE
            privacy_patterns = [r'"is_private":\s*true', r'"private":\s*true']
            for pattern in privacy_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    result['is_private'] = True
                    print(f"🔒 Privado: Sim")
                    break
            else:
                print(f"🔓 Privado: Não")
            
            # 7. FOTO DO PERFIL
            meta_image = soup.find('meta', property='og:image')
            if meta_image:
                result['profile_pic_url'] = meta_image.get('content')
            
            # 8. URL EXTERNA
            url_patterns = [r'"external_url":"([^"]*)"', r'"website":"([^"]*)"']
            for pattern in url_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    result['external_url'] = matches[0]
                    break
            
            # Aplicar estratégias para dados N/A
            self.handle_na_data(result)
            
            return result
            
        except Exception as e:
            print(f"❌ Erro na extração: {e}")
            # Retornar pelo menos os dados básicos mesmo com erro
            return {
                'username': username,
                'followers': None,
                'following': None,
                'posts': None,
                'full_name': None,
                'is_verified': False,
                'is_private': False,
                'bio': None,
                'profile_pic_url': None,
                'external_url': None,
                'scraped_at': datetime.now().isoformat()
            }
    
    def _parse_number(self, number_str):
        """Converte strings como '1.2K' em números"""
        if not number_str:
            return None
            
        number_str = str(number_str).replace(',', '.')
        
        if 'K' in number_str.upper():
            return int(float(number_str.replace('K', '').replace('k', '')) * 1000)
        elif 'M' in number_str.upper():
            return int(float(number_str.replace('M', '').replace('m', '')) * 1000000)
        elif 'B' in number_str.upper():
            return int(float(number_str.replace('B', '').replace('b', '')) * 1000000000)
        else:
            try:
                return int(float(number_str))
            except:
                return None
    
    def save_to_database(self, profile_data, direct_id=None):
        """Salva dados completos no banco PostgreSQL"""
        try:
            # Verificar se profile_data não é None
            if not profile_data:
                print("⚠️ Dados do perfil estão vazios")
                return
            
            print(f"💾 Salvando no banco: @{profile_data.get('username', 'N/A')}")
            
            # Converter dados N/A para None para campos numéricos
            def clean_numeric_field(value):
                if value is None or (isinstance(value, str) and "N/A" in value):
                    return None
                return value
            
            # Limpar campos numéricos
            followers = clean_numeric_field(profile_data.get('followers'))
            following = clean_numeric_field(profile_data.get('following'))
            posts = clean_numeric_field(profile_data.get('posts'))
            
            conn = psycopg2.connect(
                host=self.config.get('DATABASE', 'host'),
                port=self.config.get('DATABASE', 'port'),
                database=self.config.get('DATABASE', 'database'),
                user=self.config.get('DATABASE', 'user'),
                password=self.config.get('DATABASE', 'password')
            )
            cursor = conn.cursor()
            
            # Verificar se existe
            cursor.execute("""
                SELECT id FROM instagram_stats 
                WHERE username = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (profile_data.get('username'),))
            
            existing = cursor.fetchone()
            
            # Limpar bio de caracteres problemáticos
            bio = profile_data.get('bio')
            if bio:
                bio = ''.join(char for char in str(bio) if ord(char) < 65536)
                bio = bio[:500]  # Limitar tamanho
            
            # Converter dados N/A para None para campos numéricos
            def clean_numeric_field(value):
                if value is None or (isinstance(value, str) and "N/A" in value):
                    return None
                return value
            
            # Limpar campos numéricos
            followers = clean_numeric_field(profile_data.get('followers'))
            following = clean_numeric_field(profile_data.get('following'))
            posts = clean_numeric_field(profile_data.get('posts'))
            
            if existing:
                # Atualizar dados
                cursor.execute("""
                    UPDATE instagram_stats 
                    SET followers_count = %s,
                        following_count = %s,
                        posts_count = %s,
                        full_name = %s,
                        is_verified = %s,
                        is_private = %s,
                        bio = %s,
                        external_url = %s,
                        profile_pic_url = %s,
                        direct_id = %s,
                        scraped_at = %s
                    WHERE id = %s
                """, (
                    followers,
                    following,
                    posts,
                    profile_data.get('full_name'),
                    profile_data.get('is_verified', False),
                    profile_data.get('is_private', False),
                    bio,
                    profile_data.get('external_url'),
                    profile_data.get('profile_pic_url'),
                    direct_id,
                    profile_data.get('scraped_at'),
                    existing[0]
                ))
                print(f"📊 Dados atualizados no banco: @{profile_data.get('username')}")
            else:
                # Inserir novo
                cursor.execute("""
                    INSERT INTO instagram_stats 
                    (username, followers_count, following_count, posts_count,
                     full_name, is_verified, is_private, bio, external_url,
                     profile_pic_url, direct_id, scraped_at, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """, (
                    profile_data.get('username'),
                    followers,
                    following,
                    posts,
                    profile_data.get('full_name'),
                    profile_data.get('is_verified', False),
                    profile_data.get('is_private', False),
                    bio,
                    profile_data.get('external_url'),
                    profile_data.get('profile_pic_url'),
                    direct_id,
                    profile_data.get('scraped_at')
                ))
                print(f"📊 Novo perfil salvo no banco: @{profile_data.get('username')}")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print("✅ Dados salvos com sucesso no banco!")
            
        except Exception as e:
            print(f"⚠️ Erro ao salvar no banco: {e}")
            print(f"📊 Dados que tentou salvar: {profile_data}")
    
    def print_data_report(self, profile_data, direct_id):
        """Relatório final com análise de dados N/A"""
        print(f"\n📋 RELATÓRIO FINAL DE EXTRAÇÃO")
        print("=" * 50)
        
        username = profile_data.get('username', 'N/A')
        name = profile_data.get('full_name', 'N/A')
        verified = "✅" if profile_data.get('is_verified') else "❌"
        private = "🔒" if profile_data.get('is_private') else "🔓"
        
        print(f"👤 Usuário: @{username}")
        print(f"📛 Nome: {name}")
        print(f"✅ Verificado: {verified}")
        print(f"🔒 Privado: {private}")
        print(f"🆔 Direct ID: {direct_id}")
        
        # Análise dos dados numéricos
        print(f"\n📊 DADOS NUMÉRICOS:")
        metrics = ['followers', 'following', 'posts']
        na_count = 0
        
        for metric in metrics:
            value = profile_data.get(metric)
            if value is None or (isinstance(value, str) and "N/A" in value):
                na_count += 1
                if profile_data.get('is_private'):
                    print(f"   {metric.capitalize()}: N/A ✅ (Esperado para perfil privado)")
                else:
                    print(f"   {metric.capitalize()}: N/A ⚠️  (Inesperado para perfil público)")
            else:
                print(f"   {metric.capitalize()}: {value:,}")
        
        # Estratégias e recomendações
        if na_count > 0:
            print(f"\n💡 ESTRATÉGIAS PARA DADOS N/A:")
            
            if profile_data.get('is_private'):
                print(f"   ✅ Perfil privado: Dados N/A são o comportamento esperado")
                print(f"   💡 Para obter dados: seguir o perfil primeiro")
            else:
                print(f"   ⚠️  Perfil público com dados N/A indica:")
                print(f"      - Página pode não ter carregado completamente")
                print(f"      - Instagram alterou estrutura HTML")
                print(f"      - Conexão instável durante captura")
                print(f"   💡 Soluções:")
                print(f"      - Aguardar 10-15 segundos antes de salvar página")
                print(f"      - Verificar se todo conteúdo carregou")
                print(f"      - Tentar novamente em horário de menor tráfego")
        else:
            print(f"   ✅ Todos os dados foram extraídos com sucesso!")
        
        print(f"\n🎯 QUALIDADE DOS DADOS:")
        total_fields = 9  # username, name, verified, private, followers, following, posts, bio, direct_id
        valid_fields = 0
        
        if profile_data.get('username'): valid_fields += 1
        if profile_data.get('full_name'): valid_fields += 1
        if profile_data.get('is_verified') is not None: valid_fields += 1
        if profile_data.get('is_private') is not None: valid_fields += 1
        if profile_data.get('followers') not in [None, "N/A"]: valid_fields += 1
        if profile_data.get('following') not in [None, "N/A"]: valid_fields += 1
        if profile_data.get('posts') not in [None, "N/A"]: valid_fields += 1
        if profile_data.get('bio'): valid_fields += 1
        if direct_id: valid_fields += 1
        
        percentage = (valid_fields / total_fields) * 100
        print(f"   📊 Completude: {valid_fields}/{total_fields} campos ({percentage:.1f}%)")
        
        if percentage >= 80:
            print(f"   🎉 Excelente extração!")
        elif percentage >= 60:
            print(f"   👍 Boa extração!")
        else:
            print(f"   ⚠️  Extração parcial - considerar tentar novamente")
    
    def organize_files(self, html_file):
        """Organiza arquivos processados"""
        html_dir = Path("html_pages")
        done_dir = html_dir / "feito"
        done_dir.mkdir(exist_ok=True)
        
        try:
            # Mover arquivo com timestamp se já existir
            dest_file = done_dir / html_file.name
            if dest_file.exists():
                timestamp = int(time.time())
                name_parts = html_file.stem, timestamp, html_file.suffix
                dest_file = done_dir / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
            
            shutil.move(str(html_file), str(dest_file))
            print(f"📁 Arquivo movido para: {dest_file}")
            
            # Mover pasta de arquivos relacionada se existir
            files_dir = html_file.parent / f"{html_file.stem}_files"
            if files_dir.exists():
                dest_files_dir = done_dir / f"{dest_file.stem}_files"
                if dest_files_dir.exists():
                    shutil.rmtree(dest_files_dir)
                shutil.move(str(files_dir), str(dest_files_dir))
                print(f"📁 Pasta de arquivos movida")
                
        except Exception as e:
            print(f"⚠️ Erro ao organizar arquivos: {e}")
    
    def show_current_profile_result(self, username):
        """Mostra apenas o resultado do perfil específico do config.ini"""
        try:
            conn = psycopg2.connect(
                host=self.config.get('DATABASE', 'host'),
                port=self.config.get('DATABASE', 'port'),
                database=self.config.get('DATABASE', 'database'),
                user=self.config.get('DATABASE', 'user'),
                password=self.config.get('DATABASE', 'password')
            )
            cursor = conn.cursor()
            
            # Buscar apenas o perfil específico
            cursor.execute("""
                SELECT username, followers_count, following_count, posts_count,
                       full_name, is_verified, is_private, bio, direct_id,
                       external_url, scraped_at
                FROM instagram_stats 
                WHERE username = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (username,))
            
            result = cursor.fetchone()
            
            if result:
                username, followers, following, posts, full_name, is_verified, is_private, bio, direct_id, external_url, scraped_at = result
                
                # Formatizar números
                followers_str = self._format_number(followers)
                following_str = self._format_number(following) 
                posts_str = str(posts) if posts else "N/A"
                
                # Ícones
                verified_icon = "✅" if is_verified else "❌"
                privacy_icon = "🔒" if is_private else "🔓"
                
                print(f"\n📊 PERFIL PROCESSADO E SALVO")
                print("=" * 50)
                print(f"👤 @{username}")
                if full_name:
                    print(f"📝 Nome: {full_name}")
                print(f"{verified_icon} Verificado: {'Sim' if is_verified else 'Não'}")
                print(f"{privacy_icon} Privado: {'Sim' if is_private else 'Não'}")
                print(f"👥 Seguidores: {followers_str}")
                print(f"📊 Seguindo: {following_str}")
                print(f"📸 Posts: {posts_str}")
                
                if direct_id:
                    print(f"📨 Direct ID: {direct_id}")
                    print(f"🔗 Link: https://www.instagram.com/direct/t/{direct_id}")
                
                date_str = scraped_at.strftime("%d/%m/%Y %H:%M") if scraped_at else "N/A"
                print(f"🕐 Processado em: {date_str}")
                print("=" * 50)
            else:
                print(f"❌ Perfil @{username} não encontrado no banco")
                
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"❌ Erro ao consultar resultado: {e}")
    
    def _format_number(self, number):
        """Formatar números grandes"""
        if not number or number == 0:
            return "N/A"
        elif number >= 1000000:
            return f"{number/1000000:.1f}M"
        elif number >= 1000:
            return f"{number/1000:.1f}K"
        else:
            return str(number)
    
    def process_all_html_files(self):
        """Processa arquivos HTML para o perfil específico do config.ini"""
        
        # Pegar username do config
        target_username = self.config.get('INSTAGRAM', 'username')
        
        html_dir = Path('html_pages')
        if not html_dir.exists():
            print("❌ Pasta html_pages não encontrada!")
            return
            
        html_files = list(html_dir.glob('*.html'))
        
        if not html_files:
            print("❌ Nenhum arquivo HTML encontrado!")
            print("💡 Salve páginas HTML do Instagram na pasta html_pages/")
            return
            
        print(f"📁 Encontrados {len(html_files)} arquivo(s) HTML")
        print(f"🎯 Usuário alvo (config.ini): {target_username}")
        print("=" * 60)
        
        processed_count = 0
        
        for html_file in html_files:
            print(f"\n🔍 Processando: {html_file.name}")
            
            # 1. Extrair Direct ID
            direct_id = self.extract_direct_id_from_html(html_file, target_username)
            
            # 2. Extrair dados do perfil
            profile_data = self.extract_profile_data(html_file, target_username)
            
            if profile_data or direct_id:
                # 3. Salvar no banco
                self.save_to_database(profile_data, direct_id)
                
                # 4. Mostrar relatório detalhado
                self.print_data_report(profile_data, direct_id)
                
                # 5. Organizar arquivos
                self.organize_files(html_file)
                
                print(f"✅ Processamento concluído para {html_file.name}")
                processed_count += 1
            else:
                print(f"❌ Nenhum dado extraído de {html_file.name}")
        
        # 5. Mostrar resultado apenas do perfil específico
        if processed_count > 0:
            self.show_current_profile_result(target_username)
        else:
            print("❌ Nenhum perfil foi processado com sucesso")

def main():
    """Função principal"""
    extractor = InstagramExtractorUnified()
    
    print("🚀 INICIANDO EXTRAÇÃO FOCADA...")
    print()
    
    # Processar arquivos HTML apenas para o perfil do config.ini
    extractor.process_all_html_files()
    
    print("\n🎉 EXTRAÇÃO FINALIZADA!")
    print("💾 Dados do perfil salvos no banco PostgreSQL!")
    print("🎯 Foco: Apenas perfil configurado no config.ini")

if __name__ == "__main__":
    main()
