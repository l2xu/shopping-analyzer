"""Main receipt HTML parser."""

import re
from typing import Dict, Any
from bs4 import BeautifulSoup

from .info_extractor import extract_basic_receipt_info_from_html
from .items_extractor import extract_receipt_items_from_html


def parse_receipt_html(
    html_content: str, receipt_id: str, receipt_date: str, total_amount: float, store: str
) -> Dict[str, Any]:
    """
    Parse receipt HTML content to extract items and other data using the exact mechanisms from the provided code snippet.

    Args:
        html_content: HTML content of the receipt (from ticket.htmlPrintedReceipt)
        receipt_id: Receipt ID
        receipt_date: Receipt date
        total_amount: Total amount from API (might be 0)
        store: Store name

    Returns:
        dict: Parsed receipt data
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Extract basic receipt info using the exact logic from the provided code snippet
    receipt_data = extract_basic_receipt_info_from_html(
        soup, receipt_id, receipt_date, store
    )

    # Extract items using the exact logic from the provided code snippet
    receipt_data["items"] = extract_receipt_items_from_html(soup)

    # Calculate total from items (this is the price without any savings)
    total_from_items = 0.0
    for item in receipt_data.get("items", []):
        try:
            item_price = float(item.get("price", "0").replace(",", "."))
            item_qty = float(item.get("quantity", "1").replace(",", "."))
            total_from_items += item_price * item_qty
        except (ValueError, AttributeError):
            pass

    if total_from_items > 0:
        receipt_data["total_price_no_saving"] = f"{total_from_items:.2f}".replace(
            ".", ","
        )

        # Extract savings to calculate final paid price
        total_savings = 0.0

        # Add regular savings (Preisvorteil, Rabatt)
        if receipt_data.get("saved_amount"):
            try:
                saved_amount = float(receipt_data["saved_amount"].replace(",", "."))
                total_savings += saved_amount
            except (ValueError, AttributeError):
                pass

        # Add Lidl Plus savings
        if receipt_data.get("lidlplus_saved_amount"):
            try:
                lidl_savings = float(
                    receipt_data["lidlplus_saved_amount"].replace(",", ".")
                )
                total_savings += lidl_savings
            except (ValueError, AttributeError):
                pass

        # Extract pfand savings from HTML
        pfand_savings = 0.0
        try:
            purchase_list = soup.find("span", class_="purchase_list")
            if purchase_list:
                purchase_text = purchase_list.get_text()

                # Look for Pfandrückgabe lines (format: "Pfandrückgabe" followed by amount)
                # Use more specific regex to avoid matching calculation lines
                pfand_matches = re.findall(
                    r"Pfandrückgabe\s*(-?\d+,\d+)", purchase_text
                )
                for match in pfand_matches:
                    try:
                        pfand_val = float(match.replace(",", "."))
                        pfand_savings += abs(
                            pfand_val
                        )  # Take absolute value since it's negative in receipt
                    except (ValueError, AttributeError):
                        pass

                # If no direct Pfandrückgabe amount found, look for calculation lines
                if pfand_savings == 0:
                    pfand_calc_matches = re.findall(
                        r"(-?\d+)\s*x\s*(-?\d+,\d+)", purchase_text
                    )
                    for qty_match, price_match in pfand_calc_matches:
                        try:
                            qty = float(qty_match)
                            price = float(price_match.replace(",", "."))
                            calculated_pfand = abs(qty * price)  # Take absolute value
                            pfand_savings += calculated_pfand
                        except (ValueError, AttributeError):
                            pass
        except:
            pass

        if pfand_savings > 0:
            receipt_data["saved_pfand"] = f"{pfand_savings:.2f}".replace(".", ",")
            total_savings += pfand_savings

        # Calculate final paid price
        final_paid = total_from_items - total_savings
        if final_paid > 0:
            receipt_data["total_price"] = f"{final_paid:.2f}".replace(".", ",")

    return receipt_data
