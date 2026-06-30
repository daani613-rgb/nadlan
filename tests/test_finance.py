import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from realestate.finance import (  # noqa: E402
    pmt, remaining_balance, analyze_deal, amortization_schedule,
    project_sale, DealInputs,
)
from realestate.parser import parse_listing  # noqa: E402


def test_pmt_known_value():
    # 1.5M, 4.8%, 25y => ~8595
    assert round(pmt(0.048, 25 * 12, 1_500_000)) == 8595


def test_pmt_zero_principal():
    assert pmt(0.05, 240, 0) == 0


def test_remaining_balance_endpoints():
    assert remaining_balance(1_000_000, 0.05, 25, 0) == 1_000_000
    assert remaining_balance(1_000_000, 0.05, 25, 25) == 0


def test_analyze_deal_single():
    d = DealInputs(price=2_000_000, buyer_type="single", ltv_wanted=0.75,
                   interest_rate=0.048, term_years=25, monthly_rent=6000)
    r = analyze_deal(d)
    assert r.purchase_tax == 744 or round(r.purchase_tax) == 744
    assert r.mortgage == 1_500_000
    assert round(r.monthly_payment) == 8595
    assert round(r.gross_yield, 3) == 0.036


def test_ltv_cap_enforced_for_investment():
    # ביקש 75% אבל השקעה מוגבלת ל-50%
    d = DealInputs(price=2_000_000, buyer_type="invest", ltv_wanted=0.75)
    r = analyze_deal(d)
    assert r.ltv_actual == 0.50
    assert r.mortgage == 1_000_000


def test_amortization_pays_off():
    sched = amortization_schedule(1_000_000, 0.05, 20)
    assert len(sched) == 20
    assert sched[-1]["closing"] == 0
    assert sched[0]["opening"] == 1_000_000


def test_project_sale_positive_return():
    d = DealInputs(price=2_000_000, buyer_type="single", ltv_wanted=0.75,
                   interest_rate=0.048, term_years=25, monthly_rent=6000)
    s = project_sale(d, hold_years=10, appreciation=0.035, rent_growth=0.03)
    assert s.sale_price > d.price
    assert s.annualized_return > 0


def test_parse_listing_full():
    txt = 'דירה למכירה ברמת גן, 4 חדרים, 95 מ"ר, קומה 3, מחיר 2,650,000 ₪'
    r = parse_listing(txt)
    assert r["price"] == 2_650_000
    assert r["rooms"] == 4
    assert r["sqm"] == 95
    assert r["floor"] == 3


def test_parse_listing_with_rent():
    txt = "להשקעה 3 חד' 68 מטר בבת ים. מחיר 1,750,000 שח. שכ\"ד 5,800"
    r = parse_listing(txt)
    assert r["price"] == 1_750_000
    assert r["rent"] == 5_800


def test_parse_listing_fallback_price():
    txt = "דופלקס 5 חדרים 140 מטר בכרמיאל 3,100,000"
    r = parse_listing(txt)
    assert r["price"] == 3_100_000
