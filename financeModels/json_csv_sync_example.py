"""
Example of synchronizing data between JSON and CSV files for the Streamlit app.

This module demonstrates how to:
1. Load data from JSON and update CSV files
2. Load data from CSV files and update JSON
3. Keep data consistent between both formats
"""

import pandas as pd
import streamlit as st
import os
from financeModels.file_handler import (
    sync_json_to_csv,
    sync_csv_to_json,
    load_json,
    load_csv,
    save_json,
    save_csv
)

# Define the CSV and JSON file mappings
DEFAULT_CSV_MAPPING = {
    "Revenue": "Revenue.csv",
    "Equipment": "Equipment.csv",
    "Personnel": "Personnel.csv",
    "Exams": "Exams.csv"
}

DEFAULT_JSON_FILE = "carescan_data.json"

def demonstrate_json_to_csv_sync():
    """
    Demonstrate how to load data from a JSON file and update corresponding CSV files.
    """
    print("Demonstrating JSON → CSV Synchronization")
    print("=" * 50)
    
    json_file = DEFAULT_JSON_FILE
    csv_mapping = DEFAULT_CSV_MAPPING
    
    # Check if the JSON file exists
    if not os.path.exists(json_file):
        print(f"JSON file {json_file} does not exist.")
        return
    
    try:
        # Perform the synchronization
        data_dict = sync_json_to_csv(json_file, csv_mapping)
        
        # Print the results
        print(f"Successfully loaded data from {json_file} and updated CSV files:")
        for key, df in data_dict.items():
            csv_file = csv_mapping.get(key)
            if csv_file:
                print(f"- {key}: {len(df)} records → {csv_file}")
    
    except Exception as e:
        print(f"Error during JSON → CSV synchronization: {str(e)}")

def demonstrate_csv_to_json_sync():
    """
    Demonstrate how to load data from CSV files and update a JSON file.
    """
    print("\nDemonstrating CSV → JSON Synchronization")
    print("=" * 50)
    
    csv_mapping = DEFAULT_CSV_MAPPING
    json_file = DEFAULT_JSON_FILE
    
    try:
        # Perform the synchronization
        data_dict = sync_csv_to_json(csv_mapping, json_file)
        
        # Print the results
        print(f"Successfully loaded data from CSV files and updated {json_file}:")
        for key, df in data_dict.items():
            print(f"- {key}: {len(df)} records from {csv_mapping.get(key)}")
    
    except Exception as e:
        print(f"Error during CSV → JSON synchronization: {str(e)}")

def streamlit_json_csv_sync_demo():
    """
    Demonstrate JSON-CSV synchronization within a Streamlit app.
    """
    st.title("JSON-CSV Data Synchronization Demo")
    
    st.write("""
    This demo shows how to keep CSV files and JSON data in sync in a Streamlit app.
    When you load a JSON file, the corresponding CSV files will be updated, and
    when you edit CSV data, the JSON file will be updated.
    """)
    
    # File path inputs
    st.subheader("File Paths")
    json_file = st.text_input("JSON File Path", DEFAULT_JSON_FILE)
    
    # Show CSV mappings
    st.subheader("CSV File Mappings")
    csv_mapping = {}
    for key in DEFAULT_CSV_MAPPING:
        csv_mapping[key] = st.text_input(f"{key} CSV File", DEFAULT_CSV_MAPPING[key])
    
    # Create two columns for the sync operations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("JSON → CSV Sync")
        if st.button("Sync JSON to CSV Files"):
            try:
                data_dict = sync_json_to_csv(json_file, csv_mapping)
                st.success(f"Successfully synchronized data from {json_file} to CSV files.")
                
                # Show data summary
                for key, df in data_dict.items():
                    st.write(f"- {key}: {len(df)} records")
            except Exception as e:
                st.error(f"Error during synchronization: {str(e)}")
    
    with col2:
        st.subheader("CSV → JSON Sync")
        if st.button("Sync CSV Files to JSON"):
            try:
                data_dict = sync_csv_to_json(csv_mapping, json_file)
                st.success(f"Successfully synchronized data from CSV files to {json_file}.")
                
                # Show data summary
                for key, df in data_dict.items():
                    st.write(f"- {key}: {len(df)} records")
            except Exception as e:
                st.error(f"Error during synchronization: {str(e)}")
    
    # Data preview
    st.subheader("Data Preview")
    selected_data = st.selectbox("Select data to preview", list(csv_mapping.keys()))
    
    try:
        # Try to load the CSV file
        if selected_data and os.path.exists(csv_mapping[selected_data]):
            df = load_csv(csv_mapping[selected_data])
            st.dataframe(df)
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")

def app_py_integration_example():
    """
    Example code snippets to integrate JSON-CSV synchronization into app.py.
    """
    print("\nExample Code Snippets for app.py Integration")
    print("=" * 50)
    
    print("""
# Import necessary functions
from financeModels.file_handler import sync_json_to_csv, sync_csv_to_json, load_csv, save_csv

# Define the CSV and JSON file mappings
CSV_FILES = {
    "Revenue": "Revenue.csv",
    "Equipment": "Equipment.csv",
    "Personnel": "Personnel.csv",
    "Exams": "Exams.csv"
}

JSON_FILE = "carescan_data.json"

# When importing from JSON, synchronize with CSV files
def import_json_and_sync_csvs(json_filepath):
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
        return False

# When exporting to JSON, ensure it's consistent with CSV files
def export_csvs_to_json(json_filepath):
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
        return False

# Add to the Export/Import tab:
with tabs[-1]:
    # ...existing code...
    
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
""")

if __name__ == "__main__":
    # Uncomment to run the examples
    # demonstrate_json_to_csv_sync()
    # demonstrate_csv_to_json_sync()
    app_py_integration_example()
    
    # For Streamlit, run this with:
    # streamlit run financeModels/json_csv_sync_example.py
    # streamlit_json_csv_sync_demo() 