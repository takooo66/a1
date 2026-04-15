"""ディスクキャッシュ: Yahoo Transit のスクレイピング結果を保存して再利用する"""
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")
CACHE_DIR = Path.home() / ".cache" / "train-commute-finder"


class TimetableCache:
    """
    経路検索結果をJSONファイルとしてディスクにキャッシュする。
    同じ検索を短時間に繰り返しても、Yahoo Transit へのHTTPリクエストを送らない。
    """

    def __init__(self, ttl_hours: int = 6):
        self.ttl = timedelta(hours=ttl_hours)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, key: str) -> Path:
        digest = hashlib.md5(key.encode()).hexdigest()
        return CACHE_DIR / f"{digest}.json"

    def get(self, key: str) -> list[dict] | None:
        """キャッシュから経路データを取得する。期限切れ or 未存在なら None を返す"""
        path = self._cache_path(key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            fetched_at = datetime.fromisoformat(data["fetched_at"])
            if datetime.now(tz=JST) - fetched_at > self.ttl:
                return None  # 期限切れ
            return data["routes"]
        except (KeyError, ValueError, json.JSONDecodeError):
            return None

    def set(self, key: str, routes: list[dict]) -> None:
        """経路データをキャッシュに保存する"""
        path = self._cache_path(key)
        payload = {
            "fetched_at": datetime.now(tz=JST).isoformat(),
            "routes": routes,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def make_key(self, origin: str, destination: str, arrive_by: datetime) -> str:
        """キャッシュキーを生成する (出発地・目的地・到着期限の時間単位で一意)"""
        dt_str = arrive_by.strftime("%Y%m%d%H%M")
        return f"{origin}_{destination}_{dt_str}"
