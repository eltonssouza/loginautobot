#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 EXTRATOR INSTAGRAM COM INSTALOADER
====================================

Sistema híbrido que combina:
- Instaloader para dados robustos
- Sistema atual para Direct IDs
- Fallback para HTML parsing

Vantagens do Instaloader:
✅ Mais estável que parsing HTML
✅ Acesso a perfis privados (com login)
✅ Rate limiting automático
✅ Dados mais precisos
✅ Menos quebras por mudanças no Instagram

Uso: python instagram_extractor_instaloader.py
"""

import instaloader
import configparser
import psycopg2
import time
import json
from pathlib import Path
from datetime import datetime
from instagram_extractor import InstagramExtractorUnified

class InstagramExtractorInstaloader:
    def __init__(self):
        """Inicializa o extrator com Instaloader"""
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        
        # Inicializar Instaloader
        self.loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            quiet=True
        )
        
        # Sistema atual para fallback
        self.fallback_extractor = InstagramExtractorUnified()
        
        print("🚀 EXTRATOR INSTAGRAM COM INSTALOADER INICIADO")
        print("=" * 60)
    
    def authenticate(self, username=None, password=None):
        """Autenticação opcional para acessar perfis privados"""
        try:
            if username and password:
                print(f"🔐 Fazendo login como: {username}")
                self.loader.login(username, password)
                print("✅ Login realizado com sucesso!")
                return True
            else:
                print("ℹ️ Executando sem autenticação (apenas perfis públicos)")
                return False
        except Exception as e:
            print(f"❌ Erro no login: {e}")
            print("ℹ️ Continuando sem autenticação...")
            return False
    
    def extract_profile_with_instaloader(self, username):
        """Extrai dados do perfil usando Instaloader"""
        try:
            print(f"📊 EXTRAINDO COM INSTALOADER: @{username}")
            print("-" * 50)
            
            # Carregar perfil
            profile = instaloader.Profile.from_username(self.loader.context, username)
            
            # Rate limiting respeitoso
            time.sleep(2)
            
            # Extrair dados
            profile_data = {
                'username': profile.username,
                'full_name': profile.full_name,
                'followers': profile.followers,
                'following': profile.followees,
                'posts': profile.mediacount,
                'is_verified': profile.is_verified,
                'is_private': profile.is_private,
                'bio': profile.biography,
                'external_url': profile.external_url,
                'profile_pic_url': profile.profile_pic_url,
                'user_id': profile.userid,  # ID numérico do Instagram
                'scraped_at': datetime.now().isoformat(),
                'extraction_method': 'instaloader'
            }
            
            # Log dos dados extraídos
            print(f"✅ Dados extraídos com Instaloader:")
            print(f"   👤 Nome: {profile_data['full_name']}")
            print(f"   👥 Seguidores: {profile_data['followers']:,}")
            print(f"   📊 Seguindo: {profile_data['following']:,}")
            print(f"   📸 Posts: {profile_data['posts']:,}")
            print(f"   ✅ Verificado: {'Sim' if profile_data['is_verified'] else 'Não'}")
            print(f"   🔒 Privado: {'Sim' if profile_data['is_private'] else 'Não'}")
            print(f"   🆔 User ID: {profile_data['user_id']}")
            
            return profile_data
            
        except instaloader.exceptions.ProfileNotExistsException:
            print(f"❌ Perfil @{username} não existe")
            return None
            
        except instaloader.exceptions.LoginRequiredException:
            print(f"🔐 Perfil @{username} requer login para visualização")
            return None
            
        except instaloader.exceptions.PrivateProfileNotFollowedException:
            print(f"🔒 Perfil @{username} é privado e você não o segue")
            # Para perfis privados, retornar dados básicos
            try:
                profile = instaloader.Profile.from_username(self.loader.context, username)
                return {
                    'username': profile.username,
                    'full_name': profile.full_name,
                    'followers': None,  # N/A para privados
                    'following': None,  # N/A para privados
                    'posts': None,      # N/A para privados
                    'is_verified': profile.is_verified,
                    'is_private': True,
                    'bio': profile.biography if hasattr(profile, 'biography') else None,
                    'external_url': None,
                    'profile_pic_url': profile.profile_pic_url,
                    'user_id': profile.userid,
                    'scraped_at': datetime.now().isoformat(),
                    'extraction_method': 'instaloader_limited'
                }
            except:
                return None
                
        except Exception as e:
            print(f"❌ Erro no Instaloader: {e}")
            return None
    
    def get_direct_id_fallback(self, username):
        """Usa sistema atual para extrair Direct ID"""
        try:
            print(f"🔍 Buscando Direct ID com método fallback...")
            
            html_dir = Path('html_pages')
            html_files = list(html_dir.glob('*.html'))
            
            if html_files:
                for html_file in html_files:
                    direct_id = self.fallback_extractor.extract_direct_id_from_html(html_file, username)
                    if direct_id:
                        print(f"✅ Direct ID encontrado: {direct_id}")
                        return direct_id
            
            print("⚠️ Direct ID não encontrado nos arquivos HTML")
            return None
            
        except Exception as e:
            print(f"❌ Erro ao buscar Direct ID: {e}")
            return None
    
    def save_to_database(self, profile_data, direct_id=None):
        """Salva dados no banco PostgreSQL"""
        try:
            if not profile_data:
                print("⚠️ Dados do perfil estão vazios")
                return
            
            print(f"💾 Salvando no banco: @{profile_data.get('username', 'N/A')}")
            
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
            
            # Limpar bio
            bio = profile_data.get('bio')
            if bio:
                bio = ''.join(char for char in str(bio) if ord(char) < 65536)
                bio = bio[:500]
            
            if existing:
                # Atualizar
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
                        direct_id = COALESCE(%s, direct_id),
                        scraped_at = %s
                    WHERE id = %s
                """, (
                    profile_data.get('followers'),
                    profile_data.get('following'),
                    profile_data.get('posts'),
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
                    profile_data.get('followers'),
                    profile_data.get('following'),
                    profile_data.get('posts'),
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
    
    def print_comparison_report(self, instaloader_data, fallback_data=None):
        """Relatório comparativo entre métodos"""
        print(f"\n📊 RELATÓRIO DE EXTRAÇÃO COM INSTALOADER")
        print("=" * 60)
        
        if not instaloader_data:
            print("❌ Falha na extração com Instaloader")
            if fallback_data:
                print("🔄 Dados do método fallback serão usados")
            return
        
        username = instaloader_data.get('username', 'N/A')
        name = instaloader_data.get('full_name', 'N/A')
        verified = "✅" if instaloader_data.get('is_verified') else "❌"
        private = "🔒" if instaloader_data.get('is_private') else "🔓"
        method = instaloader_data.get('extraction_method', 'instaloader')
        
        print(f"👤 Usuário: @{username}")
        print(f"📛 Nome: {name}")
        print(f"✅ Verificado: {verified}")
        print(f"🔒 Privado: {private}")
        print(f"🔧 Método: {method}")
        
        # Dados numéricos
        print(f"\n📊 DADOS NUMÉRICOS (INSTALOADER):")
        followers = instaloader_data.get('followers')
        following = instaloader_data.get('following')
        posts = instaloader_data.get('posts')
        
        if followers is not None:
            print(f"   👥 Seguidores: {followers:,}")
        else:
            print(f"   👥 Seguidores: N/A {'✅ (Privado)' if private == '🔒' else '⚠️'}")
            
        if following is not None:
            print(f"   📊 Seguindo: {following:,}")
        else:
            print(f"   📊 Seguindo: N/A {'✅ (Privado)' if private == '🔒' else '⚠️'}")
            
        if posts is not None:
            print(f"   📸 Posts: {posts:,}")
        else:
            print(f"   📸 Posts: N/A {'✅ (Privado)' if private == '🔒' else '⚠️'}")
        
        # Vantagens do Instaloader
        print(f"\n🚀 VANTAGENS DO INSTALOADER:")
        print(f"   ✅ Dados obtidos via API interna (mais confiável)")
        print(f"   ✅ Rate limiting automático")
        print(f"   ✅ Menos suscetível a mudanças no HTML")
        print(f"   ✅ ID numérico oficial: {instaloader_data.get('user_id', 'N/A')}")
        
        if instaloader_data.get('is_private') and followers is None:
            print(f"\n💡 PERFIL PRIVADO:")
            print(f"   🔐 Para obter dados completos: faça login e siga o perfil")
            print(f"   📝 Configure credenciais no código para autenticação")
    
    def run_extraction(self, username=None, login_username=None, login_password=None):
        """Execução principal da extração"""
        
        # Usar username do config se não fornecido
        if not username:
            username = self.config.get('INSTAGRAM', 'username')
        
        print(f"🎯 Usuário alvo: @{username}")
        print("=" * 60)
        
        # Autenticação opcional
        if login_username and login_password:
            self.authenticate(login_username, login_password)
        
        # 1. Extração principal com Instaloader
        instaloader_data = self.extract_profile_with_instaloader(username)
        
        # 2. Buscar Direct ID (método fallback)
        direct_id = self.get_direct_id_fallback(username)
        
        # 3. Fallback para método HTML se Instaloader falhar
        fallback_data = None
        if not instaloader_data:
            print(f"\n🔄 TENTANDO MÉTODO FALLBACK (HTML)...")
            # Usar sistema atual como fallback
            html_dir = Path('html_pages')
            html_files = list(html_dir.glob('*.html'))
            
            if html_files:
                for html_file in html_files:
                    fallback_data = self.fallback_extractor.extract_profile_data(html_file, username)
                    if fallback_data:
                        break
        
        # 4. Determinar dados finais
        final_data = instaloader_data or fallback_data
        
        if final_data:
            # 5. Salvar no banco
            self.save_to_database(final_data, direct_id)
            
            # 6. Relatório
            self.print_comparison_report(instaloader_data, fallback_data)
            
            if direct_id:
                print(f"\n🔗 DIRECT MESSAGE:")
                print(f"   📨 Direct ID: {direct_id}")
                print(f"   🔗 Link: https://www.instagram.com/direct/t/{direct_id}")
            
            print(f"\n🎉 EXTRAÇÃO FINALIZADA COM SUCESSO!")
            return True
        else:
            print(f"\n❌ FALHA NA EXTRAÇÃO:")
            print(f"   - Instaloader falhou")
            print(f"   - Método fallback falhou")
            print(f"   - Verifique se o perfil existe")
            return False

if __name__ == "__main__":
    extractor = InstagramExtractorInstaloader()
    
    # Exemplo de uso básico (sem login)
    extractor.run_extraction()
    
    # Exemplo com login (descomente e configure):
    # extractor.run_extraction(
    #     login_username="seu_usuario",
    #     login_password="sua_senha"
    # )
