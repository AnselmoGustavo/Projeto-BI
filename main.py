import argparse
import logging
from datetime import date, datetime
from typing import List

from extractors.steam_api import SteamApiExtractor
from extractors.steamcharts import SteamChartsExtractor
from loaders.postgres_loader import PostgresLoader
from transformers.steam_transformer import (
    build_dim_jogos_row,
    build_player_metrics_row_enriched,
    build_price_history_row,
    build_update_frequency_row,
)


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("steam_etl")


def _select_incremental_window(app_ids: List[int], limit: int, last_app_id: int | None) -> List[int]:
    if not app_ids:
        return []

    ordered = sorted(list(set(app_ids)))
    if last_app_id in ordered:
        start = ordered.index(last_app_id) + 1
    else:
        start = 0

    rotated = ordered[start:] + ordered[:start]
    return rotated[:limit]


def run_etl(limit: int, mode: str = "incremental") -> None:
    extractor = SteamApiExtractor()
    charts_extractor = SteamChartsExtractor()
    loader = PostgresLoader()

    dim_rows: List[tuple] = []
    metric_rows: List[tuple] = []
    price_rows: List[tuple] = []
    update_rows: List[tuple] = []
    failed = 0
    candidate_ids: List[int] = []

    try:
        logger.info("Fetching app list (limit=%s, mode=%s)", limit, mode)
        app_ids = extractor.list_app_ids(max_items=max(limit * 8, limit))

        if mode == "incremental":
            metadata = loader.get_etl_metadata(data_source="steam_api")
            last_app_id = metadata.get("last_app_id_processed") if metadata else None
            candidate_ids = _select_incremental_window(app_ids, limit=limit, last_app_id=last_app_id)
            logger.info(
                "Incremental checkpoint last_app_id=%s -> selected=%s",
                last_app_id,
                len(candidate_ids),
            )
        else:
            candidate_ids = app_ids[:limit]

        for app_id in candidate_ids:
            try:
                details = extractor.fetch_app_details(app_id)
                extractor.throttle()
                if not details or details.get("type") != "game":
                    continue

                current_players = extractor.fetch_current_players(app_id)
                extractor.throttle()
                charts_metrics = charts_extractor.fetch_metrics(app_id)
                extractor.throttle()

                dim_rows.append(build_dim_jogos_row(app_id, details))
                metric_rows.append(build_player_metrics_row_enriched(app_id, current_players, charts_metrics))
                price_rows.append(build_price_history_row(app_id, details))
                update_rows.append(build_update_frequency_row(app_id, details))
            except Exception as app_err:
                failed += 1
                logger.warning("Skipping app %s due to error: %s", app_id, app_err)

        loaded_dim = loader.upsert_dim_jogos(dim_rows)
        loaded_metrics = loader.upsert_player_metrics(metric_rows)
        loaded_price = loader.upsert_price_history(price_rows)
        loaded_updates = loader.upsert_update_frequency(update_rows)
        processed = loaded_dim + loaded_metrics + loaded_price + loaded_updates

        last_processed_app_id = candidate_ids[-1] if candidate_ids else None
        loader.upsert_etl_metadata(
            data_source="steam_api",
            last_successful_run=datetime.now(),
            last_app_id_processed=last_processed_app_id,
            last_date_processed=date.today(),
            total_app_ids=len(candidate_ids),
        )

        loader.insert_etl_log(
            etl_name=f"etl_steam_api_{mode}",
            status="sucesso",
            records_processed=processed,
            records_failed=failed,
        )
        logger.info(
            "ETL finished. dim_jogos=%s player_metrics=%s price_history=%s update_frequency=%s failed=%s",
            loaded_dim,
            loaded_metrics,
            loaded_price,
            loaded_updates,
            failed,
        )
    except Exception as err:
        loader.insert_etl_log(
            etl_name=f"etl_steam_api_{mode}",
            status="erro",
            records_processed=0,
            records_failed=failed,
            error_message=str(err),
        )
        raise
    finally:
        loader.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Steam BI ETL Pilot")
    parser.add_argument("--limit", type=int, default=30, help="Number of games to load")
    parser.add_argument(
        "--mode",
        choices=["incremental", "full"],
        default="incremental",
        help="Execution mode: incremental uses etl_metadata checkpoint",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_etl(limit=args.limit, mode=args.mode)
