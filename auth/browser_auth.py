"""Browser cookie extraction for authentication."""

import requests
import browser_cookie3

from config import LidlConfig


def extract_browser_cookies(browser="firefox"):
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
        if browser == "firefox":
            cookies = browser_cookie3.firefox(domain_name="lidl.de")
        elif browser == "chrome":
            cookies = browser_cookie3.chrome(domain_name="lidl.de")
        else:
            raise ValueError(f"Unbekannter Browser: {browser}")

        # Create a requests session and add the cookies
        session = requests.Session()

        for cookie in cookies:
            session.cookies.set_cookie(
                requests.cookies.create_cookie(
                    domain=cookie.domain,
                    name=cookie.name,
                    value=cookie.value,
                    secure=cookie.secure,
                    path=cookie.path,
                )
            )

        print(
            f"Erfolgreich {len(session.cookies)} Cookies aus {browser_name} extrahiert"
        )
        return session

    except Exception as e:
        error_msg = f"Fehler beim Extrahieren der {browser_name} Cookies: {e}"
        print(error_msg)
        print("Bitte stelle sicher, dass:")
        print(f"1. {browser_name} läuft und du bei Lidl angemeldet bist")
        print("2. Die Lidl-Website (www.lidl.de) in {browser_name} geöffnet ist")
        return None
