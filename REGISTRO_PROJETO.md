# Registro do Projeto - Steam BI

Arquivo vivo para acompanhar a evolucao do projeto.
Atualize este documento a cada entrega relevante.

## 1) Resumo Executivo
- Projeto: Analise de Dados Brasileiros da Steam (Business Intelligence)
- Objetivo: Construir um Data Warehouse + ETL + Dashboards para suporte a decisao
- Status atual: Fase 4 em andamento (ETL funcional, validado em piloto e repositório higienizado)

## 2) Escopo das Fases
- Fase 1: Definicao do negocio e problema (concluida)
- Fase 2: Arquitetura da solucao BI (concluida)
- Fase 3: Desenvolvimento e construcao do DW (concluida)
- Fase 4: Implementacao ETL (em andamento)
- Fase 5: Dashboards (pendente)
- Fase 6: Apresentacao final (pendente)

## 3) Estrutura Tecnica
### Banco de dados
- SGBD: PostgreSQL 18
- Database: steam_dw
- Schema: steam_dw

### Linguagem e runtime
- Python 3.14 (system)

### Dependencias Python (arquivo requirements.txt)
- psycopg[binary]==3.3.4
- python-dotenv==1.0.1
- requests==2.32.3

## 4) Modelagem do Data Warehouse
Tabelas principais criadas e validadas:
- dim_jogos
- player_metrics
- price_history
- update_frequency
- etl_log
- etl_metadata

Views/funcoes criadas:
- ultimas_metricas_por_jogo
- jogos_em_alta
- limpar_dados_antigos(anos)
- registrar_etl(...)

Arquivo de referencia do schema:
- schema_steam_dw.sql

## 5) O que ja foi implementado
### 5.1 Setup e organizacao
- Instalacao e configuracao do PostgreSQL
- Criacao do banco steam_dw
- Execucao do script schema_steam_dw.sql
- Validacao de tabelas e relacionamento

### 5.2 Pipeline ETL (Fase 4)
Arquivos implementados:
- config.py
- main.py
- extractors/steam_api.py
- extractors/steamcharts.py
- transformers/steam_transformer.py
- loaders/postgres_loader.py
- .env.example
- requirements.txt

Fluxo atual:
1. Extracao de app_ids (Steam API / fallback)
2. Extracao de detalhes do app (Store API)
3. Extracao de jogadores atuais
4. Extracao de metricas SteamCharts (quando disponivel)
5. Transformacao para linhas de DW
6. Carga com upsert em:
   - dim_jogos
   - player_metrics
   - price_history
   - update_frequency
7. Registro de execucao em etl_log
8. Checkpoint incremental em etl_metadata (last_successful_run, last_app_id_processed, last_date_processed)

### 5.3 Compatibilidade tecnica resolvida
- Driver de banco migrado para psycopg v3 (compatibilidade com Python 3.14)
- Ajuste de endpoint/fonte para lista de apps devido a indisponibilidade de rota antiga

### 5.4 Higiene do repositório
- Criação de .gitignore para arquivos sensíveis e gerados localmente
- Sanitização de .env.example para remover senha real
- Remoção de __pycache__ e arquivos .pyc do índice do Git
- Configuração do nome e email globais do Git para commits

## 6) Evidencia de validacao (piloto)
Ultima validacao executada:
- dim_jogos: 10
- player_metrics: 10
- price_history: 10
- update_frequency: 10
- etl_log: 6

Checkpoint incremental validado:
- data_source: steam_api
- last_app_id_processed: 271590
- last_date_processed: 2026-05-08
- total_app_ids: 5

Observacao:
- Esses valores mudam conforme novas execucoes.

## 7) Como executar hoje
## 7.1 Instalar dependencias
```powershell
C:/Users/Usuario/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pip install -r requirements.txt
```

## 7.2 Configurar variaveis de ambiente
Use .env (baseado em .env.example) ou exporte no terminal:
```powershell
$env:DB_HOST='localhost'
$env:DB_PORT='5432'
$env:DB_NAME='steam_dw'
$env:DB_USER='postgres'
$env:DB_PASSWORD='SUA_SENHA'
$env:DB_SCHEMA='steam_dw'
```

## 7.3 Executar ETL piloto
```powershell
C:/Users/Usuario/AppData/Local/Python/pythoncore-3.14-64/python.exe main.py --limit 10 --mode full
```

## 7.4 Executar ETL incremental (recomendado para rotina)
```powershell
C:/Users/Usuario/AppData/Local/Python/pythoncore-3.14-64/python.exe main.py --limit 10 --mode incremental
```

## 7.5 Validar contagens
```sql
SELECT 'dim_jogos' AS tabela, COUNT(*) AS total FROM steam_dw.dim_jogos
UNION ALL
SELECT 'player_metrics', COUNT(*) FROM steam_dw.player_metrics
UNION ALL
SELECT 'price_history', COUNT(*) FROM steam_dw.price_history
UNION ALL
SELECT 'update_frequency', COUNT(*) FROM steam_dw.update_frequency
UNION ALL
SELECT 'etl_log', COUNT(*) FROM steam_dw.etl_log;
```

## 7.6 Consultar checkpoint incremental
```sql
SELECT data_source, last_successful_run, last_app_id_processed, last_date_processed, total_app_ids
FROM steam_dw.etl_metadata;
```

## 8) Pendencias e proximos passos
### Curto prazo (Fase 4)
- Melhorar tratamento de erros/retry por fonte
- Adicionar agendamento diario (scheduler)
- Incluir mais campos/qualidade para update_frequency
- Preparar cobertura para SteamDB (se for viavel no prazo)

### Medio prazo (Fase 5)
- Definir ferramenta de dashboard
- Construir paineis operacional, gerencial e estrategico
- Aplicar Data Storytelling

## 9) Riscos conhecidos
- Rate limit e mudancas de HTML em scraping
- Dado incompleto/indisponivel por app
- Dependencia de endpoints externos

## 10) Convencao de atualizacao deste arquivo
Sempre que houver alteracao relevante, adicionar uma entrada no historico abaixo:

Modelo:
- Data:
- Tipo de alteracao:
- Arquivos alterados:
- Resultado:
- Impacto:

## 11) Historico de alteracoes
### 2026-05-08
- Tipo: Inicializacao de registro continuo
- Arquivos alterados: multiples arquivos de schema/etl
- Resultado:
  - DW criado e validado
  - ETL piloto funcional para 4 tabelas principais
  - Dependencias estabilizadas para Python 3.14
- Impacto: Projeto pronto para evolucao incremental e dashboarding

### 2026-05-08
- Tipo: Evolucao do ETL para modo incremental
- Arquivos alterados: main.py, loaders/postgres_loader.py, REGISTRO_PROJETO.md
- Resultado:
  - Execucao incremental implementada com checkpoint em etl_metadata
  - Selecao incremental por rotacao de app_id com base no ultimo processado
  - Execucoes de validacao concluidas com sucesso
- Impacto: Pipeline pronto para rotina sem reprocessamento full a cada execucao

### 2026-05-08
- Tipo: Higiene do repositório
- Arquivos alterados: .gitignore, .env.example, arquivos de cache removidos do índice
- Resultado:
  - Arquivos sensiveis e artefatos gerados ignorados corretamente
  - .env.example mantido como template seguro
  - Repositorio limpo e pronto para novos commits
- Impacto: Redução de risco de vazamento de credenciais e ruído no versionamento
