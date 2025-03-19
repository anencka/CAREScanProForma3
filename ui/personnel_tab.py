"""
Personnel data tab for the CAREScan ProForma Editor.

This module contains the UI components and logic for the Personnel tab.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from typing import Dict, List, Tuple, Any, Optional
from datetime import date

from app_controller import AppController
from financeModels.personnel_expenses import PersonnelExpenseCalculator, calculate_personnel_expenses
from visualization import setup_plot_style, format_currency

def render_personnel_tab(st_obj):
    """
    Render the Personnel tab UI.
    
    Args:
        st_obj: Streamlit instance
    """
    st_obj.header("Personnel Data")
    
    # Information about editing
    st_obj.info(
        "Edit the data directly in the table below. "
        "For semicolon-separated lists, use commas or semicolons to separate values. "
        "For large numbers, you can use underscores for readability (e.g., 200_000 or 200000)."
    )
    
    # Load data
    personnel_df = AppController.get_dataframe("Personnel")
    
    if personnel_df is None or personnel_df.empty:
        st_obj.warning("No personnel data available. Please add personnel information.")
        # Create an empty DataFrame with the expected columns
        personnel_df = pd.DataFrame({
            "Name": [""],
            "Role": [""],
            "Type": [""],
            "Institution": [""],
            "Salary": [0],
            "Fringe_Rate": [0.0],
            "Effort": [1.0],
            "StartDate": ["01/01/2025"],
            "EndDate": [""],
            "Notes": [""]
        })
    
    # Convert string dates to datetime objects for the data editor
    try:
        if "StartDate" in personnel_df.columns:
            personnel_df["StartDate"] = pd.to_datetime(personnel_df["StartDate"], errors='coerce')
        if "EndDate" in personnel_df.columns and not personnel_df["EndDate"].empty:
            personnel_df["EndDate"] = pd.to_datetime(personnel_df["EndDate"], errors='coerce')
    except Exception as e:
        st_obj.warning(f"Could not convert date columns: {str(e)}")
    
    # Create a data editor with custom column configuration
    st_obj.subheader("Personnel Information")
    edited_df = st_obj.data_editor(
        personnel_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Name": st_obj.column_config.TextColumn(
                "Name",
                help="Name of the staff member"
            ),
            "Role": st_obj.column_config.TextColumn(
                "Role",
                help="Job role or title"
            ),
            "Type": st_obj.column_config.SelectboxColumn(
                "Type",
                help="Type of staff member",
                options=["Research", "Clinical", "Administrative", "Technical", "Other"],
                required=True
            ),
            "Institution": st_obj.column_config.TextColumn(
                "Institution",
                help="Affiliated institution"
            ),
            "Salary": st_obj.column_config.NumberColumn(
                "Annual Salary ($)",
                help="Annual salary amount",
                min_value=0,
                max_value=1000000,
                step=1000,
                format="$%d"
            ),
            "Fringe_Rate": st_obj.column_config.NumberColumn(
                "Fringe Rate",
                help="Fringe benefit rate (0.0 - 1.0)",
                min_value=0.0,
                max_value=1.0,
                step=0.01,
                format="%.2f"
            ),
            "Effort": st_obj.column_config.NumberColumn(
                "Effort (FTE)",
                help="Full Time Equivalent value (0.0 - 1.0)",
                min_value=0.0,
                max_value=1.0,
                step=0.1,
                format="%.2f"
            ),
            "StartDate": st_obj.column_config.DateColumn(
                "Start Date",
                help="Start date for this personnel",
                format="MM/DD/YYYY",
                min_value=date(2020, 1, 1),
                max_value=date(2050, 12, 31)
            ),
            "EndDate": st_obj.column_config.DateColumn(
                "End Date (Optional)",
                help="End date for this personnel (leave blank for no end date)",
                format="MM/DD/YYYY",
                min_value=date(2020, 1, 1),
                max_value=date(2050, 12, 31)
            ),
            "Notes": st_obj.column_config.TextColumn(
                "Notes",
                help="Additional information"
            )
        }
    )
    
    # Save changes if data was edited
    if not edited_df.equals(personnel_df):
        col1, col2 = st_obj.columns([1, 5])
        with col1:
            if st_obj.button("Save Personnel Data"):
                # Convert datetime objects back to string format before saving
                save_df = edited_df.copy()
                try:
                    if "StartDate" in save_df.columns:
                        save_df["StartDate"] = save_df["StartDate"].dt.strftime('%m/%d/%Y')
                    if "EndDate" in save_df.columns:
                        # Handle NaT values (empty dates)
                        save_df["EndDate"] = save_df["EndDate"].apply(
                            lambda x: x.strftime('%m/%d/%Y') if pd.notna(x) else ""
                        )
                except Exception as e:
                    st_obj.warning(f"Could not format date columns for saving: {str(e)}")
                
                save_result = AppController.save_dataframe("Personnel", save_df)
                if save_result:
                    st_obj.success("Personnel data saved successfully!")
                    personnel_df = edited_df
                else:
                    st_obj.error("Failed to save personnel data.")
    
    # Add a personnel expense visualization section
    st_obj.subheader("Personnel Expense Calculation")
    
    # Date range selection
    st_obj.write("##### Select Date Range")
    col1, col2 = st_obj.columns(2)
    with col1:
        start_date = st_obj.date_input(
            "Start Date", 
            value=pd.to_datetime("01/01/2025").date(),
            min_value=date(2020, 1, 1),
            max_value=date(2050, 12, 31),
            key="personnel_start_date"
        )
    with col2:
        end_date = st_obj.date_input(
            "End Date", 
            value=pd.to_datetime("12/31/2029").date(),
            min_value=date(2020, 1, 1),
            max_value=date(2050, 12, 31),
            key="personnel_end_date"
        )
    
    # Calculate button
    if st_obj.button("Calculate Personnel Expenses", key="calculate_personnel_expenses"):
        if personnel_df is None or personnel_df.empty:
            st_obj.error("No personnel data available. Please add personnel information above.")
        else:
            try:
                # Show spinner while calculating
                with st_obj.spinner("Calculating personnel expenses and generating plots..."):
                    # Convert dates to string format for the calculator
                    start_date_str = start_date.strftime("%m/%d/%Y")
                    end_date_str = end_date.strftime("%m/%d/%Y")
                    
                    # Calculate personnel expenses
                    results = calculate_personnel_expenses(
                        personnel_data=personnel_df,
                        start_date=start_date_str,
                        end_date=end_date_str
                    )
                    
                    # Store results
                    AppController.store_calculation_result("personnel_expenses", results)
                    
                    # Display results
                    render_personnel_results(st_obj, results, personnel_df, start_date, end_date)
            
            except Exception as e:
                import traceback
                st_obj.error(f"Error calculating personnel expenses: {str(e)}")
                st_obj.error(traceback.format_exc())

def render_personnel_results(st_obj, results, personnel_df, start_date, end_date):
    """
    Render the personnel expense calculation results.
    
    Args:
        st_obj: Streamlit instance
        results: Personnel expense calculation results
        personnel_df: Personnel data DataFrame
        start_date: Start date for calculations
        end_date: End date for calculations
    """
    # Display the first visualization - total expenses by year
    st_obj.subheader("Total Personnel Expenses by Year")
    annual_df = results['annual']
    
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    annual_totals = annual_df.groupby('Year')['Total_Expense'].sum()
    annual_totals.plot(kind='bar', color='skyblue', ax=ax1)
    ax1.set_title('Total Personnel Expenses by Year')
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Total Expense ($)')
    ax1.grid(axis='y', linestyle='--', alpha=0.7)
    ax1.tick_params(axis='x', rotation=0)
    
    # Format y-axis with dollar signs
    fmt = '${x:,.0f}'
    tick = mticker.StrMethodFormatter(fmt)
    ax1.yaxis.set_major_formatter(tick)
    
    st_obj.pyplot(fig1)
    
    # Display summary of annual expenses as a dataframe
    annual_table = annual_totals.reset_index()
    annual_table['Total_Expense'] = annual_table['Total_Expense'].map('${:,.2f}'.format)
    annual_table.columns = ['Year', 'Total Expense']
    st_obj.dataframe(annual_table, use_container_width=True)
    
    # Display visualization 2: Expenses by institution and type
    st_obj.subheader("Personnel Expenses by Institution and Type")
    category_df = results['by_category']
    
    fig2, ax2 = plt.subplots(figsize=(14, 7))
    pivot_df = category_df.pivot_table(
        index='Institution', 
        columns='Type', 
        values='Total_Expense',
        aggfunc='sum',
        fill_value=0
    )
    pivot_df.plot(kind='bar', stacked=True, colormap='viridis', ax=ax2)
    ax2.set_title('Personnel Expenses by Institution and Type')
    ax2.set_xlabel('Institution')
    ax2.set_ylabel('Total Expense ($)')
    ax2.grid(axis='y', linestyle='--', alpha=0.7)
    ax2.tick_params(axis='x', rotation=45)
    ax2.legend(title='Staff Type')
    
    # Format y-axis with dollar signs
    ax2.yaxis.set_major_formatter(tick)
    
    st_obj.pyplot(fig2)
    
    # Display summary of category expenses
    display_category = category_df.copy()
    # Format currency columns
    for col in ['Base_Expense', 'Fringe_Amount', 'Total_Expense']:
        if col in display_category.columns:
            display_category[col] = display_category[col].map('${:,.2f}'.format)
    
    st_obj.dataframe(display_category, use_container_width=True)
    
    # Display visualization 3: Headcount over time
    st_obj.subheader("FTE Count Over Time by Staff Type")
    headcount_df = results['headcount']
    
    # Create a date column for better plotting
    headcount_df['Date'] = pd.to_datetime(
        headcount_df['Year'].astype(str) + '-' + 
        headcount_df['Month'].astype(str) + '-01'
    )
    
    fig3, ax3 = plt.subplots(figsize=(14, 6))
    headcount_pivoted = headcount_df.pivot_table(
        index='Date', 
        columns='Type', 
        values='FTE_Count',
        aggfunc='sum',
        fill_value=0
    )
    headcount_pivoted.plot(kind='area', stacked=True, alpha=0.7, colormap='tab10', ax=ax3)
    ax3.set_title('FTE Count Over Time by Staff Type')
    ax3.set_xlabel('Date')
    ax3.set_ylabel('FTE Count')
    ax3.grid(linestyle='--', alpha=0.7)
    ax3.legend(title='Staff Type')
    st_obj.pyplot(fig3)
    
    # Display grand total
    st_obj.subheader("Grand Total")
    grand_total = results['grand_total']
    
    # Create metrics in columns
    col1, col2, col3 = st_obj.columns(3)
    with col1:
        st_obj.metric("Base Expense", f"${grand_total['Base_Expense']:,.2f}")
    with col2:
        st_obj.metric("Fringe Amount", f"${grand_total['Fringe_Amount']:,.2f}")
    with col3:
        st_obj.metric("Total Expense", f"${grand_total['Total_Expense']:,.2f}")
    
    # Display as a table as well
    formatted_grand_total = {
        'Base Expense': f"${grand_total['Base_Expense']:,.2f}",
        'Fringe Amount': f"${grand_total['Fringe_Amount']:,.2f}",
        'Total Expense': f"${grand_total['Total_Expense']:,.2f}"
    }
    
    st_obj.table(pd.DataFrame([formatted_grand_total])) 