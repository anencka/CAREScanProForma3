#!/bin/bash

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "Streamlit is not installed. Installing required dependencies..."
    pip install -r requirements.txt
fi

# Run the Streamlit app
echo "Starting CAREScan ProForma Editor..."
streamlit run app.py 