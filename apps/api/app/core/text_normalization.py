"""Text normalization helpers for search and canonical naming."""

import re
import unicodedata


def expand_nossa_senhora(value: str) -> str:
    """Expand common abbreviation variants of Nossa Senhora."""

    return re.sub(r"\bN\.?\s*Sra\.?\b", "Nossa Senhora", value, flags=re.IGNORECASE)


def normalize_search_token(value: str) -> str:
    """Normalize text to improve fuzzy-like matching in simple filters."""

    normalized = expand_nossa_senhora((value or "").strip())
    normalized = normalized.replace(".", " ")
    normalized = "".join(
        ch for ch in unicodedata.normalize("NFKD", normalized) if not unicodedata.combining(ch)
    )
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.casefold()


def normalize_city_name(value: str) -> str:
    """Canonicalize known city abbreviations/nicknames."""

    raw = (value or "").strip()
    normalized = normalize_search_token(raw)
    if normalized in {"s g amarante", "s g do amarante", "sg amarante"}:
        return "São Gonçalo do Amarante"
    return raw

