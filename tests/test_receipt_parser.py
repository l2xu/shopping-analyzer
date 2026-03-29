"""Tests for receipt_parser.py"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsing.receipt_parser import parse_receipt_html

# Minimal Bulgarian-style receipt with two items sold by the piece.
# The purchase_list contains "qty x unit_price" spans that must NOT be
# treated as Pfandrückgabe / deposit-return lines.
BG_RECEIPT_NO_PFAND = """
<span class="purchase_list">
  <span class="article" data-art-id="0496744" data-art-quantity="1" data-unit-price="12,77"
        data-art-description="КОНСТРУКТОР ЦВЕТЕ">КОНСТРУКТОР ЦВЕТЕ</span>
  <span class="article css_bold" data-art-id="0496744" data-art-quantity="1" data-unit-price="12,77"
        data-art-description="КОНСТРУКТОР ЦВЕТЕ">12,77</span>
  <span class="article" data-art-id="7202332" data-art-quantity="1" data-unit-price="3,06"
        data-art-description="KINDER ШОК">KINDER ШОК</span>
  <span class="article css_bold" data-art-id="7202332" data-art-quantity="1" data-unit-price="3,06"
        data-art-description="KINDER ШОК">3,06</span>
</span>
"""

# Same receipt but with a kg item whose span text is "0,248 x 3,55" —
# this must not be misread as a deposit-return calculation either.
BG_RECEIPT_KG_ITEM = """
<span class="purchase_list">
  <span class="article" data-art-id="0082440" data-art-quantity="0,2" data-unit-price="3,55"
        data-art-description="ДОМАТИ РОМА">0,248 x 3,55</span>
  <span class="article" data-art-id="0082440" data-art-quantity="0,2" data-unit-price="3,55"
        data-art-description="ДОМАТИ РОМА">ДОМАТИ РОМА   0,88 B</span>
</span>
"""


def test_no_pfand_savings_when_no_pfandrueckgabe_line():
    """Items with 'qty x price' format must not inflate saved_pfand."""
    result = parse_receipt_html(BG_RECEIPT_NO_PFAND, "r1", "2024.01.15", 0.0, "Lidl BG")
    assert result.get("saved_pfand") is None, (
        f"saved_pfand should be None but got {result.get('saved_pfand')!r} — "
        "item calculation spans are being mistaken for Pfandrückgabe lines"
    )


def test_total_price_set_when_no_savings():
    """total_price must equal total_price_no_saving when there are no savings or pfand."""
    result = parse_receipt_html(BG_RECEIPT_NO_PFAND, "r1", "2024.01.15", 0.0, "Lidl BG")
    assert result.get("total_price") is not None, (
        "total_price is None — likely inflated pfand savings made final_paid go negative"
    )
    assert result.get("total_price") == result.get("total_price_no_saving"), (
        f"total_price {result.get('total_price')!r} != "
        f"total_price_no_saving {result.get('total_price_no_saving')!r}"
    )


def test_kg_item_span_not_treated_as_pfand():
    """A 'qty x unit_price' kg-item span must not produce pfand savings."""
    result = parse_receipt_html(BG_RECEIPT_KG_ITEM, "r2", "2024.01.15", 0.0, "Lidl BG")
    assert result.get("saved_pfand") is None, (
        f"saved_pfand should be None but got {result.get('saved_pfand')!r}"
    )
