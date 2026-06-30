"""
מנוע נתוני שוק — עסקאות נדל"ן שנמכרו מאתר הנדל"ן הממשלתי (רשות המסים / כרמ"ן).
מקור: https://www.nadlan.gov.il  (נתונים פתוחים).

הערה חוקית: זהו מקור נתונים ממשלתי פתוח המיועד לעיון הציבור.
המודול אינו עוקף הגנות בוטים ואינו מבצע scraping של פלטפורמות מסחריות
(יד2/מדלן) — אלו אוסרות זאת בתנאי השימוש שלהן.
"""
from __future__ import annotations

import json
import statistics

BASE = "https://www.nadlan.gov.il/Nadlan.REST/Main"
_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Content-Type": "application/json;charset=UTF-8",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.nadlan.gov.il/",
}


def _num(v) -> float | None:
    try:
        return float(str(v).replace(",", "").replace("₪", "").strip())
    except (ValueError, AttributeError, TypeError):
        return None


def make_session():
    """יוצר session עם requests. מבודד כדי לאפשר mock בבדיקות."""
    import requests
    s = requests.Session()
    s.headers.update(_HEADERS)
    s.get("https://www.nadlan.gov.il/", timeout=30)  # cookies
    return s


def resolve_area(session, query: str) -> dict:
    r = session.get(f"{BASE}/GetDataByQuery", params={"query": query}, timeout=30)
    r.raise_for_status()
    data = r.json()
    nav = data.get("navigateobj") or data
    if not nav or not (nav.get("ObjectID") or nav.get("DescLayerID")):
        raise ValueError("לא נמצא אזור תואם. נסה ניסוח אחר (למשל 'רחוב, עיר').")
    return data


def fetch_deals(session, area_obj: dict, pages: int = 3) -> list[dict]:
    deals: list[dict] = []
    for page in range(1, pages + 1):
        body = dict(area_obj)
        body.update(PageNo=page, OrderByFilled="DEALDATETIME", OrderByDescending=True)
        r = session.post(f"{BASE}/GetAssestAndDeals", data=json.dumps(body), timeout=30)
        if r.status_code != 200:
            continue
        try:
            results = r.json().get("AllResults", [])
        except json.JSONDecodeError:
            break
        if not results:
            break
        deals.extend(results)
    return deals


def parse_deals(deals: list[dict]) -> list[dict]:
    rows = []
    for d in deals:
        price = _num(d.get("DEALAMOUNT"))
        area = _num(d.get("DEALNATURE"))
        rows.append({
            "address": d.get("FULLADRESS") or d.get("DISPLAYADRESS") or "",
            "date": (d.get("DEALDATE") or "")[:10],
            "price": price,
            "rooms": _num(d.get("ASSETROOMNUM")),
            "sqm": area,
            "price_per_sqm": round(price / area) if price and area else None,
            "type": d.get("DEALNATUREDESCRIPTION") or "",
            "floor": d.get("FLOORNO") or "",
            "year_built": d.get("BUILDINGYEAR") or "",
        })
    return rows


def summarize(rows: list[dict]) -> dict:
    ppm = [r["price_per_sqm"] for r in rows if r["price_per_sqm"]]
    prices = [r["price"] for r in rows if r["price"]]
    out: dict = {"deals": len(rows)}
    if ppm:
        out["avg_price_per_sqm"] = round(statistics.mean(ppm))
        out["median_price_per_sqm"] = round(statistics.median(ppm))
    if prices:
        out["avg_price"] = round(statistics.mean(prices))
        out["median_price"] = round(statistics.median(prices))
        out["min_price"] = round(min(prices))
        out["max_price"] = round(max(prices))
    return out


def get_market_data(query: str, pages: int = 3) -> tuple[list[dict], dict]:
    """נקודת כניסה: שם אזור -> (שורות עסקאות, סיכום)."""
    session = make_session()
    area = resolve_area(session, query)
    deals = fetch_deals(session, area, pages)
    rows = parse_deals(deals)
    return rows, summarize(rows)
