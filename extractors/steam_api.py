import time
from typing import Any, Dict, List, Optional

import requests

from config import api_config


class SteamApiExtractor:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Steam-BI-ETL/1.0"})

    def list_app_ids(self, max_items: int = 100) -> List[int]:
        # Primary source: complete Steam app catalog, then slice by max_items.
        all_apps_url = f"{api_config.steam_api_base_url}/ISteamApps/GetAppList/v2/"
        response = self.session.get(all_apps_url, timeout=api_config.timeout_seconds)
        if response.status_code == 200:
            apps = response.json().get("applist", {}).get("apps", [])
            ids = sorted({app.get("appid") for app in apps if app.get("appid")})
            if ids:
                return ids[:max_items]

        # Fallback source: SteamSpy catalog (public, up to ~1000 ids/page).
        steamspy_url = "https://steamspy.com/api.php?request=all"
        response = self.session.get(steamspy_url, timeout=api_config.timeout_seconds)
        if response.status_code == 200:
            payload = response.json()
            ids = sorted(
                {
                    int(app_id)
                    for app_id in payload.keys()
                    if str(app_id).isdigit()
                }
            )
            if ids:
                return ids[:max_items]

        # Secondary source: most played list (usually capped around 100).
        most_played_url = f"{api_config.steam_api_base_url}/ISteamChartsService/GetMostPlayedGames/v1/"
        response = self.session.get(most_played_url, timeout=api_config.timeout_seconds)
        if response.status_code == 200:
            ranks = response.json().get("response", {}).get("ranks", [])
            ids = [item.get("appid") for item in ranks if item.get("appid")]
            if ids:
                return ids[:max_items]

        fallback_ids = [
            730,
            570,
            440,
            578080,
            271590,
            252490,
            359550,
            1086940,
            1172470,
            230410,
            292030,
            1091500,
            381210,
            413150,
            1245620,
        ]
        return fallback_ids[:max_items]

    def fetch_app_details(self, app_id: int) -> Optional[Dict[str, Any]]:
        url = f"{api_config.steam_store_base_url}/api/appdetails"
        params = {"appids": app_id, "cc": "br", "l": "portuguese"}
        response = self.session.get(url, params=params, timeout=api_config.timeout_seconds)
        response.raise_for_status()
        payload = response.json().get(str(app_id), {})
        if not payload.get("success"):
            return None
        return payload.get("data")

    def fetch_current_players(self, app_id: int) -> Optional[int]:
        url = f"{api_config.steam_api_base_url}/ISteamUserStats/GetNumberOfCurrentPlayers/v1/"
        params = {"appid": app_id}
        response = self.session.get(url, params=params, timeout=api_config.timeout_seconds)
        response.raise_for_status()
        data = response.json().get("response", {})
        if data.get("result") != 1:
            return None
        return data.get("player_count")

    def throttle(self) -> None:
        time.sleep(api_config.request_delay_seconds)
