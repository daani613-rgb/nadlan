"""חישובי מס — מס רכישה ומס שבח."""
from __future__ import annotations

from .config import (
    PURCHASE_TAX_SINGLE,
    PURCHASE_TAX_ADDITIONAL,
    CAPITAL_GAINS_RATE,
    CAPITAL_GAINS_SURTAX,
    SINGLE_RESIDENCE_EXEMPTION_CEILING,
    RENTAL_EXEMPTION_CEILING,
    RENTAL_FLAT_RATE,
    RENTAL_MARGINAL_DEFAULT,
    DEPRECIATION_RATE,
)


def _bracket_tax(price: float, brackets) -> float:
    """מחשב מס פרוגרסיבי לפי טבלת מדרגות."""
    if price <= 0:
        return 0.0
    total = 0.0
    for low, high, rate in brackets:
        upper = price if high is None else min(price, high)
        if upper > low:
            total += (upper - low) * rate
        if high is not None and price <= high:
            break
    return total


def purchase_tax(price: float, buyer_type: str = "single") -> float:
    """
    מס רכישה לפי מחיר וסוג רוכש.
    buyer_type: 'single' | 'improve' | 'invest'
    דירה יחידה ומשפר דיור ממוסים לפי מדרגות דירה יחידה;
    דירה להשקעה לפי מדרגות דירה נוספת.
    """
    if buyer_type == "invest":
        return _bracket_tax(price, PURCHASE_TAX_ADDITIONAL)
    return _bracket_tax(price, PURCHASE_TAX_SINGLE)


def capital_gains_tax(nominal_gain: float, inflationary_amount: float = 0.0,
                      exempt: bool = False, rate: float = CAPITAL_GAINS_RATE,
                      high_income: bool = False,
                      sale_price: float | None = None) -> float:
    """
    מס שבח על השבח ה**ריאלי** ממכירה (לא הנומינלי).

    שבח ריאלי = שבח נומינלי − הסכום האינפלציוני (החלק האינפלציוני פטור
    לנכסים שנרכשו אחרי 1994). המס הוא 25% על השבח הריאלי.

    פרמטרים:
      nominal_gain       — שבח נומינלי (מכירה פחות עלות והוצאות מוכרות).
      inflationary_amount— הסכום האינפלציוני שיש לנכות (פטור).
      exempt             — פטור מלא (דירת מגורים יחידה זכאית).
      high_income        — אם True, מתווסף מס יסף של 5%.
      sale_price         — אם נמסר, פטור דירה יחידה מוגבל לתקרה
                           (5,008,000 ₪); מעליה החיוב יחסי.

    הערה: חישוב מפושט. אינו כולל לינארי מוטב (לנכסים מלפני 2014),
    פריסת מס, או ניכוי פחת שנדרש מהבסיס. לבדיקה מול יועץ מס לפני מכירה.
    """
    real_gain = max(0.0, nominal_gain - inflationary_amount)
    if real_gain <= 0:
        return 0.0

    # פטור דירה יחידה — מלא עד התקרה, יחסי מעליה
    taxable_fraction = 1.0
    if exempt:
        if sale_price is None or sale_price <= SINGLE_RESIDENCE_EXEMPTION_CEILING:
            return 0.0
        taxable_fraction = (sale_price - SINGLE_RESIDENCE_EXEMPTION_CEILING) / sale_price

    taxable = real_gain * taxable_fraction
    tax = taxable * rate
    if high_income:
        tax += taxable * CAPITAL_GAINS_SURTAX
    return tax


def rental_income_tax(monthly_rent: float, track: str = "auto",
                      marginal_rate: float = RENTAL_MARGINAL_DEFAULT,
                      annual_expenses: float = 0.0,
                      building_value: float = 0.0) -> dict:
    """
    מס שנתי על הכנסה משכירות לפי שלושת המסלולים.
    מחזיר dict: {'exempt','flat','marginal','chosen','tax'} — כל הסכומים שנתיים.

    מסלולים:
      - exempt   : פטור עד התקרה; פטור חלקי בין התקרה לכפליים; מעבר לכך חייב מלא
                   (החלק החייב ממוסה בשיעור השולי).
      - flat     : 10% על כל ההכנסה ברוטו, ללא תקרה.
      - marginal : שיעור שולי על ההכנסה בניכוי הוצאות ופחת (2% משווי המבנה).
    """
    annual = monthly_rent * 12
    ceiling = RENTAL_EXEMPTION_CEILING

    # מסלול פטור (כולל פטור חלקי)
    if monthly_rent <= ceiling:
        exempt_taxable = 0.0
    elif monthly_rent >= 2 * ceiling:
        exempt_taxable = annual
    else:
        adjusted_exemption = 2 * ceiling - monthly_rent     # פטור מתואם
        exempt_taxable = (monthly_rent - adjusted_exemption) * 12
    exempt_tax = exempt_taxable * marginal_rate

    # מסלול 10%
    flat_tax = annual * RENTAL_FLAT_RATE

    # מסלול שולי עם הוצאות ופחת
    depreciation = building_value * DEPRECIATION_RATE if building_value else 0.0
    marginal_taxable = max(0.0, annual - annual_expenses - depreciation)
    marginal_tax = marginal_taxable * marginal_rate

    options = {"exempt": exempt_tax, "flat": flat_tax, "marginal": marginal_tax}
    chosen = min(options, key=options.get) if track == "auto" else track
    return {**options, "chosen": chosen, "tax": options[chosen]}
