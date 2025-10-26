"""File I/O operations for receipt data."""

import os
import json
from typing import Dict, List, Any


def load_existing_receipts() -> tuple[set[str], list[Dict[str, Any]]]:
    """Load existing receipts from JSON file."""
    from config import LidlConfig
    
    if not os.path.exists(LidlConfig.RECEIPTS_JSON_FILE):
        return set(), []

    try:
        with open(LidlConfig.RECEIPTS_JSON_FILE, "r", encoding="utf-8") as file:
            receipts = json.load(file)
        # Handle both old format (with 'url') and new format (with 'id')
        existing_ids = set()
        for receipt in receipts:
            if "id" in receipt:
                existing_ids.add(receipt["id"])
            elif "url" in receipt:
                # For backward compatibility with old format
                existing_ids.add(receipt["url"])
        return existing_ids, receipts
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Warning: Error loading existing receipts: {e}")
        return set(), []


def save_receipts_to_json(receipts: List[Dict[str, Any]]) -> None:
    """Save all receipts to JSON file."""
    from config import LidlConfig
    
    with open(LidlConfig.RECEIPTS_JSON_FILE, "w", encoding="utf-8") as file:
        json.dump(receipts, file, ensure_ascii=False, indent=2)
