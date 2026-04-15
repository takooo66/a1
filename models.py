"""データモデル: 電車の経路・推奨結果を表すデータクラス"""
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Optional


@dataclass
class TrainLeg:
    """1本の電車の乗車区間"""
    line_name: str           # 路線名 (例: "埼玉高速鉄道")
    departure_station: str   # 出発駅
    arrival_station: str     # 到着駅
    departure_time: datetime # 出発時刻
    arrival_time: datetime   # 到着時刻
    train_type: str = ""     # 種別 (例: "各停", "急行")
    direction: str = ""      # 行き先 (例: "浦和美園行き")


@dataclass
class Route:
    """乗り継ぎを含む完全な経路"""
    legs: list[TrainLeg]
    departure_time: datetime     # 最初の出発時刻 (戸塚安行発)
    arrival_time: datetime       # 最終到着時刻 (鶴ヶ島着)
    total_duration_minutes: int  # 総所要時間 (分)
    transfer_count: int = 0      # 乗り換え回数


@dataclass
class ClassPeriod:
    """大学の時限"""
    period_number: int   # 1〜5
    start_time: time     # 授業開始時刻


@dataclass
class Recommendation:
    """推奨電車の情報"""
    target_period: ClassPeriod   # 対象の時限
    recommended_route: Route     # 推奨経路
    arrival_deadline: datetime   # 鶴ヶ島着の最終期限
    buffer_minutes: int          # 駅到着から授業開始までの余裕 (分)
    walking_minutes: int         # 鶴ヶ島駅→キャンパス 徒歩時間 (分)
