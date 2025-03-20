"""
Example usage of the ExamRevenueCalculator module.

This module demonstrates how to use the ExamRevenueCalculator class to calculate 
exam volumes, revenue, and expenses based on demographic factors, staffing, 
equipment, and revenue sources.
"""

import pandas as pd
import matplotlib.pyplot as plt
import os
from financeModels.exam_revenue import ExamRevenueCalculator, calculate_exam_revenue

def demonstrate_exam_revenue_calculator():
    """
    Example of using the ExamRevenueCalculator class directly.
    """
    print("Demonstrating ExamRevenueCalculator...")
    
    # Load data from CSV files
    exams_file = 'Exams.csv'
    revenue_file = 'Revenue.csv'
    personnel_file = 'Personnel.csv'
    equipment_file = 'Equipment.csv'
    
    # Initialize the calculator
    calculator = ExamRevenueCalculator(
        exams_file=exams_file,
        revenue_file=revenue_file,
        personnel_file=personnel_file,
        equipment_file=equipment_file
    )
    
    # Example 1: Calculate maximum reachable volume for each exam from FQHC revenue source
    print("\n1. Maximum Reachable Volume for FQHC:")
    max_volumes = calculator.calculate_max_reachable_volume('FQHC')
    print(max_volumes[['Exam', 'MaxReachableVolume']].head())
    
    # Example 2: Calculate available equipment on a specific date
    date = '01/01/2026'  # January 1, 2026
    print(f"\n2. Available Equipment on {date}:")
    equipment = calculator.get_available_equipment(date)
    print(equipment['Title'].tolist())
    
    # Example 3: Calculate available staff on a specific date
    print(f"\n3. Available Staff on {date}:")
    staff = calculator.get_available_staff(date)
    print(staff['Title'].head())
    
    # Example 4: Calculate daily exams capacity for FQHC
    print(f"\n4. Daily Exams Capacity for FQHC on {date}:")
    daily_exams = calculator.calculate_exams_per_day(date, 'FQHC')
    print(daily_exams[['Exam', 'TargetExamsPerDay']].head())
    
    # Example 5: Calculate annual exam volume, revenue, and expenses for year 2026
    print("\n5. Annual Exam Volume, Revenue, and Expenses for 2026 (FQHC):")
    annual_results = calculator.calculate_annual_exam_volume(2026, 'FQHC')
    if not annual_results.empty:
        print(annual_results[['Exam', 'AnnualVolume', 'Total_Revenue', 'Total_Direct_Expenses', 'Net_Revenue']].head())
    else:
        print("No exam revenue calculated for 2026 (FQHC) - this may be due to missing equipment or staff.")
    
    # Example 6: Multi-year analysis
    print("\n6. Multi-year Exam Revenue Analysis (2026-2030):")
    multi_year_results = calculator.calculate_multi_year_exam_revenue(2026, 2030)
    if not multi_year_results.empty:
        # Group by year and calculate totals
        yearly_summary = multi_year_results.groupby('Year').agg({
            'AnnualVolume': 'sum',
            'Total_Revenue': 'sum',
            'Total_Direct_Expenses': 'sum',
            'Net_Revenue': 'sum'
        }).reset_index()
        print(yearly_summary)
    else:
        print("No multi-year exam revenue calculated - this may be due to missing equipment or staff.")

def demonstrate_utility_function():
    """
    Example of using the calculate_exam_revenue utility function directly.
    """
    print("\nDemonstrating calculate_exam_revenue utility function...")
    
    # Load data from CSV files
    exams_data = pd.read_csv('Exams.csv', skipinitialspace=True)
    revenue_data = pd.read_csv('Revenue.csv', skipinitialspace=True)
    personnel_data = pd.read_csv('Personnel.csv', skipinitialspace=True)
    equipment_data = pd.read_csv('Equipment.csv', skipinitialspace=True)
    
    # Calculate exam revenue for all revenue sources for 2026-2030
    results = calculate_exam_revenue(
        exams_data=exams_data,
        revenue_data=revenue_data,
        personnel_data=personnel_data,
        equipment_data=equipment_data,
        start_year=2026,
        end_year=2030
    )
    
    if not results.empty:
        # Group by year and calculate totals
        yearly_summary = results.groupby('Year').agg({
            'AnnualVolume': 'sum',
            'Total_Revenue': 'sum',
            'Total_Direct_Expenses': 'sum',
            'Net_Revenue': 'sum'
        }).reset_index()
        print(yearly_summary)
    else:
        print("No exam revenue calculated - this may be due to missing equipment or staff.")

def create_visualizations(calculator):
    """
    Create visualizations of exam revenue data.
    
    Args:
        calculator: An initialized ExamRevenueCalculator instance
    """
    print("\nCreating visualizations...")
    
    # Multi-year analysis for all revenue sources
    multi_year_results = calculator.calculate_multi_year_exam_revenue(2026, 2030)
    
    if multi_year_results.empty:
        print("No data available for visualizations.")
        return
    
    # Create a directory for visualizations if it doesn't exist
    os.makedirs('visualizations', exist_ok=True)
    
    # 1. Total Revenue by Year and Revenue Source
    plt.figure(figsize=(12, 6))
    revenue_by_source = multi_year_results.groupby(['Year', 'RevenueSource'])['Total_Revenue'].sum().unstack()
    revenue_by_source.plot(kind='bar', stacked=True)
    plt.title('Total Revenue by Year and Revenue Source')
    plt.xlabel('Year')
    plt.ylabel('Revenue ($)')
    plt.savefig('visualizations/revenue_by_year_source.png')
    plt.close()
    
    # 2. Total Volume by Year and Exam Type
    plt.figure(figsize=(14, 8))
    volume_by_exam = multi_year_results.groupby(['Year', 'Exam'])['AnnualVolume'].sum().unstack()
    volume_by_exam.plot(kind='bar', stacked=True)
    plt.title('Total Exam Volume by Year and Exam Type')
    plt.xlabel('Year')
    plt.ylabel('Annual Volume')
    plt.savefig('visualizations/volume_by_year_exam.png')
    plt.close()
    
    # 3. Net Revenue by Year
    plt.figure(figsize=(10, 6))
    net_revenue = multi_year_results.groupby('Year')['Net_Revenue'].sum()
    net_revenue.plot(kind='line', marker='o', linewidth=2)
    plt.title('Net Revenue by Year')
    plt.xlabel('Year')
    plt.ylabel('Net Revenue ($)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig('visualizations/net_revenue_by_year.png')
    plt.close()
    
    # 4. Revenue vs Expenses by Year
    plt.figure(figsize=(10, 6))
    financials = multi_year_results.groupby('Year').agg({
        'Total_Revenue': 'sum',
        'Total_Direct_Expenses': 'sum'
    })
    financials.plot(kind='bar')
    plt.title('Revenue vs Direct Expenses by Year')
    plt.xlabel('Year')
    plt.ylabel('Amount ($)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig('visualizations/revenue_vs_expenses.png')
    plt.close()
    
    print("Visualizations saved to 'visualizations' directory.")

if __name__ == "__main__":
    demonstrate_exam_revenue_calculator()
    demonstrate_utility_function()
    
    # Create visualizations with an initialized calculator
    calculator = ExamRevenueCalculator(
        exams_file='Exams.csv',
        revenue_file='Revenue.csv',
        personnel_file='Personnel.csv',
        equipment_file='Equipment.csv'
    )
    create_visualizations(calculator) 