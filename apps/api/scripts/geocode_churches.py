"""Geocode churches using Nominatim and update SQLite coordinates."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Iterable

USER_AGENT = "missas-perto-de-mim-geocoder/1.3 (local dev script)"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
DB_FILE = Path(__file__).resolve().parent.parent / "missa_perto.db"


def expand_nossa_senhora(value: str) -> str:
    """Expand common abbreviation variants of Nossa Senhora."""

    return re.sub(r"\bN\.?\s*Sra\.?\b", "Nossa Senhora", value, flags=re.IGNORECASE)


def simplify(text: str) -> str:
    """Simplify noisy tokens to improve geocoding match quality."""

    value = expand_nossa_senhora((text or "").strip())
    value = value.replace("(Antiga)", "").replace("(Igreja do Galo)", "")
    value = value.replace("N. República", "Nova Republica")
    value = value.replace("Sto ", "Santo ").replace("Sta ", "Santa ")
    value = "".join(ch for ch in unicodedata.normalize("NFKD", value) if not unicodedata.combining(ch))
    value = re.sub(r"\s+", " ", value)
    return value.strip(" ,")


def geocode_query(query: str, timeout: int) -> tuple[float, float] | None:
    """Return first coordinate from Nominatim for a query."""

    params = urllib.parse.urlencode({"q": query, "format": "jsonv2", "limit": 1, "countrycodes": "br"})
    request = urllib.request.Request(f"{NOMINATIM_URL}?{params}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not payload:
        return None
    return float(payload[0]["lat"]), float(payload[0]["lon"])


def query_variants(nome: str, endereco: str, cidade: str) -> Iterable[str]:
    """Generate ordered geocoding query variants for one church."""

    name = simplify(nome)
    address = simplify(endereco)
    city = simplify(cidade)
    state_hint = "Rio Grande do Norte"
    country = "Brasil"
    yield f"{address}, {city}, {state_hint}, {country}"
    yield f"{name}, {city}, {state_hint}, {country}"
    yield f"{name}, {address}, {city}, {state_hint}, {country}"
    yield f"{address}, {city}, {country}"
    yield f"{name}, {city}, {country}"


def execute_with_retry(
    cur: sqlite3.Cursor,
    sql: str,
    params: tuple,
    retries: int = 20,
    wait_s: float = 0.4,
) -> None:
    """Retry writes when database is temporarily locked."""

    for attempt in range(retries):
        try:
            cur.execute(sql, params)
            return
        except sqlite3.OperationalError as exc:
            if "locked" not in str(exc).lower() or attempt == retries - 1:
                raise
            time.sleep(wait_s)


def main() -> None:
    parser = argparse.ArgumentParser(description="Geocode churches and update latitude/longitude.")
    parser.add_argument("--only-missing", action="store_true", help="Only geocode rows without coordinates.")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay in seconds between requests.")
    parser.add_argument("--timeout", type=int, default=8, help="Timeout per request in seconds.")
    args = parser.parse_args()

    conn = sqlite3.connect(str(DB_FILE), timeout=60)
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.cursor()

    query_sql = "SELECT id, nome, endereco, cidade, latitude, longitude FROM churches ORDER BY id"
    if args.only_missing:
        query_sql = (
            "SELECT id, nome, endereco, cidade, latitude, longitude "
            "FROM churches WHERE latitude = 0 OR longitude = 0 ORDER BY id"
        )
    churches = cur.execute(query_sql).fetchall()

    success = 0
    failed = 0
    changed = 0
    unchanged = 0

    for index, (church_id, nome, endereco, cidade, old_lat, old_lon) in enumerate(churches, start=1):
        coords = None
        for q in query_variants(nome, endereco, cidade):
            try:
                coords = geocode_query(q, timeout=args.timeout)
            except Exception:
                coords = None
            if coords:
                break
            time.sleep(max(0.2, args.delay / 2))

        normalized_name = expand_nossa_senhora(nome)
        if not coords:
            if normalized_name != nome:
                execute_with_retry(
                    cur,
                    "UPDATE churches SET nome = ? WHERE id = ?",
                    (normalized_name, church_id),
                )
            failed += 1
            print(f"[{index:03}/{len(churches)}] FAIL {normalized_name}")
            time.sleep(args.delay)
            continue

        lat, lon = coords
        execute_with_retry(
            cur,
            "UPDATE churches SET nome = ?, latitude = ?, longitude = ? WHERE id = ?",
            (normalized_name, lat, lon, church_id),
        )
        success += 1
        if abs(float(old_lat) - lat) < 1e-7 and abs(float(old_lon) - lon) < 1e-7:
            unchanged += 1
        else:
            changed += 1
        if index % 5 == 0:
            conn.commit()
        print(f"[{index:03}/{len(churches)}] OK   {normalized_name} -> ({lat:.5f}, {lon:.5f})")
        time.sleep(args.delay)

    conn.commit()
    conn.close()

    print("\nGeocoding finished")
    print(f"Success: {success}")
    print(f"Failed: {failed}")
    print(f"Updated coords: {changed}")
    print(f"Unchanged coords: {unchanged}")


if __name__ == "__main__":
    main()

