"""Extract receipt items from HTML content."""

import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup


def extract_receipt_items_from_html(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Extract items from receipt using the exact logic from the provided code snippet."""
    items = []
    try:
        # Find all article spans (they contain data-art-* attributes)
        article_spans = soup.find_all("span", class_="article")

        if not article_spans:
            print(f"Keine Artikel-Spans gefunden")
            return items

        # Group spans by article ID and description to handle duplicates
        # This handles cases where same article ID appears with different descriptions
        items_by_id_and_desc = {}
        for span in article_spans:
            art_id = span.get("data-art-id")
            art_description = span.get("data-art-description", "")
            if art_id and art_description:
                key = f"{art_id}_{art_description}"
                if key not in items_by_id_and_desc:
                    items_by_id_and_desc[key] = []
                items_by_id_and_desc[key].append(span)

        # Process each article
        for art_id_and_desc, spans in items_by_id_and_desc.items():
            try:
                # Get the first span (should contain all the data attributes)
                main_span = spans[0]

                # Extract item details from data attributes
                art_description = main_span.get("data-art-description", "")
                art_quantity = main_span.get("data-art-quantity", "1")
                unit_price = main_span.get("data-unit-price", "")

                if not art_description or not unit_price:
                    continue

                # Extract total price from span text - look for the bold price
                total_price_text = unit_price  # Default to unit price
                for span in spans:
                    # Check if this span has the css_bold class (indicating it's the total price)
                    span_class = span.get("class", [])
                    if "css_bold" in span_class:
                        span_text = span.get_text().strip()
                        # Look for price pattern (digits,digits)
                        if re.match(r"^\d+,\d+$", span_text):
                            # Check if this is likely the total price (not unit price)
                            try:
                                price_val = float(span_text.replace(",", "."))
                                unit_val = float(unit_price.replace(",", "."))
                                qty_val = float(art_quantity.replace(",", "."))

                                # If this matches the expected total, use it
                                expected_total = unit_val * qty_val
                                if abs(price_val - expected_total) < 0.01:
                                    total_price_text = span_text
                                    break
                            except (ValueError, AttributeError):
                                pass

                # Determine unit (kg or stk).
                # Primary signal: a non-integer quantity (e.g. "0,7", "1,4") means
                # the item is priced per kg.  Whole-number quantities with a trailing
                # ",0" (e.g. "2,0" for 2 pieces) must remain stk.
                unit = "stk"
                try:
                    qty_float = float(art_quantity.replace(",", "."))
                    if qty_float != int(qty_float):
                        unit = "kg"
                except (ValueError, AttributeError):
                    pass
                # Fallback: scan span text for "kg" or "кг" markers
                if unit == "stk":
                    for span in spans:
                        span_text = span.get_text()
                        if "kg" in span_text or "кг" in span_text or "КГ" in span_text:
                            unit = "kg"
                            break

                # For kg items, try to extract precise weight from visible text.
                # The data-art-quantity attribute is truncated to 1 decimal by Lidl's
                # server, while the visible receipt text has full precision.
                # Two known formats:
                #   "0,248 kg"  / "0,248 кг"  (unit label after quantity)
                #   "0,248 x 3,55"            (qty x unit_price, Lidl Bulgaria)
                if unit == "kg":
                    for span in spans:
                        span_text = span.get_text()
                        weight_match = (
                            re.search(r"(\d+[,\.]\d{2,})\s*(?:kg|кг|КГ)", span_text)
                            or re.search(r"(\d+[,\.]\d{2,})\s*x\s*\d", span_text)
                        )
                        if weight_match:
                            art_quantity = weight_match.group(1)
                            break

                # Convert values for calculation
                try:
                    quantity = float(art_quantity.replace(",", "."))
                except (ValueError, AttributeError):
                    quantity = 1.0

                try:
                    price = float(unit_price.replace(",", "."))
                except (ValueError, AttributeError):
                    price = 0.0

                items.append(
                    {
                        "name": art_description,
                        "price": unit_price,
                        "quantity": art_quantity,
                        "unit": unit,
                    }
                )

            except Exception as e:
                print(f"Fehler beim Extrahieren eines Artikels: {e}")

    except Exception as e:
        print(f"Artikel nicht gefunden: {e}")

    return items
