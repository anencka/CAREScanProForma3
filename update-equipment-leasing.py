"""
Equipment Leasing Update Script for CAREScan ProForma Editor.

This script:
1. Updates the Equipment.csv to convert mammo and CT to leases and add MRI
2. Adds MRI exam types to Exams.csv
3. Updates Personnel.csv to add necessary MRI personnel types
4. Updates Revenue.csv to include MRI in offered exams

Run this script from the main directory containing the CSV files.
"""

import pandas as pd
import os
import sys

def update_equipment_data():
    """
    Update Equipment.csv to convert mammo and CT to leases and add MRI.
    """
    print("Updating Equipment.csv...")
    
    # Check if Equipment.csv exists
    if not os.path.exists('Equipment.csv'):
        print("Error: Equipment.csv not found.")
        return False
    
    try:
        # Load the current Equipment data
        equipment_df = pd.read_csv('Equipment.csv')
        
        # Add lease columns if they don't exist
        if 'IsLeased' not in equipment_df.columns:
            equipment_df['IsLeased'] = False
        
        if 'AnnualLeaseAmount' not in equipment_df.columns:
            equipment_df['AnnualLeaseAmount'] = 0
        
        # Convert mammography to lease
        mamorows = equipment_df[equipment_df['Title'] == 'MamoVan']
        if not mamorows.empty:
            # Update existing MamoVan row
            equipment_df.loc[equipment_df['Title'] == 'MamoVan', 'IsLeased'] = True
            equipment_df.loc[equipment_df['Title'] == 'MamoVan', 'PurchaseCost'] = 0  # Zero out purchase cost
            equipment_df.loc[equipment_df['Title'] == 'MamoVan', 'AnnualLeaseAmount'] = 250000  # Set lease amount
            print("Updated MamoVan to be leased equipment")
        else:
            print("Warning: MamoVan not found in Equipment.csv")
        
        # Convert CT to lease
        ctrows = equipment_df[equipment_df['Title'] == 'CTTruck']
        if not ctrows.empty:
            # Update existing CTTruck row
            equipment_df.loc[equipment_df['Title'] == 'CTTruck', 'IsLeased'] = True
            equipment_df.loc[equipment_df['Title'] == 'CTTruck', 'PurchaseCost'] = 0  # Zero out purchase cost
            equipment_df.loc[equipment_df['Title'] == 'CTTruck', 'AnnualLeaseAmount'] = 450000  # Set lease amount
            print("Updated CTTruck to be leased equipment")
        else:
            print("Warning: CTTruck not found in Equipment.csv")
        
        # Check for MRI Truck
        mrirows = equipment_df[equipment_df['Title'] == 'MRITruck']
        if not mrirows.empty:
            # Update existing MRITruck to ensure it's leased
            equipment_df.loc[equipment_df['Title'] == 'MRITruck', 'IsLeased'] = True
            equipment_df.loc[equipment_df['Title'] == 'MRITruck', 'PurchaseCost'] = 0  # Zero out purchase cost
            equipment_df.loc[equipment_df['Title'] == 'MRITruck', 'AnnualLeaseAmount'] = 600000  # Set lease amount
            print("Updated existing MRITruck to be leased equipment")
        else:
            # Add MRI Truck as a new row
            # Get a template row from an existing truck
            template_row = None
            if not ctrows.empty:
                template_row = ctrows.iloc[0].copy()
            elif not mamorows.empty:
                template_row = mamorows.iloc[0].copy()
            
            if template_row is not None:
                # Create MRI truck data
                mri_data = {
                    'Title': 'MRITruck',
                    'PurchaseCost': 0,  # Leased, so purchase cost is 0
                    'Quantity': 1,
                    'PurchaseDate': template_row['PurchaseDate'],  # Use same date as template
                    'ConstructionTime': 300,  # Longer construction time for MRI
                    'Lifespan': 10,  # Standard lifespan
                    'AnnualServiceCost': 350000,  # Higher service costs for MRI
                    'NecessaryStaff': 'MRITech; MRIAssistant; MRIDriver',
                    'ExamsOffered': 'MRIBrain; MRISpine; MRIExtremeties',
                    'MilageCost': 5,
                    'SetupTime': 300,  # Longer setup time for MRI
                    'TakedownTime': 240,  # Longer takedown time for MRI
                    'AnnualAccreditationCost': 10000,
                    'AnnualInsuranceCost': 70000,  # Higher insurance for MRI
                    'IsLeased': True,
                    'AnnualLeaseAmount': 600000  # Annual lease payment
                }
                
                # Add MRI row to dataframe
                equipment_df = pd.concat([equipment_df, pd.DataFrame([mri_data])], ignore_index=True)
                print("Added new MRITruck as leased equipment")
            else:
                print("Warning: Could not find template row for MRITruck. MRI not added.")
        
        # Save updated Equipment.csv
        equipment_df.to_csv('Equipment.csv', index=False)
        print("Equipment.csv updated successfully.")
        return True
    
    except Exception as e:
        print(f"Error updating Equipment.csv: {str(e)}")
        return False

def update_exams_data():
    """
    Update Exams.csv to add MRI exam types.
    """
    print("Updating Exams.csv...")
    
    # Check if Exams.csv exists
    if not os.path.exists('Exams.csv'):
        print("Error: Exams.csv not found.")
        return False
    
    try:
        # Load the current Exams data
        exams_df = pd.read_csv('Exams.csv')
        
        # Check if MRI exams already exist
        mri_exams = exams_df[exams_df['Title'].isin(['MRIBrain', 'MRISpine', 'MRIExtremeties'])]
        
        if len(mri_exams) == 3:
            print("MRI exams already exist in Exams.csv")
            return True
        
        # Add MRI exam types - Brain, Spine, Extremities
        mri_exams_list = []
        
        # Only add exams that don't already exist
        existing_titles = exams_df['Title'].tolist()
        
        if 'MRIBrain' not in existing_titles:
            mri_exams_list.append({
                'Title': 'MRIBrain',
                'Equipment': 'MRITruck',
                'Staff': 'MRITech',
                'Duration': 45,  # Minutes
                'SupplyCost': 5,
                'OrderCost': 30,
                'InterpCost': 150,
                'CMSTechRate': 300,
                'CMSProRate': 250,
                'MinAge': 18,
                'MaxAge': 100,
                'ApplicableSex': 'Female; Male',
                'ApplicablePct': 0.1
            })
        
        if 'MRISpine' not in existing_titles:
            mri_exams_list.append({
                'Title': 'MRISpine',
                'Equipment': 'MRITruck',
                'Staff': 'MRITech',
                'Duration': 60,  # Minutes
                'SupplyCost': 5,
                'OrderCost': 30,
                'InterpCost': 175,
                'CMSTechRate': 350,
                'CMSProRate': 275,
                'MinAge': 18,
                'MaxAge': 100,
                'ApplicableSex': 'Female; Male',
                'ApplicablePct': 0.15
            })
        
        if 'MRIExtremeties' not in existing_titles:
            mri_exams_list.append({
                'Title': 'MRIExtremeties',
                'Equipment': 'MRITruck',
                'Staff': 'MRITech',
                'Duration': 40,  # Minutes
                'SupplyCost': 5,
                'OrderCost': 30,
                'InterpCost': 125,
                'CMSTechRate': 250,
                'CMSProRate': 200,
                'MinAge': 18,
                'MaxAge': 100,
                'ApplicableSex': 'Female; Male',
                'ApplicablePct': 0.08
            })
        
        # Add new rows to dataframe
        if mri_exams_list:
            exams_df = pd.concat([exams_df, pd.DataFrame(mri_exams_list)], ignore_index=True)
            print(f"Added {len(mri_exams_list)} MRI exam types to Exams.csv")
        else:
            print("No new MRI exams to add.")
        
        # Save updated Exams.csv
        exams_df.to_csv('Exams.csv', index=False)
        print("Exams.csv updated successfully.")
        return True
    
    except Exception as e:
        print(f"Error updating Exams.csv: {str(e)}")
        return False

def update_personnel_data():
    """
    Update Personnel.csv to add MRI personnel types.
    """
    print("Updating Personnel.csv...")
    
    # Check if Personnel.csv exists
    if not os.path.exists('Personnel.csv'):
        print("Error: Personnel.csv not found.")
        return False
    
    try:
        # Load the current Personnel data
        personnel_df = pd.read_csv('Personnel.csv')
        
        # Check if MRI personnel already exist
        mri_personnel = personnel_df[personnel_df['Type'].isin(['MRITech', 'MRIAssistant', 'MRIDriver'])]
        
        if not mri_personnel.empty:
            print(f"MRI personnel already exist in Personnel.csv ({len(mri_personnel)} entries)")
            return True
        
        # Use existing CT personnel as templates
        ct_tech = personnel_df[personnel_df['Type'] == 'CTTech']
        ct_assistant = personnel_df[personnel_df['Type'] == 'CTAssistant']
        ct_driver = personnel_df[personnel_df['Type'] == 'CTDriver']
        
        # Only proceed if we have template data
        if ct_tech.empty or ct_assistant.empty or ct_driver.empty:
            print("Warning: Could not find template CT personnel for MRI personnel")
            return False
        
        # Add MRI Tech personnel
        mri_personnel_list = []
        
        # Get standard information from existing personnel
        template_tech = ct_tech.iloc[0]
        template_assistant = ct_assistant.iloc[0]
        template_driver = ct_driver.iloc[0]
        
        # Create MRI Technicians (similar to CT Techs but higher salary)
        mri_personnel_list.append({
            'Title': 'MRITech1',
            'Type': 'MRITech',
            'Institution': template_tech['Institution'],
            'Salary': 120000,  # Higher salary than CT Tech
            'Effort': 1.0,
            'Fringe': template_tech['Fringe'],
            'StartDate': template_tech['StartDate'],
            'EndDate': template_tech['EndDate'],
            'HoursPerDay': template_tech['HoursPerDay'],
            'SupportedExams': 'MRIBrain; MRISpine; MRIExtremeties'
        })
        
        mri_personnel_list.append({
            'Title': 'MRITech2',
            'Type': 'MRITech',
            'Institution': template_tech['Institution'],
            'Salary': 120000,  # Higher salary than CT Tech
            'Effort': 0.5,  # Part-time
            'Fringe': template_tech['Fringe'],
            'StartDate': template_tech['StartDate'],
            'EndDate': template_tech['EndDate'],
            'HoursPerDay': template_tech['HoursPerDay'],
            'SupportedExams': 'MRIBrain; MRISpine; MRIExtremeties'
        })
        
        # Create MRI Assistant (similar to CT Assistant)
        mri_personnel_list.append({
            'Title': 'MRIAssistant1',
            'Type': 'MRIAssistant',
            'Institution': template_assistant['Institution'],
            'Salary': 85000,  # Higher salary than CT Assistant
            'Effort': 1.0,
            'Fringe': template_assistant['Fringe'],
            'StartDate': template_assistant['StartDate'],
            'EndDate': template_assistant['EndDate'],
            'HoursPerDay': template_assistant['HoursPerDay'],
            'SupportedExams': 'MRIBrain; MRISpine; MRIExtremeties'
        })
        
        # Create MRI Drivers (similar to CT Drivers)
        mri_personnel_list.append({
            'Title': 'MRIDriver1',
            'Type': 'MRIDriver',
            'Institution': template_driver['Institution'],
            'Salary': 60000,  # Similar to CT Driver
            'Effort': 1.0,
            'Fringe': template_driver['Fringe'],
            'StartDate': template_driver['StartDate'],
            'EndDate': template_driver['EndDate'],
            'HoursPerDay': template_driver['HoursPerDay'],
            'SupportedExams': 'MRIBrain; MRISpine; MRIExtremeties'
        })
        
        mri_personnel_list.append({
            'Title': 'MRIDriver2',
            'Type': 'MRIDriver',
            'Institution': template_driver['Institution'],
            'Salary': 60000,  # Similar to CT Driver
            'Effort': 0.5,  # Part-time
            'Fringe': template_driver['Fringe'],
            'StartDate': template_driver['StartDate'],
            'EndDate': template_driver['EndDate'],
            'HoursPerDay': template_driver['HoursPerDay'],
            'SupportedExams': 'MRIBrain; MRISpine; MRIExtremeties'
        })
        
        # Add a Radiologist for MRI interpretation
        radiologists = personnel_df[personnel_df['Title'].str.contains('Radiologist', na=False)]
        if not radiologists.empty:
            template_radiologist = radiologists.iloc[0]
            
            mri_personnel_list.append({
                'Title': 'RadiologistMRI1',
                'Type': 'Staff',
                'Institution': template_radiologist['Institution'],
                'Salary': 430000,  # High salary for MRI radiologist
                'Effort': 0.01,  # Low effort - reading only
                'Fringe': template_radiologist['Fringe'],
                'StartDate': template_radiologist['StartDate'],
                'EndDate': template_radiologist['EndDate'],
                'HoursPerDay': template_radiologist['HoursPerDay'],
                'SupportedExams': 'MRIBrain; MRISpine; MRIExtremeties'
            })
        
        # Add new rows to dataframe
        personnel_df = pd.concat([personnel_df, pd.DataFrame(mri_personnel_list)], ignore_index=True)
        print(f"Added {len(mri_personnel_list)} MRI personnel to Personnel.csv")
        
        # Save updated Personnel.csv
        personnel_df.to_csv('Personnel.csv', index=False)
        print("Personnel.csv updated successfully.")
        return True
    
    except Exception as e:
        print(f"Error updating Personnel.csv: {str(e)}")
        return False

def update_revenue_data():
    """
    Update Revenue.csv to include MRI in offered exams.
    """
    print("Updating Revenue.csv...")
    
    # Check if Revenue.csv exists
    if not os.path.exists('Revenue.csv'):
        print("Error: Revenue.csv not found.")
        return False
    
    try:
        # Load the current Revenue data
        revenue_df = pd.read_csv('Revenue.csv')
        
        # Update OfferedExams to include MRI for all revenue sources
        mri_exams = "MRIBrain; MRISpine; MRIExtremeties"
        
        for idx, row in revenue_df.iterrows():
            # Get current offered exams
            offered_exams = row['OfferedExams']
            
            # Check if MRI exams are already included
            if 'MRIBrain' not in offered_exams:
                # Add MRI exams to the list
                updated_exams = f"{offered_exams}; {mri_exams}"
                
                # Update the dataframe
                revenue_df.at[idx, 'OfferedExams'] = updated_exams
        
        # Save updated Revenue.csv
        revenue_df.to_csv('Revenue.csv', index=False)
        print("Revenue.csv updated successfully with MRI exams.")
        return True
    
    except Exception as e:
        print(f"Error updating Revenue.csv: {str(e)}")
        return False

def update_json_file():
    """
    Update carescan_data.json with all the changes.
    """
    print("Updating carescan_data.json...")
    
    # Check if regenerate_json.py exists
    if os.path.exists('regenerate_json.py'):
        try:
            # Use the existing regenerate_json.py script
            import regenerate_json
            success = regenerate_json.regenerate_json()
            
            if success:
                print("carescan_data.json updated successfully.")
                return True
            else:
                print("Failed to update carescan_data.json.")
                return False
        except Exception as e:
            print(f"Error running regenerate_json.py: {str(e)}")
            return False
    else:
        print("regenerate_json.py not found. JSON file will not be updated.")
        return False

def main():
    """Main function to execute all updates."""
    print("Starting CAREScan Equipment Leasing Update")
    print("------------------------------------------")
    
    # Update each file in sequence
    success_equipment = update_equipment_data()
    success_exams = update_exams_data()
    success_personnel = update_personnel_data()
    success_revenue = update_revenue_data()
    
    # Update JSON file after all CSV files are updated
    if success_equipment and success_exams and success_personnel and success_revenue:
        success_json = update_json_file()
        
        if success_json:
            print("\nAll updates completed successfully!")
        else:
            print("\nCSV files updated, but JSON file update failed.")
    else:
        print("\nSome updates failed. Please check the errors above.")
    
    print("\nTo apply these changes to the application:")
    print("1. Replace financeModels/equipment_expenses.py with the updated version")
    print("2. Replace ui/equipment_tab.py with the updated version")
    print("3. Run the application: streamlit run app.py")

if __name__ == "__main__":
    main()