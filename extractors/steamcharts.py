import re
from typing import Dict, Optional

import requests

from config import api_config


class SteamChartsExtractor:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Steam-BI-ETL/1.0"})

    @staticmethod
    def _to_int(value: str) -> Optional[int]:
        if value is None:
            return None
        cleaned = value.replace(",", "").replace(".", "").strip()
        if not cleaned or not cleaned.lstrip("-").isdigit():
            return None
        return int(cleaned)

    @staticmethod
    def _to_float(value: str) -> Optional[float]:
        if value is None:
            return None
        cleaned = value.replace("%", "").replace(",", ".").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None

    def fetch_metrics(self, app_id: int) -> Dict[str, Optional[float]]:
        url = f"https://steamcharts.com/app/{app_id}"
        response = self.session.get(url, timeout=api_config.timeout_seconds)
        if response.status_code != 200:
            return {
                "avg_players": None,
                "peak_players": None,
                "peak_24h": None,
                "all_time_peak": None,
                "gain": None,
                "percent_gain": None,
            }

        html = response.text

        summary_matches = re.findall(r'<span class="num">([^<]+)</span>', html)
        peak_24h = self._to_int(summary_matches[0]) if len(summary_matches) > 0 else None
        all_time_peak = self._to_int(summary_matches[1]) if len(summary_matches) > 1 else None

        row_pattern = re.compile(
            r"<tr>\s*<td>[^<]+</td>\s*<td>([^<]+)</td>\s*<td>([^<]+)</td>\s*<td>([^<]+)</td>\s*<td>([^<]+)</td>",
            re.IGNORECASE,
        )
        row_match = row_pattern.search(html)

        if row_match:
            avg_players = self._to_int(row_match.group(1))
            gain = self._to_int(row_match.group(3))
            percent_gain = self._to_float(row_match.group(4))
            peak_players = self._to_int(row_match.group(2))
        else:
            avg_players = None
            gain = None
            percent_gain = None
            peak_players = None

        return {
            "avg_players": avg_players,
            "peak_players": peak_players,
            "peak_24h": peak_24h,
            "all_time_peak": all_time_peak,
            "gain": gain,
            "percent_gain": percent_gain,
        }
