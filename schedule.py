"""大学の時間割と授業に間に合う到着期限の計算"""
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from models import ClassPeriod

JST = ZoneInfo("Asia/Tokyo")

# 時限ごとの授業開始時刻
CLASS_PERIODS: dict[int, ClassPeriod] = {
    1: ClassPeriod(1, time(9, 0)),
    2: ClassPeriod(2, time(10, 40)),
    3: ClassPeriod(3, time(13, 0)),
    4: ClassPeriod(4, time(14, 40)),
    5: ClassPeriod(5, time(16, 20)),
}


def get_period(period_number: int) -> ClassPeriod:
    """時限番号から ClassPeriod を取得する"""
    if period_number not in CLASS_PERIODS:
        raise ValueError(f"時限は1〜5の間で指定してください (入力: {period_number})")
    return CLASS_PERIODS[period_number]


def arrival_deadline(
    period_number: int,
    walk_minutes: int,
    buffer_minutes: int,
    on_date: "datetime.date",
) -> datetime:
    """
    鶴ヶ島駅に到着すべき最終時刻を返す。

    計算式:
        授業開始時刻 - 徒歩時間 - バッファ時間 = 駅到着期限
    """
    period = get_period(period_number)
    class_start = datetime.combine(on_date, period.start_time, tzinfo=JST)
    return class_start - timedelta(minutes=walk_minutes + buffer_minutes)
