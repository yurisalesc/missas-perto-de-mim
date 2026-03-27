"""Mass schedule time filtering service."""

from datetime import datetime, timedelta

from app.models.mass_schedule import MassSchedule


class MassTimeService:
    """Service for selecting upcoming masses in a time window."""

    @staticmethod
    def next_occurrence(base_time: datetime, dia_semana: int, horario) -> datetime:
        """Compute next datetime occurrence for a weekly day/time."""

        days_ahead = (dia_semana - base_time.weekday()) % 7
        occurrence = datetime.combine((base_time + timedelta(days=days_ahead)).date(), horario)
        if occurrence < base_time:
            occurrence = occurrence + timedelta(days=7)
        return occurrence

    @classmethod
    def filter_in_window(
        cls, base_time: datetime, schedules: list[MassSchedule], next_hours: int
    ) -> list[tuple[MassSchedule, datetime]]:
        """Return schedules occurring within the next time window."""

        max_time = base_time + timedelta(hours=next_hours)
        matches: list[tuple[MassSchedule, datetime]] = []
        for schedule in schedules:
            occurrence = cls.next_occurrence(base_time, schedule.dia_semana, schedule.horario)
            if occurrence <= max_time:
                matches.append((schedule, occurrence))
        matches.sort(key=lambda item: item[1])
        return matches
