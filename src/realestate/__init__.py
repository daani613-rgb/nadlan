"""ערכת ניתוח השקעות נדל"ן — ישראל 2026."""
from .config import LTV_CAPS, VAT, BUYER_TYPES
from .tax import purchase_tax, capital_gains_tax, rental_income_tax
from .finance import (
    DealInputs, DealResult, analyze_deal,
    amortization_schedule, project_sale, pmt, remaining_balance,
    Tranche, mortgage_mix, opportunity_cost,
)
from .parser import parse_listing

__version__ = "0.3.0"
__all__ = [
    "LTV_CAPS", "VAT", "BUYER_TYPES",
    "purchase_tax", "capital_gains_tax", "rental_income_tax",
    "DealInputs", "DealResult", "analyze_deal",
    "amortization_schedule", "project_sale", "pmt", "remaining_balance",
    "Tranche", "mortgage_mix", "opportunity_cost",
    "parse_listing",
]
