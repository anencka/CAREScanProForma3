"""
Simplified app.py demonstrating integration with financeModels for CSV-JSON synchronization.

This is a stripped-down version of app.py to show the integration points
for the CSV-JSON synchronization functionality in the financeModels package.
"""

import streamlit as st
import pandas as pd
import os
from typing import Dict

# Import the financeModels functionality
from financeModels.file_handler import (
    sync_json_to_csv,
    sync_csv_to_json,
    load_csv,
    save_csv
)
from financeModels.app_integration import display_personnel_expenses_dashboard

# Constants
CSV_FILES = {
    "Revenue": "Revenue.csv",
    "Equipment": "Equipment.csv",
    "Personnel": "Personnel.csv",
    "Exams": "Exams.csv"
}

# Set page configuration
st.set_page_config(
    page_title="CAREScan ProForma Editor with CSV-JSON Sync",
    page_icon="📊",
    layout="wide"
)

# Helper functions for JSON-CSV synchronization
def import_json_and_sync_csvs(json_filepath):
    """
    Import data from a JSON file and update both CSV files and session state.
    
    Args:
        json_filepath: Path to the JSON file to import
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Load the JSON data and update CSV files
        data_dict = sync_json_to_csv(json_filepath, CSV_FILES)
        
        # Update the session state with the new data
        for key, df in data_dict.items():
            st.session_state.dataframes[key] = df
        
        st.success(f"Successfully imported data from {json_filepath} and updated CSV files")
        return True
    except Exception as e:
        st.error(f"Error importing data: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return False

def export_csvs_to_json(json_filepath):
    """
    Export the current session state data to a JSON file and update CSV files.
    
    Args:
        json_filepath: Path to the JSON file to create/update
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure we have the most recent data
        data_dict = {}
        for key, filepath in CSV_FILES.items():
            if key in st.session_state.dataframes:
                # Save the current DataFrame to CSV
                save_csv(st.session_state.dataframes[key], filepath)
                data_dict[key] = st.session_state.dataframes[key]
        
        # Then synchronize all CSV files to the JSON
        sync_csv_to_json(CSV_FILES, json_filepath)
        
        st.success(f"Successfully exported data to {json_filepath}")
        return True
    except Exception as e:
        st.error(f"Error exporting data: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return False

# Save individual dataset
def save_dataset(name, df):
    """
    Save an individual dataset to its CSV file.
    
    Args:
        name: Name of the dataset (key in CSV_FILES)
        df: DataFrame to save
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if name in CSV_FILES:
            save_csv(df, CSV_FILES[name])
            return True
        return False
    except Exception as e:
        st.error(f"Error saving {name}: {str(e)}")
        return False

# Application title
st.title("CAREScan ProForma Editor with CSV-JSON Sync")

# Initialize session state
if 'dataframes' not in st.session_state:
    st.session_state.dataframes = {}
    # Load all CSV files into session state
    for name, file in CSV_FILES.items():
        try:
            st.session_state.dataframes[name] = load_csv(file)
        except Exception as e:
            st.error(f"Error loading {file}: {str(e)}")
            st.session_state.dataframes[name] = pd.DataFrame()

# Create tabs for each CSV file plus Export/Import and Personnel Analysis
tabs = st.tabs(list(CSV_FILES.keys()) + ["Export/Import", "Personnel Analysis"])

# Display and edit each CSV in its respective tab
for i, name in enumerate(CSV_FILES.keys()):
    with tabs[i]:
        st.header(f"{name} Data")
        
        # Information about editing
        st.info(
            "Edit the data directly in the table below. "
            "For semicolon-separated lists, use commas or semicolons to separate values. "
            "For large numbers, you can use underscores for readability (e.g., 200_000 or 200000)."
        )
        
        # Create an editable dataframe
        edited_df = st.data_editor(
            st.session_state.dataframes[name],
            use_container_width=True,
            num_rows="dynamic",
            key=f"editor_{name}"
        )
        
        # Save button for each tab
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            if st.button(f"Save {name}", key=f"save_{name}"):
                try:
                    # Get editor data
                    editor_data = st.session_state[f"editor_{name}"]
                    
                    # Convert to DataFrame if needed
                    if isinstance(editor_data, pd.DataFrame):
                        # Already a DataFrame
                        df_to_save = editor_data
                    elif isinstance(editor_data, dict):
                        # Try to convert dict to DataFrame
                        if all(isinstance(v, dict) for v in editor_data.values()):
                            # Dict of dicts (row_index -> row_data)
                            rows = list(editor_data.values())
                            df_to_save = pd.DataFrame(rows)
                        else:
                            st.error(f"Could not convert {name} data to DataFrame - unexpected structure.")
                            df_to_save = None
                    else:
                        st.error(f"Unexpected data type for {name}: {type(editor_data)}")
                        df_to_save = None
                    
                    # Save if we successfully got a DataFrame
                    if df_to_save is not None:
                        if save_dataset(name, df_to_save):
                            st.session_state.dataframes[name] = df_to_save
                            st.success(f"{name} data saved successfully!")
                
                except Exception as e:
                    import traceback
                    st.error(f"Error saving {name}: {str(e)}")
                    st.error(traceback.format_exc())
        
        with col2:
            if st.button(f"Save All & Sync", key=f"sync_{name}"):
                try:
                    # Save this dataset first
                    editor_data = st.session_state[f"editor_{name}"]
                    if isinstance(editor_data, pd.DataFrame):
                        df_to_save = editor_data
                    elif isinstance(editor_data, dict):
                        if all(isinstance(v, dict) for v in editor_data.values()):
                            rows = list(editor_data.values())
                            df_to_save = pd.DataFrame(rows)
                        else:
                            st.error(f"Could not convert {name} data to DataFrame.")
                            df_to_save = None
                    else:
                        st.error(f"Unexpected data type for {name}.")
                        df_to_save = None
                    
                    if df_to_save is not None:
                        # Update session state and save to CSV
                        st.session_state.dataframes[name] = df_to_save
                        save_dataset(name, df_to_save)
                        
                        # Update JSON file
                        json_filepath = "carescan_data.json"
                        export_csvs_to_json(json_filepath)
                        
                        st.success(f"Data saved and synchronized with {json_filepath}")
                
                except Exception as e:
                    import traceback
                    st.error(f"Error during save and sync: {str(e)}")
                    st.error(traceback.format_exc())

# Export/Import tab
with tabs[-2]:
    st.header("Export and Import Data")
    
    # Import section
    st.subheader("Import Data from JSON")
    import_path = st.text_input("Import file path", "carescan_data.json")
    
    if st.button("Import Data from JSON and Update CSV Files"):
        import_json_and_sync_csvs(import_path)
    
    # Export section
    st.subheader("Export Data to JSON")
    export_path = st.text_input("Export file path", "carescan_data.json")
    
    if st.button("Export All Data to JSON"):
        export_csvs_to_json(export_path)
    
    # Explanation of synchronization
    st.info("""
    ### How CSV-JSON Synchronization Works
    
    - When you import from a JSON file, all corresponding CSV files are updated automatically.
    - When you export to a JSON file, all CSV files are first updated from the app state, then compiled into the JSON.
    - The "Save & Sync" button in each tab saves the current tab's data and updates both the CSV and JSON files.
    
    This ensures that your data is consistent across all file formats.
    """)

# Personnel Analysis tab
with tabs[-1]:
    st.header("Personnel Expenses Analysis")
    
    if "Personnel" in st.session_state.dataframes:
        # Get the personnel data
        personnel_data = st.session_state.dataframes["Personnel"]
        
        # Process dates
        for date_col in ['StartDate', 'EndDate']:
            if date_col in personnel_data.columns:
                personnel_data[date_col] = pd.to_datetime(
                    personnel_data[date_col], 
                    format='%m/%d/%Y', 
                    errors='coerce'
                )
        
        # Display the personnel expenses dashboard
        display_personnel_expenses_dashboard(personnel_data)
    else:
        st.error("Personnel data not found in session state!")

# Add a footer
st.markdown("---")
st.markdown("CAREScan ProForma Editor with financeModels integration")
st.markdown("Demonstrating CSV-JSON synchronization functionality") 