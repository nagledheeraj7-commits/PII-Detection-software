#!/usr/bin/env python3
"""
Test GLiNER integration specifically
"""

import sys
import logging
from pii_detector.gliner_engine import GLiNERPIIEngine

def test_gliner():
    """Test GLiNER engine functionality"""
    print("🧪 Testing GLiNER Integration")
    print("=" * 50)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Initialize GLiNER engine
        print("1. Initializing GLiNER engine...")
        gliner = GLiNERPIIEngine("urchade/gliner_base")
        
        # Check status
        status = gliner.get_status()
        print(f"GLiNER Status: {status}")
        
        if not gliner.is_loaded:
            print("❌ GLiNER failed to load - cannot proceed with tests")
            return False
        
        # Test with sample text
        test_texts = [
            "John Smith's email is john.smith@example.com",
            "Call me at +1-555-123-4567 for details",
            "My Aadhaar number is 234567890123",
            "PAN card: ABCDE1234F",
            "I work at Microsoft Corporation"
        ]
        
        print("\n2. Testing entity detection...")
        for i, text in enumerate(test_texts, 1):
            print(f"\nTest {i}: {text}")
            entities = gliner.analyze_text(text)
            
            if entities:
                print(f"   ✅ Found {len(entities)} entities:")
                for entity in entities:
                    print(f"      - {entity['label']}: {entity['text']} (confidence: {entity['confidence']})")
            else:
                print("   ❌ No entities found")
        
        # Test PII detection
        print("\n3. Testing PII detection...")
        for i, text in enumerate(test_texts, 1):
            has_pii, pii_types = gliner.is_pii(text)
            print(f"Test {i}: {text}")
            print(f"   PII detected: {has_pii}")
            print(f"   PII types: {pii_types}")
        
        # Test summary
        print("\n4. Testing PII summary...")
        summary = gliner.get_pii_summary(test_texts[0])
        print(f"Summary for first test text:")
        print(f"   Has PII: {summary['has_pii']}")
        print(f"   PII types: {summary['pii_types']}")
        print(f"   Avg confidence: {summary['avg_confidence']}")
        
        print("\n✅ GLiNER integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during GLiNER test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gliner()
    sys.exit(0 if success else 1)
