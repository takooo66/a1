"""推奨エンジン: 時限から最適な電車を選ぶ"""
from datetime import date, datetime
from zoneinfo import ZoneInfo

from fetcher import YahooTransitFetcher
from models import ClassPeriod, Recommendation, Route
from schedule import arrival_deadline, get_period

JST = ZoneInfo("Asia/Tokyo")


class NoSuitableTrainError(Exception):
    """指定した時限に間に合う電車が見つからない場合"""

    def __init__(self, period: ClassPeriod, deadline: datetime):
        super().__init__(
            f"{period.period_number}限 ({period.start_time.strftime('%H:%M')}開始) に間に合う電車が見つかりませんでした。"
            f" (鶴ヶ島着期限: {deadline.strftime('%H:%M')})"
        )
        self.period = period
        self.deadline = deadline


class Recommender:
    """
    授業の時限を受け取り、最も遅く出発できる電車を推奨する。
    「できるだけ長く寝られる」最適な電車を選ぶ。
    """

    def __init__(self, fetcher: YahooTransitFetcher, config: dict):
        self.fetcher = fetcher
        self.config = config

    def recommend(self, period_number: int, on_date: date) -> Recommendation:
        """
        period_number 限の授業に間に合う最適な電車を返す。

        選択基準: 期限内に到着できる中で、最も出発が遅い経路 (= 最も長く家にいられる)
        """
        walk = self.config["walking_minutes_to_campus"]
        buffer = self.config["pre_class_buffer_minutes"]
        period = get_period(period_number)
        deadline = arrival_deadline(period_number, walk, buffer, on_date)

        routes = self.fetcher.fetch_routes(
            origin=self.config["origin_station"],
            destination=self.config["destination_station"],
            arrive_by=deadline,
        )

        # 期限内に到着できる経路だけに絞る
        valid_routes = [r for r in routes if r.arrival_time <= deadline]

        if not valid_routes:
            raise NoSuitableTrainError(period, deadline)

        # 最も出発が遅い (= 最も自由時間が多い) 経路を選択
        best: Route = max(valid_routes, key=lambda r: r.departure_time)

        # 駅到着から授業開始までの余裕
        class_start = datetime.combine(on_date, period.start_time, tzinfo=JST)
        buffer_actual = int((class_start - best.arrival_time).total_seconds() / 60) - walk

        return Recommendation(
            target_period=period,
            recommended_route=best,
            arrival_deadline=deadline,
            buffer_minutes=buffer_actual,
            walking_minutes=walk,
        )
