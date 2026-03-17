"""
Presidio Engine - Fixed Version with comprehensive error handling
"""

import re
import logging
from typing import List, Dict, Any

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


class PresidioPIIEngine:
    """
    Presidio-based PII detection engine with Indian-specific recognizers
    """
    
    def __init__(self):
        """Initialize Presidio engine"""
        if not PRESIDIO_AVAILABLE:
            raise ImportError("Presidio is not available")
        
        self.analyzer = self._setup_analyzer()
        self.anonymizer = AnonymizerEngine()
    
    def _setup_analyzer(self) -> AnalyzerEngine:
        """Setup analyzer with custom recognizers"""
        try:
            # Create registry
            registry = RecognizerRegistry()
            
            # Add default recognizers
            registry.load_predefined_recognizers()
            
            # Add custom Indian PII recognizers
            aadhaar_recognizer = self._create_aadhaar_recognizer()
            pan_recognizer = self._create_pan_recognizer()
            indian_phone_recognizer = self._create_indian_phone_recognizer()
            
            registry.add_recognizer(aadhaar_recognizer)
            registry.add_recognizer(pan_recognizer)
            registry.add_recognizer(indian_phone_recognizer)
            
            # Setup NLP engine
            provider = NlpEngineProvider()
            
            # Create analyzer
            analyzer = AnalyzerEngine(
                registry=registry,
                nlp_engine=provider,
                app_languages=["en"]
            )
            
            logging.info("Presidio analyzer setup completed successfully")
            return analyzer
            
        except Exception as e:
            logging.error(f"Error setting up Presidio analyzer: {e}")
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
        # Indian phone patterns: +91XXXXXXXXXX, 0XXXXXXXXXX, XXXXX-XXXXX
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
            text: Text to analyze
            language: Language code (default: 'en')
            
        Returns:
            List of recognizer results
        """
        if not text or not isinstance(text, str):
            return []
        
        try:
            # Ensure text is a clean string
            text = str(text).strip()
            
            # Use the correct analyze method
            results = self.analyzer.analyze(
                text=text,
                language=language,
                return_decision_process=True
            )
            
            # Validate and filter results to prevent attribute errors
            valid_results = []
            for result in results:
                try:
                    # Check if result has required attributes
                    if (hasattr(result, 'entity_type') and 
                        hasattr(result, 'start') and 
                        hasattr(result, 'end') and 
                        hasattr(result, 'score')):
                        
                        # Validate attribute types
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
                            logging.debug(f"Valid entity found: {entity_type} at {start}-{end}")
                        else:
                            logging.warning(f"Invalid entity attributes found, skipping")
                    else:
                        logging.warning(f"Result missing required attributes, skipping: {result}")
                        
                except Exception as e:
                    logging.warning(f"Error processing result: {e}, skipping")
                    continue
            
            return valid_results
            
        except Exception as e:
            logging.error(f"Error analyzing text with Presidio: {e}")
            return []
    
    def anonymize_text(self, text: str, analyzer_results: List[RecognizerResult]) -> str:
        """
        Anonymize text based on analyzer results
        
        Args:
            text: Text to anonymize
            analyzer_results: Results from analyze_text
            
        Returns:
            Anonymized text
        """
        if not text or not analyzer_results:
            return text
        
        try:
            # Validate analyzer results
            valid_results = []
            for result in analyzer_results:
                if (hasattr(result, 'entity_type') and 
                    hasattr(result, 'start') and 
                    hasattr(result, 'end') and 
                    hasattr(result, 'score')):
                    valid_results.append(result)
            
            anonymized_result = self.anonymizer.anonymize(
                text=text,
                analyzer_results=valid_results
            )
            return anonymized_result.text
            
        except Exception as e:
            logging.error(f"Error anonymizing text: {e}")
            return text
    
    def get_supported_entities(self) -> List[str]:
        """Get list of supported PII entities"""
        try:
            return self.analyzer.get_supported_entities()
        except Exception as e:
            logging.error(f"Error getting supported entities: {e}")
            return []
    
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
    
    def get_pii_summary(self, text: str, language: str = "en") -> Dict[str, Any]:
        """
        Get PII summary for text
        
        Args:
            text: Text to analyze
            language: Language code
            
        Returns:
            Dictionary with PII summary
        """
        results = self.analyze_text(text, language)
        
        if not results:
            return {
                "has_pii": False,
                "pii_types": [],
                "entities": [],
                "confidence_scores": []
            }
        
        pii_types = list(set([result.entity_type for result in results]))
        confidence_scores = [result.score for result in results]
        
        return {
            "has_pii": True,
            "pii_types": pii_types,
            "entities": results,
            "confidence_scores": confidence_scores,
            "avg_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        }
