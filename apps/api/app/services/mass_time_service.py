"""Mass schedule time filtering service."""

from datetime import datetime, time, timedelta
from typing import Protocol, TypeVar


class HasWeeklyTime(Protocol):
    """Minimal weekly schedule contract used by time-window filters."""

    dia_semana: int
    horario: time


ScheduleT = TypeVar("ScheduleT", bound=HasWeeklyTime)


class MassTimeService:
    """Service for selecting upcoming masses in a time window."""

    @staticmethod
    def next_occurrence(base_time: datetime, dia_semana: int, horario: time) -> datetime:
        """Compute next datetime occurrence for a weekly day/time."""

        days_ahead = (dia_semana - base_time.weekday()) % 7
        occurrence = datetime.combine((base_time + timedelta(days=days_ahead)).date(), horario)
        if occurrence < base_time:
            occurrence = occurrence + timedelta(days=7)
        return occurrence

    @classmethod
    def filter_in_window(
        cls, base_time: datetime, schedules: list[ScheduleT], next_hours: int
    ) -> list[tuple[ScheduleT, datetime]]:
        """Return schedules occurring within the next time window."""

        max_time = base_time + timedelta(hours=next_hours)
        matches: list[tuple[ScheduleT, datetime]] = []
        for schedule in schedules:
            occurrence = cls.next_occurrence(base_time, schedule.dia_semana, schedule.horario)
            if occurrence <= max_time:
                matches.append((schedule, occurrence))
        matches.sort(key=lambda item: item[1])
        return matches

    @classmethod
    def filter_happening_now(
        cls, base_time: datetime, schedules: list[ScheduleT], duration_minutes: int = 90
    ) -> list[tuple[ScheduleT, datetime]]:
        """Return schedules that started and are still ongoing now."""

        ongoing: list[tuple[ScheduleT, datetime]] = []
        for schedule in schedules:
            days_ago = (base_time.weekday() - schedule.dia_semana) % 7
            start = datetime.combine((base_time - timedelta(days=days_ago)).date(), schedule.horario)
            end = start + timedelta(minutes=duration_minutes)
            if start <= base_time <= end:
                ongoing.append((schedule, start))
        ongoing.sort(key=lambda item: item[1])
        return ongoing
