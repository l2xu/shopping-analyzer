# Shopping Analyzer

A Python tool to automatically extract and manage Lidl receipt data from your online purchase history.

Ein Python-Tool zum automatischen Extrahieren und Verwalten von Lidl-Kassenbondaten aus Ihrem Online-Kaufverlauf.

---

## 🇬🇧 English

### Features

- **Secure Login**: Prompts you to enter your Lidl credentials securely when running
- **Receipt Extraction**: Downloads all receipt data including items, prices, and dates
- **Smart Updates**: Only downloads new receipts during updates (no duplicates)
- **Data Export**: Saves all data in JSON format for easy analysis
- **Interactive Menu**: User-friendly interface for easy operation

### Prerequisites

- [Python 3.7 or higher](https://www.python.org/downloads/)
- [Google Chrome browser](https://www.google.com/chrome/) installed
- Lidl Plus account with online purchase history

### Installation

1. **Clone or download this repository**

   ```bash
   git clone <repository-url>
   cd shopping-analyzer
   ```

   Or download the ZIP file from GitHub and extract it.

2. **Open the folder in a terminal**

   Navigate to the project folder using your preferred terminal (e.g., Terminal on macOS, Command Prompt on Windows, or any terminal of your choice like Warp).

3. **Create a virtual environment (recommended)**

   This ensures that the packages we install only affect this project and don't clutter your entire system:

   ```bash
   python -m venv venv
   ```

4. **Activate the virtual environment**

   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

5. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

Now the project is successfully set up and you can start extracting data from your Lidl+ account!

### Usage

**Step 1: Run the data extraction script**

```bash
python get_data.py
```

**Step 2: Choose your operation mode**

You'll see a menu with options:

1. Initial Setup - Extract all historical receipt data (choose this for first run)
2. Update Data - Add only new receipts
3. Exit

**Step 3: Login to your Lidl+ account**

Enter your Lidl+ email address and password when prompted. Don't worry if the password doesn't appear on screen - this is normal and intentional for security.

**Step 4: Automated data extraction**

Google Chrome will open automatically and the program will:

- Log into your Lidl+ account
- Extract data from all your receipts
- Save the data automatically

⚠️ **Important**: This process may take some time, so grab a coffee or take a short walk! If the process crashes for any reason, simply run it again - the program will resume from where it left off.

**For future updates**: When you want to add new receipts later, run `python get_data.py` again and choose option 2 (Update Data). This will only extract new receipts that aren't already in your data.

### Output

The script creates a `lidl_receipts.json` file containing all your receipt data, automatically sorted by date (newest first).

### Data Analysis Dashboard

After collecting your receipt data, you can view and analyze it using the interactive dashboard:

```bash
streamlit run dashboard.py
```

This will start a web-based dashboard accessible at `http://localhost:8501` where you can analyse your shopping history.

---

## 🇩🇪 Deutsch

### Funktionen

- **Sicherer Login**: Fordert Sie zur sicheren Eingabe Ihrer Lidl-Zugangsdaten beim Ausführen auf
- **Kassenbon-Extraktion**: Lädt alle Kassenbondaten inklusive Artikel, Preise und Daten herunter
- **Intelligente Updates**: Lädt nur neue Kassenbons bei Updates herunter (keine Duplikate)
- **Datenexport**: Speichert alle Daten im JSON-Format für einfache Analyse
- **Interaktives Menü**: Benutzerfreundliche Oberfläche für einfache Bedienung

### Voraussetzungen

- [Python 3.7 oder höher](https://www.python.org/downloads/)
- [Google Chrome Browser](https://www.google.com/chrome/) installiert
- Lidl Plus Konto mit Online-Kaufverlauf

### Installation

**Schritt-für-Schritt Anleitung:**

1. **Repository herunterladen**

   Laden Sie das Repository von GitHub herunter oder klonen Sie es mit git (falls Sie damit Erfahrung haben):

   ```bash
   git clone <repository-url>
   cd shopping-analyzer
   ```

   Alternativ können Sie die ZIP-Datei herunterladen und entpacken.

2. **Ordner im Terminal öffnen**

   Öffnen Sie den Projektordner in einem Terminal Ihrer Wahl (z.B. "warp" unter macOS, aber jedes Terminal funktioniert).

3. **Python Environment aufsetzen**

   Dies sorgt dafür, dass die Packages nur dieses Projekt beeinflussen und nicht Ihren ganzen Computer:

   ```bash
   python -m venv venv
   ```

4. **Environment aktivieren**

   ```bash
   source venv/bin/activate  # Unter Windows: venv\Scripts\activate
   ```

5. **Benötigte Packages installieren**

   ```bash
   pip install -r requirements.txt
   ```

Jetzt ist das Projekt erfolgreich aufgesetzt und Sie können anfangen, Ihre Daten aus Ihrem Lidl+ Account zu ziehen!

### Verwendung

**Schritt 1: Datenextraktions-Skript starten**

```bash
python get_data.py
```

**Schritt 2: Betriebsmodus wählen**

Sie haben die Wahl zwischen:

1. Initial Setup - Alle historischen Kassenbondaten extrahieren (für den ersten Durchlauf)
2. Update Data - Nur neue Kassenbons hinzufügen
3. Exit - Beenden

Wählen Sie "1" für das Initial Setup und bestätigen Sie mit der Enter-Taste.

**Schritt 3: Mit Lidl+ Account anmelden**

Geben Sie zuerst Ihre E-Mail-Adresse ein und dann Ihr Passwort. Bestätigen Sie beides mit Enter.
**Wichtig**: Wundern Sie sich nicht, wenn das Passwort nicht angezeigt wird - das ist normal und gewollt aus Sicherheitsgründen.

**Schritt 4: Automatische Datenextraktion**

Google Chrome öffnet sich automatisch und das Programm wird:

- Sich in Ihren Lidl+ Account einloggen
- Die Daten aus allen Kassenbons extrahieren
- Alles automatisch abspeichern

⚠️ **Wichtiger Hinweis**: Dieser Prozess kann etwas dauern - holen Sie sich einen Kaffee oder gehen Sie eine kleine Runde spazieren! Sollte der Prozess aus irgendeinem Grund abstürzen, ist das kein Problem. Wiederholen Sie das Ganze einfach - das Programm springt schnell wieder zu der Stelle, wo es aufgehört hat.

**Für künftige Updates**: Wenn Sie Ihre Daten in Zukunft updaten möchten (weil neue Kassenbons hinzugekommen sind), führen Sie einfach wieder `python get_data.py` aus und wählen Sie Option 2. Hierbei werden nur die neuesten, noch nicht vorhandenen Kassenbons extrahiert und zu Ihren Daten hinzugefügt.

### Ausgabe

Nachdem der Prozess abgeschlossen ist, finden Sie alle extrahierten Daten in der `lidl_receipts.json` Datei. Diese Datei enthält alle Ihre Kassenbondaten, automatisch nach Datum sortiert (neueste zuerst), und ist gleichzeitig die Datenquelle für das Dashboard.

### Datenanalyse-Dashboard

Nach dem Sammeln Ihrer Kassenbondaten können Sie diese mit dem interaktiven Dashboard anzeigen und analysieren.

**Dashboard starten:**

```bash
streamlit run dashboard.py
```

Anschließend können Sie über den Link auf Ihr Dashboard zugreifen. Dies startet ein webbasiertes Dashboard, das unter `http://localhost:8501` erreichbar ist.
# shopping-analyzer
