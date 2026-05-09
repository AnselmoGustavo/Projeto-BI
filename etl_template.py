"""
STEAM BI - ETL Pipeline
Sistema de extração, transformação e carga de dados da Steam

Estrutura do projeto:
├── config.py              # Configurações e variáveis de ambiente
├── extractors/
│   ├── steam_api.py       # Extrator da Steam Web API
│   ├── steamcharts.py     # Extrator do SteamCharts (scraping)
│   └── steamdb.py         # Extrator do SteamDB (scraping)
├── transformers/
│   ├── data_cleaner.py    # Limpeza de dados
│   ├── data_validator.py  # Validação de dados
│   └── data_normalizer.py # Normalização e padronização
├── loaders/
│   ├── db_loader.py       # Carga no PostgreSQL
│   └── logger.py          # Logging e auditoria
├── main.py                # Orquestração do ETL
├── requirements.txt       # Dependências Python
├── .env.example           # Template de variáveis de ambiente
└── data/
    ├── raw/               # Dados brutos extraídos
    ├── processed/         # Dados processados
    └── logs/              # Logs de execução
"""

# ====================================================================
# ARQUIVO: requirements.txt
# ====================================================================
"""
# requirements.txt - Dependências do projeto

# Conexão com Banco de Dados
psycopg2-binary==2.9.9
sqlalchemy==2.0.23

# APIs e Web Scraping
requests==2.31.0
beautifulsoup4==4.12.2
lxml==4.9.3

# Manipulação de dados
pandas==2.1.3
numpy==1.26.2

# Configuração de ambiente
python-dotenv==1.0.0

# Logging e monitoramento
python-logging-loki==0.3.2

# Agendamento de tarefas
APScheduler==3.10.4

# Utilitários
python-dateutil==2.8.2
pytz==2023.3

# Testes
pytest==7.4.3
pytest-cov==4.1.0
"""

# ====================================================================
# ARQUIVO: .env.example
# ====================================================================
"""
# .env.example - Template de variáveis de ambiente

# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=steam_dw
DB_USER=postgres
DB_PASSWORD=sua_senha_aqui
DB_SCHEMA=steam_dw

# Steam API
STEAM_API_KEY=sua_chave_api_aqui
STEAM_API_BASE_URL=https://api.steampowered.com

# Configuração de ETL
ETL_LOG_DIR=./data/logs
ETL_DATA_RAW_DIR=./data/raw
ETL_DATA_PROCESSED_DIR=./data/processed
ETL_BATCH_SIZE=100
ETL_REQUEST_DELAY=1.5
ETL_RETRY_ATTEMPTS=3

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Scraping
SCRAPE_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
SCRAPE_TIMEOUT=10
SCRAPE_RETRY_DELAY=2
"""

# ====================================================================
# ARQUIVO: config.py
# ====================================================================
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv()

# Configurações de Banco de Dados
DATABASE = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'steam_dw'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'schema': os.getenv('DB_SCHEMA', 'steam_dw'),
}

# Configurações de API
STEAM_API_KEY = os.getenv('STEAM_API_KEY', '')
STEAM_API_BASE_URL = os.getenv('STEAM_API_BASE_URL', 'https://api.steampowered.com')

# Configurações de ETL
ETL_CONFIG = {
    'batch_size': int(os.getenv('ETL_BATCH_SIZE', 100)),
    'request_delay': float(os.getenv('ETL_REQUEST_DELAY', 1.5)),
    'retry_attempts': int(os.getenv('ETL_RETRY_ATTEMPTS', 3)),
    'log_dir': os.getenv('ETL_LOG_DIR', './data/logs'),
    'raw_data_dir': os.getenv('ETL_DATA_RAW_DIR', './data/raw'),
    'processed_data_dir': os.getenv('ETL_DATA_PROCESSED_DIR', './data/processed'),
}

# Configurações de Scraping
SCRAPING_CONFIG = {
    'user_agent': os.getenv('SCRAPE_USER_AGENT',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
    'timeout': int(os.getenv('SCRAPE_TIMEOUT', 10)),
    'retry_delay': float(os.getenv('SCRAPE_RETRY_DELAY', 2)),
}

# Criar diretórios se não existirem
for dir_path in [ETL_CONFIG['log_dir'], ETL_CONFIG['raw_data_dir'], 
                   ETL_CONFIG['processed_data_dir']]:
    Path(dir_path).mkdir(parents=True, exist_ok=True)

# Configuração de Logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(
            f\"{ETL_CONFIG['log_dir']}/steam_etl_{datetime.now().strftime('%Y%m%d')}.log\"
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
"""

# ====================================================================
# ARQUIVO: extractors/steam_api.py
# ====================================================================
"""
import requests
import logging
import time
from config import STEAM_API_KEY, STEAM_API_BASE_URL, ETL_CONFIG
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class SteamAPIExtractor:
    \"\"\"
    Extrator de dados da Steam Web API
    Responsável por coletar lista de jogos e dados relacionados
    \"\"\"
    
    def __init__(self):
        self.base_url = STEAM_API_BASE_URL
        self.api_key = STEAM_API_KEY
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Steam-BI-Project/1.0'})
        
    def obter_lista_jogos_brasileiro(self):
        \"\"\"
        Obtém lista de aplicativos disponíveis na Steam
        Filtra para aplicações com suporte ao português brasileiro
        
        Returns:
            list: Lista de app_ids
        \"\"\"
        logger.info("Iniciando extração da lista de jogos...")
        
        try:
            url = f"{self.base_url}/ISteamApps/GetAppList/v1/"
            response = self.session.get(url, timeout=ETL_CONFIG['timeout'])
            response.raise_for_status()
            
            apps = response.json()['applist']['apps']
            logger.info(f"Total de apps encontrados: {len(apps)}")
            
            return [app['appid'] for app in apps if app.get('type') == 'game']
            
        except Exception as e:
            logger.error(f"Erro ao obter lista de jogos: {e}")
            raise
    
    def obter_dados_jogo(self, app_id):
        \"\"\"
        Obtém detalhes de um jogo específico
        
        Args:
            app_id (int): ID da aplicação na Steam
            
        Returns:
            dict: Dados do jogo
        \"\"\"
        url = f"{self.base_url}/appdetails"
        params = {
            'appids': app_id,
            'l': 'portuguese',
            'cc': 'BR'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=ETL_CONFIG['timeout'])
            response.raise_for_status()
            
            data = response.json()
            if str(app_id) in data and data[str(app_id)]['success']:
                return data[str(app_id)]['data']
            else:
                logger.warning(f"Dados não encontrados ou erro para app_id: {app_id}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao obter dados do jogo {app_id}: {e}")
            return None
    
    def obter_jogadores_simultaneos(self, app_id):
        \"\"\"
        Obtém número de jogadores simultâneos em tempo real
        
        Args:
            app_id (int): ID da aplicação
            
        Returns:
            dict: Dados de jogadores
        \"\"\"
        url = f"{self.base_url}/ISteamUserStats/GetNumberOfCurrentPlayers/v1/"
        params = {'appid': app_id}
        
        try:
            response = self.session.get(url, params=params, timeout=ETL_CONFIG['timeout'])
            response.raise_for_status()
            
            result = response.json()
            if result['response']['result'] == 1:
                return {
                    'app_id': app_id,
                    'current_players': result['response']['player_count'],
                    'timestamp': datetime.now().isoformat()
                }
            return None
            
        except Exception as e:
            logger.error(f"Erro ao obter jogadores simultâneos {app_id}: {e}")
            return None

    def extrair_dados_batch(self, app_ids_list):
        \"\"\"
        Extrai dados para múltiplos jogos com controle de rate limiting
        
        Args:
            app_ids_list (list): Lista de app_ids
            
        Yields:
            dict: Dados extraídos de cada jogo
        \"\"\"
        for idx, app_id in enumerate(app_ids_list):
            if idx % 10 == 0:
                logger.info(f"Progresso: {idx}/{len(app_ids_list)} jogos processados")
            
            dados_jogo = self.obter_dados_jogo(app_id)
            jogadores = self.obter_jogadores_simultaneos(app_id)
            
            if dados_jogo:
                yield {
                    'app_id': app_id,
                    'game_data': dados_jogo,
                    'current_players': jogadores
                }
            
            # Rate limiting - respeitar limites da API
            time.sleep(ETL_CONFIG['request_delay'])
"""

# ====================================================================
# ARQUIVO: transformers/data_cleaner.py
# ====================================================================
"""
import logging
import pandas as pd
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class DataCleaner:
    \"\"\"
    Responsável pela limpeza e validação de dados extraídos
    \"\"\"
    
    @staticmethod
    def limpar_jogo(jogo_raw):
        \"\"\"
        Limpa e normaliza dados de um jogo
        
        Args:
            jogo_raw (dict): Dados brutos do jogo
            
        Returns:
            dict: Dados limpos ou None se inválido
        \"\"\"
        try:
            jogo_limpo = {
                'app_id': jogo_raw.get('app_id'),
                'name': jogo_raw.get('game_data', {}).get('name', '').strip(),
                'developer': ', '.join(jogo_raw.get('game_data', {}).get('developers', [])),
                'publisher': ', '.join(jogo_raw.get('game_data', {}).get('publishers', [])),
                'release_date': DataCleaner._parse_data(
                    jogo_raw.get('game_data', {}).get('release_date')
                ),
                'price': DataCleaner._parse_price(
                    jogo_raw.get('game_data', {}).get('price_overview')
                ),
                'is_free': jogo_raw.get('game_data', {}).get('is_free', False),
                'genres': json.dumps(jogo_raw.get('game_data', {}).get('genres', [])),
                'tags': json.dumps(jogo_raw.get('game_data', {}).get('tags', [])),
                'platforms': json.dumps(jogo_raw.get('game_data', {}).get('platforms', {})),
            }
            
            # Validações básicas
            if not jogo_limpo['app_id'] or not jogo_limpo['name']:
                logger.warning(f"Jogo inválido: faltam campos obrigatórios")
                return None
                
            return jogo_limpo
            
        except Exception as e:
            logger.error(f"Erro ao limpar dados do jogo: {e}")
            return None
    
    @staticmethod
    def _parse_data(data_str):
        \"\"\"Parseia strings de data para formato DATE\"\"\"
        try:
            if not data_str:
                return None
            # Steam usa formato: "3 Jan, 2020"
            return pd.to_datetime(data_str).date()
        except:
            return None
    
    @staticmethod
    def _parse_price(price_obj):
        \"\"\"Extrai preço em BRL de objeto de preço\"\"\"
        try:
            if not price_obj:
                return None
            return price_obj.get('final_formatted', '0').replace('R$', '').strip()
        except:
            return None
    
    @staticmethod
    def validar_metricas_jogadores(metricas):
        \"\"\"
        Valida dados de métricas de jogadores
        
        Returns:
            bool: True se válido
        \"\"\"
        validacoes = [
            metricas.get('app_id') > 0,
            metricas.get('current_players', 0) >= 0,
            metricas.get('avg_players', 0) >= 0,
            metricas.get('peak_players', 0) >= 0,
        ]
        
        return all(validacoes)
"""

# ====================================================================
# ARQUIVO: loaders/db_loader.py
# ====================================================================
"""
import psycopg2
from psycopg2.extras import execute_batch
import logging
from config import DATABASE
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseLoader:
    \"\"\"
    Responsável pela carga de dados no PostgreSQL
    \"\"\"
    
    def __init__(self):
        self.conn = None
        self.cursor = None
        self._conectar()
    
    def _conectar(self):
        \"\"\"Estabelece conexão com banco de dados\"\"\"
        try:
            self.conn = psycopg2.connect(
                host=DATABASE['host'],
                port=DATABASE['port'],
                database=DATABASE['database'],
                user=DATABASE['user'],
                password=DATABASE['password']
            )
            self.cursor = self.conn.cursor()
            logger.info("Conexão com banco de dados estabelecida")
        except Exception as e:
            logger.error(f"Erro ao conectar ao banco de dados: {e}")
            raise
    
    def carregar_jogos_batch(self, jogos_lista):
        \"\"\"
        Insere/atualiza jogos em lote (UPSERT)
        
        Args:
            jogos_lista (list): Lista de dicionários com dados de jogos
            
        Returns:
            int: Número de registros processados
        \"\"\"
        sql = f\"\"\"
            INSERT INTO {DATABASE['schema']}.dim_jogos 
            (app_id, name, developer, publisher, release_date, price, 
             is_free, genres, tags, platforms, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (app_id) DO UPDATE SET
                name = EXCLUDED.name,
                price = EXCLUDED.price,
                updated_at = CURRENT_TIMESTAMP
        \"\"\"
        
        try:
            dados_tuples = [
                (j['app_id'], j['name'], j['developer'], j['publisher'],
                 j['release_date'], j['price'], j['is_free'], j['genres'],
                 j['tags'], j['platforms'])
                for j in jogos_lista
            ]
            
            execute_batch(self.cursor, sql, dados_tuples)
            self.conn.commit()
            
            logger.info(f"Carregados {len(jogos_lista)} jogos com sucesso")
            return len(jogos_lista)
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Erro ao carregar jogos: {e}")
            raise
    
    def carregar_metricas_batch(self, metricas_lista):
        \"\"\"
        Insere métricas de jogadores em lote
        \"\"\"
        sql = f\"\"\"
            INSERT INTO {DATABASE['schema']}.player_metrics
            (app_id, date, current_players, avg_players, peak_players,
             peak_24h, all_time_peak, gain, percent_gain)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (app_id, date) DO UPDATE SET
                current_players = EXCLUDED.current_players,
                avg_players = EXCLUDED.avg_players
        \"\"\"
        
        try:
            dados_tuples = [
                (m['app_id'], m['date'], m['current_players'],
                 m['avg_players'], m['peak_players'], m['peak_24h'],
                 m['all_time_peak'], m['gain'], m['percent_gain'])
                for m in metricas_lista
            ]
            
            execute_batch(self.cursor, sql, dados_tuples)
            self.conn.commit()
            
            logger.info(f"Carregadas {len(metricas_lista)} métricas com sucesso")
            return len(metricas_lista)
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Erro ao carregar métricas: {e}")
            raise
    
    def registrar_etl_log(self, etl_name, status, records_processed, 
                         records_failed=0, error_msg=None, data_source=None):
        \"\"\"Registra evento de ETL no banco\"\"\"
        sql = f\"\"\"
            INSERT INTO {DATABASE['schema']}.etl_log
            (etl_name, start_time, end_time, status, records_processed,
             records_failed, error_message, data_source)
            VALUES (%s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s, %s, %s, %s, %s)
        \"\"\"
        
        try:
            self.cursor.execute(sql, (etl_name, status, records_processed,
                                      records_failed, error_msg, data_source))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Erro ao registrar ETL log: {e}")
    
    def fechar_conexao(self):
        \"\"\"Fecha a conexão com banco de dados\"\"\"
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Conexão com banco de dados fechada")
    
    def __del__(self):
        \"\"\"Garante fechamento da conexão ao destruir objeto\"\"\"
        self.fechar_conexao()
"""

# ====================================================================
# ARQUIVO: main.py - Orquestração do ETL
# ====================================================================
"""
import logging
import sys
from datetime import datetime
from extractors.steam_api import SteamAPIExtractor
from transformers.data_cleaner import DataCleaner
from loaders.db_loader import DatabaseLoader
from config import ETL_CONFIG

logger = logging.getLogger(__name__)

def executar_etl():
    \"\"\"
    Executa pipeline completo de ETL
    
    Fluxo:
    1. EXTRACT: Coletar dados das fontes
    2. TRANSFORM: Limpar e validar dados
    3. LOAD: Carregar no Data Warehouse
    4. LOG: Registrar execução
    \"\"\"
    
    extrator = None
    carregador = None
    inicio = datetime.now()
    
    try:
        logger.info("="*60)
        logger.info("INICIANDO PIPELINE ETL")
        logger.info("="*60)
        
        # FASE 1: EXTRAÇÃO
        logger.info("📊 FASE 1: EXTRAÇÃO DE DADOS")
        extrator = SteamAPIExtractor()
        app_ids = extrator.obter_lista_jogos_brasileiro()
        
        # Limitar para testes iniciais
        app_ids_teste = app_ids[:100]  # Remover para produção
        logger.info(f"Extraindo dados de {len(app_ids_teste)} jogos")
        
        # FASE 2: TRANSFORMAÇÃO
        logger.info("🔄 FASE 2: TRANSFORMAÇÃO E LIMPEZA")
        jogos_limpos = []
        metricas_coletadas = []
        
        for idx, dados_bruto in enumerate(extrator.extrair_dados_batch(app_ids_teste)):
            if idx % 10 == 0:
                logger.info(f"Processados {idx} registros")
            
            # Limpar dados do jogo
            jogo_limpo = DataCleaner.limpar_jogo(dados_bruto)
            if jogo_limpo:
                jogos_limpos.append(jogo_limpo)
            
            # Validar métricas
            if dados_bruto.get('current_players'):
                if DataCleaner.validar_metricas_jogadores(dados_bruto['current_players']):
                    metricas_coletadas.append(dados_bruto['current_players'])
        
        logger.info(f"Jogos limpos: {len(jogos_limpos)}")
        logger.info(f"Métricas coletadas: {len(metricas_coletadas)}")
        
        # FASE 3: CARGA
        logger.info("💾 FASE 3: CARREGAMENTO NO DATA WAREHOUSE")
        carregador = DatabaseLoader()
        
        registros_jogo = carregador.carregar_jogos_batch(jogos_limpos)
        registros_metricas = carregador.carregar_metricas_batch(metricas_coletadas)
        
        # FASE 4: LOGGING
        total_processados = registros_jogo + registros_metricas
        tempo_execucao = (datetime.now() - inicio).total_seconds()
        
        carregador.registrar_etl_log(
            etl_name='etl_completo',
            status='sucesso',
            records_processed=total_processados,
            data_source='steam_api'
        )
        
        logger.info("="*60)
        logger.info(f"✅ PIPELINE CONCLUÍDO COM SUCESSO")
        logger.info(f"   Registros processados: {total_processados}")
        logger.info(f"   Tempo de execução: {tempo_execucao:.2f} segundos")
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ ERRO NO PIPELINE ETL: {e}", exc_info=True)
        
        if carregador:
            carregador.registrar_etl_log(
                etl_name='etl_completo',
                status='erro',
                records_processed=0,
                error_msg=str(e),
                data_source='steam_api'
            )
        
        return False
        
    finally:
        if carregador:
            carregador.fechar_conexao()
        logger.info("Encerrando pipeline ETL...")

if __name__ == '__main__':
    sucesso = executar_etl()
    sys.exit(0 if sucesso else 1)
"""

# ====================================================================
# INSTRUÇÕES DE EXECUÇÃO
# ====================================================================
"""
PASSO 1: Preparar ambiente
   pip install -r requirements.txt

PASSO 2: Configurar variáveis
   cp .env.example .env
   # Editar .env com suas credenciais

PASSO 3: Criar banco de dados
   psql -U postgres
   CREATE DATABASE steam_dw;
   \\c steam_dw
   \\i schema_steam_dw.sql

PASSO 4: Executar ETL
   python main.py

PASSO 5: Monitorar logs
   tail -f ./data/logs/steam_etl_*.log

PASSO 6: Agendar execução (cron)
   0 2 * * * cd /caminho/projeto && python main.py
"""
"""
