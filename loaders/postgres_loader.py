from datetime import date, datetime
from typing import Iterable, Tuple

import psycopg

from config import db_config


class PostgresLoader:
    def __init__(self) -> None:
        self.conn = psycopg.connect(
            host=db_config.host,
            port=db_config.port,
            dbname=db_config.name,
            user=db_config.user,
            password=db_config.password,
        )
        self._ensure_dim_jogos_extensions()
        self._ensure_price_history_extensions()

    def _ensure_dim_jogos_extensions(self) -> None:
        sql = f"""
            ALTER TABLE {db_config.schema}.dim_jogos
            ADD COLUMN IF NOT EXISTS short_description TEXT,
            ADD COLUMN IF NOT EXISTS supported_languages TEXT,
            ADD COLUMN IF NOT EXISTS categories TEXT,
            ADD COLUMN IF NOT EXISTS metacritic_score INTEGER,
            ADD COLUMN IF NOT EXISTS required_age INTEGER,
            ADD COLUMN IF NOT EXISTS coming_soon BOOLEAN
        """
        with self.conn.cursor() as cur:
            cur.execute(sql)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def _ensure_price_history_extensions(self) -> None:
        sql = f"""
            ALTER TABLE {db_config.schema}.price_history
            ADD COLUMN IF NOT EXISTS price_initial DECIMAL(10, 2),
            ADD COLUMN IF NOT EXISTS price_final DECIMAL(10, 2),
            ADD COLUMN IF NOT EXISTS discount_percent DECIMAL(5, 2)
        """
        with self.conn.cursor() as cur:
            cur.execute(sql)
        self.conn.commit()

    def upsert_dim_jogos(self, rows: Iterable[Tuple]) -> int:
        rows = list(rows)
        if not rows:
            return 0

        sql = f"""
            INSERT INTO {db_config.schema}.dim_jogos (
                app_id, name, developer, publisher, release_date,
                price, is_free, genres, tags, platforms,
                short_description, supported_languages, categories,
                metacritic_score, required_age, coming_soon
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (app_id) DO UPDATE SET
                name = EXCLUDED.name,
                developer = EXCLUDED.developer,
                publisher = EXCLUDED.publisher,
                release_date = EXCLUDED.release_date,
                price = EXCLUDED.price,
                is_free = EXCLUDED.is_free,
                genres = EXCLUDED.genres,
                tags = EXCLUDED.tags,
                platforms = EXCLUDED.platforms,
                short_description = EXCLUDED.short_description,
                supported_languages = EXCLUDED.supported_languages,
                categories = EXCLUDED.categories,
                metacritic_score = EXCLUDED.metacritic_score,
                required_age = EXCLUDED.required_age,
                coming_soon = EXCLUDED.coming_soon,
                updated_at = CURRENT_TIMESTAMP
        """

        with self.conn.cursor() as cur:
            cur.executemany(sql, rows)
        self.conn.commit()
        return len(rows)

    def upsert_player_metrics(self, rows: Iterable[Tuple]) -> int:
        rows = list(rows)
        if not rows:
            return 0

        sql = f"""
            INSERT INTO {db_config.schema}.player_metrics (
                app_id, date, current_players, avg_players, peak_players,
                peak_24h, all_time_peak, gain, percent_gain
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (app_id, date) DO UPDATE SET
                current_players = EXCLUDED.current_players,
                avg_players = EXCLUDED.avg_players,
                peak_players = EXCLUDED.peak_players,
                peak_24h = EXCLUDED.peak_24h,
                all_time_peak = EXCLUDED.all_time_peak,
                gain = EXCLUDED.gain,
                percent_gain = EXCLUDED.percent_gain
        """

        with self.conn.cursor() as cur:
            cur.executemany(sql, rows)
        self.conn.commit()
        return len(rows)

    def upsert_price_history(self, rows: Iterable[Tuple]) -> int:
        rows = list(rows)
        if not rows:
            return 0

        sql = f"""
            INSERT INTO {db_config.schema}.price_history (
                app_id, date, price, discount, currency,
                price_initial, price_final, discount_percent
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (app_id, date) DO UPDATE SET
                price = EXCLUDED.price,
                discount = EXCLUDED.discount,
                currency = EXCLUDED.currency,
                price_initial = EXCLUDED.price_initial,
                price_final = EXCLUDED.price_final,
                discount_percent = EXCLUDED.discount_percent
        """

        with self.conn.cursor() as cur:
            cur.executemany(sql, rows)
        self.conn.commit()
        return len(rows)

    def upsert_update_frequency(self, rows: Iterable[Tuple]) -> int:
        rows = list(rows)
        if not rows:
            return 0

        sql = f"""
            INSERT INTO {db_config.schema}.update_frequency (
                app_id, update_date, build_id, size_on_disk
            ) VALUES (%s, %s, %s, %s)
            ON CONFLICT (app_id, update_date, build_id) DO UPDATE SET
                size_on_disk = EXCLUDED.size_on_disk
        """

        with self.conn.cursor() as cur:
            cur.executemany(sql, rows)
        self.conn.commit()
        return len(rows)

    def insert_etl_log(
        self,
        etl_name: str,
        status: str,
        records_processed: int,
        records_failed: int = 0,
        error_message: str = None,
        data_source: str = "steam_api",
    ) -> None:
        sql = f"""
            INSERT INTO {db_config.schema}.etl_log (
                etl_name, start_time, end_time, status,
                records_processed, records_failed, error_message, data_source
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        now = datetime.now()
        with self.conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    etl_name,
                    now,
                    now,
                    status,
                    records_processed,
                    records_failed,
                    error_message,
                    data_source,
                ),
            )
        self.conn.commit()

    def get_etl_metadata(self, data_source: str = "steam_api") -> dict | None:
        sql = f"""
            SELECT
                data_source,
                last_successful_run,
                last_app_id_processed,
                last_date_processed,
                total_app_ids
            FROM {db_config.schema}.etl_metadata
            WHERE data_source = %s
        """
        with self.conn.cursor() as cur:
            cur.execute(sql, (data_source,))
            row = cur.fetchone()
        if not row:
            return None

        return {
            "data_source": row[0],
            "last_successful_run": row[1],
            "last_app_id_processed": row[2],
            "last_date_processed": row[3],
            "total_app_ids": row[4],
        }

    def upsert_etl_metadata(
        self,
        data_source: str,
        last_successful_run: datetime,
        last_app_id_processed: int | None,
        last_date_processed: date,
        total_app_ids: int,
    ) -> None:
        sql = f"""
            INSERT INTO {db_config.schema}.etl_metadata (
                data_source,
                last_successful_run,
                last_app_id_processed,
                last_date_processed,
                total_app_ids,
                updated_at
            ) VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (data_source) DO UPDATE SET
                last_successful_run = EXCLUDED.last_successful_run,
                last_app_id_processed = EXCLUDED.last_app_id_processed,
                last_date_processed = EXCLUDED.last_date_processed,
                total_app_ids = EXCLUDED.total_app_ids,
                updated_at = CURRENT_TIMESTAMP
        """
        with self.conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    data_source,
                    last_successful_run,
                    last_app_id_processed,
                    last_date_processed,
                    total_app_ids,
                ),
            )
        self.conn.commit()
