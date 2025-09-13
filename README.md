# 🎯 Instagram Extractor - Sistema Unificado

Extrator completo de dados do Instagram com automatização de Direct ID e salvamento em PostgreSQL.

## ✨ Funcionalidades

- 📊 **Extração Focada**: Dados apenas do perfil configurado no config.ini
- 📨 **Direct ID Automático**: Detecta e salva IDs para mensagens diretas  
- 🗄️ **PostgreSQL**: Salva dados diretamente no banco
- 📁 **Organização Automática**: Move arquivos processados
- 🎯 **Sistema Otimizado**: Processo rápido e direto

## 🚀 Como Usar

### 1. **Configuração Inicial**
```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar banco no config.ini
[DATABASE]
host = seu_host
database = sua_database
user = seu_usuario
password = sua_senha

[INSTAGRAM]  
username = perfil_target
```

### 2. **Salvar HTML do Instagram**
1. Acesse o perfil no Instagram (logado)
2. Salve a página como HTML completo
3. Coloque o arquivo na pasta `html_pages/`

### 3. **Executar Extração**
```bash
python instagram_extractor.py
```

## 📊 Dados Extraídos

- 👤 **Perfil**: Nome, username, bio
- 📈 **Números**: Seguidores, seguindo, posts
- ✅ **Status**: Verificado, privado
- 📨 **Direct ID**: Para automação de mensagens
- 🔗 **URLs**: Links externos, foto do perfil

## 🗄️ Estrutura do Banco

```sql
CREATE TABLE instagram_stats (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    followers_count INTEGER,
    following_count INTEGER,
    posts_count INTEGER,
    is_verified BOOLEAN DEFAULT FALSE,
    is_private BOOLEAN DEFAULT FALSE,
    bio TEXT,
    profile_pic_url TEXT,
    external_url TEXT,
    direct_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 📁 Estrutura do Projeto

```
seguindo-seguidores/
├── instagram_extractor.py    # 🎯 Sistema principal
├── config.ini               # ⚙️  Configurações
├── requirements.txt          # 📦 Dependências
├── html_pages/              # 📁 Arquivos HTML
│   └── feito/               # ✅ Processados
├── .venv/                   # 🐍 Ambiente virtual
└── README.md                # 📖 Documentação
```

## 🎯 Exemplo de Uso

```bash
🎯 EXTRATOR UNIFICADO DO INSTAGRAM INICIADO
============================================================
🚀 INICIANDO EXTRAÇÃO FOCADA...

📁 Encontrados 1 arquivo(s) HTML
🎯 Usuário alvo (config.ini): soufelipe.barbosa
============================================================

🔍 Processando: Instagram.html
📨 Direct ID: 110614057004972
📊 EXTRAINDO DADOS DO PERFIL: @soufelipe.barbosa
   👥 Seguidores: 439
   📊 Seguindo: 647  
   📸 Posts: 119
   ❌ Verificado: Não
   🔓 Privado: Não

✅ Dados salvos no PostgreSQL
🔗 Link: https://www.instagram.com/direct/t/110614057004972

📊 PERFIL PROCESSADO E SALVO
==================================================
👤 @soufelipe.barbosa
📝 Nome: Felipe Barbosa
❌ Verificado: Não
🔓 Privado: Não
👥 Seguidores: 439
📊 Seguindo: 647
� Posts: 119
📨 Direct ID: 110614057004972
�🔗 Link: https://www.instagram.com/direct/t/110614057004972
🕐 Processado em: 11/09/2025 13:08
==================================================

🎉 EXTRAÇÃO FINALIZADA!
💾 Dados do perfil salvos no banco PostgreSQL!
🎯 Foco: Apenas perfil configurado no config.ini
```

## 🔧 Tecnologias

- **Python 3.x**
- **PostgreSQL** - Banco de dados
- **BeautifulSoup4** - Parsing HTML
- **psycopg2** - Conexão PostgreSQL
- **ConfigParser** - Configurações

## 📝 Licença

Projeto desenvolvido para automação e análise de dados do Instagram.

---

**🎉 Sistema 100% Funcional - Pronto para Produção!**
