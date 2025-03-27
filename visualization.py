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

"""
Visualization module for comparing equipment lease vs purchase options.
This can be integrated into the visualization.py file.
"""



def create_lease_vs_purchase_comparison(equipment_df: pd.DataFrame, 
                                       annual_expenses: pd.DataFrame, 
                                       years: int = 10) -> Tuple[plt.Figure, plt.Figure]:
    """
    Create visualizations comparing leased vs. purchased equipment costs over time.
    
    Args:
        equipment_df: DataFrame containing equipment data
        annual_expenses: DataFrame with calculated annual expenses
        years: Number of years for long-term comparison (default: 10)
        
    Returns:
        Tuple of Matplotlib figures (cost comparison, cumulative comparison)
    """
    from visualization import setup_plot_style, format_currency
    
    # Create figures
    fig1, ax1 = setup_plot_style(figsize=(10, 6))
    fig2, ax2 = setup_plot_style(figsize=(10, 6))
    
    # Split data into leased and purchased equipment
    if 'IsLeased' in equipment_df.columns:
        leased_equipment = equipment_df[equipment_df['IsLeased'] == True]
        purchased_equipment = equipment_df[equipment_df['IsLeased'] == False]
    else:
        # If IsLeased column doesn't exist, assume all equipment is purchased
        leased_equipment = pd.DataFrame()
        purchased_equipment = equipment_df
    
    # Calculate annual costs for comparison
    annual_costs = {
        'Leased': {},
        'Purchased': {}
    }
    
    # For leased equipment: Annual lease payment + annual service/maintenance
    if not leased_equipment.empty:
        total_lease_payment = leased_equipment['AnnualLeaseAmount'].sum() if 'AnnualLeaseAmount' in leased_equipment.columns else 0
        total_lease_service = leased_equipment['AnnualServiceCost'].sum() if 'AnnualServiceCost' in leased_equipment.columns else 0
        total_lease_accreditation = leased_equipment['AnnualAccreditationCost'].sum() if 'AnnualAccreditationCost' in leased_equipment.columns else 0
        total_lease_insurance = leased_equipment['AnnualInsuranceCost'].sum() if 'AnnualInsuranceCost' in leased_equipment.columns else 0
        
        annual_costs['Leased']['Lease Payment'] = total_lease_payment
        annual_costs['Leased']['Service'] = total_lease_service
        annual_costs['Leased']['Accreditation'] = total_lease_accreditation
        annual_costs['Leased']['Insurance'] = total_lease_insurance
        annual_costs['Leased']['Total'] = total_lease_payment + total_lease_service + total_lease_accreditation + total_lease_insurance
    
    # For purchased equipment: Depreciation + annual service/maintenance
    if not purchased_equipment.empty:
        total_purchase_cost = purchased_equipment['PurchaseCost'].sum() if 'PurchaseCost' in purchased_equipment.columns else 0
        total_purchase_service = purchased_equipment['AnnualServiceCost'].sum() if 'AnnualServiceCost' in purchased_equipment.columns else 0
        total_purchase_accreditation = purchased_equipment['AnnualAccreditationCost'].sum() if 'AnnualAccreditationCost' in purchased_equipment.columns else 0
        total_purchase_insurance = purchased_equipment['AnnualInsuranceCost'].sum() if 'AnnualInsuranceCost' in purchased_equipment.columns else 0
        
        avg_lifespan = purchased_equipment['Lifespan'].mean() if 'Lifespan' in purchased_equipment.columns else 10
        annual_depreciation = total_purchase_cost / avg_lifespan
        
        annual_costs['Purchased']['Depreciation'] = annual_depreciation
        annual_costs['Purchased']['Service'] = total_purchase_service
        annual_costs['Purchased']['Accreditation'] = total_purchase_accreditation
        annual_costs['Purchased']['Insurance'] = total_purchase_insurance
        annual_costs['Purchased']['Total'] = annual_depreciation + total_purchase_service + total_purchase_accreditation + total_purchase_insurance
    
    # Create annual cost comparison (FIGURE 1)
    if annual_costs['Leased'] and annual_costs['Purchased']:
        # Both leased and purchased equipment exist, create side-by-side comparison
        categories = ['Leased', 'Purchased']
        lease_cost = annual_costs['Leased']['Total']
        purchase_cost = annual_costs['Purchased']['Total']
        
        x = np.arange(len(categories))
        width = 0.35
        
        # Create main bars for total costs
        bars1 = ax1.bar(x, [lease_cost, purchase_cost], width, color=['#e74c3c', '#3498db'])
        
        # Add data labels on the bars
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                   f'${height:,.0f}',
                   ha='center', va='bottom')
        
        # Set chart properties
        ax1.set_ylabel('Annual Cost ($)')
        ax1.set_title('Annual Cost Comparison: Leased vs. Purchased Equipment')
        ax1.set_xticks(x)
        ax1.set_xticklabels(categories)
        
        # Add a breakdown of costs below the chart
        breakdown_text = f"""
        Leased Equipment Annual Costs:
        - Lease Payments: ${annual_costs['Leased'].get('Lease Payment', 0):,.0f}
        - Service: ${annual_costs['Leased'].get('Service', 0):,.0f}
        - Accreditation: ${annual_costs['Leased'].get('Accreditation', 0):,.0f}
        - Insurance: ${annual_costs['Leased'].get('Insurance', 0):,.0f}
        - Total Annual Cost: ${annual_costs['Leased'].get('Total', 0):,.0f}
        
        Purchased Equipment Annual Costs:
        - Depreciation: ${annual_costs['Purchased'].get('Depreciation', 0):,.0f}
        - Service: ${annual_costs['Purchased'].get('Service', 0):,.0f}
        - Accreditation: ${annual_costs['Purchased'].get('Accreditation', 0):,.0f}
        - Insurance: ${annual_costs['Purchased'].get('Insurance', 0):,.0f}
        - Total Annual Cost: ${annual_costs['Purchased'].get('Total', 0):,.0f}
        
        Note: Depreciation is calculated using average lifespan.
        """
        
        # Add the text as an annotation at the bottom of the chart
        ax1.annotate(breakdown_text, (0.5, -0.4), xycoords='axes fraction', 
                   ha='center', va='center', fontsize=9,
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))
        
        # Adjust figure size to accommodate annotation
        fig1.set_figheight(8)
        fig1.tight_layout()
        plt.subplots_adjust(bottom=0.4)
        
        # Format y-axis with dollar signs
        ax1.yaxis.set_major_formatter(mticker.FuncFormatter(format_currency))
    
    # Create cumulative cost comparison over time (FIGURE 2)
    # Initialize cumulative costs
    leased_costs = []
    purchased_costs = []
    
    # Calculate cumulative costs over years
    for year in range(1, years + 1):
        # For leased equipment: Annual costs * years
        if annual_costs['Leased']:
            leased_annual = annual_costs['Leased']['Total']
            leased_cumulative = leased_annual * year
            leased_costs.append(leased_cumulative)
        else:
            leased_costs.append(0)
        
        # For purchased equipment: Upfront cost + annual costs * years
        if annual_costs['Purchased']:
            # Upfront cost is the total purchase cost
            upfront_cost = total_purchase_cost if 'total_purchase_cost' in locals() else 0
            
            # Annual costs excluding depreciation
            annual_service = annual_costs['Purchased'].get('Service', 0)
            annual_accreditation = annual_costs['Purchased'].get('Accreditation', 0) 
            annual_insurance = annual_costs['Purchased'].get('Insurance', 0)
            recurring_annual = annual_service + annual_accreditation + annual_insurance
            
            purchased_cumulative = upfront_cost + (recurring_annual * year)
            purchased_costs.append(purchased_cumulative)
        else:
            purchased_costs.append(0)
    
    # Plot cumulative costs over time
    years_list = list(range(1, years + 1))
    
    if leased_costs and purchased_costs:
        # Plot cumulative costs
        ax2.plot(years_list, leased_costs, 'o-', color='#e74c3c', label='Leased Equipment')
        ax2.plot(years_list, purchased_costs, 's-', color='#3498db', label='Purchased Equipment')
        
        # Find intersection point (breakeven year)
        breakeven_year = None
        for i in range(len(years_list) - 1):
            if (leased_costs[i] <= purchased_costs[i] and leased_costs[i+1] > purchased_costs[i+1]) or \
               (leased_costs[i] >= purchased_costs[i] and leased_costs[i+1] < purchased_costs[i+1]):
                breakeven_year = years_list[i+1]
                break
        
        # Highlight breakeven point if exists
        if breakeven_year:
            idx = breakeven_year - 1  # Adjust for zero-indexing
            breakeven_cost = (leased_costs[idx] + purchased_costs[idx]) / 2
            ax2.plot(breakeven_year, breakeven_cost, 'ro', markersize=10)
            ax2.annotate(f'Breakeven: Year {breakeven_year}',
                      (breakeven_year, breakeven_cost),
                      xytext=(10, 20),
                      textcoords='offset points',
                      arrowprops=dict(arrowstyle='->'),
                      color='red')
        
        # Add labels and grid
        ax2.set_xlabel('Years')
        ax2.set_ylabel('Cumulative Cost ($)')
        ax2.set_title('Cumulative Cost Comparison: Leased vs. Purchased Equipment')
        ax2.grid(True, linestyle='--', alpha=0.7)
        ax2.set_xticks(years_list)
        
        # Add legend
        ax2.legend()
        
        # Format y-axis with dollar signs
        ax2.yaxis.set_major_formatter(mticker.FuncFormatter(format_currency))
        
        # Annotate insights
        if leased_costs[-1] > purchased_costs[-1]:
            insight = f"Over {years} years, purchasing is ${leased_costs[-1] - purchased_costs[-1]:,.0f} less expensive than leasing."
        else:
            insight = f"Over {years} years, leasing is ${purchased_costs[-1] - leased_costs[-1]:,.0f} less expensive than purchasing."
        
        ax2.annotate(insight, (0.5, -0.15), xycoords='axes fraction', 
                   ha='center', va='center', fontsize=10,
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))
        
        # Adjust figure size
        fig2.tight_layout()
        plt.subplots_adjust(bottom=0.2)
    
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