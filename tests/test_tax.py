import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from realestate.tax import purchase_tax, capital_gains_tax  # noqa: E402


def test_single_home_under_exemption():
    # מתחת לסף הראשון => פטור מלא
    assert purchase_tax(1_900_000, "single") == 0


def test_single_home_second_bracket():
    # 2,000,000: רק 21,255 מעל הסף הראשון ב-3.5%
    tax = purchase_tax(2_000_000, "single")
    assert round(tax) == 744


def test_investment_first_shekel():
    # דירה להשקעה: 8% מהשקל הראשון
    assert purchase_tax(2_000_000, "invest") == 160_000


def test_investment_top_bracket():
    # מעל 6,055,070 => 8% עד הסף + 10% מעבר
    tax = purchase_tax(7_000_000, "invest")
    expected = 6_055_070 * 0.08 + (7_000_000 - 6_055_070) * 0.10
    assert round(tax) == round(expected)


def test_improve_uses_single_brackets():
    assert purchase_tax(2_000_000, "improve") == purchase_tax(2_000_000, "single")


def test_capital_gains_basic():
    assert capital_gains_tax(400_000) == 100_000


def test_capital_gains_exempt():
    assert capital_gains_tax(400_000, exempt=True) == 0


def test_capital_gains_no_gain():
    assert capital_gains_tax(-50_000) == 0
