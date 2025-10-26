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
            f"{LidlConfig.TICKETS_API_URL}?country={LidlConfig.DEFAULT_COUNTRY}&page={page}",
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
        url = LidlConfig.RECEIPT_API_URL.format(receipt_id=receipt_id)
        full_url = f"{url}?country={LidlConfig.DEFAULT_COUNTRY}&languageCode={LidlConfig.DEFAULT_LANGUAGE}"

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
        if isinstance(ticket_data.get("store"), dict):
            store = ticket_data["store"].get("name", "Unknown")
        else:
            store = ticket_data.get("store", "Unknown")

        # Get HTML content
        html_content = ticket_data.get("htmlPrintedReceipt", "")

        if not html_content:
            print(f"  Kein HTML-Inhalt gefunden für receipt_id: {receipt_id}")
            return None

        # Parse the HTML receipt from the API
        parsed_data = parse_receipt_html(
            html_content, receipt_id, receipt_date, total_amount, store
        )

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
