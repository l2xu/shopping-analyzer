"""Tests for items_extractor.py"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from bs4 import BeautifulSoup
from parsing.items_extractor import extract_receipt_items_from_html


def make_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


# Minimal HTML representing a kg-sold item where data-art-quantity has only 1
# decimal but the visible receipt text shows 3-decimal precision.
KG_ITEM_HTML = """
<span class="article" data-art-id="TOD001" data-art-description="ДОМАТИ НА КГ"
      data-art-quantity="0,2" data-unit-price="3,55">0,248 kg</span>
<span class="article" data-art-id="TOD001" data-art-description="ДОМАТИ НА КГ"
      data-art-quantity="0,2" data-unit-price="3,55">EUR/kg 3,55</span>
<span class="article css_bold" data-art-id="TOD001" data-art-description="ДОМАТИ НА КГ"
      data-art-quantity="0,2" data-unit-price="3,55">0,88</span>
"""

STK_ITEM_HTML = """
<span class="article" data-art-id="MLK001" data-art-description="ПРЯСНО МЛЯКО 3%"
      data-art-quantity="1" data-unit-price="1,43">ПРЯСНО МЛЯКО 3%</span>
<span class="article css_bold" data-art-id="MLK001" data-art-description="ПРЯСНО МЛЯКО 3%"
      data-art-quantity="1" data-unit-price="1,43">1,43</span>
"""


def test_kg_item_precise_quantity_from_visible_text():
    """Precise weight from visible text must take priority over data-art-quantity."""
    items = extract_receipt_items_from_html(make_soup(KG_ITEM_HTML))
    assert len(items) == 1
    item = items[0]
    assert item["unit"] == "kg"
    # The attribute says "0,2" but visible text shows "0,248 kg" — we want the precise value
    assert item["quantity"] == "0,248", (
        f"Expected '0,248' but got '{item['quantity']}' — "
        "visible-text precision is not being used"
    )


def test_stk_item_quantity_unchanged():
    """Piece-sold items must not have their quantity altered."""
    items = extract_receipt_items_from_html(make_soup(STK_ITEM_HTML))
    assert len(items) == 1
    item = items[0]
    assert item["unit"] == "stk"
    assert item["quantity"] == "1"


# Real Lidl Bulgaria HTML uses "0,248 x 3,55" format (qty x unit_price),
# not "0,248 кг".
REAL_BG_KG_HTML = """
<span class="article" data-art-id="0082440" data-art-quantity="0,2" data-unit-price="3,55"
      data-art-description="ДОМАТИ РОМА, РОЗОВИ">0,248 x 3,55</span>
<span class="article" data-art-id="0082440" data-art-quantity="0,2" data-unit-price="3,55"
      data-art-description="ДОМАТИ РОМА, РОЗОВИ">ДОМАТИ РОМА, РОЗОВИ                   0,88 B</span>
"""


def test_real_bg_format_precise_quantity():
    """Precise weight from 'qty x price' span text must be extracted."""
    items = extract_receipt_items_from_html(make_soup(REAL_BG_KG_HTML))
    assert len(items) == 1
    item = items[0]
    assert item["unit"] == "kg"
    assert item["quantity"] == "0,248", (
        f"Expected '0,248' but got '{item['quantity']}'"
    )


def test_fractional_quantity_detected_as_kg():
    """Items with a non-integer quantity (e.g. 0,7) must be classified as kg."""
    html = """
    <span class="article" data-art-id="BAN001" data-art-description="БАНАНИ НА КГ"
          data-art-quantity="0,7" data-unit-price="1,02">БАНАНИ НА КГ</span>
    <span class="article css_bold" data-art-id="BAN001" data-art-description="БАНАНИ НА КГ"
          data-art-quantity="0,7" data-unit-price="1,02">0,71</span>
    """
    items = extract_receipt_items_from_html(make_soup(html))
    assert len(items) == 1
    assert items[0]["unit"] == "kg", (
        f"Expected 'kg' but got '{items[0]['unit']}' — fractional quantity not recognised as kg"
    )


def test_integer_comma_zero_quantity_stays_stk():
    """Items with a whole-number quantity like 2,0 must remain stk."""
    html = """
    <span class="article" data-art-id="CHO001" data-art-description="ШОКОЛАД"
          data-art-quantity="2,0" data-unit-price="1,38">ШОКОЛАД</span>
    <span class="article css_bold" data-art-id="CHO001" data-art-description="ШОКОЛАД"
          data-art-quantity="2,0" data-unit-price="1,38">2,76</span>
    """
    items = extract_receipt_items_from_html(make_soup(html))
    assert len(items) == 1
    assert items[0]["unit"] == "stk"


def test_kg_item_without_precise_text_falls_back_to_attribute():
    """When no precise weight text is present, fall back to data-art-quantity."""
    html = """
    <span class="article" data-art-id="LEM001" data-art-description="ЛИМОНИ НА КГ"
          data-art-quantity="0,3" data-unit-price="1,99">EUR/kg 1,99</span>
    <span class="article css_bold" data-art-id="LEM001" data-art-description="ЛИМОНИ НА КГ"
          data-art-quantity="0,3" data-unit-price="1,99">0,60</span>
    """
    items = extract_receipt_items_from_html(make_soup(html))
    assert len(items) == 1
    item = items[0]
    assert item["unit"] == "kg"
    assert item["quantity"] == "0,3"


def test_visible_text_deviating_from_api_is_ignored(capsys):
    """If visible text weight deviates ≥0.1 from API quantity, warn and keep API value."""
    html = """
    <span class="article" data-art-id="TOD002" data-art-description="ЯБЪЛКИ НА КГ"
          data-art-quantity="0,2" data-unit-price="2,00">1,248 kg</span>
    <span class="article css_bold" data-art-id="TOD002" data-art-description="ЯБЪЛКИ НА КГ"
          data-art-quantity="0,2" data-unit-price="2,00">0,40</span>
    """
    items = extract_receipt_items_from_html(make_soup(html))
    assert len(items) == 1
    item = items[0]
    assert item["unit"] == "kg"
    # Visible text says 1,248 but API says 0,2 — large deviation, API value must win
    assert item["quantity"] == "0,2", (
        f"Expected '0,2' (API value) but got '{item['quantity']}' — "
        "deviating visible-text value should be ignored"
    )
    captured = capsys.readouterr()
    assert captured.out, "Expected a warning to be printed to stdout"


def test_api_already_has_three_decimals_skips_regex():
    """When data-art-quantity already has 3+ decimal digits, skip visible-text regex."""
    html = """
    <span class="article" data-art-id="TOD003" data-art-description="ДОМАТИ НА КГ"
          data-art-quantity="0,248" data-unit-price="3,55">0,999 kg</span>
    <span class="article css_bold" data-art-id="TOD003" data-art-description="ДОМАТИ НА КГ"
          data-art-quantity="0,248" data-unit-price="3,55">0,88</span>
    """
    items = extract_receipt_items_from_html(make_soup(html))
    assert len(items) == 1
    item = items[0]
    assert item["unit"] == "kg"
    # API already has 3 decimals — must use it as-is, not override with visible text
    assert item["quantity"] == "0,248", (
        f"Expected '0,248' (API value) but got '{item['quantity']}' — "
        "regex should be skipped when API already has 3+ decimals"
    )
