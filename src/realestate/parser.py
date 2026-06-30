"""פירוק טקסט מודעה (הדבקה ידנית) לשדות מובנים."""
from __future__ import annotations

import re

_RTL = re.compile(r"[\u200e\u200f]")


def _find(pattern: str, text: str, flags=0) -> float | None:
    m = re.search(pattern, text, flags)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def parse_listing(text: str) -> dict:
    """
    מחלץ מחיר, חדרים, שטח, קומה ושכר דירה מטקסט מודעה חופשי.
    מחזיר dict עם המפתחות: price, rooms, sqm, floor, rent, desc.
    שדות שלא זוהו יהיו None.
    """
    clean = _RTL.sub("", text)

    price = _find(r"(?:מחיר|price)[^\d]{0,12}([\d,]{6,})", clean, re.I)
    if price is None:
        m = re.search(r"([\d,]{6,})\s*(?:₪|ש\"?ח|שח)", clean)
        if m:
            price = float(m.group(1).replace(",", ""))
    if price is None:
        candidates = [
            float(x.replace(",", ""))
            for x in re.findall(r"([\d,]{6,})", clean)
        ]
        candidates = [c for c in candidates if 200_000 <= c <= 100_000_000]
        if candidates:
            price = max(candidates)

    rooms = _find(r"([\d]+(?:\.5)?)\s*(?:חדרים|חד'|חד׳|חדר)", clean)
    sqm = _find(r"([\d]+(?:\.\d+)?)\s*(?:מ\"ר|מ״ר|מטר|מ׳ר|sqm)", clean, re.I)
    if sqm is None:
        sqm = _find(r"(?:שטח|גודל)[^\d]{0,8}([\d]+)", clean)
    floor = _find(r"קומה\s*([\d]+)", clean)
    rent = _find(r"(?:שכ\"?ד|שכר דירה|שכירות)[^\d]{0,12}([\d,]{3,})", clean)

    first_line = next((ln.strip() for ln in clean.splitlines() if ln.strip()), "")

    return {
        "price": price, "rooms": rooms, "sqm": sqm,
        "floor": floor, "rent": rent, "desc": first_line[:60],
    }
