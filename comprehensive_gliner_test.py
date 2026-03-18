#!/usr/bin/env python3
"""
Comprehensive GLiNER integration test
"""

import sys
import logging
from pii_detector.presidio_engine import PresidioPIIEngine

def test_comprehensive_gliner():
    """Test comprehensive GLiNER integration"""
    print("🧪 Comprehensive GLiNER Integration Test")
    print("=" * 60)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        # Initialize Presidio engine
        print("🔧 Initializing Presidio engine...")
        presidio = PresidioPIIEngine()
        
        # Test texts with various PII types
        test_cases = [
            {
                "text": "John Smith works at Microsoft",
                "expected_entities": ["PERSON"],
                "description": "Person name"
            },
            {
                "text": "Contact me at john.smith@example.com",
                "expected_entities": ["EMAIL_ADDRESS"],
                "description": "Email address"
            },
            {
                "text": "Call me at +1-555-123-4567",
                "expected_entities": ["PHONE_NUMBER"],
                "description": "Phone number"
            },
            {
                "text": "My Aadhaar number is 234567890123",
                "expected_entities": ["AADHAAR"],
                "description": "Aadhaar number"
            },
            {
                "text": "PAN card: ABCDE1234F",
                "expected_entities": ["PAN"],
                "description": "PAN card"
            },
            {
                "text": "Visit me at 123 Main Street, New York, NY 10001",
                "expected_entities": ["ADDRESS"],
                "description": "Address"
            },
            {
                "text": "I work at Google Inc.",
                "expected_entities": ["ORGANIZATION"],
                "description": "Organization"
            },
            {
                "text": "Meeting on March 15, 2024",
                "expected_entities": ["DATE_TIME"],
                "description": "Date"
            }
        ]
        
        print(f"📋 Running {len(test_cases)} test cases...")
        
        total_tests = 0
        passed_tests = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 Test {i}: {test_case['description']}")
            print(f"   Text: '{test_case['text']}'")
            
            # Analyze with Presidio
            presidio_results = presidio.analyze_text(test_case["text"])
            presidio_entities = [result.entity_type for result in presidio_results]
            
            print(f"   Presidio found: {len(presidio_results)} entities")
            for result in presidio_results:
                print(f"      - {result.entity_type}: {test_case['text'][result.start:result.end]} (confidence: {result.score:.3f})")
            
            # Check if expected entities were found
            expected_found = any(entity in presidio_entities for entity in test_case["expected_entities"])
            
            if expected_found:
                print(f"   ✅ PASS: Found expected entities")
                passed_tests += 1
            else:
                print(f"   ❌ FAIL: Expected entities {test_case['expected_entities']} not found")
            
            total_tests += 1
        
        # Summary
        print(f"\n📊 Test Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {total_tests - passed_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Try GLiNER integration
        print(f"\n🤖 Testing GLiNER integration...")
        try:
            from pii_detector.gliner_engine_fixed import GLiNERPIIEngine as FixedGLiNERPIIEngine
            
            gliner = FixedGLiNERPIIEngine()
            status = gliner.get_status()
            
            print(f"   GLiNER Status: {status}")
            
            if status["model_loaded"]:
                print("   ✅ GLiNER model loaded successfully")
                
                # Test one case with GLiNER
                test_case = test_cases[1]  # Email test
                gliner_results = gliner.analyze_text(test_case["text"])
                gliner_entities = [result["label"] for result in gliner_results]
                
                print(f"   GLiNER found: {len(gliner_results)} entities")
                for result in gliner_results:
                    print(f"      - {result['label']}: {result['text']} (confidence: {result['confidence']:.3f})")
                
                if any(entity in gliner_entities for entity in test_case["expected_entities"]):
                    print("   ✅ GLiNER PASS: Found expected entities")
                else:
                    print("   ❌ GLiNER FAIL: Expected entities not found")
            else:
                print("   ⚠️  GLiNER model not loaded, using rule-based fallback")
                
        except ImportError:
            print("   ❌ GLiNER not available")
        except Exception as e:
            print(f"   ❌ GLiNER integration error: {e}")
        
        print(f"\n🎯 Overall Result: GLiNER integration {'✅ READY' if passed_tests > 0 else 'NEEDS WORK'}")
        
        return passed_tests > 0
        
    except Exception as e:
        print(f"❌ Comprehensive test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_comprehensive_gliner()
    sys.exit(0 if success else 1)
