"""Integration tests for search filters."""

from datetime import datetime

from app.services.mass_time_service import MassTimeService


def test_radius_filter_returns_nearby_only(client):
    """Ensure radius filter excludes churches outside range."""

    response = client.get("/igrejas/buscar?lat=-5.7945&lon=-35.2110&radius_km=5&next_hours=168")
    assert response.status_code == 200
    payload = response.json()
    names = [item["nome"] for item in payload]
    assert "Igreja Centro" in names
    assert "Igreja Distante" not in names


def test_city_filter_returns_matching_city(client):
    """Ensure city filter narrows church results."""

    response = client.get("/igrejas/buscar?city=Natal&radius_km=50&next_hours=168")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) >= 1


def test_happening_now_returns_current_mass(client):
    """Ensure happening-now endpoint returns masses in progress."""

    response = client.get("/igrejas/acontecendo-agora?city=Natal")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) >= 1


def test_time_window_filter_respects_next_hours():
    """Ensure next_hours logic includes only valid upcoming masses."""

    now = datetime(2026, 3, 23, 18, 0, 0)
    class Schedule:
        """Simple schedule object for service test."""

        def __init__(self, dia_semana, horario):
            self.dia_semana = dia_semana
            self.horario = horario

    schedules = [Schedule(0, datetime(2026, 3, 23, 19, 0).time()), Schedule(1, datetime(2026, 3, 24, 8, 0).time())]
    matches = MassTimeService.filter_in_window(now, schedules, next_hours=2)
    assert len(matches) == 1


def test_time_window_crosses_midnight_without_overshooting():
    """Ensure window across midnight does not include morning masses beyond range."""

    now = datetime(2026, 3, 27, 23, 47, 0)  # Friday

    class Schedule:
        """Simple schedule object for service test."""

        def __init__(self, dia_semana, horario):
            self.dia_semana = dia_semana
            self.horario = horario

    schedules = [
        Schedule(4, datetime(2026, 3, 27, 23, 50).time()),  # inside 5h window
        Schedule(5, datetime(2026, 3, 28, 6, 30).time()),   # outside 5h window
    ]
    matches = MassTimeService.filter_in_window(now, schedules, next_hours=5)
    assert len(matches) == 1
    assert matches[0][0].horario.strftime("%H:%M") == "23:50"
