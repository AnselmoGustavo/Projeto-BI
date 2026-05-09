# System Patterns: Steam Brazil BI
*Version: 1.0*
*Created: 2026-05-08*
*Last Updated: 2026-05-08*

## Architecture Overview
Sistema de Business Intelligence baseado em Data Warehouse dimensional (Star Schema) com pipeline ETL automatizado. Dados são extraídos de múltiplas fontes (APIs e web scraping), transformados em uma camada de staging, e carregados em um banco PostgreSQL otimizado para análise.

```
┌─────────────────────────────────────────────────────────┐
│                    FONTE DE DADOS                        │
├─────────────────────────────────────────────────────────┤
│ Steam API    │ SteamCharts     │ SteamDB               │
│ (REST/JSON)  │ (HTML/Scraping) │ (HTML/Scraping)      │
└──────────────┴─────────────────┴──────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────┐
│              ETL PIPELINE (Python)                       │
├─────────────────────────────────────────────────────────┤
│ EXTRACT  →  TRANSFORM  →  LOAD  →  VALIDATE           │
└──────────────────────────────────────────┬──────────────┘
                                           ▼
┌─────────────────────────────────────────────────────────┐
│         DATA WAREHOUSE (PostgreSQL)                      │
├─────────────────────────────────────────────────────────┤
│ Dimensões:              │ Fatos:                        │
│ • dim_jogos             │ • player_metrics             │
│                         │ • price_history              │
│                         │ • update_frequency           │
└─────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│         BUSINESS INTELLIGENCE LAYER                      │
├─────────────────────────────────────────────────────────┤
│ Views • KPIs • Dashboards • Reports                     │
└─────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Data Extraction Layer
**Responsabilidade**: Coletar dados das 3 fontes diferentes
- **steam_api.py**: Consome Steam Web API (JSON)
  - Lista de apps
  - Dados de jogos
  - Jogadores simultâneos em tempo real
- **steamcharts.py**: Web scraping de SteamCharts
  - Histórico de jogadores
  - Médias mensais
  - Picos de uso
- **steamdb.py**: Web scraping de SteamDB
  - Histórico de preços
  - Informações de builds
  - Tags e metadados
  
**Output**: JSON/CSV temporário

### 2. Data Transformation Layer
**Responsabilidade**: Limpar, validar e normalizar dados
- **data_cleaner.py**:
  - Remove duplicatas
  - Padroniza tipos de dados
  - Normaliza datas (ISO 8601)
  - Converte moedas (BRL)
  - Remove/trata nulos
- **data_validator.py**:
  - Valida ranges (preço > 0, jogadores >= 0)
  - Verifica integridade referencial
  - Identifica anomalias
- **data_normalizer.py**:
  - Padroniza formatos
  - Agrega dados por período
  - Calcula derivados (gains, trends)

**Output**: Dados limpos e validados

### 3. Data Loading Layer
**Responsabilidade**: Persistir dados no DW
- **db_loader.py**:
  - UPSERT em dim_jogos
  - INSERT em tabelas fato
  - Gerencia transações
  - Tratamento de erros e rollback
  - Logging de operações

**Output**: Registros no PostgreSQL

### 4. Data Warehouse Layer
**Tabela Dimensional**:
```
dim_jogos (Master)
├─ app_id (PK)
├─ name, developer, publisher
├─ release_date, price
├─ is_free, genres, tags, platforms
└─ created_at, updated_at
```

**Tabelas Fato**:
```
player_metrics
├─ id (PK)
├─ app_id (FK → dim_jogos)
├─ date (TIME)
├─ current_players, avg_players
├─ peak_players, all_time_peak
├─ gain, percent_gain

price_history
├─ id (PK)
├─ app_id (FK → dim_jogos)
├─ date (TIME)
├─ price, discount, currency

update_frequency
├─ id (PK)
├─ app_id (FK → dim_jogos)
├─ update_date (TIME)
├─ build_id, size_on_disk
```

**Tabela Controle**:
```
etl_log
├─ id (PK)
├─ etl_name, status
├─ records_processed, records_failed
├─ error_message, timestamp
```

### 5. BI & Analytics Layer
**Views**:
- `ultimas_metricas_por_jogo` - Últimos 30 dias
- `jogos_em_alta` - Trending games (crescimento positivo)

**KPIs**:
- Top 10 games por jogadores
- Crescimento/queda mensal (%)
- Correlação preço vs players
- Frequência de atualizações vs crescimento

**Dashboards** (3 níveis):
- **Operacional**: Métricas em tempo real
- **Gerencial**: Tendências e comparativos
- **Estratégico**: Insights e previsões

## Design Patterns in Use

### 1. Extract-Transform-Load (ETL)
Padrão clássico de integração de dados com separação clara de fases. Permite rastreamento, retry e auditoria em cada etapa.

### 2. Dimensional Modeling (Star Schema)
Data Warehouse com tabelas dimensionais (mudança lenta) e tabelasde fato (eventos). Otimizado para analytics queries.

### 3. Idempotency
- UPSERT em dim_jogos (seguro para re-execução)
- UNIQUE constraints em (app_id, date) para fatos
- Permite retry sem duplicação

### 4. Incremental Load
- Tracking de última execução em etl_metadata
- Cargas futuras processam apenas dados novos
- Reduz tempo de pipeline

### 5. Retry & Circuit Breaker
- 3 tentativas com backoff exponencial
- Rate limiting respeitado
- Falhas registradas em etl_log

### 6. Auditoria & Logging
- Todas operações registradas em etl_log
- Timestamps em todas tabelas
- Rastreamento de erro e status

## Data Flow

```
HORA 00:00 → ETL INICIADO
├─ 00:00-00:30 → EXTRACT (3 fontes em paralelo)
├─ 00:30-01:00 → TRANSFORM (limpeza, validação)
├─ 01:00-01:30 → LOAD (inserção no DW)
└─ 01:30-02:00 → VALIDATE (testes integridade)

RESULTADO:
├─ 50.000 games processados
├─ 150.000 métricas coletadas
├─ 0 erros críticos
└─ Sucesso registrado em etl_log
```

## Scaling Considerations
- **Horizontal**: Paralelização de apps por worker
- **Vertical**: Índices em (app_id, date) para fast lookups
- **Temporal**: Particionamento de player_metrics por ano
- **Archiving**: Limpeza de dados com >2 anos (opcional)

---

*Defines structural patterns and best practices.*
