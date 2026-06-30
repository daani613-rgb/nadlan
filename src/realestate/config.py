"""
קבועי רגולציה — ישראל 2026
מקורות: רשות המסים (מס רכישה), בנק ישראל (מגבלות מימון).
מדרגות מס הרכישה הוקפאו עד 15.1.2028 (חוק ההסדרים).
כל הסכומים בשקלים חדשים.
"""
from __future__ import annotations

# מדרגות מס רכישה — דירה יחידה (from, to, rate). to=None => אינסוף
PURCHASE_TAX_SINGLE: list[tuple[float, float | None, float]] = [
    (0, 1_978_745, 0.0),
    (1_978_745, 2_347_040, 0.035),
    (2_347_040, 6_055_070, 0.05),
    (6_055_070, 20_183_565, 0.08),
    (20_183_565, None, 0.10),
]

# מדרגות מס רכישה — דירה נוספת / השקעה
PURCHASE_TAX_ADDITIONAL: list[tuple[float, float | None, float]] = [
    (0, 6_055_070, 0.08),
    (6_055_070, None, 0.10),
]

# תקרות מימון (LTV) לפי סוג רוכש — בנק ישראל
LTV_CAPS: dict[str, float] = {
    "single": 0.75,    # דירה יחידה / ראשונה
    "improve": 0.70,   # משפר דיור (דירה חלופית)
    "invest": 0.50,    # דירה להשקעה / נוספת
}

CAPITAL_GAINS_RATE = 0.25   # מס שבח (השקעה) — על השבח הריאלי
CAPITAL_GAINS_SURTAX = 0.05  # מס יסף לבעלי הכנסות גבוהות (מעל ~721,560 ₪/שנה)
SINGLE_RESIDENCE_EXEMPTION_CEILING = 5_008_000  # תקרת פטור דירה יחידה (2026, קפוא עד 2028)
INFLATION_DEFAULT = 0.025   # אומדן אינפלציה שנתית (CPI) להתאמת שבח ריאלי
VARIABLE_RATE_CAP = 2 / 3   # בנק ישראל: חלק הריבית המשתנה לא יעלה על שני שליש
DTI_REGULATORY_CAP = 0.50   # תקרת יחס החזר רגולטורית (40% מצרפי מ-1.7.2026)
VAT = 0.18                  # מע"מ (מ-2025) — חל על שירותי תיווך ועו"ד

# ברירות מחדל להנחות
DEFAULTS = {
    "interest_rate": 0.048,     # ריבית שנתית משוערת (קל"צ אמצע 2026)
    "term_years": 25,
    "broker_pct": 0.02,
    "lawyer_pct": 0.005,
    "repayment_ratio": 0.33,    # יחס החזר מקסימלי להכנסה נדרשת
    "rent_growth": 0.03,
    "appreciation": 0.035,
}

BUYER_TYPES = ("single", "improve", "invest")
BUYER_TYPE_HE = {"single": "דירה יחידה", "improve": "משפר דיור", "invest": "דירה להשקעה"}

# --- מס על הכנסה משכירות (2026) ---
RENTAL_EXEMPTION_CEILING = 5654      # תקרת פטור חודשית (₪)
# הפטור מתבטל לחלוטין בהכנסה חודשית של פי 2 מהתקרה (11,308 ₪)
RENTAL_FLAT_RATE = 0.10             # מסלול מס מחזור 10% (ללא תקרה)
RENTAL_MARGINAL_DEFAULT = 0.31     # מדרגת מס שולי מינימלית להכנסה לא-מיגיעה
DEPRECIATION_RATE = 0.02           # שיעור פחת שנתי על מבנה (מסלול שולי)
RENTAL_TRACKS = ("auto", "exempt", "flat", "marginal")
RENTAL_TRACK_HE = {
    "exempt": "מסלול פטור", "flat": "מסלול 10%",
    "marginal": "מסלול מדרגות שולי", "auto": "הזול ביותר",
}

# --- ברירות מחדל להוצאות שוטפות ועלות הזדמנות ---
EXPENSE_DEFAULTS = {
    "maintenance_pct": 0.05,   # רזרבת תחזוקה כאחוז מהשכירות
    "mgmt_pct": 0.0,           # דמי ניהול נכס כאחוז מהשכירות
    "vacancy_pct": 0.083,      # אי-אכלוס (~חודש בשנה)
    "opportunity_return": 0.04,  # תשואה חלופית שנתית על ההון העצמי
}
