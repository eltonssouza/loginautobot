#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧠 SISTEMA DE VALIDAÇÃO E INTELIGÊNCIA DE DADOS
===============================================

Módulo que adiciona inteligência ao sistema para:
- Validar qualidade dos dados extraídos
- Decidir automaticamente quando usar fallback
- Combinar dados de múltiplas fontes
- Evitar dados nulos ou incompletos
"""

class DataIntelligence:
    def __init__(self):
        """Inicializa o sistema de inteligência de dados"""
        self.quality_thresholds = {
            'excellent': 0.9,   # 90%+ dos campos válidos
            'good': 0.7,        # 70%+ dos campos válidos  
            'acceptable': 0.5,  # 50%+ dos campos válidos
            'poor': 0.3         # 30%+ dos campos válidos
        }
        
        # Campos obrigatórios para um perfil válido
        self.essential_fields = [
            'username', 'full_name', 'followers', 'following', 'posts'
        ]
        
        # Campos opcionais mas importantes
        self.optional_fields = [
            'is_verified', 'is_private', 'user_id', 'direct_id', 'biography'
        ]
    
    def analyze_data_quality(self, data, method_name="unknown"):
        """Analisa a qualidade dos dados extraídos"""
        if not data:
            return {
                'quality_score': 0.0,
                'quality_level': 'invalid',
                'missing_essential': self.essential_fields,
                'missing_optional': self.optional_fields,
                'valid_fields': 0,
                'total_fields': len(self.essential_fields) + len(self.optional_fields),
                'method': method_name,
                'should_use_fallback': True,
                'issues': ['Dados completamente nulos']
            }
        
        valid_fields = 0
        total_fields = len(self.essential_fields) + len(self.optional_fields)
        missing_essential = []
        missing_optional = []
        issues = []
        
        # Verificar campos essenciais
        for field in self.essential_fields:
            value = data.get(field)
            if self.is_valid_value(value, field):
                valid_fields += 1
            else:
                missing_essential.append(field)
                if field in ['followers', 'following', 'posts']:
                    issues.append(f"Campo numérico '{field}' é nulo ou inválido")
                else:
                    issues.append(f"Campo essencial '{field}' está ausente")
        
        # Verificar campos opcionais
        for field in self.optional_fields:
            value = data.get(field)
            if self.is_valid_value(value, field):
                valid_fields += 1
            else:
                missing_optional.append(field)
        
        # Calcular score de qualidade
        quality_score = valid_fields / total_fields
        
        # Determinar nível de qualidade
        quality_level = self.get_quality_level(quality_score)
        
        # Decidir se deve usar fallback
        should_use_fallback = self.should_use_fallback(data, quality_score, missing_essential)
        
        # Verificações específicas de qualidade
        if data.get('followers') == 0 and data.get('following') == 0 and data.get('posts') == 0:
            issues.append("Todos os contadores são zero (possível perfil privado ou erro)")
            should_use_fallback = True
        
        if data.get('full_name') in [None, '', 'N/A']:
            issues.append("Nome completo ausente")
        
        if not data.get('user_id'):
            issues.append("User ID ausente (importante para Direct Messages)")
        
        return {
            'quality_score': quality_score,
            'quality_level': quality_level,
            'missing_essential': missing_essential,
            'missing_optional': missing_optional,
            'valid_fields': valid_fields,
            'total_fields': total_fields,
            'method': method_name,
            'should_use_fallback': should_use_fallback,
            'issues': issues
        }
    
    def is_valid_value(self, value, field_name):
        """Verifica se um valor é válido para um campo específico"""
        # Valores claramente inválidos
        if value is None or value == '' or value == 'N/A':
            return False
        
        # Campos numéricos
        if field_name in ['followers', 'following', 'posts']:
            if isinstance(value, (int, float)) and value >= 0:
                return True
            if isinstance(value, str) and value.isdigit():
                return True
            return False
        
        # Campos booleanos
        if field_name in ['is_verified', 'is_private']:
            return isinstance(value, bool)
        
        # Campos de texto
        if field_name in ['username', 'full_name', 'user_id', 'direct_id']:
            return isinstance(value, str) and len(value.strip()) > 0
        
        # Outros campos (biografia, URLs, etc.)
        return True
    
    def get_quality_level(self, score):
        """Determina o nível de qualidade baseado no score"""
        if score >= self.quality_thresholds['excellent']:
            return 'excellent'
        elif score >= self.quality_thresholds['good']:
            return 'good'
        elif score >= self.quality_thresholds['acceptable']:
            return 'acceptable'
        elif score >= self.quality_thresholds['poor']:
            return 'poor'
        else:
            return 'invalid'
    
    def should_use_fallback(self, data, quality_score, missing_essential):
        """Decide se deve usar método fallback"""
        # Se muitos campos essenciais estão ausentes
        if len(missing_essential) >= 3:
            return True
        
        # Se qualidade é muito baixa
        if quality_score < self.quality_thresholds['acceptable']:
            return True
        
        # Se campos numéricos são todos zero (possível erro)
        numeric_fields = ['followers', 'following', 'posts']
        zero_count = sum(1 for field in numeric_fields if data.get(field, 0) == 0)
        if zero_count == len(numeric_fields) and data.get('is_private') != True:
            return True
        
        # Se não há Direct ID e é importante
        if not data.get('direct_id') and not data.get('user_id'):
            return True
        
        return False
    
    def combine_data_sources(self, primary_data, fallback_data, primary_method="primary", fallback_method="fallback"):
        """Combina dados de múltiplas fontes inteligentemente"""
        if not primary_data and not fallback_data:
            return None
        
        if not primary_data:
            return fallback_data
        
        if not fallback_data:
            return primary_data
        
        # Analisar qualidade de ambas as fontes
        primary_analysis = self.analyze_data_quality(primary_data, primary_method)
        fallback_analysis = self.analyze_data_quality(fallback_data, fallback_method)
        
        print(f"\n🧠 ANÁLISE DE QUALIDADE DOS DADOS:")
        print(f"📊 {primary_method}: {primary_analysis['quality_level']} ({primary_analysis['quality_score']:.1%})")
        print(f"📊 {fallback_method}: {fallback_analysis['quality_level']} ({fallback_analysis['quality_score']:.1%})")
        
        # Se primary tem qualidade excelente, usar primary
        if primary_analysis['quality_level'] in ['excellent', 'good']:
            print(f"✅ Usando dados do {primary_method} (qualidade satisfatória)")
            return self.merge_best_fields(primary_data, fallback_data, primary_method)
        
        # Se fallback tem qualidade melhor, usar fallback
        if fallback_analysis['quality_score'] > primary_analysis['quality_score']:
            print(f"🔄 Usando dados do {fallback_method} (qualidade superior)")
            return self.merge_best_fields(fallback_data, primary_data, fallback_method)
        
        # Caso contrário, combinar o melhor dos dois
        print(f"🔀 Combinando melhor de ambos os métodos")
        return self.merge_best_fields(primary_data, fallback_data, "combined")
    
    def merge_best_fields(self, primary_data, secondary_data, method_name):
        """Combina os melhores campos de duas fontes"""
        merged_data = primary_data.copy()
        
        # Para cada campo, usar o melhor valor disponível
        all_fields = set(primary_data.keys()) | set(secondary_data.keys())
        
        for field in all_fields:
            primary_value = primary_data.get(field)
            secondary_value = secondary_data.get(field)
            
            # Se primary não tem o campo, usar secondary
            if not self.is_valid_value(primary_value, field) and self.is_valid_value(secondary_value, field):
                merged_data[field] = secondary_value
                print(f"   🔄 {field}: usando valor do método secundário")
            
            # Para campos numéricos, usar o maior valor não-zero
            elif field in ['followers', 'following', 'posts']:
                primary_num = self.safe_int(primary_value)
                secondary_num = self.safe_int(secondary_value)
                
                if primary_num == 0 and secondary_num > 0:
                    merged_data[field] = secondary_num
                    print(f"   📊 {field}: {secondary_num} (método secundário tinha dados)")
        
        # Adicionar metadados
        merged_data['extraction_method'] = method_name
        merged_data['data_quality'] = self.analyze_data_quality(merged_data, method_name)
        
        return merged_data
    
    def safe_int(self, value):
        """Converte valor para int de forma segura"""
        try:
            if isinstance(value, (int, float)):
                return int(value)
            if isinstance(value, str) and value.isdigit():
                return int(value)
            return 0
        except:
            return 0
    
    def print_quality_report(self, analysis):
        """Imprime relatório detalhado de qualidade"""
        print(f"\n🧠 RELATÓRIO DE QUALIDADE DE DADOS")
        print(f"=" * 50)
        print(f"🎯 Método: {analysis['method']}")
        print(f"📊 Score de Qualidade: {analysis['quality_score']:.1%}")
        print(f"🏆 Nível: {analysis['quality_level'].upper()}")
        print(f"✅ Campos válidos: {analysis['valid_fields']}/{analysis['total_fields']}")
        
        if analysis['missing_essential']:
            print(f"❌ Campos essenciais ausentes: {', '.join(analysis['missing_essential'])}")
        
        if analysis['issues']:
            print(f"\n⚠️ PROBLEMAS IDENTIFICADOS:")
            for issue in analysis['issues']:
                print(f"   • {issue}")
        
        if analysis['should_use_fallback']:
            print(f"\n🔄 RECOMENDAÇÃO: Usar método fallback")
        else:
            print(f"\n✅ RECOMENDAÇÃO: Dados são aceitáveis")
        
        print(f"=" * 50)

# Exemplo de uso
if __name__ == "__main__":
    intelligence = DataIntelligence()
    
    # Teste com dados de qualidade variada
    test_data_good = {
        'username': 'soufelipe.barbosa',
        'full_name': 'Felipe Barbosa',
        'followers': 439,
        'following': 647,
        'posts': 119,
        'is_verified': False,
        'is_private': False,
        'user_id': '1339938469'
    }
    
    test_data_poor = {
        'username': 'soufelipe.barbosa',
        'full_name': None,
        'followers': 0,
        'following': 0,
        'posts': 0,
        'is_verified': None,
        'is_private': None
    }
    
    print("🧠 TESTE DE ANÁLISE DE QUALIDADE")
    print("=" * 50)
    
    analysis_good = intelligence.analyze_data_quality(test_data_good, "instaloader")
    intelligence.print_quality_report(analysis_good)
    
    analysis_poor = intelligence.analyze_data_quality(test_data_poor, "html_parser")
    intelligence.print_quality_report(analysis_poor)
    
    # Teste de combinação
    combined = intelligence.combine_data_sources(test_data_poor, test_data_good, "html_parser", "instaloader")
    if combined:
        combined_analysis = intelligence.analyze_data_quality(combined, "combined")
        intelligence.print_quality_report(combined_analysis)
