"""
Visualization module for the CAREScan ProForma Editor application.

This module provides functions for creating various plots and visualizations
used throughout the application.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import streamlit as st
from typing import Dict, List, Tuple, Any, Optional

def format_currency(x, pos):
    """Format axis ticks as currency."""
    return f"${x:,.0f}"

def format_percentage(x, pos):
    """Format axis ticks as percentages."""
    return f"{x:.1f}%"

def format_number(x, pos):
    """Format axis ticks with thousands separators."""
    return f"{x:,.0f}"

def setup_plot_style(figsize=(10, 6)):
    """Set up a plot with standard styling."""
    fig, ax = plt.subplots(figsize=figsize)
    
    # Set style parameters
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
    
    # Set grid and background
    ax.grid(linestyle='--', alpha=0.7)
    ax.set_facecolor('#f8f9fa')
    fig.patch.set_facecolor('#ffffff')
    
    return fig, ax

def create_revenue_by_year_source_plot(df: pd.DataFrame) -> plt.Figure:
    """
    Create a stacked bar chart of revenue by year and source.
    
    Args:
        df: DataFrame with revenue data
        
    Returns:
        Matplotlib figure
    """
    fig, ax = setup_plot_style()
    
    # Process data
    # (Implementation will depend on your specific data structure)
    
    # Set formatting
    currency_formatter = mticker.FuncFormatter(format_currency)
    ax.yaxis.set_major_formatter(currency_formatter)
    
    # Add labels and title
    ax.set_xlabel('Year')
    ax.set_ylabel('Revenue ($)')
    ax.set_title('Revenue by Year and Source')
    
    # Add legend
    ax.legend(title='Revenue Source')
    
    return fig

def create_volume_by_year_exam_plot(df: pd.DataFrame) -> plt.Figure:
    """
    Create a line chart of exam volumes by year.
    
    Args:
        df: DataFrame with exam volume data
        
    Returns:
        Matplotlib figure
    """
    fig, ax = setup_plot_style()
    
    # Process data
    # (Implementation will depend on your specific data structure)
    
    # Set formatting
    number_formatter = mticker.FuncFormatter(format_number)
    ax.yaxis.set_major_formatter(number_formatter)
    
    # Add labels and title
    ax.set_xlabel('Year')
    ax.set_ylabel('Number of Exams')
    ax.set_title('Exam Volume by Year')
    
    # Add legend
    ax.legend(title='Exam Type')
    
    return fig

def create_revenue_vs_expenses_plot(revenue_df: pd.DataFrame, expenses_df: pd.DataFrame) -> plt.Figure:
    """
    Create a comparison plot of revenue vs expenses.
    
    Args:
        revenue_df: DataFrame with revenue data
        expenses_df: DataFrame with expense data
        
    Returns:
        Matplotlib figure
    """
    fig, ax = setup_plot_style()
    
    # Process data
    # (Implementation will depend on your specific data structure)
    
    # Set formatting
    currency_formatter = mticker.FuncFormatter(format_currency)
    ax.yaxis.set_major_formatter(currency_formatter)
    
    # Add labels and title
    ax.set_xlabel('Year')
    ax.set_ylabel('Amount ($)')
    ax.set_title('Revenue vs Expenses')
    
    # Add legend
    ax.legend()
    
    return fig

def create_personnel_expenses_plot(df: pd.DataFrame) -> Tuple[plt.Figure, plt.Figure, plt.Figure]:
    """
    Create plots for personnel expenses.
    
    Args:
        df: DataFrame with personnel expense data
        
    Returns:
        Tuple of Matplotlib figures (expenses by year, expenses by type, expenses by staff type)
    """
    # Create first plot - expenses by year
    fig1, ax1 = setup_plot_style()
    # (Implementation for fig1)
    
    # Create second plot - expenses by type
    fig2, ax2 = setup_plot_style()
    # (Implementation for fig2)
    
    # Create third plot - expenses by staff type
    fig3, ax3 = setup_plot_style()
    # (Implementation for fig3)
    
    return fig1, fig2, fig3

def create_equipment_expenses_plot(df: pd.DataFrame) -> Tuple[plt.Figure, plt.Figure]:
    """
    Create plots for equipment expenses.
    
    Args:
        df: DataFrame with equipment expense data
        
    Returns:
        Tuple of Matplotlib figures (equipment costs by year, depreciation over time)
    """
    # Implementation based on the equipment_tab.py visualization
    
    # Create first plot - equipment costs by year
    fig1, ax1 = setup_plot_style(figsize=(12, 6))
    
    # Basic bar chart for equipment costs (this is a placeholder)
    # In the actual implementation, this would be populated with real data
    # from the calculator's results
    try:
        # Simple sample implementation - would be replaced with actual logic
        equipment_names = df['Equipment'].tolist() if 'Equipment' in df.columns else []
        costs = df['Cost'].tolist() if 'Cost' in df.columns else []
        
        if equipment_names and costs:
            ax1.bar(equipment_names, costs, color='skyblue')
            ax1.set_title('Equipment Costs')
            ax1.set_xlabel('Equipment')
            ax1.set_ylabel('Cost ($)')
            ax1.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Format y-axis with dollar signs
            currency_formatter = mticker.FuncFormatter(format_currency)
            ax1.yaxis.set_major_formatter(currency_formatter)
            
            plt.xticks(rotation=45)
            plt.tight_layout()
    except Exception as e:
        # Handle any errors in the visualization
        print(f"Error in equipment cost plot: {str(e)}")
    
    # Create second plot - depreciation over time (placeholder)
    fig2, ax2 = setup_plot_style(figsize=(12, 6))
    
    try:
        # Simple timeline for demonstration - would be replaced with actual logic
        years = list(range(2025, 2030))
        depreciation = [100000 * (0.8 ** i) for i in range(5)]  # Simple exponential depreciation
        
        ax2.plot(years, depreciation, marker='o', linestyle='-', color='purple', linewidth=2)
        ax2.set_title('Equipment Depreciation Over Time')
        ax2.set_xlabel('Year')
        ax2.set_ylabel('Value ($)')
        ax2.grid(True, linestyle='--', alpha=0.7)
        
        # Format y-axis with dollar signs
        currency_formatter = mticker.FuncFormatter(format_currency)
        ax2.yaxis.set_major_formatter(currency_formatter)
        
        plt.tight_layout()
    except Exception as e:
        # Handle any errors in the visualization
        print(f"Error in depreciation plot: {str(e)}")
    
    return fig1, fig2

def create_comprehensive_proforma_plot(results: Dict[str, Any]) -> Tuple[plt.Figure, plt.Figure]:
    """
    Create plots for the comprehensive proforma.
    
    Args:
        results: Dictionary with comprehensive proforma calculation results
        
    Returns:
        Tuple of Matplotlib figures (revenue vs expenses, net income over time)
    """
    # Create first plot - revenue vs expenses
    fig1, ax1 = setup_plot_style()
    # (Implementation for fig1)
    
    # Create second plot - net income over time
    fig2, ax2 = setup_plot_style()
    # (Implementation for fig2)
    
    return fig1, fig2

def create_revenue_charts(revenue_df: pd.DataFrame) -> Tuple[plt.Figure, plt.Figure]:
    """
    Create charts visualizing revenue data.
    
    Args:
        revenue_df: DataFrame with revenue data
        
    Returns:
        Tuple of Matplotlib figures (bar chart, pie chart)
    """
    # Check if required columns exist
    required_columns = ['Title', 'Amount']
    missing_columns = [col for col in required_columns if col not in revenue_df.columns]
    
    if missing_columns:
        # Create empty figures if required columns are missing
        fig1, ax1 = setup_plot_style()
        ax1.set_title(f"Missing required columns: {', '.join(missing_columns)}")
        fig2, ax2 = setup_plot_style()
        ax2.set_title(f"Missing required columns: {', '.join(missing_columns)}")
        return fig1, fig2
    
    # Filter out rows with missing or zero amounts
    valid_revenue = revenue_df[(revenue_df['Amount'].notna()) & (revenue_df['Amount'] > 0)].copy()
    
    if valid_revenue.empty:
        # Create empty figures if no valid data
        fig1, ax1 = setup_plot_style()
        ax1.set_title("No valid revenue data available")
        fig2, ax2 = setup_plot_style()
        ax2.set_title("No valid revenue data available")
        return fig1, fig2
    
    # Sort by amount descending
    sorted_revenue = valid_revenue.sort_values('Amount', ascending=False)
    
    # Create a horizontal bar chart of revenue by source
    fig1, ax1 = setup_plot_style(figsize=(10, 6))
    
    # Create horizontal bar chart
    bars = ax1.barh(sorted_revenue['Title'], sorted_revenue['Amount'], color='#4ECB71')
    
    # Add amount labels
    for bar in bars:
        width = bar.get_width()
        ax1.text(width * 1.01, bar.get_y() + bar.get_height()/2, 
                f'${width:,.0f}', va='center')
    
    # Set chart labels and styling
    ax1.set_title('Revenue by Source')
    ax1.set_xlabel('Amount ($)')
    ax1.grid(axis='x', linestyle='--', alpha=0.7)
    
    # Format x-axis with dollar signs
    currency_formatter = mticker.FuncFormatter(format_currency)
    ax1.xaxis.set_major_formatter(currency_formatter)
    
    plt.tight_layout()
    
    # Create a pie chart showing revenue distribution
    fig2, ax2 = plt.subplots(figsize=(8, 8))
    
    # Create pie chart
    wedges, texts, autotexts = ax2.pie(
        sorted_revenue['Amount'],
        labels=sorted_revenue['Title'],
        autopct='%1.1f%%',
        startangle=90,
        shadow=False,
        wedgeprops={'edgecolor': 'w', 'linewidth': 1},
        textprops={'fontsize': 10}
    )
    
    # Add a circle at the center to make it a donut chart
    centre_circle = plt.Circle((0, 0), 0.3, fc='white')
    ax2.add_patch(centre_circle)
    
    # Add title
    ax2.set_title('Revenue Distribution')
    
    # Set aspect ratio to be equal so that pie is drawn as a circle
    ax2.axis('equal')
    
    plt.tight_layout()
    
    return fig1, fig2 