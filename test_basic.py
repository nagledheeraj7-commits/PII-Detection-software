#!/usr/bin/env python3
"""
Basic test script to verify project structure and basic functionality
"""

import pandas as pd
import sys
from pathlib import Path

def test_basic_functionality():
    """Test basic CSV reading and project structure"""
    print("🧪 Testing Basic PII Detection Functionality")
    print("=" * 50)
    
    # Test project structure
    print("📁 Checking project structure...")
    required_files = [
        "main.py",
        "requirements.txt",
        "README.md",
        "pii_detector/__init__.py",
        "pii_detector/presidio_engine.py",
        "pii_detector/gliner_engine.py",
        "pii_detector/utils.py",
        "pii_detector/report_generator.py",
        "sample_data/test_data.csv"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
    
    # Test CSV reading
    print("\n📊 Testing CSV reading...")
    try:
        df = pd.read_csv("sample_data/test_data.csv")
        print(f"✅ Successfully loaded CSV: {df.shape} (rows x columns)")
        print(f"   Columns: {list(df.columns)}")
        
        # Show first few rows
        print("\n📋 Sample data preview:")
        print(df.head(3).to_string(index=False))
        
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return False
    
    # Test basic text analysis (without ML models)
    print("\n🔍 Testing basic PII patterns...")
    
    # Simple regex patterns for testing
    import re
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    phone_pattern = r'^[\+]?[0-9\s\-\(\)]{10,}$'
    aadhaar_pattern = r'^[2-9]\d{11}$'
    pan_pattern = r'^[A-Z]{5}\d{4}[A-Z]$'
    
    # Test sample data
    test_emails = df['email'].dropna().head()
    test_phones = df['phone'].dropna().head()
    test_aadhaars = df['aadhaar'].dropna().head()
    test_pans = df['pan'].dropna().head()
    
    print(f"\n📧 Email detection test:")
    for email in test_emails:
        is_email = bool(re.match(email_pattern, str(email)))
        print(f"   {email}: {'✅' if is_email else '❌'}")
    
    print(f"\n📞 Phone detection test:")
    for phone in test_phones:
        is_phone = bool(re.match(phone_pattern, str(phone)))
        print(f"   {phone}: {'✅' if is_phone else '❌'}")
    
    print(f"\n🆔 Aadhaar detection test:")
    for aadhaar in test_aadhaars:
        if pd.notna(aadhaar):
            is_aadhaar = bool(re.match(aadhaar_pattern, str(aadhaar)))
            print(f"   {aadhaar}: {'✅' if is_aadhaar else '❌'}")
    
    print(f"\n💳 PAN detection test:")
    for pan in test_pans:
        if pd.notna(pan):
            is_pan = bool(re.match(pan_pattern, str(pan)))
            print(f"   {pan}: {'✅' if is_pan else '❌'}")
    
    print("\n" + "=" * 50)
    print("🎉 Basic functionality test completed!")
    print("📝 Note: Full ML model testing requires proper dependency setup")
    print("🔧 To run full PII detection:")
    print("   pip install -r requirements.txt")
    print("   python main.py -i sample_data/test_data.csv -o test_report.json")
    
    return True

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)
