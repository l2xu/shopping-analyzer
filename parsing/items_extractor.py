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

                # Determine unit (kg or stk) from text content
                unit = "stk"
                for span in spans:
                    span_text = span.get_text()
                    if "kg" in span_text or "EUR/kg" in span_text:
                        unit = "kg"
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
