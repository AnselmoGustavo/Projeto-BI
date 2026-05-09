# Tech Context: Steam Brazil BI
*Version: 1.0*
*Created: 2026-05-08*
*Last Updated: 2026-05-08*

## Technology Stack

### Database & Data Warehouse
- **SGBD**: PostgreSQL 14+
- **Modelo**: Dimensional (Star Schema)
- **Tabelas**: dim_jogos, player_metrics, price_history, update_frequency, etl_log
- **Backup**: pg_dump automático

### ETL Pipeline
- **Linguagem**: Python 3.9+
- **Web Framework**: N/A (scripts standalone)
- **Librarias Principais**:
  - `requests` (v2.31.0) - Consumo de API
  - `beautifulsoup4` (v4.12.2) - Web scraping
  - `pandas` (v2.1.3) - Manipulação de dados
  - `psycopg2-binary` (v2.9.9) - Conexão PostgreSQL
  - `python-dotenv` (v1.0.0) - Variáveis de ambiente
  - `APScheduler` (v3.10.4) - Agendamento de tarefas

### Data Sources (APIs & Web)
- **Steam Web API**: https://api.steampowered.com (JSON)
- **SteamCharts**: https://steamcharts.com (HTML Scraping)
- **SteamDB**: https://steamdb.info (HTML Scraping)

### BI & Visualization
- **Tool**: A definir (Tableau, Power BI, Metabase, ou Grafana)
- **Formatos**: Gráficos, mapas geolocalização, dashboards interativos
- **Princípios**: Data Storytelling

### Development Tools
- **IDE**: Cursor IDE / VS Code
- **Version Control**: Git
- **Framework**: CursorRIPER (workflow estruturado)
- **Environment**: Local + PostgreSQL

## Infrastructure

### Local Development
```
├── .cursor/               # Regras do CursorRIPER
├── .memory-bank/          # Memory Bank
├── data/
│   ├── raw/              # Dados brutos extraídos
│   ├── processed/        # Dados processados
│   └── logs/             # Logs de execução
├── extractors/           # Módulos de extração
├── transformers/         # Módulos de transformação
├── loaders/              # Módulos de carga
├── main.py               # Orquestração ETL
├── config.py             # Configuração
├── requirements.txt      # Dependências
└── .env                  # Variáveis (gitignored)
```

### Database Connection
- **Host**: localhost (desenvolvimento) ou cloud (produção)
- **Port**: 5432
- **Database**: steam_dw
- **Schema**: steam_dw
- **Auth**: Usuário postgres + senha

## Performance Targets
- **Carga inicial**: 2-4 horas (10.000-50.000 games)
- **Atualização diária**: 20-30 minutos
- **Query max**: 5 segundos (dashboards)
- **Data warehouse size**: ~5-10 GB/ano

## Rate Limiting & Constraints
- **Steam API**: ~100-200 requisições/min
- **Scraping delay**: 1.5-2 segundos entre requisições
- **Retry attempts**: 3 tentativas com backoff
- **Timeout**: 10 segundos por requisição

## Environment Variables
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=steam_dw
DB_USER=postgres
DB_PASSWORD=
DB_SCHEMA=steam_dw
STEAM_API_KEY=
STEAM_API_BASE_URL=https://api.steampowered.com
ETL_BATCH_SIZE=100
ETL_REQUEST_DELAY=1.5
ETL_RETRY_ATTEMPTS=3
LOG_LEVEL=INFO
```

## Security Considerations
- ✅ Credenciais em .env (nunca versionado)
- ✅ Rate limiting para proteger APIs
- ✅ User-Agent para scraping responsável
- ✅ Validação de entrada (SQL injection prevention)
- ✅ HTTPS para todas as requisições
- ✅ Logs auditáveis (etl_log table)

---

*Technical foundation for all implementation decisions.*
