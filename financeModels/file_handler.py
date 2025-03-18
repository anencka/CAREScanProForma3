"""
Handles file operations and synchronization between JSON and CSV files.

This module provides functions to:
1. Import data from JSON files and update corresponding CSV files
2. Export data to JSON files after updating from CSV files
3. Ensure data consistency between formats
"""

import pandas as pd
import json
import os
from typing import Dict, List, Optional, Union

def process_value_for_display(value):
    """Format values for display in the data editor."""
    if isinstance(value, str) and ';' in value:
        # Clean up the semicolon-separated values
        items = [item.strip() for item in value.split(';') if item.strip()]
        return '; '.join(items)
    return value

def process_value_for_save(value):
    """Format values for saving to CSV."""
    if isinstance(value, (list, tuple)):
        # Convert lists back to semicolon-separated strings
        return '; '.join(str(item) for item in value) + ';'
    return value

def convert_underscore_numbers(value):
    """Convert string numbers with underscores to integers or floats."""
    import re
    if isinstance(value, str):
        # If it's a string that looks like a number with underscores
        if re.match(r'^\d+(_\d+)*(\.\d+)?$', value):
            # Remove underscores and convert to number
            return float(value.replace('_', ''))
    return value

def load_csv(filepath: str) -> pd.DataFrame:
    """
    Load a CSV file into a DataFrame with appropriate processing.
    
    Args:
        filepath: Path to the CSV file
        
    Returns:
        DataFrame containing the CSV data
    """
    try:
        # Handle the specific format of these CSVs with spaces after commas
        df = pd.read_csv(filepath, skipinitialspace=True)
        
        # Process numeric values with underscores
        for col in df.columns:
            df[col] = df[col].apply(convert_underscore_numbers)
            
        # Process semicolon-separated values
        for col in df.columns:
            if df[col].dtype == 'object':  # Only process string columns
                df[col] = df[col].apply(process_value_for_display)
        
        return df
    except Exception as e:
        raise IOError(f"Error loading {filepath}: {e}")

def save_csv(df: pd.DataFrame, filepath: str) -> bool:
    """
    Save a DataFrame to a CSV file with appropriate processing.
    
    Args:
        df: DataFrame to save
        filepath: Path to save the CSV file
        
    Returns:
        True if successful, raises exception otherwise
    """
    try:
        # Process values for saving
        save_df = df.copy()
        for col in save_df.columns:
            save_df[col] = save_df[col].apply(process_value_for_save)
        
        save_df.to_csv(filepath, index=False)
        return True
    except Exception as e:
        raise IOError(f"Error saving {filepath}: {e}")

def load_json(filepath: str) -> Dict[str, pd.DataFrame]:
    """
    Load a JSON file containing multiple datasets.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        Dictionary mapping names to DataFrames
    """
    try:
        with open(filepath, 'r') as f:
            json_dict = json.load(f)
        
        data_dict = {}
        for key, records in json_dict.items():
            try:
                # Make sure we have a list of records
                if not isinstance(records, list):
                    if isinstance(records, dict):
                        # If it's a dict, try to convert to list of records
                        records = [records]
                    else:
                        # Skip this key if we can't convert
                        continue
                
                # Create DataFrame from records
                df = pd.DataFrame.from_records(records)
                
                # Process values after import
                for col in df.columns:
                    df[col] = df[col].apply(convert_underscore_numbers)
                    if df[col].dtype == 'object':
                        df[col] = df[col].apply(process_value_for_display)
                
                data_dict[key] = df
            except Exception as e:
                raise ValueError(f"Error processing {key}: {str(e)}")
        
        return data_dict
    except Exception as e:
        raise IOError(f"Error importing from JSON: {str(e)}")

def save_json(data_dict: Dict[str, pd.DataFrame], filepath: str) -> bool:
    """
    Save a dictionary of DataFrames to a JSON file.
    
    Args:
        data_dict: Dictionary mapping names to DataFrames
        filepath: Path to save the JSON file
        
    Returns:
        True if successful, raises exception otherwise
    """
    try:
        # Convert DataFrames to serializable format
        json_dict = {}
        for key, df in data_dict.items():
            # Ensure we're working with a pandas DataFrame
            if not isinstance(df, pd.DataFrame):
                try:
                    df = pd.DataFrame(df)
                except Exception as e:
                    raise ValueError(f"Could not convert '{key}' to DataFrame: {str(e)}")
            
            # Process values for JSON export
            export_df = df.copy()
            for col in export_df.columns:
                export_df[col] = export_df[col].apply(process_value_for_save)
            
            json_dict[key] = export_df.to_dict(orient='records')
        
        with open(filepath, 'w') as f:
            json.dump(json_dict, f, indent=2)
        
        return True
    except Exception as e:
        raise IOError(f"Error exporting to JSON: {str(e)}")

def sync_json_to_csv(json_filepath: str, csv_mapping: Dict[str, str]) -> Dict[str, pd.DataFrame]:
    """
    Load data from a JSON file and update corresponding CSV files.
    
    Args:
        json_filepath: Path to the JSON file
        csv_mapping: Dictionary mapping JSON keys to CSV file paths
        
    Returns:
        Dictionary of loaded DataFrames
    """
    # Load the JSON data
    data_dict = load_json(json_filepath)
    
    # Update each CSV file with the corresponding data
    for key, csv_path in csv_mapping.items():
        if key in data_dict and os.path.exists(csv_path):
            try:
                # Save the data to the CSV file
                save_csv(data_dict[key], csv_path)
            except Exception as e:
                raise IOError(f"Failed to update CSV file {csv_path}: {str(e)}")
    
    return data_dict

def sync_csv_to_json(csv_mapping: Dict[str, str], json_filepath: str) -> Dict[str, pd.DataFrame]:
    """
    Load data from CSV files and update a JSON file.
    
    Args:
        csv_mapping: Dictionary mapping keys to CSV file paths
        json_filepath: Path to the JSON file to update
        
    Returns:
        Dictionary of loaded DataFrames
    """
    # Load data from each CSV file
    data_dict = {}
    for key, csv_path in csv_mapping.items():
        if os.path.exists(csv_path):
            try:
                # Load the CSV data
                data_dict[key] = load_csv(csv_path)
            except Exception as e:
                raise IOError(f"Failed to load CSV file {csv_path}: {str(e)}")
    
    # Save the data to the JSON file
    save_json(data_dict, json_filepath)
    
    return data_dict

def update_csv_from_dataframes(dataframes: Dict[str, pd.DataFrame], csv_mapping: Dict[str, str]) -> bool:
    """
    Update CSV files from a dictionary of DataFrames.
    
    Args:
        dataframes: Dictionary mapping names to DataFrames
        csv_mapping: Dictionary mapping names to CSV file paths
        
    Returns:
        True if successful, False otherwise
    """
    success = True
    for key, csv_path in csv_mapping.items():
        if key in dataframes:
            try:
                # Save the DataFrame to the CSV file
                save_csv(dataframes[key], csv_path)
            except Exception as e:
                print(f"Failed to update CSV file {csv_path}: {str(e)}")
                success = False
    
    return success

def update_json_from_csvs(csv_mapping: Dict[str, str], json_filepath: str) -> bool:
    """
    Update a JSON file from CSV files.
    
    Args:
        csv_mapping: Dictionary mapping keys to CSV file paths
        json_filepath: Path to the JSON file to update
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Load data from each CSV file
        data_dict = {}
        for key, csv_path in csv_mapping.items():
            if os.path.exists(csv_path):
                data_dict[key] = load_csv(csv_path)
        
        # Save the data to the JSON file
        save_json(data_dict, json_filepath)
        return True
    except Exception as e:
        print(f"Failed to update JSON file {json_filepath}: {str(e)}")
        return False 