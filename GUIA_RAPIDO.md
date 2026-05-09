# 🚀 GUIA RÁPIDO - IMPLEMENTAÇÃO DO BANCO DE DADOS STEAM BI

## 📌 Resumo Executivo

Seu projeto de BI visa analisar dados brasileiros da Steam. Você precisará:

1. **Criar um Data Warehouse** com 4 tabelas principais
2. **Implementar um pipeline ETL** para extrair, transformar e carregar dados
3. **Montar dashboards** com indicadores de negócio

---

## 🎯 Objetivo Final

Fornecer insights sobre o mercado de jogos brasileiro na Steam para:
- **Desenvolvedoras**: Entender preferências do público
- **Publishers**: Otimizar estratégia de lançamento
- **Investidores**: Avaliar oportunidades de mercado
- **Analistas**: Tomar decisões baseadas em dados

---

## 📊 Estrutura do Data Warehouse

### Tabelas Criadas

| Tabela | Tipo | Função |
|--------|------|--------|
| **dim_jogos** | Dimensão | Dados estáticos dos jogos |
| **player_metrics** | Fato | Métricas de jogadores por data |
| **price_history** | Fato | Histórico de preços |
| **update_frequency** | Fato | Registro de atualizações |
| **etl_log** | Controle | Auditoria do pipeline |

### Relacionamento de Dados

```
dim_jogos (1)
    ├── player_metrics (n) — Métricas diárias
    ├── price_history (n) — Histórico de preços
    └── update_frequency (n) — Histórico de updates
    
    Chave de ligação: app_id
```

---

## 🔄 Arquitetura ETL

```
┌─────────────────────────────────────────────────────────┐
│                    FONTES DE DADOS                       │
├─────────────────────────────────────────────────────────┤
│ API Steam          │ SteamCharts      │ SteamDB         │
│ (JSON)             │ (Scraping)       │ (Scraping)      │
└──────────┬──────────┴────────┬─────────┴────────┬────────┘
           │                   │                  │
           └───────────────────┼──────────────────┘
                               │
                        ┌──────▼──────┐
                        │  EXTRAÇÃO   │
                        │  (Python)   │
                        └──────┬──────┘
                               │
                        ┌──────▼──────────────┐
                        │   TRANSFORMAÇÃO    │
                        │ • Limpeza          │
                        │ • Validação        │
                        │ • Normalização     │
                        └──────┬─────────────┘
                               │
                        ┌──────▼──────┐
                        │   CARGA     │
                        │ PostgreSQL  │
                        └──────┬──────┘
                               │
                        ┌──────▼──────────┐
                        │ Data Warehouse  │
                        │   (DW STEAM)    │
                        └─────────────────┘
```

---

## 📋 Arquivos Criados para Você

### 1. **PLANO_BANCO_DADOS.md**
   - Estrutura completa do projeto
   - Fases de implementação
   - Checklist de tarefas

### 2. **schema_steam_dw.sql**
   - Script SQL pronto para executar
   - Criar tabelas com índices
   - Funções auxiliares
   - Views para análises rápidas

### 3. **etl_template.py**
   - Template completo de código Python
   - Módulos: extractors, transformers, loaders
   - Tratamento de erros
   - Logging e auditoria

---

## ⚡ Começar Agora

### Passo 1: Preparar PostgreSQL
```sql
-- Criar banco de dados
CREATE DATABASE steam_dw;

-- Executar script SQL
psql -U postgres steam_dw < schema_steam_dw.sql

-- Verificar tabelas criadas
\dt steam_dw.*
```

### Passo 2: Instalar Dependências Python
```bash
pip install -r requirements.txt
```

Dependências principais:
- `requests` - Consumir APIs
- `beautifulsoup4` - Web scraping
- `pandas` - Manipulação de dados
- `psycopg2` - Conexão PostgreSQL
- `sqlalchemy` - ORM (opcional)

### Passo 3: Configurar Variáveis de Ambiente
```bash
# Criar arquivo .env
cp .env.example .env

# Editar com suas credenciais:
DB_HOST=localhost
DB_USER=postgres
DB_PASSWORD=sua_senha
STEAM_API_KEY=sua_chave_api
```

### Passo 4: Executar ETL (Piloto)
```bash
python main.py
```

---

## 🎯 Dados Que Você Vai Coletar

### De cada jogo você terá:

| Dados | Fonte | Frequência |
|-------|-------|-----------|
| Nome, Developer, Publisher, Gênero | Steam API | Inicial |
| Preço, Desconto | SteamDB | Diária |
| Jogadores simultâneos | Steam API | Tempo real |
| Média mensal de players | SteamCharts | Diária |
| Pico de jogadores (24h, mensal, all-time) | SteamCharts | Diária |
| Histórico de atualizações | SteamDB | Diária |

---

## 📈 Indicadores Principais (KPIs)

Com esses dados você consegue medir:

✅ **Crescimento/Decaimento de Jogadores**
- Ganho mensal em %
- Trending games
- Seasonal patterns

✅ **Comportamento de Preço**
- Elasticidade de preço
- Impacto de descontos
- Sazonalidade

✅ **Popularidade e Tendências**
- Top 10 games
- Novos lançamentos
- Gêneros populares

✅ **Frequência de Atualizações**
- Correlação com player growth
- Histórico de builds
- Tamanho do jogo

---

## ⚠️ Desafios Conhecidos

| Desafio | Solução |
|---------|---------|
| **Rate Limiting** da API | Implementar delays entre requisições (1.5s) |
| **Dados históricos limitados** | SteamCharts tem 2-3 anos, SteamDB menos |
| **Scraping pode quebrar** | Monitorar mudanças de HTML e ajustar parsers |
| **Performance** | Criar índices em app_id e date |
| **Dados faltando** | Validar e logar inconsistências |

---

## 🔍 Monitoramento e Manutenção

### Verificar Execução do ETL
```sql
-- Ver último registro de execução
SELECT * FROM steam_dw.etl_log 
ORDER BY created_at DESC LIMIT 10;

-- Ver erros
SELECT * FROM steam_dw.etl_log 
WHERE status = 'erro' 
ORDER BY created_at DESC;
```

### Limpar Dados Antigos
```sql
-- Remover dados com mais de 2 anos
SELECT steam_dw.limpar_dados_antigos(2);
```

### Backup
```bash
# Backup completo
pg_dump -U postgres steam_dw > backup_steam_dw_$(date +%Y%m%d).sql

# Restaurar
psql -U postgres steam_dw < backup_steam_dw_20260508.sql
```

---

## 📚 Próximas Fases

### Fase 5: Dashboards (Após banco popular)
- Visual de top 10 games
- Crescimento de jogadores por gênero
- Histórico de preços vs players
- Mapa de distribuição geográfica

### Fase 6: Apresentação
- Demo do sistema funcionando
- Insights extraídos
- Recomendações de negócio

---

## 📞 Dúvidas Frequentes

**P: Por onde começo?**
A: Comece pelo PostgreSQL → Schema SQL → ETL Python → Testes

**P: Preciso de uma API key da Steam?**
A: Não é obrigatório, mas recomendado para melhor acesso aos dados

**P: Quanto tempo leva para popular?**
A: Carga inicial: 2-4 horas. Atualizações diárias: 20-30 minutos

**P: Posso usar SQLite em vez de PostgreSQL?**
A: Tecnicamente sim, mas PostgreSQL é melhor para volumes grandes

**P: E se a API da Steam cair?**
A: Implementar retry logic (3 tentativas) e logging de falhas

---

## 🎓 Referências Úteis

- [Steam Web API Docs](https://steamcommunity.com/dev/apidocs)
- [SteamCharts](https://steamcharts.com)
- [SteamDB](https://steamdb.info)
- [PostgreSQL JSON](https://www.postgresql.org/docs/current/functions-json.html)
- [Data Storytelling](https://www.aquare.la/o-que-e-um-dicionario-de-dados-de-data-analytics/)

---

## ✅ Checklist de Implementação

- [ ] PostgreSQL instalado e banco criado
- [ ] Schema SQL executado
- [ ] Arquivo .env configurado
- [ ] Dependências Python instaladas
- [ ] Script ETL testado (piloto com 10 jogos)
- [ ] Carga inicial realizada
- [ ] ETL agendado para execução automática
- [ ] Dashboards criados
- [ ] Apresentação preparada

---

**Próximo passo:** Comece pelo schema SQL! Execute o arquivo `schema_steam_dw.sql` no seu PostgreSQL.

