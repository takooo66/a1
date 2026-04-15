"""Yahoo Japan 路線情報スクレイパー

transit.yahoo.co.jp から「この時刻までに到着」検索を行い、
経路リスト (list[Route]) を返す。
"""
import time as time_module
import urllib.parse
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from cache import TimetableCache
from models import Route, TrainLeg

JST = ZoneInfo("Asia/Tokyo")

YAHOO_TRANSIT_URL = "https://transit.yahoo.co.jp/search/result"


class YahooTransitFetcher:
    """
    Yahoo Japan 路線情報の「着時刻指定」検索を使って経路を取得する。

    URL パラメータ:
        from   : 出発駅名
        to     : 到着駅名
        y/m/d  : 年/月/日
        hh     : 時 (到着希望)
        m1/m2  : 分の十の位 / 一の位
        type=4 : 着時刻指定モード
    """

    def __init__(self, config, cache: TimetableCache):
        self.config = config
        self.cache = cache
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": config["scraper"]["user_agent"],
            "Accept-Language": "ja,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

    def fetch_routes(self, origin: str, destination: str, arrive_by: datetime) -> list[Route]:
        """
        arrive_by までに destination へ到着できる経路を返す。
        キャッシュがあれば HTTP リクエストを省略する。
        """
        cache_key = self.cache.make_key(origin, destination, arrive_by)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return [self._dict_to_route(r) for r in cached]

        html = self._request(origin, destination, arrive_by)
        routes = self._parse(html, arrive_by)
        self.cache.set(cache_key, [self._route_to_dict(r) for r in routes])
        return routes

    # ------------------------------------------------------------------
    # HTTP リクエスト
    # ------------------------------------------------------------------

    def _request(self, origin: str, destination: str, arrive_by: datetime) -> str:
        params = {
            "from": origin,
            "to": destination,
            "y": arrive_by.strftime("%Y"),
            "m": arrive_by.strftime("%m"),
            "d": arrive_by.strftime("%d"),
            "hh": arrive_by.strftime("%H"),
            "m1": arrive_by.strftime("%M")[0],
            "m2": arrive_by.strftime("%M")[1],
            "type": "4",   # 着時刻指定
            "ws": "2",     # 徒歩速度: 普通
            "s": "0",
            "expkind": "1",
            "al": "1",
            "shin": "1",
            "ex": "1",
            "hb": "1",
            "lb": "1",
            "sr": "1",
        }
        delay = self.config["scraper"].get("request_delay_seconds", 2.0)
        time_module.sleep(delay)

        resp = self.session.get(YAHOO_TRANSIT_URL, params=params, timeout=15)
        resp.raise_for_status()
        return resp.text

    # ------------------------------------------------------------------
    # HTML パース
    # ------------------------------------------------------------------

    def _parse(self, html: str, arrive_by: datetime) -> list[Route]:
        soup = BeautifulSoup(html, "lxml")
        max_routes = self.config["scraper"].get("max_routes", 3)
        routes: list[Route] = []

        # 各経路カード (.routeList > li)
        route_items = soup.select("section.routeList > ul > li") or soup.select("ul.routeList > li")
        if not route_items:
            # 代替セレクタ
            route_items = soup.select("li.routeListItem")

        for item in route_items[:max_routes]:
            route = self._parse_route_item(item, arrive_by)
            if route:
                routes.append(route)

        return routes

    def _parse_route_item(self, item, arrive_by: datetime) -> Route | None:
        """経路カード1件をパースして Route オブジェクトを返す"""
        try:
            # 出発・到着時刻
            dep_el = item.select_one(".time .dep") or item.select_one("[class*=dep]")
            arr_el = item.select_one(".time .arr") or item.select_one("[class*=arr]")

            if not dep_el or not arr_el:
                # 時刻テキストを直接探す
                time_els = item.select(".timeBox li") or item.select(".time li")
                if len(time_els) >= 2:
                    dep_text = time_els[0].get_text(strip=True)
                    arr_text = time_els[-1].get_text(strip=True)
                else:
                    return None
            else:
                dep_text = dep_el.get_text(strip=True)
                arr_text = arr_el.get_text(strip=True)

            dep_time = self._parse_time(dep_text, arrive_by)
            arr_time = self._parse_time(arr_text, arrive_by)
            if not dep_time or not arr_time:
                return None

            # 乗り換え回数
            transfer_el = item.select_one(".transfer") or item.select_one("[class*=transfer]")
            transfer_count = 0
            if transfer_el:
                t_text = transfer_el.get_text(strip=True)
                digits = "".join(c for c in t_text if c.isdigit())
                transfer_count = int(digits) if digits else 0

            # 各区間の路線情報
            legs = self._parse_legs(item, dep_time, arr_time)

            duration = int((arr_time - dep_time).total_seconds() / 60)
            return Route(
                legs=legs,
                departure_time=dep_time,
                arrival_time=arr_time,
                total_duration_minutes=duration,
                transfer_count=transfer_count,
            )
        except Exception:
            return None

    def _parse_legs(self, item, route_dep: datetime, route_arr: datetime) -> list[TrainLeg]:
        """経路内の各乗車区間をパースする"""
        legs: list[TrainLeg] = []

        # 路線名を取得 (.transport li, .trainType など)
        transport_els = item.select("ul.transport > li") or item.select(".lineColor")
        line_names = [el.get_text(strip=True) for el in transport_els if el.get_text(strip=True)]

        if not line_names:
            # フォールバック: 出発〜到着の1区間として扱う
            legs.append(TrainLeg(
                line_name="(経路詳細は Yahoo 路線で確認)",
                departure_station=self.config["origin_station"],
                arrival_station=self.config["destination_station"],
                departure_time=route_dep,
                arrival_time=route_arr,
            ))
            return legs

        # 複数区間がある場合は均等に時間を割り当てる (詳細時刻は取れない場合が多い)
        n = len(line_names)
        total_sec = (route_arr - route_dep).total_seconds()
        seg_sec = total_sec / n

        # 駅名リスト (取れる場合のみ)
        station_els = item.select(".stationName") or item.select("[class*=station]")
        station_names = [el.get_text(strip=True) for el in station_els]

        for i, line_name in enumerate(line_names):
            seg_dep = route_dep + __import__("datetime").timedelta(seconds=seg_sec * i)
            seg_arr = route_dep + __import__("datetime").timedelta(seconds=seg_sec * (i + 1))
            dep_st = station_names[i] if i < len(station_names) else ("戸塚安行" if i == 0 else "")
            arr_st = station_names[i + 1] if (i + 1) < len(station_names) else ("鶴ヶ島" if i == n - 1 else "")
            legs.append(TrainLeg(
                line_name=line_name,
                departure_station=dep_st,
                arrival_station=arr_st,
                departure_time=seg_dep,
                arrival_time=seg_arr,
            ))

        return legs

    # ------------------------------------------------------------------
    # ユーティリティ
    # ------------------------------------------------------------------

    def _parse_time(self, text: str, reference: datetime) -> datetime | None:
        """'09:52' のような文字列を datetime に変換する"""
        text = text.strip().replace("発", "").replace("着", "")
        for fmt in ("%H:%M", "%H時%M分"):
            try:
                t = datetime.strptime(text, fmt).time()
                return datetime.combine(reference.date(), t, tzinfo=JST)
            except ValueError:
                continue
        return None

    # ------------------------------------------------------------------
    # シリアライズ / デシリアライズ (キャッシュ用)
    # ------------------------------------------------------------------

    def _route_to_dict(self, route: Route) -> dict:
        return {
            "departure_time": route.departure_time.isoformat(),
            "arrival_time": route.arrival_time.isoformat(),
            "total_duration_minutes": route.total_duration_minutes,
            "transfer_count": route.transfer_count,
            "legs": [
                {
                    "line_name": leg.line_name,
                    "departure_station": leg.departure_station,
                    "arrival_station": leg.arrival_station,
                    "departure_time": leg.departure_time.isoformat(),
                    "arrival_time": leg.arrival_time.isoformat(),
                    "train_type": leg.train_type,
                    "direction": leg.direction,
                }
                for leg in route.legs
            ],
        }

    def _dict_to_route(self, d: dict) -> Route:
        legs = [
            TrainLeg(
                line_name=leg["line_name"],
                departure_station=leg["departure_station"],
                arrival_station=leg["arrival_station"],
                departure_time=datetime.fromisoformat(leg["departure_time"]),
                arrival_time=datetime.fromisoformat(leg["arrival_time"]),
                train_type=leg.get("train_type", ""),
                direction=leg.get("direction", ""),
            )
            for leg in d["legs"]
        ]
        return Route(
            legs=legs,
            departure_time=datetime.fromisoformat(d["departure_time"]),
            arrival_time=datetime.fromisoformat(d["arrival_time"]),
            total_duration_minutes=d["total_duration_minutes"],
            transfer_count=d.get("transfer_count", 0),
        )
