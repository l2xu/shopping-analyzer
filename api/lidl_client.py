"""Lidl API client for fetching receipt data."""

import json
from typing import Optional, Dict, Any
import requests

from config import LidlConfig
from parsing import parse_receipt_html


def get_tickets_page(
    session: requests.Session, page: int = 1
) -> Optional[Dict[str, Any]]:
    """
    Fetch tickets for a specific page using the API.

    Args:
        session: requests.Session with authentication
        page: Page number to fetch

    Returns:
        dict: API response data or None if error
    """
    try:
        response = session.get(
            f"{LidlConfig.get_tickets_url()}?country={LidlConfig.get_country_code()}&page={page}",
            timeout=LidlConfig.DEFAULT_TIMEOUT,
        )
        response.raise_for_status()

        data = response.json()

        # Handle different response structures
        if isinstance(data, list):
            # Direct array of tickets
            return {
                "items": data,
                "page": page,
                "size": len(data),
                "totalCount": len(data),
            }
        elif isinstance(data, dict):
            # Structured response with metadata
            return data
        else:
            print(f"Unerwartete API-Antwort-Struktur für Seite {page}")
            return None

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print(f"✗ Nicht autorisiert beim Abrufen der Tickets-Seite {page}")
            print(
                "Bitte stelle sicher, dass du in deinem Browser bei Lidl angemeldet bist."
            )
        else:
            print(f"✗ HTTP-Fehler beim Abrufen der Tickets-Seite {page}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"✗ Fehler beim Abrufen der Tickets-Seite {page}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"✗ JSON-Decodierungsfehler für Seite {page}: {e}")
        return None


def get_receipt_details_and_html(
    session: requests.Session, receipt_id: str
) -> Optional[Dict[str, Any]]:
    """
    Fetch receipt details and HTML content for a specific receipt.

    Args:
        session: requests.Session with authentication
        receipt_id: Receipt ID to fetch

    Returns:
        dict: Parsed receipt data or None if error
    """
    try:
        url = LidlConfig.get_receipt_url(receipt_id)
        full_url = f"{url}?country={LidlConfig.get_country_code()}&languageCode={LidlConfig.get_language_code()}"

        response = session.get(full_url, timeout=LidlConfig.DEFAULT_TIMEOUT)
        response.raise_for_status()

        data = response.json()

        # Extract ticket data from the response
        if "ticket" in data:
            ticket_data = data["ticket"]
        else:
            ticket_data = data

        # Extract basic info
        receipt_date = ticket_data["date"][:10].replace("-", ".")
        total_amount = ticket_data["totalAmount"]

        # Handle store info (could be nested or direct)
        raw_store = ticket_data.get("store", {})
        if isinstance(raw_store, dict):
            store = raw_store.get("name", "Unknown")
            store_details = {
                k: raw_store.get(k)
                for k in ("id", "name", "address", "postalCode", "locality")
                if raw_store.get(k) is not None
            }
        else:
            store = raw_store or "Unknown"
            store_details = {"name": store} if store else {}

        # Log any fields in the API response that we don't currently use,
        # so we can discover richer data the server may provide.
        known_keys = {
            "date", "totalAmount", "store", "htmlPrintedReceipt", "id", "isHtml",
            # fields now captured
            "codes", "storeNumber", "languageCode",
            # presentational / low-value fields confirmed by inspection
            "sequenceNumber", "workstation", "isDeleted",
            "logoUrl", "showCopy", "collectingModel",
            "returnTickets", "coupons",
        }
        unknown_keys = set(ticket_data.keys()) - known_keys
        if unknown_keys:
            print(f"  [API discovery] receipt {receipt_id} has extra fields: {sorted(unknown_keys)}")
            for key in sorted(unknown_keys):
                value = ticket_data[key]
                # Truncate long values (e.g. nested HTML blobs)
                repr_val = repr(value)
                if len(repr_val) > 200:
                    repr_val = repr_val[:200] + "…"
                print(f"    {key}: {repr_val}")

        # Also log top-level keys outside the ticket wrapper (if any)
        if "ticket" in data:
            outer_unknown = set(data.keys()) - {"ticket"}
            if outer_unknown:
                print(f"  [API discovery] outer response keys: {sorted(outer_unknown)}")

        # Get HTML content
        html_content = ticket_data.get("htmlPrintedReceipt", "")

        if not html_content:
            print(f"  Kein HTML-Inhalt gefunden für receipt_id: {receipt_id}")
            return None

        # Parse the HTML receipt from the API
        parsed_data = parse_receipt_html(
            html_content, receipt_id, receipt_date, total_amount, store
        )

        if store_details:
            parsed_data["store_details"] = store_details

        if ticket_data.get("languageCode"):
            parsed_data["language_code"] = ticket_data["languageCode"]

        # Save receipt barcodes (e.g. return/loyalty codes printed on the receipt)
        codes = ticket_data.get("codes")
        if codes:
            parsed_data["codes"] = [
                {k: c[k] for k in ("code", "format", "codeType", "label", "position") if k in c}
                for c in codes
            ]

        if ticket_data.get("storeNumber") is not None:
            parsed_data["store_number"] = ticket_data["storeNumber"]

        # Save coupon and return-ticket data from the outer response wrapper
        # (these live outside the ticket object)
        outer = data if "ticket" in data else {}
        if outer.get("coupons"):
            parsed_data["coupons"] = outer["coupons"]
        if outer.get("returnTickets"):
            parsed_data["return_tickets"] = outer["returnTickets"]

        return parsed_data

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print(f"  Nicht autorisiert beim Abrufen von receipt_id: {receipt_id}")
            print(
                "  Bitte stelle sicher, dass du in deinem Browser bei Lidl angemeldet bist."
            )
        else:
            print(f"  HTTP-Fehler beim Abrufen: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  Fehler beim Abrufen: {e}")
        return None
    except Exception as e:
        print(f"  Unerwarteter Fehler: {e}")
        return None
