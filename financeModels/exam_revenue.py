import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union
import calendar

class ExamRevenueCalculator:
    """
    A class to calculate revenue, volume, and expenses for each type of exam.
    This model calculates the maximum reachable volume, actual volume, revenue, and expenses
    for each exam type based on demographic factors, staffing, equipment, and revenue sources.
    """
    
    def __init__(self, 
                exams_data: pd.DataFrame = None, 
                revenue_data: pd.DataFrame = None, 
                personnel_data: pd.DataFrame = None,
                equipment_data: pd.DataFrame = None,
                exams_file: str = None,
                revenue_file: str = None,
                personnel_file: str = None,
                equipment_file: str = None):
        """
        Initialize the calculator with necessary data.

        Args:
            exams_data: DataFrame containing exam data
            revenue_data: DataFrame containing revenue source data
            personnel_data: DataFrame containing personnel data
            equipment_data: DataFrame containing equipment data
            exams_file: Path to a CSV file containing exam data
            revenue_file: Path to a CSV file containing revenue source data
            personnel_file: Path to a CSV file containing personnel data
            equipment_file: Path to a CSV file containing equipment data
        """
        # Load data from DataFrames if provided, otherwise from files
        self.exams_data = exams_data.copy() if exams_data is not None else None
        self.revenue_data = revenue_data.copy() if revenue_data is not None else None
        self.personnel_data = personnel_data.copy() if personnel_data is not None else None
        self.equipment_data = equipment_data.copy() if equipment_data is not None else None
        
        if exams_file is not None and self.exams_data is None:
            self.exams_data = pd.read_csv(exams_file, skipinitialspace=True)
        if revenue_file is not None and self.revenue_data is None:
            self.revenue_data = pd.read_csv(revenue_file, skipinitialspace=True)
        if personnel_file is not None and self.personnel_data is None:
            self.personnel_data = pd.read_csv(personnel_file, skipinitialspace=True)
        if equipment_file is not None and self.equipment_data is None:
            self.equipment_data = pd.read_csv(equipment_file, skipinitialspace=True)
            
        # Process data if all required datasets are available
        if self._check_data_loaded():
            self._process_data()
    
    def _check_data_loaded(self) -> bool:
        """Check if all required data is loaded."""
        return (self.exams_data is not None and 
                self.revenue_data is not None and 
                self.personnel_data is not None and
                self.equipment_data is not None)
    
    def _process_data(self):
        """Process the data to prepare for calculations."""
        # Process date columns in personnel data
        if 'StartDate' in self.personnel_data.columns:
            self.personnel_data['StartDate'] = pd.to_datetime(
                self.personnel_data['StartDate'], 
                format='%m/%d/%Y', 
                errors='coerce'
            )
        if 'EndDate' in self.personnel_data.columns:
            self.personnel_data['EndDate'] = pd.to_datetime(
                self.personnel_data['EndDate'], 
                format='%m/%d/%Y', 
                errors='coerce'
            )
        
        # Process date columns in equipment data
        if 'PurchaseDate' in self.equipment_data.columns:
            self.equipment_data['PurchaseDate'] = pd.to_datetime(
                self.equipment_data['PurchaseDate'], 
                format='%m/%d/%Y', 
                errors='coerce'
            )
        
        # Convert duration in minutes to hours for exams
        if 'Duration' in self.exams_data.columns:
            self.exams_data['DurationHours'] = self.exams_data['Duration'] / 60.0
        
        # Process semicolon-separated lists
        for df in [self.exams_data, self.revenue_data, self.personnel_data, self.equipment_data]:
            for col in df.columns:
                if df[col].dtype == 'object':  # Only process string columns
                    # Check if any value in the column contains a semicolon
                    if df[col].astype(str).str.contains(';').any():
                        # Convert semicolon-delimited strings to lists
                        df[col] = df[col].astype(str).apply(
                            lambda x: [item.strip() for item in x.split(';')] if ';' in x else x
                        )
    
    def load_data(self, 
                 exams_data: pd.DataFrame = None, 
                 revenue_data: pd.DataFrame = None, 
                 personnel_data: pd.DataFrame = None,
                 equipment_data: pd.DataFrame = None,
                 exams_file: str = None,
                 revenue_file: str = None,
                 personnel_file: str = None,
                 equipment_file: str = None):
        """
        Load data from DataFrames or CSV files.
        
        Args:
            exams_data: DataFrame containing exam data
            revenue_data: DataFrame containing revenue source data
            personnel_data: DataFrame containing personnel data
            equipment_data: DataFrame containing equipment data
            exams_file: Path to a CSV file containing exam data
            revenue_file: Path to a CSV file containing revenue source data
            personnel_file: Path to a CSV file containing personnel data
            equipment_file: Path to a CSV file containing equipment data
        """
        if exams_data is not None:
            self.exams_data = exams_data.copy()
        elif exams_file is not None:
            self.exams_data = pd.read_csv(exams_file, skipinitialspace=True)
        
        if revenue_data is not None:
            self.revenue_data = revenue_data.copy()
        elif revenue_file is not None:
            self.revenue_data = pd.read_csv(revenue_file, skipinitialspace=True)
            
        if personnel_data is not None:
            self.personnel_data = personnel_data.copy()
        elif personnel_file is not None:
            self.personnel_data = pd.read_csv(personnel_file, skipinitialspace=True)
            
        if equipment_data is not None:
            self.equipment_data = equipment_data.copy()
        elif equipment_file is not None:
            self.equipment_data = pd.read_csv(equipment_file, skipinitialspace=True)
        
        if self._check_data_loaded():
            self._process_data()
        
        return self
    
    def calculate_max_reachable_volume(self, revenue_source: str) -> pd.DataFrame:
        """
        Calculate the maximum reachable volume for each exam from a revenue source.
        
        Formula:
        max_volume = (examMaxAge-examMinAge)/(revenueMaxAge-revenueMinAge) * 
                     (revenueTargetPopulation) * (revenuePctPopulationReached) * 
                     ((examApplicableSex==Male)*(1-revenuePctFemale) + 
                     (examApplicableSex==Female)*(revenuePctFemale)) * 
                     (examApplicablePct)
        
        Args:
            revenue_source: Name of the revenue source
            
        Returns:
            DataFrame with maximum reachable volume for each exam
        """
        if not self._check_data_loaded():
            raise ValueError("Data not fully loaded. Call load_data first.")
        
        # Get revenue source data
        revenue_row = self.revenue_data[self.revenue_data['Title'] == revenue_source]
        if len(revenue_row) == 0:
            raise ValueError(f"Revenue source '{revenue_source}' not found")
        
        revenue_source_data = revenue_row.iloc[0]
        
        # Get offered exams for this revenue source
        offered_exams_str = revenue_source_data['OfferedExams']
        if isinstance(offered_exams_str, list):
            offered_exams = offered_exams_str
        else:
            offered_exams = [exam.strip() for exam in str(offered_exams_str).split(';')]
        
        # Filter exams data to include only offered exams
        filtered_exams = self.exams_data[self.exams_data['Title'].isin(offered_exams)]
        
        # Calculate max reachable volume for each exam
        results = []
        
        for _, exam in filtered_exams.iterrows():
            # Calculate the age factor
            exam_age_range = exam['MaxAge'] - exam['MinAge']
            revenue_age_range = revenue_source_data['PopulationMaxAge'] - revenue_source_data['PopulationMinAge']
            age_factor = exam_age_range / revenue_age_range if revenue_age_range > 0 else 0
            
            # Calculate the gender factor
            gender_factor = 0
            applicable_sex = exam['ApplicableSex']
            if isinstance(applicable_sex, list):
                if 'Male' in applicable_sex and 'Female' in applicable_sex:
                    gender_factor = 1.0
                elif 'Male' in applicable_sex:
                    gender_factor = 1.0 - revenue_source_data['PctFemale']
                elif 'Female' in applicable_sex:
                    gender_factor = revenue_source_data['PctFemale']
            else:
                if 'Male' in str(applicable_sex) and 'Female' in str(applicable_sex):
                    gender_factor = 1.0
                elif 'Male' in str(applicable_sex):
                    gender_factor = 1.0 - revenue_source_data['PctFemale']
                elif 'Female' in str(applicable_sex):
                    gender_factor = revenue_source_data['PctFemale']
            
            # Calculate the maximum reachable volume
            max_volume = (age_factor * 
                         revenue_source_data['TargetPopulation'] * 
                         revenue_source_data['PctPopulationReached'] * 
                         gender_factor * 
                         exam['ApplicablePct'])
            
            results.append({
                'RevenueSource': revenue_source,
                'Exam': exam['Title'],
                'MaxReachableVolume': max_volume,
                'AgeFactor': age_factor,
                'GenderFactor': gender_factor,
                'ApplicablePct': exam['ApplicablePct']
            })
        
        return pd.DataFrame(results)
    
    def get_available_equipment(self, date: str) -> pd.DataFrame:
        """
        Determine which equipment is available on a given date.
        
        Args:
            date: Date in format 'MM/DD/YYYY'
            
        Returns:
            DataFrame with available equipment
        """
        if not self._check_data_loaded():
            raise ValueError("Data not fully loaded. Call load_data first.")
        
        # Convert date to datetime
        check_date = pd.to_datetime(date, format='%m/%d/%Y')
        
        # Filter equipment that has been purchased by the check date
        available_equipment = self.equipment_data[self.equipment_data['PurchaseDate'] <= check_date]
        
        return available_equipment
    
    def get_available_staff(self, date: str) -> pd.DataFrame:
        """
        Determine which staff members are available on a given date.
        
        Args:
            date: Date in format 'MM/DD/YYYY'
            
        Returns:
            DataFrame with available staff
        """
        if not self._check_data_loaded():
            raise ValueError("Data not fully loaded. Call load_data first.")
        
        # Convert date to datetime
        check_date = pd.to_datetime(date, format='%m/%d/%Y')
        
        # Filter staff who are employed on the check date
        available_staff = self.personnel_data[
            (self.personnel_data['StartDate'] <= check_date) & 
            ((self.personnel_data['EndDate'] >= check_date) | pd.isna(self.personnel_data['EndDate']))
        ]
        
        return available_staff
    
    def calculate_staff_hours_available(self, date: str) -> Dict[str, float]:
        """
        Calculate available hours for each staff type on a given date.
        
        Args:
            date: Date in format 'MM/DD/YYYY'
            
        Returns:
            Dictionary mapping staff types to available hours
        """
        available_staff = self.get_available_staff(date)
        
        # Calculate hours available by staff type
        staff_hours = {}
        
        for _, staff in available_staff.iterrows():
            staff_type = staff['Type']
            
            # Calculate available hours: Effort * HoursPerDay
            hours = staff['Effort'] * staff['HoursPerDay']
            
            if staff_type in staff_hours:
                staff_hours[staff_type] += hours
            else:
                staff_hours[staff_type] = hours
        
        return staff_hours
    
    def calculate_exams_per_day(self, date: str, revenue_source: str) -> pd.DataFrame:
        """
        Calculate the number of exams that can be performed per day.
        
        Args:
            date: Date in format 'MM/DD/YYYY'
            revenue_source: Name of the revenue source
            
        Returns:
            DataFrame with exam volumes per day
        """
        if not self._check_data_loaded():
            raise ValueError("Data not fully loaded. Call load_data first.")
        
        # Get available equipment
        available_equipment = self.get_available_equipment(date)
        available_equip_titles = available_equipment['Title'].tolist()
        
        # Get revenue source data
        revenue_row = self.revenue_data[self.revenue_data['Title'] == revenue_source]
        if len(revenue_row) == 0:
            raise ValueError(f"Revenue source '{revenue_source}' not found")
        
        revenue_source_data = revenue_row.iloc[0]
        
        # Get offered exams for this revenue source
        offered_exams_str = revenue_source_data['OfferedExams']
        if isinstance(offered_exams_str, list):
            offered_exams = offered_exams_str
        else:
            offered_exams = [exam.strip() for exam in str(offered_exams_str).split(';')]
        
        # Filter exams that are offered by this revenue source and have available equipment
        filtered_exams = self.exams_data[self.exams_data['Title'].isin(offered_exams)]
        
        # Filter exams that have the necessary equipment
        exams_with_equipment = []
        for _, exam in filtered_exams.iterrows():
            exam_equipment = exam['Equipment']
            if isinstance(exam_equipment, list):
                if all(equip in available_equip_titles for equip in exam_equipment):
                    exams_with_equipment.append(exam['Title'])
            else:
                if exam_equipment in available_equip_titles:
                    exams_with_equipment.append(exam['Title'])
        
        # Re-filter exams to only those with available equipment
        filtered_exams = filtered_exams[filtered_exams['Title'].isin(exams_with_equipment)]
        
        # Calculate the maximum reachable volume for each exam
        max_volumes_df = self.calculate_max_reachable_volume(revenue_source)
        
        # Filter max volumes to only exams with available equipment
        max_volumes_df = max_volumes_df[max_volumes_df['Exam'].isin(exams_with_equipment)]
        
        # Calculate staff hours available
        staff_hours = self.calculate_staff_hours_available(date)
        
        # Calculate daily exam capacity based on staff availability
        results = []
        total_staff_hours_required = 0
        
        # First calculate proportions based on max reachable volumes
        total_max_volume = max_volumes_df['MaxReachableVolume'].sum()
        
        for _, row in max_volumes_df.iterrows():
            exam_title = row['Exam']
            exam_row = filtered_exams[filtered_exams['Title'] == exam_title].iloc[0]
            
            # Calculate proportion of this exam type
            proportion = row['MaxReachableVolume'] / total_max_volume if total_max_volume > 0 else 0
            
            # Get required staff type for this exam
            exam_staff = exam_row['Staff']
            if isinstance(exam_staff, list):
                staff_types = exam_staff
            else:
                staff_types = [s.strip() for s in str(exam_staff).split(';')]
            
            # Get duration in hours
            duration_hours = exam_row['DurationHours'] if 'DurationHours' in exam_row else exam_row['Duration'] / 60.0
            
            # Calculate capacity for each staff type
            min_capacity = float('inf')
            limiting_staff = None
            
            for staff_type in staff_types:
                if staff_type in staff_hours:
                    # How many exams can this staff type support in a day
                    staff_capacity = staff_hours[staff_type] / duration_hours
                    if staff_capacity < min_capacity:
                        min_capacity = staff_capacity
                        limiting_staff = staff_type
                else:
                    # Staff type not available
                    min_capacity = 0
                    limiting_staff = staff_type
                    break
            
            # Calculate target exams per day based on proportion
            target_exams = proportion * min_capacity
            
            # Calculate staff hours required
            staff_hours_required = target_exams * duration_hours
            total_staff_hours_required += staff_hours_required
            
            results.append({
                'RevenueSource': revenue_source,
                'Exam': exam_title,
                'Proportion': proportion,
                'StaffCapacity': min_capacity,
                'LimitingStaff': limiting_staff,
                'TargetExamsPerDay': target_exams,
                'Duration': duration_hours,
                'StaffHoursRequired': staff_hours_required
            })
        
        # Adjust target exams to not exceed staff capacity
        results_df = pd.DataFrame(results)
        
        return results_df
    
    def calculate_annual_exam_volume(self, year: int, revenue_source: str, work_days_per_year: int = 250) -> pd.DataFrame:
        """
        Calculate the annual volume, revenue, and expenses for exams for a specific year and revenue source.
        
        Args:
            year: The year to calculate for
            revenue_source: Name of the revenue source
            work_days_per_year: Number of working days per year
            
        Returns:
            DataFrame with annual exam volumes, revenue, and expenses
        """
        if not self._check_data_loaded():
            raise ValueError("Data not fully loaded. Call load_data first.")
        
        # Use mid-year date to check availability
        check_date = f"07/01/{year}"
        
        # Get revenue source data
        revenue_row = self.revenue_data[self.revenue_data['Title'] == revenue_source]
        if len(revenue_row) == 0:
            raise ValueError(f"Revenue source '{revenue_source}' not found")
        
        revenue_source_data = revenue_row.iloc[0]
        
        # Calculate daily exam volume
        daily_exams_df = self.calculate_exams_per_day(check_date, revenue_source)
        
        if daily_exams_df.empty:
            return pd.DataFrame()  # No exams can be performed
        
        # Calculate annual volume with the full model percentage
        full_model_pct = revenue_source_data['PctFullModel']
        
        results = []
        for _, row in daily_exams_df.iterrows():
            exam_title = row['Exam']
            
            # Get exam data
            exam_row = self.exams_data[self.exams_data['Title'] == exam_title].iloc[0]
            
            # Calculate annual volume
            annual_volume = work_days_per_year * full_model_pct * row['TargetExamsPerDay']
            
            # Calculate revenue
            cms_pct = revenue_source_data['PctCMS']
            non_cms_multiplier = revenue_source_data['NonCMSMultiplier']
            flat_patient_fee = revenue_source_data['FlatPatientFee']
            
            cms_tech_revenue = annual_volume * cms_pct * exam_row['CMSTechRate']
            cms_pro_revenue = annual_volume * cms_pct * exam_row['CMSProRate']
            non_cms_tech_revenue = annual_volume * (1 - cms_pct) * exam_row['CMSTechRate'] * non_cms_multiplier
            non_cms_pro_revenue = annual_volume * (1 - cms_pct) * exam_row['CMSProRate'] * non_cms_multiplier
            patient_fee_revenue = annual_volume * flat_patient_fee
            
            total_revenue = cms_tech_revenue + cms_pro_revenue + non_cms_tech_revenue + non_cms_pro_revenue + patient_fee_revenue
            
            # Calculate expenses
            supply_cost = annual_volume * exam_row['SupplyCost']
            order_cost = annual_volume * exam_row['OrderCost']
            interp_cost = annual_volume * exam_row['InterpCost']
            
            # Calculate revenue to partner
            revenue_to_partner_pct = revenue_source_data['RevenueToPartner']
            revenue_to_partner = total_revenue * revenue_to_partner_pct
            
            # Calculate net revenue
            total_direct_expenses = supply_cost + order_cost + interp_cost + revenue_to_partner
            net_revenue = total_revenue - total_direct_expenses
            
            results.append({
                'Year': year,
                'RevenueSource': revenue_source,
                'Exam': exam_title,
                'AnnualVolume': annual_volume,
                'CMS_Tech_Revenue': cms_tech_revenue,
                'CMS_Pro_Revenue': cms_pro_revenue,
                'NonCMS_Tech_Revenue': non_cms_tech_revenue,
                'NonCMS_Pro_Revenue': non_cms_pro_revenue,
                'Patient_Fee_Revenue': patient_fee_revenue,
                'Total_Revenue': total_revenue,
                'Supply_Cost': supply_cost,
                'Order_Cost': order_cost,
                'Interp_Cost': interp_cost,
                'Revenue_To_Partner': revenue_to_partner,
                'Total_Direct_Expenses': total_direct_expenses,
                'Net_Revenue': net_revenue
            })
        
        return pd.DataFrame(results)
    
    def calculate_multi_year_exam_revenue(self, start_year: int, end_year: int, revenue_sources: List[str] = None, work_days_per_year: int = 250) -> pd.DataFrame:
        """
        Calculate exam revenue and expenses across multiple years and revenue sources.
        
        Args:
            start_year: Starting year for the analysis
            end_year: Ending year for the analysis
            revenue_sources: List of revenue sources to analyze (default: all revenue sources)
            work_days_per_year: Number of working days per year
            
        Returns:
            DataFrame with annual exam volumes, revenue, and expenses for all years and revenue sources
        """
        if not self._check_data_loaded():
            raise ValueError("Data not fully loaded. Call load_data first.")
        
        # If no revenue sources specified, use all
        if revenue_sources is None:
            revenue_sources = self.revenue_data['Title'].tolist()
        
        # Collect results for all years and revenue sources
        all_results = []
        
        for year in range(start_year, end_year + 1):
            for revenue_source in revenue_sources:
                annual_results = self.calculate_annual_exam_volume(year, revenue_source, work_days_per_year)
                if not annual_results.empty:
                    all_results.append(annual_results)
        
        # Combine all results
        if all_results:
            return pd.concat(all_results, ignore_index=True)
        else:
            return pd.DataFrame()


# Utility functions for direct use without instantiating the class
def calculate_exam_revenue(exams_data: pd.DataFrame, 
                          revenue_data: pd.DataFrame, 
                          personnel_data: pd.DataFrame,
                          equipment_data: pd.DataFrame,
                          start_year: int, 
                          end_year: int,
                          revenue_sources: List[str] = None,
                          work_days_per_year: int = 250) -> pd.DataFrame:
    """
    Utility function to calculate exam revenue without having to manually instantiate the class.
    
    Args:
        exams_data: DataFrame containing exam data
        revenue_data: DataFrame containing revenue source data
        personnel_data: DataFrame containing personnel data
        equipment_data: DataFrame containing equipment data
        start_year: Starting year for the analysis
        end_year: Ending year for the analysis
        revenue_sources: List of revenue sources to analyze (default: all revenue sources)
        work_days_per_year: Number of working days per year
        
    Returns:
        DataFrame with annual exam volumes, revenue, and expenses for all years and revenue sources
    """
    calculator = ExamRevenueCalculator(
        exams_data=exams_data,
        revenue_data=revenue_data,
        personnel_data=personnel_data,
        equipment_data=equipment_data
    )
    
    return calculator.calculate_multi_year_exam_revenue(
        start_year=start_year,
        end_year=end_year,
        revenue_sources=revenue_sources,
        work_days_per_year=work_days_per_year
    ) 