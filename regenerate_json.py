"""
Utility script to regenerate the JSON file from CSV files.
This can be used when the JSON file is corrupted.
"""

import os
import sys
from financeModels.file_handler import (
    load_csv, save_json, sync_csv_to_json
)

# Define the CSV files to load
CSV_FILES = {
    "Revenue": "Revenue.csv",
    "Equipment": "Equipment.csv",
    "Personnel": "Personnel.csv",
    "Exams": "Exams.csv",
    "OtherExpenses": "OtherExpenses.csv"
}

JSON_FILE = "carescan_data.json"

def regenerate_json():
    """Regenerate the JSON file from CSV files."""
    print(f"Regenerating {JSON_FILE} from CSV files...")
    
    # Check if CSV files exist
    missing_files = []
    for name, filepath in CSV_FILES.items():
        if not os.path.exists(filepath):
            missing_files.append(filepath)
    
    if missing_files:
        print(f"Error: The following CSV files are missing: {', '.join(missing_files)}")
        return False
    
    try:
        # Load data from each CSV file
        data_dict = {}
        for key, filepath in CSV_FILES.items():
            print(f"  Loading {filepath}...")
            try:
                df = load_csv(filepath)
                data_dict[key] = df
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
                return False
        
        # Save to JSON file
        print(f"  Saving to {JSON_FILE}...")
        save_json(data_dict, JSON_FILE)
        
        print(f"Successfully regenerated {JSON_FILE} from CSV files.")
        return True
    except Exception as e:
        print(f"Error regenerating JSON file: {e}")
        return False

if __name__ == "__main__":
    success = regenerate_json()
    if success:
        print("Done.")
    else:
        print("Failed to regenerate JSON file.")
        sys.exit(1) 