"""Receipt ID collection and processing logic."""

import time
from typing import List, Tuple
import requests

from config import LidlConfig
from api import get_tickets_page, get_receipt_details_and_html
from storage import load_existing_receipts, add_receipt_to_json


def collect_all_receipt_ids(session: requests.Session) -> List[str]:
    """
    Collect all receipt IDs from all pages efficiently.

    Args:
        session: requests.Session with authentication

    Returns:
        list: List of all receipt IDs
    """
    all_receipt_ids = []
    page = 1

    print("Sammle alle Kassenbon-IDs mit digitalem Kassenbon über API...")

    while True:
        # Get tickets for current page
        tickets_data = get_tickets_page(session, page)

        if not tickets_data or "items" not in tickets_data:
            break

        tickets = tickets_data["items"]

        if not tickets:
            break

        # Extract receipt IDs from tickets (only those with HTML documents)
        for ticket in tickets:
            if isinstance(ticket, dict):
                if "ticket" in ticket:
                    ticket_data = ticket["ticket"]
                    receipt_id = ticket_data["id"]
                    has_html = ticket_data.get("isHtml", False)
                else:
                    receipt_id = ticket.get("id", "")
                    has_html = ticket.get("isHtml", False)

                if receipt_id and has_html:
                    all_receipt_ids.append(receipt_id)

        page += 1

        # Check if we have more pages
        total_count = tickets_data.get("totalCount", 0)
        page_size = tickets_data.get("size", 10)
        total_pages = (total_count + page_size - 1) // page_size

        if page > total_pages:
            break

    print(f"Gefunden: {len(all_receipt_ids)} Kassenbon-IDs")
    return all_receipt_ids


def process_all_tickets(session: requests.Session) -> Tuple[int, int, int]:
    """
    Process all tickets efficiently by collecting IDs first, then fetching HTML.

    Args:
        session: requests.Session with authentication

    Returns:
        tuple: (processed_count, skipped_count, total_pages)
    """
    processed_count = 0
    skipped_count = 0

    # Load existing receipts to avoid duplicates
    existing_ids, _ = load_existing_receipts()

    # Collect all receipt IDs first
    all_receipt_ids = collect_all_receipt_ids(session)

    print(f"Zu verarbeitende Kassenbons: {len(all_receipt_ids)}")
    print(f"Bereits vorhandene: {len(existing_ids)}")

    # Filter out already processed receipts
    new_receipt_ids = [rid for rid in all_receipt_ids if rid not in existing_ids]

    print(f"Neue Kassenbons zu verarbeiten: {len(new_receipt_ids)}")

    # Process each new receipt
    for i, receipt_id in enumerate(new_receipt_ids, 1):
        print(f"Verarbeite Kassenbon {i}/{len(new_receipt_ids)}: {receipt_id}")

        # Get receipt details and HTML
        receipt_data = get_receipt_details_and_html(session, receipt_id)

        if receipt_data and receipt_data["items"]:
            add_receipt_to_json(receipt_data)
            processed_count += 1
            print(f"✓ Verarbeitet: {len(receipt_data['items'])} Artikel")
        else:
            print("⚠ Fehler beim Verarbeiten")
            skipped_count += 1

        # Add pause between requests to be respectful
        time.sleep(LidlConfig.REQUEST_DELAY)

    return processed_count, skipped_count, len(all_receipt_ids) // 10 + 1
