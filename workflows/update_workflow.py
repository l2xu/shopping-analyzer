"""Update workflow for adding only new receipts."""

import time

from config import LidlConfig
from auth import setup_and_test_session
from api import get_tickets_page, get_receipt_details_and_html
from storage import load_existing_receipts, add_receipt_to_json, sort_receipts_by_date


def update_data() -> bool:
    """
    Add only new receipts and sort by date at the end.

    Returns:
        bool: True if successful, False otherwise
    """
    print("=== UPDATE: Füge neue Kassenbons hinzu ===")

    # Setup session with browser selection, cookie extraction, and API testing
    session = setup_and_test_session()
    if not session:
        return False

    # Collect recent receipt IDs (check first few pages)
    recent_receipt_ids = []

    for page in range(1, LidlConfig.PAGES_TO_CHECK + 1):
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
                    recent_receipt_ids.append(receipt_id)

    # Load existing receipts
    existing_ids, existing_receipts = load_existing_receipts()
    print(f"Bereits vorhandene Kassenbons: {len(existing_receipts)}")

    # Filter for new receipts
    new_receipt_ids = [rid for rid in recent_receipt_ids if rid not in existing_ids]

    print(f"Neue Kassenbons zu verarbeiten: {len(new_receipt_ids)}")

    # Process new receipts
    processed_count = 0

    for i, receipt_id in enumerate(new_receipt_ids, 1):
        print(f"Verarbeite neuen Kassenbon {i}/{len(new_receipt_ids)}: {receipt_id}")

        receipt_data = get_receipt_details_and_html(session, receipt_id)

        if receipt_data and receipt_data["items"]:
            add_receipt_to_json(receipt_data)
            processed_count += 1
            print(f"✓ Hinzugefügt: {len(receipt_data['items'])} Artikel")
        else:
            print("⚠ Fehler beim Verarbeiten")

        time.sleep(LidlConfig.REQUEST_DELAY)

    # Final sort if we added new receipts
    if processed_count > 0:
        total_receipts = sort_receipts_by_date()
        print(f"\n{processed_count} neue Kassenbons hinzugefügt und sortiert.")
    else:
        total_receipts = len(existing_receipts)
        print("\nKeine neuen Kassenbons gefunden.")

    print("\n=== UPDATE ABGESCHLOSSEN ===")
    print(f"Neue Kassenbons hinzugefügt: {processed_count}")
    print(f"Gesamte Kassenbons in Datei: {total_receipts}")

    return True
