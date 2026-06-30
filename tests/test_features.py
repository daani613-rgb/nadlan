import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from realestate.tax import rental_income_tax  # noqa: E402
from realestate.finance import (  # noqa: E402
    analyze_deal, DealInputs, mortgage_mix, opportunity_cost, Tranche,
)


# ---- מס הכנסה משכירות ----
def test_rental_tax_exempt_below_ceiling():
    r = rental_income_tax(5000, track="auto")
    assert r["exempt"] == 0
    assert r["chosen"] == "exempt"
    assert r["tax"] == 0


def test_rental_tax_flat_track():
    r = rental_income_tax(8000, track="flat")
    assert r["tax"] == 8000 * 12 * 0.10


def test_rental_tax_partial_exemption():
    # 7000: פטור מתואם = 2*5654 - 7000 = 4308; חייב = 7000-4308 = 2692/חודש
    r = rental_income_tax(7000, track="exempt", marginal_rate=0.31)
    taxable_annual = (7000 - (2 * 5654 - 7000)) * 12
    assert round(r["exempt"]) == round(taxable_annual * 0.31)


def test_rental_tax_auto_picks_cheapest():
    r = rental_income_tax(8000, track="auto")
    assert r["tax"] == min(r["exempt"], r["flat"], r["marginal"])


# ---- תשואה נטו ----
def test_net_yield_below_gross():
    d = DealInputs(price=2_000_000, buyer_type="invest", ltv_wanted=0.5,
                   interest_rate=0.048, monthly_rent=6000,
                   arnona_monthly=300, vaad_monthly=200, insurance_monthly=80)
    r = analyze_deal(d)
    assert r.net_yield < r.gross_yield
    assert r.noi < r.annual_rent
    assert r.cap_rate > 0


def test_net_metrics_present():
    d = DealInputs(price=2_000_000, buyer_type="invest", monthly_rent=7000)
    r = analyze_deal(d)
    assert r.rental_tax_track in ("exempt", "flat", "marginal")
    assert r.annual_expenses > 0


# ---- תמהיל משכנתא ----
def test_mortgage_mix_sums_payments():
    tr = [Tranche("prime", 0.5, 0.055, 25), Tranche("fixed", 0.5, 0.045, 25)]
    mix = mortgage_mix(1_000_000, tr)
    assert len(mix["breakdown"]) == 2
    assert round(mix["blended_rate"], 4) == 0.05
    # ההחזר הכולל = סכום החזרי המסלולים (עד הפרש עיגול)
    assert abs(round(mix["monthly"]) - sum(b["payment"] for b in mix["breakdown"])) <= 1


def test_mortgage_mix_normalizes_shares():
    tr = [Tranche("a", 1, 0.05, 25), Tranche("b", 1, 0.05, 25)]  # סכום 2 -> מנורמל
    mix = mortgage_mix(1_000_000, tr)
    assert abs(sum(b["share"] for b in mix["breakdown"]) - 1.0) < 1e-9


# ---- עלות הזדמנות ----
def test_opportunity_cost_growth():
    o = opportunity_cost(500_000, 0.04, 10)
    assert round(o["future_value"]) == round(500_000 * 1.04 ** 10)
    assert o["profit"] > 0


# ---- תיקונים: מס שבח ריאלי, פטור, יסף, מגבלת ריבית משתנה ----
from realestate.tax import capital_gains_tax  # noqa: E402
from realestate.finance import project_sale  # noqa: E402


def test_capital_gains_real_below_nominal():
    # אינפלציה מקטינה את השבח החייב לעומת חישוב נומינלי
    nominal = capital_gains_tax(400_000, inflationary_amount=0)
    real = capital_gains_tax(400_000, inflationary_amount=150_000)
    assert real < nominal
    assert real == (400_000 - 150_000) * 0.25


def test_capital_gains_inflation_wipes_gain():
    # אם כל השבח אינפלציוני -> אין מס
    assert capital_gains_tax(200_000, inflationary_amount=250_000) == 0


def test_capital_gains_surtax():
    base = capital_gains_tax(1_000_000)
    with_surtax = capital_gains_tax(1_000_000, high_income=True)
    assert round(with_surtax - base) == round(1_000_000 * 0.05)


def test_single_residence_exemption_ceiling():
    # מתחת לתקרה -> פטור מלא
    assert capital_gains_tax(500_000, exempt=True, sale_price=4_000_000) == 0
    # מעל התקרה -> חיוב יחסי בלבד
    tax = capital_gains_tax(500_000, exempt=True, sale_price=10_000_000)
    assert tax > 0
    frac = (10_000_000 - 5_008_000) / 10_000_000
    assert round(tax) == round(500_000 * frac * 0.25)


def test_project_sale_real_gain_lower_tax():
    d = DealInputs(price=2_000_000, buyer_type="invest", ltv_wanted=0.5,
                   interest_rate=0.048, monthly_rent=7000)
    s = project_sale(d, hold_years=10, appreciation=0.035, inflation=0.025)
    assert s.real_gain < s.gross_gain          # אינפלציה מנכה חלק מהשבח
    assert s.inflationary_amount > 0


def test_mortgage_mix_variable_warning():
    from realestate.finance import mortgage_mix, Tranche
    # 80% פריים (משתנה) -> חריגה ממגבלת שני שליש
    tr = [Tranche("prime", 0.8, 0.055, 25, is_variable=True),
          Tranche("fixed", 0.2, 0.045, 25)]
    mix = mortgage_mix(1_000_000, tr)
    assert mix["warning"] is not None
    assert round(mix["variable_share"], 2) == 0.80


def test_mortgage_mix_no_warning_within_cap():
    from realestate.finance import mortgage_mix, Tranche
    tr = [Tranche("prime", 0.5, 0.055, 25, is_variable=True),
          Tranche("fixed", 0.5, 0.045, 25)]
    mix = mortgage_mix(1_000_000, tr)
    assert mix["warning"] is None
