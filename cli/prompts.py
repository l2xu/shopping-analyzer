"""User input and selection prompts."""


def select_auth_method() -> str:
    """
    Let user select authentication method (browser extraction or file).

    Returns:
        str: 'file' for cookie file, or browser name ('firefox' or 'chrome')
    """
    print("\n=== Authentifizierungs-Methode ===")
    print("Wie möchten Sie sich authentifizieren?")
    print("1. Firefox Browser (muss geöffnet sein)")
    print("2. Chrome Browser (muss geöffnet sein)")
    print("3. Cookie-Datei (muss cookies enthalten)")

    while True:
        try:
            choice = input("\nWähle eine Option (1-3): ").strip()

            if choice == "1":
                return "firefox"
            elif choice == "2":
                return "chrome"
            elif choice == "3":
                return "file"
            else:
                print("Ungültige Eingabe. Bitte wähle 1, 2 oder 3.")

        except KeyboardInterrupt:
            print("\n\nAuthentifizierungs-Auswahl abgebrochen.")
            return "firefox"  # Default fallback


def select_browser() -> str:
    """
    DEPRECATED: Use select_auth_method() instead.
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
