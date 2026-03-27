"""Seed initial church and Sunday mass data for Natal."""

from datetime import time

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.church import Church
from app.models.mass_schedule import MassSchedule


def parse_hour(token: str) -> time:
    """Convert compact Portuguese hour strings into time."""

    normalized = token.lower().replace("h", ":")
    if normalized.endswith(":"):
        normalized = normalized[:-1]
    parts = normalized.split(":")
    if len(parts) == 1:
        return time(int(parts[0]), 0)
    return time(int(parts[0]), int(parts[1]))


def run_seed() -> None:
    """Populate database with initial churches and Sunday schedules."""

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        dataset = [
            ("Catedral Metropolitana", "Av. Deodoro da Fonseca, s/n", "Natal", -5.7877, -35.2023, ["07h", "09h", "11h", "19h"]),
            ("São Pedro", "Praça São Pedro, Alecrim", "Natal", -5.7951, -35.2218, ["06h30", "08h", "17h", "19h"]),
            ("Sta Teresinha", "Av. Hermes da Fonseca, Tirol", "Natal", -5.7985, -35.2015, ["09h", "11h", "18h", "19h30"]),
            ("Santuário dos Mártires", "R. Luíza Bezerra, Nazaré", "Natal", -5.8192, -35.2324, ["07h", "09h", "11h", "18h"]),
            ("Imaculada Conceição", "R. Adolfo Gordo, Cidade Alta", "Natal", -5.7834, -35.2109, ["07h", "09h", "11h30", "18h"]),
            ("Sagrada Família", "R. Praia de Genipabu, Rocas", "Natal", -5.7761, -35.1972, ["07h", "09h", "17h", "19h30"]),
            ("N. Sra da Apresentação", "Praça André de Albuquerque", "Natal", -5.7852, -35.2115, ["06h30", "08h", "10h", "18h"]),
            ("São João Batista", "R. Miramar, Lagoa Seca", "Natal", -5.8083, -35.2125, ["07h", "09h", "11h", "18h"]),
            ("Sto Afonso Maria de Ligório", "R. Mirassol, Neópolis", "Natal", -5.8611, -35.2101, ["07h", "09h", "11h", "18h", "19h30"]),
            ("N. Sra da Esperança", "Av. Jerônimo Câmara, Cidade da Esperança", "Natal", -5.8245, -35.2390, ["07h", "09h", "11h", "19h"]),
        ]
        for nome, endereco, cidade, latitude, longitude, horarios in dataset:
            church = Church(
                nome=nome,
                endereco=endereco,
                cidade=cidade,
                latitude=latitude,
                longitude=longitude,
            )
            db.add(church)
            db.flush()
            parsed = [parse_hour(slot) for slot in horarios]
            for dia in range(7):
                for horario in parsed:
                    db.add(
                        MassSchedule(
                            church_id=church.id,
                            dia_semana=dia,
                            horario=horario,
                        )
                    )
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
