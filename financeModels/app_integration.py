"""
Integration examples for using financeModels in Streamlit app.py.

This module provides examples and functions for integrating
the financeModels package with the main Streamlit application.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
from datetime import datetime, timedelta
import numpy as np
from financeModels.personnel_expenses import PersonnelExpenseCalculator, calculate_personnel_expenses

def display_personnel_expenses_dashboard(personnel_data: pd.DataFrame):
    """
    Create a Streamlit dashboard for personnel expenses analysis.
    
    Args:
        personnel_data: DataFrame containing personnel data
    """
    st.header("Personnel Expenses Analysis")
    
    # Create columns for date range selection
    col1, col2 = st.columns(2)
    
    # Get min and max dates from personnel data
    min_date = personnel_data['StartDate'].min() if 'StartDate' in personnel_data.columns else datetime.now()
    max_date = personnel_data['EndDate'].max() if 'EndDate' in personnel_data.columns else datetime.now() + timedelta(days=365*5)
    
    # Try to convert to datetime if they're not already
    if not isinstance(min_date, datetime):
        try:
            min_date = pd.to_datetime(min_date, format='%m/%d/%Y')
        except:
            min_date = datetime.now()
            
    if not isinstance(max_date, datetime):
        try:
            max_date = pd.to_datetime(max_date, format='%m/%d/%Y')
        except:
            max_date = datetime.now() + timedelta(days=365*5)
    
    # Convert to date objects for the date_input
    min_date = min_date.date() if hasattr(min_date, 'date') else datetime.now().date()
    max_date = max_date.date() if hasattr(max_date, 'date') else (datetime.now() + timedelta(days=365*5)).date()
    
    # Date selectors
    with col1:
        start_date = st.date_input(
            "Start Date",
            min_date,
            min_value=min_date,
            max_value=max_date
        )
    
    with col2:
        end_date = st.date_input(
            "End Date",
            max_date,
            min_value=min_date,
            max_value=max_date
        )
    
    # Convert dates to string format for the calculator
    start_date_str = start_date.strftime('%m/%d/%Y')
    end_date_str = end_date.strftime('%m/%d/%Y')
    
    # Create instance of calculator
    calculator = PersonnelExpenseCalculator(personnel_data=personnel_data)
    
    # Run calculations
    try:
        # Calculate and display results
        st.subheader("Personnel Expense Summary")
        
        # Display grand totals
        grand_total = calculator.calculate_grand_total(start_date_str, end_date_str)
        
        # Create three metrics in a row
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Base Salary", f"${grand_total['Base_Expense']:,.2f}")
        col2.metric("Total Fringe Benefits", f"${grand_total['Fringe_Amount']:,.2f}")
        col3.metric("Total Personnel Cost", f"${grand_total['Total_Expense']:,.2f}")
        
        # Display expenses by category
        st.subheader("Expenses by Staff Type and Institution")
        category_df = calculator.calculate_total_by_category(start_date_str, end_date_str)
        
        # Format for display
        display_df = category_df.copy()
        for col in ['Base_Expense', 'Fringe_Amount', 'Total_Expense']:
            display_df[col] = display_df[col].map('${:,.2f}'.format)
        
        st.dataframe(display_df)
        
        # Create visualization of expenses by category
        fig, ax = plt.subplots(figsize=(10, 6))
        pivot_df = category_df.pivot_table(
            index='Institution', 
            columns='Type', 
            values='Total_Expense',
            aggfunc='sum',
            fill_value=0
        )
        pivot_df.plot(kind='bar', stacked=True, colormap='viridis', ax=ax)
        plt.title('Personnel Expenses by Institution and Type')
        plt.xlabel('Institution')
        plt.ylabel('Total Expense ($)')
        plt.xticks(rotation=45)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.legend(title='Staff Type')
        plt.tight_layout()
        
        # Display the plot in Streamlit
        st.pyplot(fig)
        
        # Annual expenses tab
        st.subheader("Annual Personnel Expenses")
        annual_df = calculator.calculate_annual_expense(start_date_str, end_date_str)
        
        # Format for display
        annual_display_df = annual_df.copy()
        for col in ['Base_Expense', 'Fringe_Amount', 'Total_Expense']:
            annual_display_df[col] = annual_display_df[col].map('${:,.2f}'.format)
        
        st.dataframe(annual_display_df)
        
        # Create visualization of annual expenses
        fig, ax = plt.subplots(figsize=(10, 6))
        annual_totals = annual_df.groupby('Year')['Total_Expense'].sum()
        annual_totals.plot(kind='bar', color='skyblue', ax=ax)
        plt.title('Total Personnel Expenses by Year')
        plt.xlabel('Year')
        plt.ylabel('Total Expense ($)')
        plt.xticks(rotation=0)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        # Display the plot in Streamlit
        st.pyplot(fig)
        
        # Headcount visualization
        st.subheader("FTE Headcount Over Time")
        headcount_df = calculator.get_headcount_by_month(start_date_str, end_date_str)
        
        # Create a date column for better plotting
        headcount_df['Date'] = pd.to_datetime(
            headcount_df['Year'].astype(str) + '-' + 
            headcount_df['Month'].astype(str) + '-01'
        )
        
        # Create visualization of headcount
        fig, ax = plt.subplots(figsize=(12, 6))
        headcount_pivoted = headcount_df.pivot_table(
            index='Date', 
            columns='Type', 
            values='FTE_Count',
            aggfunc='sum',
            fill_value=0
        )
        headcount_pivoted.plot(kind='area', stacked=True, alpha=0.7, colormap='tab10', ax=ax)
        plt.title('FTE Count Over Time by Staff Type')
        plt.xlabel('Date')
        plt.ylabel('FTE Count')
        plt.grid(linestyle='--', alpha=0.7)
        plt.legend(title='Staff Type')
        plt.tight_layout()
        
        # Display the plot in Streamlit
        st.pyplot(fig)
        
        # Download buttons for detailed data
        st.subheader("Download Detailed Reports")
        
        # Monthly expenses download button
        monthly_df = calculator.calculate_monthly_expense(start_date_str, end_date_str)
        
        # Convert to Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            monthly_df.to_excel(writer, sheet_name='Monthly Detail', index=False)
            annual_df.to_excel(writer, sheet_name='Annual Summary', index=False)
            category_df.to_excel(writer, sheet_name='By Category', index=False)
            headcount_df.to_excel(writer, sheet_name='Headcount', index=False)
        
        excel_data = output.getvalue()
        
        # Download button for Excel data
        st.download_button(
            label="Download Excel Reports",
            data=excel_data,
            file_name=f"personnel_expenses_{start_date}_to_{end_date}.xlsx",
            mime="application/vnd.ms-excel"
        )
        
    except Exception as e:
        st.error(f"Error calculating personnel expenses: {str(e)}")
        import traceback
        st.error(traceback.format_exc())

def app_integration_example():
    """Example of how to use the personnel expenses functions in a Streamlit app"""
    st.title("Personnel Expenses Module Integration Example")
    
    # Load the personnel data
    try:
        personnel_data = pd.read_csv("Personnel.csv", skipinitialspace=True)
        
        # Process the data
        for date_col in ['StartDate', 'EndDate']:
            if date_col in personnel_data.columns:
                personnel_data[date_col] = pd.to_datetime(
                    personnel_data[date_col], 
                    format='%m/%d/%Y', 
                    errors='coerce'
                )
        
        # Display the dashboard
        display_personnel_expenses_dashboard(personnel_data)
        
    except Exception as e:
        st.error(f"Error loading personnel data: {str(e)}")
        import traceback
        st.error(traceback.format_exc())

if __name__ == "__main__":
    app_integration_example() 