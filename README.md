# CAREScan ProForma Editor

A Streamlit application for financial modeling and visualization of imaging center pro forma projections.

## Features

- View and edit data from multiple CSV files in a modular, tabbed interface
- Calculate and visualize financial projections including:
  - Equipment expenses and depreciation
  - Personnel costs
  - Exam revenue analysis
  - Other expenses tracking
  - Comprehensive financial pro forma
- Add, edit, and delete rows in each data table
- Save changes back to CSV files
- Export all data to a JSON structure
- Import data from a JSON structure

## Project Structure

The application has been refactored into a modular architecture:

- **app.py**: Main application entry point
- **app_controller.py**: Application state management
- **visualization.py**: Reusable visualization functions
- **ui/**: UI components
  - **revenue_tab.py**: Revenue data editing and visualization
  - **equipment_tab.py**: Equipment data editing and expense analysis
  - **personnel_tab.py**: Personnel data editing and expense analysis
  - **exams_tab.py**: Exam data editing and revenue analysis
  - **other_expenses_tab.py**: Other expenses data editing and analysis
  - **plots_tab.py**: Summary financial visualizations
  - **comprehensive_tab.py**: Comprehensive pro forma analysis
- **financeModels/**: Core financial calculation modules
  - **equipment_expenses.py**: Equipment expense calculations
  - **personnel_expenses.py**: Personnel expense calculations
  - **exam_revenue.py**: Exam revenue calculations
  - **other_expenses.py**: Other expenses calculations
  - **comprehensive_proforma.py**: Comprehensive financial model
  - **file_handler.py**: CSV and JSON data handling utilities

## CSV Files Included

- **Revenue.csv**: Contains information about revenue streams
- **Equipment.csv**: Contains information about equipment costs
- **Personnel.csv**: Contains information about personnel and staff
- **Exams.csv**: Contains information about exams offered
- **OtherExpenses.csv**: Contains information about other expenses

## Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the Streamlit application:

```bash
streamlit run app.py
```
or use the provided shell script:
```bash
./run_app.sh
```

2. The application will open in your web browser.
3. Use the tabs to switch between different sections of the application.
4. Edit data directly in the tables and see visualizations update.
5. Click "Save" to save changes to the respective CSV file.

## Data Export/Import

- All data is automatically saved to their respective CSV files when edited
- Data is also synchronized with a JSON file (carescan_data.json) for backup and easier access
- Use the "Reload All Data" button in the sidebar if you need to refresh from disk

## Development

To extend the application:

1. Add new UI components in the `ui/` directory following the existing pattern
2. Update financial models in the `financeModels/` directory as needed
3. Register new tabs in `app.py` and update the `ui/__init__.py` file as necessary

## Notes

- The application automatically detects semicolon-separated list values in the CSV files
- Financial calculations are performed using the specialized calculators in the financeModels directory 