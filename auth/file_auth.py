"""File-based cookie loading for authentication."""

import os
import json
from typing import Optional
import requests

from config import LidlConfig


def load_cookies_from_file(file_path: Optional[str] = None) -> Optional[requests.Session]:
    """
    Load authentication cookies from a JSON file (e.g., exported from EditThisCookie).
    
    The JSON file should contain an array of cookie objects with fields like:
    - domain, name, value, path, secure, httpOnly, etc.
    
    Args:
        file_path: Path to the cookie JSON file. If None, uses default from config.
    
    Returns:
        requests.Session: Session with loaded cookies, or None if error
    """
    if file_path is None:
        file_path = LidlConfig.COOKIES_JSON_FILE
    
    print(f"Lade Cookies aus Datei: {file_path}...")
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"✗ Cookie-Datei nicht gefunden: {file_path}")
            print(f"\nBitte erstelle eine Datei '{file_path}' mit deinen Cookies.")
            print("Du kannst Cookies exportieren mit Browser-Erweiterungen wie:")
            print("  - EditThisCookie (exportiere als JSON)")
            print("  - Cookie-Editor")
            print("\nDie Datei sollte ein JSON-Array von Cookie-Objekten enthalten.")
            return None
        
        # Load the JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            cookies_data = json.load(f)
        
        # Handle both array and object formats
        if isinstance(cookies_data, dict) and 'cookies' in cookies_data:
            cookies_list = cookies_data['cookies']
        elif isinstance(cookies_data, list):
            cookies_list = cookies_data
        else:
            print("✗ Ungültiges Cookie-Dateiformat. Erwarte ein JSON-Array oder Objekt mit 'cookies'-Feld.")
            return None
        
        # Create a requests session
        session = requests.Session()
        
        # Add cookies to session
        cookie_count = 0
        for cookie_data in cookies_list:
            # Skip cookies not for lidl.de domain
            domain = cookie_data.get('domain', '')
            if 'lidl.de' not in domain:
                continue
            
            # Create cookie with available fields
            session.cookies.set_cookie(
                requests.cookies.create_cookie(
                    domain=cookie_data.get('domain', ''),
                    name=cookie_data.get('name', ''),
                    value=cookie_data.get('value', ''),
                    path=cookie_data.get('path', '/'),
                    secure=cookie_data.get('secure', False),
                    expires=cookie_data.get('expirationDate', None),
                )
            )
            cookie_count += 1
        
        if cookie_count == 0:
            print("✗ Keine Cookies für lidl.de in der Datei gefunden.")
            return None
        
        print(f"✓ Erfolgreich {cookie_count} Cookies aus Datei geladen")
        return session
    
    except json.JSONDecodeError as e:
        print(f"✗ Fehler beim Parsen der Cookie-Datei: {e}")
        print("Bitte stelle sicher, dass die Datei gültiges JSON enthält.")
        return None
    except Exception as e:
        print(f"✗ Fehler beim Laden der Cookie-Datei: {e}")
        return None
