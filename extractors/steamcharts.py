import re
from datetime import datetime
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
        cleaned = value.replace(",", "").strip()
        if not cleaned:
            return None
        try:
            return int(round(float(cleaned)))
        except ValueError:
            return None

    @staticmethod
    def _to_float(value: str) -> Optional[float]:
        if value is None:
            return None
        cleaned = value.replace("%", "").replace(",", ".").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None

    @staticmethod
    def _parse_month_label(label: str):
        cleaned = re.sub(r"\s+", " ", (label or "").strip())
        for fmt in ("%B %Y", "%b %Y"):
            try:
                parsed = datetime.strptime(cleaned, fmt)
                return parsed.date().replace(day=1)
            except ValueError:
                continue
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
                "monthly_history": [],
            }

        html = response.text

        summary_matches = re.findall(r'<span class="num">([^<]+)</span>', html)
        peak_24h = self._to_int(summary_matches[0]) if len(summary_matches) > 0 else None
        all_time_peak = self._to_int(summary_matches[1]) if len(summary_matches) > 1 else None

        history_pattern = re.compile(
            r"<tr[^>]*>\s*"
            r"<td[^>]*>(.*?)</td>\s*"
            r"<td[^>]*>([^<]+)</td>\s*"
            r"<td[^>]*>([^<]+)</td>\s*"
            r"<td[^>]*>([^<]+)</td>\s*"
            r"<td[^>]*>([^<]+)</td>",
            re.IGNORECASE | re.DOTALL,
        )
        monthly_history = []
        parsed_rows = []
        for label, avg, gain_value, pct, peak in history_pattern.findall(html):
            label_clean = re.sub(r"<[^>]+>", " ", label)
            label_clean = re.sub(r"\s+", " ", label_clean).strip()
            parsed_rows.append((label_clean, avg, gain_value, pct, peak))

        for label_clean, avg, gain_value, pct, peak in parsed_rows:
            month_date = self._parse_month_label(label_clean)
            if not month_date:
                continue
            monthly_history.append(
                {
                    "date": month_date,
                    "avg_players": self._to_int(avg),
                    "peak_players": self._to_int(peak),
                    "gain": self._to_int(gain_value),
                    "percent_gain": self._to_float(pct),
                }
            )

        # The first parsed row is typically "Last 30 Days" and serves as the latest snapshot.
        if parsed_rows:
            _, avg, gain_value, pct, peak = parsed_rows[0]
            avg_players = self._to_int(avg)
            gain = self._to_int(gain_value)
            percent_gain = self._to_float(pct)
            peak_players = self._to_int(peak)
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
            "monthly_history": monthly_history,
        }
