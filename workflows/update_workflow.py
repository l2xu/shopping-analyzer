"""Update workflow for adding only new receipts."""

import time
from typing import Optional

from config import LidlConfig
from auth import setup_and_test_session
from api import get_tickets_page, get_receipt_details_and_html
from storage import load_existing_receipts, add_receipt_to_json, sort_receipts_by_date
from .progress_display import ReceiptProgressDisplay, ProgressState


def update_data(
    auth_method: Optional[str] = None,
    cookies_file: Optional[str] = None,
) -> bool:
    """
    Add only new receipts and sort by date at the end.

    Args:
        auth_method: Authentication method - 'firefox', 'chrome', 'chromium', or 'file'.
                     If None, prompts user interactively.
        cookies_file: Path to cookies file (only used when auth_method is 'file').

    Returns:
        bool: True if successful, False otherwise
    """
    print("=== UPDATE: Füge neue Kassenbons hinzu ===")

    # Setup session with browser selection, cookie extraction, and API testing
    session = setup_and_test_session(auth_method, cookies_file)
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
    skipped_count = 0
    error_count = 0
    total_items = 0
    progress = ReceiptProgressDisplay()
    total_new = len(new_receipt_ids)
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

        time.sleep(LidlConfig.REQUEST_DELAY)

    progress.close()

    # Final sort if we added new receipts
    if processed_count > 0:
        total_receipts = sort_receipts_by_date()
        print(f"\n{processed_count} neue Kassenbons hinzugefügt und sortiert.")
    else:
        total_receipts = len(existing_receipts)
        print("\nKeine neuen Kassenbons gefunden.")

    print("\n=== UPDATE ABGESCHLOSSEN ===")
    print(f"Neue Kassenbons hinzugefügt: {processed_count}")
    print(f"Fehler/Uebersprungen: {skipped_count}")
    print(f"Verarbeitete Artikel: {total_items}")
    print(f"Gesamte Kassenbons in Datei: {total_receipts}")

    return True
