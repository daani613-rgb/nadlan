#!/usr/bin/env python3
"""
מעדכן את rate.json עם ריבית בנק ישראל העדכנית, ממאגר הסדרות הרשמי
(edge.boi.gov.il, SDMX). מריץ אותו ה-GitHub Action על לוח זמנים.

עיקרון בטיחות: אם המשיכה נכשלת או מחזירה ערך לא-סביר — הסקריפט
*לא* כותב דבר, ומשאיר את rate.json הקיים (הערך האחרון הידוע) על כנו.
כך הפאנל לעולם לא יציג מספר שגוי שמתחזה ל"חי".

CLAUDE CODE — לפני ההפעלה הראשונה יש לאמת את SERIES_URL מול ה-API החי:
ראה scripts/README_rate.md לנוהל האימות (לוודא שמוחזר ~4.00%).
"""
from __future__ import annotations
import csv
import io
import json
import sys
import urllib.request
from datetime import date
from pathlib import Path

# כתובת הסדרה של ריבית בנק ישראל ב-API הרשמי (SDMX, פורמט CSV, התצפית האחרונה).
# יש לאמת מול edge.boi.gov.il — ראה README_rate.md. ברירת מחדל לאימות:
SERIES_URL = (
    "https://edge.boi.gov.il/FusionEdgeServer/sdmx/v2/data/dataflow/"
    "BOI.STATISTICS/BR/1.0/MNT_RIB_BOI_D/?lastNObservations=1&format=csv"
)
PRIME_SPREAD = 1.5          # פריים = ריבית בנק ישראל + 1.5%
TIMEOUT = 30

HERE = Path(__file__).resolve().parent.parent
TARGETS = [HERE / "web" / "rate.json", HERE / "docs" / "rate.json"]


def fetch_boi_rate(url: str) -> tuple[float, str]:
    """מחזיר (ריבית, תאריך_ISO) מהתצפית האחרונה בתשובת ה-SDMX CSV."""
    req = urllib.request.Request(url, headers={"User-Agent": "nadlan-calc/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        text = resp.read().decode("utf-8-sig", errors="replace")
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        raise ValueError("תשובה ריקה מה-API")
    # שמות עמודות אפשריים בפורמט SDMX
    val_keys = ("OBS_VALUE", "value", "Value", "OBSVALUE")
    time_keys = ("TIME_PERIOD", "TIME", "time", "Time")
    last = rows[-1]
    val = next((last[k] for k in val_keys if k in last and last[k] != ""), None)
    when = next((last[k] for k in time_keys if k in last and last[k] != ""), "")
    if val is None:
        raise ValueError(f"לא נמצאה עמודת ערך. עמודות: {list(last.keys())}")
    return float(val), str(when)


def main() -> int:
    url = sys.argv[1] if len(sys.argv) > 1 else SERIES_URL
    try:
        boi, when = fetch_boi_rate(url)
    except Exception as e:  # noqa: BLE001
        print(f"לא עודכן (נשמר הערך הקיים) · Not updated, kept existing: {e}",
              file=sys.stderr)
        return 1
    # בדיקת שפיות — ריבית סבירה בלבד
    if not (0.0 <= boi <= 30.0):
        print(f"ערך לא סביר ({boi}), לא נכתב · implausible value, skipped",
              file=sys.stderr)
        return 1
    data = {
        "boi_rate": round(boi, 2),
        "prime": round(boi + PRIME_SPREAD, 2),
        "date": when or date.today().isoformat(),
        "source": "Bank of Israel (edge.boi.gov.il)",
        "fetched": date.today().isoformat(),
    }
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    for t in TARGETS:
        if t.parent.exists():
            t.write_text(payload, encoding="utf-8")
            print(f"נכתב · wrote {t}: {data['boi_rate']}% (prime {data['prime']}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
