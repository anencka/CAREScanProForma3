"""
Equipment expenses tab for the CAREScan ProForma Editor.

This module contains the UI components and logic for the Equipment tab.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from typing import Dict, List, Tuple, Any, Optional
from datetime import date

from app_controller import AppController
from financeModels.equipment_expenses import EquipmentExpenseCalculator, calculate_equipment_expenses
from visualization import create_equipment_expenses_plot, setup_plot_style, format_currency

def render_equipment_tab(st_obj):
    """
    Render the Equipment tab UI.
    
    Args:
        st_obj: Streamlit instance
    """
    st_obj.header("Equipment Expenses")
    
    # Explanation of this tab
    st_obj.info(
        "This tab allows you to edit equipment data and calculate depreciation expenses. "
        "Enter equipment information including purchase dates, costs, and useful life."
    )
    
    # Load data
    equipment_df = AppController.get_dataframe("Equipment")
    
    if equipment_df is None or equipment_df.empty:
        st_obj.warning("No equipment data available. Please add equipment information.")
        equipment_df = pd.DataFrame({
            "Equipment": [""],
            "Purchase_Date": ["01/01/2025"],
            "Cost": [0],
            "Useful_Life": [5],
            "Notes": [""]
        })
    
    # Convert string dates to datetime objects for the data editor
    try:
        if "Purchase_Date" in equipment_df.columns:
            equipment_df["Purchase_Date"] = pd.to_datetime(equipment_df["Purchase_Date"], errors='coerce')
    except Exception as e:
        st_obj.warning(f"Could not convert date columns: {str(e)}")
    
    # Create data editor
    st_obj.subheader("Equipment Data")
    edited_df = st_obj.data_editor(
        equipment_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Equipment": st_obj.column_config.TextColumn(
                "Equipment Name",
                help="Name or description of the equipment"
            ),
            "Purchase_Date": st_obj.column_config.DateColumn(
                "Purchase Date",
                help="Date of purchase or planned purchase",
                format="MM/DD/YYYY",
                min_value=date(2020, 1, 1),
                max_value=date(2050, 12, 31)
            ),
            "Cost": st_obj.column_config.NumberColumn(
                "Cost ($)",
                help="Total cost of equipment including installation",
                min_value=0,
                max_value=10000000,
                step=1000,
                format="$%d"
            ),
            "Useful_Life": st_obj.column_config.NumberColumn(
                "Useful Life (Years)",
                help="Expected useful life in years for depreciation",
                min_value=1,
                max_value=30,
                step=1
            ),
            "Notes": st_obj.column_config.TextColumn(
                "Notes",
                help="Additional information about this equipment"
            )
        }
    )
    
    # Save changes if data was edited
    if not edited_df.equals(equipment_df):
        if st_obj.button("Save Equipment Changes"):
            # Convert datetime objects back to string format before saving
            save_df = edited_df.copy()
            try:
                if "Purchase_Date" in save_df.columns:
                    save_df["Purchase_Date"] = save_df["Purchase_Date"].dt.strftime('%m/%d/%Y')
            except Exception as e:
                st_obj.warning(f"Could not format date columns for saving: {str(e)}")
            
            save_result = AppController.save_dataframe("Equipment", save_df)
            if save_result:
                st_obj.success("Equipment data saved successfully!")
                equipment_df = edited_df
            else:
                st_obj.error("Failed to save equipment data.")
    
    # Create a form for equipment expense calculations
    st_obj.subheader("Equipment Expense Calculation")
    
    # Date Range Selection
    st_obj.write("##### Select Date Range")
    col1, col2 = st_obj.columns(2)
    with col1:
        start_date = st_obj.date_input(
            "Start Date",
            value=pd.to_datetime("01/01/2025").date(),
            min_value=date(2020, 1, 1),
            max_value=date(2050, 12, 31),
            key="equipment_start_date"
        )
    with col2:
        end_date = st_obj.date_input(
            "End Date",
            value=pd.to_datetime("12/31/2029").date(),
            min_value=date(2020, 1, 1),
            max_value=date(2050, 12, 31),
            key="equipment_end_date"
        )
    
    # Travel parameters
    st_obj.write("##### Travel Parameters")
    travel_col1, travel_col2 = st_obj.columns(2)
    with travel_col1:
        days_between_travel = st_obj.number_input(
            "Days Between Travel",
            min_value=1,
            max_value=30,
            value=5,
            help="Number of days between travel events",
            key="equipment_days_between_travel"
        )
    with travel_col2:
        miles_per_travel = st_obj.number_input(
            "Miles Per Travel",
            min_value=1,
            max_value=100,
            value=20,
            help="Number of miles traveled in each travel event",
            key="equipment_miles_per_travel"
        )
    
    # Depreciation method selection
    st_obj.write("##### Depreciation Method")
    depreciation_method = st_obj.selectbox(
        "Depreciation Method",
        options=["Straight Line", "Double Declining Balance"],
        index=0,
        key="equipment_depreciation_method"
    )
    
    # Calculate button
    if st_obj.button("Calculate Equipment Expenses", key="calculate_equipment_expenses"):
        try:
            # Show spinner while calculating
            with st_obj.spinner("Calculating equipment expenses and generating plots..."):
                # Convert dates to string format for the calculator
                start_date_str = start_date.strftime("%m/%d/%Y")
                end_date_str = end_date.strftime("%m/%d/%Y")
                
                # Calculate equipment expenses - passing parameters directly instead of as a dictionary
                results = calculate_equipment_expenses(
                    equipment_data=equipment_df,
                    start_date=start_date_str,
                    end_date=end_date_str,
                    days_between_travel=days_between_travel,
                    miles_per_travel=miles_per_travel,
                    depreciation_method=depreciation_method
                )
                
                # Store results
                AppController.store_calculation_result("equipment_expenses", results)
                
                # Display results
                render_equipment_results(st_obj, results, equipment_df, start_date, end_date)
        
        except Exception as e:
            import traceback
            st_obj.error(f"Error calculating equipment expenses: {str(e)}")
            st_obj.error(traceback.format_exc())

def render_equipment_results(st_obj, results, equipment_df, start_date, end_date):
    """
    Render the equipment expense calculation results.
    
    Args:
        st_obj: Streamlit instance
        results: Equipment expense calculation results
        equipment_df: Equipment data DataFrame
        start_date: Start date for calculations
        end_date: End date for calculations
    """
    # Extract results
    annual_expenses = results.get('annual', pd.DataFrame())
    expenses_by_equipment = results.get('by_equipment', pd.DataFrame())
    grand_total = results.get('grand_total', {})
    
    # Create yearly expenses from annual data if not empty
    if not annual_expenses.empty and 'Year' in annual_expenses.columns:
        yearly_expenses = annual_expenses.groupby('Year').sum().reset_index()
    else:
        yearly_expenses = pd.DataFrame()
    
    if annual_expenses.empty:
        st_obj.warning("No equipment expenses found in the selected date range.")
        return
    
    # Display key metrics
    st_obj.subheader("Key Metrics Summary")
    
    # Display total metrics in columns
    metric_col1, metric_col2, metric_col3 = st_obj.columns(3)
    with metric_col1:
        st_obj.metric("Total Purchase Cost", f"${grand_total.get('TotalPurchaseCost', 0):,.2f}")
    with metric_col2:
        st_obj.metric("Total Depreciation", f"${grand_total.get('TotalDepreciation', 0):,.2f}")
    with metric_col3:
        st_obj.metric("Total Annual Expenses", f"${grand_total.get('TotalAnnualExpense', 0):,.2f}")
    
    # Display recurring expenses in columns
    expense_col1, expense_col2, expense_col3, expense_col4 = st_obj.columns(4)
    with expense_col1:
        st_obj.metric("Service Costs", f"${grand_total.get('TotalServiceCost', 0):,.2f}")
    with expense_col2:
        st_obj.metric("Accreditation Costs", f"${grand_total.get('TotalAccreditationCost', 0):,.2f}")
    with expense_col3:
        st_obj.metric("Insurance Costs", f"${grand_total.get('TotalInsuranceCost', 0):,.2f}")
    with expense_col4:
        st_obj.metric("Travel Costs", f"${grand_total.get('TotalTravelExpense', 0):,.2f}")
    
    # Display equipment summary table
    st_obj.subheader("Equipment Expense Summary")
    
    # Format the table for display
    display_df = expenses_by_equipment.copy()
    for col in ['PurchaseCost', 'AnnualDepreciation', 'ServiceCost', 
              'AccreditationCost', 'InsuranceCost', 'TravelExpense', 'TotalAnnualExpense']:
        if col in display_df.columns:
            display_df[col] = display_df[col].map('${:,.2f}'.format)
    
    st_obj.dataframe(display_df)
    
    # 1. Annual Expenses by Equipment Type
    st_obj.subheader("Annual Expenses by Equipment Type")
    
    if 'Title' in annual_expenses.columns:
        fig1, ax1 = plt.subplots(figsize=(12, 6))
        
        # Plot stacked bar chart of expenses by equipment type
        pivot_df = annual_expenses.pivot_table(
            index='Title',
            values=['ServiceCost', 'AccreditationCost', 'InsuranceCost', 'TravelExpense'],
            aggfunc='sum'
        )
        
        pivot_df.plot(kind='bar', stacked=True, ax=ax1)
        ax1.set_title('Annual Expenses by Equipment Type')
        ax1.set_xlabel('Equipment')
        ax1.set_ylabel('Annual Expense ($)')
        ax1.grid(axis='y', linestyle='--', alpha=0.7)
        plt.xticks(rotation=45)
        plt.tight_layout()
        st_obj.pyplot(fig1)
    
    # 2. Annual Depreciation by Equipment Type
    st_obj.subheader("Annual Depreciation by Equipment Type")
    
    if 'Title' in expenses_by_equipment.columns and 'AnnualDepreciation' in expenses_by_equipment.columns:
        fig2, ax2 = plt.subplots(figsize=(12, 6))
        
        # Plot bar chart of annual depreciation
        depreciation_by_equipment = expenses_by_equipment.set_index('Title')['AnnualDepreciation']
        depreciation_by_equipment.plot(kind='bar', ax=ax2, color='skyblue')
        ax2.set_title('Annual Depreciation by Equipment Type')
        ax2.set_xlabel('Equipment')
        ax2.set_ylabel('Annual Depreciation ($)')
        ax2.grid(axis='y', linestyle='--', alpha=0.7)
        
        for i, v in enumerate(depreciation_by_equipment):
            ax2.text(i, v + 0.1, f"${v:,.0f}", ha='center')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        st_obj.pyplot(fig2)
    
    # 3. Annual Expenses Over Time
    st_obj.subheader("Equipment Expenses Over Time")
    
    if 'Year' in annual_expenses.columns:
        # Group expenses by year
        yearly_expenses = annual_expenses.groupby('Year').agg({
            'ServiceCost': 'sum',
            'AccreditationCost': 'sum',
            'InsuranceCost': 'sum',
            'TravelExpense': 'sum',
            'AnnualDepreciation': 'sum',
            'TotalAnnualExpense': 'sum'
        })
        
        # Create line chart of expenses over time
        fig3, ax3 = plt.subplots(figsize=(12, 6))
        
        # Use distinct colors, line styles, and markers for each expense type
        yearly_expenses['ServiceCost'].plot(
            kind='line', 
            marker='o',
            ax=ax3,
            linewidth=3,
            color='darkblue',
            label='Service Cost'
        )
        
        yearly_expenses['AccreditationCost'].plot(
            kind='line', 
            marker='s',
            ax=ax3,
            linewidth=3,
            linestyle='--',
            color='darkgreen',
            label='Accreditation Cost'
        )
        
        yearly_expenses['InsuranceCost'].plot(
            kind='line', 
            marker='^',
            ax=ax3,
            linewidth=3,
            linestyle=':',
            color='darkred',
            label='Insurance Cost'
        )
        
        yearly_expenses['TravelExpense'].plot(
            kind='line', 
            marker='d',
            ax=ax3,
            linewidth=3,
            linestyle='-.',
            color='darkorange',
            label='Travel Expense'
        )
        
        yearly_expenses['AnnualDepreciation'].plot(
            kind='line', 
            marker='x',
            ax=ax3,
            linewidth=3,
            color='purple',
            label='Annual Depreciation'
        )
        
        ax3.set_title('Equipment Expenses Over Time')
        ax3.set_xlabel('Year')
        ax3.set_ylabel('Expense Amount ($)')
        ax3.grid(True, linestyle='--', alpha=0.7)
        
        # Format y-axis with dollar signs
        fmt = '${x:,.0f}'
        tick = mticker.StrMethodFormatter(fmt)
        ax3.yaxis.set_major_formatter(tick)
        
        # Ensure legend is visible and clear
        ax3.legend(loc='best', frameon=True, fancybox=True, shadow=True)
        
        # Add data labels to the end points for better readability
        for column in ['ServiceCost', 'AccreditationCost', 'InsuranceCost', 'TravelExpense', 'AnnualDepreciation']:
            last_year = yearly_expenses.index[-1]
            last_value = yearly_expenses.loc[last_year, column]
            ax3.annotate(f'${last_value:,.0f}', 
                        xy=(last_year, last_value),
                        xytext=(10, 0),
                        textcoords='offset points',
                        va='center')
        
        plt.tight_layout()
        st_obj.pyplot(fig3)
        
        # Format and display the yearly expenses table with dollar formatting
        display_yearly = yearly_expenses.reset_index().copy()
        for col in display_yearly.columns:
            if col != 'Year':
                display_yearly[col] = display_yearly[col].map('${:,.2f}'.format)
        
        st_obj.dataframe(display_yearly)
        
        # 4. Total Annual Cost vs. Depreciation
        st_obj.subheader("Total Annual Cost vs. Depreciation")
        
        fig4, ax4 = plt.subplots(figsize=(12, 6))
        
        # Create a new DataFrame with just Annual Expenses and Depreciation
        cost_vs_depreciation = pd.DataFrame({
            'Annual Expenses': yearly_expenses['TotalAnnualExpense'],
            'Annual Depreciation': yearly_expenses['AnnualDepreciation']
        })
        
        cost_vs_depreciation.plot(kind='bar', ax=ax4)
        ax4.set_title('Total Annual Cost vs. Depreciation')
        ax4.set_xlabel('Year')
        ax4.set_ylabel('Amount ($)')
        ax4.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        st_obj.pyplot(fig4) 