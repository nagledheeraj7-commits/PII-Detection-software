# Installation Guide

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

**Windows Users:**
```cmd
setup.bat
```

**Linux/macOS Users:**
```bash
chmod +x setup.sh
./setup.sh
```

### Option 2: Manual Setup

#### Step 1: Check Python Version
```bash
python --version
# Should show Python 3.10.x or 3.11.x
```

If you have Python 3.12+, install Python 3.10 or 3.11 from [python.org](https://python.org)

#### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/macOS)
source venv/bin/activate
```

#### Step 3: Install Dependencies
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

#### Step 4: Download spaCy Model
```bash
python -m spacy download en_core_web_sm
```

#### Step 5: Test Installation
```bash
python main.py --help
```

## 🔧 Troubleshooting

### Common Issues and Solutions

**Issue: "Failed to build spacy" or "numpy build error"**
- **Solution**: Use Python 3.10 or 3.11 (not 3.12+)
- **Alternative**: `pip install --only-binary=all -r requirements.txt`

**Issue: "gcc/clang not found"**
- **Solution**: Use the automated setup script (it handles this)
- **Alternative**: Install Visual Studio Build Tools (Windows)

**Issue: "pip not found"**
- **Solution**: Ensure Python is installed and in PATH
- **Alternative**: Use `python -m pip` instead of `pip`

**Issue: "virtual environment activation fails"**
- **Solution**: Run Command Prompt as Administrator (Windows)
- **Alternative**: Use PowerShell instead of CMD

**Issue: "spaCy model download fails"**
- **Solution**: Run after activating virtual environment
- **Alternative**: `pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1.tar.gz`

## ✅ Verification

After installation, test with sample data:

```bash
# Basic test
python main.py -i sample_data/test_data.csv -o test_report.json

# With CSV output
python main.py -i sample_data/test_data.csv -o test_report.json -c test_reports/

# Anonymization test
python main.py -i sample_data/test_data.csv -o test_report.json --anonymize anonymized_test.csv
```

If all commands work without errors, installation is successful!

## 📋 Requirements Summary

- **Python**: 3.10 or 3.11 (recommended)
- **OS**: Windows 10+, macOS 10.14+, Linux
- **Memory**: 4GB+ RAM (8GB recommended for large files)
- **Storage**: 2GB free space for dependencies

## 🆘 Still Having Issues?

1. Check Python version: `python --version`
2. Use clean virtual environment
3. Run automated setup script
4. Check internet connection (for model downloads)
5. Try different Python version if needed

For additional help, check the main README.md file.
