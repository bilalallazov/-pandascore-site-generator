from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class DayRange:
    day_local: date
    start_utc: datetime
    end_utc: datetime

    def start_utc_iso(self) -> str:
        return self.start_utc.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")

    def end_utc_iso(self) -> str:
        return self.end_utc.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def _local_day_bounds(day_local: date, tz: ZoneInfo) -> tuple[datetime, datetime]:
    start_local = datetime.combine(day_local, time.min).replace(tzinfo=tz)
    end_local = datetime.combine(day_local + timedelta(days=1), time.min).replace(tzinfo=tz)
    return start_local, end_local


def day_range(day_local: date, tz_name: str) -> DayRange:
    tz = ZoneInfo(tz_name)
    start_local, end_local = _local_day_bounds(day_local, tz)
    return DayRange(
        day_local=day_local,
        start_utc=start_local.astimezone(timezone.utc),
        end_utc=end_local.astimezone(timezone.utc),
    )


def yesterday_today_tomorrow(tz_name: str, now_utc: datetime | None = None) -> dict[str, DayRange]:
    tz = ZoneInfo(tz_name)
    now_utc = now_utc or datetime.now(timezone.utc)
    now_local = now_utc.astimezone(tz)
    today_local = now_local.date()

    return {
        "yesterday": day_range(today_local - timedelta(days=1), tz_name),
        "today": day_range(today_local, tz_name),
        "tomorrow": day_range(today_local + timedelta(days=1), tz_name),
    }

