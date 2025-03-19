"""
Summary plots tab for the CAREScan ProForma Editor.

This module contains the UI components and logic for the Summary Plots tab,
which provides an overview of the financial data from various sources.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from typing import Dict, List, Tuple, Any, Optional
from datetime import date

from app_controller import AppController
from financeModels.equipment_expenses import calculate_equipment_expenses
from financeModels.personnel_expenses import calculate_personnel_expenses
from financeModels.exam_revenue import calculate_exam_revenue, ExamRevenueCalculator
from financeModels.other_expenses import calculate_other_expenses
from visualization import setup_plot_style, format_currency

def render_plots_tab(st_obj):
    """
    Render the Summary Plots tab UI.
    
    Args:
        st_obj: Streamlit instance
    """
    st_obj.header("Summary Plots")
    
    # Information about this tab
    st_obj.info(
        "This tab provides consolidated visualizations of all financial data. "
        "It combines revenue, expenses, personnel costs, and equipment costs into comprehensive financial charts."
    )
    
    # Date Range Selection
    st_obj.subheader("Select Date Range")
    col1, col2 = st_obj.columns(2)
    with col1:
        start_date = st_obj.date_input(
            "Start Date",
            value=pd.to_datetime("01/01/2025").date(),
            min_value=date(2020, 1, 1),
            max_value=date(2050, 12, 31),
            key="summary_start_date"
        )
    with col2:
        end_date = st_obj.date_input(
            "End Date",
            value=pd.to_datetime("12/31/2029").date(),
            min_value=date(2020, 1, 1),
            max_value=date(2050, 12, 31),
            key="summary_end_date"
        )
    
    # Calculate button
    if st_obj.button("Generate Summary Plots", key="generate_summary_plots"):
        try:
            # Show spinner while calculating
            with st_obj.spinner("Calculating financial data and generating plots..."):
                # Check data availability
                data_available = check_data_availability(st_obj)
                
                if data_available:
                    # Convert dates to string format for the calculators
                    start_date_str = start_date.strftime("%m/%d/%Y")
                    end_date_str = end_date.strftime("%m/%d/%Y")
                    
                    # Generate summary results
                    results = generate_summary_data(st_obj, start_date_str, end_date_str)
                    
                    # Store results
                    AppController.store_calculation_result("summary_plots", results)
                    
                    # Display results
                    render_summary_results(st_obj, results, start_date, end_date)
                else:
                    st_obj.error("Cannot generate summary plots. Please ensure all required data is available.")
        
        except Exception as e:
            import traceback
            st_obj.error(f"Error generating summary plots: {str(e)}")
            st_obj.error(traceback.format_exc())

def check_data_availability(st_obj):
    """
    Check if all necessary data is available for generating summary plots.
    
    Args:
        st_obj: Streamlit instance
        
    Returns:
        bool: True if all required data is available, False otherwise
    """
    required_data = ["Revenue", "Equipment", "Personnel", "Exams", "OtherExpenses"]
    missing_data = []
    
    for data_name in required_data:
        df = AppController.get_dataframe(data_name)
        if df is None or df.empty:
            missing_data.append(data_name)
    
    if missing_data:
        st_obj.warning(f"The following data is missing or empty: {', '.join(missing_data)}")
        st_obj.info("You can still generate plots with partial data, but some charts may be incomplete.")
        return True  # Allow generating plots with partial data
    
    return True

def generate_summary_data(st_obj, start_date: str, end_date: str) -> Dict:
    """
    Generate summary data for all financial aspects.
    
    Args:
        st_obj: Streamlit instance
        start_date: Start date in format 'MM/DD/YYYY'
        end_date: End date in format 'MM/DD/YYYY'
        
    Returns:
        Dictionary containing all financial summary data
    """
    results = {}
    total_revenue = 0
    
    # Extract years from dates for calculations
    start_year = pd.to_datetime(start_date, format='%m/%d/%Y').year
    end_year = pd.to_datetime(end_date, format='%m/%d/%Y').year
    
    # We'll combine revenue from multiple sources
    st_obj.info("Gathering revenue data from available sources...")
    
    # 1. Check traditional Revenue.csv (which might not have the right schema)
    revenue_df = AppController.get_dataframe("Revenue")
    if revenue_df is not None and not revenue_df.empty:
        # Check if 'Amount' column exists
        if 'Amount' in revenue_df.columns:
            results['revenue_total'] = revenue_df['Amount'].sum()
            total_revenue += results['revenue_total']
            st_obj.success(f"Added ${results['revenue_total']:,.2f} from Revenue sources")
        else:
            st_obj.warning("Revenue data schema mismatch: 'Amount' column not found. Exploring alternative revenue sources.")
            results['revenue_total'] = 0
    else:
        results['revenue_total'] = 0
        st_obj.warning("No standard revenue data available. Exploring alternative revenue sources.")
    
    # 2. Calculate exam revenue if available (this is a major revenue source)
    exams_df = AppController.get_dataframe("Exams")
    if exams_df is not None and not exams_df.empty:
        try:
            from financeModels.exam_revenue import ExamRevenueCalculator
            
            # Get needed data
            personnel_df = AppController.get_dataframe("Personnel")
            equipment_df = AppController.get_dataframe("Equipment")
            
            # Initialize the calculator (following pattern from exams_tab.py)
            calculator = ExamRevenueCalculator(
                exams_data=exams_df,
                revenue_data=revenue_df if revenue_df is not None else pd.DataFrame(),
                personnel_data=personnel_df if personnel_df is not None else pd.DataFrame(),
                equipment_data=equipment_df if equipment_df is not None else pd.DataFrame(),
                start_date=start_date
            )
            
            # Calculate exam revenue for all available sources
            # We don't know which sources to include, so include all
            revenue_sources = None
            if revenue_df is not None and 'Title' in revenue_df.columns:
                revenue_sources = revenue_df['Title'].tolist()
            
            # Calculate exam revenue
            exam_results = calculator.calculate_multi_year_exam_revenue(
                start_year=start_year,
                end_year=end_year,
                revenue_sources=revenue_sources,
                work_days_per_year=252
            )
            
            results['exam_revenue'] = {}

            # Process the exam_results DataFrame
            if not exam_results.empty:
                # Store the raw exam results
                results['exam_revenue']['raw_data'] = exam_results
                
                # Create an annual summary from the raw data
                annual_summary = exam_results.groupby('Year').agg({
                    'AnnualVolume': 'sum',
                    'Total_Revenue': 'sum',
                    'Total_Direct_Expenses': 'sum',
                    'Net_Revenue': 'sum'
                }).reset_index()
                
                results['exam_revenue']['annual_summary'] = annual_summary
                
                # Add exam revenue to the total revenue
                exam_total_revenue = annual_summary['Total_Revenue'].sum()
                total_revenue += exam_total_revenue
                st_obj.success(f"Added ${exam_total_revenue:,.2f} from Exam Revenue")
            else:
                results['exam_revenue'] = {'annual_summary': pd.DataFrame(), 'raw_data': pd.DataFrame()}
                st_obj.warning("No exam revenue data could be calculated for the selected period. This might be because there is no equipment or required staff available.")
            
        except Exception as e:
            import traceback
            st_obj.warning(f"Could not calculate exam revenue: {str(e)}")
            st_obj.error(traceback.format_exc())
    else:
        results['exam_revenue'] = {}
        st_obj.warning("No exam data available for revenue calculations")
    
    # 3. Get revenue from other expenses (some might be revenue items)
    other_expenses_df = AppController.get_dataframe("OtherExpenses")
    if other_expenses_df is not None and not other_expenses_df.empty:
        try:
            # OtherExpenses.csv has 'Expense' column (boolean) instead of 'IsExpense'
            # and 'AppliedDate' instead of 'Year'
            expense_column_name = None
            date_column_name = None
            
            # Check available columns
            if 'Expense' in other_expenses_df.columns:
                expense_column_name = 'Expense'
            elif 'IsExpense' in other_expenses_df.columns:
                expense_column_name = 'IsExpense'
                
            if 'Year' in other_expenses_df.columns:
                date_column_name = 'Year'
            elif 'AppliedDate' in other_expenses_df.columns:
                date_column_name = 'AppliedDate'
                # Convert dates to years if we have dates
                if 'AppliedDate' in other_expenses_df.columns:
                    other_expenses_df['Year'] = pd.to_datetime(
                        other_expenses_df['AppliedDate'], 
                        errors='coerce'
                    ).dt.year
                    date_column_name = 'Year'
            
            if expense_column_name and date_column_name and 'Amount' in other_expenses_df.columns:
                # Filter only revenue items (not expenses)
                # For 'Expense' column, False means revenue
                # For 'IsExpense' column, False means revenue
                if expense_column_name == 'Expense':
                    revenue_items = other_expenses_df[~other_expenses_df['Expense'].astype(bool)]
                else:
                    revenue_items = other_expenses_df[~other_expenses_df['IsExpense']]
                
                if not revenue_items.empty:
                    # Filter by date range
                    filtered_items = revenue_items[
                        (revenue_items[date_column_name] >= start_year) & 
                        (revenue_items[date_column_name] <= end_year)
                    ]
                    
                    if not filtered_items.empty:
                        other_revenue_total = filtered_items['Amount'].sum()
                        total_revenue += other_revenue_total
                        st_obj.success(f"Added ${other_revenue_total:,.2f} from Other Revenue items")
            else:
                st_obj.warning(f"Other Expenses data missing required columns for revenue calculation. Found: {list(other_expenses_df.columns)}")
                
            # Calculate other expenses normally
            other_expenses_results = calculate_other_expenses(
                other_data=other_expenses_df,
                start_date=start_date,
                end_date=end_date
            )
            results['other_expenses'] = other_expenses_results
            
        except Exception as e:
            st_obj.warning(f"Could not calculate other expenses revenue: {str(e)}")
            results['other_expenses'] = {}
    else:
        results['other_expenses'] = {}
        st_obj.warning("No other expenses data available for revenue calculations")
    
    # Store the combined total revenue
    results['combined_revenue_total'] = total_revenue
    
    # Calculate equipment expenses if available
    equipment_df = AppController.get_dataframe("Equipment")
    if equipment_df is not None and not equipment_df.empty:
        try:
            equipment_results = calculate_equipment_expenses(
                equipment_data=equipment_df,
                start_date=start_date,
                end_date=end_date
            )
            results['equipment_expenses'] = equipment_results
        except Exception as e:
            st_obj.warning(f"Could not calculate equipment expenses: {str(e)}")
            results['equipment_expenses'] = {}
    else:
        results['equipment_expenses'] = {}
    
    # Calculate personnel expenses if available
    personnel_df = AppController.get_dataframe("Personnel")
    if personnel_df is not None and not personnel_df.empty:
        try:
            personnel_results = calculate_personnel_expenses(
                personnel_data=personnel_df,
                start_date=start_date,
                end_date=end_date
            )
            results['personnel_expenses'] = personnel_results
        except Exception as e:
            st_obj.warning(f"Could not calculate personnel expenses: {str(e)}")
            results['personnel_expenses'] = {}
    else:
        results['personnel_expenses'] = {}
    
    # Generate annual summary data
    annual_summary = generate_annual_summary(results, start_date, end_date)
    results['annual_summary'] = annual_summary
    
    return results

def generate_annual_summary(results: Dict, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Generate a consolidated annual summary of all financial data.
    
    Args:
        results: Dictionary of calculation results
        start_date: Start date in format 'MM/DD/YYYY'
        end_date: End date in format 'MM/DD/YYYY'
        
    Returns:
        DataFrame with annual summary
    """
    # Parse start and end dates
    start_year = pd.to_datetime(start_date, format='%m/%d/%Y').year
    end_year = pd.to_datetime(end_date, format='%m/%d/%Y').year
    
    # Create a DataFrame with years in the range
    years = list(range(start_year, end_year + 1))
    annual_summary = pd.DataFrame({'Year': years})
    
    # Initialize columns
    annual_summary['Revenue'] = 0
    annual_summary['Personnel_Expenses'] = 0
    annual_summary['Equipment_Expenses'] = 0
    annual_summary['Other_Expenses'] = 0
    annual_summary['Total_Expenses'] = 0
    annual_summary['Net_Income'] = 0
    
    # Add exam revenue if available
    if ('exam_revenue' in results and 
        isinstance(results['exam_revenue'], dict) and 
        'annual_summary' in results['exam_revenue']):
        
        exam_annual = results['exam_revenue']['annual_summary']
        if isinstance(exam_annual, pd.DataFrame) and not exam_annual.empty:
            if 'Year' in exam_annual.columns and 'Total_Revenue' in exam_annual.columns:
                for idx, row in exam_annual.iterrows():
                    year = row['Year']
                    if year in years:
                        idx = years.index(year)
                        annual_summary.loc[idx, 'Revenue'] += row['Total_Revenue']
    
    # Add other revenue items if available
    if ('other_expenses' in results and 
        isinstance(results['other_expenses'], dict) and 
        not len(results['other_expenses']) == 0 and
        'annual_items' in results['other_expenses']):
        
        other_annual = results['other_expenses']['annual_items']
        if isinstance(other_annual, pd.DataFrame) and not other_annual.empty:
            # Check for IsExpense or Expense columns
            expense_column = None
            if 'IsExpense' in other_annual.columns:
                expense_column = 'IsExpense'
            elif 'Expense' in other_annual.columns:
                expense_column = 'Expense'
                
            if expense_column and 'Amount' in other_annual.columns and 'Year' in other_annual.columns:
                # Only include revenue items (where Expense/IsExpense is False)
                # Convert to bool to handle string "True"/"False" values
                other_revenue = other_annual[~other_annual[expense_column].astype(bool)]
                if not other_revenue.empty:
                    other_by_year = other_revenue.groupby('Year')['Amount'].sum()
                    for year, amount in other_by_year.items():
                        if year in years:
                            idx = years.index(year)
                            annual_summary.loc[idx, 'Revenue'] += amount
    
    # If we have any undistributed revenue (from sources without year info), distribute it evenly
    total_revenue_allocated = annual_summary['Revenue'].sum()
    if 'combined_revenue_total' in results:
        combined_total = results['combined_revenue_total']
        unallocated_revenue = combined_total - total_revenue_allocated
        
        if unallocated_revenue > 0:
            # Distribute evenly across years
            revenue_per_year = unallocated_revenue / len(years)
            for i in range(len(years)):
                annual_summary.loc[i, 'Revenue'] += revenue_per_year
    
    # Add personnel expenses if available
    if ('personnel_expenses' in results and 
        isinstance(results['personnel_expenses'], dict) and 
        not len(results['personnel_expenses']) == 0 and
        'annual' in results['personnel_expenses']):
        
        personnel_annual = results['personnel_expenses']['annual']
        if isinstance(personnel_annual, pd.DataFrame) and not personnel_annual.empty:
            if 'Year' in personnel_annual.columns:
                personnel_by_year = personnel_annual.groupby('Year')['Total_Expense'].sum()
                for year, amount in personnel_by_year.items():
                    if year in years:
                        idx = years.index(year)
                        annual_summary.loc[idx, 'Personnel_Expenses'] += amount
    
    # Add equipment expenses if available
    if ('equipment_expenses' in results and 
        isinstance(results['equipment_expenses'], dict) and 
        not len(results['equipment_expenses']) == 0 and
        'annual' in results['equipment_expenses']):
        
        equipment_annual = results['equipment_expenses']['annual']
        if isinstance(equipment_annual, pd.DataFrame) and not equipment_annual.empty:
            if 'Year' in equipment_annual.columns:
                equipment_by_year = equipment_annual.groupby('Year')['TotalAnnualExpense'].sum()
                for year, amount in equipment_by_year.items():
                    if year in years:
                        idx = years.index(year)
                        annual_summary.loc[idx, 'Equipment_Expenses'] += amount
    
    # Add other expenses if available
    if ('other_expenses' in results and 
        isinstance(results['other_expenses'], dict) and 
        not len(results['other_expenses']) == 0 and
        'annual_items' in results['other_expenses']):
        
        other_annual = results['other_expenses']['annual_items']
        if isinstance(other_annual, pd.DataFrame) and not other_annual.empty:
            # Check for IsExpense or Expense columns
            expense_column = None
            if 'IsExpense' in other_annual.columns:
                expense_column = 'IsExpense'
            elif 'Expense' in other_annual.columns:
                expense_column = 'Expense'
                
            if expense_column and 'Amount' in other_annual.columns and 'Year' in other_annual.columns:
                # Only include expense items
                # Convert to bool to handle string "True"/"False" values
                other_expenses = other_annual[other_annual[expense_column].astype(bool)]
                other_by_year = other_expenses.groupby('Year')['Amount'].sum()
                for year, amount in other_by_year.items():
                    if year in years:
                        idx = years.index(year)
                        annual_summary.loc[idx, 'Other_Expenses'] += amount
    
    # Calculate totals and net income
    annual_summary['Total_Expenses'] = (
        annual_summary['Personnel_Expenses'] + 
        annual_summary['Equipment_Expenses'] + 
        annual_summary['Other_Expenses']
    )
    
    annual_summary['Net_Income'] = annual_summary['Revenue'] - annual_summary['Total_Expenses']
    
    return annual_summary

def render_summary_results(st_obj, results: Dict, start_date, end_date):
    """
    Render the summary plots and tables.
    
    Args:
        st_obj: Streamlit instance
        results: Dictionary with calculation results
        start_date: Start date for calculations
        end_date: End date for calculations
    """
    annual_summary = results.get('annual_summary', pd.DataFrame())
    
    if annual_summary.empty:
        st_obj.warning("No data available for the selected date range.")
        return
    
    # Display summary metrics
    st_obj.subheader("Financial Summary")
    
    # Calculate total values across all years - ensure these are scalar values
    total_revenue = annual_summary['Revenue'].sum()
    total_expenses = annual_summary['Total_Expenses'].sum()
    net_income = total_revenue - total_expenses
    
    # Make sure these are scalar values
    total_revenue = float(total_revenue)
    total_expenses = float(total_expenses)
    net_income = float(net_income)
    
    # Display metrics in columns
    col1, col2, col3 = st_obj.columns(3)
    with col1:
        st_obj.metric("Total Revenue", f"${total_revenue:,.2f}")
    with col2:
        st_obj.metric("Total Expenses", f"${total_expenses:,.2f}")
    with col3:
        st_obj.metric("Net Income", f"${net_income:,.2f}")
    
    try:
        # Create tabs for different visualizations
        viz_tabs = st_obj.tabs([
            "Revenue vs Expenses", 
            "Expense Breakdown", 
            "Net Income", 
            "Annual Summary"
        ])
        
        # Revenue vs Expenses Visualization
        with viz_tabs[0]:
            st_obj.subheader("Revenue vs Expenses by Year")
            
            fig1, ax1 = plt.subplots(figsize=(12, 7))
            
            # Create bar chart of revenue vs expenses
            x = annual_summary['Year'].tolist()  # Convert to list to avoid Series issues
            revenue = annual_summary['Revenue'].tolist()  # Convert to list
            expenses = annual_summary['Total_Expenses'].tolist()  # Convert to list
            
            bar_width = 0.35
            x_pos = np.arange(len(x))
            
            bars1 = ax1.bar(x_pos - bar_width/2, revenue, bar_width, label='Revenue', color='#4ECB71')
            bars2 = ax1.bar(x_pos + bar_width/2, expenses, bar_width, label='Expenses', color='#FF6B6B')
            
            # Add data labels
            for bar in bars1:
                height = bar.get_height()
                if height > 0:
                    ax1.text(bar.get_x() + bar.get_width()/2., height + 5000,
                           f"${height:,.0f}", ha='center', va='bottom', rotation=0, fontsize=9)
            
            for bar in bars2:
                height = bar.get_height()
                if height > 0:
                    ax1.text(bar.get_x() + bar.get_width()/2., height + 5000,
                           f"${height:,.0f}", ha='center', va='bottom', rotation=0, fontsize=9)
            
            ax1.set_xlabel('Year')
            ax1.set_ylabel('Amount ($)')
            ax1.set_title('Revenue vs Expenses by Year')
            ax1.set_xticks(x_pos)
            ax1.set_xticklabels(x)
            ax1.grid(axis='y', linestyle='--', alpha=0.7)
            ax1.legend()
            
            # Format y-axis with dollar signs
            formatter = mticker.FuncFormatter(lambda x, p: f"${x:,.0f}")
            ax1.yaxis.set_major_formatter(formatter)
            
            plt.tight_layout()
            st_obj.pyplot(fig1)
        
        # Expense Breakdown Visualization
        with viz_tabs[1]:
            st_obj.subheader("Expense Breakdown by Year")
            
            fig2, ax2 = plt.subplots(figsize=(12, 7))
            
            # Create stacked bar chart of expenses
            x = annual_summary['Year'].tolist()  # Convert to list
            personnel = annual_summary['Personnel_Expenses'].tolist()  # Convert to list
            equipment = annual_summary['Equipment_Expenses'].tolist()  # Convert to list
            other = annual_summary['Other_Expenses'].tolist()  # Convert to list
            
            bar_width = 0.6
            x_pos = np.arange(len(x))
            
            # Create stacked bars
            bars1 = ax2.bar(x_pos, personnel, bar_width, label='Personnel', color='#5DA5DA')
            bars2 = ax2.bar(x_pos, equipment, bar_width, bottom=personnel, label='Equipment', color='#FAA43A')
            bars3 = ax2.bar(x_pos, other, bar_width, bottom=[p+e for p,e in zip(personnel, equipment)], label='Other', color='#60BD68')
            
            ax2.set_xlabel('Year')
            ax2.set_ylabel('Amount ($)')
            ax2.set_title('Expense Breakdown by Year')
            ax2.set_xticks(x_pos)
            ax2.set_xticklabels(x)
            ax2.grid(axis='y', linestyle='--', alpha=0.7)
            ax2.legend()
            
            # Format y-axis with dollar signs
            formatter = mticker.FuncFormatter(lambda x, p: f"${x:,.0f}")
            ax2.yaxis.set_major_formatter(formatter)
            
            plt.tight_layout()
            st_obj.pyplot(fig2)
            
            # Also show as a pie chart for total expenses
            st_obj.subheader("Total Expense Distribution")
            
            total_personnel = sum(personnel)
            total_equipment = sum(equipment)
            total_other = sum(other)
            
            if total_personnel > 0 or total_equipment > 0 or total_other > 0:
                fig3, ax3 = plt.subplots(figsize=(8, 8))
                
                # Create pie chart
                expense_types = ['Personnel', 'Equipment', 'Other']
                expense_values = [total_personnel, total_equipment, total_other]
                colors = ['#5DA5DA', '#FAA43A', '#60BD68']
                
                # Add percentage and value labels
                def autopct_format(values):
                    def my_format(pct):
                        total = sum(values)
                        val = int(round(pct*total/100.0))
                        return f'{pct:.1f}%\n(${val:,.0f})'
                    return my_format
                
                wedges, texts, autotexts = ax3.pie(
                    expense_values, 
                    labels=expense_types, 
                    colors=colors,
                    autopct=autopct_format(expense_values),
                    startangle=90,
                    wedgeprops={'edgecolor': 'w', 'linewidth': 1}
                )
                
                # Make text properties better for readability
                for text in autotexts:
                    text.set_fontsize(9)
                
                ax3.set_title('Distribution of Total Expenses')
                plt.tight_layout()
                st_obj.pyplot(fig3)
            else:
                st_obj.info("No expense data available to create distribution chart.")
        
        # Net Income Visualization
        with viz_tabs[2]:
            st_obj.subheader("Net Income by Year")
            
            fig4, ax4 = plt.subplots(figsize=(12, 7))
            
            # Create bar chart for net income
            x = annual_summary['Year'].tolist()  # Convert to list
            net_income_by_year = annual_summary['Net_Income'].tolist()  # Convert to list
            
            bars = ax4.bar(x, net_income_by_year, color=['#4ECB71' if val >= 0 else '#FF6B6B' for val in net_income_by_year])
            
            # Add data labels
            for bar in bars:
                height = bar.get_height()
                if height >= 0:
                    ax4.text(bar.get_x() + bar.get_width()/2., height + 5000,
                           f"${height:,.0f}", ha='center', va='bottom', rotation=0, fontsize=9)
                else:
                    ax4.text(bar.get_x() + bar.get_width()/2., height - 20000,
                           f"${height:,.0f}", ha='center', va='top', rotation=0, fontsize=9)
            
            ax4.set_xlabel('Year')
            ax4.set_ylabel('Amount ($)')
            ax4.set_title('Net Income by Year')
            ax4.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Add a horizontal line at y=0
            ax4.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            
            # Format y-axis with dollar signs
            formatter = mticker.FuncFormatter(lambda x, p: f"${x:,.0f}")
            ax4.yaxis.set_major_formatter(formatter)
            
            plt.tight_layout()
            st_obj.pyplot(fig4)
            
            # Add cumulative net income chart
            st_obj.subheader("Cumulative Net Income")
            
            fig5, ax5 = plt.subplots(figsize=(12, 7))
            
            # Calculate cumulative net income
            cumulative_net_income = [sum(net_income_by_year[:i+1]) for i in range(len(net_income_by_year))]
            
            # Create line chart
            ax5.plot(x, cumulative_net_income, marker='o', linestyle='-', color='#4361EE', linewidth=2)
            
            # Add data labels
            for i, val in enumerate(cumulative_net_income):
                ax5.text(x[i], val + 10000, f"${val:,.0f}", ha='center', fontsize=9)
            
            ax5.set_xlabel('Year')
            ax5.set_ylabel('Amount ($)')
            ax5.set_title('Cumulative Net Income')
            ax5.grid(True, linestyle='--', alpha=0.7)
            
            # Format y-axis with dollar signs
            ax5.yaxis.set_major_formatter(formatter)
            
            plt.tight_layout()
            st_obj.pyplot(fig5)
        
        # Annual Summary Table
        with viz_tabs[3]:
            st_obj.subheader("Annual Financial Summary")
            
            # Format the summary table for display
            display_summary = annual_summary.copy()
            
            # Format currency columns - using series.apply instead of map for better compatibility
            for col in annual_summary.columns:
                if col != 'Year':
                    display_summary[col] = display_summary[col].apply(lambda x: f"${x:,.2f}")
            
            # Rename columns for better display
            display_summary.columns = [
                'Year',
                'Revenue',
                'Personnel Expenses',
                'Equipment Expenses',
                'Other Expenses',
                'Total Expenses',
                'Net Income'
            ]
            
            st_obj.dataframe(display_summary, use_container_width=True)
            
            # Calculate and display key financial metrics
            st_obj.subheader("Key Financial Metrics")
            
            # Calculate breakeven year
            breakeven_years = []
            for i, row in annual_summary.iterrows():
                if row['Net_Income'] >= 0:
                    breakeven_years.append(row['Year'])
            
            col1, col2 = st_obj.columns(2)
            
            with col1:
                # Total values - ensure these are scalar values, not Series
                # (We've already converted these at the start of the function)
                
                # Calculate ROI
                roi_pct = (net_income / total_expenses * 100) if total_expenses > 0 else 0
                
                # Total values
                st_obj.write("##### Project Totals")
                total_metrics = pd.DataFrame({
                    'Metric': [
                        'Total Revenue',
                        'Total Expenses',
                        'Net Income',
                        'Return on Investment'
                    ],
                    'Value': [
                        f"${total_revenue:,.2f}",
                        f"${total_expenses:,.2f}",
                        f"${net_income:,.2f}",
                        f"{roi_pct:.2f}%"
                    ]
                })
                st_obj.dataframe(total_metrics, use_container_width=True, hide_index=True)
            
            with col2:
                # Breakeven analysis
                st_obj.write("##### Breakeven Analysis")
                if breakeven_years:
                    st_obj.success(f"Breakeven Year(s): {', '.join(map(str, breakeven_years))}")
                    
                    # Find the first breakeven year
                    first_breakeven = min(breakeven_years)
                    first_year = min(annual_summary['Year'])
                    years_to_breakeven = first_breakeven - first_year
                    
                    st_obj.info(f"Years to First Breakeven: {years_to_breakeven}")
                else:
                    st_obj.warning("No breakeven year found in the projection period.")
    except Exception as e:
        import traceback
        st_obj.error(f"Error rendering summary plots: {str(e)}")
        st_obj.error(traceback.format_exc()) 