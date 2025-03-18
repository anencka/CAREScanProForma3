"""
Example usage of the financeModels package.

This module demonstrates how to use the personnelExpenses module
to calculate various financial metrics for the CAREScan ProForma.
"""

import pandas as pd
import matplotlib.pyplot as plt
from financeModels.personnel_expenses import PersonnelExpenseCalculator, calculate_personnel_expenses

def run_personnel_expense_example():
    """Run an example of personnel expense calculations."""
    print("Running Personnel Expense Calculation Example")
    print("=" * 50)
    
    # Load the personnel data
    personnel_file = "Personnel.csv"
    calculator = PersonnelExpenseCalculator(personnel_file=personnel_file)
    
    # Define the date range for calculations (example: 5-year projection)
    start_date = "01/01/2025"
    end_date = "12/31/2029"
    
    # Calculate monthly expenses
    print("\nCalculating monthly expenses...")
    monthly_df = calculator.calculate_monthly_expense(start_date, end_date)
    print(f"Generated {len(monthly_df)} monthly expense records")
    print(monthly_df.head())
    
    # Calculate annual expenses
    print("\nCalculating annual expenses...")
    annual_df = calculator.calculate_annual_expense(start_date, end_date)
    print(annual_df.head())
    
    # Calculate expenses by category
    print("\nCalculating expenses by category...")
    category_df = calculator.calculate_total_by_category(start_date, end_date)
    print(category_df)
    
    # Calculate grand total
    print("\nCalculating grand total...")
    grand_total = calculator.calculate_grand_total(start_date, end_date)
    print(f"Total Base Expense: ${grand_total['Base_Expense']:,.2f}")
    print(f"Total Fringe Amount: ${grand_total['Fringe_Amount']:,.2f}")
    print(f"Total Personnel Expense: ${grand_total['Total_Expense']:,.2f}")
    
    # Calculate headcount
    print("\nCalculating headcount by month...")
    headcount_df = calculator.get_headcount_by_month(start_date, end_date)
    print(headcount_df.head())
    
    # Example of using the utility function directly
    print("\nUsing utility function to calculate all reports at once...")
    results = calculate_personnel_expenses(
        personnel_data=pd.read_csv(personnel_file, skipinitialspace=True),
        start_date=start_date,
        end_date=end_date
    )
    
    # Access the results
    print(f"Results contain {len(results)} reports:")
    for report_name in results:
        if isinstance(results[report_name], pd.DataFrame):
            print(f"- {report_name}: DataFrame with {len(results[report_name])} records")
        else:
            print(f"- {report_name}: {type(results[report_name])}")
    
    return results

def visualize_personnel_expenses(results):
    """Create some visualizations of personnel expenses."""
    if 'annual' not in results:
        print("Annual results not found in the results dictionary")
        return
    
    annual_df = results['annual']
    
    # Visualization 1: Annual expenses by year
    plt.figure(figsize=(12, 6))
    annual_totals = annual_df.groupby('Year')['Total_Expense'].sum()
    annual_totals.plot(kind='bar', color='skyblue')
    plt.title('Total Personnel Expenses by Year')
    plt.xlabel('Year')
    plt.ylabel('Total Expense ($)')
    plt.xticks(rotation=0)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('personnel_expenses_by_year.png')
    
    # Visualization 2: Expenses by institution and type
    if 'by_category' in results:
        category_df = results['by_category']
        
        plt.figure(figsize=(14, 7))
        pivot_df = category_df.pivot_table(
            index='Institution', 
            columns='Type', 
            values='Total_Expense',
            aggfunc='sum',
            fill_value=0
        )
        pivot_df.plot(kind='bar', stacked=True, colormap='viridis')
        plt.title('Personnel Expenses by Institution and Type')
        plt.xlabel('Institution')
        plt.ylabel('Total Expense ($)')
        plt.xticks(rotation=45)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.legend(title='Staff Type')
        plt.tight_layout()
        plt.savefig('personnel_expenses_by_category.png')
    
    # Visualization 3: Headcount over time
    if 'headcount' in results:
        headcount_df = results['headcount']
        
        # Create a date column for better plotting
        headcount_df['Date'] = pd.to_datetime(
            headcount_df['Year'].astype(str) + '-' + 
            headcount_df['Month'].astype(str) + '-01'
        )
        
        plt.figure(figsize=(14, 6))
        headcount_pivoted = headcount_df.pivot_table(
            index='Date', 
            columns='Type', 
            values='FTE_Count',
            aggfunc='sum',
            fill_value=0
        )
        headcount_pivoted.plot(kind='area', stacked=True, alpha=0.7, colormap='tab10')
        plt.title('FTE Count Over Time by Staff Type')
        plt.xlabel('Date')
        plt.ylabel('FTE Count')
        plt.grid(linestyle='--', alpha=0.7)
        plt.legend(title='Staff Type')
        plt.tight_layout()
        plt.savefig('personnel_fte_over_time.png')
    
    print("Visualizations saved to PNG files.")

if __name__ == "__main__":
    # Run the example
    results = run_personnel_expense_example()
    
    # Create visualizations (uncomment to run)
    # Note: This requires matplotlib to be installed
    # visualize_personnel_expenses(results) 