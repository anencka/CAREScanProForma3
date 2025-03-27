"""
Comprehensive ProForma module update to support equipment leasing.

This updates the relevant parts of financeModels/comprehensive_proforma.py to 
correctly handle leased equipment in financial calculations.
"""

def update_comprehensive_proforma_for_equipment_expenses(proforma_results, annual_equipment_expenses):
    """
    Update equipment expenses in comprehensive proforma results to handle leased equipment.
    
    This function should be called from within calculate_comprehensive_proforma after
    calculating equipment expenses but before integrating all results.
    
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

# Modified version of integrate_results that includes lease handling
def _integrate_results_with_leasing(self, 
                         personnel_results: Dict,
                         exam_results: pd.DataFrame,
                         equipment_results: Dict,
                         other_results: Dict) -> Dict:
    """
    Integrate results from all financial models into a comprehensive proforma.
    This version has been updated to handle leased equipment expenses.
    
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

# Modified version of create_annual_summary that includes lease handling
def _create_annual_summary_with_leasing(self,
                              personnel_results: Dict,
                              exam_results: pd.DataFrame,
                              equipment_results: Dict,
                              other_results: Dict) -> pd.DataFrame:
    """
    Create an annual summary table with all revenue and expense categories.
    This version has been updated to handle leased equipment expenses.
    
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
                
                # Sum all expense types (now including LeaseExpense column)
                total_equipment_expense = year_equipment_data['TotalAnnualExpense'].sum()
                
                # For future breakdown analysis, also store the lease vs depreciation amounts
                lease_expense = 0
                if 'LeaseExpense' in year_equipment_data.columns:
                    lease_expense = year_equipment_data['LeaseExpense'].sum()
                
                depreciation_expense = 0
                if 'AnnualDepreciation' in year_equipment_data.columns:
                    depreciation_expense = year_equipment_data['AnnualDepreciation'].sum()
                
                row['Equipment_Expenses'] = total_equipment_expense
                row['Equipment_Lease_Expenses'] = lease_expense
                row['Equipment_Depreciation_Expenses'] = depreciation_expense
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

# Integration instructions for comprehensive_proforma.py:
"""
To integrate these changes into the comprehensive_proforma.py file:

1. Import the update_comprehensive_proforma_for_equipment_expenses function at the top of the file

2. In the calculate_comprehensive_proforma method, after calculating equipment expenses:
   ```python
   # Calculate equipment expenses if available
   equipment_df = AppController.get_dataframe("Equipment")
   if equipment_df is not None and not equipment_df.empty:
       try:
           equipment_results = calculate_equipment_expenses(
               equipment_data=equipment_df,
               start_date=start_date,
               end_date=end_date
           )
           results['equipment_expenses'] = equipment_results
           
           # Add this line to update the results with lease handling
           results = update_comprehensive_proforma_for_equipment_expenses(
               results, equipment_results['annual'])
       except Exception as e:
           st_obj.warning(f"Could not calculate equipment expenses: {str(e)}")
           results['equipment_expenses'] = {}
   else:
       results['equipment_expenses'] = {}
   ```

3. Replace the _integrate_results method with _integrate_results_with_leasing
4. Replace the _create_annual_summary method with _create_annual_summary_with_leasing
"""