import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union
import calendar

class OtherExpensesCalculator:
    """
    A class to calculate other expenses and revenue items, based on the OtherExpenses.csv file.
    This model accounts for both expense and revenue items through the 'Expense' boolean column.
    """
    
    def __init__(self, other_data: pd.DataFrame = None, other_file: str = None):
        """
        Initialize the calculator with other expenses/revenue data.

        Args:
            other_data: DataFrame containing other expenses/revenue data
            other_file: Path to a CSV file containing other expenses/revenue data
        """
        if other_data is not None:
            self.other_data = other_data.copy()
        elif other_file is not None:
            self.other_data = pd.read_csv(other_file, skipinitialspace=True)
        else:
            self.other_data = None
            
        # Process data if available
        if self.other_data is not None:
            self._process_data()
    
    def _process_data(self):
        """Process the other expenses/revenue data to prepare for calculations."""
        # Convert date strings to datetime objects
        if 'AppliedDate' in self.other_data.columns:
            self.other_data['AppliedDate'] = pd.to_datetime(
                self.other_data['AppliedDate'], 
                format='%m/%d/%Y', 
                errors='coerce'
            )
        
        # Ensure the Expense column is boolean
        if 'Expense' in self.other_data.columns:
            if self.other_data['Expense'].dtype != bool:
                self.other_data['Expense'] = self.other_data['Expense'].map({'True': True, 'False': False})
    
    def load_data(self, other_data: pd.DataFrame = None, other_file: str = None):
        """
        Load other expenses/revenue data from a DataFrame or CSV file.
        
        Args:
            other_data: DataFrame containing other expenses/revenue data
            other_file: Path to a CSV file containing other expenses/revenue data
        """
        if other_data is not None:
            self.other_data = other_data.copy()
        elif other_file is not None:
            self.other_data = pd.read_csv(other_file, skipinitialspace=True)
        else:
            raise ValueError("Either other_data or other_file must be provided")
        
        self._process_data()
        return self
    
    def calculate_annual_items(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Calculate annual expenses/revenue within a date range.
        
        Args:
            start_date: Start date in format 'MM/DD/YYYY'
            end_date: End date in format 'MM/DD/YYYY'
            
        Returns:
            DataFrame with annual expenses and revenue
        """
        if self.other_data is None:
            raise ValueError("Other expenses/revenue data not loaded. Call load_data first.")
        
        # Convert input dates to datetime
        start_dt = pd.to_datetime(start_date, format='%m/%d/%Y')
        end_dt = pd.to_datetime(end_date, format='%m/%d/%Y')
        
        # Create a list to store annual items records
        annual_items = []
        
        # Process each expense/revenue item
        for _, item in self.other_data.iterrows():
            applied_date = item['AppliedDate']
            
            # Skip if item is applied after the specified end date
            if applied_date > end_dt:
                continue
            
            # Skip if item is applied before the specified start date
            if applied_date < start_dt:
                continue
            
            # Add record to the list
            record = {
                'Title': item['Title'],
                'Vendor': item['Vendor'],
                'Year': applied_date.year,
                'Month': applied_date.month,
                'Amount': item['Amount'],
                'Description': item['Description'],
                'IsExpense': item['Expense'],
                'Category': 'Expense' if item['Expense'] else 'Revenue'
            }
            annual_items.append(record)
        
        # Convert to DataFrame
        result = pd.DataFrame(annual_items)
        return result
    
    def calculate_by_category(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Calculate expenses/revenue by category.
        
        Args:
            start_date: Start date in format 'MM/DD/YYYY'
            end_date: End date in format 'MM/DD/YYYY'
            
        Returns:
            DataFrame with expenses/revenue aggregated by category
        """
        # Get items first
        items_df = self.calculate_annual_items(start_date, end_date)
        
        if items_df.empty:
            return pd.DataFrame(columns=['Title', 'Category', 'Amount'])
        
        # Group by title and category
        category_df = items_df.groupby(['Title', 'Category']).agg({
            'Amount': 'sum',
        }).reset_index()
        
        return category_df
    
    def calculate_expense_total(self, start_date: str, end_date: str) -> float:
        """
        Calculate grand total of all expenses.
        
        Args:
            start_date: Start date in format 'MM/DD/YYYY'
            end_date: End date in format 'MM/DD/YYYY'
            
        Returns:
            Total expenses amount
        """
        # Get items first
        items_df = self.calculate_annual_items(start_date, end_date)
        
        # Calculate grand total for expenses only
        if not items_df.empty:
            expense_total = items_df[items_df['IsExpense']]['Amount'].sum()
        else:
            expense_total = 0.0
        
        return expense_total
    
    def calculate_revenue_total(self, start_date: str, end_date: str) -> float:
        """
        Calculate grand total of all revenue.
        
        Args:
            start_date: Start date in format 'MM/DD/YYYY'
            end_date: End date in format 'MM/DD/YYYY'
            
        Returns:
            Total revenue amount
        """
        # Get items first
        items_df = self.calculate_annual_items(start_date, end_date)
        
        # Calculate grand total for revenue only
        if not items_df.empty:
            revenue_total = items_df[~items_df['IsExpense']]['Amount'].sum()
        else:
            revenue_total = 0.0
        
        return revenue_total
    
    def calculate_net_total(self, start_date: str, end_date: str) -> float:
        """
        Calculate net total (revenue - expenses).
        
        Args:
            start_date: Start date in format 'MM/DD/YYYY'
            end_date: End date in format 'MM/DD/YYYY'
            
        Returns:
            Net total amount
        """
        revenue = self.calculate_revenue_total(start_date, end_date)
        expenses = self.calculate_expense_total(start_date, end_date)
        return revenue - expenses
    
    def calculate_summary(self, start_date: str, end_date: str) -> Dict[str, float]:
        """
        Calculate summary of expenses, revenue, and net total.
        
        Args:
            start_date: Start date in format 'MM/DD/YYYY'
            end_date: End date in format 'MM/DD/YYYY'
            
        Returns:
            Dictionary with grand totals
        """
        # Get totals
        revenue = self.calculate_revenue_total(start_date, end_date)
        expenses = self.calculate_expense_total(start_date, end_date)
        net_total = revenue - expenses
        
        # Create summary
        summary = {
            'Total_Revenue': revenue,
            'Total_Expenses': expenses,
            'Net_Total': net_total
        }
        
        return summary


# Utility function for direct use without instantiating the class
def calculate_other_expenses(other_data: pd.DataFrame, start_date: str, end_date: str) -> Dict[str, Union[pd.DataFrame, Dict[str, float]]]:
    """
    Calculate other expenses/revenue and return a dictionary of results.
    
    Args:
        other_data: DataFrame containing other expenses/revenue data
        start_date: Start date in format 'MM/DD/YYYY'
        end_date: End date in format 'MM/DD/YYYY'
        
    Returns:
        Dictionary containing calculated DataFrames and summaries
    """
    calculator = OtherExpensesCalculator(other_data=other_data)
    
    results = {
        'annual_items': calculator.calculate_annual_items(start_date, end_date),
        'by_category': calculator.calculate_by_category(start_date, end_date),
        'summary': calculator.calculate_summary(start_date, end_date)
    }
    
    return results 