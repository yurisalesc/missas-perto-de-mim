"""Admin CSV import/export application service."""

from __future__ import annotations

import csv
import re
from datetime import time
from io import StringIO

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.text_normalization import expand_nossa_senhora, normalize_city_name
from app.models.church import Church
from app.models.mass_schedule import MassSchedule

MAX_CSV_SIZE_BYTES = 2 * 1024 * 1024
REQUIRED_COLUMNS = {"nome", "endereco", "cidade", "latitude", "longitude"}
WEEKDAY_COLUMNS = [("Seg", 0), ("Ter", 1), ("Qua", 2), ("Qui", 3), ("Sex", 4), ("Sab", 5), ("Dom", 6)]
REQUIRED_POPULATE_COLUMNS = {"Nome da Instituição", "Endereço", "Cidade"}


class AdminCsvService:
    """Handles CSV parsing and persistence for admin import/export endpoints."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _read_optional(row: dict, *keys: str) -> str | None:
        for key in keys:
            value = row.get(key)
            if value is None:
                continue
            text_value = str(value).strip()
            if text_value and text_value != "-":
                return text_value
        return None

    @staticmethod
    def _parse_day_times(raw: str | None) -> list[time]:
        value = (raw or "").strip()
        if not value or value == "-":
            return []
        parsed: list[time] = []
        for hours_text, minutes_text in re.findall(r"(\d{1,2}):(\d{2})", value):
            hours = int(hours_text)
            minutes = int(minutes_text)
            if 0 <= hours <= 23 and 0 <= minutes <= 59:
                parsed.append(time(hours, minutes))
        return parsed

    @staticmethod
    def _parse_coordinate(raw: str | None, *, is_latitude: bool) -> float | None:
        value = (raw or "").strip().replace(",", ".")
        if not value:
            return None
        try:
            number = float(value)
        except ValueError:
            return None
        if is_latitude:
            while abs(number) > 9:
                number /= 10.0
            return number if -90 <= number <= 90 else None
        while abs(number) > 90:
            number /= 10.0
        return number if -180 <= number <= 180 else None

    @staticmethod
    def _sort_time_strings(values: list[str]) -> list[str]:
        return sorted(set(values), key=lambda value: int(value.split(":")[0]) * 60 + int(value.split(":")[1]))

    @staticmethod
    def _decode_rows(content: bytes) -> tuple[list[dict], set[str]]:
        if len(content) > MAX_CSV_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="CSV file is too large")
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded") from exc

        reader = csv.DictReader(StringIO(text))
        if not reader.fieldnames:
            raise HTTPException(status_code=400, detail="CSV header is required")
        columns = {value.strip() for value in reader.fieldnames if value}
        return list(reader), columns

    def import_compact_csv(self, content: bytes) -> dict:
        rows, columns = self._decode_rows(content)
        missing = sorted(REQUIRED_COLUMNS - columns)
        if missing:
            raise HTTPException(status_code=400, detail=f"Missing CSV columns: {', '.join(missing)}")

        created_churches = 0
        created_schedules = 0
        try:
            for row in rows:
                try:
                    church = Church(
                        nome=expand_nossa_senhora(str(row["nome"]).strip()),
                        endereco=str(row["endereco"]).strip(),
                        cidade=normalize_city_name(str(row["cidade"]).strip()),
                        estado=self._read_optional(row, "estado", "Estado"),
                        latitude=float(row["latitude"]),
                        longitude=float(row["longitude"]),
                        telefone=self._read_optional(row, "telefone", "Telefone"),
                        redes_sociais_site=self._read_optional(
                            row, "redes_sociais_site", "redes sociais/site", "Redes Sociais/Site"
                        ),
                        observacao=self._read_optional(row, "observacao", "Observação", "flags", "Flags"),
                    )
                except (TypeError, ValueError) as exc:
                    raise HTTPException(status_code=400, detail="Invalid church row in CSV") from exc

                self.db.add(church)
                self.db.flush()
                created_churches += 1

                schedules_raw = (row.get("horarios") or "").strip()
                for token in schedules_raw.split("|"):
                    value = token.strip()
                    if not value:
                        continue
                    try:
                        hours, minutes = value.split(":")
                        schedule = MassSchedule(
                            church_id=church.id,
                            dia_semana=int(row.get("dia_semana", 6)),
                            horario=time(int(hours), int(minutes)),
                            observacao=(row.get("observacao") or None),
                        )
                    except (TypeError, ValueError) as exc:
                        raise HTTPException(status_code=400, detail="Invalid schedule row in CSV") from exc
                    self.db.add(schedule)
                    created_schedules += 1
            self.db.commit()
        except HTTPException:
            self.db.rollback()
            raise
        return {"created_churches": created_churches, "created_schedules": created_schedules}

    def populate_database_from_wide_csv(self, content: bytes, replace_existing: bool = True) -> dict:
        rows, columns = self._decode_rows(content)
        missing = sorted(REQUIRED_POPULATE_COLUMNS - columns)
        if missing:
            raise HTTPException(status_code=400, detail=f"Missing CSV columns: {', '.join(missing)}")

        created_churches = 0
        created_schedules = 0
        try:
            if replace_existing:
                self.db.query(MassSchedule).delete()
                self.db.query(Church).delete()
                self.db.flush()

            for row in rows:
                name = expand_nossa_senhora(str(row.get("Nome da Instituição", "")).strip())
                address = str(row.get("Endereço", "")).strip()
                city = normalize_city_name(str(row.get("Cidade", "")).strip())
                if not name or not address or not city:
                    continue
                latitude = self._parse_coordinate(row.get("latitude"), is_latitude=True)
                longitude = self._parse_coordinate(row.get("longitude"), is_latitude=False)
                if latitude is None or longitude is None:
                    continue

                church = Church(
                    nome=name,
                    endereco=address,
                    cidade=city,
                    estado=self._read_optional(row, "Estado", "estado") or "RN",
                    latitude=latitude,
                    longitude=longitude,
                    telefone=self._read_optional(row, "Telefone", "telefone"),
                    redes_sociais_site=self._read_optional(row, "Redes Sociais/Site", "redes_sociais_site"),
                    observacao=self._read_optional(row, "Flags", "flags", "observacao", "Observação"),
                )
                self.db.add(church)
                self.db.flush()
                created_churches += 1

                for column_name, weekday in WEEKDAY_COLUMNS:
                    for schedule_time in self._parse_day_times(row.get(column_name)):
                        self.db.add(
                            MassSchedule(
                                church_id=church.id,
                                dia_semana=weekday,
                                horario=schedule_time,
                                observacao=self._read_optional(row, "Flags", "flags"),
                            )
                        )
                        created_schedules += 1
            self.db.commit()
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Failed to populate database: {exc}") from exc

        return {
            "created_churches": created_churches,
            "created_schedules": created_schedules,
            "replace_existing": replace_existing,
        }

    def export_database_csv_response(self) -> StreamingResponse:
        churches = self.db.execute(select(Church).options(joinedload(Church.horarios))).unique().scalars().all()

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "Nome da Instituição",
                "Categoria",
                "Endereço",
                "Telefone",
                "Redes Sociais/Site",
                "Cidade",
                "Estado",
                "Seg",
                "Ter",
                "Qua",
                "Qui",
                "Sex",
                "Sab",
                "Dom",
                "Flags",
                "latitude",
                "longitude",
            ]
        )

        for church in churches:
            by_day: dict[int, list[str]] = {i: [] for i in range(7)}
            schedule_notes: list[str] = []
            for schedule in church.horarios:
                by_day[schedule.dia_semana].append(schedule.horario.strftime("%H:%M"))
                if schedule.observacao:
                    schedule_notes.append(schedule.observacao.strip())

            writer.writerow(
                [
                    church.nome,
                    "",
                    church.endereco,
                    church.telefone or "",
                    church.redes_sociais_site or "",
                    church.cidade,
                    church.estado or "RN",
                    ", ".join(self._sort_time_strings(by_day[0])),
                    ", ".join(self._sort_time_strings(by_day[1])),
                    ", ".join(self._sort_time_strings(by_day[2])),
                    ", ".join(self._sort_time_strings(by_day[3])),
                    ", ".join(self._sort_time_strings(by_day[4])),
                    ", ".join(self._sort_time_strings(by_day[5])),
                    ", ".join(self._sort_time_strings(by_day[6])),
                    church.observacao or (schedule_notes[0] if schedule_notes else ""),
                    f"{church.latitude:.6f}",
                    f"{church.longitude:.6f}",
                ]
            )

        output.seek(0)
        headers = {"Content-Disposition": "attachment; filename=missas_export.csv"}
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv; charset=utf-8", headers=headers)
