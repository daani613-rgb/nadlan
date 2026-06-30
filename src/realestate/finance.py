"""חישובי מימון: משכנתא, ניתוח עסקה, לוח סילוקין ותחזית מכירה."""
from __future__ import annotations

from dataclasses import dataclass, field

from .config import LTV_CAPS, VAT, DEFAULTS, EXPENSE_DEFAULTS, INFLATION_DEFAULT, VARIABLE_RATE_CAP
from .tax import purchase_tax, capital_gains_tax, rental_income_tax


def pmt(annual_rate: float, n_months: int, principal: float) -> float:
    """החזר חודשי קבוע (כמו PMT באקסל)."""
    if principal <= 0 or n_months <= 0:
        return 0.0
    i = annual_rate / 12
    if i == 0:
        return principal / n_months
    return principal * i / (1 - (1 + i) ** -n_months)


def remaining_balance(principal: float, annual_rate: float,
                      term_years: int, years_paid: float) -> float:
    """יתרת קרן לאחר years_paid שנים."""
    if years_paid >= term_years:
        return 0.0
    i = annual_rate / 12
    m = min(years_paid * 12, term_years * 12)
    p = pmt(annual_rate, term_years * 12, principal)
    if i == 0:
        return max(0.0, principal - p * m)
    return max(0.0, principal * (1 + i) ** m - p * ((1 + i) ** m - 1) / i)


@dataclass
class DealInputs:
    price: float
    buyer_type: str = "single"
    ltv_wanted: float = 0.75
    term_years: int = field(default_factory=lambda: DEFAULTS["term_years"])
    interest_rate: float = field(default_factory=lambda: DEFAULTS["interest_rate"])
    monthly_rent: float = 0.0
    broker_pct: float = field(default_factory=lambda: DEFAULTS["broker_pct"])
    lawyer_pct: float = field(default_factory=lambda: DEFAULTS["lawyer_pct"])
    extra_costs: float = 0.0
    vat: float = VAT
    repayment_ratio: float = field(default_factory=lambda: DEFAULTS["repayment_ratio"])
    # --- הוצאות שוטפות ומס שכירות (לתשואה נטו) ---
    arnona_monthly: float = 0.0
    vaad_monthly: float = 0.0
    insurance_monthly: float = 0.0
    maintenance_pct: float = field(default_factory=lambda: EXPENSE_DEFAULTS["maintenance_pct"])
    mgmt_pct: float = field(default_factory=lambda: EXPENSE_DEFAULTS["mgmt_pct"])
    vacancy_pct: float = field(default_factory=lambda: EXPENSE_DEFAULTS["vacancy_pct"])
    rental_tax_track: str = "auto"
    marginal_rate: float = 0.31


@dataclass
class DealResult:
    purchase_tax: float
    broker_cost: float
    lawyer_cost: float
    closing_costs: float
    ltv_cap: float
    ltv_actual: float
    mortgage: float
    equity_required: float
    monthly_payment: float
    income_required: float
    total_interest: float
    annual_rent: float
    total_cost: float
    gross_yield: float
    yield_on_cost: float
    monthly_cashflow: float
    cash_on_cash: float
    # --- מדדי נטו (אחרי הוצאות ומס שכירות) ---
    annual_expenses: float = 0.0
    rental_tax: float = 0.0
    rental_tax_track: str = "auto"
    noi: float = 0.0                 # הכנסה תפעולית נטו שנתית
    net_yield: float = 0.0           # תשואה נטו על העלות הכוללת
    cap_rate: float = 0.0            # NOI / מחיר
    net_monthly_cashflow: float = 0.0
    net_cash_on_cash: float = 0.0


def analyze_deal(d: DealInputs) -> DealResult:
    """מחשב את כל מדדי העסקה מקלט יחיד."""
    tax = purchase_tax(d.price, d.buyer_type)
    broker = d.price * d.broker_pct * (1 + d.vat)
    lawyer = d.price * d.lawyer_pct * (1 + d.vat)
    closing = tax + broker + lawyer + d.extra_costs

    cap = LTV_CAPS.get(d.buyer_type, 0.75)
    ltv = min(d.ltv_wanted, cap)
    mortgage = d.price * ltv
    equity = d.price - mortgage + closing

    monthly = pmt(d.interest_rate, d.term_years * 12, mortgage)
    income = monthly / d.repayment_ratio if d.repayment_ratio > 0 else 0.0
    total_interest = monthly * d.term_years * 12 - mortgage

    annual_rent = d.monthly_rent * 12
    total_cost = d.price + closing
    gross_yield = annual_rent / d.price if d.price > 0 else 0.0
    yield_on_cost = annual_rent / total_cost if total_cost > 0 else 0.0
    cashflow = d.monthly_rent - monthly
    coc = cashflow * 12 / equity if equity > 0 else 0.0

    # --- מדדי נטו ---
    effective_rent = annual_rent * (1 - d.vacancy_pct)
    recurring = (d.arnona_monthly + d.vaad_monthly + d.insurance_monthly) * 12
    recurring += d.monthly_rent * (d.maintenance_pct + d.mgmt_pct) * 12
    building_value = d.price * 0.7   # אומדן רכיב המבנה לצורך פחת
    rtax = rental_income_tax(d.monthly_rent, d.rental_tax_track,
                             d.marginal_rate, recurring, building_value)
    noi = effective_rent - recurring
    net_annual = noi - rtax["tax"]
    net_yield = net_annual / total_cost if total_cost > 0 else 0.0
    cap_rate = noi / d.price if d.price > 0 else 0.0
    net_monthly_cf = (net_annual - monthly * 12) / 12
    net_coc = (net_annual - monthly * 12) / equity if equity > 0 else 0.0

    return DealResult(
        purchase_tax=tax, broker_cost=broker, lawyer_cost=lawyer,
        closing_costs=closing, ltv_cap=cap, ltv_actual=ltv, mortgage=mortgage,
        equity_required=equity, monthly_payment=monthly, income_required=income,
        total_interest=total_interest, annual_rent=annual_rent, total_cost=total_cost,
        gross_yield=gross_yield, yield_on_cost=yield_on_cost,
        monthly_cashflow=cashflow, cash_on_cash=coc,
        annual_expenses=recurring, rental_tax=rtax["tax"], rental_tax_track=rtax["chosen"],
        noi=noi, net_yield=net_yield, cap_rate=cap_rate,
        net_monthly_cashflow=net_monthly_cf, net_cash_on_cash=net_coc,
    )


def amortization_schedule(principal: float, annual_rate: float,
                          term_years: int) -> list[dict]:
    """לוח סילוקין שנתי."""
    monthly = pmt(annual_rate, term_years * 12, principal)
    rows = []
    opening = principal
    for year in range(1, term_years + 1):
        closing = remaining_balance(principal, annual_rate, term_years, year)
        principal_paid = opening - closing
        payment = monthly * 12
        interest = max(0.0, payment - principal_paid)
        rows.append({
            "year": year, "opening": round(opening), "payment": round(payment),
            "interest": round(interest), "principal": round(principal_paid),
            "closing": round(closing),
        })
        opening = closing
    return rows


@dataclass
class SaleResult:
    sale_price: float
    remaining_mortgage: float
    selling_cost: float
    gross_gain: float
    inflationary_amount: float
    real_gain: float
    capital_gains_tax: float
    net_from_sale: float
    cumulative_cashflow: float
    equity_invested: float
    total_profit: float
    total_return: float
    annualized_return: float


def project_sale(d: DealInputs, hold_years: int,
                 rent_growth: float | None = None,
                 appreciation: float | None = None,
                 selling_cost_pct: float = 0.02,
                 exempt_capital_gains: bool = False,
                 inflation: float | None = None,
                 high_income: bool = False) -> SaleResult:
    """מודל החזקה ומכירה לאחר hold_years שנים (מס שבח על שבח ריאלי)."""
    rent_growth = DEFAULTS["rent_growth"] if rent_growth is None else rent_growth
    appreciation = DEFAULTS["appreciation"] if appreciation is None else appreciation
    inflation = INFLATION_DEFAULT if inflation is None else inflation
    deal = analyze_deal(d)

    sale_price = d.price * (1 + appreciation) ** hold_years
    rem_mort = remaining_balance(deal.mortgage, d.interest_rate, d.term_years, hold_years)
    sell_cost = sale_price * selling_cost_pct
    gross_gain = sale_price - deal.total_cost - sell_cost
    # הסכום האינפלציוני (פטור) — אינפלציה על בסיס העלות לאורך ההחזקה
    inflationary = deal.total_cost * ((1 + inflation) ** hold_years - 1)
    real_gain = max(0.0, gross_gain - inflationary)
    cgt = capital_gains_tax(gross_gain, inflationary_amount=inflationary,
                            exempt=exempt_capital_gains, high_income=high_income,
                            sale_price=sale_price)
    net_from_sale = sale_price - sell_cost - rem_mort - cgt

    cumulative = 0.0
    for y in range(1, hold_years + 1):
        rent = d.monthly_rent * 12 * (1 + rent_growth) ** (y - 1)
        payment = deal.monthly_payment * 12 if y <= d.term_years else 0.0
        cumulative += rent - payment

    profit = net_from_sale + cumulative - deal.equity_required
    total_return = profit / deal.equity_required if deal.equity_required > 0 else 0.0
    annualized = ((1 + total_return) ** (1 / hold_years) - 1) if hold_years > 0 else 0.0

    return SaleResult(
        sale_price=sale_price, remaining_mortgage=rem_mort, selling_cost=sell_cost,
        gross_gain=gross_gain, inflationary_amount=inflationary, real_gain=real_gain,
        capital_gains_tax=cgt, net_from_sale=net_from_sale,
        cumulative_cashflow=cumulative, equity_invested=deal.equity_required,
        total_profit=profit, total_return=total_return, annualized_return=annualized,
    )


@dataclass
class Tranche:
    """מסלול בתמהיל משכנתא."""
    name: str          # 'prime' | 'fixed' | 'cpi' וכו'
    share: float       # חלק מסך המשכנתא (0-1)
    annual_rate: float
    term_years: int = 25
    is_variable: bool = False   # ריבית משתנה (פריים/משתנה צמודה)


def mortgage_mix(total_mortgage: float, tranches: list[Tranche]) -> dict:
    """
    מחשב החזר חודשי לתמהיל משכנתא מרובה מסלולים.
    מחזיר: {'monthly','blended_rate','variable_share','warning','breakdown':[...]}.
    סכום ה-share מנורמל אוטומטית ל-1.
    כולל אזהרה אם חלק הריבית המשתנה עולה על שני שליש (מגבלת בנק ישראל).
    """
    if not tranches:
        return {"monthly": 0.0, "blended_rate": 0.0, "variable_share": 0.0,
                "warning": None, "breakdown": []}
    total_share = sum(t.share for t in tranches) or 1.0
    breakdown, monthly, variable_share = [], 0.0, 0.0
    for t in tranches:
        share = t.share / total_share
        principal = total_mortgage * share
        pay = pmt(t.annual_rate, t.term_years * 12, principal)
        monthly += pay
        if t.is_variable:
            variable_share += share
        breakdown.append({
            "name": t.name, "share": round(share, 4),
            "principal": round(principal), "rate": t.annual_rate,
            "term_years": t.term_years, "payment": round(pay),
            "is_variable": t.is_variable,
        })
    blended = sum(t.annual_rate * (t.share / total_share) for t in tranches)
    warning = None
    if variable_share > VARIABLE_RATE_CAP + 1e-9:
        warning = (f"חלק הריבית המשתנה ({variable_share*100:.0f}%) חורג ממגבלת "
                   f"בנק ישראל (עד {VARIABLE_RATE_CAP*100:.0f}%).")
    return {"monthly": monthly, "blended_rate": blended,
            "variable_share": variable_share, "warning": warning,
            "breakdown": breakdown}


def opportunity_cost(equity: float, alt_annual_return: float, years: int) -> dict:
    """
    כמה ההון העצמי היה מניב בחלופה (פיקדון/מדד) באותו אופק זמן.
    מחזיר: {'future_value','profit'} — לרווח חלופי להשוואה מול הנדל"ן.
    """
    future = equity * (1 + alt_annual_return) ** years
    return {"future_value": future, "profit": future - equity}
