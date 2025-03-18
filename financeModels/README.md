# financeModels

A comprehensive financial modeling package for CAREScan ProForma calculations.

## Overview

This package contains modules for various financial calculations and projections used in the CAREScan ProForma application. It provides tools for:

- Personnel expense calculations and projections
- Financial reporting and visualization
- Integration with Streamlit for interactive dashboards
- CSV-JSON data synchronization for consistent file formats

## Modules

### personnel_expenses.py

The `personnel_expenses.py` module provides tools for calculating personnel expenses based on salary, effort, fringe benefits, and time periods. It includes:

- `PersonnelExpenseCalculator` class for detailed personnel expense calculations
- Functions to calculate monthly, annual, and categorical expenses
- Headcount calculations (by full-time equivalent)
- Support for date ranges and partial periods

#### Example Usage

```python
from financeModels.personnel_expenses import PersonnelExpenseCalculator

# Initialize with data from a CSV file
calculator = PersonnelExpenseCalculator(personnel_file="Personnel.csv")

# Calculate monthly expenses for a date range
monthly_expenses = calculator.calculate_monthly_expense(
    start_date="01/01/2025", 
    end_date="12/31/2029"
)

# Calculate annual summaries
annual_expenses = calculator.calculate_annual_expense(
    start_date="01/01/2025", 
    end_date="12/31/2029"
)

# Get grand total
grand_total = calculator.calculate_grand_total(
    start_date="01/01/2025", 
    end_date="12/31/2029"
)
print(f"Total Personnel Expenses: ${grand_total['Total_Expense']:,.2f}")
```

### file_handler.py

The `file_handler.py` module provides tools for handling file operations and ensuring data consistency between CSV and JSON formats. It includes:

- Functions to load and save CSV files with proper formatting
- Functions to load and save JSON files with multiple datasets
- Tools to synchronize data between CSV and JSON formats
- Utilities for processing values for display and storage

#### Example Usage

```python
from financeModels.file_handler import sync_json_to_csv, sync_csv_to_json

# Define the CSV and JSON file mappings
csv_mapping = {
    "Revenue": "Revenue.csv",
    "Equipment": "Equipment.csv",
    "Personnel": "Personnel.csv",
    "Exams": "Exams.csv"
}

# Import data from JSON and update CSV files
data_dict = sync_json_to_csv("carescan_data.json", csv_mapping)

# Export data from CSV files to JSON
data_dict = sync_csv_to_json(csv_mapping, "carescan_data.json")
```

### example_usage.py

This module provides examples of how to use the financeModels package. It includes:

- A demonstration function that runs through core features
- Visualization examples using matplotlib
- Example data processing workflows

#### Running the Example

```python
from financeModels.example_usage import run_personnel_expense_example

# Run the example
results = run_personnel_expense_example()

# Create visualizations
from financeModels.example_usage import visualize_personnel_expenses
visualize_personnel_expenses(results)
```

### app_integration.py

This module demonstrates how to integrate the financeModels package with a Streamlit application. It includes:

- Dashboard components for visualizing personnel expenses
- Interactive date selection and filtering
- Excel report generation and download
- Error handling and logging

#### Using in a Streamlit App

```python
import streamlit as st
import pandas as pd
from financeModels.app_integration import display_personnel_expenses_dashboard

# Load personnel data
personnel_data = pd.read_csv("Personnel.csv")

# Process dates
for date_col in ['StartDate', 'EndDate']:
    if date_col in personnel_data.columns:
        personnel_data[date_col] = pd.to_datetime(
            personnel_data[date_col], 
            format='%m/%d/%Y', 
            errors='coerce'
        )

# Add the dashboard to your Streamlit app
display_personnel_expenses_dashboard(personnel_data)
```

### json_csv_sync_example.py

This module demonstrates how to keep CSV files and JSON files synchronized in a Streamlit application. It includes:

- Example functions for CSV to JSON synchronization
- Example functions for JSON to CSV synchronization
- A sample Streamlit app demonstrating the synchronization process
- Code snippets for integration with app.py

#### Running the Example

```python
# Run the Streamlit example
streamlit run financeModels/json_csv_sync_example.py

# See code examples
from financeModels.json_csv_sync_example import app_py_integration_example
app_py_integration_example()
```

### app_example.py

This is a simplified version of app.py that demonstrates how to integrate the financeModels package for CSV-JSON synchronization. It includes:

- Tab-based UI for editing different datasets
- Import/Export functionality with automatic synchronization
- Personnel expenses analysis dashboard integration
- Error handling and state management

#### Running the Example App

```bash
streamlit run financeModels/app_example.py
```

## Dependencies

- pandas
- numpy
- matplotlib (for visualizations)
- streamlit (for app integration)
- xlsxwriter (for Excel export)

## Installation

Ensure the financeModels directory is in your Python path, or install it directly from the project root:

```
pip install -e .
```

## Integration with app.py

To integrate the CSV-JSON synchronization functionality with the existing app.py, modify the following parts:

1. Import the necessary functions:
```python
from financeModels.file_handler import sync_json_to_csv, sync_csv_to_json, load_csv, save_csv
```

2. Replace the existing file loading/saving functions with the synchronized versions:
```python
# Replace existing import_from_json with:
def import_from_json(filepath):
    data_dict = sync_json_to_csv(filepath, CSV_FILES)
    return data_dict

# Replace existing export_to_json with:
def export_to_json(data_dict, filepath):
    # Ensure CSV files are updated first
    for key, df in data_dict.items():
        if key in CSV_FILES:
            save_csv(df, CSV_FILES[key])
    
    # Then synchronize all to JSON
    sync_csv_to_json(CSV_FILES, filepath)
    return True
```

3. Add "Save & Sync" buttons to each tab to keep JSON file updated with CSV changes.

## Contributing

When contributing to this package:

1. Follow the existing code style and documentation patterns
2. Add tests for any new functionality
3. Update the README.md with details of changes to the interface
4. Update requirements.txt if adding new dependencies 