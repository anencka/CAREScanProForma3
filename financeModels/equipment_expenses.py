import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union
import calendar

class EquipmentExpenseCalculator:
    """
    A class to calculate equipment expenses, including purchase costs, depreciation, 
    service costs, and other related expenses.
    """
    
    def __init__(self, equipment_data: pd.DataFrame = None, equipment_file: str = None):
        """
        Initialize the calculator with equipment data.

        Args:
            equipment_data: DataFrame containing equipment data
            equipment_file: Path to a CSV file containing equipment data
        """
        if equipment_data is not None:
            self.equipment_data = equipment_data.copy()
        elif equipment_file is not None:
            self.equipment_data = pd.read_csv(equipment_file, skipinitialspace=True)
        else:
            self.equipment_data = None
            
        # Process data if available
        if self.equipment_data is not None:
            self._process_data()
    
    def _process_data(self):
        """Process the equipment data to prepare for calculations."""
        # Convert date strings to datetime objects
        if 'PurchaseDate' in self.equipment_data.columns:
            self.equipment_data['PurchaseDate'] = pd.to_datetime(
                self.equipment_data['PurchaseDate'], 
                format='%m/%d/%Y', 
                errors='coerce'
            )
    
    def load_data(self, equipment_data: pd.DataFrame = None, equipment_file: str = None):
        """
        Load equipment data from a DataFrame or CSV file.
        
        Args:
            equipment_data: DataFrame containing equipment data
            equipment_file: Path to a CSV file containing equipment data
        """
        if equipment_data is not None:
            self.equipment_data = equipment_data.copy()
        elif equipment_file is not None:
            self.equipment_data = pd.read_csv(equipment_file, skipinitialspace=True)
        else:
            raise ValueError("Either equipment_data or equipment_file must be provided")
        
        self._process_data()
        return self
    
    def calculate_annual_expenses(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Calculate annual equipment expenses within a date range.
        
        Args:
            start_date: Start date in format 'MM/DD/YYYY'
            end_date: End date in format 'MM/DD/YYYY'
            
        Returns:
            DataFrame with annual equipment expenses
        """
        if self.equipment_data is None:
            raise ValueError("Equipment data not loaded. Call load_data first.")
        
        # Convert input dates to datetime
        start_dt = pd.to_datetime(start_date, format='%m/%d/%Y')
        end_dt = pd.to_datetime(end_date, format='%m/%d/%Y')
        
        # Create a list to store annual expense records
        annual_expenses = []
        
        # Process each equipment item
        for _, equipment in self.equipment_data.iterrows():
            purchase_date = equipment['PurchaseDate']
            
            # Skip if equipment is purchased after the specified end date
            if purchase_date > end_dt:
                continue
            
            # Calculate end of life date based on lifespan
            end_of_life_date = purchase_date + pd.DateOffset(years=equipment['Lifespan'])
            
            # Generate records for each year in the date range
            current_year = max(purchase_date.year, start_dt.year)
            last_year = min(end_of_life_date.year, end_dt.year)
            
            for year in range(current_year, last_year + 1):
                # Calculate the fraction of the year the equipment is in service
                year_start = datetime(year, 1, 1)
                year_end = datetime(year, 12, 31)
                
                effective_start = max(purchase_date, year_start)
                effective_end = min(end_of_life_date, year_end)
                
                # If equipment wasn't in service during this year, skip
                if effective_start > effective_end:
                    continue
                
                # Calculate days in service this year
                days_in_year = 366 if calendar.isleap(year) else 365
                days_in_service = (effective_end - effective_start).days + 1
                year_fraction = days_in_service / days_in_year
                
                # Calculate annual depreciation
                annual_depreciation = equipment['PurchaseCost'] / equipment['Lifespan']
                
                # Calculate prorated depreciation for partial years
                depreciation = annual_depreciation * year_fraction
                
                # Calculate annual recurring costs
                service_cost = equipment['AnnualServiceCost'] * year_fraction
                accreditation_cost = equipment['AnnualAccreditationCost'] * year_fraction
                insurance_cost = equipment['AnnualInsuranceCost'] * year_fraction
                
                # Calculate total annual expense
                total_annual_expense = service_cost + accreditation_cost + insurance_cost
                
                # Add record to the list
                record = {
                    'Title': equipment['Title'],
                    'Year': year,
                    'PurchaseCost': equipment['PurchaseCost'],
                    'QuantityPurchased': equipment['Quantity'],
                    'AnnualDepreciation': depreciation,
                    'ServiceCost': service_cost,
                    'AccreditationCost': accreditation_cost,
                    'InsuranceCost': insurance_cost,
                    'TotalAnnualExpense': total_annual_expense
                }
                annual_expenses.append(record)
        
        # Convert to DataFrame
        result = pd.DataFrame(annual_expenses)
        return result
    
    def calculate_total_by_equipment(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Calculate total equipment expenses by equipment type.
        
        Args:
            start_date: Start date in format 'MM/DD/YYYY'
            end_date: End date in format 'MM/DD/YYYY'
            
        Returns:
            DataFrame with expenses aggregated by equipment type
        """
        # Get annual expenses first
        annual_df = self.calculate_annual_expenses(start_date, end_date)
        
        if annual_df.empty:
            return pd.DataFrame()
        
        # Group by equipment type
        equipment_df = annual_df.groupby('Title').agg({
            'PurchaseCost': 'first',
            'QuantityPurchased': 'first',
            'AnnualDepreciation': 'sum',
            'ServiceCost': 'sum',
            'AccreditationCost': 'sum',
            'InsuranceCost': 'sum',
            'TotalAnnualExpense': 'sum'
        }).reset_index()
        
        return equipment_df
    
    def calculate_grand_total(self, start_date: str, end_date: str) -> Dict[str, float]:
        """
        Calculate grand total of all equipment expenses.
        
        Args:
            start_date: Start date in format 'MM/DD/YYYY'
            end_date: End date in format 'MM/DD/YYYY'
            
        Returns:
            Dictionary with grand totals
        """
        # Get annual expenses first
        annual_df = self.calculate_annual_expenses(start_date, end_date)
        
        if annual_df.empty:
            return {
                'TotalPurchaseCost': 0,
                'TotalDepreciation': 0,
                'TotalServiceCost': 0,
                'TotalAccreditationCost': 0,
                'TotalInsuranceCost': 0,
                'TotalAnnualExpense': 0
            }
        
        # Calculate grand totals
        purchase_costs = self.equipment_data['PurchaseCost'] * self.equipment_data['Quantity']
        
        grand_total = {
            'TotalPurchaseCost': purchase_costs.sum(),
            'TotalDepreciation': annual_df['AnnualDepreciation'].sum(),
            'TotalServiceCost': annual_df['ServiceCost'].sum(),
            'TotalAccreditationCost': annual_df['AccreditationCost'].sum(),
            'TotalInsuranceCost': annual_df['InsuranceCost'].sum(),
            'TotalAnnualExpense': annual_df['TotalAnnualExpense'].sum()
        }
        
        return grand_total


# Utility function for direct use without instantiating the class
def calculate_equipment_expenses(equipment_data: pd.DataFrame, start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
    """
    Utility function to calculate equipment expenses without having to manually instantiate the class.
    
    Args:
        equipment_data: DataFrame containing equipment data
        start_date: Start date in format 'MM/DD/YYYY'
        end_date: End date in format 'MM/DD/YYYY'
        
    Returns:
        Dictionary with annual expenses, expenses by equipment type, and grand totals
    """
    calculator = EquipmentExpenseCalculator(equipment_data=equipment_data)
    
    annual_expenses = calculator.calculate_annual_expenses(start_date, end_date)
    expenses_by_equipment = calculator.calculate_total_by_equipment(start_date, end_date)
    grand_total = calculator.calculate_grand_total(start_date, end_date)
    
    return {
        'annual': annual_expenses,
        'by_equipment': expenses_by_equipment,
        'grand_total': grand_total
    } 