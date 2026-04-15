"""
電車通学ファインダー - メインスクリプト

使い方:
    python main.py --period 2        # 2限を指定して実行
    python main.py                   # 対話形式で時限を入力
    python main.py --period 3 --no-email  # ターミナルに表示のみ (メール送信なし)
"""
import argparse
import sys
from datetime import date, datetime
from zoneinfo import ZoneInfo

import yaml

from cache import TimetableCache
from fetcher import YahooTransitFetcher
from models import Recommendation
from notifier import EmailNotifier
from recommender import NoSuitableTrainError, Recommender
from schedule import CLASS_PERIODS

JST = ZoneInfo("Asia/Tokyo")


def load_config(path: str = "config.yaml") -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def print_recommendation(rec: Recommendation) -> None:
    """推奨結果をターミナルに表示する"""
    from datetime import timedelta

    route = rec.recommended_route
    period = rec.target_period
    walk = rec.walking_minutes
    campus_arrival = route.arrival_time + timedelta(minutes=walk)

    print()
    print(f"{'=' * 44}")
    print(f"  {period.period_number}限 ({period.start_time.strftime('%H:%M')}開始) の推奨電車")
    print(f"{'=' * 44}")
    print()

    if route.legs:
        for i, leg in enumerate(route.legs):
            dep = leg.departure_time.strftime("%H:%M")
            arr = leg.arrival_time.strftime("%H:%M")
            print(f"  {dep}  {leg.departure_station} 発")
            detail = f"  　↓  {leg.line_name}"
            if leg.train_type:
                detail += f" ({leg.train_type})"
            if leg.direction:
                detail += f" {leg.direction}"
            print(detail)
            print(f"  {arr}  {leg.arrival_station} 着")
            if i < len(route.legs) - 1:
                print("        [乗換]")
        print()
    else:
        dep = route.departure_time.strftime("%H:%M")
        arr = route.arrival_time.strftime("%H:%M")
        print(f"  {dep} 戸塚安行発  →  {arr} 鶴ヶ島着")
        print()

    print(f"{'─' * 44}")
    print(f"  鶴ヶ島着:         {route.arrival_time.strftime('%H:%M')}")
    print(f"  徒歩 {walk} 分後:     キャンパス着 {campus_arrival.strftime('%H:%M')}")
    print(f"  授業まで余裕:     {rec.buffer_minutes} 分")
    print(f"{'─' * 44}")
    print(f"  所要時間 {route.total_duration_minutes} 分  |  乗り換え {route.transfer_count} 回")
    print()


def ask_period() -> int:
    """対話形式で時限を入力してもらう"""
    print("\n何限から授業がありますか?")
    print()
    for num, period in CLASS_PERIODS.items():
        print(f"  {num}  →  {num}限 ({period.start_time.strftime('%H:%M')}開始)")
    print()
    while True:
        try:
            val = int(input("時限番号を入力 (1〜5): ").strip())
            if val in CLASS_PERIODS:
                return val
            print("  1〜5 の数字を入力してください。")
        except (ValueError, KeyboardInterrupt):
            print("\n終了します。")
            sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="授業の時限から最適な電車を調べてメールで通知します"
    )
    parser.add_argument(
        "--period", "-p",
        type=int,
        choices=[1, 2, 3, 4, 5],
        metavar="N",
        help="授業の時限 (1〜5)。省略すると対話形式で入力できます。",
    )
    parser.add_argument(
        "--date", "-d",
        type=str,
        default=None,
        metavar="YYYY-MM-DD",
        help="対象日付 (省略すると今日)",
    )
    parser.add_argument(
        "--no-email",
        action="store_true",
        help="メール送信をスキップしてターミナルにのみ表示する",
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        default="config.yaml",
        help="設定ファイルのパス (デフォルト: config.yaml)",
    )
    args = parser.parse_args()

    # 設定読み込み
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"エラー: 設定ファイル '{args.config}' が見つかりません。", file=sys.stderr)
        sys.exit(1)

    # 日付の決定
    if args.date:
        try:
            target_date = date.fromisoformat(args.date)
        except ValueError:
            print("エラー: 日付は YYYY-MM-DD 形式で入力してください。", file=sys.stderr)
            sys.exit(1)
    else:
        target_date = datetime.now(tz=JST).date()

    # 時限の決定
    period_number = args.period if args.period else ask_period()

    # 経路検索
    cache = TimetableCache(ttl_hours=config["scraper"]["cache_ttl_hours"])
    fetcher = YahooTransitFetcher(config, cache)
    recommender = Recommender(fetcher, config)

    print(f"\n{target_date} の {period_number}限 に間に合う電車を検索中...")

    try:
        rec = recommender.recommend(period_number, target_date)
    except NoSuitableTrainError as e:
        print(f"\nエラー: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n検索中にエラーが発生しました: {e}", file=sys.stderr)
        sys.exit(1)

    # ターミナルに表示
    print_recommendation(rec)

    # メール送信
    if not args.no_email:
        try:
            notifier = EmailNotifier(config)
            notifier.send(rec)
        except ValueError as e:
            print(f"メール設定エラー: {e}", file=sys.stderr)
            print("ヒント: .env.example を参考に .env ファイルを作成してください。", file=sys.stderr)
        except Exception as e:
            print(f"メール送信エラー: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
