"""
Controller module for the CAREScan ProForma Editor application.

This module manages the application state and provides functions to interact with
the financial models and data storage.
"""

import pandas as pd
import streamlit as st
from typing import Dict, List, Optional, Any

from financeModels.file_handler import (
    load_csv, save_csv, load_json, save_json,
    sync_json_to_csv, sync_csv_to_json,
    update_csv_from_dataframes, update_json_from_csvs
)

# Constants
CSV_FILES = {
    "Revenue": "Revenue.csv",
    "Equipment": "Equipment.csv",
    "Personnel": "Personnel.csv",
    "Exams": "Exams.csv",
    "OtherExpenses": "OtherExpenses.csv"
}

JSON_FILE = "carescan_data.json"

class AppController:
    """Controller class for managing app state and interactions."""
    
    @staticmethod
    def initialize_session_state():
        """Initialize or reset the session state with default values."""
        if 'dataframes' not in st.session_state:
            st.session_state.dataframes = {}
            
        if 'loaded_from' not in st.session_state:
            st.session_state.loaded_from = 'csv'  # or 'json'
            
        if 'calculation_results' not in st.session_state:
            st.session_state.calculation_results = {}
    
    @staticmethod
    def load_all_data():
        """Load all data from CSV files into session state."""
        AppController.initialize_session_state()
        
        for name, filepath in CSV_FILES.items():
            try:
                df = load_csv(filepath)
                st.session_state.dataframes[name] = df
            except Exception as e:
                st.error(f"Error loading {name}: {e}")
        
        st.session_state.loaded_from = 'csv'
        return st.session_state.dataframes
    
    @staticmethod
    def load_from_json():
        """Load all data from JSON file into session state."""
        try:
            data_dict = load_json(JSON_FILE)
            
            # If we got an empty dictionary, it means JSON loading failed
            if not data_dict:
                st.warning("Could not load data from JSON file. Falling back to CSV files.")
                return AppController.load_all_data()
            
            st.session_state.dataframes = data_dict
            st.session_state.loaded_from = 'json'
            return data_dict
        except Exception as e:
            st.warning(f"Error loading from JSON: {str(e)}. Falling back to CSV files.")
            # Fall back to CSV loading
            return AppController.load_all_data()
    
    @staticmethod
    def save_dataframe(name: str, df: pd.DataFrame) -> bool:
        """Save a DataFrame to both CSV and JSON storage."""
        if name not in CSV_FILES:
            st.error(f"Unknown data type: {name}")
            return False
        
        try:
            # Update session state
            st.session_state.dataframes[name] = df
            
            # Save to CSV
            save_result = save_csv(df, CSV_FILES[name])
            
            # Update JSON file
            json_result = save_json(st.session_state.dataframes, JSON_FILE)
            
            return save_result and json_result
        except Exception as e:
            st.error(f"Error saving {name}: {e}")
            return False
    
    @staticmethod
    def get_dataframe(name: str) -> Optional[pd.DataFrame]:
        """Get a DataFrame from the session state, loading if necessary."""
        AppController.initialize_session_state()
        
        if name not in st.session_state.dataframes:
            # Try to load from CSV
            if name in CSV_FILES:
                try:
                    df = load_csv(CSV_FILES[name])
                    st.session_state.dataframes[name] = df
                    return df
                except Exception as e:
                    st.error(f"Error loading {name}: {e}")
                    return None
            else:
                st.error(f"Unknown data type: {name}")
                return None
        
        return st.session_state.dataframes.get(name)
    
    @staticmethod
    def store_calculation_result(name: str, result: Any):
        """Store a calculation result in the session state."""
        AppController.initialize_session_state()
        st.session_state.calculation_results[name] = result
    
    @staticmethod
    def get_calculation_result(name: str) -> Optional[Any]:
        """Get a calculation result from the session state."""
        AppController.initialize_session_state()
        return st.session_state.calculation_results.get(name) 