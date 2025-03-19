"""
Exams data tab for the CAREScan ProForma Editor.

This module contains the UI components and logic for the Exams tab,
including exam data editing and revenue analysis visualization.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as mticker
from typing import Dict, List, Tuple, Any, Optional
from datetime import date

from app_controller import AppController
from financeModels.exam_revenue import ExamRevenueCalculator, calculate_exam_revenue
from visualization import setup_plot_style, format_currency

def render_exams_tab(st_obj):
    """
    Render the Exams tab UI.
    
    Args:
        st_obj: Streamlit instance
    """
    st_obj.header("Exams Data")
    
    # Information about editing
    st_obj.info(
        "Edit the data directly in the table below. "
        "For semicolon-separated lists, use commas or semicolons to separate values. "
        "For large numbers, you can use underscores for readability (e.g., 200_000 or 200000)."
    )
    
    # Load data
    exams_df = AppController.get_dataframe("Exams")
    
    if exams_df is None or exams_df.empty:
        st_obj.warning("No exams data available. Please add exam information.")
        # Create an empty DataFrame with the expected columns
        exams_df = pd.DataFrame({
            "Title": [""],
            "Equipment": [""],
            "Staff": [""],
            "Duration": [0],
            "SupplyCost": [0],
            "OrderCost": [0],
            "InterpCost": [0],
            "CMSTechRate": [0],
            "CMSProRate": [0],
            "MinAge": [0],
            "MaxAge": [0],
            "ApplicableSex": [""],
            "ApplicablePct": [0.0]
        })
    
    # Create a data editor with custom column configuration
    st_obj.subheader("Exam Information")
    edited_df = st_obj.data_editor(
        exams_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Title": st_obj.column_config.TextColumn(
                "Exam Title",
                help="Name of the exam"
            ),
            "Equipment": st_obj.column_config.TextColumn(
                "Equipment",
                help="Equipment required for this exam"
            ),
            "Staff": st_obj.column_config.TextColumn(
                "Staff",
                help="Staff type required for this exam"
            ),
            "Duration": st_obj.column_config.NumberColumn(
                "Duration (minutes)",
                help="Duration of the exam in minutes",
                min_value=0,
                max_value=240,
                step=5,
                format="%d"
            ),
            "SupplyCost": st_obj.column_config.NumberColumn(
                "Supply Cost ($)",
                help="Cost of supplies per exam",
                min_value=0,
                max_value=10000,
                step=1,
                format="$%d"
            ),
            "OrderCost": st_obj.column_config.NumberColumn(
                "Order Cost ($)",
                help="Cost of ordering the exam",
                min_value=0,
                max_value=10000,
                step=1,
                format="$%d"
            ),
            "InterpCost": st_obj.column_config.NumberColumn(
                "Interpretation Cost ($)",
                help="Cost of interpretation per exam",
                min_value=0,
                max_value=10000,
                step=1,
                format="$%d"
            ),
            "CMSTechRate": st_obj.column_config.NumberColumn(
                "CMS Tech Rate ($)",
                help="CMS reimbursement rate for technician component",
                min_value=0,
                max_value=10000,
                step=1,
                format="$%d"
            ),
            "CMSProRate": st_obj.column_config.NumberColumn(
                "CMS Professional Rate ($)",
                help="CMS reimbursement rate for professional component",
                min_value=0,
                max_value=10000,
                step=1,
                format="$%d"
            ),
            "MinAge": st_obj.column_config.NumberColumn(
                "Minimum Age",
                help="Minimum patient age for this exam",
                min_value=0,
                max_value=120,
                step=1
            ),
            "MaxAge": st_obj.column_config.NumberColumn(
                "Maximum Age",
                help="Maximum patient age for this exam",
                min_value=0,
                max_value=120,
                step=1
            ),
            "ApplicableSex": st_obj.column_config.TextColumn(
                "Applicable Sex",
                help="Applicable patient sex (e.g., 'Female', 'Male', or 'Female; Male')"
            ),
            "ApplicablePct": st_obj.column_config.NumberColumn(
                "Applicable Percentage",
                help="Percentage of applicable population (0.0 - 1.0)",
                min_value=0.0,
                max_value=1.0,
                step=0.01,
                format="%.2f"
            )
        }
    )
    
    # Save changes if data was edited
    if not edited_df.equals(exams_df):
        col1, col2 = st_obj.columns([1, 5])
        with col1:
            if st_obj.button("Save Exams Data"):
                save_result = AppController.save_dataframe("Exams", edited_df)
                if save_result:
                    st_obj.success("Exams data saved successfully!")
                    exams_df = edited_df
                else:
                    st_obj.error("Failed to save exams data.")
    
    # Add an exam revenue analysis section
    st_obj.subheader("Exam Revenue Analysis")
    
    st_obj.info(
        "This analysis calculates exam revenue based on the Exams.csv and Revenue.csv data. "
        "It shows annual exam volume, revenue by source, and projected net revenue."
    )
    
    # Date range selection
    st_obj.write("##### Select Date Range")
    col1, col2 = st_obj.columns(2)
    with col1:
        start_date = st_obj.date_input(
            "Start Date", 
            value=pd.to_datetime("01/01/2025").date(),
            min_value=date(2020, 1, 1),
            max_value=date(2050, 12, 31),
            key="exam_start_date"
        )
    with col2:
        end_date = st_obj.date_input(
            "End Date", 
            value=pd.to_datetime("12/31/2029").date(),
            min_value=date(2020, 1, 1),
            max_value=date(2050, 12, 31),
            key="exam_end_date"
        )
    
    # Revenue source selection
    st_obj.write("##### Select Revenue Sources")
    revenue_df = AppController.get_dataframe("Revenue")
    if revenue_df is not None and not revenue_df.empty and 'Title' in revenue_df.columns:
        revenue_sources = revenue_df['Title'].tolist()
        selected_sources = st_obj.multiselect(
            "Revenue Sources", 
            revenue_sources, 
            default=revenue_sources, 
            key="exam_revenue_sources"
        )
    else:
        selected_sources = []
        st_obj.error("Revenue data is not available. Please add revenue sources in the Revenue tab.")
    
    # Working days per year option
    work_days = st_obj.number_input(
        "Working Days Per Year", 
        min_value=200, 
        max_value=300, 
        value=250, 
        key="exam_work_days"
    )
    
    # Calculate button
    if st_obj.button("Calculate Exam Revenue", key="calculate_exam_revenue"):
        try:
            with st_obj.spinner("Calculating exam revenue and generating plots..."):
                # Check if required data is available
                required_tables = ['Revenue', 'Exams', 'Personnel', 'Equipment']
                missing_tables = [table for table in required_tables if table not in st_obj.session_state.dataframes or st_obj.session_state.dataframes[table].empty]
                
                if missing_tables:
                    st_obj.error(f"The following required data is missing: {', '.join(missing_tables)}")
                elif not selected_sources:
                    st_obj.error("Please select at least one revenue source.")
                else:
                    # Extract years from selected dates
                    start_year = start_date.year
                    end_year = end_date.year
                    
                    # Initialize the calculator
                    calculator = ExamRevenueCalculator(
                        exams_data=st_obj.session_state.dataframes['Exams'],
                        revenue_data=st_obj.session_state.dataframes['Revenue'],
                        personnel_data=st_obj.session_state.dataframes['Personnel'],
                        equipment_data=st_obj.session_state.dataframes['Equipment'],
                        start_date=start_date.strftime('%m/%d/%Y')
                    )
                    
                    # Calculate exam revenue for all selected sources
                    results = calculator.calculate_multi_year_exam_revenue(
                        start_year=start_year,
                        end_year=end_year,
                        revenue_sources=selected_sources,
                        work_days_per_year=work_days
                    )
                    
                    # Store results
                    AppController.store_calculation_result("exam_revenue", results)
                    
                    # Display results
                    render_exam_results(st_obj, results, exams_df, start_date, end_date)
        
        except Exception as e:
            import traceback
            st_obj.error(f"Error calculating exam revenue: {str(e)}")
            st_obj.error(traceback.format_exc())

def render_exam_results(st_obj, results, exams_df, start_date, end_date):
    """
    Render the exam revenue calculation results.
    
    Args:
        st_obj: Streamlit instance
        results: Exam revenue calculation results
        exams_df: Exams data DataFrame
        start_date: Start date for calculations
        end_date: End date for calculations
    """
    if results.empty:
        st_obj.warning("No exam revenue data could be calculated. This might be because there is no equipment or required staff available during the selected period.")
        return
    
    # Display key metrics
    st_obj.subheader("Key Metrics Summary")
    
    # Calculate summary metrics
    total_volume = results['AnnualVolume'].sum()
    total_revenue = results['Total_Revenue'].sum()
    total_expenses = results['Total_Direct_Expenses'].sum()
    net_revenue = results['Net_Revenue'].sum()
    
    # Display metrics in columns
    metric_col1, metric_col2, metric_col3, metric_col4 = st_obj.columns(4)
    with metric_col1:
        st_obj.metric("Total Exam Volume", f"{total_volume:,.0f}")
    with metric_col2:
        st_obj.metric("Total Revenue", f"${total_revenue:,.2f}")
    with metric_col3:
        st_obj.metric("Total Expenses", f"${total_expenses:,.2f}")
    with metric_col4:
        st_obj.metric("Net Revenue", f"${net_revenue:,.2f}")
    
    # 1. Total Revenue by Year and Revenue Source
    st_obj.subheader("Total Revenue by Year and Revenue Source")
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    revenue_by_source = results.groupby(['Year', 'RevenueSource'])['Total_Revenue'].sum().unstack()
    revenue_by_source.plot(kind='bar', stacked=True, ax=ax1, colormap='viridis')
    ax1.set_title('Total Revenue by Year and Revenue Source')
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Revenue ($)')
    ax1.grid(axis='y', linestyle='--', alpha=0.7)
    ax1.legend(title='Revenue Source')
    
    # Format y-axis with dollar signs
    fmt = '${x:,.0f}'
    tick = mticker.StrMethodFormatter(fmt)
    ax1.yaxis.set_major_formatter(tick)
    
    st_obj.pyplot(fig1)
    
    # Show summary table
    # Format the table for display
    display_revenue = revenue_by_source.copy()
    for col in display_revenue.columns:
        display_revenue[col] = display_revenue[col].map('${:,.2f}'.format)
    
    st_obj.dataframe(display_revenue)
    
    # 2. Exam Volume by Year
    st_obj.subheader("Exam Volume by Year")
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    volume_by_year = results.groupby('Year')['AnnualVolume'].sum()
    volume_by_year.plot(kind='bar', ax=ax2, color='skyblue')
    ax2.set_title('Total Exam Volume by Year')
    ax2.set_xlabel('Year')
    ax2.set_ylabel('Annual Volume')
    ax2.grid(axis='y', linestyle='--', alpha=0.7)
    for i, v in enumerate(volume_by_year):
        ax2.text(i, v + 0.1, f"{v:,.0f}", ha='center')
    st_obj.pyplot(fig2)
    
    # 3. Revenue vs Expenses by Year
    st_obj.subheader("Revenue vs Expenses by Year")
    fig3, ax3 = plt.subplots(figsize=(12, 6))
    financials = results.groupby('Year').agg({
        'Total_Revenue': 'sum',
        'Total_Direct_Expenses': 'sum'
    })
    financials.plot(kind='bar', ax=ax3)
    ax3.set_title('Revenue vs Direct Expenses by Year')
    ax3.set_xlabel('Year')
    ax3.set_ylabel('Amount ($)')
    ax3.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Format y-axis with dollar signs
    ax3.yaxis.set_major_formatter(tick)
    
    st_obj.pyplot(fig3)
    
    # 4. Top Exams by Revenue
    st_obj.subheader("Top Exams by Revenue")
    exam_revenue = results.groupby('Exam')['Total_Revenue'].sum().sort_values(ascending=False)
    fig4, ax4 = plt.subplots(figsize=(12, 6))
    
    # Plot top 10 exams
    top_exams = exam_revenue.head(10)
    colors = plt.cm.YlOrRd(np.linspace(0.2, 0.8, len(top_exams)))
    top_exams.plot(kind='bar', ax=ax4, color=colors)
    ax4.set_title('Top 10 Exams by Total Revenue')
    ax4.set_xlabel('Exam')
    ax4.set_ylabel('Total Revenue ($)')
    ax4.grid(axis='y', linestyle='--', alpha=0.7)
    ax4.tick_params(axis='x', rotation=45)
    
    # Format y-axis with dollar signs
    ax4.yaxis.set_major_formatter(tick)
    
    st_obj.pyplot(fig4)
    
    # 5. Detailed Data Table
    st_obj.subheader("Detailed Exam Revenue Data")
    
    # Create a year filter for the detailed table
    all_years = sorted(results['Year'].unique())
    selected_year = st_obj.selectbox("Select Year for Detailed View", all_years, key="detail_year_select")
    
    # Filter the results for the selected year
    year_results = results[results['Year'] == selected_year].copy()
    
    # Format currency columns
    for col in ['Total_Revenue', 'Total_Direct_Expenses', 'Net_Revenue']:
        if col in year_results.columns:
            year_results[col] = year_results[col].map('${:,.2f}'.format)
    
    # Display the detailed table
    st_obj.dataframe(year_results, use_container_width=True)
    
    # 6. Exam Volume Distribution
    st_obj.subheader("Exam Volume Distribution")
    
    # Aggregate exam volumes across all years
    volume_by_exam = results.groupby('Exam')['AnnualVolume'].sum().sort_values(ascending=False)
    
    # Create pie chart
    fig5, ax5 = plt.subplots(figsize=(10, 10))
    
    # Limit to top 15 exams for readability, group the rest as "Other"
    if len(volume_by_exam) > 15:
        top_volume = volume_by_exam.head(15)
        other_volume = volume_by_exam[15:].sum()
        plot_data = pd.concat([top_volume, pd.Series([other_volume], index=["Other"])])
    else:
        plot_data = volume_by_exam
    
    # Create pie chart
    ax5.pie(
        plot_data, 
        labels=plot_data.index, 
        autopct='%1.1f%%',
        startangle=90, 
        shadow=False,
        wedgeprops={'edgecolor': 'w', 'linewidth': 1},
        textprops={'fontsize': 9}
    )
    
    ax5.set_title('Exam Volume Distribution')
    ax5.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    
    st_obj.pyplot(fig5)
    
    # Display volume by exam as dataframe
    display_volume = pd.DataFrame(volume_by_exam).reset_index()
    display_volume.columns = ['Exam', 'Total Volume']
    display_volume['Percentage'] = (display_volume['Total Volume'] / display_volume['Total Volume'].sum()) * 100
    display_volume['Percentage'] = display_volume['Percentage'].map('{:.1f}%'.format)
    
    st_obj.dataframe(display_volume, use_container_width=True) 