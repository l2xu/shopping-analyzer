"""Extract basic receipt information from HTML content."""

import re
from typing import Dict, Any
from bs4 import BeautifulSoup


def extract_basic_receipt_info_from_html(
    soup: BeautifulSoup, receipt_id: str, receipt_date: str, store: str
) -> Dict[str, Any]:
    """Extract basic receipt information using the exact logic from the provided code snippet."""
    receipt_data = {
        "id": receipt_id,
        "purchase_date": receipt_date,
        "total_price": None,  # Final amount actually paid
        "total_price_no_saving": None,  # Sum of all items without any savings
        "saved_amount": None,  # Regular savings (Preisvorteil, Rabatt)
        "sticker_discount_amount": None,  # RABATT X% sticker monetary amount
        "sticker_discount_pct": [],
        "saved_pfand": None,  # Pfand/deposit returns
        "lidlplus_saved_amount": None,  # Lidl Plus savings
        "store": store,
        "items": [],
    }

    # Extract total price (amount to pay - "zu zahlen")
    try:
        # Method 1: Look for "zu zahlen" line and extract the amount from the same line
        purchase_summary_elements = soup.find_all(id=re.compile(r"^purchase_summary_"))
        for element in purchase_summary_elements:
            element_text = element.get_text().strip()
            if "zu zahlen" in element_text:
                # Find all spans with bold class in the same parent to get the amount
                parent = element.parent
                amount_spans = parent.find_all("span", class_="css_bold")
                for span in amount_spans:
                    span_text = span.get_text().strip()
                    # Look for a price pattern (digits,digits)
                    if re.match(r"^\d+,\d+$", span_text):
                        receipt_data["total_price"] = span_text
                        break
                if receipt_data["total_price"]:
                    break
    except:
        # Fallback: Try the old method from purchase_tender_information_5
        try:
            total_element = soup.find(id="purchase_tender_information_5")
            if total_element:
                parts = total_element.get_text().strip().split()
                if len(parts) >= 2:
                    receipt_data["total_price"] = parts[-2]
        except:
            pass

    # Extract saved amount (only "Preisvorteil" and "Rabatt" lines, excluding "Lidl Plus Rabatt")
    try:
        total_regular_savings = 0.0

        # Get the purchase list text and search for discount lines
        try:
            purchase_list = soup.find("span", class_="purchase_list")
            if purchase_list:
                purchase_text = purchase_list.get_text()

                # Find all discount lines and extract the amounts
                lines = purchase_text.split("\n")
                # Regex to find monetary amount like -0,20 or - 0.20 or 0,20
                amount_regex = re.compile(r"-?\s*(\d+[\.,]\d{2})")
                pct_regex = re.compile(r"rabatt\s*(\d{1,3})\s*%")
                for line in lines:
                    line_stripped = line.strip()
                    line_lower = line_stripped.lower()

                    # Include "Preisvorteil" lines (exclude summary lines)
                    if "preisvorteil" in line_lower and "gesamter" not in line_lower:
                        amount_match = amount_regex.search(line_stripped)
                        if amount_match:
                            amount_str = amount_match.group(1)
                            amount_float = float(amount_str.replace(",", "."))
                            total_regular_savings += amount_float

                    # Exclude Lidl Plus Rabatt explicitly
                    elif "rabatt" in line_lower and "lidl plus rabatt" not in line_lower:
                        # Check for percent sticker like "RABATT 20%"
                        pct_match = pct_regex.search(line_lower)
                        amount_match = amount_regex.search(line_stripped)

                        if pct_match:
                            try:
                                pct_val = int(pct_match.group(1))
                                # record the percent (keep as int)
                                receipt_data.setdefault("sticker_discount_pct", []).append(pct_val)
                            except ValueError:
                                pass

                        # If a monetary amount is present on the same line, treat as sticker monetary saving
                        if amount_match:
                            amount_str = amount_match.group(1)
                            try:
                                amount_float = float(amount_str.replace(",", "."))
                                # accumulate into regular savings as well for backward compatibility
                                total_regular_savings += amount_float
                                # also accumulate into sticker-specific total
                                # use a temp var to collect sticker amounts
                                if receipt_data.get("sticker_discount_amount") is None:
                                    receipt_data["sticker_discount_amount"] = 0.0
                                receipt_data["sticker_discount_amount"] += amount_float
                            except (ValueError, AttributeError):
                                pass
        except:
            pass

        # Set the saved_amount if we found any regular savings
        if total_regular_savings > 0:
            receipt_data["saved_amount"] = f"{total_regular_savings:.2f}".replace(
                ".", ","
            )
    except:
        pass

    # Extract Lidl Plus savings
    try:
        # Look for the "Mit Lidl Plus" box that shows "X,XX EUR gespart"
        try:
            # First, try to find the specific "EUR gespart" text in the VAT info section
            vat_info_elements = soup.find_all("span", class_="vat_info")
            for element in vat_info_elements:
                element_text = element.get_text().strip()
                if "EUR gespart" in element_text:
                    # Extract the amount before "EUR gespart"
                    amount_match = re.search(r"(\d+,\d+)\s+EUR gespart", element_text)
                    if amount_match:
                        receipt_data["lidlplus_saved_amount"] = amount_match.group(1)
                        break
        except:
            # Fallback: search in the entire page for "EUR gespart"
            try:
                page_text = soup.get_text()
                gespart_match = re.search(r"(\d+,\d+)\s+EUR gespart", page_text)
                if gespart_match:
                    receipt_data["lidlplus_saved_amount"] = gespart_match.group(1)
            except:
                pass
    except:
        pass

    return receipt_data
