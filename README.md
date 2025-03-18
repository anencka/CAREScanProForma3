# CAREScan ProForma Editor

A Streamlit application for viewing and editing CAREScan ProForma data contained in CSV files.

## Features

- View and edit data from multiple CSV files in a tabbed interface
- Add, edit, and delete rows in each table
- Save changes back to CSV files
- Export all data to a JSON structure
- Import data from a JSON structure

## CSV Files Included

- **Revenue.csv**: Contains information about revenue streams
- **Equipment.csv**: Contains information about equipment costs
- **Personnel.csv**: Contains information about personnel and staff
- **Exams.csv**: Contains information about exams offered

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

2. The application will open in your web browser.
3. Use the tabs to switch between different CSV files.
4. Edit data directly in the tables.
5. Click "Save" to save changes to the respective CSV file.
6. Use the "Export/Import" tab to export all data to a JSON file or import data from a JSON file.

## Data Export/Import

- **Export**: All data from the CSVs will be saved to a JSON file with the specified name.
- **Import**: Data from a JSON file will be loaded and used to update the respective CSV files.

## Notes

- The application automatically detects semicolon-separated list values in the CSV files.
- Timestamps for each file's last modification are displayed in the sidebar. 