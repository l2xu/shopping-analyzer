"""
Lidl Receipt Data Updater - API Version
=======================================

This module provides functions to extract Lidl receipt data using the official API
with authentication tokens extracted from Google Chrome or Firefox browser.

Requirements:
- User must be logged into Lidl website in Google Chrome or Firefox browser

Usage:
    from lidl_api_updater import initial_setup, update_data
    
    # For first-time setup or complete refresh
    initial_setup()
    
    # For monthly updates (adds only new data and sorts by date)
    update_data()
"""

import re
import time
import json
import os
import sys
from datetime import datetime
from typing import Optional, Dict, List, Any
import requests
from bs4 import BeautifulSoup
import browser_cookie3


# Configuration
class LidlConfig:
    """Configuration constants for Lidl API integration."""

    # File paths
    RECEIPTS_JSON_FILE = "lidl_receipts.json"

    # API endpoints
    LIDL_BASE_URL = "https://www.lidl.de"
    TICKETS_API_URL = f"{LIDL_BASE_URL}/mre/api/v1/tickets"
    RECEIPT_API_URL = f"{LIDL_BASE_URL}/mre/api/v1/tickets/{{receipt_id}}"

    # Request settings
    DEFAULT_TIMEOUT = 15
    REQUEST_DELAY = 0.5
    PAGES_TO_CHECK = 3

    # Browser settings
    SUPPORTED_BROWSERS = {
        'firefox': 'Firefox',
        'chrome': 'Chrome'
    }

    # API settings
    DEFAULT_COUNTRY = "DE"
    DEFAULT_LANGUAGE = "de-DE"
    DEFAULT_PAGE_SIZE = 10

def setup_and_test_session() -> Optional[requests.Session]:
    """
    Common setup logic for both initial_setup and update_data.
    Handles browser selection, cookie extraction, and API testing.

    Returns:
        requests.Session: Authenticated session if successful, None otherwise
    """
    # Let user select browser
    browser = select_browser()

    # Extract cookies from selected browser
    session = extract_browser_cookies(browser)
    if not session:
        return None

    # Test API connection
    if not test_api_connection(session):
        return None

    return session


def extract_browser_cookies(browser='firefox'):
    """
    Extract authentication cookies from browser for Lidl website.

    Args:
        browser: Browser to extract cookies from ('firefox' or 'chrome')

    Returns:
        requests.Session: Session with Lidl authentication cookies
    """
    browser_name = LidlConfig.SUPPORTED_BROWSERS.get(browser, browser)
    print(f"Extrahiere Cookies aus {browser_name} Browser...")

    try:
        # Load cookies from specified browser
        if browser == 'firefox':
            cookies = browser_cookie3.firefox(domain_name='lidl.de')
        elif browser == 'chrome':
            cookies = browser_cookie3.chrome(domain_name='lidl.de')
        else:
            raise ValueError(f"Unbekannter Browser: {browser}")

        # Create a requests session and add the cookies
        session = requests.Session()

        for cookie in cookies:
            session.cookies.set_cookie(requests.cookies.create_cookie(
                domain=cookie.domain,
                name=cookie.name,
                value=cookie.value,
                secure=cookie.secure,
                path=cookie.path
            ))

        print(f"Erfolgreich {len(session.cookies)} Cookies aus {browser_name} extrahiert")
        return session

    except Exception as e:
        error_msg = f"Fehler beim Extrahieren der {browser_name} Cookies: {e}"
        print(error_msg)
        print("Bitte stelle sicher, dass:")
        print(f"1. {browser_name} läuft und du bei Lidl angemeldet bist")
        print("2. Die Lidl-Website (www.lidl.de) in {browser_name} geöffnet ist")
        raise CookieExtractionError(error_msg) from e



def select_browser():
    """
    Let user select browser for cookie extraction.

    Returns:
        str: Browser name ('firefox' or 'chrome')
    """
    print("\n=== Browser-Auswahl ===")
    print("Aus welchem Browser möchten Sie die Anmeldedaten extrahieren?")
    print("1. Firefox")
    print("2. Chrome")

    while True:
        try:
            choice = input("\nWähle einen Browser (1-2): ").strip()

            if choice == "1":
                return "firefox"
            elif choice == "2":
                return "chrome"
            else:
                print("Ungültige Eingabe. Bitte wähle 1 oder 2.")

        except KeyboardInterrupt:
            print("\n\nBrowser-Auswahl abgebrochen.")
            return "firefox"  # Default fallback


def test_api_connection(session: requests.Session) -> bool:
    """
    Test if the API connection with extracted cookies works.

    Args:
        session: requests.Session with authentication cookies

    Returns:
        bool: True if connection works, False otherwise
    """
    print("Teste API-Verbindung...")

    try:
        # Test the tickets API endpoint
        response = session.get(
            f"{LidlConfig.TICKETS_API_URL}?country={LidlConfig.DEFAULT_COUNTRY}&page=1",
            timeout=LidlConfig.DEFAULT_TIMEOUT
        )
        response.raise_for_status()

        data = response.json()
        if 'items' in data and len(data['items']) > 0:
            print(f"✓ API-Verbindung erfolgreich! {data['totalCount']} Kassenbons gefunden")
            return True
        else:
            print("⚠ API-Antwort enthält keine Kassenbons")
            return False

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("✗ API-Verbindung fehlgeschlagen: Nicht autorisiert (401)")
            print("Bitte stelle sicher, dass du in deinem Browser bei Lidl angemeldet bist.")
            print("Öffne www.lidl.de im Browser und melde dich an, bevor du das Programm ausführst.")
        else:
            print(f"✗ API-Verbindungsfehler ({e.response.status_code}): {e}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"✗ API-Verbindungsfehler: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"✗ JSON-Decodierungsfehler: {e}")
        return False


def get_tickets_page(session: requests.Session, page: int = 1) -> Optional[Dict[str, Any]]:
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
            timeout=LidlConfig.DEFAULT_TIMEOUT
        )
        response.raise_for_status()

        data = response.json()

        # Handle different response structures
        if isinstance(data, list):
            # Direct array of tickets
            return {
                'items': data,
                'page': page,
                'size': len(data),
                'totalCount': len(data)
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
            print("Bitte stelle sicher, dass du in deinem Browser bei Lidl angemeldet bist.")
        else:
            print(f"✗ HTTP-Fehler beim Abrufen der Tickets-Seite {page}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"✗ Fehler beim Abrufen der Tickets-Seite {page}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"✗ JSON-Decodierungsfehler für Seite {page}: {e}")
        return None


def get_receipt_details_and_html(session: requests.Session, receipt_id: str) -> Optional[Dict[str, Any]]:
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
        if 'ticket' in data:
            ticket_data = data['ticket']
        else:
            ticket_data = data

        # Extract basic info
        receipt_date = ticket_data['date'][:10].replace('-', '.')
        total_amount = ticket_data['totalAmount']

        # Handle store info (could be nested or direct)
        if isinstance(ticket_data.get('store'), dict):
            store = ticket_data['store'].get('name', 'Unknown')
        else:
            store = ticket_data.get('store', 'Unknown')

        # Get HTML content
        html_content = ticket_data.get('htmlPrintedReceipt', '')

        if not html_content:
            print(f"  Kein HTML-Inhalt gefunden für receipt_id: {receipt_id}")
            return None

        # Parse the HTML (pass the API total amount as well)
        parsed_data = parse_receipt_html(html_content, receipt_id, receipt_date, total_amount, store)

        # Calculate total from items (this is more accurate than API total)
        total_from_items = 0.0
        for item in parsed_data.get('items', []):
            try:
                item_total = float(item.get('total_price', '0').replace(',', '.'))
                total_from_items += item_total
            except (ValueError, AttributeError):
                pass

        if total_from_items > 0:
            parsed_data['total_price'] = f"{total_from_items:.2f}".replace('.', ',')

        return parsed_data

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print(f"  Nicht autorisiert beim Abrufen von receipt_id: {receipt_id}")
            print("  Bitte stelle sicher, dass du in deinem Browser bei Lidl angemeldet bist.")
        else:
            print(f"  HTTP-Fehler beim Abrufen: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  Fehler beim Abrufen: {e}")
        return None
    except Exception as e:
        print(f"  Unerwarteter Fehler: {e}")
        return None


def extract_savings_info(soup, receipt_data):
    """Extract savings information from the receipt HTML."""
    # Extract saved amount (only "Preisvorteil" and "Rabatt" lines, excluding "Lidl Plus Rabatt")
    try:
        total_regular_savings = 0.0

        # Get the purchase list text and search for discount lines
        purchase_list = soup.find('span', class_='purchase_list')
        if purchase_list:
            purchase_text = purchase_list.get_text()

            # Find all discount lines and extract the amounts
            lines = purchase_text.split('\n')
            for line in lines:
                # Include "Preisvorteil" lines
                if "Preisvorteil" in line and "Gesamter" not in line:
                    amount_match = re.search(r'-(\d+,\d+)', line)
                    if amount_match:
                        amount_str = amount_match.group(1)
                        amount_float = float(amount_str.replace(',', '.'))
                        total_regular_savings += amount_float
                # Include "Rabatt" lines but exclude "Lidl Plus Rabatt"
                elif "Rabatt" in line and "Lidl Plus Rabatt" not in line:
                    amount_match = re.search(r'-(\d+,\d+)', line)
                    if amount_match:
                        amount_str = amount_match.group(1)
                        amount_float = float(amount_str.replace(',', '.'))
                        total_regular_savings += amount_float

        # Set the saved_amount if we found any regular savings
        if total_regular_savings > 0:
            receipt_data['saved_amount'] = f"{total_regular_savings:.2f}".replace('.', ',')
    except Exception as e:
        print(f"Fehler beim Extrahieren der regulären Ersparnisse: {e}")

    # Extract Lidl Plus savings
    try:
        # Look for the "Mit Lidl Plus" box that shows "X,XX EUR gespart"
        vat_info = soup.find('span', class_='vat_info')
        if vat_info:
            vat_text = vat_info.get_text()
            gespart_match = re.search(r'(\d+,\d+)\s+EUR gespart', vat_text)
            if gespart_match:
                receipt_data['lidlplus_saved_amount'] = gespart_match.group(1)
    except Exception as e:
        print(f"Fehler beim Extrahieren der Lidl Plus Ersparnisse: {e}")


def load_existing_receipts() -> tuple[set[str], list[Dict[str, Any]]]:
    """Load existing receipts from JSON file."""
    if not os.path.exists(LidlConfig.RECEIPTS_JSON_FILE):
        return set(), []

    try:
        with open(LidlConfig.RECEIPTS_JSON_FILE, 'r', encoding='utf-8') as file:
            receipts = json.load(file)
        # Handle both old format (with 'url') and new format (with 'id')
        existing_ids = set()
        for receipt in receipts:
            if 'id' in receipt:
                existing_ids.add(receipt['id'])
            elif 'url' in receipt:
                # For backward compatibility with old format
                existing_ids.add(receipt['url'])
        return existing_ids, receipts
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Warning: Error loading existing receipts: {e}")
        return set(), []


def save_receipts_to_json(receipts):
    """Save all receipts to JSON file."""
    with open(LidlConfig.RECEIPTS_JSON_FILE, 'w', encoding='utf-8') as file:
        json.dump(receipts, file, ensure_ascii=False, indent=2)


def add_receipt_to_json(receipt_data):
    """Add or update a single receipt in the JSON file immediately."""
    existing_ids, existing_receipts = load_existing_receipts()

    # Check if receipt already exists and update it
    receipt_updated = False
    for i, existing_receipt in enumerate(existing_receipts):
        # Check both 'id' and 'url' fields for compatibility
        existing_key = existing_receipt.get('id') or existing_receipt.get('url', '')
        new_key = receipt_data.get('id') or receipt_data.get('url', '')

        if existing_key == new_key:
            existing_receipts[i] = receipt_data
            receipt_updated = True
            break

    # If not found, add as new receipt
    if not receipt_updated:
        existing_receipts.append(receipt_data)

    save_receipts_to_json(existing_receipts)

    action = "aktualisiert" if receipt_updated else "hinzugefügt"
    print(f"Kassenbon {action}: {receipt_data['purchase_date']} - {receipt_data['total_price']}")


def sort_receipts_by_date():
    """Sort all receipts in the JSON file by date (newest first)."""
    _, receipts = load_existing_receipts()
    
    def get_date_key(receipt):
        date_str = receipt.get('purchase_date')
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


def parse_receipt_html(html_content, receipt_id, receipt_date, total_amount, store):
    """
    Parse receipt HTML content to extract items and other data.

    Args:
        html_content: HTML content of the receipt (from ticket.htmlPrintedReceipt)
        receipt_id: Receipt ID
        receipt_date: Receipt date
        total_amount: Total amount from API (might be 0)
        store: Store name

    Returns:
        dict: Parsed receipt data
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract basic receipt info
    receipt_data = {
        'id': receipt_id,
        'purchase_date': receipt_date,
        'total_price': '0',  # Will be calculated from items later
        'saved_amount': None,
        'lidlplus_saved_amount': None,
        'store': store,
        'items': []
    }

    # Extract savings information first
    extract_savings_info(soup, receipt_data)

    # Find all article spans (they contain data-art-* attributes)
    article_spans = soup.find_all('span', class_='article')

    if not article_spans:
        print(f"Keine Artikel-Spans gefunden für {receipt_id}")
        return receipt_data

    # Group spans by article ID
    items_by_id = {}
    for span in article_spans:
        art_id = span.get('data-art-id')
        if art_id:
            if art_id not in items_by_id:
                items_by_id[art_id] = []
            items_by_id[art_id].append(span)

    # Process each item group
    for art_id, spans in items_by_id.items():
        try:
            # Get the first span (should contain all the data attributes)
            main_span = spans[0]

            # Extract item details from data attributes
            art_description = main_span.get('data-art-description', '')
            art_quantity = main_span.get('data-art-quantity', '1')
            unit_price = main_span.get('data-unit-price', '')
            tax_type = main_span.get('data-tax-type', 'A')

            if not art_description or not unit_price:
                continue

            # Extract total price from span text
            total_price_text = unit_price  # Default to unit price
            for span in spans:
                span_text = span.get_text().strip()
                # Look for price pattern (digits,digits)
                if re.match(r'^\d+,\d+$', span_text):
                    # Check if this is likely the total price (not unit price)
                    try:
                        price_val = float(span_text.replace(',', '.'))
                        unit_val = float(unit_price.replace(',', '.'))
                        qty_val = float(art_quantity.replace(',', '.'))

                        # If this matches the expected total, use it
                        expected_total = unit_val * qty_val
                        if abs(price_val - expected_total) < 0.01:
                            total_price_text = span_text
                            break
                    except (ValueError, AttributeError):
                        pass

            # Determine unit (kg or stk) from text content
            unit = 'kg' if any('kg' in span.get_text() or 'EUR/kg' in span.get_text() for span in spans) else 'stk'

            # Convert values for calculation
            try:
                quantity = float(art_quantity.replace(',', '.'))
            except (ValueError, AttributeError):
                quantity = 1.0

            try:
                price = float(unit_price.replace(',', '.'))
            except (ValueError, AttributeError):
                price = 0.0

            receipt_data['items'].append({
                'name': art_description,
                'price': unit_price,
                'quantity': art_quantity,
                'unit': unit,
                'total_price': total_price_text
            })

        except Exception as e:
            print(f"Fehler beim Parsen eines Artikels: {e}")
            continue

    return receipt_data


def collect_all_receipt_ids(session):
    """
    Collect all receipt IDs from all pages efficiently.

    Args:
        session: requests.Session with authentication

    Returns:
        list: List of all receipt IDs
    """
    all_receipt_ids = []
    page = 1

    print("Sammle alle Kassenbon-IDs...")

    while True:
        # Get tickets for current page
        tickets_data = get_tickets_page(session, page)

        if not tickets_data or 'items' not in tickets_data:
                        break
                
        tickets = tickets_data['items']

        if not tickets:
            break

        # Extract receipt IDs from tickets (only those with HTML documents)
        for ticket in tickets:
            if isinstance(ticket, dict):
                if 'ticket' in ticket:
                    ticket_data = ticket['ticket']
                    receipt_id = ticket_data['id']
                    has_html = ticket_data.get('hasHtmlDocument', False)
                else:
                    receipt_id = ticket.get('id', '')
                    has_html = ticket.get('hasHtmlDocument', False)

                if receipt_id and has_html:
                    all_receipt_ids.append(receipt_id)

        page += 1

        # Check if we have more pages
        total_count = tickets_data.get('totalCount', 0)
        page_size = tickets_data.get('size', 10)
        total_pages = (total_count + page_size - 1) // page_size

        if page > total_pages:
            break

    print(f"Gefunden: {len(all_receipt_ids)} Kassenbon-IDs")
    return all_receipt_ids


def process_all_tickets(session):
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

        if receipt_data and receipt_data['items']:
            add_receipt_to_json(receipt_data)
            processed_count += 1
            print(f"✓ Verarbeitet: {len(receipt_data['items'])} Artikel")
        else:
            print("⚠ Fehler beim Verarbeiten")
            skipped_count += 1

        # Add pause between requests to be respectful
        time.sleep(LidlConfig.REQUEST_DELAY)

    return processed_count, skipped_count, len(all_receipt_ids) // 10 + 1


def initial_setup():
    """
    Extract all historical receipt data using the API.

    Returns:
        bool: True if successful, False otherwise
    """
    print("=== INITIAL SETUP: Extrahiere alle Kassenbons ===")

    # Setup session with browser selection, cookie extraction, and API testing
    session = setup_and_test_session()
    if not session:
        return False

    # Process all tickets
    processed_count, skipped_count, total_pages = process_all_tickets(session)

    # Final sort
    total_receipts = sort_receipts_by_date()
    print(f"Alle Kassenbons nach Datum sortiert.")

    print("\n=== INITIAL SETUP ABGESCHLOSSEN ===")
    print(f"Verarbeitete Seiten: {total_pages}")
    print(f"Neue Kassenbons extrahiert: {processed_count}")
    print(f"Übersprungene Kassenbons: {skipped_count}")
    print(f"Gesamte Kassenbons in Datei: {total_receipts}")

    return True


def update_data():
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

        if not tickets_data or 'items' not in tickets_data:
            break

        tickets = tickets_data['items']
        if not tickets:
            break

        # Extract receipt IDs from tickets (only those with HTML documents)
        for ticket in tickets:
            if isinstance(ticket, dict):
                if 'ticket' in ticket:
                    ticket_data = ticket['ticket']
                    receipt_id = ticket_data['id']
                    has_html = ticket_data.get('hasHtmlDocument', False)
                else:
                    receipt_id = ticket.get('id', '')
                    has_html = ticket.get('hasHtmlDocument', False)

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

        if receipt_data and receipt_data['items']:
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


def main():
    """
    Main function that provides a simple menu for choosing between
    initial setup and update modes.
    """
    print("=== Willkommen, welche Kassenbons möchtest du hinzufügen? ===")
    print("1. Initial Setup (Alle Kassenbons)")
    print("2. Update (Nur neue Kassenbons hinzufügen)")
    print("3. Beenden")

    while True:
        try:
            choice = input("\nWähle eine Option (1-3): ").strip()
            
            if choice == "1":
                print("\nStarte Initial Setup...")
                success = initial_setup()
                if success:
                    print("✓ Initial Setup erfolgreich abgeschlossen!")
                else:
                    print("✗ Initial Setup fehlgeschlagen!")
                break
                
            elif choice == "2":
                print("\nStarte Update...")
                success = update_data()
                if success:
                    print("✓ Update erfolgreich abgeschlossen!")
                else:
                    print("✗ Update fehlgeschlagen!")
                break
                
            elif choice == "3":
                print("Auf Wiedersehen!")
                break
                
            else:
                print("Ungültige Eingabe. Bitte wähle 1, 2 oder 3.")
                
        except KeyboardInterrupt:
            print("\n\nProgramm unterbrochen.")
            break
        except Exception as e:
            print(f"Ein Fehler ist aufgetreten: {e}")
            break


if __name__ == "__main__":
    """
    Entry point for the script. Provides a menu interface for users.
    """
    import sys
    
    # Check for command line arguments for backwards compatibility
    if len(sys.argv) > 1:
        if sys.argv[1] == 'initial':
            initial_setup()
        elif sys.argv[1] == 'update':
            update_data()
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Usage: python get_data.py [initial|update]")
    else:
        # Run interactive menu
        main()
