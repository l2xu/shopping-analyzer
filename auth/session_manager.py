"""Session management and API connection testing."""

import json
from typing import Optional
import requests

from config import LidlConfig
from cli.prompts import select_auth_method
from .file_auth import load_cookies_from_file
from .browser_auth import extract_browser_cookies


def setup_and_test_session() -> Optional[requests.Session]:
    """
    Common setup logic for both initial_setup and update_data.
    Handles browser selection, cookie extraction, and API testing.

    Returns:
        requests.Session: Authenticated session if successful, None otherwise
    """
    # Let user select authentication method
    auth_method = select_auth_method()

    # Extract cookies based on selected method
    if auth_method == "file":
        session = load_cookies_from_file()
    else:
        # auth_method is the browser name ('firefox' or 'chrome')
        session = extract_browser_cookies(auth_method)
    
    if not session:
        return None

    # Test API connection
    if not test_api_connection(session):
        return None

    return session


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
            timeout=LidlConfig.DEFAULT_TIMEOUT,
        )
        response.raise_for_status()

        data = response.json()
        if "items" in data and len(data["items"]) > 0:
            print(
                f"✓ API-Verbindung erfolgreich! {data['totalCount']} Kassenbons gefunden"
            )
            return True
        else:
            print("⚠ API-Antwort enthält keine Kassenbons")
            return False

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("✗ API-Verbindung fehlgeschlagen: Nicht autorisiert (401)")
            print(
                "Bitte stelle sicher, dass du in deinem Browser bei Lidl angemeldet bist."
            )
            print(
                "Öffne www.lidl.de im Browser und melde dich an, bevor du das Programm ausführst."
            )
        else:
            print(f"✗ API-Verbindungsfehler ({e.response.status_code}): {e}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"✗ API-Verbindungsfehler: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"✗ JSON-Decodierungsfehler: {e}")
        return False
