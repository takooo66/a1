"""メール通知: Gmail SMTP で推奨電車の情報を送信する"""
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.utils import formatdate
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from models import Recommendation

load_dotenv()
JST = ZoneInfo("Asia/Tokyo")


class EmailNotifier:
    """Gmail SMTP を使って電車情報をメールで通知する"""

    def __init__(self, config: dict):
        self.smtp_host = config["email"]["smtp_host"]
        self.smtp_port = config["email"]["smtp_port"]
        self.from_addr = os.environ.get("GMAIL_USER", config["email"].get("from_address", ""))
        self.to_addr = os.environ.get("GMAIL_TO", config["email"].get("to_address", ""))
        self.password = os.environ.get("GMAIL_APP_PASSWORD", "")

        if not self.from_addr:
            raise ValueError(".env に GMAIL_USER が設定されていません")
        if not self.to_addr:
            raise ValueError(".env に GMAIL_TO が設定されていません")
        if not self.password:
            raise ValueError(".env に GMAIL_APP_PASSWORD が設定されていません")

    def send(self, rec: Recommendation) -> None:
        """推奨電車情報をメールで送信する"""
        subject = self._build_subject(rec)
        body = self._build_body(rec)
        self._send_email(subject, body)
        print(f"メール送信完了: {self.to_addr}")

    def _build_subject(self, rec: Recommendation) -> str:
        route = rec.recommended_route
        dep_str = route.departure_time.strftime("%H:%M")
        return f"【電車】{rec.target_period.period_number}限 - {dep_str} {rec.recommended_route.legs[0].departure_station if rec.recommended_route.legs else '戸塚安行'}発"

    def _build_body(self, rec: Recommendation) -> str:
        route = rec.recommended_route
        period = rec.target_period
        walk = rec.walking_minutes
        campus_arrival = route.arrival_time + timedelta(minutes=walk)
        class_start_str = period.start_time.strftime("%H:%M")

        lines = [
            f"■ {period.period_number}限 ({class_start_str}開始) の推奨電車",
            "=" * 40,
            "",
        ]

        # 区間ごとの表示
        if route.legs:
            for i, leg in enumerate(route.legs):
                dep_str = leg.departure_time.strftime("%H:%M")
                arr_str = leg.arrival_time.strftime("%H:%M")
                lines.append(f"  出発: {dep_str}  {leg.departure_station}")
                if leg.train_type or leg.line_name:
                    detail = leg.line_name
                    if leg.train_type:
                        detail += f" ({leg.train_type})"
                    if leg.direction:
                        detail += f" {leg.direction}"
                    lines.append(f"  　↓ {detail}")
                lines.append(f"  到着: {arr_str}  {leg.arrival_station}")
                if i < len(route.legs) - 1:
                    lines.append("  　↓ [乗換]")
                lines.append("")
        else:
            dep_str = route.departure_time.strftime("%H:%M")
            arr_str = route.arrival_time.strftime("%H:%M")
            lines.append(f"  {dep_str} 戸塚安行発 → {arr_str} 鶴ヶ島着")
            lines.append("")

        lines += [
            "-" * 40,
            f"  鶴ヶ島着:    {route.arrival_time.strftime('%H:%M')}",
            f"  徒歩 {walk} 分  →  キャンパス着: {campus_arrival.strftime('%H:%M')}",
            f"  授業まで余裕: {rec.buffer_minutes} 分",
            "=" * 40,
            "",
            f"所要時間: {route.total_duration_minutes} 分  |  乗り換え: {route.transfer_count} 回",
        ]

        return "\n".join(lines)

    def _send_email(self, subject: str, body: str) -> None:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = self.from_addr
        msg["To"] = self.to_addr
        msg["Date"] = formatdate(localtime=True)

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(self.from_addr, self.password)
            smtp.sendmail(self.from_addr, [self.to_addr], msg.as_string())
