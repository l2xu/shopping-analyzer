"""Receipt ID collection and processing logic."""

import time
from typing import List, Tuple
import requests

from config import LidlConfig
from api import get_tickets_page, get_receipt_details_and_html
from storage import load_existing_receipts, add_receipt_to_json
from .progress_display import ReceiptProgressDisplay, ProgressState


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

        # Log unknown fields on the first ticket of the first page for API discovery.
        _logged_list_discovery = getattr(collect_all_receipt_ids, "_logged_list_discovery", False)

        # Extract receipt IDs from tickets (only those with HTML documents)
        for ticket in tickets:
            if isinstance(ticket, dict):
                if "ticket" in ticket:
                    ticket_data = ticket["ticket"]
                    receipt_id = ticket_data["id"]
                    has_html = ticket_data.get("isHtml", False)
                else:
                    ticket_data = ticket
                    receipt_id = ticket.get("id", "")
                    has_html = ticket.get("isHtml", False)

                # Log unknown fields once to discover richer API data
                if not _logged_list_discovery and isinstance(ticket_data, dict):
                    known_list_keys = {"id", "isHtml", "date", "totalAmount", "store"}
                    unknown = set(ticket_data.keys()) - known_list_keys
                    if unknown:
                        print(f"  [API discovery] ticket list item has extra fields: {sorted(unknown)}")
                        for key in sorted(unknown):
                            val = repr(ticket_data[key])
                            if len(val) > 200:
                                val = val[:200] + "…"
                            print(f"    {key}: {val}")
                    collect_all_receipt_ids._logged_list_discovery = True
                    _logged_list_discovery = True

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

    progress = ReceiptProgressDisplay()
    total_new = len(new_receipt_ids)
    total_items = 0
    error_count = 0
    current_receipt = "-"

    progress.render(
        ProgressState(
            current=0,
            total=total_new,
            added=processed_count,
            skipped=skipped_count,
            errors=error_count,
            items=total_items,
            current_receipt=current_receipt,
        )
    )

    # Process each new receipt
    for i, receipt_id in enumerate(new_receipt_ids, 1):
        current_receipt = receipt_id
        progress.render(
            ProgressState(
                current=i - 1,
                total=total_new,
                added=processed_count,
                skipped=skipped_count,
                errors=error_count,
                items=total_items,
                current_receipt=current_receipt,
            )
        )

        # Get receipt details and HTML
        receipt_data = get_receipt_details_and_html(session, receipt_id)

        if receipt_data and receipt_data["items"]:
            add_receipt_to_json(receipt_data, verbose=False)
            processed_count += 1
            total_items += len(receipt_data["items"])
        else:
            skipped_count += 1
            error_count += 1

        progress.render(
            ProgressState(
                current=i,
                total=total_new,
                added=processed_count,
                skipped=skipped_count,
                errors=error_count,
                items=total_items,
                current_receipt=current_receipt,
            )
        )

        # Add pause between requests to be respectful
        time.sleep(LidlConfig.REQUEST_DELAY)

    progress.close()

    return processed_count, skipped_count, len(all_receipt_ids) // 10 + 1
