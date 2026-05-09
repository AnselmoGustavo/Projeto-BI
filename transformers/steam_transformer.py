from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple


def _parse_release_date(raw: Dict[str, Any]) -> Optional[date]:
    raw_date = (raw or {}).get("date")
    if not raw_date:
        return None

    cleaned = raw_date.replace(",", "")
    for fmt in ("%d %b %Y", "%b %d %Y", "%d %B %Y", "%B %d %Y"):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None


def _to_price_brl(details: Dict[str, Any]) -> Optional[Decimal]:
    if details.get("is_free"):
        return Decimal("0.00")

    price = details.get("price_overview") or {}
    final_value = price.get("final")
    if final_value is None:
        return None

    return (Decimal(final_value) / Decimal("100")).quantize(Decimal("0.01"))


def build_dim_jogos_row(app_id: int, details: Dict[str, Any]) -> Tuple:
    developers = ", ".join(details.get("developers") or [])
    publishers = ", ".join(details.get("publishers") or [])
    genres = ", ".join([g.get("description", "") for g in (details.get("genres") or []) if g.get("description")])

    platforms_obj = details.get("platforms") or {}
    platforms = ", ".join([name for name, enabled in platforms_obj.items() if enabled])

    return (
        app_id,
        (details.get("name") or f"APP_{app_id}")[:255],
        developers[:255] if developers else None,
        publishers[:255] if publishers else None,
        _parse_release_date(details.get("release_date") or {}),
        _to_price_brl(details),
        bool(details.get("is_free", False)),
        genres or None,
        None,
        platforms or None,
    )


def build_player_metrics_row(app_id: int, current_players: Optional[int]) -> Tuple:
    return (
        app_id,
        date.today(),
        current_players,
        None,
        None,
        None,
        None,
        None,
        None,
    )


def build_player_metrics_row_enriched(
    app_id: int,
    current_players: Optional[int],
    charts: Optional[Dict[str, Any]],
) -> Tuple:
    charts = charts or {}

    return (
        app_id,
        date.today(),
        current_players,
        charts.get("avg_players"),
        charts.get("peak_players"),
        charts.get("peak_24h"),
        charts.get("all_time_peak"),
        charts.get("gain"),
        charts.get("percent_gain"),
    )


def build_price_history_row(app_id: int, details: Dict[str, Any]) -> Tuple:
    price = _to_price_brl(details)
    initial = details.get("price_overview", {}).get("initial")
    final = details.get("price_overview", {}).get("final")

    discount = None
    if initial and final is not None and int(initial) > 0:
        discount_raw = (Decimal(initial) - Decimal(final)) / Decimal(initial) * Decimal("100")
        discount = discount_raw.quantize(Decimal("0.01"))

    return (
        app_id,
        date.today(),
        price,
        discount,
        "BRL",
    )


def build_update_frequency_row(app_id: int, details: Dict[str, Any]) -> Tuple:
    build_id = details.get("steam_appid") or app_id
    size_on_disk = details.get("required_age")
    if size_on_disk is not None:
        try:
            size_on_disk = int(size_on_disk)
        except (TypeError, ValueError):
            size_on_disk = None

    return (
        app_id,
        date.today(),
        int(build_id),
        size_on_disk,
    )
