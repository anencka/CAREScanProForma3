"""
Comprehensive ProForma tab for the CAREScan ProForma Editor.

This module contains the UI components and logic for the Comprehensive ProForma tab,
which integrates all revenue and expense sources into a unified financial projection.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from typing import Dict, List, Tuple, Any, Optional
from datetime import date

from app_controller import AppController
from financeModels.comprehensive_proforma import calculate_comprehensive_proforma
from visualization import setup_plot_style, format_currency as mpl_format_currency

# Create a wrapper for format_currency that handles both formatting for matplotlib and for display
def format_currency(value, include_cents=True, pos=None):
    """
    Format a number as currency.
    
    Args:
        value: The number to format
        include_cents: Whether to include cents in the formatting
        pos: Position parameter (used by matplotlib, can be None for direct formatting)
        
    Returns:
        Formatted currency string
    """
    if pd.isna(value):
        return "$0"
    
    if pos is not None:
        # This is being called by matplotlib
        return mpl_format_currency(value, pos)
    
    # This is being called directly for display
    if include_cents:
        return f"${value:,.2f}"
    else:
        return f"${value:,.0f}"

def render_comprehensive_tab(st_obj):
    """
    Render the Comprehensive ProForma tab UI.
    
    Args:
        st_obj: Streamlit instance
    """
    st_obj.header("Comprehensive ProForma")
    
    # Explanation of the proforma
    st_obj.info(
        "This tab generates a comprehensive financial proforma that integrates all revenue and expense sources. "
        "It combines data from Personnel, Equipment, Exams, and Other Expenses to create a unified financial projection."
    )
    
    # Add a note about data reloading
    st_obj.warning(
        "**Important**: If you have made changes to data in other tabs, ensure these changes are reflected in your report "
        "by using the '🔄 Reload All Data' button in the sidebar before generating the proforma. "
        "This will ensure all calculations use the most recent data from your CSV files."
    )
    
    # Date range selection
    st_obj.subheader("Select Date Range")
    col1, col2 = st_obj.columns(2)
    with col1:
        start_date = st_obj.date_input(
            "Start Date", 
            value=pd.to_datetime("01/01/2025").date(),
            min_value=date(2020, 1, 1),
            max_value=date(2040, 12, 31),
            key="proforma_start_date"
        )
    with col2:
        end_date = st_obj.date_input(
            "End Date", 
            value=pd.to_datetime("12/31/2029").date(),
            min_value=date(2020, 1, 1),
            max_value=date(2040, 12, 31),
            key="proforma_end_date"
        )
    
    # Revenue source selection
    st_obj.subheader("Select Revenue Sources")
    if 'Revenue' in st_obj.session_state.dataframes:
        revenue_sources = st_obj.session_state.dataframes['Revenue']['Title'].tolist()
        selected_sources = st_obj.multiselect(
            "Revenue Sources", 
            revenue_sources, 
            default=revenue_sources, 
            key="proforma_revenue_sources"
        )
    else:
        st_obj.warning("No revenue sources found. Please ensure Revenue.csv is loaded correctly.")
        selected_sources = []
    
    # Additional parameters
    st_obj.subheader("Additional Parameters")
    
    # Working days
    work_days = st_obj.number_input(
        "Working Days Per Year", 
        min_value=200, 
        max_value=365, 
        value=250, 
        step=1,
        help="Number of working days per year for calculating exam volume"
    )
    
    # Travel parameters
    col1, col2 = st_obj.columns(2)
    with col1:
        days_between_travel = st_obj.number_input(
            "Days Between Travel", 
            min_value=1, 
            max_value=30, 
            value=5, 
            step=1,
            help="Number of days between travel events for mobile equipment"
        )
    with col2:
        miles_per_travel = st_obj.number_input(
            "Miles Per Travel", 
            min_value=1, 
            max_value=100, 
            value=20, 
            step=1,
            help="Number of miles traveled in each travel event for mobile equipment"
        )
    
    # Population growth rate
    st_obj.subheader("Population Growth Rates")
    st_obj.write("Specify annual growth rates for population reached (affects exam volume)")
    
    # Calculate number of years in the range
    if start_date and end_date:
        start_year = start_date.year
        end_year = end_date.year
        num_years = end_year - start_year + 1
        
        # Create input fields for each year's growth rate
        growth_rates = []
        growth_cols = st_obj.columns(min(5, num_years))
        
        # Define default increasing growth rates: 0.05, 0.10, 0.15, 0.2, 0.25
        default_growth_rates = [0.05, 0.10, 0.15, 0.20, 0.25]
        
        for i, year in enumerate(range(start_year, end_year + 1)):
            col_idx = i % len(growth_cols)
            # Set default value based on year index, reuse the last value if more years than defaults
            default_value = default_growth_rates[min(i, len(default_growth_rates)-1)] if i < len(default_growth_rates) else default_growth_rates[-1]
            
            with growth_cols[col_idx]:
                growth_rate = st_obj.number_input(
                    f"Growth {year}",
                    min_value=-0.5,
                    max_value=2.0,
                    value=default_value,
                    step=0.01,
                    format="%.2f",
                    key=f"growth_rate_{year}"
                )
                growth_rates.append(growth_rate)
    
    # Generate Proforma button
    if st_obj.button("Generate Comprehensive ProForma", key="generate_proforma_btn"):
        if selected_sources:
            with st_obj.spinner("Calculating Comprehensive ProForma..."):
                try:
                    # Convert start and end dates to the required string format
                    start_date_str = start_date.strftime("%m/%d/%Y")
                    end_date_str = end_date.strftime("%m/%d/%Y")
                    
                    # Get the updated data from the AppController
                    updated_data = st_obj.session_state.dataframes
                    
                    # Check if all required data is available
                    required_data = ['Personnel', 'Exams', 'Revenue', 'Equipment', 'OtherExpenses']
                    missing_data = [d for d in required_data if d not in updated_data or updated_data[d].empty]
                    
                    if missing_data:
                        st_obj.error(f"Missing data: {', '.join(missing_data)}. Please ensure all required data is loaded.")
                    else:
                        # Ensure numeric data types for calculations
                        for df_name in updated_data:
                            # Process each dataframe to ensure numeric columns are properly typed
                            df = updated_data[df_name]
                            # Try to convert potentially numeric columns
                            for col in df.columns:
                                # Skip converting true string columns like 'Title', 'Name', etc.
                                if col.lower() in ['title', 'name', 'description', 'type', 'institution', 'category', 'stafftype', 'notes']:
                                    continue
                                # Check if column might be numeric
                                try:
                                    # Only try to convert if the column has mixed types or is an object dtype
                                    if df[col].dtype == 'object' or df[col].dtype == 'string':
                                        # Handle different date formats first
                                        if 'date' in col.lower():
                                            df[col] = pd.to_datetime(df[col], errors='ignore')
                                        else:
                                            # For potential numeric columns, remove any currency symbols and commas
                                            df[col] = df[col].astype(str).str.replace('$', '', regex=False)
                                            df[col] = df[col].astype(str).str.replace(',', '', regex=False)
                                            df[col] = pd.to_numeric(df[col], errors='ignore')
                                except Exception:
                                    # If conversion fails, leave as is
                                    pass
                            updated_data[df_name] = df
                        
                        # Calculate comprehensive proforma
                        try:
                            proforma_results = calculate_comprehensive_proforma(
                                personnel_data=updated_data['Personnel'],
                                exams_data=updated_data['Exams'],
                                revenue_data=updated_data['Revenue'],
                                equipment_data=updated_data['Equipment'],
                                other_data=updated_data['OtherExpenses'],
                                start_date=start_date_str,
                                end_date=end_date_str,
                                revenue_sources=selected_sources,
                                work_days_per_year=work_days,
                                days_between_travel=days_between_travel,
                                miles_per_travel=miles_per_travel,
                                population_growth_rates=growth_rates
                            )
                            
                            # Store the results in session state for use in other tabs
                            st_obj.session_state.comprehensive_proforma_results = {
                                'results': proforma_results,
                                'start_date': start_date_str,
                                'end_date': end_date_str,
                                'revenue_sources': selected_sources,
                                'work_days': work_days,
                                'population_growth_rates': growth_rates
                            }
                            
                            # Display the results
                            _display_proforma_results(st_obj, proforma_results)
                        except Exception as e:
                            import traceback
                            st_obj.error(f"Error calculating comprehensive proforma: {str(e)}")
                            st_obj.error(traceback.format_exc())
                except Exception as e:
                    import traceback
                    st_obj.error(f"Error calculating comprehensive proforma: {str(e)}")
                    st_obj.error(traceback.format_exc())
        else:
            st_obj.error("Please select at least one revenue source.")
    
    # Check if we have results to display
    elif 'comprehensive_proforma_results' in st_obj.session_state and st_obj.session_state.comprehensive_proforma_results:
        _display_proforma_results(st_obj, st_obj.session_state.comprehensive_proforma_results['results'])

def _display_proforma_results(st_obj, proforma_results):
    """
    Display the comprehensive proforma results.
    
    Args:
        st_obj: Streamlit instance
        proforma_results: Results from the comprehensive proforma calculation
    """
    annual_summary = proforma_results['annual_summary']
    financial_metrics = proforma_results['financial_metrics']
    
    # Success message
    st_obj.success("Comprehensive ProForma generated successfully!")
    
    # Create tabs for different result views
    result_tabs = st_obj.tabs([
        "Financial Summary", 
        "Revenue vs Expenses", 
        "Cash Flow Projection", 
        "Financial Metrics", 
        "Raw Data"
    ])
    
    # Financial Summary Tab
    with result_tabs[0]:
        _display_financial_summary(st_obj, annual_summary, financial_metrics)
    
    # Revenue vs Expenses Tab
    with result_tabs[1]:
        _display_revenue_expenses(st_obj, annual_summary)
    
    # Cash Flow Projection Tab
    with result_tabs[2]:
        _display_cash_flow(st_obj, proforma_results['monthly_cash_flow'])
    
    # Financial Metrics Tab
    with result_tabs[3]:
        _display_financial_metrics(st_obj, financial_metrics)
    
    # Raw Data Tab
    with result_tabs[4]:
        _display_raw_data(st_obj, annual_summary)

def _display_financial_summary(st_obj, annual_summary, financial_metrics):
    """Display the financial summary section."""
    st_obj.subheader("Financial Summary")
    
    # Key financial metrics
    col1, col2, col3 = st_obj.columns(3)
    
    with col1:
        st_obj.metric(
            "Total Revenue", 
            format_currency(financial_metrics.get('total_revenue', 0)),
            help="Total revenue over the projection period"
        )
    
    with col2:
        st_obj.metric(
            "Total Expenses", 
            format_currency(financial_metrics.get('total_expenses', 0)),
            help="Total expenses over the projection period"
        )
    
    # Calculate net income if not available
    if 'net_income' not in financial_metrics and 'total_revenue' in financial_metrics and 'total_expenses' in financial_metrics:
        financial_metrics['net_income'] = financial_metrics['total_revenue'] - financial_metrics['total_expenses']
    
    with col3:
        st_obj.metric(
            "Net Income", 
            format_currency(financial_metrics.get('net_income', 0)),
            delta=f"{financial_metrics.get('profit_margin', 0):.1f}%" if 'profit_margin' in financial_metrics else None,
            delta_color="normal",
            help="Total net income over the projection period"
        )
    
    st_obj.markdown("---")
    
    # Annual summary table
    st_obj.subheader("Annual Financial Summary")
    
    # Create a display version of the annual summary
    display_df = annual_summary.copy()
    
    # Format currency columns
    currency_columns = [
        'Total_Revenue', 'Exam_Revenue', 'Other_Revenue',
        'Total_Expenses', 'Personnel_Expenses', 'Equipment_Expenses',
        'Exam_Direct_Expenses', 'Other_Expenses', 'Net_Income'
    ]
    
    for col in currency_columns:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: format_currency(x, include_cents=False))
    
    st_obj.dataframe(
        display_df[['Year'] + currency_columns],
        hide_index=True,
        use_container_width=True
    )
    
    # Breakeven analysis
    if 'breakeven_year' in financial_metrics and financial_metrics['breakeven_year']:
        st_obj.success(f"Breakeven achieved in Year {financial_metrics['breakeven_year']}")
    else:
        st_obj.warning("Breakeven not achieved within the projection period")

def _display_revenue_expenses(st_obj, annual_summary):
    """Display the revenue vs expenses section."""
    st_obj.subheader("Revenue vs. Expenses")
    
    # Ensure columns exist in the annual summary
    required_columns = ['Year', 'Total_Revenue', 'Total_Expenses', 'Net_Income']
    if not all(col in annual_summary.columns for col in required_columns):
        st_obj.warning("Some required data columns are missing. Cannot generate revenue vs expenses chart.")
        return
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    # Manual styling instead of using setup_plot_style
    ax.grid(linestyle='--', alpha=0.7)
    ax.set_facecolor('#f8f9fa')
    fig.patch.set_facecolor('#ffffff')
    
    # Set style parameters
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
    
    # Prepare data
    years = annual_summary['Year'].astype(str).tolist()
    revenue = annual_summary['Total_Revenue'].tolist()
    expenses = annual_summary['Total_Expenses'].tolist()
    
    # Check if we have data to plot
    if not years or not revenue or not expenses:
        st_obj.warning("No data available for Revenue vs. Expenses chart.")
        return
    
    # Set x-axis position for bars
    x = np.arange(len(years))
    width = 0.35
    
    # Plot bars
    ax.bar(x - width/2, revenue, width, label='Revenue', color='#4CAF50')
    ax.bar(x + width/2, expenses, width, label='Expenses', color='#F44336')
    
    # Add net income line
    net_income = annual_summary['Net_Income'].tolist()
    ax2 = ax.twinx()
    ax2.plot(x, net_income, color='#2196F3', marker='o', linestyle='-', linewidth=2, label='Net Income')
    
    # Add data labels
    for i, v in enumerate(revenue):
        ax.text(i - width/2, v + max(revenue) * 0.02, format_currency(v, include_cents=False), 
                ha='center', va='bottom', fontsize=9, rotation=0)
    
    for i, v in enumerate(expenses):
        ax.text(i + width/2, v + max(revenue) * 0.02, format_currency(v, include_cents=False), 
                ha='center', va='bottom', fontsize=9, rotation=0)
    
    for i, v in enumerate(net_income):
        ax2.text(i, v + max(net_income) * 0.05 if any(n > 0 for n in net_income) else max(net_income) * 0.5, 
                format_currency(v, include_cents=False), 
                ha='center', va='bottom', fontsize=9, rotation=0)
    
    # Set labels and title
    ax.set_xlabel('Year')
    ax.set_ylabel('Amount ($)')
    ax2.set_ylabel('Net Income ($)')
    ax.set_title('Annual Revenue vs. Expenses')
    
    # Set x-ticks
    ax.set_xticks(x)
    ax.set_xticklabels(years)
    
    # Format y-axis ticks as currency
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: format_currency(x, include_cents=False)))
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: format_currency(x, include_cents=False)))
    
    # Combine legends
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    # Adjust layout and display the plot
    plt.tight_layout()
    st_obj.pyplot(fig)
    
    # Expense breakdown
    st_obj.subheader("Expense Breakdown")
    
    # Check if required columns exist for the expense breakdown
    expense_columns = ['Personnel_Expenses', 'Equipment_Expenses', 'Exam_Direct_Expenses', 'Other_Expenses']
    if not all(col in annual_summary.columns for col in expense_columns):
        st_obj.warning("Some required expense categories are missing. Cannot generate expense breakdown chart.")
        return
    
    # Create expense breakdown plot
    fig2, ax = plt.subplots(figsize=(10, 6))
    # Manual styling instead of using setup_plot_style
    ax.grid(linestyle='--', alpha=0.7)
    ax.set_facecolor('#f8f9fa')
    fig2.patch.set_facecolor('#ffffff')
    
    # Set style parameters
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
    
    # Stack the bars
    personnel = annual_summary['Personnel_Expenses'].fillna(0).tolist()
    equipment = annual_summary['Equipment_Expenses'].fillna(0).tolist()
    exam_direct = annual_summary['Exam_Direct_Expenses'].fillna(0).tolist()
    other = annual_summary['Other_Expenses'].fillna(0).tolist()
    
    # Check if we have data to plot
    if not any(personnel) and not any(equipment) and not any(exam_direct) and not any(other):
        st_obj.warning("No expense data available for the breakdown chart.")
        return
    
    # Plot stacked bars
    ax.bar(years, personnel, label='Personnel', color='#3F51B5')
    ax.bar(years, equipment, bottom=personnel, label='Equipment', color='#009688')
    
    # Calculate cumulative values for bottom of each stack
    bottom_exam = [p + e for p, e in zip(personnel, equipment)]
    ax.bar(years, exam_direct, bottom=bottom_exam, label='Exam Direct', color='#FF9800')
    
    # Calculate bottom for other expenses
    bottom_other = [p + e + ed for p, e, ed in zip(personnel, equipment, exam_direct)]
    ax.bar(years, other, bottom=bottom_other, label='Other', color='#9C27B0')
    
    # Set labels and title
    ax.set_xlabel('Year')
    ax.set_ylabel('Amount ($)')
    ax.set_title('Annual Expense Breakdown by Category')
    
    # Format y-axis ticks as currency
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: format_currency(x, include_cents=False)))
    
    # Add legend
    ax.legend(loc='upper left')
    
    # Adjust layout and display the plot
    plt.tight_layout()
    st_obj.pyplot(fig2)

def _display_cash_flow(st_obj, monthly_cash_flow):
    """Display the cash flow projection section."""
    st_obj.subheader("Monthly Cash Flow Projection")
    
    if monthly_cash_flow is None or monthly_cash_flow.empty:
        st_obj.warning("No monthly cash flow data available.")
        return

    # Check if required columns exist
    required_columns = ['Year', 'Month', 'Total_Revenue', 'Total_Expenses', 'Net_Income']
    if not all(col in monthly_cash_flow.columns for col in required_columns):
        st_obj.warning("Some required data columns are missing from monthly cash flow data.")
        return
    
    # Create date column for plotting
    monthly_cash_flow['Date'] = pd.to_datetime(
        monthly_cash_flow['Year'].astype(str) + '-' + 
        monthly_cash_flow['Month'].astype(str) + '-01'
    )
    
    # Sort by date
    monthly_cash_flow = monthly_cash_flow.sort_values('Date')
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 6))
    # Manual styling instead of using setup_plot_style
    ax.grid(linestyle='--', alpha=0.7)
    ax.set_facecolor('#f8f9fa')
    fig.patch.set_facecolor('#ffffff')
    
    # Set style parameters
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
    
    # Plot revenue and expenses
    ax.plot(
        monthly_cash_flow['Date'], 
        monthly_cash_flow['Total_Revenue'], 
        marker='o', 
        markersize=4, 
        linewidth=2,
        label='Revenue', 
        color='#4CAF50'
    )
    
    ax.plot(
        monthly_cash_flow['Date'], 
        monthly_cash_flow['Total_Expenses'], 
        marker='s', 
        markersize=4, 
        linewidth=2,
        label='Expenses', 
        color='#F44336'
    )
    
    # Plot net income
    ax.plot(
        monthly_cash_flow['Date'], 
        monthly_cash_flow['Net_Income'], 
        marker='^', 
        markersize=4, 
        linewidth=2,
        label='Net Income', 
        color='#2196F3'
    )
    
    # Fill between net income and zero
    ax.fill_between(
        monthly_cash_flow['Date'],
        monthly_cash_flow['Net_Income'],
        0,
        where=(monthly_cash_flow['Net_Income'] > 0),
        color='#4CAF50',
        alpha=0.2
    )
    
    ax.fill_between(
        monthly_cash_flow['Date'],
        monthly_cash_flow['Net_Income'],
        0,
        where=(monthly_cash_flow['Net_Income'] < 0),
        color='#F44336',
        alpha=0.2
    )
    
    # Calculate cumulative net income
    monthly_cash_flow['Cumulative_Net_Income'] = monthly_cash_flow['Net_Income'].cumsum()
    
    # Create secondary axis for cumulative net income
    ax2 = ax.twinx()
    ax2.plot(
        monthly_cash_flow['Date'], 
        monthly_cash_flow['Cumulative_Net_Income'], 
        marker='d', 
        markersize=4, 
        linewidth=2,
        linestyle='--',
        label='Cumulative Net Income', 
        color='#FF9800'
    )
    
    # Format axes
    ax.set_xlabel('Date')
    ax.set_ylabel('Monthly Amount ($)')
    ax2.set_ylabel('Cumulative Amount ($)')
    ax.set_title('Monthly Cash Flow Projection')
    
    # Format dates on x-axis
    plt.gcf().autofmt_xdate()
    
    # Format y-axis ticks as currency
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: format_currency(x, include_cents=False)))
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: format_currency(x, include_cents=False)))
    
    # Combine legends
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    # Adjust layout and display the plot
    plt.tight_layout()
    st_obj.pyplot(fig)
    
    # Display monthly cash on hand plot
    st_obj.subheader("Monthly Cash on Hand")
    
    # Add explanation about cash on hand calculation
    st_obj.info(
        "This cash on hand projection shows actual cash flows, treating equipment purchases as one-time cash outflows "
        "when they occur, and excluding non-cash expenses like depreciation. It represents the literal cash available "
        "in bank accounts rather than accounting profit/loss."
    )
    
    # Calculate initial cash position (assuming starting from zero)
    # Add a user input for initial cash position
    initial_cash = st_obj.number_input(
        "Initial Cash Position ($)", 
        min_value=0, 
        value=0,  # Changed default from 100000 to 0
        step=10000,
        format="%d",
        help="Starting cash position at the beginning of the projection period"
    )
    
    # Get the equipment purchases data from raw data in session state
    equipment_purchases = pd.DataFrame()
    equipment_data = pd.DataFrame()
    
    if ('comprehensive_proforma_results' in st_obj.session_state and 
        'results' in st_obj.session_state.comprehensive_proforma_results):
        
        results = st_obj.session_state.comprehensive_proforma_results['results']
        
        # Get equipment_results if available
        if 'equipment_results' in results:
            equipment_results = results['equipment_results']
            if 'annual' in equipment_results and not equipment_results['annual'].empty:
                # Create a copy of the equipment annual data for cash flow adjustments
                equipment_purchases = equipment_results['annual'].copy()
        
        # Try to get original equipment data which contains PurchaseDate
        if 'dataframes' in st_obj.session_state and 'Equipment' in st_obj.session_state.dataframes:
            equipment_data = st_obj.session_state.dataframes['Equipment'].copy()
    
    # Log debugging info
    if equipment_data.empty:
        st_obj.warning("No equipment data found. The cash flow projection will not include equipment purchases.", icon="⚠️")
    
    # Create a cash-based version of the monthly cash flow
    cash_flow = monthly_cash_flow.copy()
    
    # Add a new column for equipment purchases
    cash_flow['Equipment_Purchases'] = 0.0
    
    # Remove depreciation from equipment expenses (since it's a non-cash expense)
    if not equipment_purchases.empty and 'AnnualDepreciation' in equipment_purchases.columns:
        # Process each month to adjust for depreciation and add equipment purchases
        for i, row in cash_flow.iterrows():
            year = row['Year']
            month = row['Month']
            
            # Find equipment expenses for this year
            year_equipment = equipment_purchases[equipment_purchases['Year'] == year]
            
            if not year_equipment.empty:
                # Calculate depreciation for this month (annual depreciation / 12)
                monthly_depreciation = year_equipment['AnnualDepreciation'].sum() / 12
                
                # Adjust equipment expenses by removing depreciation
                if 'Equipment_Expenses' in cash_flow.columns:
                    cash_flow.at[i, 'Equipment_Expenses'] -= monthly_depreciation
                    cash_flow.at[i, 'Total_Expenses'] -= monthly_depreciation
                    cash_flow.at[i, 'Net_Income'] += monthly_depreciation
    
    # Add equipment purchase costs as full cash outlays in the month they occur
    if not equipment_data.empty and 'PurchaseDate' in equipment_data.columns:
        # Process each equipment purchase
        for _, equipment in equipment_data.iterrows():
            if pd.notna(equipment['PurchaseDate']):
                try:
                    # Convert purchase date to datetime
                    purchase_date = pd.to_datetime(equipment['PurchaseDate'])
                    purchase_year = purchase_date.year
                    purchase_month = purchase_date.month
                    
                    # Calculate total purchase cost
                    quantity = equipment['Quantity'] if 'Quantity' in equipment.index else 1
                    purchase_cost = equipment['PurchaseCost'] * quantity
                    
                    # Skip if purchase cost is zero or NaN
                    if pd.isna(purchase_cost) or purchase_cost == 0:
                        continue
                    
                    # Split payment: 80% when ordered, 20% when delivered
                    initial_payment = purchase_cost * 0.8
                    final_payment = purchase_cost * 0.2
                    
                    # Get construction time (in days) with default of 0 if not specified
                    construction_time = equipment['ConstructionTime'] if 'ConstructionTime' in equipment.index else 0
                    if pd.isna(construction_time):
                        construction_time = 0
                    
                    # Calculate delivery date (PurchaseDate + ConstructionTime)
                    delivery_date = purchase_date + pd.DateOffset(days=int(construction_time))
                    delivery_year = delivery_date.year
                    delivery_month = delivery_date.month
                    
                    # Find the corresponding row for initial payment (order date)
                    order_idx = cash_flow[(cash_flow['Year'] == purchase_year) & 
                                        (cash_flow['Month'] == purchase_month)].index
                    
                    if not order_idx.empty:
                        order_idx = order_idx[0]
                        # Add the initial payment (80%) to equipment purchases
                        cash_flow.at[order_idx, 'Equipment_Purchases'] += initial_payment
                        # Add to total expenses and adjust net income
                        cash_flow.at[order_idx, 'Total_Expenses'] += initial_payment
                        cash_flow.at[order_idx, 'Net_Income'] -= initial_payment
                        
                        # Add text to identify this payment in the table
                        equipment_name = equipment['Title'] if 'Title' in equipment.index else "Equipment"
                        if 'Equipment_Purchase_Details' not in cash_flow.columns:
                            cash_flow['Equipment_Purchase_Details'] = ""
                        
                        if cash_flow.at[order_idx, 'Equipment_Purchase_Details']:
                            cash_flow.at[order_idx, 'Equipment_Purchase_Details'] += f"; {equipment_name}"
                        else:
                            cash_flow.at[order_idx, 'Equipment_Purchase_Details'] = f"{equipment_name}"
                    
                    # Now handle the final payment (delivery date)
                    delivery_idx = cash_flow[(cash_flow['Year'] == delivery_year) & 
                                            (cash_flow['Month'] == delivery_month)].index
                    
                    if not delivery_idx.empty and (construction_time > 0 or delivery_month != purchase_month or delivery_year != purchase_year):
                        delivery_idx = delivery_idx[0]
                        # Add the final payment (20%) to equipment purchases
                        cash_flow.at[delivery_idx, 'Equipment_Purchases'] += final_payment
                        # Add to total expenses and adjust net income
                        cash_flow.at[delivery_idx, 'Total_Expenses'] += final_payment
                        cash_flow.at[delivery_idx, 'Net_Income'] -= final_payment
                        
                        # Add text to identify this payment in the table
                        equipment_name = equipment['Title'] if 'Title' in equipment.index else "Equipment"
                        if 'Equipment_Purchase_Details' not in cash_flow.columns:
                            cash_flow['Equipment_Purchase_Details'] = ""
                        
                        if cash_flow.at[delivery_idx, 'Equipment_Purchase_Details']:
                            cash_flow.at[delivery_idx, 'Equipment_Purchase_Details'] += f"; {equipment_name}"
                        else:
                            cash_flow.at[delivery_idx, 'Equipment_Purchase_Details'] = f"{equipment_name}"
                    else:
                        # If delivery is in same month as purchase or we don't have a matching row, 
                        # add the final payment to the initial payment month
                        if not order_idx.empty:
                            cash_flow.at[order_idx, 'Equipment_Purchases'] += final_payment
                            cash_flow.at[order_idx, 'Total_Expenses'] += final_payment
                            cash_flow.at[order_idx, 'Net_Income'] -= final_payment
                
                except Exception as e:
                    st_obj.error(f"Error processing equipment purchase: {str(e)}")
    
    # Recalculate cumulative net income based on cash flow
    cash_flow['Cumulative_Net_Income'] = cash_flow['Net_Income'].cumsum()
    
    # Calculate cash on hand
    cash_flow['Cash_On_Hand'] = initial_cash + cash_flow['Cumulative_Net_Income']
    
    # Create the cash on hand plot
    fig3, ax = plt.subplots(figsize=(12, 6))
    # Manual styling
    ax.grid(linestyle='--', alpha=0.7)
    ax.set_facecolor('#f8f9fa')
    fig3.patch.set_facecolor('#ffffff')
    
    # Plot cash on hand
    ax.plot(
        cash_flow['Date'], 
        cash_flow['Cash_On_Hand'], 
        marker='o', 
        markersize=4, 
        linewidth=2,
        label='Cash on Hand', 
        color='#673AB7'  # Purple color for cash on hand
    )
    
    # Add a horizontal line at zero
    ax.axhline(y=0, color='red', linestyle='-', linewidth=1, alpha=0.5)
    
    # Fill between cash on hand and zero
    ax.fill_between(
        cash_flow['Date'],
        cash_flow['Cash_On_Hand'],
        0,
        where=(cash_flow['Cash_On_Hand'] > 0),
        color='#673AB7',
        alpha=0.2
    )
    
    # If we have equipment purchases, mark them on the chart
    if 'Equipment_Purchases' in cash_flow.columns and cash_flow['Equipment_Purchases'].sum() > 0:
        purchases = cash_flow[cash_flow['Equipment_Purchases'] > 0]
        if not purchases.empty:
            ax.scatter(
                purchases['Date'],
                purchases['Cash_On_Hand'],
                s=100,  # Marker size
                color='red',
                marker='v',  # Down-pointing triangle
                label='Equipment Purchase',
                zorder=5  # Ensure it's drawn on top
            )
            
            # Add annotations for large purchases
            for _, purchase in purchases.iterrows():
                if purchase['Equipment_Purchases'] > 10000:  # Only annotate significant purchases
                    # Add details from Equipment_Purchase_Details if available
                    annotation_text = f"${purchase['Equipment_Purchases']:,.0f}"
                    if 'Equipment_Purchase_Details' in purchase and pd.notna(purchase['Equipment_Purchase_Details']):
                        detail_text = purchase['Equipment_Purchase_Details']
                        # Truncate very long detail text
                        if len(detail_text) > 50:
                            detail_text = detail_text[:47] + "..."
                        annotation_text = f"{annotation_text}\n{detail_text}"
                        
                    ax.annotate(
                        annotation_text,
                        (purchase['Date'], purchase['Cash_On_Hand']),
                        xytext=(0, -25),  # Offset text below the point
                        textcoords='offset points',
                        ha='center',
                        fontsize=7,
                        bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.8),
                        wrap=True
                    )
    
    # Format axes
    ax.set_xlabel('Date')
    ax.set_ylabel('Cash on Hand ($)')
    ax.set_title('Monthly Cash on Hand Projection (True Cash Basis)')
    
    # Format dates on x-axis
    plt.gcf().autofmt_xdate()
    
    # Format y-axis ticks as currency
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: format_currency(x, include_cents=False)))
    
    # Add minimum cash position line
    min_cash = cash_flow['Cash_On_Hand'].min()
    if min_cash < 0:
        ax.axhline(y=min_cash, color='#F44336', linestyle='--', linewidth=1)
        ax.text(
            cash_flow['Date'].iloc[0], 
            min_cash * 1.1, 
            f"Minimum: {format_currency(min_cash, include_cents=False)}", 
            color='#F44336',
            fontweight='bold'
        )
    
    # Add threshold line and annotation for when cash on hand is low
    cash_threshold = initial_cash * 0.2  # 20% of initial cash
    if cash_flow['Cash_On_Hand'].min() < cash_threshold:
        ax.axhline(y=cash_threshold, color='orange', linestyle='-.', linewidth=1)
        ax.text(
            cash_flow['Date'].iloc[0], 
            cash_threshold * 1.1, 
            f"Low Cash Threshold: {format_currency(cash_threshold, include_cents=False)}", 
            color='orange',
            fontweight='bold'
        )
    
    # Add legend
    ax.legend()
    
    # Adjust layout and display the plot
    plt.tight_layout()
    st_obj.pyplot(fig3)
    
    # Add a note about the equipment purchases
    st_obj.caption(
        "**Note:** Equipment purchases are split into two payments: 80% when ordered and 20% upon delivery. "
        "The red triangles on the chart mark these payments."
    )
    
    # Display monthly cash flow table (with formatting)
    st_obj.subheader("Monthly Cash Flow Table (True Cash Basis)")
    
    # Create a display version of the dataframe
    display_df = cash_flow.copy()
    
    # Format the date
    display_df['Month/Year'] = display_df['Date'].dt.strftime('%b %Y')
    
    # Format currency columns
    currency_columns = [
        'Total_Revenue', 'Exam_Revenue', 'Other_Revenue',
        'Total_Expenses', 'Personnel_Expenses', 'Equipment_Expenses',
        'Exam_Direct_Expenses', 'Other_Expenses', 'Net_Income',
        'Cumulative_Net_Income', 'Cash_On_Hand'
    ]
    
    if 'Equipment_Purchases' in display_df.columns:
        currency_columns.append('Equipment_Purchases')
    
    for col in currency_columns:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: format_currency(x, include_cents=False))
    
    # Select columns for display
    display_cols = ['Month/Year', 'Total_Revenue', 'Total_Expenses']
    
    if 'Equipment_Purchases' in display_df.columns:
        display_cols.append('Equipment_Purchases')
    
    if 'Equipment_Purchase_Details' in display_df.columns:
        display_cols.append('Equipment_Purchase_Details')
        
    display_cols.extend(['Net_Income', 'Cumulative_Net_Income', 'Cash_On_Hand'])
    
    st_obj.dataframe(
        display_df[display_cols],
        hide_index=True,
        use_container_width=True
    )

def _display_financial_metrics(st_obj, financial_metrics):
    """Display the financial metrics section."""
    st_obj.subheader("Financial Metrics")
    
    # Create a metrics dashboard
    col1, col2, col3 = st_obj.columns(3)
    
    with col1:
        st_obj.metric(
            "Return on Investment (ROI)", 
            f"{financial_metrics.get('roi', 0):.1f}%" if 'roi' in financial_metrics else "N/A",
            help="Return on Investment over the projection period"
        )
        
        st_obj.metric(
            "Profit Margin", 
            f"{financial_metrics.get('profit_margin', 0):.1f}%" if 'profit_margin' in financial_metrics else "N/A",
            help="Average profit margin over the projection period"
        )
    
    with col2:
        st_obj.metric(
            "Breakeven Year", 
            str(financial_metrics.get('breakeven_year', 'Not achieved')) if financial_metrics.get('breakeven_year') else "Not achieved",
            help="Year when cumulative net income becomes positive"
        )
        
        st_obj.metric(
            "Breakeven Month", 
            financial_metrics.get('breakeven_month', 'Not achieved') if financial_metrics.get('breakeven_month') else "Not achieved",
            help="Month when cumulative net income becomes positive"
        )
    
    with col3:
        st_obj.metric(
            "Total Investment", 
            format_currency(financial_metrics.get('total_investment', 0)) if 'total_investment' in financial_metrics else "N/A",
            help="Total investment required (cumulative negative cash flow)"
        )
        
        st_obj.metric(
            "Peak Negative Cash Flow", 
            format_currency(financial_metrics.get('peak_negative_cash_flow', 0)) if 'peak_negative_cash_flow' in financial_metrics else "N/A",
            help="Maximum negative cumulative cash flow"
        )
    
    # Display ROI over time if available
    if 'annual_roi' in financial_metrics and financial_metrics['annual_roi']:
        st_obj.subheader("Return on Investment Over Time")
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(10, 6))
        # Manual styling instead of using setup_plot_style
        ax.grid(linestyle='--', alpha=0.7)
        ax.set_facecolor('#f8f9fa')
        fig.patch.set_facecolor('#ffffff')
        
        # Set style parameters
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
        
        # Prepare data
        years = list(financial_metrics['annual_roi'].keys())
        roi_values = list(financial_metrics['annual_roi'].values())
        
        # Plot bars
        bars = ax.bar(years, roi_values, color='#2196F3')
        
        # Add a horizontal line at 0%
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        # Add data labels
        for bar in bars:
            height = bar.get_height()
            label_pos = height + 5 if height > 0 else height - 5
            alignment = 'bottom' if height > 0 else 'top'
            ax.text(
                bar.get_x() + bar.get_width()/2, 
                label_pos,
                f"{height:.1f}%", 
                ha='center', 
                va=alignment, 
                fontsize=9
            )
        
        # Set labels and title
        ax.set_xlabel('Year')
        ax.set_ylabel('ROI (%)')
        ax.set_title('Annual Return on Investment')
        
        # Adjust layout and display the plot
        plt.tight_layout()
        st_obj.pyplot(fig)

def _display_raw_data(st_obj, annual_summary):
    """Display the raw data section."""
    st_obj.subheader("Raw Annual Summary Data")
    st_obj.dataframe(annual_summary, use_container_width=True) 