"""
Other expenses tab for the CAREScan ProForma Editor.

This module contains the UI components and logic for the Other Expenses tab.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from typing import Dict, List, Tuple, Any, Optional
from datetime import date

from app_controller import AppController
from financeModels.other_expenses import OtherExpensesCalculator, calculate_other_expenses
from visualization import setup_plot_style, format_currency

def render_other_expenses_tab(st_obj):
    """
    Render the Other Expenses tab UI.
    
    Args:
        st_obj: Streamlit instance
    """
    st_obj.header("Other Expenses Data")
    
    # Information about editing
    st_obj.info(
        "Edit the data directly in the table below. "
        "This tab allows you to enter both expenses and revenue items. "
        "Use the 'Expense' checkbox to indicate whether an item is an expense (checked) or revenue (unchecked)."
    )
    
    # Load data
    other_expenses_df = AppController.get_dataframe("OtherExpenses")
    
    if other_expenses_df is None or other_expenses_df.empty:
        st_obj.warning("No other expenses data available. Please add expense information.")
        other_expenses_df = pd.DataFrame({
            "Title": [""],
            "Vendor": [""],
            "AppliedDate": ["01/01/2025"],
            "Amount": [0],
            "Expense": [True],
            "Description": [""]
        })
    
    # Convert string dates to datetime objects for the data editor
    try:
        if "AppliedDate" in other_expenses_df.columns:
            other_expenses_df["AppliedDate"] = pd.to_datetime(other_expenses_df["AppliedDate"], errors='coerce')
    except Exception as e:
        st_obj.warning(f"Could not convert date columns: {str(e)}")
    
    # Create data editor with custom column configuration
    st_obj.subheader("Other Expenses Information")
    edited_df = st_obj.data_editor(
        other_expenses_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Title": st_obj.column_config.TextColumn(
                "Title",
                help="Title or name of the expense/revenue item"
            ),
            "Vendor": st_obj.column_config.TextColumn(
                "Vendor",
                help="Name of the vendor or provider"
            ),
            "AppliedDate": st_obj.column_config.DateColumn(
                "Applied Date",
                help="Date when the expense/revenue is applied",
                format="MM/DD/YYYY",
                min_value=date(2020, 1, 1),
                max_value=date(2050, 12, 31)
            ),
            "Amount": st_obj.column_config.NumberColumn(
                "Amount ($)",
                help="Dollar amount (positive value)",
                min_value=0,
                max_value=10000000,
                step=100,
                format="$%d"
            ),
            "Expense": st_obj.column_config.CheckboxColumn(
                "Is Expense?",
                help="Check if this is an expense, uncheck if it's revenue"
            ),
            "Description": st_obj.column_config.TextColumn(
                "Description",
                help="Additional details about this item"
            )
        }
    )
    
    # Save changes if data was edited
    if not edited_df.equals(other_expenses_df):
        col1, col2 = st_obj.columns([1, 5])
        with col1:
            if st_obj.button("Save Changes"):
                # Convert datetime objects back to string format before saving
                save_df = edited_df.copy()
                try:
                    if "AppliedDate" in save_df.columns:
                        save_df["AppliedDate"] = save_df["AppliedDate"].dt.strftime('%m/%d/%Y')
                except Exception as e:
                    st_obj.warning(f"Could not format date columns for saving: {str(e)}")
                
                save_result = AppController.save_dataframe("OtherExpenses", save_df)
                if save_result:
                    st_obj.success("Other expenses data saved successfully!")
                    other_expenses_df = edited_df
                else:
                    st_obj.error("Failed to save other expenses data.")
    
    # Add visualization section
    st_obj.header("Other Expenses Analysis")
    
    # Date Range Selection
    st_obj.subheader("Select Date Range")
    col1, col2 = st_obj.columns(2)
    with col1:
        start_date = st_obj.date_input(
            "Start Date",
            value=pd.to_datetime("01/01/2025").date(),
            min_value=date(2020, 1, 1),
            max_value=date(2050, 12, 31),
            key="other_expenses_start_date"
        )
    with col2:
        end_date = st_obj.date_input(
            "End Date",
            value=pd.to_datetime("12/31/2029").date(),
            min_value=date(2020, 1, 1),
            max_value=date(2050, 12, 31),
            key="other_expenses_end_date"
        )
    
    # Calculate button
    if st_obj.button("Calculate Expenses and Generate Plots", key="calculate_other_expenses"):
        if other_expenses_df is None or other_expenses_df.empty:
            st_obj.error("No other expenses data available. Please add expense information above.")
        else:
            try:
                # Show spinner while calculating
                with st_obj.spinner("Calculating expenses and generating plots..."):
                    # Convert dates to string format for the calculator
                    start_date_str = start_date.strftime("%m/%d/%Y")
                    end_date_str = end_date.strftime("%m/%d/%Y")
                    
                    # Calculate other expenses
                    results = calculate_other_expenses(
                        other_data=other_expenses_df,
                        start_date=start_date_str,
                        end_date=end_date_str
                    )
                    
                    # Store results
                    AppController.store_calculation_result("other_expenses", results)
                    
                    # Display results
                    render_other_expenses_results(st_obj, results, other_expenses_df, start_date, end_date)
            
            except Exception as e:
                import traceback
                st_obj.error(f"Error calculating other expenses: {str(e)}")
                st_obj.error(traceback.format_exc())

def render_other_expenses_results(st_obj, results, other_expenses_df, start_date, end_date):
    """
    Render the other expenses calculation results.
    
    Args:
        st_obj: Streamlit instance
        results: Other expenses calculation results
        other_expenses_df: Other expenses data DataFrame
        start_date: Start date for calculations
        end_date: End date for calculations
    """
    # Extract results
    annual_items = results.get('annual_items', pd.DataFrame())
    category_data = results.get('by_category', pd.DataFrame())
    summary = results.get('summary', {})
    
    if annual_items.empty:
        st_obj.warning("No expenses or revenue items found in the selected date range.")
        return
    
    # Display summary metrics
    st_obj.subheader("Summary Metrics")
    col1, col2, col3 = st_obj.columns(3)
    with col1:
        st_obj.metric("Total Revenue", f"${summary.get('Total_Revenue', 0):,.2f}")
    with col2:
        st_obj.metric("Total Expenses", f"${summary.get('Total_Expenses', 0):,.2f}")
    with col3:
        st_obj.metric("Net Total", f"${summary.get('Net_Total', 0):,.2f}")
    
    # Create tabs for different visualizations
    viz_tabs = st_obj.tabs(["By Category", "By Year", "Expense vs Revenue", "Raw Data"])
    
    # By Category Visualization
    with viz_tabs[0]:
        st_obj.subheader("Expenses and Revenue by Category")
        
        # Prepare data for visualization
        if not category_data.empty:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Group data by Category (Expense or Revenue)
            by_category_totals = category_data.groupby('Category')['Amount'].sum()
            
            # Create bar chart
            by_category_totals.plot(kind='bar', ax=ax, color=['#FF6B6B', '#4ECB71'])
            
            for i, value in enumerate(by_category_totals):
                ax.text(i, value * 1.01, f'${value:,.0f}', ha='center')
            
            ax.set_title('Total Expenses vs Revenue')
            ax.set_ylabel('Amount ($)')
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            
            st_obj.pyplot(fig)
            
            # Now show breakdown by title within each category
            st_obj.subheader("Breakdown by Title")
            
            # Separate expenses and revenue for detailed visualizations
            expenses_df = category_data[category_data['Category'] == 'Expense']
            revenue_df = category_data[category_data['Category'] == 'Revenue']
            
            # Create visualization for expenses if there are any
            if not expenses_df.empty:
                st_obj.write("##### Expenses Breakdown")
                fig1, ax1 = plt.subplots(figsize=(12, 6))
                
                # Sort by amount descending
                expenses_df = expenses_df.sort_values('Amount', ascending=False)
                
                # Create horizontal bar chart
                bars = ax1.barh(expenses_df['Title'], expenses_df['Amount'], color='#FF6B6B')
                
                # Add amount labels
                for bar in bars:
                    width = bar.get_width()
                    ax1.text(width * 1.01, bar.get_y() + bar.get_height()/2, 
                           f'${width:,.0f}', va='center')
                
                ax1.set_title('Expenses by Title')
                ax1.set_xlabel('Amount ($)')
                ax1.grid(axis='x', linestyle='--', alpha=0.7)
                plt.tight_layout()
                
                st_obj.pyplot(fig1)
                
                # Display as table
                display_expenses = expenses_df.copy()
                display_expenses['Amount'] = display_expenses['Amount'].map('${:,.2f}'.format)
                st_obj.dataframe(display_expenses, use_container_width=True)
            
            # Create visualization for revenue if there are any
            if not revenue_df.empty:
                st_obj.write("##### Revenue Breakdown")
                
                # Check if required columns exist
                if 'Title' in revenue_df.columns and 'Amount' in revenue_df.columns:
                    fig2, ax2 = plt.subplots(figsize=(12, 6))
                    
                    # Sort by amount descending
                    revenue_df = revenue_df.sort_values('Amount', ascending=False)
                    
                    # Create horizontal bar chart
                    bars = ax2.barh(revenue_df['Title'], revenue_df['Amount'], color='#4ECB71')
                    
                    # Add amount labels
                    for bar in bars:
                        width = bar.get_width()
                        ax2.text(width * 1.01, bar.get_y() + bar.get_height()/2, 
                               f'${width:,.0f}', va='center')
                    
                    ax2.set_title('Revenue by Title')
                    ax2.set_xlabel('Amount ($)')
                    ax2.grid(axis='x', linestyle='--', alpha=0.7)
                    plt.tight_layout()
                    
                    st_obj.pyplot(fig2)
                    
                    # Display as table
                    display_revenue = revenue_df.copy()
                    display_revenue['Amount'] = display_revenue['Amount'].map('${:,.2f}'.format)
                    st_obj.dataframe(display_revenue, use_container_width=True)
                else:
                    st_obj.warning("Cannot create revenue visualization: missing required columns (Title and/or Amount)")
                    st_obj.write("Available columns:", list(revenue_df.columns))
                    # Show sample data
                    st_obj.dataframe(revenue_df.head(5))
        else:
            st_obj.warning("No data available for the selected date range.")
    
    # By Year Visualization
    with viz_tabs[1]:
        st_obj.subheader("Expenses and Revenue by Year")
        
        if not annual_items.empty:
            # Group data by year and category
            yearly_data = annual_items.groupby(['Year', 'Category'])['Amount'].sum().unstack()
            
            # Handle if either Expense or Revenue columns are missing
            if 'Expense' not in yearly_data.columns:
                yearly_data['Expense'] = 0
            if 'Revenue' not in yearly_data.columns:
                yearly_data['Revenue'] = 0
            
            # Create visualization
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Plot bars
            yearly_data.plot(kind='bar', ax=ax, color=['#FF6B6B', '#4ECB71'])
            
            # Add data labels
            for i, year_data in enumerate(yearly_data.iterrows()):
                year, amounts = year_data
                for j, amount in enumerate(amounts):
                    if amount > 0:  # Only add labels to non-zero amounts
                        ax.text(i + (j * 0.2 - 0.1), amount * 1.01, f'${amount:,.0f}', 
                               ha='center', va='bottom', rotation=0, fontsize=8)
            
            ax.set_title('Expenses and Revenue by Year')
            ax.set_ylabel('Amount ($)')
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            
            st_obj.pyplot(fig)
            
            # Display as table
            display_yearly = yearly_data.reset_index()
            for col in display_yearly.columns:
                if col != 'Year':
                    display_yearly[col] = display_yearly[col].map('${:,.2f}'.format)
            st_obj.dataframe(display_yearly, use_container_width=True)
        else:
            st_obj.warning("No data available for the selected date range.")
    
    # Expense vs Revenue Timeline
    with viz_tabs[2]:
        st_obj.subheader("Expense vs Revenue Timeline")
        
        if not annual_items.empty:
            # Group by year, month, and category
            timeline_data = annual_items.groupby(['Year', 'Month', 'Category'])['Amount'].sum().unstack().reset_index()
            
            # Create a date column for better plotting
            timeline_data['Date'] = pd.to_datetime(
                timeline_data['Year'].astype(str) + '-' + 
                timeline_data['Month'].astype(str) + '-01'
            )
            
            # Sort by date
            timeline_data = timeline_data.sort_values('Date')
            
            # Handle if either Expense or Revenue columns are missing
            if 'Expense' not in timeline_data.columns:
                timeline_data['Expense'] = 0
            if 'Revenue' not in timeline_data.columns:
                timeline_data['Revenue'] = 0
            
            # Calculate net value
            timeline_data['Net'] = timeline_data['Revenue'] - timeline_data['Expense']
            
            # Create visualization
            fig, ax = plt.subplots(figsize=(14, 7))
            
            # Plot lines with markers
            timeline_data.plot(
                x='Date', 
                y=['Expense', 'Revenue', 'Net'], 
                ax=ax, 
                marker='o',
                color=['#FF6B6B', '#4ECB71', '#007BFF'],
                linewidth=2
            )
            
            ax.set_title('Expense vs Revenue Timeline')
            ax.set_xlabel('Date')
            ax.set_ylabel('Amount ($)')
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.legend(['Expenses', 'Revenue', 'Net'])
            
            # Format y-axis with dollar signs
            formatter = mticker.FuncFormatter(lambda x, p: f"${x:,.0f}")
            ax.yaxis.set_major_formatter(formatter)
            
            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            st_obj.pyplot(fig)
            
            # Display as table
            display_timeline = timeline_data.copy()
            display_timeline['Date'] = display_timeline['Date'].dt.strftime('%b %Y')
            for col in ['Expense', 'Revenue', 'Net']:
                display_timeline[col] = display_timeline[col].map('${:,.2f}'.format)
            display_timeline = display_timeline.drop(['Year', 'Month'], axis=1)
            st_obj.dataframe(display_timeline, use_container_width=True)
        else:
            st_obj.warning("No data available for the selected date range.")
    
    # Raw Data
    with viz_tabs[3]:
        st_obj.subheader("Raw Data")
        
        if not annual_items.empty:
            # Format the data for display
            display_data = annual_items.copy()
            
            # Format amount column
            display_data['Amount'] = display_data['Amount'].map('${:,.2f}'.format)
            
            # Add a formatted date column
            if 'Year' in display_data.columns and 'Month' in display_data.columns:
                display_data['Date'] = pd.to_datetime(
                    display_data['Year'].astype(str) + '-' + 
                    display_data['Month'].astype(str) + '-01'
                ).dt.strftime('%b %Y')
            
            # Reorder columns for better display
            column_order = ['Title', 'Vendor', 'Date', 'Year', 'Month', 'Amount', 'Category', 'Description']
            display_columns = [col for col in column_order if col in display_data.columns]
            
            st_obj.dataframe(display_data[display_columns], use_container_width=True)
        else:
            st_obj.warning("No data available for the selected date range.") 