#!/usr/bin/env python3
"""
Debug test to isolate the regex issue
"""

import sys
import logging
from pii_detector.presidio_engine import PresidioPIIEngine

def test_presidio_only():
    """Test Presidio engine only"""
    print("🧪 Testing Presidio Engine Only")
    print("=" * 50)
    
    # Setup logging
    logging.basicConfig(level=logging.DEBUG)
    
    try:
        # Initialize Presidio engine
        print("1. Initializing Presidio engine...")
        presidio = PresidioPIIEngine()
        
        # Test with sample text
        test_text = "John Smith works at Microsoft and his email is john.smith@example.com"
        print(f"2. Testing: '{test_text}'")
        
        # Analyze text
        results = presidio.analyze_text(test_text)
        print(f"3. Results: {len(results)} entities found")
        
        for i, result in enumerate(results):
            print(f"   Entity {i+1}: {result.entity_type} - {test_text[result.start:result.end]} (confidence: {result.score})")
        
        print("✅ Presidio test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during Presidio test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_presidio_only()
    sys.exit(0 if success else 1)
