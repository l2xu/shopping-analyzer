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
- [Google Chrome browser](https://www.google.com/chrome/) or [Mozilla Firefox browser](https://www.mozilla.org/firefox/) installed
  - You need to be logged in to your Lidl Plus Account in the browser of your choice
- Lidl Plus account with online purchase history

### Important Limitation

⚠️ **Data Availability**: Receipt data on the Lidl website is only available from **February 2023 onwards**. The script will automatically stop when it encounters receipts older than February 2023, as this data is no longer accessible on the Lidl website.

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

   **On Mac/Linux:**

   ```bash
   source venv/bin/activate
   ```

   **On Windows:**

   ```cmd
   venv\Scripts\activate
   ```

5. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

Now the project is successfully set up and you can start extracting data from your Lidl+ account!

### Usage

**Step 1: Login to Lidl Plus in Firefox or Chrome**

- [Lidl Login](https://www.lidl.de/mla/)

**Step 2: Run the data extraction script**

```bash
python get_data.py
```

**Step 3: Choose your operation mode**

You'll see a menu with options:

1. Initial Setup - Extract all historical receipt data (choose this for first run)
2. Update Data - Add only new receipts
3. Exit

**Step 4: Login to your Lidl+ account**

Choose which browser you used for **Step 1**:

1. Firefox
2. Chrome

**Step 5: Automated data extraction**

The program will automatically extract data from all your receipts (after 14.02.2022)

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
- [Google Chrome browser](https://www.google.com/chrome/) oder [Mozilla Firefox Browser](https://www.mozilla.org/firefox/) installiert
  - In dem Browser deiner Wahl in dein Lidl-Plus Konto eingeloggt
- Lidl Plus Konto mit Online-Kaufverlauf

### Wichtige Einschränkung

⚠️ **Datenverfügbarkeit**: Kassenbondaten sind auf der Lidl-Website nur ab **Februar 2023** verfügbar. Das Skript stoppt automatisch, wenn es auf ältere Kassenbons stößt, da diese Daten nicht mehr auf der Lidl-Website zugänglich sind.

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

   **Unter Mac/Linux:**

   ```bash
   source venv/bin/activate
   ```

   **Unter Windows:**

   ```cmd
   venv\Scripts\activate
   ```

5. **Benötigte Packages installieren**

   ```bash
   pip install -r requirements.txt
   ```

Jetzt ist das Projekt erfolgreich aufgesetzt und Sie können anfangen, Ihre Daten aus Ihrem Lidl+ Account zu ziehen!

### Verwendung

**Schritt 1: In Firefox oder Chrome in Lidl-Plus einloggen**

- [Lidl Login](https://www.lidl.de/mla/)

**Schritt 2: Datenextraktions-Skript starten**

```bash
python get_data.py
```

**Schritt 3: Betriebsmodus wählen**

Sie haben die Wahl zwischen:

1. Initial Setup - Alle historischen Kassenbondaten extrahieren (für den ersten Durchlauf)
2. Update Data - Nur neue Kassenbons hinzufügen
3. Exit - Beenden

Wählen Sie "1" für das Initial Setup und bestätigen Sie mit der Enter-Taste.

**Schritt 4: Mit Lidl+ Account anmelden**

Wählen Sie aus welchen Browser Sie für **Schritt 1** verwendet haben:

1. Firefox
2. Chrome

**Schritt 5: Automatische Datenextraktion**

Nun wird das Programm automatisiert die Daten all Ihrer Kassenbons (nach dem 14.02.2022) extrahieren

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

---

## 📄 License

This project is licensed under the **GNU Affero General Public License v3.0** (AGPL-3.0).

### Copyright Notice

```text
Shopping Analyzer - Tool to extract and manage Lidl receipt data
Copyright (C) 2025 Lukas Weihrauch

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
```

### What this means for you:

- **Freedom to use**: You can use this software for any purpose
- **Freedom to study**: You can examine how the program works and adapt it to your needs
- **Freedom to share**: You can redistribute copies to help others
- **Freedom to improve**: You can distribute copies of your modified versions to benefit the community

### Important AGPL-3.0 Requirements:

- **Network use = Source sharing**: If you run a modified version of this software on a server that others can access over a network, you must make the source code of your modified version available to those users
- **Share improvements**: Any modifications or derivative works must also be licensed under AGPL-3.0
- **Attribution**: You must preserve all copyright notices and license information

For the complete license terms, see the [`LICENCE.md`](./LICENCE.md) file in this repository.

---
