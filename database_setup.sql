-- 🗄️ ESTRUTURA DO BANCO POSTGRESQL
-- ===================================

-- Criar banco de dados (executar como superuser)
-- CREATE DATABASE instagram_followers;

-- Conectar ao banco e executar:

-- Tabela principal de perfis do Instagram
CREATE TABLE IF NOT EXISTS instagram_profiles (
    id SERIAL PRIMARY KEY,
    
    -- Dados básicos do perfil
    username VARCHAR(150) UNIQUE NOT NULL,
    full_name VARCHAR(300),
    biography TEXT,
    external_url VARCHAR(500),
    profile_pic_url VARCHAR(500),
    
    -- Estatísticas
    followers INTEGER DEFAULT 0,
    following INTEGER DEFAULT 0,
    posts INTEGER DEFAULT 0,
    
    -- Status da conta
    is_verified BOOLEAN DEFAULT FALSE,
    is_private BOOLEAN DEFAULT FALSE,
    is_business BOOLEAN DEFAULT FALSE,
    
    -- Identificadores únicos
    user_id VARCHAR(50),
    direct_id VARCHAR(50),
    
    -- Metadados de extração
    extracted_at TIMESTAMP DEFAULT NOW(),
    extraction_method VARCHAR(50) DEFAULT 'unknown',
    data_quality_score INTEGER DEFAULT 0,
    
    -- Dados adicionais em JSON
    additional_data JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices para otimização
CREATE INDEX IF NOT EXISTS idx_instagram_profiles_username ON instagram_profiles(username);
CREATE INDEX IF NOT EXISTS idx_instagram_profiles_user_id ON instagram_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_instagram_profiles_direct_id ON instagram_profiles(direct_id);
CREATE INDEX IF NOT EXISTS idx_instagram_profiles_extracted_at ON instagram_profiles(extracted_at);
CREATE INDEX IF NOT EXISTS idx_instagram_profiles_quality_score ON instagram_profiles(data_quality_score);

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_instagram_profiles_updated_at 
    BEFORE UPDATE ON instagram_profiles 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Tabela de histórico de extrações
CREATE TABLE IF NOT EXISTS extraction_history (
    id SERIAL PRIMARY KEY,
    username VARCHAR(150) NOT NULL,
    extraction_method VARCHAR(50) NOT NULL,
    data_quality_score INTEGER DEFAULT 0,
    success BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    execution_time FLOAT DEFAULT 0,
    extracted_at TIMESTAMP DEFAULT NOW()
);

-- Índice para histórico
CREATE INDEX IF NOT EXISTS idx_extraction_history_username ON extraction_history(username);
CREATE INDEX IF NOT EXISTS idx_extraction_history_extracted_at ON extraction_history(extracted_at);

-- Tabela de configurações do sistema
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Inserir configurações padrão
INSERT INTO system_config (config_key, config_value, description) VALUES
('min_quality_threshold', '70', 'Pontuação mínima de qualidade aceitável')
ON CONFLICT (config_key) DO NOTHING;

INSERT INTO system_config (config_key, config_value, description) VALUES
('excellent_quality_threshold', '90', 'Pontuação para qualidade excelente')
ON CONFLICT (config_key) DO NOTHING;

INSERT INTO system_config (config_key, config_value, description) VALUES
('preferred_extraction_method', 'auto', 'Método preferido de extração')
ON CONFLICT (config_key) DO NOTHING;

INSERT INTO system_config (config_key, config_value, description) VALUES
('enable_intelligent_analysis', 'true', 'Habilitar análise inteligente de dados')
ON CONFLICT (config_key) DO NOTHING;

-- View para relatórios de qualidade
CREATE OR REPLACE VIEW quality_report AS
SELECT 
    extraction_method,
    COUNT(*) as total_extractions,
    AVG(data_quality_score) as avg_quality,
    MIN(data_quality_score) as min_quality,
    MAX(data_quality_score) as max_quality,
    COUNT(CASE WHEN data_quality_score >= 90 THEN 1 END) as excellent_count,
    COUNT(CASE WHEN data_quality_score >= 70 AND data_quality_score < 90 THEN 1 END) as good_count,
    COUNT(CASE WHEN data_quality_score < 70 THEN 1 END) as poor_count
FROM instagram_profiles 
WHERE extracted_at >= NOW() - INTERVAL '30 days'
GROUP BY extraction_method
ORDER BY avg_quality DESC;

-- View para últimas extrações
CREATE OR REPLACE VIEW recent_extractions AS
SELECT 
    username,
    full_name,
    followers,
    following,
    posts,
    is_verified,
    is_private,
    extraction_method,
    data_quality_score,
    CASE 
        WHEN data_quality_score >= 90 THEN 'EXCELENTE'
        WHEN data_quality_score >= 70 THEN 'BOA'
        WHEN data_quality_score >= 50 THEN 'ACEITÁVEL'
        ELSE 'RUIM'
    END as quality_level,
    extracted_at
FROM instagram_profiles 
ORDER BY extracted_at DESC
LIMIT 100;

-- Função para cleanup de dados antigos
CREATE OR REPLACE FUNCTION cleanup_old_data(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM extraction_history 
    WHERE extracted_at < NOW() - INTERVAL '1 day' * days_to_keep;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Comentários nas tabelas
COMMENT ON TABLE instagram_profiles IS 'Perfis do Instagram extraídos com análise de qualidade';
COMMENT ON TABLE extraction_history IS 'Histórico de todas as tentativas de extração';
COMMENT ON TABLE system_config IS 'Configurações do sistema de extração';

COMMENT ON COLUMN instagram_profiles.data_quality_score IS 'Pontuação de qualidade dos dados (0-100)';
COMMENT ON COLUMN instagram_profiles.extraction_method IS 'Método usado: instaloader, chrome, html, combined';
COMMENT ON COLUMN instagram_profiles.direct_id IS 'ID único para Direct Messages';

-- Grants de permissão (ajustar conforme necessário)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO instagram_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO instagram_user;

-- Verificação final
SELECT 'Banco de dados configurado com sucesso!' as status;
