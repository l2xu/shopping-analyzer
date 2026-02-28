import streamlit as st
import pandas as pd
import json
import os # Imported to check for file existence

# --- Data Loading and Preparation ---

# Define the filename
DATA_FILE = "lidl_receipts.json"

# Function to load data from the JSON file
def load_data(filename):
    if not os.path.exists(filename):
        st.error(f"Fehler: Die Datei '{filename}' wurde nicht gefunden. Bitte erstellen Sie sie im gleichen Verzeichnis wie das Skript.")
        return None # Return None to stop the script from running further

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError:
        st.error(f"Fehler: Die Datei '{filename}' ist keine gültige JSON-Datei. Bitte überprüfen Sie das Format.")
        return None
    except Exception as e:
        st.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
        return None

# Load the data
data = load_data(DATA_FILE)

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
    df['purchase_date'] = pd.to_datetime(df['purchase_date'], format='%Y.%m.%d')
    df['total_price'] = df['total_price'].apply(to_float)
    df['saved_amount'] = df['saved_amount'].apply(to_float)
    df['lidlplus_saved_amount'] = df['lidlplus_saved_amount'].apply(to_float) if 'lidlplus_saved_amount' in df.columns else 0.0
    # Handle sticker discounts (RABATT X%) if present
    if 'sticker_discount_amount' in df.columns:
        df['sticker_discount_amount'] = df['sticker_discount_amount'].apply(to_float)
    else:
        df['sticker_discount_amount'] = 0.0

    # --- Data Filtering ---
    # Filter out entries with null/zero total_price or empty items array
    initial_count = len(df)
    
    # Remove entries where total_price is null, 0, or NaN
    
    # Remove entries where items array is empty or null
    df = df[df['items'].notna()]  # Remove null items
    df = df[df['items'].apply(lambda x: isinstance(x, list) and len(x) > 0)]  # Remove empty arrays
    
    filtered_count = len(df)
    filtered_out = initial_count - filtered_count
    
    if filtered_out > 0:
        st.info(f"Info: Kassenbons ({filtered_out}) wurden herausgefiltert. Entweder hatten sie keinen Gesamtpreis oder keine Artikel. Kassenbons vor Februar 2023 sind möglicherweise betroffen.")

    # --- Streamlit Dashboard ---

    st.set_page_config(layout="wide", page_title="Lidl Kassenbons Dashboard", page_icon="🛒")

    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("Lidl+ Dashboard")

    # --- Sidebar for Filters ---
    st.sidebar.header("Nach Datum filtern")
    min_date = df['purchase_date'].min().date()
    max_date = df['purchase_date'].max().date()

    start_date = st.sidebar.date_input("Startdatum", min_date, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input("Enddatum", max_date, min_value=min_date, max_value=max_date)

    # Convert dates to datetime objects for comparison
    start_datetime = pd.to_datetime(start_date)
    end_datetime = pd.to_datetime(end_date) + pd.Timedelta(days=1)

    # Filter dataframe based on date range
    filtered_df = df[(df['purchase_date'] >= start_datetime) & (df['purchase_date'] < end_datetime)]

    # --- Main Page ---

    st.header("Kennzahlen")

    # Calculate metrics from the filtered data
    total_receipts = len(filtered_df)
    total_spent = filtered_df['total_price'].sum()
    total_saved = filtered_df['saved_amount'].sum()
    # Sticker discounts (separate from regular 'saved_amount')
    sticker_saved = filtered_df['sticker_discount_amount'].sum() if 'sticker_discount_amount' in filtered_df.columns else 0.0
    
    # Handle Lidl Plus savings if available
    if 'lidlplus_saved_amount' in filtered_df.columns:
        lidlplus_saved = filtered_df['lidlplus_saved_amount'].sum()
    else:
        lidlplus_saved = 0

    # First row: Basic metrics
    st.markdown("##### Grunddaten")
    col1, col2 = st.columns(2)
    col1.metric("Ausgaben gesamt", f"€{total_spent:,.2f}")

    col2.metric("Kassenbons gesamt", f"{total_receipts}")
    
    # Second row: Lidl Plus savings
    st.markdown("##### Lidl Plus Ersparnisse")
    col1, col2 = st.columns(2)
    lidlplus_percentage = (lidlplus_saved / total_spent * 100) if total_spent > 0 else 0
    col1.metric("Lidl Plus gespart", f"€{lidlplus_saved:,.2f}")
    col2.metric("Lidl Plus Sparquote", f"{lidlplus_percentage:.1f}%")
    
    # Third row: Regular savings
    st.markdown("##### Reguläre Rabatte")
    col1, col2 = st.columns(2)
    regular_percentage = (total_saved / total_spent * 100) if total_spent > 0 else 0
    col1.metric("Reguläre Rabatte gespart", f"€{total_saved:,.2f}")
    col2.metric("Reguläre Sparquote", f"{regular_percentage:.1f}%")

    # Fourth row: Sticker discounts (RABATT X%)
    st.markdown("##### Sticker Rabatte (RABATT X%)")
    col1, col2 = st.columns(2)
    sticker_percentage = (sticker_saved / total_spent * 100) if total_spent > 0 else 0
    col1.metric("Sticker Rabatte gespart", f"€{sticker_saved:,.2f}")
    col2.metric("Sticker Sparquote", f"{sticker_percentage:.1f}%")

    st.markdown("---")

    # --- Spending Over Time ---
    st.header("Ausgaben über Zeit")
    
    if not filtered_df.empty:
        # Create daily spending aggregation
        spending_over_time = filtered_df.copy()
        spending_over_time['date'] = spending_over_time['purchase_date'].dt.date
        daily_spending = spending_over_time.groupby('date')['total_price'].sum().reset_index()
        daily_spending.columns = ['Datum', 'Tägliche Ausgaben (€)']
        
        # Calculate cumulative spending
        daily_spending['Kumulative Ausgaben (€)'] = daily_spending['Tägliche Ausgaben (€)'].cumsum()
        
        # Toggle for daily vs cumulative view
        spending_view = st.radio("Ausgabenansicht:", ["Täglich", "Kumulativ"], horizontal=True, key="spending_view")
        
        if spending_view == "Täglich":
            st.bar_chart(daily_spending.set_index('Datum')['Tägliche Ausgaben (€)'])
            
            # Show summary stats
            col1, col2, col3 = st.columns(3)
            col1.metric("Durchschnittliche tägliche Ausgaben", f"€{daily_spending['Tägliche Ausgaben (€)'].mean():.2f}")
            col2.metric("Höchste tägliche Ausgaben", f"€{daily_spending['Tägliche Ausgaben (€)'].max():.2f}")
            col3.metric("Niedrigste tägliche Ausgaben", f"€{daily_spending['Tägliche Ausgaben (€)'].min():.2f}")
            
        else:  # Cumulative view
            st.bar_chart(daily_spending.set_index('Datum')['Kumulative Ausgaben (€)'])
            
            # Show growth metrics
            total_days = len(daily_spending)
            avg_daily_growth = daily_spending['Kumulative Ausgaben (€)'].iloc[-1] / total_days if total_days > 0 else 0
            
            col1, col2 = st.columns(2)
            col1.metric("Tage gesamt", total_days)
            col2.metric("Durchschnittliches tägliches Wachstum", f"€{avg_daily_growth:.2f}")
    else:
        st.write("Keine Ausgabendaten für den ausgewählten Datumsbereich verfügbar.")

    st.markdown("---")

    # --- Top 10 Most Purchased Items ---
    st.header("Top 10 der meistgekauften Artikel")

    if not filtered_df.empty:
        # Toggle for quantity vs price
        view_mode = st.radio("Anzeigen nach:", ["Menge", "Gesamtpreis"], horizontal=True)
        
        # Extract all items from the filtered receipts
        items_data = []
        for _, row in filtered_df.iterrows():
            if row.get('items') and isinstance(row['items'], list):
                for item in row['items']:
                    try:
                        # Handle both string and numeric quantities, convert commas to dots for German format
                        quantity_str = str(item.get('quantity', 1))
                        quantity = float(quantity_str.replace(',', '.'))
                        price = to_float(item.get('price', 0))
                        unit = item.get('unit', 'stk')  # Default to 'stk' if no unit specified
                    except (ValueError, TypeError):
                        quantity = 1.0
                        price = 0
                        unit = 'stk'
                    
                    items_data.append({
                        'name': item['name'],
                        'quantity': quantity,
                        'price': price,
                        'unit': unit,
                        'total_value': quantity * price
                    })

        if items_data:
            items_df = pd.DataFrame(items_data)
            
            # Filter out Pfand items (deposit bottles/cans)
            items_df = items_df[~items_df['name'].str.contains('Pfand', case=False, na=False)]
            
            if view_mode == "Menge":
                # Group by item name and sum quantities, keeping track of units
                grouped = items_df.groupby('name').agg({
                    'quantity': 'sum',
                    'unit': 'first'  # Take the first unit (should be consistent for same item)
                }).reset_index()
                grouped = grouped.sort_values('quantity', ascending=False).head(10)
                
                # Format quantities nicely and add units
                grouped['Gesamtmenge'] = grouped.apply(lambda row: 
                    f"{row['quantity']:.3f} {row['unit']}" if row['unit'] == 'kg' 
                    else f"{int(row['quantity'])} {row['unit']}", axis=1)
                
                # Select only the columns we want to display
                display_df = grouped[['name', 'Gesamtmenge']].copy()
                display_df.columns = ['Artikel', 'Gesamtmenge']
                
                st.dataframe(display_df, width='stretch', hide_index=True)
                
            else:  # Total Price view
                # Group by item name and sum total values
                grouped = items_df.groupby('name')['total_value'].sum().reset_index()
                grouped = grouped.sort_values('total_value', ascending=False).head(10)
                grouped.columns = ['Artikel', 'Ausgaben gesamt (€)']
                grouped['Ausgaben gesamt (€)'] = grouped['Ausgaben gesamt (€)'].round(2)
                
                st.dataframe(grouped, width='stretch', hide_index=True)
        else:
            st.write("Keine Artikel im ausgewählten Datumsbereich gefunden.")

    else:
        st.write("Keine Daten für den ausgewählten Datumsbereich verfügbar.")