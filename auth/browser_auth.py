"""Browser cookie extraction for authentication."""

import requests
import browser_cookie3

from config import LidlConfig


def extract_browser_cookies(browser="firefox"):
    """
    Extract authentication cookies from browser for Lidl website.

    Args:
        browser: Browser to extract cookies from ('firefox', 'chrome', or 'chromium')

    Returns:
        requests.Session: Session with Lidl authentication cookies
    """
    browser_name = LidlConfig.SUPPORTED_BROWSERS.get(browser, browser)
    cookie_domain = LidlConfig.get_cookie_domain()

    print(f"Extrahiere Cookies für {cookie_domain} aus {browser_name} Browser...")

    try:
        # Load cookies from specified browser
        if browser == "firefox":
            cookies = browser_cookie3.firefox(domain_name=cookie_domain)
        elif browser == "chrome":
            cookies = browser_cookie3.chrome(domain_name=cookie_domain)
        elif browser == "chromium":
            cookies = browser_cookie3.chromium(domain_name=cookie_domain)
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
        print(f"2. Die Lidl-Website (www.{cookie_domain}) in {browser_name} geöffnet ist")
        return None
