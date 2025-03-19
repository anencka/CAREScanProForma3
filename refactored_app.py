"""
CAREScan ProForma Editor - Financial modeling and visualization application

This is the main entry point for the CAREScan ProForma application.
It uses modular components from the ui/ directory and the app_controller.py.
"""

import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
from financeModels.file_handler import load_csv, save_csv, load_json, save_json

# Import the controller
from app_controller import AppController, CSV_FILES

# Import UI modules (uncomment as they are created)
from ui.revenue_tab import render_revenue_tab
from ui.equipment_tab import render_equipment_tab
from ui.personnel_tab import render_personnel_tab
from ui.exams_tab import render_exams_tab
from ui.other_expenses_tab import render_other_expenses_tab
from ui.plots_tab import render_plots_tab
# from ui.comprehensive_tab import render_comprehensive_tab

# Set page configuration
st.set_page_config(
    page_title="CAREScan ProForma Editor",
    page_icon="📊",
    layout="wide"
)

# Initialize the application state
AppController.initialize_session_state()

# Add a reload data button in the sidebar
with st.sidebar:
    if st.button("🔄 Reload All Data"):
        # Reload all data from CSV files
        AppController.load_all_data()
        st.success("All data reloaded from CSV files!")
    
    # Add an about section
    st.sidebar.markdown("---")
    st.sidebar.header("About")
    st.sidebar.info(
        "This application is a financial modeling tool for CAREScan. "
        "It allows creating pro forma projections for imaging centers."
    )

# Load data if not already loaded
if 'dataframes' not in st.session_state or not st.session_state.dataframes:
    try:
        # Try to load from JSON first
        if os.path.exists("carescan_data.json"):
            AppController.load_from_json()
        else:
            # Fall back to CSV loading
            AppController.load_all_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        # Initialize empty dataframes
        st.session_state.dataframes = {}

# Create tabs
tabs = st.tabs([
    "Revenue", 
    "Equipment", 
    "Personnel", 
    "Exams",
    "Other Expenses",
    "Summary Plots",
    "Equipment Expense Plots",
    "Personnel Expense Plots",
    "Exam Revenue Analysis",
    "Comprehensive ProForma"
])

# Revenue tab
with tabs[0]:
    render_revenue_tab(st)

# Equipment tab
with tabs[1]:
    render_equipment_tab(st)

# Personnel tab
with tabs[2]:
    render_personnel_tab(st)

# Exams tab
with tabs[3]:
    render_exams_tab(st)

# Other Expenses tab
with tabs[4]:
    render_other_expenses_tab(st)

# Summary Plots tab
with tabs[5]:
    render_plots_tab(st)

# Equipment Expense Plots tab
with tabs[6]:
    st.header("Equipment Expense Plots")
    st.info(
        "This tab visualizes equipment expenses and depreciation based on the Equipment.csv data. "
        "It shows annual expenses by category, equipment depreciation over time, and total costs."
    )
    st.warning("Equipment Expense Plots has been integrated into the Equipment tab in this refactored version.")

# Personnel Expense Plots tab
with tabs[7]:
    st.header("Personnel Expense Plots")
    st.warning("Personnel Expense Plots has been integrated into the Personnel tab in this refactored version.")

# Exam Revenue Analysis tab
with tabs[8]:
    st.header("Exam Revenue Analysis")
    st.warning("Exam Revenue Analysis has been integrated into the Exams tab in this refactored version.")

# Comprehensive ProForma tab
with tabs[9]:
    st.header("Comprehensive ProForma")
    st.warning("Comprehensive ProForma tab module is not yet implemented in this refactored version.") 