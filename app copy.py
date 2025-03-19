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
from financeModels.comprehensive_proforma import ComprehensiveProformaCalculator, calculate_comprehensive_proforma, get_exam_calculator_from_proforma_params
import matplotlib.ticker as mticker

# Set page configuration
st.set_page_config(
    page_title="CAREScan ProForma Editor",
    page_icon="📊",
    layout="wide"
)

# Add a reload data button in the sidebar
with st.sidebar:
    if st.button("🔄 Reload All Data"):
        # Reload all data from CSV files
        for name, filepath in CSV_FILES.items():
            try:
                df = load_csv(filepath)
                st.session_state.dataframes[name] = df
                st.toast(f"Reloaded {name} data")
            except Exception as e:
                st.error(f"Error reloading {name}: {e}")
        st.success("All data reloaded from CSV files!")

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
        # Ensure we're working with a DataFrame
        if not isinstance(df, pd.DataFrame):
            st.warning(f"Converting to DataFrame before saving to {filepath}")
            try:
                df = pd.DataFrame(df)
            except Exception as e:
                st.error(f"Failed to convert to DataFrame: {e}")
                return False
        
        # Process values for saving
        save_df = df.copy()
        for col in save_df.columns:
            save_df[col] = save_df[col].apply(process_value_for_save)
        
        # Remove any rows that are completely empty
        save_df = save_df.dropna(how='all')
        
        # Ensure there are no duplicated columns
        if save_df.columns.duplicated().any():
            st.warning(f"Found duplicated columns. Fixing before saving.")
            save_df = save_df.loc[:, ~save_df.columns.duplicated()]
        
        save_df.to_csv(filepath, index=False)
        
        # Also update the JSON file with the latest data
        if os.path.exists("carescan_data.json") and 'dataframes' in st.session_state:
            # Get the key name from the filepath
            for key, file_path in CSV_FILES.items():
                if file_path == filepath:
                    # Update the corresponding DataFrame in session state
                    st.session_state.dataframes[key] = df
                    # Export all DataFrames to JSON to keep it in sync
                    export_to_json(st.session_state.dataframes, "carescan_data.json")
                    break
        
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

# Add state variable for comprehensive proforma results
if 'comprehensive_proforma_results' not in st.session_state:
    st.session_state.comprehensive_proforma_results = None

# Create tabs for each CSV file plus visualization tabs and Export/Import
tabs = st.tabs([
    "Revenue", "Equipment", "Personnel", "Exams", "OtherExpenses",  # CSV Editor tabs
    "Personnel Expense Plots", "Equipment Expense Plots", "Exam Revenue Analysis", "Other Expense Plots", 
    "Export/Import", "Comprehensive Proforma", "Volume Limiting Factors", "Comprehensive Report"
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
            disabled=False,
            hide_index=False,
            column_config={
                # Configure specific column options if needed
                # Example: "Title": st.column_config.TextColumn("Title", help="Name of the revenue source")
            },
            key=f"editor_{name}"
        )
        
        # Save button for each tab
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button(f"Save {name}", key=f"save_{name}"):
                try:
                    # Get editor data
                    editor_data = st.session_state[f"editor_{name}"]
                    
                    # Check if we have edited_rows format from newer Streamlit versions
                    if isinstance(editor_data, dict) and 'edited_rows' in editor_data:
                        # Start with the original DataFrame
                        df_to_save = st.session_state.dataframes[name].copy()
                        
                        # Apply edits from edited_rows
                        for row_idx, row_edits in editor_data['edited_rows'].items():
                            for col, value in row_edits.items():
                                df_to_save.loc[int(row_idx), col] = value
                        
                        # If there are added rows, add them
                        if 'added_rows' in editor_data and editor_data['added_rows']:
                            new_rows = pd.DataFrame(editor_data['added_rows'])
                            df_to_save = pd.concat([df_to_save, new_rows], ignore_index=True)
                        
                        # If there are deleted rows, remove them
                        if 'deleted_rows' in editor_data and editor_data['deleted_rows']:
                            df_to_save = df_to_save.drop(editor_data['deleted_rows']).reset_index(drop=True)
                        
                        # Save the dataframe
                        if save_csv(df_to_save, CSV_FILES[name]):
                            st.session_state.dataframes[name] = df_to_save
                            st.success(f"{name} data saved successfully!")
                        
                        # Skip the rest of the code since we've handled it
                        continue
                    
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
                            # Try alternative conversion method for newer Streamlit versions
                            try:
                                # Try to construct a DataFrame from dictionary with mixed values
                                # First, filter out any metadata keys (non-numeric keys or keys starting with _)
                                row_data = {}
                                for k, v in editor_data.items():
                                    if isinstance(k, (int, float)) or (isinstance(k, str) and k.isdigit()):
                                        row_idx = int(k) if isinstance(k, str) else k
                                        row_data[row_idx] = v
                                
                                # If we have row data, convert to DataFrame
                                if row_data:
                                    if all(isinstance(v, dict) for v in row_data.values()):
                                        rows = list(row_data.values())
                                        df_to_save = pd.DataFrame(rows)
                                    else:
                                        # Try a different approach - if editor_data has columns
                                        columns = set()
                                        for v in editor_data.values():
                                            if isinstance(v, dict):
                                                columns.update(v.keys())
                                        
                                        if columns:
                                            data = {col: [] for col in columns}
                                            for v in editor_data.values():
                                                if isinstance(v, dict):
                                                    for col in columns:
                                                        data[col].append(v.get(col, None))
                                            df_to_save = pd.DataFrame(data)
                                        else:
                                            st.error(f"Could not convert {name} data to DataFrame - unexpected structure.")
                                            df_to_save = None
                                else:
                                    st.error(f"Could not convert {name} data to DataFrame - no valid row data found.")
                                    df_to_save = None
                            except Exception as conversion_error:
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
            format="MM/DD/YYYY",
            key="equipment_start_date"
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=pd.to_datetime("12/31/2029", format='%m/%d/%Y'),
            min_value=pd.to_datetime("01/01/2020", format='%m/%d/%Y'),
            max_value=pd.to_datetime("12/31/2040", format='%m/%d/%Y'),
            format="MM/DD/YYYY",
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
                            fmt = '${x:,.0f}'
                            tick = mticker.StrMethodFormatter(fmt)
                            ax3.yaxis.set_major_formatter(tick)
                            
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
    
    # Date range selection (replacing year range selection)
    st.subheader("Select Date Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=pd.to_datetime("01/01/2025", format='%m/%d/%Y'),
            min_value=pd.to_datetime("01/01/2020", format='%m/%d/%Y'),
            max_value=pd.to_datetime("12/31/2040", format='%m/%d/%Y'),
            format="MM/DD/YYYY",
            key="exam_start_date"
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=pd.to_datetime("12/31/2029", format='%m/%d/%Y'),
            min_value=pd.to_datetime("01/01/2020", format='%m/%d/%Y'),
            max_value=pd.to_datetime("12/31/2040", format='%m/%d/%Y'),
            format="MM/DD/YYYY",
            key="exam_end_date"
        )
    
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
                    # Extract years from selected dates
                    start_year = start_date.year
                    end_year = end_date.year
                    
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
                                    autopct='%1.1f%%', startangle=90, shadow=True)
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
            format="MM/DD/YYYY",
            key="other_expenses_start_date"
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=pd.to_datetime("12/31/2029", format='%m/%d/%Y'),
            min_value=pd.to_datetime("01/01/2020", format='%m/%d/%Y'),
            max_value=pd.to_datetime("12/31/2040", format='%m/%d/%Y'),
            format="MM/DD/YYYY",
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
    
    # Add a note about data reloading
    st.warning(
        "**Important**: If you have made changes to data in other tabs, ensure these changes are reflected in your report "
        "by using the '🔄 Reload All Data' button in the sidebar before generating the proforma. "
        "This will ensure all calculations use the most recent data from your CSV files."
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
            format="MM/DD/YYYY",
            key="proforma_start_date"
        )
    with col2:
        end_date = st.date_input(
            "End Date", 
            value=pd.to_datetime("12/31/2029", format='%m/%d/%Y'),
            min_value=pd.to_datetime("01/01/2020", format='%m/%d/%Y'),
            max_value=pd.to_datetime("12/31/2040", format='%m/%d/%Y'),
            format="MM/DD/YYYY",
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
    
    # Population Growth Rates
    st.subheader("Population Growth Rates")
    st.write("Set the yearly growth rate for Population Reached percentage. These growth rates will be applied cumulatively year by year.")
    
    # Calculate number of years in the range (up to max 5 years)
    years_in_range = min(5, end_date.year - start_date.year + 1)
    
    # Default growth rates - these are decimal values where 0.05 means 5% growth
    default_growth_rates = [0.0, 0.0, 0.05, 0.05, 0.04]
    
    # Create sliders for each year's growth rate
    population_growth_rates = []
    col1, col2 = st.columns(2)
    
    for i in range(years_in_range):
        year = start_date.year + i
        default_rate = default_growth_rates[i] if i < len(default_growth_rates) else 0.0
        
        # Alternate columns for better layout
        with col1 if i % 2 == 0 else col2:
            # Display as 0-50 representing 0%-50% but store as 0.0-0.5
            growth_rate_pct = st.slider(
                f"Year {i+1} ({year}) Growth Rate",
                min_value=0,
                max_value=50,  # 0-50%
                value=int(default_rate * 100),  # Convert decimal to percentage
                step=1,
                format="%d%%",  # Display as whole number percentage
                help=f"Population reached growth rate for year {year}",
                key=f"population_growth_year_{i+1}"
            )
            # Convert back to decimal (0.0-0.5) for calculations
            population_growth_rates.append(growth_rate_pct / 100.0)
    
    # Warning about cumulative growth and max 100% - update for clarity
    st.warning(
        "**Note**: These growth rates represent the percentage increase in population reached each year. "
        "For example, a 5% growth means that if the population reached was 20% initially, it would grow to 21% (a 5% increase from 20%). "
        "The growth is applied cumulatively each year to the PctPopulationReached value in the Revenue.csv file. "
        "The system will automatically ensure the population reached doesn't exceed 100%."
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
                    
                    # Reload data from CSV files to ensure we have the latest data
                    updated_data = {}
                    for name, filepath in CSV_FILES.items():
                        updated_data[name] = load_csv(filepath)
                        st.session_state.dataframes[name] = updated_data[name]
                    
                    # Calculate comprehensive proforma
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
                        population_growth_rates=population_growth_rates
                    )
                    
                    # Store the results in session state for use in Volume Limiting Factors tab
                    st.session_state.comprehensive_proforma_results = {
                        'results': proforma_results,
                        'start_date': start_date_str,
                        'end_date': end_date_str,
                        'revenue_sources': selected_sources,
                        'work_days': work_days,
                        'population_growth_rates': population_growth_rates
                    }
                    
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
                            personnel_data=updated_data['Personnel'],
                            exams_data=updated_data['Exams'],
                            revenue_data=updated_data['Revenue'],
                            equipment_data=updated_data['Equipment'],
                            other_data=updated_data['OtherExpenses']
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
                        
                        # Revenue Line Breakdown
                        st.subheader("Revenue Line Breakdown")
                        st.info("This breakdown shows the revenue associated with each revenue line's model and " 
                                "the percentage of overall expenses scaled to match each line's PctFullModel value.")
                        
                        # Get the raw exam results that include revenue source information
                        exam_results = proforma_results['exam_results']
                        
                        if not exam_results.empty and 'RevenueSource' in exam_results.columns:
                            # Calculate revenue by revenue source
                            revenue_by_source = exam_results.groupby('RevenueSource')['Total_Revenue'].sum().reset_index()
                            
                            # Get the PctFullModel values for each revenue source
                            revenue_data = updated_data['Revenue']
                            
                            # Create a dataframe to hold the breakdown results
                            breakdown_data = []
                            
                            # Calculate total expenses across all years
                            total_expenses = annual_summary['Total_Expenses'].sum()
                            
                            for _, row in revenue_by_source.iterrows():
                                source_name = row['RevenueSource']
                                source_revenue = row['Total_Revenue']
                                
                                # Find the PctFullModel for this revenue source
                                source_row = revenue_data[revenue_data['Title'] == source_name]
                                if not source_row.empty:
                                    pct_full_model = source_row.iloc[0]['PctFullModel']
                                    # Calculate scaled expenses based on PctFullModel
                                    scaled_expenses = total_expenses * pct_full_model
                                    # Calculate net income
                                    net_income = source_revenue - scaled_expenses
                                    
                                    breakdown_data.append({
                                        'Revenue Source': source_name,
                                        'Revenue': source_revenue,
                                        'PctFullModel': pct_full_model,
                                        'Scaled Expenses': scaled_expenses,
                                        'Net Income': net_income
                                    })
                            
                            if breakdown_data:
                                # Convert to dataframe
                                breakdown_df = pd.DataFrame(breakdown_data)
                                
                                # Calculate totals
                                total_row = {
                                    'Revenue Source': 'TOTAL',
                                    'Revenue': breakdown_df['Revenue'].sum(),
                                    'PctFullModel': breakdown_df['PctFullModel'].sum(),
                                    'Scaled Expenses': breakdown_df['Scaled Expenses'].sum(), 
                                    'Net Income': breakdown_df['Net Income'].sum()
                                }
                                breakdown_df = pd.concat([breakdown_df, pd.DataFrame([total_row])], ignore_index=True)
                                
                                # Format for display
                                formatted_breakdown = breakdown_df.copy()
                                formatted_breakdown['Revenue'] = formatted_breakdown['Revenue'].map('${:,.2f}'.format)
                                formatted_breakdown['PctFullModel'] = formatted_breakdown['PctFullModel'].map('{:.1%}'.format)
                                formatted_breakdown['Scaled Expenses'] = formatted_breakdown['Scaled Expenses'].map('${:,.2f}'.format)
                                formatted_breakdown['Net Income'] = formatted_breakdown['Net Income'].map('${:,.2f}'.format)
                                
                                st.dataframe(formatted_breakdown)
                                
                                # Create a bar chart showing revenue vs scaled expenses for each source
                                fig, ax = plt.subplots(figsize=(12, 6))
                                
                                # Skip the total row for the chart
                                chart_df = breakdown_df[breakdown_df['Revenue Source'] != 'TOTAL']
                                
                                # Set up bar positions
                                x = np.arange(len(chart_df))
                                width = 0.35
                                
                                # Create bars
                                ax.bar(x - width/2, chart_df['Revenue'], width, label='Revenue')
                                ax.bar(x + width/2, chart_df['Scaled Expenses'], width, label='Scaled Expenses')
                                
                                # Add labels and title
                                ax.set_xlabel('Revenue Source')
                                ax.set_ylabel('Amount ($)')
                                ax.set_title('Revenue vs Scaled Expenses by Revenue Line')
                                ax.set_xticks(x)
                                ax.set_xticklabels(chart_df['Revenue Source'])
                                ax.legend()
                                
                                # Format y-axis with dollar signs
                                fmt = '${x:,.0f}'
                                tick = mticker.StrMethodFormatter(fmt)
                                ax.yaxis.set_major_formatter(tick)
                                
                                # Display the chart
                                st.pyplot(fig)
                            else:
                                st.warning("No revenue source data available for breakdown.")
                        else:
                            st.warning("No revenue source data available in the exam results.")
                        
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

# Volume Limiting Factors tab
with tabs[11]:
    st.header("Volume Limiting Factors")
    
    # Explanation of this tab
    st.info(
        "This tab shows what factors are limiting the exam volume for each revenue model. "
        "It provides visualizations of exam usage compared to their maximum achievable volumes, "
        "as well as the utilization percentage of each personnel type. "
        "The analysis uses data from the Comprehensive Proforma tab."
    )
    
    # Add a note about running comprehensive proforma first
    st.warning(
        "**Important**: You must first generate the Comprehensive Proforma analysis before running this analysis. "
        "This ensures that the Volume Limiting Factors analysis uses the same data and calculations as the financial projections."
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
            format="MM/DD/YYYY",
            key="volume_start_date"
        )
    with col2:
        end_date = st.date_input(
            "End Date", 
            value=pd.to_datetime("12/31/2029", format='%m/%d/%Y'),
            min_value=pd.to_datetime("01/01/2020", format='%m/%d/%Y'),
            max_value=pd.to_datetime("12/31/2040", format='%m/%d/%Y'),
            format="MM/DD/YYYY",
            key="volume_end_date"
        )
    
    # Revenue source selection
    st.subheader("Select Revenue Sources")
    if 'Revenue' in st.session_state.dataframes:
        revenue_sources = st.session_state.dataframes['Revenue']['Title'].tolist()
        selected_sources = st.multiselect("Revenue Sources", revenue_sources, default=revenue_sources, key="volume_revenue_sources")
    else:
        selected_sources = []
        st.error("Revenue data is not available. Please upload Revenue.csv file.")
    
    # Working days per year option
    work_days = st.number_input("Working Days Per Year", min_value=200, max_value=300, value=250, key="volume_work_days")
    
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
            key="volume_days_between_travel"
        )
    with travel_col2:
        miles_per_travel = st.number_input(
            "Miles Per Travel",
            min_value=1,
            max_value=100,
            value=20,
            help="Number of miles traveled in each travel event",
            key="volume_miles_per_travel"
        )
    
    # Population Growth Rates
    st.subheader("Population Growth Rates")
    st.write("Set the yearly growth rate for Population Reached percentage. These growth rates will be applied cumulatively year by year.")
    
    # Calculate number of years in the range (up to max 5 years)
    years_in_range = min(5, end_date.year - start_date.year + 1)
    
    # Default growth rates - these are decimal values where 0.05 means 5% growth
    default_growth_rates = [0.0, 0.0, 0.05, 0.05, 0.04]
    
    # Create sliders for each year's growth rate
    population_growth_rates = []
    col1, col2 = st.columns(2)
    
    for i in range(years_in_range):
        year = start_date.year + i
        default_rate = default_growth_rates[i] if i < len(default_growth_rates) else 0.0
        
        # Alternate columns for better layout
        with col1 if i % 2 == 0 else col2:
            # Display as 0-50 representing 0%-50% but store as 0.0-0.5
            growth_rate_pct = st.slider(
                f"Year {i+1} ({year}) Growth Rate",
                min_value=0,
                max_value=50,  # 0-50%
                value=int(default_rate * 100),  # Convert decimal to percentage
                step=1,
                format="%d%%",  # Display as whole number percentage
                help=f"Population reached growth rate for year {year}",
                key=f"volume_population_growth_year_{i+1}"
            )
            # Convert back to decimal (0.0-0.5) for calculations
            population_growth_rates.append(growth_rate_pct / 100.0)
    
    # Generate analysis
    if st.button("Generate Volume Analysis"):
        try:
            # Check if comprehensive proforma has been generated
            if st.session_state.comprehensive_proforma_results is None:
                st.error("Please generate the Comprehensive Proforma first. This analysis needs data from the proforma.")
            else:
                with st.spinner("Calculating volume limitations and generating visualizations..."):
                    # Check if required data is available
                    required_tables = ['Revenue', 'Exams', 'Personnel', 'Equipment']
                    missing_tables = [table for table in required_tables if table not in st.session_state.dataframes or st.session_state.dataframes[table].empty]
                    
                    if missing_tables:
                        st.error(f"The following required data is missing: {', '.join(missing_tables)}")
                    elif not selected_sources:
                        st.error("Please select at least one revenue source.")
                    else:
                        # Convert dates to string format for the calculator
                        start_date_str = start_date.strftime('%m/%d/%Y')
                        end_date_str = end_date.strftime('%m/%d/%Y')
                        
                        # Reload data from CSV files to ensure we have the latest data
                        updated_data = {}
                        for name, filepath in CSV_FILES.items():
                            updated_data[name] = load_csv(filepath)
                            st.session_state.dataframes[name] = updated_data[name]
                        
                        # Get the parameters from the comprehensive proforma
                        proforma_data = st.session_state.comprehensive_proforma_results
                        
                        # Create a calculator with the same parameters as the comprehensive proforma
                        calculator = get_exam_calculator_from_proforma_params(
                            personnel_data=updated_data['Personnel'],
                            exams_data=updated_data['Exams'],
                            revenue_data=updated_data['Revenue'],
                            equipment_data=updated_data['Equipment'],
                            start_date=start_date_str,
                            population_growth_rates=proforma_data['population_growth_rates']
                        )
                        
                        # Create tabs for different visualizations
                        viz_tabs = st.tabs(["Exam Volume Analysis", "Personnel Utilization"])
                        
                        # Exam Volume Analysis tab
                        with viz_tabs[0]:
                            st.subheader("Exam Volume Analysis")
                            st.write("This visualization shows each exam's actual volume compared to its maximum achievable volume.")
                            st.write("**Note**: This analysis uses the same calculations as the Comprehensive Proforma for consistency.")
                            
                            # Process and display data for each year
                            start_year = start_date.year
                            end_year = end_date.year
                            
                            for year in range(start_year, end_year + 1):
                                st.markdown(f"### Year {year}")
                                
                                # Create a figure for the year plots with subplots for each revenue source
                                fig, axes = plt.subplots(len(selected_sources), 1, figsize=(10, 5 * len(selected_sources)), sharex=True)
                                
                                # Use a single axis if there's only one revenue source
                                if len(selected_sources) == 1:
                                    axes = [axes]
                                
                                # Process each revenue source
                                for i, revenue_source in enumerate(selected_sources):
                                    max_volumes = pd.DataFrame()
                                    actual_volumes = pd.DataFrame()
                                    
                                    try:
                                        # Calculate max reachable volume
                                        max_volumes = calculator.calculate_max_reachable_volume(revenue_source)
                                        
                                        # Calculate actual volume using the work_days from proforma
                                        actual_volumes = calculator.calculate_annual_exam_volume(year, revenue_source, proforma_data['work_days'])
                                        
                                        # Prepare data for plotting
                                        # Check if required columns exist in the DataFrames
                                        if "Exam" not in max_volumes.columns or "MaxReachableVolume" not in max_volumes.columns:
                                            st.warning(f"Required columns missing in max_volumes data for {revenue_source}: {max_volumes.columns.tolist()}. Skipping.")
                                            continue
                                            
                                        if "Exam" not in actual_volumes.columns or "AnnualVolume" not in actual_volumes.columns:
                                            st.warning(f"Required columns missing in actual_volumes data for {revenue_source}: {actual_volumes.columns.tolist()}. Skipping.")
                                            continue
                                        
                                        # Display debugging information
                                        st.caption(f"Found {len(max_volumes)} exam(s) with max volumes and {len(actual_volumes)} exam(s) with actual volumes for {revenue_source}")
                                            
                                        # Merge the data and handle mismatches gracefully
                                        combined_df = pd.merge(
                                            max_volumes[["Exam", "MaxReachableVolume"]],
                                            actual_volumes[["Exam", "AnnualVolume"]],
                                            on="Exam",
                                            how='outer'
                                        ).fillna(0)
                                        
                                        # Check if we have any data after merging
                                        if combined_df.empty:
                                            st.warning(f"No matching exams found between max volumes and actual volumes for {revenue_source}.")
                                            continue
                                        
                                        # Calculate percentage of max
                                        combined_df['UsagePercentage'] = (combined_df['AnnualVolume'] / combined_df['MaxReachableVolume'] * 100).fillna(0)
                                        combined_df['UsagePercentage'] = combined_df['UsagePercentage'].clip(upper=100)  # Cap at 100%
                                        
                                        # Sort by usage percentage for better visualization
                                        combined_df = combined_df.sort_values(by='UsagePercentage', ascending=False)
                                        
                                        # Plot the data
                                        ax = axes[i]
                                        bar_width = 0.35
                                        bar_positions = np.arange(len(combined_df))
                                        
                                        # Plot max volume bars
                                        max_bars = ax.bar(bar_positions, combined_df['MaxReachableVolume'], bar_width, 
                                                         label='Max Achievable Volume', alpha=0.7, color='lightblue')
                                        
                                        # Plot actual volume bars
                                        actual_bars = ax.bar(bar_positions, combined_df['AnnualVolume'], bar_width, 
                                                            label='Actual Volume', alpha=0.9, color='darkblue')
                                        
                                        # Add percentage text on top of each bar
                                        for j, (_, row) in enumerate(combined_df.iterrows()):
                                            ax.text(j, row['AnnualVolume'] + (0.05 * max(combined_df['MaxReachableVolume'])), 
                                                   f"{row['UsagePercentage']:.1f}%", 
                                                   ha='center', va='bottom', fontsize=8, rotation=0)
                                        
                                        # Set title and labels
                                        ax.set_title(f"Exam Volume for {revenue_source} in {year}")
                                        ax.set_ylabel('Volume (# of exams)')
                                        ax.set_xticks(bar_positions)
                                        ax.set_xticklabels(combined_df["Exam"], rotation=45, ha='right')
                                        ax.legend()
                                        
                                        # Format y-axis to show whole numbers
                                        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, pos: f'{int(x):,}'))
                                        
                                        # Add a grid for better readability
                                        ax.grid(axis='y', linestyle='--', alpha=0.7)
                                        
                                        # Display the data table below the plots
                                        st.write(f"#### {revenue_source} - {year} Volume Data")
                                        
                                        # Format the dataframe for display
                                        display_df = combined_df.copy()
                                        display_df['MaxReachableVolume'] = display_df['MaxReachableVolume'].map('{:,.0f}'.format)
                                        display_df['AnnualVolume'] = display_df['AnnualVolume'].map('{:,.0f}'.format)
                                        display_df['UsagePercentage'] = display_df['UsagePercentage'].map('{:.1f}%'.format)
                                        
                                        # Rename columns for better display
                                        display_df = display_df.rename(columns={
                                            'Exam': 'Exam',
                                            'MaxReachableVolume': 'Max Achievable Volume',
                                            'AnnualVolume': 'Actual Annual Volume',
                                            'UsagePercentage': 'Usage Percentage'
                                        })
                                        
                                        st.dataframe(display_df, use_container_width=True)
                                        
                                        # Identify limiting factors
                                        st.write("##### Limiting Factors Analysis")
                                        
                                        # Get available staff and equipment
                                        available_staff = calculator.get_available_staff(f"01/01/{year}")
                                        available_equipment = calculator.get_available_equipment(f"01/01/{year}")
                                        
                                        # Calculate exams per day
                                        exams_per_day = calculator.calculate_exams_per_day(f"01/01/{year}", revenue_source)
                                        
                                        if not exams_per_day.empty:
                                            # Determine limiting factors for each exam
                                            limiting_factors = []
                                            
                                            for _, row in exams_per_day.iterrows():
                                                if "Title" not in row and "Exam" not in row: continue
                                                exam = row["Title"] if "Title" in row else row["Exam"]
                                                if exam not in combined_df["Exam"].values: continue
                                                max_vol = combined_df.loc[combined_df["Exam"] == exam, "MaxReachableVolume"].values[0]
                                                actual_vol = combined_df.loc[combined_df["Exam"] == exam, 'AnnualVolume'].values[0]
                                                
                                                if actual_vol < max_vol * 0.99:  # If we're not achieving at least 99% of max
                                                    # Check if limited by equipment
                                                    equipment_limited = row['LimitedByEquipment'] if 'LimitedByEquipment' in row else False
                                                    
                                                    # Check if limited by staff
                                                    staff_limited = row['LimitedByStaff'] if 'LimitedByStaff' in row else False
                                                    staff_limiting_type = row['LimitingStaffType'] if 'LimitingStaffType' in row else None
                                                    
                                                    factor = "Population demographics"  # Default
                                                    
                                                    if equipment_limited:
                                                        equipment_type = row['Equipment'] if 'Equipment' in row else None
                                                        factor = f"Equipment availability ({equipment_type})"
                                                    elif staff_limited and staff_limiting_type:
                                                        factor = f"Staff availability ({staff_limiting_type})"
                                                    
                                                    limiting_factors.append({
                                                        'Exam': exam,
                                                        'Limiting Factor': factor,
                                                        'Max Volume': int(max_vol),
                                                        'Actual Volume': int(actual_vol),
                                                        'Usage %': f"{actual_vol/max_vol*100:.1f}%" if max_vol > 0 else "N/A"
                                                    })
                                            
                                            if limiting_factors:
                                                lf_df = pd.DataFrame(limiting_factors)
                                                st.dataframe(lf_df, use_container_width=True)
                                            else:
                                                st.write("No significant limiting factors found.")
                                        else:
                                            st.write("Could not determine exams per day.")
                                    
                                    except Exception as e:
                                        st.error(f"Error processing {revenue_source}: {str(e)}")
                                
                                # Adjust layout and show the plot
                                plt.tight_layout()
                                st.pyplot(fig)
                        
                        # Personnel Utilization tab
                        with viz_tabs[1]:
                            st.subheader("Personnel Utilization Analysis")
                            st.write("This visualization shows the utilization percentage of each personnel type across all revenue sources.")
                            
                            # Process and display data for each year
                            for year in range(start_year, end_year + 1):
                                st.markdown(f"### Year {year}")
                                
                                # Initialize a dictionary to store staff usage hours by type
                                staff_usage = {}
                                staff_capacity = {}
                                
                                # Initialize staff capacity from available staff
                                available_staff = calculator.get_available_staff(f"01/01/{year}")
                                staff_hours = calculator.calculate_staff_hours_available(f"01/01/{year}")
                                
                                for staff_type, hours in staff_hours.items():
                                    staff_capacity[staff_type] = hours * proforma_data['work_days']
                                    staff_usage[staff_type] = 0
                                
                                # For each revenue source, calculate staff hours used
                                for revenue_source in selected_sources:
                                    try:
                                        # Calculate annual exam volume for this revenue source using work_days from proforma
                                        annual_volume = calculator.calculate_annual_exam_volume(year, revenue_source, proforma_data['work_days'])
                                        
                                        # For each exam, calculate staff hours used
                                        for _, exam_row in annual_volume.iterrows():
                                            if "Title" not in exam_row and "Exam" not in exam_row: continue
                                            exam_title = exam_row["Title"] if "Title" in exam_row else exam_row["Exam"]
                                            annual_volume_num = exam_row['AnnualVolume']
                                            
                                            # Get the exam details
                                            exam_data = updated_data['Exams'][updated_data['Exams']['Title'] == exam_title]
                                            
                                            if not exam_data.empty:
                                                # Get staff types for this exam
                                                staff_types = exam_data.iloc[0]['Staff']
                                                if isinstance(staff_types, list):
                                                    staff_list = staff_types
                                                else:
                                                    staff_list = [s.strip() for s in str(staff_types).split(';')]
                                                
                                                # Get exam duration in hours
                                                duration_hours = exam_data.iloc[0]['Duration'] / 60.0 if 'Duration' in exam_data else 0
                                                
                                                # Add hours to each staff type
                                                for staff_type in staff_list:
                                                    if staff_type and staff_type.strip():
                                                        staff_type = staff_type.strip()
                                                        if staff_type not in staff_usage:
                                                            staff_usage[staff_type] = 0
                                                        
                                                        # Add the hours used for this exam
                                                        staff_usage[staff_type] += annual_volume_num * duration_hours
                                    except Exception as e:
                                        st.error(f"Error calculating staff usage for {revenue_source}: {str(e)}")
                                
                                # Calculate utilization percentages
                                utilization = []
                                for staff_type, hours_used in staff_usage.items():
                                    capacity = staff_capacity.get(staff_type, 0)
                                    usage_pct = (hours_used / capacity * 100) if capacity > 0 else 0
                                    utilization.append({
                                        'Staff Type': staff_type,
                                        'Hours Used': hours_used,
                                        'Total Capacity (Hours)': capacity,
                                        'Utilization %': usage_pct
                                    })
                                
                                if utilization:
                                    # Convert to dataframe and sort
                                    util_df = pd.DataFrame(utilization)
                                    util_df = util_df.sort_values(by='Utilization %', ascending=False)
                                    
                                    # Plot the utilization percentages
                                    fig, ax = plt.subplots(figsize=(10, 6))
                                    
                                    # Create bars
                                    bar_positions = np.arange(len(util_df))
                                    bars = ax.bar(bar_positions, util_df['Utilization %'], 
                                                 color=['red' if pct > 100 else 'green' for pct in util_df['Utilization %']])
                                    
                                    # Add data labels
                                    for i, (_, row) in enumerate(util_df.iterrows()):
                                        ax.text(i, row['Utilization %'] + 1, f"{row['Utilization %']:.1f}%", 
                                              ha='center', va='bottom', fontsize=9)
                                    
                                    # Add a horizontal line at 100%
                                    ax.axhline(y=100, linestyle='--', color='r', alpha=0.7)
                                    
                                    # Set title and labels
                                    ax.set_title(f"Personnel Utilization in {year}")
                                    ax.set_ylabel('Utilization %')
                                    ax.set_xticks(bar_positions)
                                    ax.set_xticklabels(util_df['Staff Type'], rotation=45, ha='right')
                                    
                                    # Add grid and adjust layout
                                    ax.grid(axis='y', linestyle='--', alpha=0.7)
                                    ax.set_ylim(0, max(110, util_df['Utilization %'].max() * 1.1))
                                    plt.tight_layout()
                                    
                                    # Display the plot
                                    st.pyplot(fig)
                                    
                                    # Display the data table
                                    display_df = util_df.copy()
                                    display_df['Hours Used'] = display_df['Hours Used'].map('{:,.1f}'.format)
                                    display_df['Total Capacity (Hours)'] = display_df['Total Capacity (Hours)'].map('{:,.1f}'.format)
                                    display_df['Utilization %'] = display_df['Utilization %'].map('{:.1f}%'.format)
                                    
                                    st.dataframe(display_df, use_container_width=True)
                                    
                                    # Highlight potential staffing issues
                                    over_utilized = util_df[util_df['Utilization %'] > 100]
                                    if not over_utilized.empty:
                                        st.warning("### Potential Staffing Issues")
                                        st.write("The following staff types are over-utilized and may be limiting exam volume:")
                                        for _, row in over_utilized.iterrows():
                                            st.write(f"- **{row['Staff Type']}**: {row['Utilization %']:.1f}% utilization")
                                        
                                        st.write("Recommendations:")
                                        st.write("1. Consider hiring additional staff for these roles")
                                        st.write("2. Reduce exam volume expectations")
                                        st.write("3. Increase staff efficiency or adjust exam durations")
                                    
                                    # Highlight under-utilized staff
                                    under_utilized = util_df[util_df['Utilization %'] < 50]
                                    if not under_utilized.empty:
                                        st.info("### Efficiency Opportunities")
                                        st.write("The following staff types are under-utilized and may present efficiency opportunities:")
                                        for _, row in under_utilized.iterrows():
                                            st.write(f"- **{row['Staff Type']}**: {row['Utilization %']:.1f}% utilization")
                                        
                                        st.write("Recommendations:")
                                        st.write("1. Consider reducing staff levels for these roles")
                                        st.write("2. Cross-train these staff for other responsibilities")
                                        st.write("3. Increase exam offerings that utilize these staff types")
                                else:
                                    st.write("No personnel utilization data available.")
        
        except Exception as e:
            st.error(f"An error occurred during analysis: {str(e)}")

# Comprehensive Report Tab
with tabs[12]:  # Last tab (index 12) is Comprehensive Report
    st.header("Comprehensive Report")
    
    # Explanation of the report
    st.info(
        "This tab provides a comprehensive report of financial projections and analysis based on your data. "
        "First, enter the parameters below and generate the report. Then you can download it as a PDF."
    )
    
    # Add a note about running comprehensive proforma first
    st.warning(
        "**Important**: You must first generate the Comprehensive Proforma analysis before running this report. "
        "This ensures that the Comprehensive Report uses the same data and calculations as the financial projections."
    )
    
    # Check if comprehensive proforma results exist
    if 'comprehensive_proforma_results' not in st.session_state or st.session_state.comprehensive_proforma_results is None:
        st.error("No Comprehensive Proforma data available. Please go to the 'Comprehensive Proforma' tab and generate the proforma first.")
    else:
        # Generate report button
        if st.button("Generate Comprehensive Report"):
            try:
                with st.spinner("Generating comprehensive report..."):
                    # Display key metrics and visualizations from the comprehensive proforma
                    proforma_data = st.session_state.comprehensive_proforma_results
                    
                    # Key Financial Metrics
                    st.subheader("Key Financial Metrics")
                    metrics = proforma_data['results']['financial_metrics']
                    
                    # Display metrics in a visually appealing format
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
                    formatted_summary = proforma_data['results']['annual_summary'].copy()
                    for col in formatted_summary.columns:
                        if col != 'Year' and formatted_summary[col].dtype in [np.float64, np.int64]:
                            formatted_summary[col] = formatted_summary[col].map('${:,.2f}'.format)
                    
                    st.dataframe(formatted_summary)
                    
                    # Create visualization of revenue vs expenses
                    st.subheader("Revenue vs Expenses")
                    annual_data = proforma_data['results']['annual_summary']
                    
                    # Plot
                    fig, ax = plt.subplots(figsize=(10, 6))
                    ax.plot(annual_data['Year'], annual_data['Total_Revenue'], marker='o', linewidth=2, label='Revenue')
                    ax.plot(annual_data['Year'], annual_data['Total_Expenses'], marker='s', linewidth=2, label='Expenses')
                    ax.plot(annual_data['Year'], annual_data['Net_Income'], marker='^', linewidth=2, label='Net Income')
                    
                    # Add a horizontal line at y=0
                    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.7)
                    
                    # Format the plot
                    ax.set_title('Annual Financial Performance')
                    ax.set_xlabel('Year')
                    ax.set_ylabel('Amount ($)')
                    ax.grid(True, linestyle='--', alpha=0.7)
                    ax.legend()
                    
                    # Format y-axis with dollar signs
                    fmt = '${x:,.0f}'
                    tick = mticker.StrMethodFormatter(fmt)
                    ax.yaxis.set_major_formatter(tick)
                    
                    st.pyplot(fig)
                    
                    # Display the expense breakdown
                    st.subheader("Expense Breakdown")
                    
                    # Calculate total expense for each category across all years
                    total_personnel = annual_data['Personnel_Expenses'].sum()
                    total_equipment = annual_data['Equipment_Expenses'].sum()
                    total_exam_direct = annual_data['Exam_Direct_Expenses'].sum()
                    total_other_expense = annual_data['Other_Expenses'].sum()
                    
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
                    
                    # If monthly data is available, show cash flow
                    if 'monthly_cash_flow' in proforma_data['results']:
                        st.subheader("Monthly Cash Flow")
                        monthly_cash_flow = proforma_data['results']['monthly_cash_flow']
                        
                        # Plot monthly cash flow
                        fig, ax = plt.subplots(figsize=(12, 6))
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
                    
                    # Show download instructions after the report is generated
                    st.subheader("Download Comprehensive Report")
                    st.info("To save this entire report, please use your browser's print functionality to save as PDF.")
                    st.write("1. Press Ctrl+P (or Cmd+P on Mac)")
                    st.write("2. Change the destination to 'Save as PDF'")
                    st.write("3. Click Save")
                    
                    # Provide a summary of what was included in the report
                    st.subheader("Report Summary")
                    st.write("This comprehensive report includes:")
                    st.markdown("""
                    - Raw CSV data from all input files
                    - Financial metrics and projections
                    - Personnel expense analysis and visualizations
                    - Equipment expense analysis and visualizations
                    - Exam revenue analysis by type and source
                    - Other expenses breakdown
                    - Volume limiting factors analysis
                    """)
                    
                    # Add disclaimer
                    st.markdown("---")
                    st.markdown("""
                    **Disclaimer**: This report is generated based on the data and parameters provided in the input files and parameters selected.
                    The financial projections and analysis should be used for planning purposes only and validated by financial experts.
                    """)
            except Exception as e:
                import traceback
                st.error(f"Error generating comprehensive report: {str(e)}")
                st.error(traceback.format_exc())
        else:
            # Only show this when report hasn't been generated yet
            st.write("Click the 'Generate Comprehensive Report' button to create a detailed report based on your proforma analysis.")
            
            # Empty placeholders for download instructions that will be shown only after report generation
            st.subheader("Download Comprehensive Report")
            st.info("The download instructions will appear here after you generate the report.")

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