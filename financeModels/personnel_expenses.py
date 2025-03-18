import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union
import calendar

class PersonnelExpenseCalculator:
    """
    A class to calculate personnel expenses based on salary, effort, fringe benefits,
    and time periods.
    """
    
    def __init__(self, personnel_data: pd.DataFrame = None, personnel_file: str = None):
        """
        Initialize the calculator with personnel data.

        Args:
            personnel_data: DataFrame containing personnel data
            personnel_file: Path to a CSV file containing personnel data
        """
        if personnel_data is not None:
            self.personnel_data = personnel_data.copy()
        elif personnel_file is not None:
            self.personnel_data = pd.read_csv(personnel_file, skipinitialspace=True)
        else:
            self.personnel_data = None
            
        # Convert date columns to datetime objects if data is available
        if self.personnel_data is not None:
            self._process_data()
    
    def _process_data(self):
        """Process the personnel data to prepare for calculations."""
        # Convert date strings to datetime objects
        for date_col in ['StartDate', 'EndDate']:
            if date_col in self.personnel_data.columns:
                self.personnel_data[date_col] = pd.to_datetime(
                    self.personnel_data[date_col], 
                    format='%m/%d/%Y', 
                    errors='coerce'
                )
    
    def load_data(self, personnel_data: pd.DataFrame = None, personnel_file: str = None):
        """
        Load personnel data from a DataFrame or CSV file.
        
        Args:
            personnel_data: DataFrame containing personnel data
            personnel_file: Path to a CSV file containing personnel data
        """
        if personnel_data is not None:
            self.personnel_data = personnel_data.copy()
        elif personnel_file is not None:
            self.personnel_data = pd.read_csv(personnel_file, skipinitialspace=True)
        else:
            raise ValueError("Either personnel_data or personnel_file must be provided")
        
        self._process_data()
        return self
    
    def calculate_monthly_expense(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Calculate monthly personnel expenses within a date range.
        
        Args:
            start_date: Start date in format 'MM/DD/YYYY'
            end_date: End date in format 'MM/DD/YYYY'
            
        Returns:
            DataFrame with monthly expenses by person
        """
        if self.personnel_data is None:
            raise ValueError("Personnel data not loaded. Call load_data first.")
        
        # Convert input dates to datetime
        start_dt = pd.to_datetime(start_date, format='%m/%d/%Y')
        end_dt = pd.to_datetime(end_date, format='%m/%d/%Y')
        
        # Create a list to store monthly expense records
        monthly_expenses = []
        
        # Process each person
        for _, person in self.personnel_data.iterrows():
            # Skip if person starts after the specified end date or ends before the specified start date
            if pd.notna(person['StartDate']) and person['StartDate'] > end_dt:
                continue
            if pd.notna(person['EndDate']) and person['EndDate'] < start_dt:
                continue
                
            # Calculate effective start and end dates
            effective_start = max(person['StartDate'], start_dt) if pd.notna(person['StartDate']) else start_dt
            effective_end = min(person['EndDate'], end_dt) if pd.notna(person['EndDate']) else end_dt
            
            # Generate monthly records
            current_date = effective_start.replace(day=1)
            while current_date <= effective_end:
                year = current_date.year
                month = current_date.month
                
                # Calculate days in month and worked days in month
                days_in_month = calendar.monthrange(year, month)[1]
                
                month_start = current_date
                month_end = current_date.replace(day=days_in_month)
                
                # Adjust for partial months
                if month_start.month == effective_start.month and month_start.year == effective_start.year:
                    first_day = effective_start.day
                else:
                    first_day = 1
                    
                if month_end.month == effective_end.month and month_end.year == effective_end.year:
                    last_day = effective_end.day
                else:
                    last_day = days_in_month
                
                days_worked = last_day - first_day + 1
                month_fraction = days_worked / days_in_month
                
                # Calculate monthly expense
                monthly_salary = person['Salary'] / 12
                monthly_expense = monthly_salary * person['Effort'] * month_fraction
                fringe_benefit = monthly_expense * person['Fringe']
                total_expense = monthly_expense + fringe_benefit
                
                # Create record
                record = {
                    'Title': person['Title'],
                    'Type': person['Type'],
                    'Institution': person['Institution'],
                    'Year': year,
                    'Month': month,
                    'Salary': monthly_salary,
                    'Effort': person['Effort'],
                    'Days': days_worked,
                    'Base_Expense': monthly_expense,
                    'Fringe_Rate': person['Fringe'],
                    'Fringe_Amount': fringe_benefit,
                    'Total_Expense': total_expense
                }
                monthly_expenses.append(record)
                
                # Move to next month
                if month == 12:
                    current_date = current_date.replace(year=year+1, month=1)
                else:
                    current_date = current_date.replace(month=month+1)
        
        # Convert to DataFrame
        result = pd.DataFrame(monthly_expenses)
        return result
    
    def calculate_annual_expense(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Calculate annual personnel expenses within a date range.
        
        Args:
            start_date: Start date in format 'MM/DD/YYYY'
            end_date: End date in format 'MM/DD/YYYY'
            
        Returns:
            DataFrame with annual expenses by person
        """
        # Get monthly expenses first
        monthly_df = self.calculate_monthly_expense(start_date, end_date)
        
        # Group by person and year
        annual_df = monthly_df.groupby(['Title', 'Type', 'Institution', 'Year']).agg({
            'Base_Expense': 'sum',
            'Fringe_Amount': 'sum',
            'Total_Expense': 'sum'
        }).reset_index()
        
        return annual_df
    
    def calculate_total_by_category(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Calculate total personnel expenses by Type and Institution.
        
        Args:
            start_date: Start date in format 'MM/DD/YYYY'
            end_date: End date in format 'MM/DD/YYYY'
            
        Returns:
            DataFrame with expenses aggregated by Type and Institution
        """
        # Get monthly expenses first
        monthly_df = self.calculate_monthly_expense(start_date, end_date)
        
        # Group by type and institution
        category_df = monthly_df.groupby(['Type', 'Institution']).agg({
            'Base_Expense': 'sum',
            'Fringe_Amount': 'sum',
            'Total_Expense': 'sum'
        }).reset_index()
        
        return category_df
    
    def calculate_grand_total(self, start_date: str, end_date: str) -> Dict[str, float]:
        """
        Calculate grand total of all personnel expenses.
        
        Args:
            start_date: Start date in format 'MM/DD/YYYY'
            end_date: End date in format 'MM/DD/YYYY'
            
        Returns:
            Dictionary with grand totals
        """
        # Get monthly expenses first
        monthly_df = self.calculate_monthly_expense(start_date, end_date)
        
        # Calculate grand totals
        grand_total = {
            'Base_Expense': monthly_df['Base_Expense'].sum(),
            'Fringe_Amount': monthly_df['Fringe_Amount'].sum(),
            'Total_Expense': monthly_df['Total_Expense'].sum()
        }
        
        return grand_total
    
    def get_headcount_by_month(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Calculate headcount by month, accounting for effort.
        
        Args:
            start_date: Start date in format 'MM/DD/YYYY'
            end_date: End date in format 'MM/DD/YYYY'
            
        Returns:
            DataFrame with headcount by month and type
        """
        # Get monthly expenses
        monthly_df = self.calculate_monthly_expense(start_date, end_date)
        
        # For headcount, count each person weighted by their effort
        headcount_df = monthly_df.groupby(['Year', 'Month', 'Type']).agg({
            'Effort': 'sum',  # Sum of efforts gives the FTE count
            'Title': 'count'  # Number of unique people
        }).reset_index()
        
        headcount_df = headcount_df.rename(columns={
            'Effort': 'FTE_Count', 
            'Title': 'Headcount'
        })
        
        return headcount_df


# Utility functions for direct use without instantiating the class

def calculate_personnel_expenses(personnel_data: pd.DataFrame, start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
    """
    Calculate various personnel expense reports.
    
    Args:
        personnel_data: DataFrame containing personnel data
        start_date: Start date in format 'MM/DD/YYYY'
        end_date: End date in format 'MM/DD/YYYY'
        
    Returns:
        Dictionary with different expense reports
    """
    calculator = PersonnelExpenseCalculator(personnel_data=personnel_data)
    
    results = {
        'monthly': calculator.calculate_monthly_expense(start_date, end_date),
        'annual': calculator.calculate_annual_expense(start_date, end_date),
        'by_category': calculator.calculate_total_by_category(start_date, end_date),
        'grand_total': calculator.calculate_grand_total(start_date, end_date),
        'headcount': calculator.get_headcount_by_month(start_date, end_date)
    }
    
    return results 