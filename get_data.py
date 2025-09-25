"""
Lidl Receipt Data Updater
=========================

This module provides functions to handle both initial setup and incremental updates
of Lidl receipt data with automatic date sorting.

Usage:
    from lidl_updater import initial_setup, update_data
    
    # For first-time setup or complete refresh
    initial_setup()
    
    # For monthly updates (adds only new data and sorts by date)
    update_data()
"""

import time
import json
import os
import getpass
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Configuration
PURCHASE_HISTORY_URL = "https://www.lidl.de/mre/purchase-history?page=1"
RECEIPTS_JSON_FILE = "lidl_receipts.json"


def get_user_credentials():
    """
    Prompt user for email and password securely.
    
    Returns:
        tuple: (email, password) as strings
    """
    print("\n=== Lidl Login Daten ===")
    email = input("E-Mail Adresse: ").strip()
    
    while not email:
        print("E-Mail Adresse kann nicht leer sein!")
        email = input("E-Mail Adresse: ").strip()
    
    password = getpass.getpass("Passwort: ")
    
    while not password:
        print("Passwort kann nicht leer sein!")
        password = getpass.getpass("Passwort: ")
    
    return email, password


def setup_driver():
    """Initializes and returns a Chrome WebDriver instance."""
    print("Initialisiere Chrome WebDriver...")
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    # Disable images
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    # Disable GPU, extensions, and set minimal resource usage
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # You can add more options if needed
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def accept_cookies(driver):
    """Accept cookies on the website."""
    try:
        time.sleep(3)
        cookie_button = driver.find_element(By.ID, "onetrust-accept-btn-handler")
        cookie_button.click()
        print("Cookies akzeptiert.")
        return True
    except Exception as e:
        print(f"Fehler beim Akzeptieren der Cookies: {e}")
        return False


def login_to_lidl(driver, email, password):
    """
    Log in to Lidl website with provided credentials.
    
    Args:
        driver: WebDriver instance
        email: User's email address
        password: User's password
    
    Returns:
        bool: True if login successful, False otherwise
    """
    LOGIN_URL = "https://www.lidl.de/mre/purchase-history?client_id=GermanyEcommerceClient&country_code=de&language=de-DE&page=1"

    try:
        print("Versuche, Login-Formular auszufüllen...")
        driver.get(LOGIN_URL)
        wait = WebDriverWait(driver, 10)

        # Fill email field
        email_field = wait.until(EC.presence_of_element_located((By.ID, "input-email")))
        email_field.send_keys(email)

        # Fill password field
        password_field = driver.find_element(By.ID, "Password")
        password_field.send_keys(password)
        
        # Click login button
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        print("Login-Daten eingegeben. Klicke auf Login...")
        login_button.click()

        # Wait for login to complete
        wait.until(EC.url_changes(LOGIN_URL))
        print("Login erfolgreich!")
        return True
        
    except Exception as e:
        print(f"Login fehlgeschlagen: {e}")
        return False


def load_existing_receipts():
    """Load existing receipts from JSON file."""
    if not os.path.exists(RECEIPTS_JSON_FILE):
        return set(), []
    
    try:
        with open(RECEIPTS_JSON_FILE, 'r', encoding='utf-8') as file:
            receipts = json.load(file)
        existing_urls = {receipt['url'] for receipt in receipts if 'url' in receipt}
        return existing_urls, receipts
    except (json.JSONDecodeError, KeyError):
        return set(), []


def save_receipts_to_json(receipts):
    """Save all receipts to JSON file."""
    with open(RECEIPTS_JSON_FILE, 'w', encoding='utf-8') as file:
        json.dump(receipts, file, ensure_ascii=False, indent=2)


def add_receipt_to_json(receipt_data):
    """Add a single receipt to the JSON file immediately."""
    _, existing_receipts = load_existing_receipts()
    existing_receipts.append(receipt_data)
    save_receipts_to_json(existing_receipts)
    print(f"Kassenbon gespeichert: {receipt_data['purchase_date']} - {receipt_data['total_price']}")


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


def collect_ticket_links_from_page(driver):
    """Collect all ticket links from the current page."""
    try:
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.purchase-history_ticketsTable__D-i0e")))
        
        ticket_elements = driver.find_elements(
            By.CSS_SELECTOR, 
            "div.purchase-history_ticketsTable__D-i0e a.ticket-row_row__3-1Iv"
        )
        
        return [elem.get_attribute("href") for elem in ticket_elements if elem.get_attribute("href")]
        
    except Exception as e:
        print(f"Fehler beim Sammeln der Links: {e}")
        return []


def has_next_page(driver):
    """Check if there is a next page available."""
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='right-arrow']")
        return "disabled" not in next_button.get_attribute("class")
    except:
        return False


def go_to_next_page(driver):
    """Navigate to the next page."""
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='right-arrow']")
        next_button.click()
        
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.purchase-history_ticketsTable__D-i0e")))
        return True
    except Exception as e:
        print(f"Fehler beim Navigieren zur nächsten Seite: {e}")
        return False


def wait_for_receipt_page(driver, wait):
    """Wait for receipt page to load properly."""
    if "purchase-detail" not in driver.current_url:
        try:
            wait.until(EC.url_contains("purchase-detail"))
        except:
            pass
    
    try:
        wait.until(EC.any_of(
            EC.presence_of_element_located((By.ID, "purchase_tender_information_7")),
            EC.presence_of_element_located((By.ID, "purchase_tender_information_5")),
            EC.presence_of_element_located((By.CSS_SELECTOR, ".article"))
        ))
    except:
        time.sleep(2)
    
    if "purchase-detail" not in driver.current_url:
        print(f"WARNUNG: Nicht auf der Kassenbon-Seite! Umgeleitet zu: {driver.current_url}")
        return False
    return True


def extract_basic_receipt_info(driver):
    """Extract basic receipt information (date, price, savings)."""
    receipt_data = {
        'purchase_date': None,
        'total_price': None,
        'saved_amount': None,
        'lidlplus_saved_amount': None
    }
    
    # Extract purchase date
    try:
        date_element = driver.find_element(By.ID, "purchase_tender_information_7")
        parts = date_element.text.strip().split()
        if len(parts) >= 2:
            receipt_data['purchase_date'] = f"{parts[0]} {parts[1]}"
    except:
        pass

    # Extract total price
    try:
        total_element = driver.find_element(By.ID, "purchase_tender_information_5")
        parts = total_element.text.strip().split()
        if len(parts) >= 2:
            receipt_data['total_price'] = parts[-2]
    except:
        pass

    # Extract saved amount
    try:
        saved_elements = driver.find_elements(By.ID, "purchase_summary_5")
        if saved_elements:
            receipt_data['saved_amount'] = saved_elements[-1].text.strip()
    except:
        pass

    # Extract Lidl Plus savings
    try:
        lidlplus_elements = driver.find_elements(By.ID, "vat_info_line_8")
        for element in lidlplus_elements:
            if "EUR gespart" in element.text:
                parts = element.text.strip().split()
                for part in parts:
                    clean_part = part.replace(',', '.').replace('-', '').replace('+', '').replace('€', '').replace('EUR', '').strip()
                    if clean_part:
                        try:
                            float(clean_part)
                            receipt_data['lidlplus_saved_amount'] = part
                            break
                        except ValueError:
                            continue
                break
    except:
        pass
    
    return receipt_data


def extract_receipt_items(driver):
    """Extract items from receipt."""
    items = []
    try:
        article_elements = driver.find_elements(By.CSS_SELECTOR, ".article")
        items_by_art_id = {}
        
        # Group elements by article ID
        for element in article_elements:
            art_id = element.get_attribute('data-art-id')
            if art_id:
                if art_id not in items_by_art_id:
                    items_by_art_id[art_id] = []
                items_by_art_id[art_id].append(element)
        
        # Process each article
        for art_id, elements in items_by_art_id.items():
            try:
                # Get article name
                name = None
                for element in elements:
                    art_description = element.get_attribute('data-art-description')
                    if art_description:
                        name = art_description
                        break
                
                # Get quantity
                quantity = "1"
                for element in elements:
                    art_quantity = element.get_attribute('data-art-quantity')
                    if art_quantity:
                        quantity = art_quantity
                        break
                
                # Get unit (kg or stk)
                unit = "stk"
                for element in elements:
                    if 'kg' in element.text or 'EUR/kg' in element.text:
                        unit = "kg"
                        break
                
                # Get price (complex logic simplified)
                total_price = None
                for element in elements:
                    unit_price = element.get_attribute('data-unit-price')
                    if unit_price:
                        total_price = unit_price
                        break
                
                # Fallback: look for bold price elements
                if not total_price:
                    for element in elements:
                        element_classes = element.get_attribute('class') or ''
                        element_text = element.text.strip()
                        if ('css_bold' in element_classes and ',' in element_text and 
                            element_text.replace(',', '').replace('.', '').isdigit() and
                            'kg' not in element_text and 'EUR/kg' not in element_text and 'x' not in element_text):
                            try:
                                float(element_text.replace(',', '.'))
                                total_price = element_text
                                break
                            except ValueError:
                                continue
                
                if name and total_price:
                    items.append({
                        'name': name,
                        'price': total_price,
                        'quantity': quantity,
                        'unit': unit
                    })
                    
            except Exception as e:
                print(f"Fehler beim Extrahieren eines Artikels: {e}")
                
    except Exception as e:
        print(f"Artikel nicht gefunden: {e}")
    
    return items


def extract_receipt_data(driver, url):
    """Extract receipt data from a single receipt page."""
    try:
        print(f"Extrahiere Daten von: {url}")
        driver.get(url)
        
        wait = WebDriverWait(driver, 15)
        if not wait_for_receipt_page(driver, wait):
            return None
        
        # Extract basic info and items
        receipt_data = extract_basic_receipt_info(driver)
        receipt_data['url'] = url
        receipt_data['items'] = extract_receipt_items(driver)
        
        return receipt_data
        
    except Exception as e:
        print(f"Fehler beim Extrahieren der Daten von {url}: {e}")
        return None


def setup_driver_and_login():
    """Setup driver and login to Lidl."""
    # Get user credentials
    email, password = get_user_credentials()
    
    driver = setup_driver()
    if not login_to_lidl(driver, email, password):
        print("Login fehlgeschlagen!")
        if driver:
            driver.quit()
        return None
    accept_cookies(driver)
    return driver


def process_receipts_from_pages(driver, existing_urls, stop_on_duplicate=False):
    """Process receipts from multiple pages."""
    processed_count = 0
    skipped_count = 0
    page_count = 0
    
    while True:
        page_count += 1
        print(f"\n--- Seite {page_count} ---")
        
        page_links = collect_ticket_links_from_page(driver)
        print(f"Gefundene Links auf dieser Seite: {len(page_links)}")
        
        for i, link in enumerate(page_links, 1):
            print(f"\nVerarbeite Link {i}/{len(page_links)} auf Seite {page_count}")
            
            if link in existing_urls:
                print(f"Kassenbon bereits vorhanden, überspringe: {link}")
                skipped_count += 1
                if stop_on_duplicate:
                    print("Duplikat gefunden - Update beendet.")
                    return processed_count, skipped_count, page_count, True
                continue
            
            receipt_data = extract_receipt_data(driver, link)
            if receipt_data:
                add_receipt_to_json(receipt_data)
                existing_urls.add(link)
                processed_count += 1
            else:
                print("Fehler beim Extrahieren der Daten")
        
        # Navigate back and check for next page
        current_page_url = f"https://www.lidl.de/mre/purchase-history?page={page_count}"
        driver.get(current_page_url)
        
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.purchase-history_ticketsTable__D-i0e")))
        
        if not has_next_page(driver) or not go_to_next_page(driver):
            print("Keine weiteren Seiten gefunden.")
            break
    
    return processed_count, skipped_count, page_count, False


def initial_setup():
    """Extract all historical receipt data."""
    driver = None
    try:
        print("=== INITIAL SETUP: Extrahiere alle Kassenbons ===")
        
        driver = setup_driver_and_login()
        if not driver:
            return False
        
        driver.get(PURCHASE_HISTORY_URL)
        existing_urls, _ = load_existing_receipts()
        print(f"Bereits vorhandene Kassenbons: {len(_)}")
        
        processed_count, skipped_count, page_count, _ = process_receipts_from_pages(driver, existing_urls)
        
        # Final sort
        total_receipts = sort_receipts_by_date()
        print(f"Alle Kassenbons nach Datum sortiert.")
        
        print(f"\n=== INITIAL SETUP ABGESCHLOSSEN ===")
        print(f"Verarbeitete Seiten: {page_count}")
        print(f"Neue Kassenbons extrahiert: {processed_count}")
        print(f"Übersprungene Kassenbons: {skipped_count}")
        print(f"Gesamte Kassenbons in Datei: {total_receipts}")
        
        return True
        
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")
        return False
    finally:
        if driver:
            driver.quit()
        print("Initial Setup beendet.")


def update_data():
    """Add only new receipts and sort by date at the end."""
    driver = None
    try:
        print("=== UPDATE: Füge neue Kassenbons hinzu ===")
        
        driver = setup_driver_and_login()
        if not driver:
            return False
        
        driver.get(PURCHASE_HISTORY_URL)
        existing_urls, existing_receipts = load_existing_receipts()
        print(f"Bereits vorhandene Kassenbons: {len(existing_receipts)}")
        
        processed_count, _, page_count, found_duplicate = process_receipts_from_pages(
            driver, existing_urls, stop_on_duplicate=True
        )
        
        # Final sort
        if processed_count > 0:
            total_receipts = sort_receipts_by_date()
            print(f"\n{processed_count} neue Kassenbons hinzugefügt und alle nach Datum sortiert.")
        else:
            total_receipts = len(existing_receipts)
            print("\nKeine neuen Kassenbons gefunden.")
        
        print(f"\n=== UPDATE ABGESCHLOSSEN ===")
        print(f"Verarbeitete Seiten: {page_count}")
        print(f"Neue Kassenbons hinzugefügt: {processed_count}")
        print(f"Gesamte Kassenbons in Datei: {total_receipts}")
        
        return True
        
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")
        return False
    finally:
        if driver:
            driver.quit()
        print("Update beendet.")


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
    Can also be run with command line arguments for backwards compatibility:
    - For initial setup: Run this script with 'initial' argument
    - For updates: Run this script with 'update' argument
    - Default: Run interactive menu
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