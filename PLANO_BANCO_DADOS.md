# Plano de Implementação - Banco de Dados Steam BI

## 📋 Visão Geral do Projeto
**Objetivo**: Análise de dados brasileiros da plataforma Steam
**SGBD**: PostgreSQL
**Público-alvo**: Desenvolvedoras, publishers, analistas de dados, investidores e jogadores

---

## 🗂️ Arquitetura de Dados

### Fontes de Dados
1. **Steam Web API** (JSON) - `https://api.steampowered.com`
2. **SteamCharts** (Web Scraping) - `https://steamcharts.com`
3. **SteamDB** (Web Scraping) - `https://steamdb.info`

### Chave de Integração
- **app_id**: Identificador único do jogo (PK comum em todas as tabelas)

---

## 📊 Estrutura do Data Warehouse

### 1. Tabela Dimensional: `dim_jogos` (Fato Fixa)
Armazena informações estáticas dos jogos
```
app_id (INT) - PK
name (VARCHAR)
developer (VARCHAR)
publisher (VARCHAR)
release_date (DATE)
price (DECIMAL)
is_free (BOOLEAN)
genres (VARCHAR) - JSON ou string separada por vírgula
tags (VARCHAR) - JSON ou string separada por vírgula
platforms (VARCHAR) - JSON ou string separada por vírgula
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

### 2. Tabela Fato: `player_metrics` (Métricas Temporais)
Armazena métricas de jogadores por data
```
id (SERIAL) - PK
app_id (INT) - FK → dim_jogos
date (DATE)
current_players (INT)
avg_players (INT)
peak_players (INT)
peak_24h (INT)
all_time_peak (INT)
gain (INT) - crescimento/queda mensal
percent_gain (DECIMAL)
created_at (TIMESTAMP)
```

### 3. Tabela Fato: `price_history` (Histórico de Preços)
Armazena histórico de preços com descontos
```
id (SERIAL) - PK
app_id (INT) - FK → dim_jogos
date (DATE)
price (DECIMAL)
discount (DECIMAL) - em percentual
currency (VARCHAR) - moeda
created_at (TIMESTAMP)
```

### 4. Tabela Fato: `update_frequency` (Histórico de Atualizações)
Armazena informações sobre atualizações dos jogos
```
id (SERIAL) - PK
app_id (INT) - FK → dim_jogos
update_date (DATE)
build_id (INT)
size_on_disk (BIGINT) - em bytes
created_at (TIMESTAMP)
```

### 5. Tabela de Controle: `etl_log` (Monitoramento ETL)
Registra execuções do ETL
```
id (SERIAL) - PK
etl_name (VARCHAR)
start_time (TIMESTAMP)
end_time (TIMESTAMP)
status (VARCHAR) - 'sucesso', 'erro', 'parcial'
records_processed (INT)
error_message (TEXT)
created_at (TIMESTAMP)
```

---

## 🔄 Processo ETL

### Fase 1: Extração
```
1. Consumir lista de games via Steam API
2. Para cada app_id identificado:
   - Extrair dados do jogo via API
   - Fazer scraping do SteamCharts (histórico de players)
   - Fazer scraping do SteamDB (histórico de preços, atualizações)
3. Armazenar dados temporários em JSON/CSV
```

### Fase 2: Transformação (Limpeza e Validação)
```
✓ Remover duplicatas
✓ Validar tipos de dados (INT, DATE, DECIMAL, etc.)
✓ Padronizar datas (ISO 8601: YYYY-MM-DD)
✓ Padronizar preços em uma única moeda (BRL)
✓ Remover/tratar valores nulos
✓ Validar ranges de valores (preço > 0, jogadores >= 0)
✓ Remover linhas sem app_id ou identificador
✓ Converter strings de gêneros/tags em formato consistente
```

### Fase 3: Carga
```
1. Validar integridade referencial (app_id existe em dim_jogos)
2. Inserir/atualizar em dim_jogos (UPSERT)
3. Inserir novos registros em player_metrics
4. Inserir novos registros em price_history
5. Inserir novos registros em update_frequency
6. Registrar sucesso/erro em etl_log
```

---

## 🛠️ Ferramentas Necessárias

| Ferramenta | Função |
|-----------|--------|
| **requests** | Consumir Steam Web API (JSON) |
| **beautifulsoup4** | Web scraping de SteamCharts e SteamDB |
| **psycopg2** ou **sqlalchemy** | Conexão e operações PostgreSQL |
| **pandas** | Manipulação e limpeza de dados |
| **python-dotenv** | Gerenciar variáveis de ambiente (conexões) |

---

## 📝 Passos de Implementação

### ✅ Etapa 1: Preparação do Ambiente
- [ ] Instalar PostgreSQL
- [ ] Criar banco de dados `steam_dw`
- [ ] Instalar dependências Python (requirements.txt)
- [ ] Configurar arquivo .env com credenciais

### ✅ Etapa 2: Criar Estrutura do Banco de Dados
- [ ] Executar script SQL para criar schema
- [ ] Criar tabelas (dim_jogos, player_metrics, price_history, update_frequency, etl_log)
- [ ] Definir chaves primárias e estrangeiras
- [ ] Criar índices em colunas frequentemente consultadas (app_id, date)

### ✅ Etapa 3: Implementar Extração de Dados
- [ ] Script para consumir Steam Web API
- [ ] Script para scraping SteamCharts
- [ ] Script para scraping SteamDB
- [ ] Tratamento de erros e rate limiting

### ✅ Etapa 4: Implementar Transformação
- [ ] Validação de tipos e formatos
- [ ] Limpeza de dados inconsistentes
- [ ] Padronização de valores
- [ ] Tratamento de valores nulos

### ✅ Etapa 5: Implementar Carga
- [ ] UPSERT em dim_jogos
- [ ] INSERT em tabelas fato
- [ ] Validação de integridade referencial
- [ ] Logging e tratamento de erros

### ✅ Etapa 6: Orquestração ETL
- [ ] Scheduler (cron ou APScheduler) para execuções periódicas
- [ ] Monitoramento e alertas
- [ ] Backup automático

---

## 📈 Estratégia de População Inicial

### Carga Incremental (Recomendado)
1. **Primeira execução**: Carregar últimos 12 meses de dados históricos
2. **Execuções posteriores**: Apenas novos dados desde a última execução
3. **Frequência**: Diária (ou conforme necessário para métricas em tempo real)

### Volume Estimado
- **Jogos únicos**: ~10.000 a 50.000 (apps brasileiros)
- **Métricas diárias**: ~2-5 GB/ano
- **Histórico de preços**: ~500 MB/ano
- **Atualizações**: ~100 MB/ano

---

## 🔒 Considerações Importantes

1. **Rate Limiting**: Respeitar limits de API (Steam permite ~100-200 req/min)
2. **Web Scraping**: Usar delays (1-2 seg entre requisições) para não sobrecarregar servidores
3. **Dados Históricos**: Alguns dados podem não estar disponíveis retroativamente
4. **Índices**: Criar em app_id, date para queries de análise
5. **Backup**: Implementar rotina diária de backup

---

## 🎯 Ordem de Execução Recomendada

```
1. Criar banco e schema (SQL)
2. Implementar conectores de dados (APIs + scraping)
3. Executar extração piloto (10-100 jogos)
4. Ajustar transformações conforme necessário
5. Executar população inicial
6. Montar dashboards
7. Ir para produção com scheduler
```

---

## 📞 Próximas Ações

1. ✅ Preparar scripts Python para extração
2. ✅ Criar schema SQL
3. ✅ Definir schedule de atualização
4. ✅ Implementar dashboards (Fase 5)

