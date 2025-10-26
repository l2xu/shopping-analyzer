"""Receipt repository for CRUD operations."""

from datetime import datetime
from typing import Dict, Any

from .file_manager import load_existing_receipts, save_receipts_to_json


def add_receipt_to_json(receipt_data: Dict[str, Any]) -> None:
    """Add or update a single receipt in the JSON file immediately."""
    existing_ids, existing_receipts = load_existing_receipts()

    # Check if receipt already exists and update it
    receipt_updated = False
    for i, existing_receipt in enumerate(existing_receipts):
        # Check both 'id' and 'url' fields for compatibility
        existing_key = existing_receipt.get("id") or existing_receipt.get("url", "")
        new_key = receipt_data.get("id") or receipt_data.get("url", "")

        if existing_key == new_key:
            existing_receipts[i] = receipt_data
            receipt_updated = True
            break

    # If not found, add as new receipt
    if not receipt_updated:
        existing_receipts.append(receipt_data)

    save_receipts_to_json(existing_receipts)

    action = "aktualisiert" if receipt_updated else "hinzugefügt"
    print(
        f"Kassenbon {action}: {receipt_data['purchase_date']} - {receipt_data['total_price']}"
    )


def sort_receipts_by_date() -> int:
    """Sort all receipts in the JSON file by date (newest first)."""
    _, receipts = load_existing_receipts()

    def get_date_key(receipt):
        date_str = receipt.get("purchase_date")
        if not date_str:
            return datetime.min
        try:
            return datetime.strptime(date_str, "%d.%m.%Y %H:%M")
        except ValueError:
            try:
                return datetime.strptime(date_str, "%d.%m.%Y")
            except ValueError:
                return datetime.min

    sorted_receipts = sorted(receipts, key=get_date_key, reverse=True)
    save_receipts_to_json(sorted_receipts)
    return len(sorted_receipts)
