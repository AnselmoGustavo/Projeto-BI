# Registro do Projeto - Steam BI

Documento vivo para registrar arquitetura, operacao e evolucao do projeto.
Ultima atualizacao: 2026-05-08

## 1) Resumo Executivo
- Projeto: Analise de Dados Brasileiros da Steam (Business Intelligence)
- Objetivo: Construir um Data Warehouse + pipeline ETL + dashboards para suporte a decisao
- Status: Fase 4 ativa (ETL operacional, incremental e com enriquecimentos recentes)

## 2) Escopo das Fases
- Fase 1: Definicao do negocio e problema (concluida)
- Fase 2: Arquitetura da solucao BI (concluida)
- Fase 3: Desenvolvimento e construcao do DW (concluida)
- Fase 4: Implementacao ETL (em andamento)
- Fase 5: Dashboards (pendente)
- Fase 6: Apresentacao final (pendente)

## 3) Stack Tecnica

### 3.1 Banco de dados
- SGBD: PostgreSQL 18
- Database: steam_dw
- Schema: steam_dw

### 3.2 Runtime e bibliotecas
- Python: 3.14
- Bibliotecas principais:
  - psycopg[binary]==3.3.4
  - requests==2.32.3
  - python-dotenv==1.0.1

### 3.3 Arquivos principais do ETL
- config.py
- main.py
- extractors/steam_api.py
- extractors/steamcharts.py
- transformers/steam_transformer.py
- loaders/postgres_loader.py
- run_etl.ps1

## 4) Fontes de Dados (APIs e scraping)

### 4.1 Steam API (oficial)
- Base: https://api.steampowered.com
- Endpoints usados no projeto:
  - ISteamUserStats/GetNumberOfCurrentPlayers/v1/ (players atuais)
  - ISteamChartsService/GetMostPlayedGames/v1/ (ranking de jogos populares)
- Observacao:
  - Endpoint de catalogo amplo ISteamApps/GetAppList/v2/ nao respondeu neste ambiente (404)

### 4.2 Steam Store API
- Base: https://store.steampowered.com
- Endpoint usado:
  - /api/appdetails?appids={id}&cc=br&l=portuguese
- Campos extraidos:
  - nome, developer, publisher, release_date, is_free, genres, platforms
  - short_description, supported_languages, categories, metacritic_score, required_age, coming_soon
  - price_overview (preco inicial/final/desconto/moeda)

### 4.3 SteamCharts (scraping)
- Base: https://steamcharts.com
- Endpoint usado:
  - /app/{app_id}
- Dados extraidos:
  - snapshot atual: avg_players, peak_players, gain, percent_gain, peak_24h, all_time_peak
  - historico mensal: serie de meses (date, avg_players, peak_players, gain, percent_gain)

### 4.4 Fallback para catalogo de app_ids
- Fonte: https://steamspy.com/api.php?request=all
- Motivo:
  - ampliar pool de app_ids quando endpoint oficial de catalogo nao esta disponivel
  - permitir crescimento real do banco em modo incremental

## 5) Modelagem do Data Warehouse

### 5.1 Dimensao
- dim_jogos (dimensao principal)
  - chaves e atributos basicos: app_id, name, developer, publisher, release_date, is_free
  - atributos de classificacao: genres, tags, platforms, categories, supported_languages
  - atributos de qualidade/enriquecimento: short_description, metacritic_score, required_age, coming_soon
  - atributos de precificacao atual: price

### 5.2 Fatos
- player_metrics (fato temporal)
  - granularidade: app_id + date
  - medidas: current_players, avg_players, peak_players, peak_24h, all_time_peak, gain, percent_gain

- price_history (fato de preco)
  - granularidade: app_id + date
  - medidas: price, discount, currency
  - enriquecimento recente: price_initial, price_final, discount_percent

- update_frequency (fato de updates)
  - granularidade: app_id + update_date + build_id
  - medidas: size_on_disk

### 5.3 Controle e auditoria
- etl_log: status, volume processado, falhas, mensagem de erro, data_source
- etl_metadata: checkpoint incremental (last_app_id_processed, total_app_ids, last_successful_run)

### 5.4 Views e funcoes
- ultimas_metricas_por_jogo
- jogos_em_alta
- limpar_dados_antigos(anos)
- registrar_etl(...)

Arquivo de referencia: schema_steam_dw.sql

## 6) Processo ETL (Extracao, Transformacao, Carga)

### 6.1 Extracao
1. Buscar pool de app_ids
2. Selecionar janela incremental com checkpoint em etl_metadata
3. Para cada app_id:
   - buscar detalhes do jogo (Store API)
   - buscar players atuais (Steam API)
   - buscar dados de SteamCharts (snapshot + historico mensal)

### 6.2 Transformacao
- Normalizacao de datas (ex.: release_date e meses do SteamCharts)
- Conversao monetaria de centavos para decimal (price_overview)
- Derivacao de campos de desconto (discount_percent)
- Tratamento de tipos e nulos
- Conversao de listas para texto consolidado (genres/categories/platforms/languages)

### 6.3 Carga
- Upsert em dim_jogos
- Upsert em player_metrics (snapshot diario + historico mensal)
- Upsert em price_history (com detalhes de preco)
- Upsert em update_frequency
- Registro operacional em etl_log
- Atualizacao de checkpoint em etl_metadata

### 6.4 Resiliencia
- Falha em app especifico nao interrompe lote inteiro (skip por item com warning)
- Migracoes leves automaticas no loader (ALTER TABLE ... IF NOT EXISTS)

## 7) Operacao e Execucao

### 7.1 Script recomendado
```powershell
.\run_etl.ps1 -Mode incremental -Limit 200
```

### 7.2 Modo rapido (validacao)
```powershell
.\run_etl.ps1 -Quick
```

### 7.3 Execucao direta (sem wrapper)
```powershell
.venv\Scripts\python.exe main.py --mode incremental --limit 200
```

## 8) Snapshot Atual (2026-05-08)

### 8.1 Contagens no DW
- dim_jogos: 293
- player_metrics: 602
- price_history: 293
- update_frequency: 293
- etl_log: 18

### 8.2 Checkpoint incremental
- data_source: steam_api
- last_successful_run: 2026-05-08 23:37:51
- last_app_id_processed: 460950
- last_date_processed: 2026-05-08
- total_app_ids (ultimo lote): 3

Observacao: contagens mudam a cada execucao incremental.

## 9) Riscos e Limitacoes
- Dependencia de endpoints externos e variacao de disponibilidade
- Mudancas de HTML em fontes de scraping
- Rate limit e latencia de API
- Qualidade de dado heterogenea entre fontes

## 10) Pendencias e Proximos Passos

### 10.1 Curto prazo (Fase 4)
- Evoluir update_frequency com fontes mais especificas de update/build
- Implementar agendamento diario no Windows Task Scheduler
- Consolidar monitoramento automatico de falhas (consulta de etl_log)

### 10.2 Medio prazo (Fase 5)
- Definir ferramenta de BI
- Construir dashboards operacional, gerencial e estrategico
- Definir e acompanhar KPIs com serie historica mensal

## 11) Convencao de Atualizacao
Ao registrar mudancas relevantes, sempre incluir:
- Data
- Tipo de alteracao
- Arquivos alterados
- Resultado
- Impacto

## 12) Historico de Alteracoes

### 2026-05-08 - Inicializacao do projeto
- Tipo: Inicializacao de registro continuo
- Arquivos alterados: multiplos arquivos de schema/etl
- Resultado:
  - DW criado e validado
  - ETL piloto funcional para tabelas principais
- Impacto: base operacional pronta

### 2026-05-08 - Incremental e checkpoint
- Tipo: Evolucao ETL incremental
- Arquivos alterados: main.py, loaders/postgres_loader.py
- Resultado:
  - checkpoint funcional em etl_metadata
  - rotacao incremental de app_ids
- Impacto: rotina sem full reload a cada execucao

### 2026-05-08 - Higiene de repositorio
- Tipo: Segurança e versionamento
- Arquivos alterados: .gitignore, .env.example, indice git
- Resultado:
  - arquivos sensiveis/caches fora do versionamento
- Impacto: reducao de risco operacional

### 2026-05-08 - Enriquecimento de dimensao e preco
- Tipo: Enriquecimento de dados
- Arquivos alterados: transformers/steam_transformer.py, loaders/postgres_loader.py, schema_steam_dw.sql
- Resultado:
  - novos campos em dim_jogos (descricao, idiomas, categorias, metacritic, idade, coming_soon)
  - novos campos em price_history (price_initial, price_final, discount_percent)
- Impacto: melhor qualidade para analise de produto e promocao

### 2026-05-08 - Historico mensal SteamCharts
- Tipo: Evolucao de serie temporal
- Arquivos alterados: extractors/steamcharts.py, transformers/steam_transformer.py, main.py, loaders/postgres_loader.py
- Resultado:
  - ingestao de historico mensal em player_metrics
  - upsert de metricas completo por (app_id, date)
- Impacto: suporte a analise de tendencia, sazonalidade e crescimento historico
