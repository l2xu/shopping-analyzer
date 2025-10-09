import streamlit as st
import pandas as pd
import json
import os  # Imported to check for file existence

# --- Translations ---
LANGUAGES = {
    "de": {
        "page_title": "Lidl Kassenbons Dashboard",
        "title": "Lidl+ Dashboard",
        "filter_header": "Nach Datum filtern",
        "start_date": "Startdatum",
        "end_date": "Enddatum",
        "kpi_header": "Kennzahlen",
        "basic_data": "Grunddaten",
        "total_spent": "Ausgaben gesamt",
        "total_receipts": "Kassenbons gesamt",
        "lidl_plus_savings_header": "Lidl Plus Ersparnisse",
        "lidl_plus_saved": "Lidl Plus gespart",
        "lidl_plus_rate": "Lidl Plus Sparquote",
        "regular_savings_header": "Reguläre Rabatte",
        "regular_saved": "Reguläre Rabatte gespart",
        "regular_rate": "Reguläre Sparquote",
        "spending_over_time": "Ausgaben über Zeit",
        "spending_view": "Ausgabenansicht:",
        "daily": "Täglich",
        "cumulative": "Kumulativ",
        "avg_daily_spending": "Durchschnittliche tägliche Ausgaben",
        "highest_daily_spending": "Höchste tägliche Ausgaben",
        "lowest_daily_spending": "Niedrigste tägliche Ausgaben",
        "total_days": "Tage gesamt",
        "avg_daily_growth": "Durchschnittliches tägliches Wachstum",
        "no_spending_data": "Keine Ausgabendaten für den ausgewählten Datumsbereich verfügbar.",
        "top_10_items": "Top 10 der meistgekauften Artikel",
        "view_by": "Anzeigen nach:",
        "quantity": "Menge",
        "total_price_view": "Gesamtpreis",
        "item_col": "Artikel",
        "total_quantity_col": "Gesamtmenge",
        "total_spent_col": "Ausgaben gesamt (€)",
        "no_items_found": "Keine Artikel im ausgewählten Datumsbereich gefunden.",
        "no_data_for_range": "Keine Daten für den ausgewählten Datumsbereich verfügbar.",
        "error_file_not_found": "Fehler: Keine der Dateien ('lidl_receipts.json', 'lidl_receipts_nl.json') wurde gefunden.",
        "error_invalid_json": "Fehler: Eine der JSON-Dateien ist ungültig. Bitte überprüfen Sie das Format.",
        "error_unexpected": "Ein unerwarteter Fehler ist aufgetreten: {e}"
    },
    "nl": {
        "page_title": "Lidl Kassabonnen Dashboard",
        "title": "Lidl+ Dashboard",
        "filter_header": "Filter op datum",
        "start_date": "Startdatum",
        "end_date": "Einddatum",
        "kpi_header": "Kerncijfers",
        "basic_data": "Basisgegevens",
        "total_spent": "Totaal uitgegeven",
        "total_receipts": "Totaal kassabonnen",
        "lidl_plus_savings_header": "Lidl Plus Besparingen",
        "lidl_plus_saved": "Lidl Plus bespaard",
        "lidl_plus_rate": "Lidl Plus besparingspercentage",
        "regular_savings_header": "Reguliere Kortingen",
        "regular_saved": "Reguliere kortingen bespaard",
        "regular_rate": "Regulier besparingspercentage",
        "spending_over_time": "Uitgaven in de tijd",
        "spending_view": "Uitgavenweergave:",
        "daily": "Dagelijks",
        "cumulative": "Cumulatieg",
        "avg_daily_spending": "Gemiddelde dagelijkse uitgaven",
        "highest_daily_spending": "Hoogste dagelijkse uitgaven",
        "lowest_daily_spending": "Laagste dagelijkse uitgaven",
        "total_days": "Totaal aantal dagen",
        "avg_daily_growth": "Gemiddelde dagelijkse groei",
        "no_spending_data": "Geen uitgavengegevens beschikbaar voor de geselecteerde periode.",
        "top_10_items": "Top 10 meest gekochte artikelen",
        "view_by": "Weergeven op:",
        "quantity": "Hoeveelheid",
        "total_price_view": "Totale prijs",
        "item_col": "Artikel",
        "total_quantity_col": "Totale hoeveelheid",
        "total_spent_col": "Totaal uitgegeven (€)",
        "no_items_found": "Geen artikelen gevonden in de geselecteerde periode.",
        "no_data_for_range": "Geen gegevens beschikbaar voor de geselecteerde periode.",
        "error_file_not_found": "Fout: Geen van de bestanden ('lidl_receipts.json', 'lidl_receipts_nl.json') gevonden.",
        "error_invalid_json": "Fout: Een van de JSON-bestanden is ongeldig. Controleer het formaat.",
        "error_unexpected": "Er is een onverwachte fout opgetreden: {e}"
    }
}

# --- Language Selection ---
if 'language' not in st.session_state:
    st.title("Select Language / Sprache wählen")
    lang_choice = st.selectbox("Choose your language:", ("Deutsch", "Nederlands"))
    if st.button("Start Dashboard"):
        st.session_state.language = "de" if lang_choice == "Deutsch" else "nl"
        st.rerun()
    st.stop()

LANG = st.session_state.language
T = LANGUAGES[LANG]

# --- Data Loading and Preparation ---

# Function to load data from the JSON files
def load_data(filenames, lang):
    all_data = []
    found_files = False
    for filename in filenames:
        if os.path.exists(filename):
            found_files = True
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    all_data.extend(data)
            except json.JSONDecodeError:
                st.error(LANGUAGES[lang]["error_invalid_json"])
                return None
            except Exception as e:
                st.error(LANGUAGES[lang]["error_unexpected"].format(e=e))
                return None
    
    if not found_files:
        st.error(LANGUAGES[lang]["error_file_not_found"])
        return None
        
    return all_data

# Define filenames
DATA_FILES = ["lidl_receipts.json", "lidl_receipts_nl.json"]
# Load the data
data = load_data(DATA_FILES, LANG)

# --- Main Application Logic ---
# We only run the dashboard logic if the data was loaded successfully
if data:
    # Convert to a pandas DataFrame
    df = pd.DataFrame(data)

    # --- Data Cleaning and Transformation ---

    # Function to convert comma-decimal strings to floats
    def to_float(x):
        if x is None or x == '' or str(x).strip() == '':
            return 0.0
        return float(str(x).replace(',', '.'))

    # Apply conversions
    df['purchase_date'] = pd.to_datetime(df['purchase_date'], format='%d.%m.%Y', errors='coerce')
    df.dropna(subset=['purchase_date'], inplace=True) # Drop rows where date conversion failed

    df['total_price'] = df['total_price'].apply(to_float)
    df['saved_amount'] = df['saved_amount'].apply(to_float)
    df['lidlplus_saved_amount'] = df['lidlplus_saved_amount'].apply(to_float) if 'lidlplus_saved_amount' in df.columns else 0.0

    # --- Data Filtering ---
    # Filter out entries with null/zero total_price or empty items array
    initial_count = len(df)
    
    # Remove entries where total_price is null, 0, or NaN
    df = df[df['total_price'] > 0]
    
    # Remove entries where items array is empty or null
    df = df[df['items'].notna()]  # Remove null items
    df = df[df['items'].apply(lambda x: isinstance(x, list) and len(x) > 0)]  # Remove empty arrays
    
    filtered_count = len(df)
    filtered_out = initial_count - filtered_count
    
    if filtered_out > 0:
        st.info(f"Info: Kassenbons ({filtered_out}) wurden herausgefiltert. Entweder hatten sie keinen Gesamtpreis oder keine Artikel. Kassenbons vor Februar 2023 sind möglicherweise betroffen.")

    # --- Streamlit Dashboard ---
    st.set_page_config(layout="wide", page_title=T["page_title"], page_icon="🛒")

    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main .block-container {padding-top: 2rem;}
    .metric-card {background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #1f77b4;}
    </style>
    """, unsafe_allow_html=True)
    st.title(T["title"])

    # --- Sidebar for Filters ---
    st.sidebar.header(T["filter_header"])
    min_date = df['purchase_date'].min().date()
    max_date = df['purchase_date'].max().date()
    start_date = st.sidebar.date_input(T["start_date"], min_date, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input(T["end_date"], max_date, min_value=min_date, max_value=max_date)
    
    # Convert dates to datetime objects for comparison
    start_datetime = pd.to_datetime(start_date)
    end_datetime = pd.to_datetime(end_date) + pd.Timedelta(days=1)
    # Filter dataframe based on date range
    filtered_df = df[(df['purchase_date'] >= start_datetime) & (df['purchase_date'] < end_datetime)]

    # --- Main Page ---
    st.header(T["kpi_header"])

    # Calculate metrics from the filtered data
    total_receipts = len(filtered_df)
    total_spent = filtered_df['total_price'].sum()
    total_saved = filtered_df['saved_amount'].sum()
    lidlplus_saved = filtered_df['lidlplus_saved_amount'].sum() if 'lidlplus_saved_amount' in filtered_df.columns else 0

    # First row: Basic metrics
    st.markdown(f"##### {T['basic_data']}")
    col1, col2 = st.columns(2)
    col1.metric(T["total_spent"], f"€{total_spent:,.2f}")
    col2.metric(T["total_receipts"], f"{total_receipts}")

    # Second row: Lidl Plus savings
    st.markdown(f"##### {T['lidl_plus_savings_header']}")
    col1, col2 = st.columns(2)
    lidlplus_percentage = (lidlplus_saved / total_spent * 100) if total_spent > 0 else 0
    col1.metric(T["lidl_plus_saved"], f"€{lidlplus_saved:,.2f}")
    col2.metric(T["lidl_plus_rate"], f"{lidlplus_percentage:.1f}%")

    # Third row: Regular savings
    st.markdown(f"##### {T['regular_savings_header']}")
    col1, col2 = st.columns(2)
    regular_percentage = (total_saved / total_spent * 100) if total_spent > 0 else 0
    col1.metric(T["regular_saved"], f"€{total_saved:,.2f}")
    col2.metric(T["regular_rate"], f"{regular_percentage:.1f}%")

    st.markdown("---")
    # --- Spending Over Time ---
    st.header(T["spending_over_time"])
    if not filtered_df.empty:
        # Create daily spending aggregation
        spending_over_time = filtered_df.copy()
        spending_over_time['date'] = spending_over_time['purchase_date'].dt.date
        daily_spending = spending_over_time.groupby('date')['total_price'].sum().reset_index()
        daily_spending.columns = ['Datum' if LANG == 'de' else 'Datum', 'Daily Spend (€)']
        # Calculate cumulative spending
        daily_spending['Cumulative Spend (€)'] = daily_spending['Daily Spend (€)'].cumsum()
        
        # Toggle for daily vs cumulative view
        spending_view = st.radio(T["spending_view"], [T["daily"], T["cumulative"]], horizontal=True, key="spending_view")
        
        if spending_view == T["daily"]:
            st.bar_chart(daily_spending.set_index('Datum' if LANG == 'de' else 'Datum')['Daily Spend (€)'])
            # Show summary stats
            col1, col2, col3 = st.columns(3)
            col1.metric(T["avg_daily_spending"], f"€{daily_spending['Daily Spend (€)'].mean():.2f}")
            col2.metric(T["highest_daily_spending"], f"€{daily_spending['Daily Spend (€)'].max():.2f}")
            col3.metric(T["lowest_daily_spending"], f"€{daily_spending['Daily Spend (€)'].min():.2f}")
        else: # Cumulative view
            st.bar_chart(daily_spending.set_index('Datum' if LANG == 'de' else 'Datum')['Cumulative Spend (€)'])
            # Show growth metrics
            total_days = len(daily_spending)
            avg_daily_growth = daily_spending['Cumulative Spend (€)'].iloc[-1] / total_days if total_days > 0 else 0
            col1, col2 = st.columns(2)
            col1.metric(T["total_days"], total_days)
            col2.metric(T["avg_daily_growth"], f"€{avg_daily_growth:.2f}")
    else:
        st.write(T["no_spending_data"])

    st.markdown("---")
    # --- Top 10 Most Purchased Items ---
    st.header(T["top_10_items"])
    if not filtered_df.empty:
        # Toggle for quantity vs price
        view_mode = st.radio(T["view_by"], [T["quantity"], T["total_price_view"]], horizontal=True)
        # Extract all items from the filtered receipts
        items_data = []
        for _, row in filtered_df.iterrows():
            if row.get('items') and isinstance(row['items'], list):
                for item in row['items']:
                    try:
                        # Handle both string and numeric quantities, convert commas to dots
                        quantity = float(str(item.get('quantity', 1)).replace(',', '.'))
                        price = to_float(item.get('price', 0))
                        unit = item.get('unit', 'stk')
                        items_data.append({'name': item['name'], 'quantity': quantity, 'price': price, 'unit': unit, 'total_value': quantity * price})
                    except (ValueError, TypeError):
                        continue
        if items_data:
            items_df = pd.DataFrame(items_data)
            if view_mode == T["quantity"]:
                # Group by item name and sum quantities, keeping track of units
                grouped = items_df.groupby('name').agg({'quantity': 'sum', 'unit': 'first'}).reset_index()
                grouped = grouped.sort_values('quantity', ascending=False).head(10)
                # Format quantities nicely and add units
                grouped[T['total_quantity_col']] = grouped.apply(lambda r: f"{r['quantity']:.3f} {r['unit']}" if r['unit'] == 'kg' else f"{int(r['quantity'])} {r['unit']}", axis=1)
                # Select only the columns we want to display
                display_df = grouped[['name', T['total_quantity_col']]].copy()
                display_df.columns = [T['item_col'], T['total_quantity_col']]
                st.dataframe(display_df, width='stretch', hide_index=True)
            else: # Total Price view
                # Group by item name and sum total values
                grouped = items_df.groupby('name')['total_value'].sum().reset_index()
                grouped = grouped.sort_values('total_value', ascending=False).head(10)
                grouped.columns = [T['item_col'], 'total_spent_value']
                # Format the value as a currency string to ensure left alignment
                grouped[T['total_spent_col']] = grouped['total_spent_value'].apply(lambda x: f"{x:,.2f}")
                
                # Select and rename columns for display
                display_df = grouped[[T['item_col'], T['total_spent_col']]]
                st.dataframe(display_df, width='stretch', hide_index=True)
        else:
            st.write(T["no_items_found"])
    else:
        st.write(T["no_data_for_range"])
