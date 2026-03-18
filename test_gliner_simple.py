#!/usr/bin/env python3
"""
Simple GLiNER test with correct model names
"""

import sys
import logging
from pii_detector.gliner_engine import GLiNERPIIEngine

def test_gliner_models():
    """Test different GLiNER models"""
    print("🧪 Testing GLiNER Models")
    print("=" * 50)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Test different model names
    models_to_test = [
        "gliner_base",
        "gliner_medium",
        "gliner_small",
        "urchade/gliner_base",
        "urchade/gliner_medium"
    ]
    
    for model_name in models_to_test:
        print(f"\n🔍 Testing model: {model_name}")
        
        try:
            # Initialize GLiNER engine
            gliner = GLiNERPIIEngine(model_name)
            
            # Check status
            status = gliner.get_status()
            print(f"   Status: {status}")
            
            if gliner.is_loaded:
                # Test with sample text
                test_text = "John Smith works at Microsoft and his email is john.smith@example.com"
                print(f"   Testing: '{test_text}'")
                
                entities = gliner.analyze_text(test_text)
                if entities:
                    print(f"   ✅ Found {len(entities)} entities:")
                    for entity in entities:
                        print(f"      - {entity['label']}: {entity['text']} (confidence: {entity['confidence']})")
                else:
                    print("   ❌ No entities found")
                
                print("   ✅ Model works!")
                return True
            else:
                print("   ❌ Model failed to load")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n❌ All models failed!")
    return False

if __name__ == "__main__":
    success = test_gliner_models()
    sys.exit(0 if success else 1)
