#!/bin/bash

echo "========================================"
echo "PII Detection Software Setup"
echo "========================================"

# Check Python version
echo "Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "ERROR: Python3 is not installed"
    echo "Please install Python 3.10 or 3.11"
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Removing old one..."
    rm -rf venv
fi
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi

# Upgrade pip
echo ""
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements
echo ""
echo "Installing requirements..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install requirements"
    exit 1
fi

# Download spaCy model
echo ""
echo "Downloading spaCy model..."
python -m spacy download en_core_web_sm
if [ $? -ne 0 ]; then
    echo "WARNING: Failed to download spaCy model"
    echo "You may need to run: python -m spacy download en_core_web_sm manually"
fi

echo ""
echo "========================================"
echo "Setup completed successfully!"
echo "========================================"
echo ""
echo "To run the PII detection tool:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run analysis: python main.py -i sample_data/test_data.csv -o report.json"
echo ""
echo "To deactivate virtual environment: deactivate"
