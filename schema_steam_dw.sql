-- ====================================================================
-- SCRIPT DE CRIAÇÃO - DATA WAREHOUSE STEAM BRASIL
-- ====================================================================
-- Banco de Dados: steam_dw
-- SGBD: PostgreSQL
-- Data: 2026
-- ====================================================================

-- Criar schema
CREATE SCHEMA IF NOT EXISTS steam_dw;
SET search_path TO steam_dw, public;

-- ====================================================================
-- TABELA DIMENSIONAL: DIM_JOGOS
-- ====================================================================
-- Armazena informações estáticas dos jogos
-- Atualizada periodicamente quando há mudanças de preço/nome/etc
-- ====================================================================
CREATE TABLE IF NOT EXISTS dim_jogos (
    app_id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    developer VARCHAR(255),
    publisher VARCHAR(255),
    release_date DATE,
    price DECIMAL(10, 2),
    is_free BOOLEAN DEFAULT FALSE,
    genres TEXT, -- JSON array ou string separada por vírgula
    tags TEXT, -- JSON array ou string separada por vírgula
    platforms TEXT, -- JSON array ou string separada por vírgula
    short_description TEXT,
    supported_languages TEXT,
    categories TEXT,
    metacritic_score INTEGER,
    required_age INTEGER,
    coming_soon BOOLEAN,
    country VARCHAR(10) DEFAULT 'BR', -- Brasil
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para dim_jogos
CREATE INDEX idx_dim_jogos_name ON dim_jogos(name);
CREATE INDEX idx_dim_jogos_release_date ON dim_jogos(release_date);
CREATE INDEX idx_dim_jogos_is_free ON dim_jogos(is_free);

-- ====================================================================
-- TABELA FATO: PLAYER_METRICS
-- ====================================================================
-- Armazena métricas de jogadores por data
-- Dados históricos e em tempo real
-- Cardinality: Alta (múltiplos registros por app_id)
-- ====================================================================
CREATE TABLE IF NOT EXISTS player_metrics (
    id SERIAL PRIMARY KEY,
    app_id INTEGER NOT NULL REFERENCES dim_jogos(app_id),
    date DATE NOT NULL,
    current_players INTEGER,
    avg_players INTEGER,
    peak_players INTEGER,
    peak_24h INTEGER,
    all_time_peak INTEGER,
    gain INTEGER, -- crescimento/queda mensal
    percent_gain DECIMAL(10, 2), -- percentual de crescimento
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_player_metrics UNIQUE(app_id, date)
);

-- Índices para player_metrics
CREATE INDEX idx_player_metrics_app_id ON player_metrics(app_id);
CREATE INDEX idx_player_metrics_date ON player_metrics(date);
CREATE INDEX idx_player_metrics_app_date ON player_metrics(app_id, date);
CREATE INDEX idx_player_metrics_current_players ON player_metrics(current_players);

-- ====================================================================
-- TABELA FATO: PRICE_HISTORY
-- ====================================================================
-- Armazena histórico de preços e descontos
-- Rastreia mudanças de preço ao longo do tempo
-- ====================================================================
CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    app_id INTEGER NOT NULL REFERENCES dim_jogos(app_id),
    date DATE NOT NULL,
    price DECIMAL(10, 2),
    discount DECIMAL(5, 2), -- percentual (0-100)
    currency VARCHAR(3) DEFAULT 'BRL',
    price_initial DECIMAL(10, 2),
    price_final DECIMAL(10, 2),
    discount_percent DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_price_history UNIQUE(app_id, date)
);

-- Índices para price_history
CREATE INDEX idx_price_history_app_id ON price_history(app_id);
CREATE INDEX idx_price_history_date ON price_history(date);
CREATE INDEX idx_price_history_app_date ON price_history(app_id, date);
CREATE INDEX idx_price_history_discount ON price_history(discount);

-- ====================================================================
-- TABELA FATO: UPDATE_FREQUENCY
-- ====================================================================
-- Armazena histórico de atualizações dos jogos
-- Rastreia releases, patches e atualizações
-- ====================================================================
CREATE TABLE IF NOT EXISTS update_frequency (
    id SERIAL PRIMARY KEY,
    app_id INTEGER NOT NULL REFERENCES dim_jogos(app_id),
    update_date DATE NOT NULL,
    build_id INTEGER,
    size_on_disk BIGINT, -- tamanho em bytes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_update_frequency UNIQUE(app_id, update_date, build_id)
);

-- Índices para update_frequency
CREATE INDEX idx_update_frequency_app_id ON update_frequency(app_id);
CREATE INDEX idx_update_frequency_date ON update_frequency(update_date);
CREATE INDEX idx_update_frequency_app_date ON update_frequency(app_id, update_date);

-- ====================================================================
-- TABELA DE CONTROLE: ETL_LOG
-- ====================================================================
-- Monitoramento e auditoria do processo ETL
-- Rastreia todas as execuções do pipeline
-- ====================================================================
CREATE TABLE IF NOT EXISTS etl_log (
    id SERIAL PRIMARY KEY,
    etl_name VARCHAR(100) NOT NULL, -- 'extract_api', 'extract_scrape', 'transform', 'load'
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status VARCHAR(20) NOT NULL, -- 'em_progresso', 'sucesso', 'erro', 'parcial'
    records_processed INTEGER,
    records_failed INTEGER DEFAULT 0,
    error_message TEXT,
    data_source VARCHAR(50), -- 'steam_api', 'steamcharts', 'steamdb'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para etl_log
CREATE INDEX idx_etl_log_etl_name ON etl_log(etl_name);
CREATE INDEX idx_etl_log_status ON etl_log(status);
CREATE INDEX idx_etl_log_created_at ON etl_log(created_at);

-- ====================================================================
-- TABELA DE CONTROLE: ETL_METADATA
-- ====================================================================
-- Armazena informações de última execução para incrementalidade
-- ====================================================================
CREATE TABLE IF NOT EXISTS etl_metadata (
    id SERIAL PRIMARY KEY,
    data_source VARCHAR(50) NOT NULL UNIQUE, -- 'steam_api', 'steamcharts', 'steamdb'
    last_successful_run TIMESTAMP,
    last_app_id_processed INTEGER,
    last_date_processed DATE,
    total_app_ids BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================================
-- VIEW: ULTIMAS_METRICAS_POR_JOGO
-- ====================================================================
-- Últimas métricas de cada jogo (últimas 30 dias)
-- ====================================================================
CREATE OR REPLACE VIEW ultimas_metricas_por_jogo AS
SELECT 
    d.app_id,
    d.name,
    d.price,
    d.is_free,
    pm.date,
    pm.current_players,
    pm.avg_players,
    pm.peak_players,
    pm.percent_gain,
    ROW_NUMBER() OVER (PARTITION BY d.app_id ORDER BY pm.date DESC) as dias_desde_ultima_metrica
FROM dim_jogos d
LEFT JOIN player_metrics pm ON d.app_id = pm.app_id
WHERE pm.date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY d.app_id, pm.date DESC;

-- ====================================================================
-- VIEW: JOGOS_EM_ALTA
-- ====================================================================
-- Jogos com maior crescimento de jogadores (últimos 30 dias)
-- ====================================================================
CREATE OR REPLACE VIEW jogos_em_alta AS
SELECT 
    d.app_id,
    d.name,
    d.price,
    pm_recente.current_players,
    pm_recente.avg_players,
    pm_recente.percent_gain,
    pm_recente.date as ultima_atualizacao
FROM dim_jogos d
INNER JOIN (
    SELECT app_id, current_players, avg_players, percent_gain, date,
           ROW_NUMBER() OVER (PARTITION BY app_id ORDER BY date DESC) as rn
    FROM player_metrics
    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
) pm_recente ON d.app_id = pm_recente.app_id
WHERE pm_recente.rn = 1 AND pm_recente.percent_gain > 0
ORDER BY pm_recente.percent_gain DESC;

-- ====================================================================
-- PROCEDIMENTO: LIMPAR_DADOS_ANTIGOS
-- ====================================================================
-- Remove dados com mais de X anos para manter o DW otimizado
-- ====================================================================
CREATE OR REPLACE FUNCTION limpar_dados_antigos(anos INTEGER DEFAULT 2)
RETURNS TABLE(registros_deletados BIGINT, tabela_processada VARCHAR) AS $$
DECLARE
    data_limite DATE := CURRENT_DATE - (anos * INTERVAL '1 year');
    deletados BIGINT;
BEGIN
    -- Limpar player_metrics
    DELETE FROM player_metrics WHERE date < data_limite;
    deletados := ROW_COUNT;
    RETURN QUERY SELECT deletados::BIGINT, 'player_metrics'::VARCHAR;
    
    -- Limpar price_history
    DELETE FROM price_history WHERE date < data_limite;
    deletados := ROW_COUNT;
    RETURN QUERY SELECT deletados::BIGINT, 'price_history'::VARCHAR;
    
    -- Limpar update_frequency
    DELETE FROM update_frequency WHERE update_date < data_limite;
    deletados := ROW_COUNT;
    RETURN QUERY SELECT deletados::BIGINT, 'update_frequency'::VARCHAR;
END;
$$ LANGUAGE plpgsql;

-- ====================================================================
-- PROCEDIMENTO: REGISTRAR_ETL
-- ====================================================================
-- Registra eventos do ETL de forma centralizada
-- ====================================================================
CREATE OR REPLACE FUNCTION registrar_etl(
    p_etl_name VARCHAR,
    p_status VARCHAR,
    p_records_processed INTEGER,
    p_records_failed INTEGER DEFAULT 0,
    p_error_message TEXT DEFAULT NULL,
    p_data_source VARCHAR DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    v_id INTEGER;
BEGIN
    INSERT INTO etl_log (
        etl_name, start_time, end_time, status, records_processed,
        records_failed, error_message, data_source
    ) VALUES (
        p_etl_name, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, p_status,
        p_records_processed, p_records_failed, p_error_message, p_data_source
    )
    RETURNING id INTO v_id;
    
    RETURN v_id;
END;
$$ LANGUAGE plpgsql;

-- ====================================================================
-- COMMITS E FINALIZAÇÃO
-- ====================================================================
COMMIT;

-- Verificar tabelas criadas
SELECT schemaname, tablename 
FROM pg_tables 
WHERE schemaname = 'steam_dw'
ORDER BY tablename;
