#!/usr/bin/env python3
"""
Python Version Checker for PII Detection Project
"""

import sys
import subprocess
import platform

def check_python_version():
    """Check if Python version is compatible"""
    version_info = sys.version_info
    version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    
    print(f"Current Python version: {version_str}")
    print(f"Platform: {platform.system()}")
    
    # Check if version is compatible
    if version_info.major == 3 and 10 <= version_info.minor <= 11:
        print("✅ Python version is compatible!")
        return True
    elif version_info.major == 3 and version_info.minor >= 12:
        print("⚠️  Python 3.12+ detected. This may cause compatibility issues.")
        print("   Recommended: Python 3.10 or 3.11")
        print("   You can continue, but some dependencies might fail to install.")
        return False
    else:
        print("❌ Python version is not supported!")
        print("   Required: Python 3.10 or 3.11")
        print("   Please install a compatible Python version from https://python.org")
        return False

def check_pip():
    """Check if pip is available"""
    try:
        import pip
        print("✅ pip is available")
        return True
    except ImportError:
        print("❌ pip is not available")
        return False

def check_virtual_env():
    """Check if we're in a virtual environment"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Running in virtual environment")
        return True
    else:
        print("⚠️  Not in virtual environment")
        return False

def main():
    """Main check function"""
    print("🔍 PII Detection Project - Environment Check")
    print("=" * 50)
    
    # Check Python version
    python_ok = check_python_version()
    
    # Check pip
    pip_ok = check_pip()
    
    # Check virtual environment
    venv_ok = check_virtual_env()
    
    print("\n" + "=" * 50)
    
    if python_ok and pip_ok:
        print("🎉 Environment is ready for setup!")
        if not venv_ok:
            print("💡 Tip: Consider using a virtual environment")
        
        print("\nNext steps:")
        print("1. Run setup.bat (Windows) or ./setup.sh (Linux/macOS)")
        print("2. Or manually: pip install -r requirements.txt")
        print("3. Then: python -m spacy download en_core_web_sm")
    else:
        print("❌ Environment needs attention before setup")
        if not python_ok:
            print("   - Install Python 3.10 or 3.11")
        if not pip_ok:
            print("   - Install pip or ensure it's in PATH")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
