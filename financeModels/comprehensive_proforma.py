import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union
import calendar
import matplotlib.pyplot as plt

from financeModels.personnel_expenses import PersonnelExpenseCalculator
from financeModels.exam_revenue import ExamRevenueCalculator
from financeModels.equipment_expenses import EquipmentExpenseCalculator
from financeModels.other_expenses import OtherExpensesCalculator

def update_comprehensive_proforma_for_equipment_expenses(proforma_results, annual_equipment_expenses):
    """
    Update equipment expenses in comprehensive proforma results to handle leased equipment.
    
    Args:
        proforma_results: The results dictionary being built in the comprehensive proforma
        annual_equipment_expenses: Annual equipment expenses from the equipment calculator
        
    Returns:
        Updated proforma_results with proper lease handling
    """
    # Ensure the equipment expenses structure has a 'lease' category
    if 'expenses' in proforma_results and 'equipment' in proforma_results['expenses']:
        equipment_expenses = proforma_results['expenses']['equipment']
        
        # Add lease category if it doesn't exist
        if 'lease' not in equipment_expenses:
            years = proforma_results['years']
            equipment_expenses['lease'] = {year: 0 for year in years}
    
    # Extract lease expenses from annual equipment expenses
    if 'LeaseExpense' in annual_equipment_expenses.columns:
        lease_by_year = annual_equipment_expenses.groupby('Year')['LeaseExpense'].sum()
        
        # Update the lease expenses in the results
        for year, amount in lease_by_year.items():
            if year in proforma_results['expenses']['equipment']['lease']:
                proforma_results['expenses']['equipment']['lease'][year] = amount
    
    # Recalculate total equipment expenses for each year
    for year in proforma_results['years']:
        proforma_results['expenses']['equipment']['total'][year] = (
            proforma_results['expenses']['equipment']['depreciation'].get(year, 0) +
            proforma_results['expenses']['equipment']['lease'].get(year, 0) +
            proforma_results['expenses']['equipment']['service'].get(year, 0) +
            proforma_results['expenses']['equipment']['accreditation'].get(year, 0) +
            proforma_results['expenses']['equipment']['insurance'].get(year, 0)
        )
        
        # Update the total expenses for this year
        proforma_results['expenses']['total'][year] = (
            proforma_results['expenses']['equipment']['total'][year] +
            proforma_results['expenses']['personnel'].get(year, 0) +
            proforma_results['expenses']['other'].get(year, 0)
        )
        
        # Update net income
        proforma_results['net_income'][year] = (
            proforma_results['revenue'].get(year, 0) - 
            proforma_results['expenses']['total'][year]
        )
    
    # Recalculate cumulative net income
    cumulative = 0
    for year in sorted(proforma_results['years']):
        cumulative += proforma_results['net_income'][year]
        proforma_results['cumulative_net_income'][year] = cumulative
    
    return proforma_results

class ComprehensiveProformaCalculator:
    """
    A class to calculate a comprehensive financial proforma integrating personnel,
    exam revenue, equipment expenses, and other expenses/revenue.
    """
    
    def __init__(self, 
                personnel_data: pd.DataFrame = None, 
                exams_data: pd.DataFrame = None, 
                revenue_data: pd.DataFrame = None, 
                equipment_data: pd.DataFrame = None,
                other_data: pd.DataFrame = None,
                personnel_file: str = None,
                exams_file: str = None,
                revenue_file: str = None,
                equipment_file: str = None,
                other_file: str = None,
                days_between_travel: int = 5,
                miles_per_travel: int = 20,
                start_date: str = "01/01/2025",
                population_growth_rates: List[float] = None):
        """
        Initialize the calculator with necessary data.

        Args:
            personnel_data: DataFrame containing personnel data
            exams_data: DataFrame containing exam data
            revenue_data: DataFrame containing revenue source data
            equipment_data: DataFrame containing equipment data
            other_data: DataFrame containing other expense/revenue data
            personnel_file: Path to a CSV file containing personnel data
            exams_file: Path to a CSV file containing exam data
            revenue_file: Path to a CSV file containing revenue source data
            equipment_file: Path to a CSV file containing equipment data
            other_file: Path to a CSV file containing other expense/revenue data
            days_between_travel: Number of days between travel events (default: 5)
            miles_per_travel: Number of miles traveled in each travel event (default: 20)
            start_date: Start date in format 'MM/DD/YYYY' used by exam calculator (default: "01/01/2025")
            population_growth_rates: List of growth rates for PctPopulationReached by year
        """
        # Save travel parameters
        self.days_between_travel = days_between_travel
        self.miles_per_travel = miles_per_travel
        self.start_date = start_date
        self.population_growth_rates = population_growth_rates
        
        # Initialize financial model calculators
        self.personnel_calculator = PersonnelExpenseCalculator()
        self.exam_calculator = ExamRevenueCalculator(start_date=start_date, population_growth_rates=population_growth_rates)
        self.equipment_calculator = EquipmentExpenseCalculator(days_between_travel=days_between_travel, miles_per_travel=miles_per_travel)
        self.other_calculator = OtherExpensesCalculator()
        
        # Load data if provided
        self.load_data(
            personnel_data=personnel_data,
            exams_data=exams_data,
            revenue_data=revenue_data,
            equipment_data=equipment_data,
            other_data=other_data,
            personnel_file=personnel_file,
            exams_file=exams_file,
            revenue_file=revenue_file,
            equipment_file=equipment_file,
            other_file=other_file,
            start_date=start_date,
            population_growth_rates=population_growth_rates
        )
    
    def load_data(self, 
                personnel_data: pd.DataFrame = None, 
                exams_data: pd.DataFrame = None, 
                revenue_data: pd.DataFrame = None, 
                equipment_data: pd.DataFrame = None,
                other_data: pd.DataFrame = None,
                personnel_file: str = None,
                exams_file: str = None,
                revenue_file: str = None,
                equipment_file: str = None,
                other_file: str = None,
                days_between_travel: int = None,
                miles_per_travel: int = None,
                start_date: str = None,
                population_growth_rates: List[float] = None):
        """
        Load data from DataFrames or CSV files.
        
        Args:
            personnel_data: DataFrame containing personnel data
            exams_data: DataFrame containing exam data
            revenue_data: DataFrame containing revenue source data
            equipment_data: DataFrame containing equipment data
            other_data: DataFrame containing other expense/revenue data
            personnel_file: Path to a CSV file containing personnel data
            exams_file: Path to a CSV file containing exam data
            revenue_file: Path to a CSV file containing revenue source data
            equipment_file: Path to a CSV file containing equipment data
            other_file: Path to a CSV file containing other expense/revenue data
            days_between_travel: Number of days between travel events
            miles_per_travel: Number of miles traveled in each travel event
            start_date: Start date in format 'MM/DD/YYYY' used by exam calculator
            population_growth_rates: List of growth rates for PctPopulationReached by year
        """
        # Update travel parameters if provided
        if days_between_travel is not None:
            self.days_between_travel = days_between_travel
        
        if miles_per_travel is not None:
            self.miles_per_travel = miles_per_travel
            
        if population_growth_rates is not None:
            self.population_growth_rates = population_growth_rates
        
        # Load personnel data
        if personnel_data is not None:
            self.personnel_calculator.load_data(personnel_data=personnel_data)
        elif personnel_file is not None:
            self.personnel_calculator.load_data(personnel_file=personnel_file)
            
        # Load exam and revenue data
        if exams_data is not None and revenue_data is not None:
            self.exam_calculator.load_data(
                exams_data=exams_data, 
                revenue_data=revenue_data,
                personnel_data=personnel_data if personnel_data is not None else None,
                equipment_data=equipment_data if equipment_data is not None else None,
                start_date=start_date,
                population_growth_rates=population_growth_rates
            )
        elif exams_file is not None and revenue_file is not None:
            self.exam_calculator.load_data(
                exams_file=exams_file, 
                revenue_file=revenue_file,
                personnel_file=personnel_file if personnel_file is not None else None,
                equipment_file=equipment_file if equipment_file is not None else None,
                start_date=start_date,
                population_growth_rates=population_growth_rates
            )
            
        # Load equipment data
        if equipment_data is not None:
            self.equipment_calculator.load_data(
                equipment_data=equipment_data,
                days_between_travel=self.days_between_travel,
                miles_per_travel=self.miles_per_travel
            )
        elif equipment_file is not None:
            self.equipment_calculator.load_data(
                equipment_file=equipment_file,
                days_between_travel=self.days_between_travel,
                miles_per_travel=self.miles_per_travel
            )
            
        # Load other expense/revenue data
        if other_data is not None:
            self.other_calculator.load_data(other_data=other_data)
        elif other_file is not None:
            self.other_calculator.load_data(other_file=other_file)
            
        return self
    
    def calculate_comprehensive_proforma(self, 
                                        start_date: str, 
                                        end_date: str, 
                                        revenue_sources: List[str] = None,
                                        work_days_per_year: int = 250,
                                        days_between_travel: int = None,
                                        miles_per_travel: int = None,
                                        population_growth_rates: List[float] = None) -> Dict:
        """
        Calculate a comprehensive financial proforma.
        
        Args:
            start_date: Start date in format 'MM/DD/YYYY'
            end_date: End date in format 'MM/DD/YYYY'
            revenue_sources: List of revenue source names to include
            work_days_per_year: Number of working days per year
            days_between_travel: Number of days between travel events
            miles_per_travel: Number of miles traveled in each travel event
            population_growth_rates: List of growth rates for PctPopulationReached by year
            
        Returns:
            Dictionary containing all financial results
        """
        # Update travel parameters if provided
        if days_between_travel is not None:
            self.days_between_travel = days_between_travel
            self.equipment_calculator.days_between_travel = days_between_travel
        
        if miles_per_travel is not None:
            self.miles_per_travel = miles_per_travel
            self.equipment_calculator.miles_per_travel = miles_per_travel
            
        # Update population growth rates if provided
        if population_growth_rates is not None:
            self.population_growth_rates = population_growth_rates
            self.exam_calculator.population_growth_rates = population_growth_rates
            
        # Also update start_date in the exam_calculator
        self.exam_calculator.start_date = start_date
            
        # Convert date strings to datetime
        start_dt = pd.to_datetime(start_date, format='%m/%d/%Y')
        end_dt = pd.to_datetime(end_date, format='%m/%d/%Y')
        
        # Extract years for exam revenue calculations
        start_year = start_dt.year
        end_year = end_dt.year
        
        # Calculate personnel expenses
        personnel_results = self._calculate_personnel_expenses(start_date, end_date)
        
        # Calculate exam revenue
        exam_results = self._calculate_exam_revenue(start_year, end_year, revenue_sources, work_days_per_year)
        
        # Calculate equipment expenses
        equipment_results = self._calculate_equipment_expenses(start_date, end_date)

    
        if equipment_results and 'annual' in equipment_results:
            results = update_comprehensive_proforma_for_equipment_expenses(
                results, equipment_results['annual'])
            # Calculate other expenses and revenue
        other_results = self._calculate_other_expenses(start_date, end_date)
        
        # Integrate all results
        integrated_results = self._integrate_results(
            personnel_results, 
            exam_results, 
            equipment_results, 
            other_results
        )
        
        return integrated_results
    
    def _calculate_personnel_expenses(self, start_date: str, end_date: str) -> Dict:
        """Calculate personnel expenses for the proforma."""
        annual_expenses = self.personnel_calculator.calculate_annual_expense(start_date, end_date)
        monthly_expenses = self.personnel_calculator.calculate_monthly_expense(start_date, end_date)
        category_expenses = self.personnel_calculator.calculate_total_by_category(start_date, end_date)
        grand_total = self.personnel_calculator.calculate_grand_total(start_date, end_date)
        headcount = self.personnel_calculator.get_headcount_by_month(start_date, end_date)
        
        return {
            'annual': annual_expenses,
            'monthly': monthly_expenses,
            'by_category': category_expenses,
            'headcount': headcount,
            'grand_total': grand_total
        }
    
    def _calculate_exam_revenue(self, 
                              start_year: int, 
                              end_year: int, 
                              revenue_sources: List[str] = None,
                              work_days_per_year: int = 250) -> pd.DataFrame:
        """Calculate exam revenue for the proforma."""
        return self.exam_calculator.calculate_multi_year_exam_revenue(
            start_year=start_year,
            end_year=end_year,
            revenue_sources=revenue_sources,
            work_days_per_year=work_days_per_year
        )
    
    # def _calculate_equipment_expenses(self, start_date: str, end_date: str) -> Dict:
    #     """Calculate equipment expenses for the proforma."""
    #     annual_expenses = self.equipment_calculator.calculate_annual_expenses(start_date, end_date)
    #     total_by_equipment = self.equipment_calculator.calculate_total_by_equipment(start_date, end_date)
    #     grand_total = self.equipment_calculator.calculate_grand_total(start_date, end_date)
        
    #     return {
    #         'annual': annual_expenses,
    #         'by_category': total_by_equipment,
    #         'total': grand_total,
    #         'monthly': self._convert_equipment_annual_to_monthly(annual_expenses)
    #     }
    
    def _calculate_equipment_expenses(self, start_date: str, end_date: str) -> Dict:
        """Calculate equipment expenses for the proforma."""
        annual_expenses = self.equipment_calculator.calculate_annual_expenses(start_date, end_date)
        total_by_equipment = self.equipment_calculator.calculate_total_by_equipment(start_date, end_date)
        grand_total = self.equipment_calculator.calculate_grand_total(start_date, end_date)
        
        results = {
            'annual': annual_expenses,
            'by_category': total_by_equipment,
            'total': grand_total,
            'monthly': self._convert_equipment_annual_to_monthly(annual_expenses)
        }
        
        return results

    
    
    def _convert_equipment_annual_to_monthly(self, annual_expenses: pd.DataFrame) -> pd.DataFrame:
        """
        Convert annual equipment expenses to monthly.
        This is a simplified approach that distributes annual values evenly across months.
        
        Returns:
            DataFrame with monthly equipment data
        """
        if annual_expenses.empty:
            return pd.DataFrame()
        
        monthly_data = []
        
        for _, row in annual_expenses.iterrows():
            year = row['Year'] if 'Year' in row else row.name
            
            # For each year, create 12 monthly entries
            for month in range(1, 13):
                monthly_row = {
                    'Year': year,
                    'Month': month,
                    'Equipment': row['Title'] if 'Title' in row else 'Unknown',
                    'Monthly_Cost': row['TotalAnnualExpense'] / 12 if 'TotalAnnualExpense' in row else 0,
                }
                monthly_data.append(monthly_row)
        
        return pd.DataFrame(monthly_data)
    
    def _calculate_other_expenses(self, start_date: str, end_date: str) -> Dict:
        """Calculate other expenses and revenue for the proforma."""
        annual_items = self.other_calculator.calculate_annual_items(start_date, end_date)
        category_items = self.other_calculator.calculate_by_category(start_date, end_date)
        expense_total = self.other_calculator.calculate_expense_total(start_date, end_date)
        revenue_total = self.other_calculator.calculate_revenue_total(start_date, end_date)
        net_total = self.other_calculator.calculate_net_total(start_date, end_date)
        summary = self.other_calculator.calculate_summary(start_date, end_date)
        
        return {
            'annual': annual_items,
            'by_category': category_items,
            'expense_total': expense_total,
            'revenue_total': revenue_total,
            'net_total': net_total,
            'summary': summary
        }
    

    def _integrate_results(self, 
                         personnel_results: Dict,
                         exam_results: pd.DataFrame,
                         equipment_results: Dict,
                         other_results: Dict) -> Dict:
        """
        Integrate results from all financial models into a comprehensive proforma.
        
        Returns:
            Dictionary containing integrated results
        """
        # Create annual summary with all revenue and expense categories
        annual_summary = self._create_annual_summary(
            personnel_results, 
            exam_results, 
            equipment_results, 
            other_results
        )
        
        # Create monthly cash flow projection
        monthly_cash_flow = self._create_monthly_cash_flow(
            personnel_results, 
            exam_results, 
            equipment_results, 
            other_results
        )
        
        # Create integrated financial metrics
        financial_metrics = self._calculate_financial_metrics(annual_summary)
        
        # Return complete integrated results
        return {
            'annual_summary': annual_summary,
            'monthly_cash_flow': monthly_cash_flow,
            'financial_metrics': financial_metrics,
            'personnel_results': personnel_results,
            'exam_results': exam_results,
            'equipment_results': equipment_results,
            'other_results': other_results
        }
    
    def _create_annual_summary(self,
                             personnel_results: Dict,
                             exam_results: pd.DataFrame,
                             equipment_results: Dict,
                             other_results: Dict) -> pd.DataFrame:
        """
        Create an annual summary table with all revenue and expense categories.
        
        Returns:
            DataFrame with annual financial summary
        """
        # Get years range from the data
        years = []
        
        # Add years from personnel data
        if not personnel_results['annual'].empty:
            years.extend(personnel_results['annual']['Year'].unique())
        
        # Add years from exam revenue data
        if not exam_results.empty:
            years.extend(exam_results['Year'].unique())
        
        # Add years from equipment data
        if not equipment_results['annual'].empty:
            if 'Year' in equipment_results['annual'].columns:
                years.extend(equipment_results['annual']['Year'].unique())
        
        # Add years from other expenses/revenue data
        if not other_results['annual'].empty and 'Year' in other_results['annual'].columns:
            years.extend(other_results['annual']['Year'].unique())
        
        # Get unique sorted years
        years = sorted(set(years))
        
        if not years:
            return pd.DataFrame()  # No data available
        
        # Create a dataframe with all years
        summary_data = []
        
        for year in years:
            row = {'Year': year}
            
            # Add exam revenue
            if not exam_results.empty:
                year_exam_revenue = exam_results[exam_results['Year'] == year]['Total_Revenue'].sum()
                row['Exam_Revenue'] = year_exam_revenue
            else:
                row['Exam_Revenue'] = 0
            
            # Add other revenue
            if not other_results['annual'].empty and 'Year' in other_results['annual'].columns:
                # Check which column name is used for expense flag
                expense_col = 'IsExpense' if 'IsExpense' in other_results['annual'].columns else 'Expense'
                
                year_other_revenue = other_results['annual'][
                    (other_results['annual']['Year'] == year) & 
                    (other_results['annual'][expense_col] == False)
                ]['Amount'].sum()
                row['Other_Revenue'] = year_other_revenue
            else:
                row['Other_Revenue'] = 0
            
            # Calculate total revenue
            row['Total_Revenue'] = row['Exam_Revenue'] + row['Other_Revenue']
            
            # Add personnel expenses
            if not personnel_results['annual'].empty:
                year_personnel = personnel_results['annual'][
                    personnel_results['annual']['Year'] == year
                ]['Total_Expense'].sum()
                row['Personnel_Expenses'] = year_personnel
            else:
                row['Personnel_Expenses'] = 0
            
                # Add equipment expenses - now handling both lease and depreciation
            if not equipment_results['annual'].empty:
                if 'Year' in equipment_results['annual'].columns:
                    year_equipment_data = equipment_results['annual'][
                        equipment_results['annual']['Year'] == year
                    ]
                    
                    # Sum all expense types
                    total_equipment_expense = year_equipment_data['TotalAnnualExpense'].sum()
                    
                    # Also track lease vs depreciation amounts separately for better reporting
                    lease_expense = 0
                    if 'LeaseExpense' in year_equipment_data.columns:
                        lease_expense = year_equipment_data['LeaseExpense'].sum()
                    
                    depreciation_expense = 0
                    if 'AnnualDepreciation' in year_equipment_data.columns:
                        depreciation_expense = year_equipment_data['AnnualDepreciation'].sum()
                    
                    # Add all values to the row
                    row['Equipment_Expenses'] = total_equipment_expense
                    row['Equipment_Lease_Expenses'] = lease_expense  # New field
                    row['Equipment_Depreciation_Expenses'] = depreciation_expense  # New field
                else:
                    # If 'Year' is not in columns, it might be a different structure
                    row['Equipment_Expenses'] = 0
                    row['Equipment_Lease_Expenses'] = 0
                    row['Equipment_Depreciation_Expenses'] = 0
            else:
                row['Equipment_Expenses'] = 0
                row['Equipment_Lease_Expenses'] = 0
                row['Equipment_Depreciation_Expenses'] = 0
            
            # Add exam direct expenses
            if not exam_results.empty:
                year_exam_expenses = exam_results[
                    exam_results['Year'] == year
                ]['Total_Direct_Expenses'].sum()
                row['Exam_Direct_Expenses'] = year_exam_expenses
            else:
                row['Exam_Direct_Expenses'] = 0
            
            # Add other expenses
            if not other_results['annual'].empty and 'Year' in other_results['annual'].columns:
                # Check which column name is used for expense flag
                expense_col = 'IsExpense' if 'IsExpense' in other_results['annual'].columns else 'Expense'
                
                year_other_expenses = other_results['annual'][
                    (other_results['annual']['Year'] == year) & 
                    (other_results['annual'][expense_col] == True)
                ]['Amount'].sum()
                row['Other_Expenses'] = year_other_expenses
            else:
                row['Other_Expenses'] = 0
            
            # Calculate total expenses
            row['Total_Expenses'] = (
                row['Personnel_Expenses'] + 
                row['Equipment_Expenses'] + 
                row['Exam_Direct_Expenses'] + 
                row['Other_Expenses']
            )
            
            # Calculate net income
            row['Net_Income'] = row['Total_Revenue'] - row['Total_Expenses']
            
            summary_data.append(row)
        
        return pd.DataFrame(summary_data)
    
    def _create_monthly_cash_flow(self,
                                personnel_results: Dict,
                                exam_results: pd.DataFrame,
                                equipment_results: Dict,
                                other_results: Dict) -> pd.DataFrame:
        """
        Create a monthly cash flow projection.
        
        Returns:
            DataFrame with monthly cash flow projection
        """
        # First, create a set of all year-month combinations from our data
        all_months = set()
        
        # Add months from personnel data
        if 'monthly' in personnel_results and not personnel_results['monthly'].empty:
            for _, row in personnel_results['monthly'].iterrows():
                all_months.add((row['Year'], row['Month']))
        
        # Add months from equipment data
        if 'monthly' in equipment_results and not equipment_results['monthly'].empty:
            for _, row in equipment_results['monthly'].iterrows():
                all_months.add((row['Year'], row['Month']))
        
        # Convert exam annual data to monthly (simplified approach)
        exam_monthly = self._convert_exam_annual_to_monthly(exam_results)
        
        # Add months from exam data
        if not exam_monthly.empty:
            for _, row in exam_monthly.iterrows():
                all_months.add((row['Year'], row['Month']))
        
        # Add months from other expenses/revenue
        if not other_results['annual'].empty and 'Year' in other_results['annual'].columns and 'Month' in other_results['annual'].columns:
            for _, row in other_results['annual'].iterrows():
                # Get year and month from the row if available
                if 'Year' in row and 'Month' in row:
                    all_months.add((row['Year'], row['Month']))
                elif 'Year' in row:
                    # If only year is available, add all months for that year
                    for month in range(1, 13):
                        all_months.add((row['Year'], month))
        
        # Sort all months chronologically
        all_months = sorted(all_months)
        
        if not all_months:
            return pd.DataFrame()  # No data available
        
        # Create monthly cash flow dataframe
        monthly_data = []
        
        for year, month in all_months:
            row = {
                'Year': year,
                'Month': month,
                'Date': f"{year}-{month:02d}-01"
            }
            
            # Add exam revenue (from our monthly conversion)
            if not exam_monthly.empty:
                month_exam_revenue = exam_monthly[
                    (exam_monthly['Year'] == year) & 
                    (exam_monthly['Month'] == month)
                ]['Monthly_Revenue'].sum()
                row['Exam_Revenue'] = month_exam_revenue
            else:
                row['Exam_Revenue'] = 0
            
            # Add other revenue (simplified - dividing annual by 12)
            if not other_results['annual'].empty and 'Year' in other_results['annual'].columns:
                # Check which column name is used for expense flag
                expense_col = 'IsExpense' if 'IsExpense' in other_results['annual'].columns else 'Expense'
                
                # Filter by year first
                year_data = other_results['annual'][other_results['annual']['Year'] == year]
                
                if not year_data.empty:
                    # Get revenue items
                    revenue_items = year_data[year_data[expense_col] == False]
                    
                    # If we have month information, filter by month
                    if 'Month' in year_data.columns:
                        month_revenue = revenue_items[revenue_items['Month'] == month]['Amount'].sum()
                        row['Other_Revenue'] = month_revenue
                    else:
                        # Otherwise, distribute evenly across months
                        year_revenue = revenue_items['Amount'].sum()
                        row['Other_Revenue'] = year_revenue / 12
                else:
                    row['Other_Revenue'] = 0
            else:
                row['Other_Revenue'] = 0
            
            # Calculate total monthly revenue
            row['Total_Revenue'] = row['Exam_Revenue'] + row['Other_Revenue']
            
            # Add personnel expenses
            if 'monthly' in personnel_results and not personnel_results['monthly'].empty:
                month_personnel = personnel_results['monthly'][
                    (personnel_results['monthly']['Year'] == year) & 
                    (personnel_results['monthly']['Month'] == month)
                ]['Total_Expense'].sum()
                row['Personnel_Expenses'] = month_personnel
            else:
                row['Personnel_Expenses'] = 0
            
            # Add equipment expenses
            if 'monthly' in equipment_results and not equipment_results['monthly'].empty:
                month_equipment = equipment_results['monthly'][
                    (equipment_results['monthly']['Year'] == year) & 
                    (equipment_results['monthly']['Month'] == month)
                ]['Monthly_Cost'].sum()
                row['Equipment_Expenses'] = month_equipment
            else:
                row['Equipment_Expenses'] = 0
            
            # Add exam direct expenses (from our monthly conversion)
            if not exam_monthly.empty:
                month_exam_expenses = exam_monthly[
                    (exam_monthly['Year'] == year) & 
                    (exam_monthly['Month'] == month)
                ]['Monthly_Expenses'].sum()
                row['Exam_Direct_Expenses'] = month_exam_expenses
            else:
                row['Exam_Direct_Expenses'] = 0
            
            # Add other expenses (handling monthly data if available)
            if not other_results['annual'].empty and 'Year' in other_results['annual'].columns:
                # Check which column name is used for expense flag
                expense_col = 'IsExpense' if 'IsExpense' in other_results['annual'].columns else 'Expense'
                
                # Filter by year first
                year_data = other_results['annual'][other_results['annual']['Year'] == year]
                
                if not year_data.empty:
                    # Get expense items
                    expense_items = year_data[year_data[expense_col] == True]
                    
                    # If we have month information, filter by month
                    if 'Month' in year_data.columns:
                        month_expenses = expense_items[expense_items['Month'] == month]['Amount'].sum()
                        row['Other_Expenses'] = month_expenses
                    else:
                        # Otherwise, distribute evenly across months
                        year_expenses = expense_items['Amount'].sum()
                        row['Other_Expenses'] = year_expenses / 12
                else:
                    row['Other_Expenses'] = 0
            else:
                row['Other_Expenses'] = 0
            
            # Calculate total monthly expenses
            row['Total_Expenses'] = (
                row['Personnel_Expenses'] + 
                row['Equipment_Expenses'] + 
                row['Exam_Direct_Expenses'] + 
                row['Other_Expenses']
            )
            
            # Calculate monthly net income
            row['Net_Income'] = row['Total_Revenue'] - row['Total_Expenses']
            
            monthly_data.append(row)
        
        # Convert to DataFrame and ensure date column is datetime
        monthly_df = pd.DataFrame(monthly_data)
        if not monthly_df.empty:
            monthly_df['Date'] = pd.to_datetime(monthly_df['Date'])
        
        return monthly_df
    
    def _convert_exam_annual_to_monthly(self, exam_results: pd.DataFrame) -> pd.DataFrame:
        """
        Convert annual exam data to monthly estimates.
        This is a simplified approach that distributes annual values evenly across months.
        
        Returns:
            DataFrame with monthly exam data
        """
        if exam_results.empty:
            return pd.DataFrame()
        
        monthly_data = []
        
        for _, row in exam_results.iterrows():
            year = row['Year']
            
            # For each year, create 12 monthly entries
            for month in range(1, 13):
                monthly_row = {
                    'Year': year,
                    'Month': month,
                    'Exam': row['Exam'],
                    'RevenueSource': row['RevenueSource'],
                    'Monthly_Volume': row['AnnualVolume'] / 12,  # Simple monthly allocation
                    'Monthly_Revenue': row['Total_Revenue'] / 12,
                    'Monthly_Expenses': row['Total_Direct_Expenses'] / 12,
                    'Monthly_Net': row['Net_Revenue'] / 12
                }
                monthly_data.append(monthly_row)
        
        return pd.DataFrame(monthly_data)
    
    def _calculate_financial_metrics(self, annual_summary: pd.DataFrame) -> Dict:
        """
        Calculate financial metrics based on the annual summary.
        
        Returns:
            Dictionary with key financial metrics
        """
        if annual_summary.empty:
            return {
                'total_revenue': 0,
                'total_expenses': 0,
                'total_net_income': 0,
                'average_annual_revenue': 0,
                'average_annual_expenses': 0,
                'average_annual_net_income': 0,
                'revenue_expense_ratio': 0,
                'breakeven_year': None
            }
        
        # Calculate overall totals
        total_revenue = annual_summary['Total_Revenue'].sum()
        total_expenses = annual_summary['Total_Expenses'].sum()
        total_net_income = annual_summary['Net_Income'].sum()
        
        # Calculate averages
        num_years = len(annual_summary)
        avg_annual_revenue = total_revenue / num_years
        avg_annual_expenses = total_expenses / num_years
        avg_annual_net_income = total_net_income / num_years
        
        # Calculate revenue to expense ratio
        revenue_expense_ratio = total_revenue / total_expenses if total_expenses > 0 else 0
        
        # Determine breakeven year (first year with positive cumulative net income)
        annual_summary = annual_summary.sort_values('Year')
        annual_summary['Cumulative_Net_Income'] = annual_summary['Net_Income'].cumsum()
        breakeven_years = annual_summary[annual_summary['Cumulative_Net_Income'] > 0]['Year'].tolist()
        breakeven_year = breakeven_years[0] if breakeven_years else None
        
        return {
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'total_net_income': total_net_income,
            'average_annual_revenue': avg_annual_revenue,
            'average_annual_expenses': avg_annual_expenses,
            'average_annual_net_income': avg_annual_net_income,
            'revenue_expense_ratio': revenue_expense_ratio,
            'breakeven_year': breakeven_year
        }
    
    def generate_visualization(self, annual_summary: pd.DataFrame, metric: str = 'net_income'):
        """
        Generate visualization based on the annual summary.
        
        Args:
            annual_summary: DataFrame with annual summary data
            metric: Type of visualization to generate ('net_income', 'revenue_expense', 'cash_flow')
            
        Returns:
            Matplotlib figure
        """
        if annual_summary.empty:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "No data available for visualization", 
                   horizontalalignment='center', verticalalignment='center')
            return fig
        
        if metric == 'net_income':
            # Net Income by Year
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.bar(annual_summary['Year'], annual_summary['Net_Income'], color='green')
            ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            ax.set_title('Net Income by Year')
            ax.set_xlabel('Year')
            ax.set_ylabel('Amount ($)')
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Add data labels
            for i, v in enumerate(annual_summary['Net_Income']):
                label_color = 'black' if v > 0 else 'white'
                ax.text(annual_summary['Year'].iloc[i], v, f"${v:,.0f}", 
                       ha='center', va='bottom' if v > 0 else 'top', color=label_color)
            
        elif metric == 'revenue_expense':
            # Revenue vs Expenses by Year
            fig, ax = plt.subplots(figsize=(12, 6))
            width = 0.35
            x = np.arange(len(annual_summary))
            
            ax.bar(x - width/2, annual_summary['Total_Revenue'], width, label='Revenue', color='blue')
            ax.bar(x + width/2, annual_summary['Total_Expenses'], width, label='Expenses', color='red')
            
            ax.set_title('Revenue vs Expenses by Year')
            ax.set_xlabel('Year')
            ax.set_ylabel('Amount ($)')
            ax.set_xticks(x)
            ax.set_xticklabels(annual_summary['Year'])
            ax.legend()
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            
        elif metric == 'cash_flow':
            # Cumulative Cash Flow
            fig, ax = plt.subplots(figsize=(12, 6))
            annual_summary['Cumulative_Net_Income'] = annual_summary['Net_Income'].cumsum()
            
            ax.plot(annual_summary['Year'], annual_summary['Cumulative_Net_Income'], 
                   marker='o', linestyle='-', color='purple', linewidth=2)
            ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            ax.set_title('Cumulative Cash Flow')
            ax.set_xlabel('Year')
            ax.set_ylabel('Cumulative Net Income ($)')
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Add data labels
            for i, v in enumerate(annual_summary['Cumulative_Net_Income']):
                ax.text(annual_summary['Year'].iloc[i], v, f"${v:,.0f}", 
                       ha='center', va='bottom' if v > 0 else 'top')
        
        else:
            # Default to revenue breakdown
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Create stacked bar for revenue components
            revenue_cols = ['Exam_Revenue', 'Other_Revenue']
            annual_summary[revenue_cols].plot(kind='bar', stacked=True, ax=ax, colormap='Blues')
            
            ax.set_title('Revenue Breakdown by Year')
            ax.set_xlabel('Year')
            ax.set_ylabel('Amount ($)')
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            ax.set_xticklabels(annual_summary['Year'])
            
        return fig


def calculate_comprehensive_proforma(
    personnel_data: pd.DataFrame,
    exams_data: pd.DataFrame,
    revenue_data: pd.DataFrame,
    equipment_data: pd.DataFrame,
    other_data: pd.DataFrame,
    start_date: str,
    end_date: str,
    revenue_sources: List[str] = None,
    work_days_per_year: int = 250,
    days_between_travel: int = 5,
    miles_per_travel: int = 20,
    population_growth_rates: List[float] = None
) -> Dict:
    """
    Utility function to calculate a comprehensive proforma without having to manually instantiate the class.
    
    Args:
        personnel_data: DataFrame containing personnel data
        exams_data: DataFrame containing exam data
        revenue_data: DataFrame containing revenue source data
        equipment_data: DataFrame containing equipment data
        other_data: DataFrame containing other expense/revenue data
        start_date: Start date in format 'MM/DD/YYYY'
        end_date: End date in format 'MM/DD/YYYY'
        revenue_sources: List of revenue source names to include
        work_days_per_year: Number of working days per year
        days_between_travel: Number of days between travel events (default: 5)
        miles_per_travel: Number of miles traveled in each travel event (default: 20)
        population_growth_rates: List of growth rates for PctPopulationReached by year
        
    Returns:
        Dictionary containing all financial results
    """
    calculator = ComprehensiveProformaCalculator(
        personnel_data=personnel_data,
        exams_data=exams_data,
        revenue_data=revenue_data,
        equipment_data=equipment_data,
        other_data=other_data,
        days_between_travel=days_between_travel,
        miles_per_travel=miles_per_travel,
        start_date=start_date,
        population_growth_rates=population_growth_rates
    )
    
    return calculator.calculate_comprehensive_proforma(
        start_date=start_date,
        end_date=end_date,
        revenue_sources=revenue_sources,
        work_days_per_year=work_days_per_year,
        population_growth_rates=population_growth_rates
    ) 


def get_exam_calculator_from_proforma_params(
    personnel_data: pd.DataFrame,
    exams_data: pd.DataFrame,
    revenue_data: pd.DataFrame,
    equipment_data: pd.DataFrame,
    start_date: str,
    population_growth_rates: List[float] = None
) -> ExamRevenueCalculator:
    """
    Creates an ExamRevenueCalculator with the same parameters as used in the comprehensive proforma.
    This ensures consistency between the comprehensive proforma and volume limiting factors analyses.
    
    Args:
        personnel_data: DataFrame containing personnel data
        exams_data: DataFrame containing exam data
        revenue_data: DataFrame containing revenue source data
        equipment_data: DataFrame containing equipment data
        start_date: Start date in format 'MM/DD/YYYY'
        population_growth_rates: List of growth rates for PctPopulationReached by year
        
    Returns:
        An initialized ExamRevenueCalculator
    """
    return ExamRevenueCalculator(
        personnel_data=personnel_data,
        exams_data=exams_data,
        revenue_data=revenue_data,
        equipment_data=equipment_data,
        start_date=start_date,
        population_growth_rates=population_growth_rates
    ) 