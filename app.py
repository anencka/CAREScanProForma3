import streamlit as st
import pandas as pd
import json
import os
import re
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List
from financeModels.personnel_expenses import PersonnelExpenseCalculator, calculate_personnel_expenses
from financeModels.exam_revenue import ExamRevenueCalculator, calculate_exam_revenue
from financeModels.equipment_expenses import EquipmentExpenseCalculator, calculate_equipment_expenses
from financeModels.other_expenses import OtherExpensesCalculator, calculate_other_expenses
from financeModels.comprehensive_proforma import ComprehensiveProformaCalculator, calculate_comprehensive_proforma

# Set page configuration
st.set_page_config(
    page_title="CAREScan ProForma Editor",
    page_icon="📊",
    layout="wide"
)

# Constants
CSV_FILES = {
    "Revenue": "Revenue.csv",
    "Equipment": "Equipment.csv",
    "Personnel": "Personnel.csv",
    "Exams": "Exams.csv",
    "OtherExpenses": "OtherExpenses.csv"
}

# Helper functions
def convert_underscore_numbers(value):
    """Convert string numbers with underscores to integers or floats."""
    if isinstance(value, str):
        # If it's a string that looks like a number with underscores
        if re.match(r'^\d+(_\d+)*(\.\d+)?$', value):
            # Remove underscores and convert to number
            return float(value.replace('_', ''))
    return value

def process_value_for_display(value):
    """Format values for display in the data editor."""
    if isinstance(value, str) and ';' in value:
        # Clean up the semicolon-separated values
        items = [item.strip() for item in value.split(';') if item.strip()]
        return '; '.join(items)
    return value

def process_value_for_save(value):
    """Format values for saving to CSV."""
    if isinstance(value, (list, tuple)):
        # Convert lists back to semicolon-separated strings
        return '; '.join(str(item) for item in value) + ';'
    return value

def load_csv(filepath: str) -> pd.DataFrame:
    """Load CSV data from file."""
    try:
        # Handle the specific format of these CSVs with spaces after commas
        df = pd.read_csv(filepath, skipinitialspace=True)
        
        # Process numeric values with underscores
        for col in df.columns:
            df[col] = df[col].apply(convert_underscore_numbers)
            
        # Process semicolon-separated values
        for col in df.columns:
            if df[col].dtype == 'object':  # Only process string columns
                df[col] = df[col].apply(process_value_for_display)
        
        return df
    except Exception as e:
        st.error(f"Error loading {filepath}: {e}")
        return pd.DataFrame()

def save_csv(df: pd.DataFrame, filepath: str) -> bool:
    """Save DataFrame to CSV file."""
    try:
        # Process values for saving
        save_df = df.copy()
        for col in save_df.columns:
            save_df[col] = save_df[col].apply(process_value_for_save)
        
        save_df.to_csv(filepath, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving {filepath}: {e}")
        return False

def export_to_json(data_dict: Dict[str, pd.DataFrame], filepath: str) -> bool:
    """Export all data to a JSON file."""
    try:
        # Convert DataFrames to serializable format
        json_dict = {}
        for key, df in data_dict.items():
            # Ensure we're working with a pandas DataFrame
            if not isinstance(df, pd.DataFrame):
                st.warning(f"'{key}' is not a DataFrame. Attempting conversion.")
                try:
                    df = pd.DataFrame(df)
                except Exception as e:
                    st.error(f"Could not convert '{key}' to DataFrame: {str(e)}")
                    # Skip this item
                    continue
            
            # Process values for JSON export
            export_df = df.copy()
            for col in export_df.columns:
                export_df[col] = export_df[col].apply(process_value_for_save)
            
            json_dict[key] = export_df.to_dict(orient='records')
        
        with open(filepath, 'w') as f:
            json.dump(json_dict, f, indent=2)
        
        return True
    except Exception as e:
        import traceback
        st.error(f"Error exporting to JSON: {str(e)}")
        st.error(traceback.format_exc())
        return False

def import_from_json(filepath: str) -> Dict[str, pd.DataFrame]:
    """Import data from a JSON file."""
    try:
        with open(filepath, 'r') as f:
            json_dict = json.load(f)
        
        data_dict = {}
        for key, records in json_dict.items():
            try:
                # Make sure we have a list of records
                if not isinstance(records, list):
                    st.warning(f"Converting {key} from unexpected format")
                    if isinstance(records, dict):
                        # If it's a dict, try to convert to list of records
                        records = [records]
                    else:
                        # Skip this key if we can't convert
                        st.error(f"Skipping {key} - unexpected format: {type(records)}")
                        continue
                
                # Create DataFrame from records
                df = pd.DataFrame.from_records(records)
                
                # Process values after import
                for col in df.columns:
                    df[col] = df[col].apply(convert_underscore_numbers)
                    if df[col].dtype == 'object':
                        df[col] = df[col].apply(process_value_for_display)
                
                data_dict[key] = df
            except Exception as e:
                st.error(f"Error processing {key}: {str(e)}")
                import traceback
                st.error(traceback.format_exc())
        
        return data_dict
    except Exception as e:
        import traceback
        st.error(f"Error importing from JSON: {str(e)}")
        st.error(traceback.format_exc())
        return {}

# Application title
st.title("CAREScan ProForma Editor")

# Initialize session state
if 'dataframes' not in st.session_state:
    st.session_state.dataframes = {}
    for name, file in CSV_FILES.items():
        st.session_state.dataframes[name] = load_csv(file)

# Create tabs for each CSV file plus visualization tabs and Export/Import
tabs = st.tabs([
    "Revenue", "Equipment", "Personnel", "Exams", "OtherExpenses",  # CSV Editor tabs
    "Personnel Expense Plots", "Equipment Expense Plots", "Exam Revenue Analysis", "Other Expense Plots", 
    "Export/Import", "Comprehensive Proforma"
])

# CSV Editor tabs
for i, name in enumerate(CSV_FILES.keys()):
    with tabs[i]:
        st.header(f"{name} Data")
        
        # Information about editing
        st.info(
            "Edit the data directly in the table below. "
            "For semicolon-separated lists, use commas or semicolons to separate values. "
            "For large numbers, you can use underscores for readability (e.g., 200_000 or 200000)."
        )
        
        # Create an editable dataframe
        edited_df = st.data_editor(
            st.session_state.dataframes[name],
            use_container_width=True,
            num_rows="dynamic",
            key=f"editor_{name}"
        )
        
        # Save button for each tab
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button(f"Save {name}", key=f"save_{name}"):
                try:
                    # Get editor data
                    editor_data = st.session_state[f"editor_{name}"]
                    
                    # Convert to DataFrame if needed
                    if isinstance(editor_data, pd.DataFrame):
                        # Already a DataFrame
                        df_to_save = editor_data
                    elif isinstance(editor_data, dict):
                        # Try to convert dict to DataFrame
                        if all(isinstance(v, dict) for v in editor_data.values()):
                            # Dict of dicts (row_index -> row_data)
                            rows = list(editor_data.values())
                            df_to_save = pd.DataFrame(rows)
                        else:
                            st.error(f"Could not convert {name} data to DataFrame - unexpected structure.")
                            df_to_save = None
                    else:
                        st.error(f"Unexpected data type for {name}: {type(editor_data)}")
                        df_to_save = None
                    
                    # Save if we successfully got a DataFrame
                    if df_to_save is not None:
                        if save_csv(df_to_save, CSV_FILES[name]):
                            st.session_state.dataframes[name] = df_to_save
                            st.success(f"{name} data saved successfully!")
                
                except Exception as e:
                    import traceback
                    st.error(f"Error saving {name}: {str(e)}")
                    st.error(traceback.format_exc())

# Personnel Expense Plots tab
with tabs[5]:
    st.header("Personnel Expense Plots")
    
    # Explanation of these plots
    st.info(
        "This tab visualizes the personnel expenses based on the Personnel.csv data. "
        "It shows annual expenses, expenses by institution and staff type, and headcount over time."
    )
    
    # Date range selection
    st.subheader("Select Date Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=pd.to_datetime("01/01/2025"), format="MM/DD/YYYY", key="personnel_start_date")
        start_date_str = start_date.strftime("%m/%d/%Y")
    with col2:
        end_date = st.date_input("End Date", value=pd.to_datetime("12/31/2029"), format="MM/DD/YYYY", key="personnel_end_date")
        end_date_str = end_date.strftime("%m/%d/%Y")
    
    # Generate visualizations
    if st.button("Generate Personnel Expense Plots", key="generate_personnel_plots"):
        try:
            with st.spinner("Calculating personnel expenses and generating plots..."):
                # Check if Personnel data is available
                if 'Personnel' not in st.session_state.dataframes or st.session_state.dataframes['Personnel'].empty:
                    st.error("Personnel data is not available. Please upload Personnel.csv file.")
                else:
                    # Calculate personnel expenses
                    personnel_data = st.session_state.dataframes['Personnel']
                    results = calculate_personnel_expenses(
                        personnel_data=personnel_data,
                        start_date=start_date_str,
                        end_date=end_date_str
                    )
                    
                    # Display the first visualizations
                    st.subheader("Total Personnel Expenses by Year")
                    annual_df = results['annual']
                    
                    fig1, ax1 = plt.subplots(figsize=(12, 6))
                    annual_totals = annual_df.groupby('Year')['Total_Expense'].sum()
                    annual_totals.plot(kind='bar', color='skyblue', ax=ax1)
                    ax1.set_title('Total Personnel Expenses by Year')
                    ax1.set_xlabel('Year')
                    ax1.set_ylabel('Total Expense ($)')
                    ax1.grid(axis='y', linestyle='--', alpha=0.7)
                    ax1.tick_params(axis='x', rotation=0)
                    st.pyplot(fig1)
                    
                    # Display summary of annual expenses
                    st.dataframe(annual_totals.reset_index().rename(
                        columns={'Year': 'Year', 'Total_Expense': 'Total Expense ($)'}
                    ))
                    
                    # Display visualization 2: Expenses by institution and type
                    st.subheader("Personnel Expenses by Institution and Type")
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
                    st.pyplot(fig2)
                    
                    # Display summary of category expenses
                    st.dataframe(category_df)
                    
                    # Display visualization 3: Headcount over time
                    st.subheader("FTE Count Over Time by Staff Type")
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
                    st.pyplot(fig3)
                    
                    # Display grand total
                    st.subheader("Grand Total")
                    grand_total = results['grand_total']
                    
                    # Format with commas for thousands
                    formatted_grand_total = {
                        'Base Expense': f"${grand_total['Base_Expense']:,.2f}",
                        'Fringe Amount': f"${grand_total['Fringe_Amount']:,.2f}",
                        'Total Expense': f"${grand_total['Total_Expense']:,.2f}"
                    }
                    
                    # Display as a table
                    st.table(pd.DataFrame([formatted_grand_total]))
        
        except Exception as e:
            import traceback
            st.error(f"Error generating personnel expense plots: {str(e)}")
            st.error(traceback.format_exc())

# Equipment Expense Plots tab
with tabs[6]:
    st.header("Equipment Expense Plots")
    
    # Explanation of these plots
    st.info(
        "This tab visualizes equipment expenses and depreciation based on the Equipment.csv data. "
        "It shows annual expenses by category, equipment depreciation over time, and total costs."
    )
    
    # Date Range Selection
    st.subheader("Select Date Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=pd.to_datetime("01/01/2025", format='%m/%d/%Y'),
            min_value=pd.to_datetime("01/01/2020", format='%m/%d/%Y'),
            max_value=pd.to_datetime("12/31/2040", format='%m/%d/%Y'),
            key="equipment_start_date"
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=pd.to_datetime("12/31/2035", format='%m/%d/%Y'),
            min_value=pd.to_datetime("01/01/2020", format='%m/%d/%Y'),
            max_value=pd.to_datetime("12/31/2040", format='%m/%d/%Y'),
            key="equipment_end_date"
        )
    
    # Travel parameters
    st.subheader("Travel Parameters")
    travel_col1, travel_col2 = st.columns(2)
    with travel_col1:
        days_between_travel = st.number_input(
            "Days Between Travel",
            min_value=1,
            max_value=30,
            value=5,
            help="Number of days between travel events",
            key="equipment_days_between_travel"
        )
    with travel_col2:
        miles_per_travel = st.number_input(
            "Miles Per Travel",
            min_value=1,
            max_value=100,
            value=20,
            help="Number of miles traveled in each travel event",
            key="equipment_miles_per_travel"
        )
    
    # Generate visualizations
    if st.button("Generate Equipment Expense Plots", key="generate_equipment_plots"):
        try:
            with st.spinner("Calculating equipment expenses and generating plots..."):
                # Check if equipment data is available
                if 'Equipment' not in st.session_state.dataframes or st.session_state.dataframes['Equipment'].empty:
                    st.error("Equipment data is not available. Please upload Equipment.csv file.")
                else:
                    # Convert dates to string format for the calculator
                    start_date_str = start_date.strftime('%m/%d/%Y')
                    end_date_str = end_date.strftime('%m/%d/%Y')
                    
                    # Initialize the calculator with travel parameters
                    equipment_data = st.session_state.dataframes['Equipment']
                    calculator = EquipmentExpenseCalculator(
                        equipment_data=equipment_data,
                        days_between_travel=days_between_travel,
                        miles_per_travel=miles_per_travel
                    )
                    
                    # Calculate equipment expenses
                    annual_expenses = calculator.calculate_annual_expenses(start_date_str, end_date_str)
                    expenses_by_equipment = calculator.calculate_total_by_equipment(start_date_str, end_date_str)
                    grand_total = calculator.calculate_grand_total(start_date_str, end_date_str)
                    
                    if annual_expenses.empty:
                        st.warning("No equipment expenses found in the selected date range.")
                    else:
                        # Display key metrics
                        st.subheader("Key Metrics Summary")
                        
                        # Display total metrics in columns
                        metric_col1, metric_col2, metric_col3 = st.columns(3)
                        with metric_col1:
                            st.metric("Total Purchase Cost", f"${grand_total['TotalPurchaseCost']:,.2f}")
                        with metric_col2:
                            st.metric("Total Depreciation", f"${grand_total['TotalDepreciation']:,.2f}")
                        with metric_col3:
                            st.metric("Total Annual Expenses", f"${grand_total['TotalAnnualExpense']:,.2f}")
                        
                        # Display recurring expenses in columns
                        expense_col1, expense_col2, expense_col3, expense_col4 = st.columns(4)
                        with expense_col1:
                            st.metric("Service Costs", f"${grand_total['TotalServiceCost']:,.2f}")
                        with expense_col2:
                            st.metric("Accreditation Costs", f"${grand_total['TotalAccreditationCost']:,.2f}")
                        with expense_col3:
                            st.metric("Insurance Costs", f"${grand_total['TotalInsuranceCost']:,.2f}")
                        with expense_col4:
                            st.metric("Travel Costs", f"${grand_total['TotalTravelExpense']:,.2f}")
                        
                        # Display equipment summary table
                        st.subheader("Equipment Expense Summary")
                        
                        # Format the table for display
                        display_df = expenses_by_equipment.copy()
                        for col in ['PurchaseCost', 'AnnualDepreciation', 'ServiceCost', 
                                  'AccreditationCost', 'InsuranceCost', 'TravelExpense', 'TotalAnnualExpense']:
                            if col in display_df.columns:
                                display_df[col] = display_df[col].map('${:,.2f}'.format)
                        
                        st.dataframe(display_df)
                        
                        # 1. Annual Expenses by Equipment Type
                        st.subheader("Annual Expenses by Equipment Type")
                        fig1, ax1 = plt.subplots(figsize=(12, 6))
                        
                        # Plot stacked bar chart of expenses by equipment type
                        pivot_df = annual_expenses.pivot_table(
                            index='Title',
                            values=['ServiceCost', 'AccreditationCost', 'InsuranceCost', 'TravelExpense'],
                            aggfunc='sum'
                        )
                        
                        pivot_df.plot(kind='bar', stacked=True, ax=ax1)
                        ax1.set_title('Annual Expenses by Equipment Type')
                        ax1.set_xlabel('Equipment')
                        ax1.set_ylabel('Annual Expense ($)')
                        ax1.grid(axis='y', linestyle='--', alpha=0.7)
                        plt.xticks(rotation=45)
                        plt.tight_layout()
                        st.pyplot(fig1)
                        
                        # 2. Annual Depreciation by Equipment Type
                        st.subheader("Annual Depreciation by Equipment Type")
                        fig2, ax2 = plt.subplots(figsize=(12, 6))
                        
                        # Plot bar chart of annual depreciation
                        depreciation_by_equipment = expenses_by_equipment.set_index('Title')['AnnualDepreciation']
                        depreciation_by_equipment.plot(kind='bar', ax=ax2, color='skyblue')
                        ax2.set_title('Annual Depreciation by Equipment Type')
                        ax2.set_xlabel('Equipment')
                        ax2.set_ylabel('Annual Depreciation ($)')
                        ax2.grid(axis='y', linestyle='--', alpha=0.7)
                        
                        for i, v in enumerate(depreciation_by_equipment):
                            ax2.text(i, v + 0.1, f"${v:,.0f}", ha='center')
                        
                        plt.xticks(rotation=45)
                        plt.tight_layout()
                        st.pyplot(fig2)
                        
                        # 3. Annual Expenses Over Time
                        st.subheader("Equipment Expenses Over Time")
                        
                        if 'Year' in annual_expenses.columns:
                            # Group expenses by year
                            yearly_expenses = annual_expenses.groupby('Year').agg({
                                'ServiceCost': 'sum',
                                'AccreditationCost': 'sum',
                                'InsuranceCost': 'sum',
                                'TravelExpense': 'sum',
                                'AnnualDepreciation': 'sum',
                                'TotalAnnualExpense': 'sum'
                            })
                            
                            # Create line chart of expenses over time
                            fig3, ax3 = plt.subplots(figsize=(12, 6))
                            
                            # Use distinct colors, line styles, and markers for each expense type
                            yearly_expenses['ServiceCost'].plot(
                                kind='line', 
                                marker='o',
                                ax=ax3,
                                linewidth=3,
                                color='darkblue',
                                label='Service Cost'
                            )
                            
                            yearly_expenses['AccreditationCost'].plot(
                                kind='line', 
                                marker='s',
                                ax=ax3,
                                linewidth=3,
                                linestyle='--',
                                color='darkgreen',
                                label='Accreditation Cost'
                            )
                            
                            yearly_expenses['InsuranceCost'].plot(
                                kind='line', 
                                marker='^',
                                ax=ax3,
                                linewidth=3,
                                linestyle=':',
                                color='darkred',
                                label='Insurance Cost'
                            )
                            
                            yearly_expenses['TravelExpense'].plot(
                                kind='line', 
                                marker='d',
                                ax=ax3,
                                linewidth=3,
                                linestyle='-.',
                                color='darkorange',
                                label='Travel Expense'
                            )
                            
                            yearly_expenses['AnnualDepreciation'].plot(
                                kind='line', 
                                marker='x',
                                ax=ax3,
                                linewidth=3,
                                color='purple',
                                label='Annual Depreciation'
                            )
                            
                            ax3.set_title('Equipment Expenses Over Time')
                            ax3.set_xlabel('Year')
                            ax3.set_ylabel('Expense Amount ($)')
                            ax3.grid(True, linestyle='--', alpha=0.7)
                            
                            # Format y-axis with dollar signs
                            import matplotlib.ticker as mtick
                            ax3.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
                            
                            # Ensure legend is visible and clear
                            ax3.legend(loc='best', frameon=True, fancybox=True, shadow=True)
                            
                            # Add data labels to the end points for better readability
                            for column in ['ServiceCost', 'AccreditationCost', 'InsuranceCost', 'TravelExpense', 'AnnualDepreciation']:
                                last_year = yearly_expenses.index[-1]
                                last_value = yearly_expenses.loc[last_year, column]
                                ax3.annotate(f'${last_value:,.0f}', 
                                            xy=(last_year, last_value),
                                            xytext=(10, 0),
                                            textcoords='offset points',
                                            va='center')
                            
                            plt.tight_layout()
                            st.pyplot(fig3)
                            
                            # Format and display the yearly expenses table with dollar formatting
                            display_yearly = yearly_expenses.reset_index().copy()
                            for col in display_yearly.columns:
                                if col != 'Year':
                                    display_yearly[col] = display_yearly[col].map('${:,.2f}'.format)
                            
                            st.dataframe(display_yearly)
                            
                            # 4. Total Annual Cost vs. Depreciation
                            st.subheader("Total Annual Cost vs. Depreciation")
                            
                            fig4, ax4 = plt.subplots(figsize=(12, 6))
                            
                            # Create a new DataFrame with just Annual Expenses and Depreciation
                            cost_vs_depreciation = pd.DataFrame({
                                'Annual Expenses': yearly_expenses['TotalAnnualExpense'],
                                'Annual Depreciation': yearly_expenses['AnnualDepreciation']
                            })
                            
                            cost_vs_depreciation.plot(kind='bar', ax=ax4)
                            ax4.set_title('Total Annual Cost vs. Depreciation')
                            ax4.set_xlabel('Year')
                            ax4.set_ylabel('Amount ($)')
                            ax4.grid(axis='y', linestyle='--', alpha=0.7)
                            plt.tight_layout()
                            st.pyplot(fig4)
        except Exception as e:
            import traceback
            st.error(f"Error generating equipment expense plots: {str(e)}")
            st.error(traceback.format_exc())

# Exam Revenue Analysis tab
with tabs[7]:
    st.header("Exam Revenue Analysis")
    
    # Explanation of these plots
    st.info(
        "This tab analyzes exam revenue based on the Exams.csv and Revenue.csv data. "
        "It shows annual exam volume, revenue by source, and projected net revenue."
    )
    
    # Year range selection
    st.subheader("Select Year Range")
    col1, col2 = st.columns(2)
    with col1:
        start_year = st.number_input("Start Year", min_value=2025, max_value=2040, value=2026, key="exam_start_year")
    with col2:
        end_year = st.number_input("End Year", min_value=2025, max_value=2040, value=2030, key="exam_end_year")
    
    # Revenue source selection
    st.subheader("Select Revenue Sources")
    if 'Revenue' in st.session_state.dataframes:
        revenue_sources = st.session_state.dataframes['Revenue']['Title'].tolist()
        selected_sources = st.multiselect("Revenue Sources", revenue_sources, default=revenue_sources, key="exam_revenue_sources")
    else:
        selected_sources = []
        st.error("Revenue data is not available. Please upload Revenue.csv file.")
    
    # Working days per year option
    work_days = st.number_input("Working Days Per Year", min_value=200, max_value=300, value=250, key="exam_work_days")
    
    # Generate visualizations
    if st.button("Generate Exam Revenue Analysis", key="generate_exam_analysis"):
        try:
            with st.spinner("Calculating exam revenue and generating plots..."):
                # Check if required data is available
                required_tables = ['Revenue', 'Exams', 'Personnel', 'Equipment']
                missing_tables = [table for table in required_tables if table not in st.session_state.dataframes or st.session_state.dataframes[table].empty]
                
                if missing_tables:
                    st.error(f"The following required data is missing: {', '.join(missing_tables)}")
                elif not selected_sources:
                    st.error("Please select at least one revenue source.")
                else:
                    # Initialize the calculator
                    calculator = ExamRevenueCalculator(
                        exams_data=st.session_state.dataframes['Exams'],
                        revenue_data=st.session_state.dataframes['Revenue'],
                        personnel_data=st.session_state.dataframes['Personnel'],
                        equipment_data=st.session_state.dataframes['Equipment'],
                        start_date=start_date.strftime('%m/%d/%Y')
                    )
                    
                    # Calculate exam revenue for all selected sources
                    results = calculator.calculate_multi_year_exam_revenue(
                        start_year=start_year,
                        end_year=end_year,
                        revenue_sources=selected_sources,
                        work_days_per_year=work_days
                    )
                    
                    if results.empty:
                        st.warning("No exam revenue data could be calculated. This might be because there is no equipment or required staff available during the selected period.")
                    else:
                        # Display key metrics
                        st.subheader("Key Metrics Summary")
                        
                        # Calculate summary metrics
                        total_volume = results['AnnualVolume'].sum()
                        total_revenue = results['Total_Revenue'].sum()
                        total_expenses = results['Total_Direct_Expenses'].sum()
                        net_revenue = results['Net_Revenue'].sum()
                        
                        # Display metrics in columns
                        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                        with metric_col1:
                            st.metric("Total Exam Volume", f"{total_volume:,.0f}")
                        with metric_col2:
                            st.metric("Total Revenue", f"${total_revenue:,.2f}")
                        with metric_col3:
                            st.metric("Total Expenses", f"${total_expenses:,.2f}")
                        with metric_col4:
                            st.metric("Net Revenue", f"${net_revenue:,.2f}")
                        
                        # Display visualizations
                        
                        # 1. Total Revenue by Year and Revenue Source
                        st.subheader("Total Revenue by Year and Revenue Source")
                        fig1, ax1 = plt.subplots(figsize=(12, 6))
                        revenue_by_source = results.groupby(['Year', 'RevenueSource'])['Total_Revenue'].sum().unstack()
                        revenue_by_source.plot(kind='bar', stacked=True, ax=ax1, colormap='viridis')
                        ax1.set_title('Total Revenue by Year and Revenue Source')
                        ax1.set_xlabel('Year')
                        ax1.set_ylabel('Revenue ($)')
                        ax1.grid(axis='y', linestyle='--', alpha=0.7)
                        ax1.legend(title='Revenue Source')
                        st.pyplot(fig1)
                        
                        # Show summary table
                        st.dataframe(revenue_by_source)
                        
                        # 2. Exam Volume by Year
                        st.subheader("Exam Volume by Year")
                        fig2, ax2 = plt.subplots(figsize=(12, 6))
                        volume_by_year = results.groupby('Year')['AnnualVolume'].sum()
                        volume_by_year.plot(kind='bar', ax=ax2, color='skyblue')
                        ax2.set_title('Total Exam Volume by Year')
                        ax2.set_xlabel('Year')
                        ax2.set_ylabel('Annual Volume')
                        ax2.grid(axis='y', linestyle='--', alpha=0.7)
                        for i, v in enumerate(volume_by_year):
                            ax2.text(i, v + 0.1, f"{v:,.0f}", ha='center')
                        st.pyplot(fig2)
                        
                        # 3. Revenue vs Expenses by Year
                        st.subheader("Revenue vs Expenses by Year")
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
                        st.pyplot(fig3)
                        
                        # 4. Top Exams by Revenue
                        st.subheader("Top Exams by Revenue")
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
                        st.pyplot(fig4)
                        
                        # 5. Detailed Data Table
                        st.subheader("Detailed Exam Revenue Data")
                        
                        # Create a summary by exam and year
                        summary_by_exam_year = results.groupby(['Year', 'Exam']).agg({
                            'AnnualVolume': 'sum',
                            'Total_Revenue': 'sum',
                            'Total_Direct_Expenses': 'sum',
                            'Net_Revenue': 'sum'
                        }).reset_index()
                        
                        # Format the summary for display
                        formatted_summary = summary_by_exam_year.copy()
                        formatted_summary['AnnualVolume'] = formatted_summary['AnnualVolume'].map('{:,.0f}'.format)
                        formatted_summary['Total_Revenue'] = formatted_summary['Total_Revenue'].map('${:,.2f}'.format)
                        formatted_summary['Total_Direct_Expenses'] = formatted_summary['Total_Direct_Expenses'].map('${:,.2f}'.format)
                        formatted_summary['Net_Revenue'] = formatted_summary['Net_Revenue'].map('${:,.2f}'.format)
                        
                        # Display the summary
                        st.dataframe(formatted_summary)
                        
                        # 6. Yearly Summary
                        st.subheader("Yearly Financial Summary")
                        yearly_summary = results.groupby('Year').agg({
                            'AnnualVolume': 'sum',
                            'Total_Revenue': 'sum',
                            'Total_Direct_Expenses': 'sum',
                            'Net_Revenue': 'sum'
                        }).reset_index()
                        
                        # Format the yearly summary
                        formatted_yearly = yearly_summary.copy()
                        formatted_yearly['AnnualVolume'] = formatted_yearly['AnnualVolume'].map('{:,.0f}'.format)
                        formatted_yearly['Total_Revenue'] = formatted_yearly['Total_Revenue'].map('${:,.2f}'.format)
                        formatted_yearly['Total_Direct_Expenses'] = formatted_yearly['Total_Direct_Expenses'].map('${:,.2f}'.format)
                        formatted_yearly['Net_Revenue'] = formatted_yearly['Net_Revenue'].map('${:,.2f}'.format)
                        
                        # Display the yearly summary
                        st.dataframe(formatted_yearly)
                        
                        # Allow user to download the results as CSV
                        st.subheader("Download Results")
                        csv = results.to_csv(index=False)
                        st.download_button(
                            label="Download Exam Revenue Data as CSV",
                            data=csv,
                            file_name="exam_revenue_analysis.csv",
                            mime="text/csv",
                        )
                        
                        # Add a section for results by individual revenue source
                        st.subheader("Results by Revenue Source")
                        st.info("This section shows detailed metrics and visualizations for each revenue source individually.")
                        
                        # Create an expander for each revenue source
                        for revenue_source in selected_sources:
                            with st.expander(f"Revenue Source: {revenue_source}", expanded=False):
                                # Filter results for this revenue source
                                source_results = results[results['RevenueSource'] == revenue_source]
                                
                                if source_results.empty:
                                    st.warning(f"No data available for revenue source: {revenue_source}")
                                    continue
                                
                                # Calculate key metrics for this revenue source
                                source_volume = source_results['AnnualVolume'].sum()
                                source_revenue = source_results['Total_Revenue'].sum()
                                source_expenses = source_results['Total_Direct_Expenses'].sum()
                                source_net = source_results['Net_Revenue'].sum()
                                
                                # Display metrics in columns
                                src_col1, src_col2, src_col3, src_col4 = st.columns(4)
                                with src_col1:
                                    st.metric("Total Volume", f"{source_volume:,.0f}")
                                with src_col2:
                                    st.metric("Total Revenue", f"${source_revenue:,.2f}")
                                with src_col3:
                                    st.metric("Total Expenses", f"${source_expenses:,.2f}")
                                with src_col4:
                                    st.metric("Net Revenue", f"${source_net:,.2f}")
                                
                                # Yearly trend for this revenue source
                                yearly_source = source_results.groupby('Year').agg({
                                    'AnnualVolume': 'sum',
                                    'Total_Revenue': 'sum', 
                                    'Total_Direct_Expenses': 'sum',
                                    'Net_Revenue': 'sum'
                                }).reset_index()
                                
                                # Plot yearly trend
                                fig_src1, ax_src1 = plt.subplots(figsize=(10, 5))
                                ax_src1.bar(yearly_source['Year'], yearly_source['AnnualVolume'], color='skyblue')
                                ax_src1.set_title(f'{revenue_source}: Annual Volume by Year')
                                ax_src1.set_xlabel('Year')
                                ax_src1.set_ylabel('Volume')
                                ax_src1.grid(axis='y', linestyle='--', alpha=0.7)
                                
                                # Add data labels
                                for i, v in enumerate(yearly_source['AnnualVolume']):
                                    ax_src1.text(yearly_source['Year'].iloc[i], v + 0.1, f"{v:,.0f}", ha='center')
                                
                                st.pyplot(fig_src1)
                                
                                # Plot revenue and expenses
                                fig_src2, ax_src2 = plt.subplots(figsize=(10, 5))
                                
                                yearly_source.plot(
                                    x='Year', 
                                    y=['Total_Revenue', 'Total_Direct_Expenses', 'Net_Revenue'],
                                    kind='bar',
                                    ax=ax_src2
                                )
                                
                                ax_src2.set_title(f'{revenue_source}: Financial Summary by Year')
                                ax_src2.set_xlabel('Year')
                                ax_src2.set_ylabel('Amount ($)')
                                ax_src2.grid(axis='y', linestyle='--', alpha=0.7)
                                ax_src2.legend(['Total Revenue', 'Total Expenses', 'Net Revenue'])
                                
                                st.pyplot(fig_src2)
                                
                                # Top exams for this revenue source
                                st.subheader(f"Top Exams for {revenue_source}")
                                source_by_exam = source_results.groupby('Exam').agg({
                                    'AnnualVolume': 'sum',
                                    'Total_Revenue': 'sum',
                                    'Total_Direct_Expenses': 'sum',
                                    'Net_Revenue': 'sum'
                                }).reset_index()
                                
                                # Sort by revenue
                                source_by_exam = source_by_exam.sort_values('Total_Revenue', ascending=False)
                                
                                # Format for display
                                formatted_source_exam = source_by_exam.copy()
                                formatted_source_exam['AnnualVolume'] = formatted_source_exam['AnnualVolume'].map('{:,.0f}'.format)
                                formatted_source_exam['Total_Revenue'] = formatted_source_exam['Total_Revenue'].map('${:,.2f}'.format)
                                formatted_source_exam['Total_Direct_Expenses'] = formatted_source_exam['Total_Direct_Expenses'].map('${:,.2f}'.format)
                                formatted_source_exam['Net_Revenue'] = formatted_source_exam['Net_Revenue'].map('${:,.2f}'.format)
                                
                                # Show the table
                                st.dataframe(formatted_source_exam)
                                
                                # Pie chart of exam volumes
                                fig_src3, ax_src3 = plt.subplots(figsize=(10, 8))
                                source_by_exam.plot(
                                    kind='pie',
                                    y='AnnualVolume',
                                    labels=source_by_exam['Exam'],
                                    autopct='%1.1f%%',
                                    startangle=90,
                                    ax=ax_src3,
                                    legend=False,
                                    colormap='viridis'
                                )
                                ax_src3.set_title(f'{revenue_source}: Distribution of Exam Volumes')
                                ax_src3.set_ylabel('')
                                
                                st.pyplot(fig_src3)
                                
                                # Yearly summary table for this revenue source
                                st.subheader(f"Yearly Summary for {revenue_source}")
                                
                                # Format the yearly summary for this source
                                formatted_yearly_source = yearly_source.copy()
                                formatted_yearly_source['AnnualVolume'] = formatted_yearly_source['AnnualVolume'].map('{:,.0f}'.format)
                                formatted_yearly_source['Total_Revenue'] = formatted_yearly_source['Total_Revenue'].map('${:,.2f}'.format)
                                formatted_yearly_source['Total_Direct_Expenses'] = formatted_yearly_source['Total_Direct_Expenses'].map('${:,.2f}'.format)
                                formatted_yearly_source['Net_Revenue'] = formatted_yearly_source['Net_Revenue'].map('${:,.2f}'.format)
                                
                                st.dataframe(formatted_yearly_source)
                                
                                # Monthly detail (estimated by dividing annual by 12)
                                st.subheader(f"Monthly Estimates for {revenue_source}")
                                
                                # Calculate monthly averages
                                monthly_source = yearly_source.copy()
                                monthly_source['MonthlyVolume'] = monthly_source['AnnualVolume'] / 12
                                monthly_source['MonthlyRevenue'] = monthly_source['Total_Revenue'] / 12
                                monthly_source['MonthlyExpenses'] = monthly_source['Total_Direct_Expenses'] / 12
                                monthly_source['MonthlyNetRevenue'] = monthly_source['Net_Revenue'] / 12
                                
                                # Format for display
                                formatted_monthly = monthly_source[['Year', 'MonthlyVolume', 'MonthlyRevenue', 'MonthlyExpenses', 'MonthlyNetRevenue']].copy()
                                formatted_monthly['MonthlyVolume'] = formatted_monthly['MonthlyVolume'].map('{:,.1f}'.format)
                                formatted_monthly['MonthlyRevenue'] = formatted_monthly['MonthlyRevenue'].map('${:,.2f}'.format)
                                formatted_monthly['MonthlyExpenses'] = formatted_monthly['MonthlyExpenses'].map('${:,.2f}'.format)
                                formatted_monthly['MonthlyNetRevenue'] = formatted_monthly['MonthlyNetRevenue'].map('${:,.2f}'.format)
                                
                                # Rename columns for clarity
                                formatted_monthly.columns = ['Year', 'Monthly Volume', 'Monthly Revenue', 'Monthly Expenses', 'Monthly Net Revenue']
                                
                                st.dataframe(formatted_monthly)
        
        except Exception as e:
            import traceback
            st.error(f"Error generating exam revenue analysis: {str(e)}")
            st.error(traceback.format_exc())

# Other Expense Plots tab
with tabs[8]:
    st.header("Other Expense Plots")
    
    # Explanation of these plots
    st.info(
        "This tab visualizes other expenses and revenue items from the OtherExpenses.csv data. "
        "It shows annual expenses by category, revenue items, and net totals."
    )
    
    # Date Range Selection
    st.subheader("Select Date Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=pd.to_datetime("01/01/2025", format='%m/%d/%Y'),
            min_value=pd.to_datetime("01/01/2020", format='%m/%d/%Y'),
            max_value=pd.to_datetime("12/31/2040", format='%m/%d/%Y'),
            key="other_expenses_start_date"
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=pd.to_datetime("12/31/2035", format='%m/%d/%Y'),
            min_value=pd.to_datetime("01/01/2020", format='%m/%d/%Y'),
            max_value=pd.to_datetime("12/31/2040", format='%m/%d/%Y'),
            key="other_expenses_end_date"
        )
    
    # Generate visualizations
    if st.button("Generate Other Expense Plots", key="generate_other_expense_plots"):
        try:
            # Initialize calculator with data
            other_calculator = OtherExpensesCalculator(other_data=st.session_state.dataframes['OtherExpenses'])
            
            # Format dates for the calculator
            start_str = start_date.strftime('%m/%d/%Y')
            end_str = end_date.strftime('%m/%d/%Y')
            
            # Calculate expenses and revenue
            annual_items = other_calculator.calculate_annual_items(start_str, end_str)
            category_data = other_calculator.calculate_by_category(start_str, end_str)
            summary = other_calculator.calculate_summary(start_str, end_str)
            
            # Display summary metrics
            st.subheader("Summary Metrics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Revenue", f"${summary['Total_Revenue']:,.2f}")
            with col2:
                st.metric("Total Expenses", f"${summary['Total_Expenses']:,.2f}")
            with col3:
                st.metric("Net Total", f"${summary['Net_Total']:,.2f}")
            
            # Create tabs for different visualizations
            viz_tabs = st.tabs(["By Category", "By Year", "Expense vs Revenue", "Raw Data"])
            
            # By Category Visualization
            with viz_tabs[0]:
                st.subheader("Expenses and Revenue by Category")
                
                # Prepare data for visualization
                if not category_data.empty:
                    fig, ax = plt.figure(figsize=(12, 6)), plt.subplot()
                    
                    # Group data by Category (Expense or Revenue)
                    by_category_totals = category_data.groupby('Category')['Amount'].sum()
                    
                    # Create bar chart
                    by_category_totals.plot(kind='bar', ax=ax, color=['#FF6B6B', '#4ECB71'])
                    
                    for i, value in enumerate(by_category_totals):
                        ax.text(i, value * 1.01, f'${value:,.0f}', ha='center')
                    
                    plt.title('Total Expenses vs Revenue')
                    plt.ylabel('Amount ($)')
                    plt.grid(axis='y', linestyle='--', alpha=0.7)
                    plt.tight_layout()
                    
                    st.pyplot(fig)
                    
                    # Now show breakdown by title within each category
                    st.subheader("Breakdown by Title")
                    
                    # Separate expenses and revenue for detailed visualizations
                    expenses_df = category_data[category_data['Category'] == 'Expense']
                    revenue_df = category_data[category_data['Category'] == 'Revenue']
                    
                    # Create visualization for expenses if there are any
                    if not expenses_df.empty:
                        st.subheader("Expenses by Title")
                        fig, ax = plt.figure(figsize=(12, 8)), plt.subplot()
                        
                        # Sort by amount descending
                        expenses_df = expenses_df.sort_values('Amount', ascending=False)
                        
                        # Create horizontal bar chart
                        bars = ax.barh(expenses_df['Title'], expenses_df['Amount'], color='#FF6B6B')
                        
                        # Add amount labels
                        for bar in bars:
                            width = bar.get_width()
                            ax.text(width * 1.01, bar.get_y() + bar.get_height()/2, 
                                    f'${width:,.0f}', va='center')
                        
                        plt.title('Expenses by Title')
                        plt.xlabel('Amount ($)')
                        plt.grid(axis='x', linestyle='--', alpha=0.7)
                        plt.tight_layout()
                        
                        st.pyplot(fig)
                    
                    # Create visualization for revenue if there are any
                    if not revenue_df.empty:
                        st.subheader("Revenue by Title")
                        fig, ax = plt.figure(figsize=(12, 8)), plt.subplot()
                        
                        # Sort by amount descending
                        revenue_df = revenue_df.sort_values('Amount', ascending=False)
                        
                        # Create horizontal bar chart
                        bars = ax.barh(revenue_df['Title'], revenue_df['Amount'], color='#4ECB71')
                        
                        # Add amount labels
                        for bar in bars:
                            width = bar.get_width()
                            ax.text(width * 1.01, bar.get_y() + bar.get_height()/2, 
                                    f'${width:,.0f}', va='center')
                        
                        plt.title('Revenue by Title')
                        plt.xlabel('Amount ($)')
                        plt.grid(axis='x', linestyle='--', alpha=0.7)
                        plt.tight_layout()
                        
                        st.pyplot(fig)
                else:
                    st.warning("No data available for the selected date range.")
            
            # By Year Visualization
            with viz_tabs[1]:
                st.subheader("Expenses and Revenue by Year")
                
                if not annual_items.empty:
                    # Group data by year and category
                    yearly_data = annual_items.groupby(['Year', 'Category'])['Amount'].sum().unstack()
                    
                    # Handle if either Expense or Revenue columns are missing
                    if 'Expense' not in yearly_data.columns:
                        yearly_data['Expense'] = 0
                    if 'Revenue' not in yearly_data.columns:
                        yearly_data['Revenue'] = 0
                    
                    # Create visualization
                    fig, ax = plt.figure(figsize=(12, 6)), plt.subplot()
                    
                    # Plot bars
                    yearly_data.plot(kind='bar', ax=ax, color=['#FF6B6B', '#4ECB71'])
                    
                    # Add data labels
                    for i, year_data in enumerate(yearly_data.iterrows()):
                        year, amounts = year_data
                        for j, amount in enumerate(amounts):
                            if amount > 0:  # Only add labels to non-zero amounts
                                ax.text(i + (j * 0.2 - 0.1), amount * 1.01, f'${amount:,.0f}', 
                                       ha='center', va='bottom', rotation=0, fontsize=8)
                    
                    plt.title('Expenses and Revenue by Year')
                    plt.ylabel('Amount ($)')
                    plt.grid(axis='y', linestyle='--', alpha=0.7)
                    plt.tight_layout()
                    
                    st.pyplot(fig)
                else:
                    st.warning("No data available for the selected date range.")
            
            # Expense vs Revenue Timeline
            with viz_tabs[2]:
                st.subheader("Expense vs Revenue Timeline")
                
                if not annual_items.empty:
                    # Group by year and month
                    monthly_data = annual_items.groupby(['Year', 'Month', 'Category'])['Amount'].sum().unstack(fill_value=0)
                    
                    # Create a proper datetime index for better visualization
                    monthly_data = monthly_data.reset_index()
                    monthly_data['Date'] = pd.to_datetime(monthly_data[['Year', 'Month']].assign(day=1))
                    monthly_data = monthly_data.set_index('Date')
                    
                    # Handle if either Expense or Revenue columns are missing
                    if 'Expense' not in monthly_data.columns:
                        monthly_data['Expense'] = 0
                    if 'Revenue' not in monthly_data.columns:
                        monthly_data['Revenue'] = 0
                    
                    # Create visualization
                    fig, ax = plt.figure(figsize=(12, 6)), plt.subplot()
                    
                    # Plot lines
                    monthly_data['Expense'].plot(ax=ax, label='Expenses', color='#FF6B6B', marker='o')
                    monthly_data['Revenue'].plot(ax=ax, label='Revenue', color='#4ECB71', marker='s')
                    
                    # Add net line
                    monthly_data['Net'] = monthly_data['Revenue'] - monthly_data['Expense']
                    monthly_data['Net'].plot(ax=ax, label='Net', color='#3498DB', linestyle='--')
                    
                    plt.title('Expense vs Revenue Timeline')
                    plt.ylabel('Amount ($)')
                    plt.grid(True, linestyle='--', alpha=0.7)
                    plt.legend()
                    plt.tight_layout()
                    
                    st.pyplot(fig)
                    
                    # Also show cumulative chart
                    st.subheader("Cumulative Expense vs Revenue")
                    
                    # Calculate cumulative amounts
                    cumulative_data = monthly_data[['Expense', 'Revenue']].cumsum()
                    cumulative_data['Net'] = cumulative_data['Revenue'] - cumulative_data['Expense']
                    
                    # Create visualization
                    fig, ax = plt.figure(figsize=(12, 6)), plt.subplot()
                    
                    # Plot cumulative lines
                    cumulative_data['Expense'].plot(ax=ax, label='Cum. Expenses', color='#FF6B6B')
                    cumulative_data['Revenue'].plot(ax=ax, label='Cum. Revenue', color='#4ECB71')
                    cumulative_data['Net'].plot(ax=ax, label='Cum. Net', color='#3498DB', linestyle='--')
                    
                    plt.title('Cumulative Expense vs Revenue Over Time')
                    plt.ylabel('Amount ($)')
                    plt.grid(True, linestyle='--', alpha=0.7)
                    plt.legend()
                    plt.tight_layout()
                    
                    st.pyplot(fig)
                else:
                    st.warning("No data available for the selected date range.")
            
            # Raw Data View
            with viz_tabs[3]:
                st.subheader("Raw Data")
                
                if not annual_items.empty:
                    # Display the raw data
                    st.dataframe(annual_items.sort_values(['Year', 'Month', 'Title']))
                    
                    # Allow downloading as CSV
                    csv = annual_items.to_csv(index=False)
                    st.download_button(
                        label="Download data as CSV",
                        data=csv,
                        file_name="other_expenses_revenue_data.csv",
                        mime="text/csv",
                    )
                else:
                    st.warning("No data available for the selected date range.")
        
        except Exception as e:
            st.error(f"Error generating other expense plots: {str(e)}")
            st.exception(e)

# Export/Import tab
with tabs[9]:
    st.header("Export/Import Data")
    
    # Explanation of this tab
    st.info(
        "This tab allows you to export all CSV data to a single JSON file, "
        "or import data from a previously exported JSON file."
    )
    
    # Export section
    st.subheader("Export Data to JSON")
    export_col1, export_col2 = st.columns([1, 2])
    with export_col1:
        if st.button("Export to JSON", key="export_button"):
            with st.spinner("Exporting data..."):
                export_success = export_to_json(st.session_state.dataframes, "carescan_data.json")
                if export_success:
                    st.success("Data exported successfully to carescan_data.json!")
    with export_col2:
        st.write("This will export all CSV data to a single JSON file for backup or sharing.")
    
    # Import section
    st.subheader("Import Data from JSON")
    import_col1, import_col2 = st.columns([1, 2])
    with import_col1:
        if st.button("Import from JSON", key="import_button"):
            with st.spinner("Importing data..."):
                imported_data = import_from_json("carescan_data.json")
                if imported_data:
                    # Update session state with imported data
                    for name, df in imported_data.items():
                        if name in CSV_FILES:
                            st.session_state.dataframes[name] = df
                            # Also save to CSV
                            save_csv(df, CSV_FILES[name])
                    st.success("Data imported successfully!")
    with import_col2:
        st.write("This will import data from a previously exported JSON file and update all CSV files.")

# Comprehensive Proforma tab
with tabs[10]:
    st.header("Comprehensive Proforma")
    
    # Explanation of the proforma
    st.info(
        "This tab generates a comprehensive financial proforma that integrates all revenue and expense sources. "
        "It combines data from Personnel, Equipment, Exams, and Other Expenses to create a unified financial projection."
    )
    
    # Date range selection
    st.subheader("Select Date Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date", 
            value=pd.to_datetime("01/01/2025", format='%m/%d/%Y'),
            min_value=pd.to_datetime("01/01/2020", format='%m/%d/%Y'),
            max_value=pd.to_datetime("12/31/2040", format='%m/%d/%Y'),
            key="proforma_start_date"
        )
    with col2:
        end_date = st.date_input(
            "End Date", 
            value=pd.to_datetime("12/31/2035", format='%m/%d/%Y'),
            min_value=pd.to_datetime("01/01/2020", format='%m/%d/%Y'),
            max_value=pd.to_datetime("12/31/2040", format='%m/%d/%Y'),
            key="proforma_end_date"
        )
    
    # Revenue source selection
    st.subheader("Select Revenue Sources")
    if 'Revenue' in st.session_state.dataframes:
        revenue_sources = st.session_state.dataframes['Revenue']['Title'].tolist()
        selected_sources = st.multiselect("Revenue Sources", revenue_sources, default=revenue_sources, key="proforma_revenue_sources")
    else:
        selected_sources = []
        st.error("Revenue data is not available. Please upload Revenue.csv file.")
    
    # Working days per year option
    work_days = st.number_input("Working Days Per Year", min_value=200, max_value=300, value=250, key="proforma_work_days")
    
    # Travel parameters
    st.subheader("Travel Parameters")
    travel_col1, travel_col2 = st.columns(2)
    with travel_col1:
        days_between_travel = st.number_input(
            "Days Between Travel",
            min_value=1,
            max_value=30,
            value=5,
            help="Number of days between travel events",
            key="proforma_days_between_travel"
        )
    with travel_col2:
        miles_per_travel = st.number_input(
            "Miles Per Travel",
            min_value=1,
            max_value=100,
            value=20,
            help="Number of miles traveled in each travel event",
            key="proforma_miles_per_travel"
        )
    
    # Generate proforma
    if st.button("Generate Comprehensive Proforma"):
        try:
            with st.spinner("Calculating comprehensive proforma and generating visualizations..."):
                # Check if required data is available
                required_tables = ['Revenue', 'Exams', 'Personnel', 'Equipment', 'OtherExpenses']
                missing_tables = [table for table in required_tables if table not in st.session_state.dataframes or st.session_state.dataframes[table].empty]
                
                if missing_tables:
                    st.error(f"The following required data is missing: {', '.join(missing_tables)}")
                elif not selected_sources:
                    st.error("Please select at least one revenue source.")
                else:
                    # Convert dates to string format for the calculator
                    start_date_str = start_date.strftime('%m/%d/%Y')
                    end_date_str = end_date.strftime('%m/%d/%Y')
                    
                    # Calculate comprehensive proforma
                    proforma_results = calculate_comprehensive_proforma(
                        personnel_data=st.session_state.dataframes['Personnel'],
                        exams_data=st.session_state.dataframes['Exams'],
                        revenue_data=st.session_state.dataframes['Revenue'],
                        equipment_data=st.session_state.dataframes['Equipment'],
                        other_data=st.session_state.dataframes['OtherExpenses'],
                        start_date=start_date_str,
                        end_date=end_date_str,
                        revenue_sources=selected_sources,
                        work_days_per_year=work_days,
                        days_between_travel=days_between_travel,
                        miles_per_travel=miles_per_travel
                    )
                    
                    # Get annual summary for visualizations
                    annual_summary = proforma_results['annual_summary']
                    
                    if annual_summary.empty:
                        st.warning("No data could be calculated for the selected date range.")
                    else:
                        # Display key financial metrics
                        st.subheader("Key Financial Metrics")
                        metrics = proforma_results['financial_metrics']
                        
                        # Display metrics in a more visually appealing format
                        metric_col1, metric_col2, metric_col3 = st.columns(3)
                        with metric_col1:
                            st.metric("Total Revenue", f"${metrics['total_revenue']:,.2f}")
                            st.metric("Avg. Annual Revenue", f"${metrics['average_annual_revenue']:,.2f}")
                        with metric_col2:
                            st.metric("Total Expenses", f"${metrics['total_expenses']:,.2f}")
                            st.metric("Avg. Annual Expenses", f"${metrics['average_annual_expenses']:,.2f}")
                        with metric_col3:
                            st.metric("Net Income", f"${metrics['total_net_income']:,.2f}")
                            st.metric("Revenue/Expense Ratio", f"{metrics['revenue_expense_ratio']:.2f}")
                        
                        if metrics['breakeven_year']:
                            st.info(f"Breakeven Year: {metrics['breakeven_year']}")
                        else:
                            st.warning("No breakeven year identified in the projection period.")
                        
                        # Display annual summary table
                        st.subheader("Annual Financial Summary")
                        
                        # Format the summary for better display
                        formatted_summary = annual_summary.copy()
                        for col in formatted_summary.columns:
                            if col != 'Year' and formatted_summary[col].dtype in [np.float64, np.int64]:
                                formatted_summary[col] = formatted_summary[col].map('${:,.2f}'.format)
                        
                        st.dataframe(formatted_summary)
                        
                        # Visualizations
                        st.subheader("Financial Visualizations")
                        
                        # Create tabs for different visualizations
                        viz_tabs = st.tabs(["Net Income", "Revenue vs Expenses", "Cash Flow"])
                        
                        # Initialize the calculator for visualizations
                        calculator = ComprehensiveProformaCalculator(
                            personnel_data=st.session_state.dataframes['Personnel'],
                            exams_data=st.session_state.dataframes['Exams'],
                            revenue_data=st.session_state.dataframes['Revenue'],
                            equipment_data=st.session_state.dataframes['Equipment'],
                            other_data=st.session_state.dataframes['OtherExpenses']
                        )
                        
                        # Net Income Visualization
                        with viz_tabs[0]:
                            fig = calculator.generate_visualization(annual_summary, metric='net_income')
                            st.pyplot(fig)
                        
                        # Revenue vs Expenses Visualization
                        with viz_tabs[1]:
                            fig = calculator.generate_visualization(annual_summary, metric='revenue_expense')
                            st.pyplot(fig)
                        
                        # Cash Flow Visualization
                        with viz_tabs[2]:
                            fig = calculator.generate_visualization(annual_summary, metric='cash_flow')
                            st.pyplot(fig)
                        
                        # Monthly Cash Flow
                        st.subheader("Monthly Cash Flow Projection")
                        monthly_cash_flow = proforma_results['monthly_cash_flow']
                        
                        if not monthly_cash_flow.empty:
                            # Plot monthly cash flow
                            fig, ax = plt.subplots(figsize=(14, 7))
                            
                            # Ensure date is sorted
                            monthly_cash_flow = monthly_cash_flow.sort_values('Date')
                            
                            # Plot the line
                            ax.plot(monthly_cash_flow['Date'], monthly_cash_flow['Net_Income'], 
                                   marker='', linestyle='-', color='blue', linewidth=2)
                            ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
                            
                            # Format the x-axis to show dates nicely
                            plt.gcf().autofmt_xdate()
                            
                            ax.set_title('Monthly Net Income')
                            ax.set_xlabel('Date')
                            ax.set_ylabel('Net Income ($)')
                            ax.grid(True, linestyle='--', alpha=0.7)
                            
                            st.pyplot(fig)
                            
                            # Show sample of monthly data
                            st.write("Sample of Monthly Cash Flow Data (first 12 months)")
                            
                            # Format the monthly data for display
                            display_cols = ['Date', 'Total_Revenue', 'Total_Expenses', 'Net_Income']
                            formatted_monthly = monthly_cash_flow[display_cols].head(12).copy()
                            
                            # Format currency columns
                            for col in ['Total_Revenue', 'Total_Expenses', 'Net_Income']:
                                formatted_monthly[col] = formatted_monthly[col].map('${:,.2f}'.format)
                                
                            # Format date column
                            formatted_monthly['Date'] = formatted_monthly['Date'].dt.strftime('%b %Y')
                            
                            st.dataframe(formatted_monthly)
                        
                        # Revenue and Expense Breakdown
                        st.subheader("Revenue and Expense Breakdown")
                        
                        # Create two columns
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("Revenue Breakdown")
                            
                            # Calculate total revenue for each source across all years
                            total_exam_revenue = annual_summary['Exam_Revenue'].sum()
                            total_other_revenue = annual_summary['Other_Revenue'].sum()
                            total_revenue = total_exam_revenue + total_other_revenue
                            
                            # Create pie chart for revenue
                            fig, ax = plt.subplots(figsize=(8, 8))
                            revenue_data = [total_exam_revenue, total_other_revenue]
                            revenue_labels = ['Exam Revenue', 'Other Revenue']
                            
                            # Only include non-zero values
                            non_zero_idx = [i for i, x in enumerate(revenue_data) if x > 0]
                            if non_zero_idx:
                                ax.pie([revenue_data[i] for i in non_zero_idx], 
                                      labels=[revenue_labels[i] for i in non_zero_idx],
                                      autopct='%1.1f%%', startangle=90, shadow=True)
                                ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
                                st.pyplot(fig)
                            else:
                                st.write("No revenue data to display")
                        
                        with col2:
                            st.write("Expense Breakdown")
                            
                            # Calculate total expense for each category across all years
                            total_personnel = annual_summary['Personnel_Expenses'].sum()
                            total_equipment = annual_summary['Equipment_Expenses'].sum()
                            total_exam_direct = annual_summary['Exam_Direct_Expenses'].sum()
                            total_other_expense = annual_summary['Other_Expenses'].sum()
                            
                            # Create pie chart for expenses
                            fig, ax = plt.subplots(figsize=(8, 8))
                            expense_data = [total_personnel, total_equipment, total_exam_direct, total_other_expense]
                            expense_labels = ['Personnel', 'Equipment', 'Exam Direct', 'Other']
                            
                            # Only include non-zero values
                            non_zero_idx = [i for i, x in enumerate(expense_data) if x > 0]
                            if non_zero_idx:
                                ax.pie([expense_data[i] for i in non_zero_idx], 
                                      labels=[expense_labels[i] for i in non_zero_idx],
                                      autopct='%1.1f%%', startangle=90, shadow=True)
                                ax.axis('equal')
                                st.pyplot(fig)
                            else:
                                st.write("No expense data to display")
                        
                        # Allow user to download the results as CSV
                        st.subheader("Download Results")
                        csv = annual_summary.to_csv(index=False)
                        st.download_button(
                            label="Download Annual Summary as CSV",
                            data=csv,
                            file_name="comprehensive_proforma_summary.csv",
                            mime="text/csv",
                        )
                        
                        # If monthly data is available, allow that to be downloaded too
                        if not monthly_cash_flow.empty:
                            monthly_csv = monthly_cash_flow.to_csv(index=False)
                            st.download_button(
                                label="Download Monthly Cash Flow as CSV",
                                data=monthly_csv,
                                file_name="comprehensive_proforma_monthly.csv",
                                mime="text/csv",
                            )
                        
        except Exception as e:
            import traceback
            st.error(f"Error generating comprehensive proforma: {str(e)}")
            st.error(traceback.format_exc())

# Display sidebar with information
with st.sidebar:
    st.title("About")
    st.info(
        "This application allows you to view and edit the CAREScan ProForma data. "
        "You can modify the data directly in each tab and save your changes. "
        "You can also export all data to a JSON file and import data from a JSON file."
    )
    
    # Data formatting help
    st.subheader("Data Formatting")
    st.markdown("""
    - **Large Numbers**: You can use underscores for readability (e.g., `200_000` or `200000`).
    - **Lists**: Use semicolons to separate values (e.g., `Item1; Item2; Item3;`).
    - **Dates**: Use format MM/DD/YYYY (e.g., `06/01/2025`).
    """)
    
    # Show modification timestamps
    st.subheader("Last Modified")
    for name, file in CSV_FILES.items():
        if os.path.exists(file):
            timestamp = os.path.getmtime(file)
            modified_time = pd.to_datetime(timestamp, unit='s').strftime('%Y-%m-%d %H:%M:%S')
            st.text(f"{name}: {modified_time}") 