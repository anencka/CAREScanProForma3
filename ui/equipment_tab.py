"""
Updated equipment tab UI with leasing options for the CAREScan ProForma Editor.

This module contains the updated UI components and logic for the Equipment tab.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from datetime import date

from app_controller import AppController
from financeModels.equipment_expenses import EquipmentExpenseCalculator, calculate_equipment_expenses
from visualization import create_equipment_expenses_plot, setup_plot_style, format_currency

def render_equipment_tab(st_obj):
    """
    Render the Equipment tab UI with lease options.
    
    Args:
        st_obj: Streamlit instance
    """
    st_obj.header("Equipment Expenses")
    
    # Explanation of this tab
    st_obj.info(
        "This tab allows you to edit equipment data and calculate expenses. "
        "You can specify whether equipment is purchased or leased. "
        "For leased equipment, enter the annual lease amount instead of purchase cost."
    )
    
    # Load data
    equipment_df = AppController.get_dataframe("Equipment")
    
    if equipment_df is None or equipment_df.empty:
        st_obj.warning("No equipment data available. Please add equipment information.")
        equipment_df = pd.DataFrame({
            "Title": [""],
            "PurchaseDate": ["01/01/2025"],
            "PurchaseCost": [0],
            "Quantity": [1],
            "Lifespan": [5],
            "ConstructionTime": [0],
            "AnnualServiceCost": [0],
            "AnnualAccreditationCost": [0],
            "AnnualInsuranceCost": [0],
            "MilageCost": [0],
            "SetupTime": [0],
            "TakedownTime": [0],
            "NecessaryStaff": [""],
            "ExamsOffered": [""],
            "IsLeased": [False],
            "AnnualLeaseAmount": [0]
        })
    
    # Ensure lease columns exist
    if 'IsLeased' not in equipment_df.columns:
        equipment_df['IsLeased'] = False
    
    if 'AnnualLeaseAmount' not in equipment_df.columns:
        equipment_df['AnnualLeaseAmount'] = 0
    
    # Convert string dates to datetime objects for the data editor
    try:
        if "PurchaseDate" in equipment_df.columns:
            equipment_df["PurchaseDate"] = pd.to_datetime(equipment_df["PurchaseDate"], errors='coerce')
    except Exception as e:
        st_obj.warning(f"Could not convert date columns: {str(e)}")
    
    # Ensure boolean type for IsLeased
    equipment_df['IsLeased'] = equipment_df['IsLeased'].astype(bool)
    
    # Create data editor with lease options
    st_obj.subheader("Equipment Data")
    
    # Add a help text about leasing
    st_obj.markdown("""
    ℹ️ **Leasing vs. Purchasing**:
    - For **leased equipment**, check the "Is Leased" box and enter the annual lease amount.
    - For **purchased equipment**, leave "Is Leased" unchecked and enter the purchase cost.
    """)
    
    edited_df = st_obj.data_editor(
        equipment_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Title": st_obj.column_config.TextColumn(
                "Equipment Name",
                help="Name or description of the equipment"
            ),
            "PurchaseDate": st_obj.column_config.DateColumn(
                "Purchase/Lease Date",
                help="Date of purchase or start of lease",
                format="MM/DD/YYYY",
                min_value=date(2020, 1, 1),
                max_value=date(2050, 12, 31)
            ),
            "IsLeased": st_obj.column_config.CheckboxColumn(
                "Is Leased",
                help="Check if equipment is leased rather than purchased"
            ),
            "PurchaseCost": st_obj.column_config.NumberColumn(
                "Purchase Cost ($)",
                help="Total cost of equipment including installation (for purchased equipment)",
                min_value=0,
                max_value=10000000,
                step=1000,
                format="$%d"
            ),
            "AnnualLeaseAmount": st_obj.column_config.NumberColumn(
                "Annual Lease Amount ($)",
                help="Annual lease payment amount (for leased equipment)",
                min_value=0,
                max_value=1000000,
                step=1000,
                format="$%d"
            ),
            "Quantity": st_obj.column_config.NumberColumn(
                "Quantity",
                help="Number of units",
                min_value=1,
                max_value=100,
                step=1
            ),
            "Lifespan": st_obj.column_config.NumberColumn(
                "Useful Life (Years)",
                help="Expected useful life in years for depreciation",
                min_value=1,
                max_value=30,
                step=1
            ),
            "ConstructionTime": st_obj.column_config.NumberColumn(
                "Construction Time (Days)",
                help="Number of days needed for construction/setup before equipment is available",
                min_value=0,
                max_value=365,
                step=1
            ),
            "AnnualServiceCost": st_obj.column_config.NumberColumn(
                "Annual Service Cost ($)",
                help="Annual cost for service contracts and maintenance",
                min_value=0,
                max_value=500000,
                step=1000,
                format="$%d"
            ),
            "AnnualAccreditationCost": st_obj.column_config.NumberColumn(
                "Annual Accreditation Cost ($)",
                help="Annual cost for accreditation and compliance",
                min_value=0,
                max_value=100000,
                step=1000,
                format="$%d"
            ),
            "AnnualInsuranceCost": st_obj.column_config.NumberColumn(
                "Annual Insurance Cost ($)",
                help="Annual cost for insurance",
                min_value=0,
                max_value=100000,
                step=1000,
                format="$%d"
            ),
            "MilageCost": st_obj.column_config.NumberColumn(
                "Mileage Cost ($/mile)",
                help="Cost per mile for travel",
                min_value=0,
                max_value=100,
                step=1
            ),
            "SetupTime": st_obj.column_config.NumberColumn(
                "Setup Time (min)",
                help="Time in minutes to set up equipment at a location",
                min_value=0,
                max_value=480,
                step=15
            ),
            "TakedownTime": st_obj.column_config.NumberColumn(
                "Takedown Time (min)",
                help="Time in minutes to take down equipment at a location",
                min_value=0,
                max_value=480,
                step=15
            ),
            "NecessaryStaff": st_obj.column_config.TextColumn(
                "Necessary Staff",
                help="Staff types required for this equipment (semicolon-separated)"
            ),
            "ExamsOffered": st_obj.column_config.TextColumn(
                "Exams Offered",
                help="Exams that can be performed with this equipment (semicolon-separated)"
            )
        }
    )
    
    # Save changes if data was edited
    if not edited_df.equals(equipment_df):
        if st_obj.button("Save Equipment Changes"):
            # Validate leased vs purchased equipment
            for idx, row in edited_df.iterrows():
                if row['IsLeased']:
                    # For leased equipment, purchase cost should be 0
                    if row['PurchaseCost'] > 0:
                        edited_df.at[idx, 'PurchaseCost'] = 0
                        st_obj.info(f"Purchase cost for {row['Title']} was set to 0 because it is leased.")
                    # Lease amount should be greater than 0
                    if row['AnnualLeaseAmount'] <= 0:
                        st_obj.error(f"Please enter an annual lease amount for {row['Title']}.")
                        return
                else:
                    # For purchased equipment, purchase cost should be > 0
                    if row['PurchaseCost'] <= 0:
                        st_obj.error(f"Please enter a purchase cost for {row['Title']}.")
                        return
            
            # Convert datetime objects back to string format before saving
            save_df = edited_df.copy()
            try:
                if "PurchaseDate" in save_df.columns:
                    save_df["PurchaseDate"] = save_df["PurchaseDate"].dt.strftime('%m/%d/%Y')
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
    Render the equipment expense calculation results with lease expenses.
    
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
        lease_total = grand_total.get('TotalLeaseExpense', 0)
        if lease_total > 0:
            st_obj.metric("Total Lease Expenses", f"${lease_total:,.2f}")
        else:
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
    for col in ['PurchaseCost', 'AnnualDepreciation', 'LeaseExpense', 'ServiceCost', 
               'AccreditationCost', 'InsuranceCost', 'TravelExpense', 'TotalAnnualExpense']:
        if col in display_df.columns:
            display_df[col] = display_df[col].map('${:,.2f}'.format)
    
    st_obj.dataframe(display_df)
    
    # 1. Annual Expenses by Equipment Type and Acquisition Method
    st_obj.subheader("Annual Expenses by Equipment Type")
    
    if 'Title' in annual_expenses.columns:
        fig1, ax1 = plt.subplots(figsize=(12, 6))
        
        # Split data into leased and purchased equipment
        leased_equipment = expenses_by_equipment[expenses_by_equipment['IsLeased'] == True]
        purchased_equipment = expenses_by_equipment[expenses_by_equipment['IsLeased'] == False]
        
        # Create stacked bar chart - purchased equipment expenses
        purchased_data = []
        purchased_titles = []
        if not purchased_equipment.empty:
            purchased_titles = purchased_equipment['Title'].tolist()
            
            # Create data for plotting
            depreciation = purchased_equipment.get('AnnualDepreciation', pd.Series([0] * len(purchased_equipment))).tolist()
            service = purchased_equipment.get('ServiceCost', pd.Series([0] * len(purchased_equipment))).tolist()
            accreditation = purchased_equipment.get('AccreditationCost', pd.Series([0] * len(purchased_equipment))).tolist()
            insurance = purchased_equipment.get('InsuranceCost', pd.Series([0] * len(purchased_equipment))).tolist()
            travel = purchased_equipment.get('TravelExpense', pd.Series([0] * len(purchased_equipment))).tolist()
            
            width = 0.35
            x_pos = np.arange(len(purchased_titles))
            
            # Create stacked bars for purchased equipment
            if len(x_pos) > 0:
                ax1.bar(x_pos, depreciation, width, label='Depreciation', color='#1f77b4')
                ax1.bar(x_pos, service, width, bottom=depreciation, label='Service', color='#ff7f0e')
                ax1.bar(x_pos, accreditation, width, bottom=[d+s for d,s in zip(depreciation, service)], label='Accreditation', color='#2ca02c')
                ax1.bar(x_pos, insurance, width, bottom=[d+s+a for d,s,a in zip(depreciation, service, accreditation)], label='Insurance', color='#d62728')
                ax1.bar(x_pos, travel, width, bottom=[d+s+a+i for d,s,a,i in zip(depreciation, service, accreditation, insurance)], label='Travel', color='#9467bd')
        
        # Leased equipment expenses
        leased_data = []
        leased_titles = []
        if not leased_equipment.empty:
            leased_titles = leased_equipment['Title'].tolist()
            
            # Create data for plotting
            lease = leased_equipment.get('LeaseExpense', pd.Series([0] * len(leased_equipment))).tolist()
            service = leased_equipment.get('ServiceCost', pd.Series([0] * len(leased_equipment))).tolist()
            accreditation = leased_equipment.get('AccreditationCost', pd.Series([0] * len(leased_equipment))).tolist()
            insurance = leased_equipment.get('InsuranceCost', pd.Series([0] * len(leased_equipment))).tolist()
            travel = leased_equipment.get('TravelExpense', pd.Series([0] * len(leased_equipment))).tolist()
            
            width = 0.35
            x_pos = np.arange(len(leased_titles)) + len(purchased_titles) + 1  # Offset for purchased equipment
            
            # Create stacked bars for leased equipment
            if len(x_pos) > 0:
                ax1.bar(x_pos, lease, width, label='Lease Payment', color='#8c564b')
                ax1.bar(x_pos, service, width, bottom=lease, label='Service' if len(purchased_titles) == 0 else "", color='#ff7f0e')
                ax1.bar(x_pos, accreditation, width, bottom=[l+s for l,s in zip(lease, service)], label='Accreditation' if len(purchased_titles) == 0 else "", color='#2ca02c')
                ax1.bar(x_pos, insurance, width, bottom=[l+s+a for l,s,a in zip(lease, service, accreditation)], label='Insurance' if len(purchased_titles) == 0 else "", color='#d62728')
                ax1.bar(x_pos, travel, width, bottom=[l+s+a+i for l,s,a,i in zip(lease, service, accreditation, insurance)], label='Travel' if len(purchased_titles) == 0 else "", color='#9467bd')
        
        # Combine titles and set axes
        all_titles = purchased_titles + leased_titles
        all_x_pos = list(range(len(all_titles)))
        
        # Set axes and labels
        ax1.set_title('Annual Expenses by Equipment Type')
        ax1.set_xlabel('Equipment')
        ax1.set_ylabel('Annual Expense ($)')
        ax1.set_xticks(all_x_pos)
        ax1.set_xticklabels(all_titles, rotation=45, ha='right')
        ax1.grid(axis='y', linestyle='--', alpha=0.7)
        ax1.legend()
        
        # Format y-axis with dollar signs
        fmt = '${x:,.0f}'
        tick = mticker.StrMethodFormatter(fmt)
        ax1.yaxis.set_major_formatter(tick)
        
        # Add a dashed line between purchased and leased
        if len(purchased_titles) > 0 and len(leased_titles) > 0:
            ax1.axvline(x=len(purchased_titles) - 0.5, color='black', linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        st_obj.pyplot(fig1)
        
        # Add an explanation about leased vs purchased equipment
        if len(purchased_titles) > 0 and len(leased_titles) > 0:
            st_obj.info(
                "The chart shows both purchased equipment (left) with depreciation expense and "
                "leased equipment (right) with lease payments. Both types incur service, accreditation, "
                "insurance, and travel costs."
            )
    
    # 2. Annual Expenses Over Time with lease vs purchase breakdown
    st_obj.subheader("Equipment Expenses Over Time")
    
    if 'Year' in annual_expenses.columns:
        # Group expenses by year and track lease vs depreciation
        yearly_expenses = annual_expenses.groupby('Year').agg({
            'LeaseExpense': 'sum',
            'AnnualDepreciation': 'sum',
            'ServiceCost': 'sum',
            'AccreditationCost': 'sum',
            'InsuranceCost': 'sum',
            'TravelExpense': 'sum',
            'TotalAnnualExpense': 'sum'
        })
        
        # Create line chart of expenses over time
        fig3, ax3 = plt.subplots(figsize=(12, 6))
        
        # Plot lines with markers for each expense type
        years = yearly_expenses.index.tolist()
        
        # Plot both lease and depreciation expenses
        if 'LeaseExpense' in yearly_expenses.columns and yearly_expenses['LeaseExpense'].sum() > 0:
            yearly_expenses['LeaseExpense'].plot(
                kind='line', 
                marker='o',
                ax=ax3,
                linewidth=3,
                color='#8c564b',
                label='Lease Payments'
            )
        
        if 'AnnualDepreciation' in yearly_expenses.columns and yearly_expenses['AnnualDepreciation'].sum() > 0:
            yearly_expenses['AnnualDepreciation'].plot(
                kind='line', 
                marker='x',
                ax=ax3,
                linewidth=3,
                color='#1f77b4',
                label='Depreciation'
            )
        
        # Add other expense lines
        if 'ServiceCost' in yearly_expenses.columns:
            yearly_expenses['ServiceCost'].plot(
                kind='line', 
                marker='s',
                ax=ax3,
                linewidth=3,
                linestyle='--',
                color='#ff7f0e',
                label='Service Cost'
            )
        
        if 'AccreditationCost' in yearly_expenses.columns:
            yearly_expenses['AccreditationCost'].plot(
                kind='line', 
                marker='^',
                ax=ax3,
                linewidth=3,
                linestyle=':',
                color='#2ca02c',
                label='Accreditation Cost'
            )
        
        if 'InsuranceCost' in yearly_expenses.columns:
            yearly_expenses['InsuranceCost'].plot(
                kind='line', 
                marker='d',
                ax=ax3,
                linewidth=3,
                linestyle='-.',
                color='#d62728',
                label='Insurance Cost'
            )
        
        if 'TravelExpense' in yearly_expenses.columns:
            yearly_expenses['TravelExpense'].plot(
                kind='line', 
                marker='p',
                ax=ax3,
                linewidth=3,
                linestyle='-.',
                color='#9467bd',
                label='Travel Expense'
            )
        
        # Plot total annual expense
        if 'TotalAnnualExpense' in yearly_expenses.columns:
            yearly_expenses['TotalAnnualExpense'].plot(
                kind='line', 
                marker='*',
                ax=ax3,
                linewidth=4,
                color='black',
                label='Total Expenses'
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
        for column in yearly_expenses.columns:
            if yearly_expenses[column].sum() > 0:
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
        
        # 4. Lease vs Purchase Cost Comparison
        st_obj.subheader("Lease vs Purchase Cost Comparison")
        
        # Check if we have both leased and purchased equipment
        has_leased = len(leased_equipment) > 0
        has_purchased = len(purchased_equipment) > 0
        
        if has_leased and has_purchased:
            # Create comparison chart
            fig4, ax4 = plt.subplots(figsize=(12, 6))
            
            # Create a summary of total costs by year for leased vs purchased
            annual_expenses['IsLeased'] = annual_expenses['IsLeased'].astype(bool)
            
            lease_by_year = annual_expenses[annual_expenses['IsLeased']].groupby('Year')['TotalAnnualExpense'].sum()
            purchase_by_year = annual_expenses[~annual_expenses['IsLeased']].groupby('Year')['TotalAnnualExpense'].sum()
            
            # Plot the comparison
            if not lease_by_year.empty:
                lease_by_year.plot(
                    kind='bar',
                    ax=ax4,
                    position=0,
                    width=0.4,
                    color='#e74c3c',
                    label='Leased Equipment'
                )
            
            if not purchase_by_year.empty:
                purchase_by_year.plot(
                    kind='bar',
                    ax=ax4,
                    position=1,
                    width=0.4,
                    color='#3498db',
                    label='Purchased Equipment'
                )
            
            ax4.set_title('Annual Costs: Lease vs Purchase')
            ax4.set_xlabel('Year')
            ax4.set_ylabel('Annual Cost ($)')
            ax4.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Format y-axis with dollar signs
            fmt = '${x:,.0f}'
            tick = mticker.StrMethodFormatter(fmt)
            ax4.yaxis.set_major_formatter(tick)
            
            # Add legend
            ax4.legend()
            
            plt.tight_layout()
            st_obj.pyplot(fig4)
            
            # Add analysis and explanation
            st_obj.markdown("""
            ### Lease vs Purchase Analysis
            
            Leasing equipment typically results in:
            - Lower upfront costs (no large capital expenditure)
            - Higher annual expenses (lease payments instead of depreciation)
            - Easier equipment upgrades at the end of the lease term
            - Maintenance often included in the lease agreement
            
            Purchasing equipment typically results in:
            - Higher upfront costs (capital expenditure)
            - Lower long-term costs once the equipment is fully depreciated
            - Asset ownership at the end of the depreciation period
            - Responsible for all maintenance and upgrades
            """)
        elif has_leased:
            st_obj.info("All equipment is leased. No purchase comparison available.")
        elif has_purchased:
            st_obj.info("All equipment is purchased. No lease comparison available.")