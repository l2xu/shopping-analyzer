"""
Lidl Receipt Data Updater
=========================

This module provides functions to handle both initial setup and incremental updates
of Lidl receipt data with automatic date sor        wait = WebDriverWait(driver, 25)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.purchase-history_ticketsTable__D-i0e")))
        
        # Give page additional time to stabilize
        time.sleep(3)
        
        ticket_elements = driver.find_elements(
            By.CSS_SELECTOR, 
            "div.purchase-history_ticketsTable__D-i0e a.ticket-row_row__3-1Iv"
        )Usage:
    from lidl_updater import initial_setup, update_data
    
    # For first-time setup or complete refresh
    initial_setup()
    
    # For monthly updates (adds only new data and sorts by date)
    update_data()
"""

import re
import time
import json
import os
import getpass
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- Germany (DE) Configuration ---
DE_CONFIG = {
    "country_code": "de",
    "language": "de-DE",
    "url": "https://www.lidl.de/mre/purchase-history?page=1",
    "login_url": "https://www.lidl.de/mre/purchase-history?client_id=GermanyEcommerceClient&country_code=de&language=de-DE&page=1",
    "json_file": "lidl_receipts.json",
    "lang_prompts": {
        "credentials_header": "\n=== Lidl Login Daten ===",
        "email_prompt": "E-Mail Adresse: ",
        "email_empty": "E-Mail Adresse kann nicht leer sein!",
        "password_prompt": "Passwort: ",
        "password_empty": "Passwort kann nicht leer sein!",
        "login_attempt": "Versuche, Login-Formular auszufüllen...",
        "login_data_entered": "Login-Daten eingegeben. Klicke auf Login...",
        "mfa_detected": "MFA-Schritt erkannt. Warte auf die Verifizierungs-Auswahl...",
        "mfa_prompt": "Bitte wählen Sie die Verifizierungsart (1 -> E-Mail, 2 -> SMS): ",
        "mfa_email_sending": "Klicke auf 'E-Mail senden'...",
        "mfa_email_fail": "Fehler: Konnte den 'E-Mail senden'-Button nicht finden oder klicken: ",
        "mfa_email_sent": "Eine E-Mail mit einem 6-stelligen Code wurde versendet.",
        "mfa_code_prompt": "Bitte den 6-stelligen Code aus der E-Mail eingeben und Enter drücken: ",
        "mfa_code_confirm": "Bestätige den Code...",
        "mfa_code_fail": "Fehler bei der Eingabe des MFA-Codes: ",
        "mfa_sms_prompt": "Bitte den 6-Stelligen Code aus der SMS eingeben und Enter drücken: ",
        "mfa_sms_fail": "Fehler: Konnte das 'verificationCode'-Feld nicht finden oder den Code eingeben: ",
        "wait_for_history": "Warte auf die Weiterleitung zur Einkaufs-Historie...",
        "login_success": "Login erfolgreich!",
        "login_fail": "Login fehlgeschlagen. Möglicherweise falsche Anmeldedaten oder eine unerwartete Seitenänderung: ",
        "total_price_keyword": "zu zahlen",
        "discount_keyword": "Rabatt",
        "lidl_plus_discount_keyword": "Lidl Plus Rabatt",
        "price_advantage_keyword": "Preisvorteil",
        "total_advantage_keyword": "Gesamter",
        "saved_keyword": "gespart",
        "saved_unit": "EUR"
    }
}

# --- Netherlands (NL) Configuration ---
NL_CONFIG = {
    "country_code": "nl",
    "language": "nl-NL",
    "url": "https://www.lidl.nl/mre/purchase-history?page=1",
    "login_url": "https://www.lidl.nl/mre/purchase-history?client_id=NetherlandsEcommerceClient&country_code=nl&language=nl-NL&page=1",
    "json_file": "lidl_receipts_nl.json",
    "lang_prompts": {
        "credentials_header": "\n=== Lidl Inloggegevens ===",
        "email_prompt": "E-mailadres: ",
        "email_empty": "E-mailadres mag niet leeg zijn!",
        "password_prompt": "Wachtwoord: ",
        "password_empty": "Wachtwoord mag niet leeg zijn!",
        "login_attempt": "Inlogformulier invullen...",
        "login_data_entered": "Inloggegevens ingevoerd. Klikken op Login...",
        "mfa_detected": "MFA-stap gedetecteerd. Wachten op verificatiekeuze...",
        "mfa_prompt": "Kies de verificatiemethode (1 -> E-mail, 2 -> SMS): ",
        "mfa_email_sending": "Klikken op 'E-mail verzenden'...",
        "mfa_email_fail": "Fout: Kon de 'E-mail verzenden'-knop niet vinden of aanklikken: ",
        "mfa_email_sent": "Een e-mail met een 6-cijferige code is verzonden.",
        "mfa_code_prompt": "Voer de 6-cijferige code uit de e-mail in en druk op Enter: ",
        "mfa_code_confirm": "Code bevestigen...",
        "mfa_code_fail": "Fout bij het invoeren van de MFA-code: ",
        "mfa_sms_prompt": "Voer de 6-cijferige code uit de SMS in en druk op Enter: ",
        "mfa_sms_fail": "Fout: Kon het 'verificationCode'-veld niet vinden of de code invoeren: ",
        "wait_for_history": "Wachten op doorverwijzing naar aankoopgeschiedenis...",
        "login_success": "Login succesvol!",
        "login_fail": "Login mislukt. Mogelijk onjuiste inloggegevens of een onverwachte paginawijziging: ",
        "total_price_keyword": "Totaal",
        "discount_keyword": "KORTING",
        "lidl_plus_discount_keyword": "Lidl Plus korting",
        "price_advantage_keyword": "In prijs verlaagd", # Using one of the Dutch variants
        "total_advantage_keyword": "", # Not present in Dutch version
        "saved_keyword": "bespaard",
        "saved_unit": "EUR"
    }
}


def get_user_credentials(prompts):
    """Prompt user for email and password securely."""
    print(prompts["credentials_header"])
    email = input(prompts["email_prompt"]).strip()
    while not email:
        print(prompts["email_empty"])
        email = input(prompts["email_prompt"]).strip()
    password = getpass.getpass(prompts["password_prompt"])
    while not password:
        print(prompts["password_empty"])
        password = getpass.getpass(prompts["password_prompt"])
    return email, password


def setup_driver():
    """Initializes and returns a Chrome WebDriver instance."""
    print("Initialising Chrome WebDriver...")
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def accept_cookies(driver):
    """Accept cookies on the website."""
    try:
        time.sleep(5) # Wait for banner to appear
        cookie_button = driver.find_element(By.ID, "onetrust-accept-btn-handler")
        cookie_button.click()
        print("Cookies accepted.")
        return True
    except Exception:
        print("Could not find or click cookie banner, continuing...")
        return False


def login_to_lidl(driver, email, password, config):
    """Log in to Lidl website with provided credentials."""
    prompts = config["lang_prompts"]
    try:
        print(prompts["login_attempt"])
        driver.get(config["login_url"])
        wait = WebDriverWait(driver, 20)
        email_field = wait.until(EC.presence_of_element_located((By.ID, "input-email")))
        email_field.send_keys(email)
        password_field = driver.find_element(By.ID, "Password")
        password_field.send_keys(password)
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        print(prompts["login_data_entered"])
        login_button.click()
        time.sleep(5)

        if "accounts.lidl.com/account/login/mfa" in driver.current_url:
            print(prompts["mfa_detected"])
            verification = int(input(prompts["mfa_prompt"]))
            if verification == 1:
                try:
                    email_mfa_button = wait.until(EC.element_to_be_clickable((By.ID, "sso_2FAvalidation_emailbutton")))
                    print(prompts["mfa_email_sending"])
                    email_mfa_button.click()
                    code_field = wait.until(EC.presence_of_element_located((By.ID, "verificationCode")))
                    print(prompts["mfa_email_sent"])
                    mfa_code = input(prompts["mfa_code_prompt"]).strip()
                    code_field.send_keys(mfa_code)
                    confirm_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    print(prompts["mfa_code_confirm"])
                    confirm_button.click()
                except Exception as e:
                    print(f"{prompts['mfa_email_fail']} {e}")
                    return False
            elif verification == 2:
                try:
                    sms_code_field = wait.until(EC.element_to_be_clickable((By.ID, "verificationCode")))
                    verification_code = input(prompts["mfa_sms_prompt"])
                    sms_code_field.send_keys(verification_code)
                    confirm_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    print(prompts["mfa_code_confirm"])
                    confirm_button.click()
                except Exception as e:
                    print(f"{prompts['mfa_sms_fail']} {e}")
                    return False

        print(prompts["wait_for_history"])
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.purchase-history_ticketsTable__D-i0e")))
        print(prompts["login_success"])
        return True
    except Exception as e:
        print(f"{prompts['login_fail']} {e}")
        return False


def load_existing_receipts(json_file):
    """Load existing receipts from a specific JSON file."""
    if not os.path.exists(json_file):
        return set(), []
    try:
        with open(json_file, 'r', encoding='utf-8') as file:
            receipts = json.load(file)
        existing_urls = {receipt['url'] for receipt in receipts if 'url' in receipt}
        return existing_urls, receipts
    except (json.JSONDecodeError, KeyError):
        return set(), []


def save_receipts_to_json(receipts, json_file):
    """Save all receipts to a specific JSON file."""
    with open(json_file, 'w', encoding='utf-8') as file:
        json.dump(receipts, file, ensure_ascii=False, indent=2)


def add_receipt_to_json(receipt_data, json_file):
    """Add a single receipt to the specific JSON file."""
    _, existing_receipts = load_existing_receipts(json_file)
    existing_receipts.append(receipt_data)
    save_receipts_to_json(existing_receipts, json_file)
    print(f"Receipt saved: {receipt_data['purchase_date']} - {receipt_data['total_price']}")


def sort_receipts_by_date(json_file):
    """Sort all receipts in the specific JSON file by date."""
    _, receipts = load_existing_receipts(json_file)
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
    save_receipts_to_json(sorted_receipts, json_file)
    return len(sorted_receipts)


def collect_ticket_links_from_page(driver):
    """Collect all ticket links from the current page."""
    try:
        wait = WebDriverWait(driver, 25)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.purchase-history_ticketsTable__D-i0e")))
        ticket_elements = driver.find_elements(By.CSS_SELECTOR, "div.purchase-history_ticketsTable__D-i0e a.ticket-row_row__3-1Iv")
        return [elem.get_attribute("href") for elem in ticket_elements if elem.get_attribute("href")]
    except Exception as e:
        print(f"Error collecting links: {e}")
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
        time.sleep(2)
        wait = WebDriverWait(driver, 25)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.purchase-history_ticketsTable__D-i0e")))
        return True
    except Exception as e:
        print(f"Error navigating to next page: {e}")
        return False


def wait_for_receipt_page_de(driver, wait):
    """Wait for German receipt page to load properly."""
    try:
        wait.until(EC.any_of(
            EC.presence_of_element_located((By.ID, "purchase_tender_information_7")),
            EC.presence_of_element_located((By.ID, "purchase_tender_information_5")),
            EC.presence_of_element_located((By.CSS_SELECTOR, ".article"))
        ))
    except:
        time.sleep(2)
    if "purchase-detail" not in driver.current_url:
        print(f"WARNING: Not on receipt page! Redirected to: {driver.current_url}")
        return False
    return True

def wait_for_receipt_page_nl(driver, wait):
    """Wait for Dutch receipt page to load properly."""
    try:
        wait.until(EC.any_of(
             EC.presence_of_element_located((By.ID, "purchase_header_0")),
             EC.presence_of_element_located((By.CSS_SELECTOR, ".article"))
        ))
    except:
        time.sleep(2)
    if "purchase-detail" not in driver.current_url:
        print(f"WARNING: Not on receipt page! Redirected to: {driver.current_url}")
        return False
    return True


def extract_basic_receipt_info_de(driver, url):
    """Extract basic receipt information for Germany."""
    receipt_data = {'purchase_date': None, 'total_price': None, 'saved_amount': None, 'lidlplus_saved_amount': None}
    prompts = DE_CONFIG["lang_prompts"]
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        if 't' in query_params:
            t_param = query_params['t'][0]
            date_match = re.search(r'(20\d{6})', t_param)
            if date_match:
                date_str = date_match.group(1)
                receipt_data['purchase_date'] = f"{date_str[6:8]}.{date_str[4:6]}.{date_str[:4]}"
    except:
        pass

    try:
        purchase_summary_elements = driver.find_elements(By.CSS_SELECTOR, "[id^='purchase_summary_']")
        for element in purchase_summary_elements:
            if prompts["total_price_keyword"] in element.text.strip():
                parent = element.find_element(By.XPATH, "..")
                amount_spans = parent.find_elements(By.CSS_SELECTOR, "span.css_bold")
                for span in amount_spans:
                    if re.match(r'^\d+,\d+$', span.text.strip()):
                        receipt_data['total_price'] = span.text.strip()
                        break
                if receipt_data['total_price']:
                    break
    except:
        pass

    try:
        total_regular_savings = 0.0
        purchase_list = driver.find_element(By.CLASS_NAME, "purchase_list")
        lines = purchase_list.text.split('\n')
        for line in lines:
            if (prompts["price_advantage_keyword"] in line and prompts["total_advantage_keyword"] not in line) or \
               (prompts["discount_keyword"] in line and prompts["lidl_plus_discount_keyword"] not in line):
                amount_match = re.search(r'-(\d+,\d+)', line)
                if amount_match:
                    total_regular_savings += float(amount_match.group(1).replace(',', '.'))
        if total_regular_savings > 0:
            receipt_data['saved_amount'] = f"{total_regular_savings:.2f}".replace('.', ',')
    except:
        pass

    try:
        page_text = driver.find_element(By.TAG_NAME, "body").text
        saved_match_text = fr'(\d+,\d+)\s+{prompts["saved_unit"]}\s+{prompts["saved_keyword"]}'
        gespart_match = re.search(saved_match_text, page_text)
        if gespart_match:
            receipt_data['lidlplus_saved_amount'] = gespart_match.group(1)
    except:
        pass
    
    return receipt_data


def extract_basic_receipt_info_nl(driver, url):
    """Extract basic receipt information for Netherlands."""
    receipt_data = {'purchase_date': None, 'total_price': None, 'saved_amount': None, 'lidlplus_saved_amount': None}
    prompts = NL_CONFIG["lang_prompts"]
    try:
        date_match = re.search(r'(20\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01]))', urlparse(url).query)
        if date_match:
            date_str = date_match.group(1)
            receipt_data['purchase_date'] = f"{date_str[6:8]}.{date_str[4:6]}.{date_str[:4]}"
    except:
        pass

    try:
        purchase_summary_elements = driver.find_elements(By.CSS_SELECTOR, "[id^='purchase_summary_']")
        for element in purchase_summary_elements:
            if prompts["total_price_keyword"] in element.text.strip():
                parent = element.find_element(By.XPATH, "..")
                amount_spans = parent.find_elements(By.CSS_SELECTOR, "span.css_big.css_bold, span.css_bold")
                for span in amount_spans:
                    if re.match(r'^\d+,\d+$', span.text.strip()):
                        receipt_data['total_price'] = span.text.strip()
                        break
                if receipt_data['total_price']:
                    break
    except:
        pass
        
    try:
        total_regular_savings = 0.0
        purchase_list = driver.find_element(By.CLASS_NAME, "purchase_list")
        lines = purchase_list.text.split('\n')
        for line in lines:
            if ("In prijs verlaagd" in line or "Actieprijs" in line or "2 voor actie" in line) or \
               (prompts["discount_keyword"] in line and prompts["lidl_plus_discount_keyword"] not in line):
                amount_match = re.search(r'-(\d+,\d+)', line)
                if amount_match:
                    total_regular_savings += float(amount_match.group(1).replace(',', '.'))
        if total_regular_savings > 0:
            receipt_data['saved_amount'] = f"{total_regular_savings:.2f}".replace('.', ',')
    except:
        pass
        
    try:
        total_lidl_plus_savings = 0.0
        purchase_list = driver.find_element(By.CLASS_NAME, "purchase_list")
        lines = purchase_list.text.split('\n')
        for line in lines:
            if prompts["lidl_plus_discount_keyword"] in line or "kassabon korting" in line:
                amount_match = re.search(r'-(\d+,\d+)', line)
                if amount_match:
                    total_lidl_plus_savings += float(amount_match.group(1).replace(',', '.'))
        if total_lidl_plus_savings > 0:
            receipt_data['lidlplus_saved_amount'] = f"{total_lidl_plus_savings:.2f}".replace('.', ',')
    except:
        pass

    return receipt_data

def extract_receipt_items(driver):
    """Extract items from receipt (generic for both countries)."""
    items = []
    try:
        article_elements = driver.find_elements(By.CSS_SELECTOR, ".article")
        items_by_art_id = {}
        for element in article_elements:
            art_id = element.get_attribute('data-art-id')
            if art_id:
                if art_id not in items_by_art_id:
                    items_by_art_id[art_id] = []
                items_by_art_id[art_id].append(element)
        
        for art_id, elements in items_by_art_id.items():
            try:
                name = quantity = total_price = None
                unit = "stk"
                for element in elements:
                    if not name and element.get_attribute('data-art-description'):
                        name = element.get_attribute('data-art-description')
                    if not quantity and element.get_attribute('data-art-quantity'):
                        quantity = element.get_attribute('data-art-quantity')
                    if not total_price and element.get_attribute('data-unit-price'):
                        total_price = element.get_attribute('data-unit-price')
                    if 'kg' in element.text or 'kg x' in element.text:
                        unit = "kg"
                
                if not total_price:
                    for element in elements:
                        if 'css_bold' in (element.get_attribute('class') or '') and ',' in element.text.strip():
                            try:
                                if 'kg' not in element.text and 'EUR/kg' not in element.text and 'x' not in element.text:
                                    float(element.text.strip().replace(',', '.'))
                                    total_price = element.text.strip()
                                    break
                            except ValueError:
                                continue
                
                if name and total_price:
                    items.append({'name': name, 'price': total_price, 'quantity': quantity or '1', 'unit': unit})
            except Exception as e:
                print(f"Error extracting an item: {e}")
    except Exception as e:
        print(f"Articles not found: {e}")
    return items


def run_process(config, mode):
    """Generic function to run the scraping process for a given config and mode."""
    driver = None
    try:
        prompts = config["lang_prompts"]
        json_file = config["json_file"]
        
        if mode == 'initial':
            print("=== INITIAL SETUP: Extracting all receipts ===")
        else:
            print("=== UPDATE: Adding new receipts ===")

        email, password = get_user_credentials(prompts)
        driver = setup_driver()
        if not login_to_lidl(driver, email, password, config):
            raise Exception("Login failed")

        driver.get(config["url"])
        accept_cookies(driver)
        
        existing_urls, existing_receipts = load_existing_receipts(json_file)
        print(f"Existing receipts: {len(existing_receipts)}")
        
        stop_on_duplicate = (mode == 'update')
        
        # --- Main processing loop ---
        processed_count, skipped_count, page_count = 0, 0, 1
        while True:
            print(f"\n--- Page {page_count} ---")
            page_links = collect_ticket_links_from_page(driver)
            print(f"Found {len(page_links)} links on this page.")

            if not page_links:
                break

            stop_processing = False
            for i, link in enumerate(page_links, 1):
                print(f"\nProcessing link {i}/{len(page_links)} on page {page_count}")
                if link in existing_urls:
                    print(f"Receipt already exists, skipping: {link}")
                    skipped_count += 1
                    if stop_on_duplicate:
                        print("Duplicate found - stopping update.")
                        stop_processing = True
                        break
                    continue
                
                driver.get(link)
                wait = WebDriverWait(driver, 25)
                
                wait_func = wait_for_receipt_page_de if config['country_code'] == 'de' else wait_for_receipt_page_nl
                if not wait_func(driver, wait):
                    print("Failed to load receipt page.")
                    continue

                extract_func = extract_basic_receipt_info_de if config['country_code'] == 'de' else extract_basic_receipt_info_nl
                receipt_data = extract_func(driver, link)
                receipt_data['url'] = link
                receipt_data['items'] = extract_receipt_items(driver)
                
                if receipt_data:
                    add_receipt_to_json(receipt_data, json_file)
                    existing_urls.add(link)
                    processed_count += 1
                else:
                    print("Failed to extract data")
                time.sleep(1)
            
            if stop_processing:
                break

            driver.get(f"{config['url'].split('?')[0]}?page={page_count}")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.purchase-history_ticketsTable__D-i0e")))
            if not has_next_page(driver):
                print("No more pages found.")
                break
            go_to_next_page(driver)
            page_count += 1

        if processed_count > 0:
            total_receipts = sort_receipts_by_date(json_file)
            print(f"\n{processed_count} new receipts added and all receipts sorted by date.")
        else:
            total_receipts = len(existing_receipts)
            print("\nNo new receipts found.")
            
        print(f"\n=== PROCESS COMPLETE ===")
        print(f"Pages processed: {page_count}")
        print(f"New receipts added: {processed_count}")
        print(f"Total receipts in file: {total_receipts}")
        return True

    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    finally:
        if driver:
            driver.quit()
        print("Process finished.")


def main():
    """Main menu to select mode and country."""
    print("=== Welcome to the Lidl Receipt Scraper ===")
    print("1. Initial Setup (All receipts)")
    print("2. Update (Only new receipts)")
    print("3. Exit")
    
    choice = ""
    while choice not in ["1", "2", "3"]:
        choice = input("\nSelect an option (1-3): ").strip()

    if choice == "3":
        print("Goodbye!")
        return

    print("\nSelect the country:")
    print("1. Germany (de)")
    print("2. Netherlands (nl)")
    
    country_choice = ""
    while country_choice not in ["1", "2"]:
        country_choice = input("\nSelect a country (1-2): ").strip()
        
    config = DE_CONFIG if country_choice == "1" else NL_CONFIG
    mode = 'initial' if choice == "1" else 'update'
    
    run_process(config, mode)


if __name__ == "__main__":
    main()
