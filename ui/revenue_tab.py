"""
Revenue data tab for the CAREScan ProForma Editor.

This module contains the UI components and logic for the Revenue tab.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Any, Optional
from datetime import date

from app_controller import AppController
from visualization import setup_plot_style, format_currency, create_revenue_charts

def render_revenue_tab(st_obj):
    """
    Render the Revenue tab UI.
    
    Args:
        st_obj: Streamlit instance
    """
    st_obj.header("Revenue Data")
    
    # Information about editing
    st_obj.info(
        "Edit the data directly in the table below. "
        "For semicolon-separated lists, use commas or semicolons to separate values. "
        "For large numbers, you can use underscores for readability (e.g., 200_000 or 200000)."
    )
    
    # Load data
    revenue_df = AppController.get_dataframe("Revenue")
    
    if revenue_df is None or revenue_df.empty:
        st_obj.warning("No revenue data available. Please add revenue sources.")
        # Create an empty DataFrame with the expected columns
        revenue_df = pd.DataFrame({
            "Title": [""],
            "Type": [""],
            "Amount": [0],
            "Notes": [""]
        })
    
    # Create a data editor with custom column configuration
    st_obj.subheader("Revenue Sources")
    edited_df = st_obj.data_editor(
        revenue_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Title": st_obj.column_config.TextColumn(
                "Revenue Source",
                help="Name of the revenue source (e.g., Medicare, Private Insurance)"
            ),
            "Type": st_obj.column_config.SelectboxColumn(
                "Type",
                help="Type of revenue",
                options=["Fixed", "Variable", "Per-Use", "Recurring"],
                required=True
            ),
            "Amount": st_obj.column_config.NumberColumn(
                "Amount ($)",
                help="Dollar amount of revenue",
                min_value=0,
                max_value=10000000,
                step=1000,
                format="$%d"
            ),
            "Notes": st_obj.column_config.TextColumn(
                "Notes",
                help="Additional information about this revenue source"
            )
        }
    )
    
    # Save changes if data was edited
    if not edited_df.equals(revenue_df):
        col1, col2 = st_obj.columns([1, 5])
        with col1:
            if st_obj.button("Save Revenue Data"):
                save_result = AppController.save_dataframe("Revenue", edited_df)
                if save_result:
                    st_obj.success("Revenue data saved successfully!")
                    revenue_df = edited_df
                else:
                    st_obj.error("Failed to save revenue data.")
    
    # Add a revenue visualization section if there is data
    if not revenue_df.empty and 'Title' in revenue_df.columns and 'Amount' in revenue_df.columns:
        st_obj.subheader("Revenue Visualization")
        
        if st_obj.button("Generate Revenue Chart"):
            render_revenue_chart(st_obj, revenue_df)

def render_revenue_chart(st_obj, revenue_df):
    """
    Render a chart visualizing revenue data.
    
    Args:
        st_obj: Streamlit instance
        revenue_df: Revenue data DataFrame
    """
    # Filter out rows with missing or zero amounts
    valid_revenue = revenue_df[(revenue_df['Amount'].notna()) & (revenue_df['Amount'] > 0)]
    
    if valid_revenue.empty:
        st_obj.warning("No valid revenue data to visualize. Please add revenue sources with amounts greater than zero.")
        return
    
    try:
        # Use the visualization module to create charts
        bar_chart, pie_chart = create_revenue_charts(revenue_df)
        
        # Display the bar chart
        st_obj.subheader("Revenue by Source")
        st_obj.pyplot(bar_chart)
        
        # Display the pie chart
        st_obj.subheader("Revenue Distribution")
        st_obj.pyplot(pie_chart)
        
        # Sort by amount descending for tables
        sorted_revenue = valid_revenue.sort_values('Amount', ascending=False)
        
        # Create a summary table with revenue totals
        st_obj.subheader("Revenue Summary")
        
        # Group by revenue type
        if 'Type' in sorted_revenue.columns:
            type_summary = sorted_revenue.groupby('Type')['Amount'].sum().reset_index()
            type_summary = type_summary.sort_values('Amount', ascending=False)
            
            # Format the amount column
            type_summary['Amount'] = type_summary['Amount'].map('${:,.2f}'.format)
            
            # Display as a table
            st_obj.write("Revenue by Type:")
            st_obj.table(type_summary)
        
        # Total revenue
        total_revenue = sorted_revenue['Amount'].sum()
        st_obj.metric("Total Revenue", f"${total_revenue:,.2f}")
        
        # Display all revenue sources in a nicely formatted table
        st_obj.write("All Revenue Sources:")
        
        # Create a copy for display formatting
        display_df = sorted_revenue.copy()
        
        # Format amount column
        if 'Amount' in display_df.columns:
            display_df['Amount'] = display_df['Amount'].map('${:,.2f}'.format)
        
        st_obj.dataframe(display_df, use_container_width=True)
    
    except Exception as e:
        import traceback
        st_obj.error(f"Error generating revenue charts: {str(e)}")
        st_obj.error(traceback.format_exc()) 