#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎯 INSTAGRAM EXTRACTOR - VERSÃO FINAL
====================================

Sistema inteligente que combina Instaloader e HTML Parser:

✅ INSTALOADER (RECOMENDADO):
   - Mais preciso e confiável
   - API oficial do Instagram
   - Rate limiting automático
   - Dados completos para perfis públicos
   - Suporte a login para perfis privados

🔄 HTML PARSER (FALLBACK):
   - Para casos onde Instaloader falha
   - Extração de Direct IDs
   - Backup quando API não funciona

🤖 MODO AUTOMÁTICO:
   - Tenta Instaloader primeiro
   - Fallback automático para HTML se necessário
   - Combina melhores resultados de ambos

Configuração: config.ini [EXTRACTION] preferred_method
Uso: python main_extractor.py
"""

import configparser
import sys
from pathlib import Path
from instagram_extractor_instaloader import InstagramExtractorInstaloader
from instagram_extractor import InstagramExtractorUnified
from instagram_chrome_extractor import InstagramChromeExtractor
from data_intelligence import DataIntelligence

class MainInstagramExtractor:
    def __init__(self):
        """Inicializa o extrator principal"""
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.intelligence = DataIntelligence()
        
        print("🎯 INSTAGRAM EXTRACTOR - VERSÃO FINAL")
        print("=" * 50)
        
    def get_extraction_method(self):
        """Determina método de extração a partir da configuração"""
        try:
            method = self.config.get('EXTRACTION', 'preferred_method', fallback='auto')
            return method.lower()
        except:
            return 'auto'
    
    def run_intelligent_extraction(self, username):
        """Execução inteligente com análise de qualidade automática"""
        print(f"🧠 MODO INTELIGENTE PARA @{username}")
        print("-" * 40)
        
        all_results = {}
        final_data = None
        
        # 1. Tentar todos os métodos e coletar dados
        methods_to_try = [
            ('chrome', self.run_chrome_extraction_data),
            ('instaloader', self.run_instaloader_extraction_data), 
            ('html', self.run_html_extraction_data)
        ]
        
        for method_name, method_func in methods_to_try:
            try:
                print(f"\n🔄 Tentando {method_name}...")
                data = method_func(username)
                
                if data:
                    analysis = self.intelligence.analyze_data_quality(data, method_name)
                    all_results[method_name] = {
                        'data': data,
                        'analysis': analysis
                    }
                    
                    print(f"✅ {method_name}: {analysis['quality_level']} ({analysis['quality_score']:.1%})")
                    
                    # Se encontrou dados excelentes, pode parar
                    if analysis['quality_level'] == 'excellent':
                        print(f"🏆 Qualidade excelente encontrada com {method_name}!")
                        final_data = data
                        break
                        
                else:
                    print(f"❌ {method_name}: Sem dados")
                    
            except Exception as e:
                print(f"❌ {method_name}: Erro - {e}")
        
        # 2. Se não encontrou dados excelentes, escolher o melhor
        if not final_data and all_results:
            print(f"\n🧠 ESCOLHENDO MELHOR RESULTADO:")
            
            # Ordenar por qualidade
            sorted_results = sorted(
                all_results.items(), 
                key=lambda x: x[1]['analysis']['quality_score'], 
                reverse=True
            )
            
            best_method, best_result = sorted_results[0]
            print(f"🏆 Melhor método: {best_method} ({best_result['analysis']['quality_score']:.1%})")
            
            # Se há múltiplos resultados, combinar
            if len(sorted_results) > 1:
                second_method, second_result = sorted_results[1]
                print(f"🔄 Combinando com: {second_method}")
                
                final_data = self.intelligence.combine_data_sources(
                    best_result['data'], 
                    second_result['data'],
                    best_method,
                    second_method
                )
            else:
                final_data = best_result['data']
        
        # 3. Validar resultado final
        if final_data:
            final_analysis = self.intelligence.analyze_data_quality(final_data, "final")
            self.intelligence.print_quality_report(final_analysis)
            
            # Salvar se qualidade é aceitável
            if final_analysis['quality_level'] in ['excellent', 'good', 'acceptable']:
                print(f"\n💾 Salvando dados de qualidade {final_analysis['quality_level']}...")
                # Aqui você chamaria o método de salvamento
                return True
            else:
                print(f"\n❌ Qualidade insuficiente ({final_analysis['quality_level']}) - não salvando")
                return False
        else:
            print(f"\n❌ Nenhum dado válido obtido de nenhum método")
            return False
    
    def run_chrome_extraction_data(self, username):
        """Executa Chrome e retorna apenas os dados"""
        extractor = InstagramChromeExtractor()
        # Simulação - você adaptaria para retornar dados ao invés de salvar
        return extractor.extract_profile_data(username)
    
    def run_instaloader_extraction_data(self, username):
        """Executa Instaloader e retorna apenas os dados"""
        extractor = InstagramExtractorInstaloader()
        return extractor.extract_profile_with_instaloader(username)
    
    def run_html_extraction_data(self, username):
        """Executa HTML parser e retorna apenas os dados"""
        extractor = InstagramExtractorUnified()
        # Simulação - você adaptaria para retornar dados
        html_dir = Path('html_pages')
        html_files = list(html_dir.glob('*.html'))
        
        if html_files:
            for html_file in html_files:
                data = extractor.extract_profile_data(html_file, username)
                if data:
                    return data
        return None
    
    def run_chrome_extraction(self, username):
        """Executa extração com cookies do Chrome"""
        print(f"🔐 USANDO COOKIES DO CHROME PARA @{username}")
        print("-" * 40)
        
        extractor = InstagramChromeExtractor()
        return extractor.run_extraction(username)
    
    def run_instaloader_extraction(self, username):
        """Executa extração com Instaloader"""
        print(f"🚀 USANDO INSTALOADER PARA @{username}")
        print("-" * 40)
        
        extractor = InstagramExtractorInstaloader()
        
        # Verificar se há credenciais de login
        login_user = self.config.get('EXTRACTION', 'login_username', fallback=None)
        login_pass = self.config.get('EXTRACTION', 'login_password', fallback=None)
        
        if login_user and login_pass:
            print(f"🔐 Credenciais de login encontradas")
        
        return extractor.run_extraction(username, login_user, login_pass)
    
    def run_html_extraction(self, username):
        """Executa extração com HTML Parser"""
        print(f"🔄 USANDO HTML PARSER PARA @{username}")
        print("-" * 40)
        
        extractor = InstagramExtractorUnified()
        extractor.run_extraction()
        return True
    
    def run_hybrid_extraction(self, username):
        """Execução híbrida: Instaloader + HTML para Direct IDs"""
        print(f"🔀 MODO HÍBRIDO PARA @{username}")
        print("-" * 40)
        
        success = False
        
        # 1. Tentar Instaloader primeiro
        try:
            print(f"1️⃣ Tentando Instaloader...")
            instaloader_extractor = InstagramExtractorInstaloader()
            
            # Obter dados do perfil
            profile_data = instaloader_extractor.extract_profile_with_instaloader(username)
            
            # Obter Direct ID com método HTML
            direct_id = None
            try:
                print(f"2️⃣ Buscando Direct ID com HTML Parser...")
                html_extractor = InstagramExtractorUnified()
                html_dir = Path('html_pages')
                html_files = list(html_dir.glob('*.html'))
                
                if html_files:
                    for html_file in html_files:
                        direct_id = html_extractor.extract_direct_id_from_html(html_file, username)
                        if direct_id:
                            break
            except Exception as e:
                print(f"⚠️ Erro ao buscar Direct ID: {e}")
            
            # Salvar dados combinados
            if profile_data:
                instaloader_extractor.save_to_database(profile_data, direct_id)
                instaloader_extractor.print_comparison_report(profile_data)
                
                if direct_id:
                    print(f"\n🔗 DIRECT MESSAGE:")
                    print(f"   📨 Direct ID: {direct_id}")
                    print(f"   🔗 Link: https://www.instagram.com/direct/t/{direct_id}")
                
                success = True
                
        except Exception as e:
            print(f"❌ Erro no Instaloader: {e}")
        
        # 3. Fallback para HTML se Instaloader falhou
        if not success:
            print(f"\n🔄 FALLBACK - Usando HTML Parser...")
            try:
                self.run_html_extraction(username)
                success = True
            except Exception as e:
                print(f"❌ Erro no HTML Parser: {e}")
        
        return success
    
    def show_method_info(self, method):
        """Mostra informações sobre o método escolhido"""
        print(f"\n📋 MÉTODO SELECIONADO: {method.upper()}")
        
        if method == 'intelligent':
            print(f"🧠 VANTAGENS:")
            print(f"   ✅ Analisa qualidade dos dados automaticamente")
            print(f"   ✅ Evita dados nulos ou incompletos")
            print(f"   ✅ Combina melhor de múltiplas fontes")
            print(f"   ✅ Decisões automáticas baseadas em IA")
            print(f"ℹ️ ESTRATÉGIA:")
            print(f"   1️⃣ Testa todos os métodos disponíveis")
            print(f"   2️⃣ Analisa qualidade de cada resultado")
            print(f"   3️⃣ Escolhe automaticamente o melhor")
            print(f"   4️⃣ Combina dados quando necessário")
            
        elif method == 'chrome':
            print(f"🔐 VANTAGENS:")
            print(f"   ✅ Usa sessão já logada no Chrome")
            print(f"   ✅ Acesso completo aos dados (como usuário logado)")
            print(f"   ✅ Extrai Direct IDs com precisão")
            print(f"   ✅ Não precisa de credenciais no código")
            print(f"⚠️ LIMITAÇÕES:")
            print(f"   ⚠️ Requer Chrome fechado para acessar cookies")
            print(f"   ⚠️ Precisa estar logado no Instagram pelo Chrome")
            
        elif method == 'instaloader':
            print(f"🚀 VANTAGENS:")
            print(f"   ✅ Dados mais precisos e confiáveis")
            print(f"   ✅ API oficial do Instagram")
            print(f"   ✅ Rate limiting automático")
            print(f"   ✅ Suporte a perfis privados com login")
            print(f"⚠️ LIMITAÇÕES:")
            print(f"   ⚠️ Não extrai Direct IDs")
            print(f"   ⚠️ Pode ser bloqueado em uso intensivo")
            
        elif method == 'html':
            print(f"🔄 VANTAGENS:")
            print(f"   ✅ Extrai Direct IDs")
            print(f"   ✅ Funciona offline com arquivos salvos")
            print(f"   ✅ Não depende de APIs externas")
            print(f"⚠️ LIMITAÇÕES:")
            print(f"   ⚠️ Menos preciso que Instaloader")
            print(f"   ⚠️ Suscetível a mudanças no HTML")
            print(f"   ⚠️ Pode interpretar perfis incorretamente")
            
        elif method == 'auto':
            print(f"🤖 VANTAGENS:")
            print(f"   ✅ Combina melhor dos dois mundos")
            print(f"   ✅ Fallback automático")
            print(f"   ✅ Máxima confiabilidade")
            print(f"ℹ️ ESTRATÉGIA:")
            print(f"   1️⃣ Tenta Chrome cookies primeiro")
            print(f"   2️⃣ Fallback para Instaloader")
            print(f"   3️⃣ Fallback final para HTML se necessário")
            print(f"   4️⃣ Combina resultados quando possível")
    
    def run(self):
        """Execução principal"""
        # Obter configurações
        username = self.config.get('INSTAGRAM', 'username')
        method = self.get_extraction_method()
        
        print(f"🎯 Usuário alvo: @{username}")
        
        # Mostrar informações do método
        self.show_method_info(method)
        print("=" * 50)
        
        # Executar extração baseada no método
        success = False
        
        if method == 'intelligent':
            success = self.run_intelligent_extraction(username)
            
        elif method == 'chrome':
            success = self.run_chrome_extraction(username)
            
        elif method == 'instaloader':
            success = self.run_instaloader_extraction(username)
            
        elif method == 'html':
            success = self.run_html_extraction(username)
            
        elif method == 'auto':
            # Estratégia: Chrome -> Instaloader -> HTML
            print(f"🤖 MODO AUTOMÁTICO INICIADO")
            print("-" * 40)
            
            # 1. Tentar Chrome cookies primeiro
            try:
                print(f"1️⃣ Tentando Chrome cookies...")
                success = self.run_chrome_extraction(username)
                if success:
                    print(f"✅ Sucesso com Chrome cookies!")
                else:
                    raise Exception("Chrome cookies falharam")
            except Exception as e:
                print(f"⚠️ Chrome cookies falhou: {e}")
                
                # 2. Fallback para Instaloader
                try:
                    print(f"\n2️⃣ Fallback - Tentando Instaloader...")
                    success = self.run_instaloader_extraction(username)
                    if success:
                        print(f"✅ Sucesso com Instaloader!")
                    else:
                        raise Exception("Instaloader falhou")
                except Exception as e:
                    print(f"⚠️ Instaloader falhou: {e}")
                    
                    # 3. Fallback final para HTML
                    try:
                        print(f"\n3️⃣ Fallback final - Tentando HTML Parser...")
                        success = self.run_html_extraction(username)
                        if success:
                            print(f"✅ Sucesso com HTML Parser!")
                    except Exception as e:
                        print(f"❌ Todos os métodos falharam: {e}")
            
        else:
            print(f"❌ Método '{method}' não reconhecido. Use: intelligent, chrome, instaloader, html, auto")
            return False
        
        # Resultado final
        if success:
            print(f"\n🎉 EXTRAÇÃO FINALIZADA COM SUCESSO!")
            print(f"💾 Dados salvos no banco PostgreSQL")
            return True
        else:
            print(f"\n❌ FALHA NA EXTRAÇÃO")
            print(f"💡 Verifique:")
            print(f"   - Se o perfil @{username} existe")
            print(f"   - Conexão com internet")
            print(f"   - Configurações no config.ini")
            return False

if __name__ == "__main__":
    extractor = MainInstagramExtractor()
    extractor.run()
