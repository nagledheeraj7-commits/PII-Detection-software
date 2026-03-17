"""
Presidio Engine - Simple Version without NLP regex issues
"""

import logging
from typing import List, Dict, Any

def safe_string(value) -> str:
    """
    Convert any value to a safe string for Presidio analysis
    
    Args:
        value: Any value to convert
        
    Returns:
        Safe string representation
    """
    if value is None:
        return ""
    
    if isinstance(value, dict):
        # Convert dict to string by joining values
        return " ".join(str(v) for v in value.values() if v is not None)
    
    if isinstance(value, list):
        # Convert list to string by joining elements
        return " ".join(str(v) for v in value if v is not None)
    
    # Handle pandas NaN/NaT values
    try:
        import pandas as pd
        if pd.isna(value):
            return ""
    except ImportError:
        pass
    
    # Convert any other type to string
    return str(value).strip()

try:
    from presidio_analyzer import AnalyzerEngine, PatternRecognizer, RecognizerResult
    from presidio_analyzer.nlp_engine import NlpEngineProvider
    from presidio_analyzer.recognizer_registry import RecognizerRegistry
    from presidio_anonymizer import AnonymizerEngine
    PRESIDIO_AVAILABLE = True
except ImportError as e:
    PRESIDIO_AVAILABLE = False
    print(f"⚠️  Presidio not available: {e}")
    AnalyzerEngine = None
    PatternRecognizer = None
    RecognizerResult = None
    NlpEngineProvider = None
    RecognizerRegistry = None
    AnonymizerEngine = None


class SimplePresidioPIIEngine:
    """
    Simplified Presidio-based PII detection engine that avoids regex attribute errors
    """
    
    def __init__(self):
        """Initialize Presidio engine with minimal NLP features"""
        if not PRESIDIO_AVAILABLE:
            raise ImportError("Presidio is not available")
        
        self.analyzer = self._setup_simple_analyzer()
        self.anonymizer = AnonymizerEngine()
    
    def _setup_simple_analyzer(self) -> AnalyzerEngine:
        """Setup analyzer with minimal NLP to avoid regex errors"""
        try:
            # Create registry with only pattern recognizers (no NLP)
            registry = RecognizerRegistry()
            
            # Add only pattern-based recognizers (no spaCy/NLP)
            registry.load_predefined_recognizers()
            
            # Add custom Indian PII recognizers
            aadhaar_recognizer = self._create_aadhaar_recognizer()
            pan_recognizer = self._create_pan_recognizer()
            indian_phone_recognizer = self._create_indian_phone_recognizer()
            
            registry.add_recognizer(aadhaar_recognizer)
            registry.add_recognizer(pan_recognizer)
            registry.add_recognizer(indian_phone_recognizer)
            
            # Use simple NLP configuration without spaCy
            nlp_configuration = {
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}]
            }
            
            provider = NlpEngineProvider(nlp_configuration=nlp_configuration)
            
            # Create analyzer
            analyzer = AnalyzerEngine(
                registry=registry,
                nlp_engine=provider.create_nlp_engine(),
                app_languages=["en"]
            )
            
            logging.info("Simple Presidio analyzer setup completed successfully")
            return analyzer
            
        except Exception as e:
            logging.error(f"Error setting up simple Presidio analyzer: {e}")
            # Fallback to basic analyzer without NLP
            return self._create_fallback_analyzer()
    
    def _create_fallback_analyzer(self) -> AnalyzerEngine:
        """Create a fallback analyzer with only pattern recognizers"""
        try:
            registry = RecognizerRegistry()
            
            # Add only our custom recognizers
            aadhaar_recognizer = self._create_aadhaar_recognizer()
            pan_recognizer = self._create_pan_recognizer()
            indian_phone_recognizer = self._create_indian_phone_recognizer()
            
            registry.add_recognizer(aadhaar_recognizer)
            registry.add_recognizer(pan_recognizer)
            registry.add_recognizer(indian_phone_recognizer)
            
            # Create analyzer without app_languages parameter
            analyzer = AnalyzerEngine(registry=registry)
            
            logging.info("Fallback Presidio analyzer created successfully")
            return analyzer
            
        except Exception as e:
            logging.error(f"Error creating fallback analyzer: {e}")
            raise
    
    def _create_aadhaar_recognizer(self) -> PatternRecognizer:
        """Create Aadhaar number recognizer (12 digits)"""
        aadhaar_pattern = r"\\b[2-9]\\d{11}\\b"
        return PatternRecognizer(
            supported_entity="AADHAAR",
            name="Aadhaar Recognizer",
            patterns=[{"pattern": aadhaar_pattern, "score": 0.9}],
            context=["aadhaar", "uid", "unique identification"]
        )
    
    def _create_pan_recognizer(self) -> PatternRecognizer:
        """Create PAN card recognizer (ABCDE1234F format)"""
        pan_pattern = r"\\b[A-Z]{5}\\d{4}[A-Z]\\b"
        return PatternRecognizer(
            supported_entity="PAN",
            name="PAN Recognizer",
            patterns=[{"pattern": pan_pattern, "score": 0.95}],
            context=["pan", "permanent account number", "tax"]
        )
    
    def _create_indian_phone_recognizer(self) -> PatternRecognizer:
        """Create Indian phone number recognizer"""
        phone_patterns = [
            r"\\+91[6-9]\\d{9}",  # +91 followed by 10 digits starting with 6-9
            r"0[6-9]\\d{9}",     # 0 followed by 10 digits starting with 6-9
            r"[6-9]\\d{9}",      # 10 digits starting with 6-9
            r"\\b\\d{5}[-\\s]?\\d{5}\\b"  # XXXXX-XXXXX or XXXXX XXXXX format
        ]
        
        patterns = [{"pattern": pattern, "score": 0.8} for pattern in phone_patterns]
        
        return PatternRecognizer(
            supported_entity="PHONE_NUMBER",
            name="Indian Phone Recognizer",
            patterns=patterns,
            context=["phone", "mobile", "contact", "call"]
        )
    
    def analyze_text(self, text: str, language: str = "en") -> List[RecognizerResult]:
        """
        Analyze text for PII entities with comprehensive error handling
        
        Args:
            text: Text to analyze (any type)
            language: Language code (default: 'en')
            
        Returns:
            List of recognizer results
        """
        # Convert any input to safe string
        text = safe_string(text)
        
        if not text:
            return []
        
        try:
            # Use analyze method with minimal NLP features
            results = self.analyzer.analyze(
                text=text,
                language=language
            )
            
            # Filter and validate results
            valid_results = []
            for result in results:
                try:
                    # Check if result has required attributes
                    if (hasattr(result, 'entity_type') and 
                        hasattr(result, 'start') and 
                        hasattr(result, 'end') and 
                        hasattr(result, 'score')):
                        
                        # Validate attribute values
                        entity_type = getattr(result, 'entity_type', None)
                        start = getattr(result, 'start', None)
                        end = getattr(result, 'end', None)
                        score = getattr(result, 'score', None)
                        
                        # Only include if all attributes are valid
                        if (entity_type is not None and 
                            start is not None and 
                            end is not None and 
                            score is not None):
                            
                            valid_results.append(result)
                        else:
                            logging.warning(f"Invalid entity attributes found, skipping")
                    else:
                        logging.warning(f"Result missing required attributes, skipping")
                        
                except Exception as e:
                    logging.warning(f"Error processing result: {e}, skipping")
                    continue
            
            return valid_results
            
        except Exception as e:
            logging.error(f"Error analyzing text: {e}")
            return []
    
    def get_supported_entities(self) -> List[str]:
        """Get list of supported PII entities"""
        try:
            return self.analyzer.get_supported_entities()
        except Exception as e:
            logging.error(f"Error getting supported entities: {e}")
            return ["AADHAAR", "PAN", "PHONE_NUMBER"]  # Return our custom entities
    
    def is_pii(self, text: str, language: str = "en") -> tuple[bool, List[str]]:
        """
        Check if text contains any PII
        
        Args:
            text: Text to check
            language: Language code
            
        Returns:
            Tuple of (has_pii, pii_types)
        """
        results = self.analyze_text(text, language)
        pii_types = list(set([result.entity_type for result in results]))
        return len(results) > 0, pii_types
