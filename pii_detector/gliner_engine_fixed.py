"""
GLiNER Engine for Generalized Named Entity Recognition - Fixed Version
"""

import logging
from typing import List, Dict, Any, Tuple

try:
    from gliner import GLiNER
    GLINER_AVAILABLE = True
except ImportError:
    GLINER_AVAILABLE = False
    GLiNER = None


class GLiNERPIIEngine:
    """
    GLiNER-based PII detection engine for additional entity detection
    """
    
    def __init__(self, model_name: str = "urchade/gliner_medium-v2.1"):
        """
        Initialize GLiNER PII Engine
        
        Args:
            model_name: Name of the GLiNER model to use
        """
        self.model_name = model_name
        self.model = None
        self.is_loaded = False
        self.using_fallback = False
        
        # Load model on initialization
        self.load_model()
        
        # Add debug log
        if self.is_loaded:
            logging.info("GLiNER model loaded successfully")
            print("GLiNER model loaded successfully")
        elif self.using_fallback:
            logging.info("GLiNER using rule-based fallback")
            print("GLiNER using rule-based fallback")
        else:
            logging.warning("GLiNER failed to load completely")
            print("GLiNER failed to load completely")
    
    def load_model(self):
        """Load GLiNER model with proper error handling"""
        if not GLINER_AVAILABLE:
            logging.error("GLiNER is not available. Install with: pip install gliner")
            self.model = None
            self.is_loaded = False
            return
        
        try:
            logging.info(f"Loading GLiNER model: {self.model_name}")
            print(f"Loading GLiNER model: {self.model_name}")
            
            # Try to load model with minimal parameters to avoid auth issues
            try:
                # Try loading from local cache first
                self.model = GLiNER.from_pretrained(
                    self.model_name,
                    local_files_only=True
                )
                self.is_loaded = True
                logging.info("GLiNER model loaded from cache")
                print("GLiNER model loaded from cache")
            except Exception as cache_error:
                logging.warning(f"Cache loading failed: {cache_error}")
                print(f"Cache loading failed, trying network...")
                
                try:
                    # Try with network (may require auth)
                    self.model = GLiNER.from_pretrained(
                        self.model_name,
                        local_files_only=False
                    )
                    self.is_loaded = True
                    logging.info("GLiNER model loaded from network")
                    print("GLiNER model loaded from network")
                except Exception as network_error:
                    logging.error(f"Network loading failed: {network_error}")
                    print(f"Network loading failed: {network_error}")
                    logging.warning("Using rule-based fallback for GLiNER")
                    print("Using rule-based fallback for GLiNER")
                    self.model = None
                    self.is_loaded = False
                    logging.warning("Using rule-based fallback for GLiNER")
                    print("Using rule-based fallback for GLiNER")
                
        except Exception as e:
            logging.error(f"Error loading GLiNER model: {e}")
            print(f"Error loading GLiNER model: {e}")
            self.model = None
            self.is_loaded = False
    
    def analyze_text(self, text: str, labels: List[str] = None) -> List[Dict[str, Any]]:
        """
        Analyze text for entities using GLiNER
        
        Args:
            text: Text to analyze
            labels: List of entity labels to detect
            
        Returns:
            List of detected entities
        """
        if not text or not isinstance(text, str):
            return []
        
        # If model not loaded, use rule-based fallback
        if not self.is_loaded or not self.model:
            return self._rule_based_analysis(text, labels)
        
        # Default PII labels if none provided
        if labels is None:
            labels = [
                "person", "name", "email", "phone number", "address", "location",
                "organization", "company", "id", "identifier", "number",
                "date", "birth date", "age", "gender", "title", "profession"
            ]
        
        try:
            # Run GLiNER prediction
            logging.debug(f"Analyzing text with GLiNER: {text[:50]}...")
            entities = self.model.predict_entities(text, labels)
            
            # Convert to standard format
            results = []
            for entity in entities:
                # Handle both dict and object formats safely
                try:
                    if isinstance(entity, dict):
                        entity_dict = entity
                    else:
                        # Handle object format
                        entity_dict = {
                            "text": str(getattr(entity, "text", "")),
                            "label": str(getattr(entity, "label", "")),
                            "start": int(getattr(entity, "start", 0)),
                            "end": int(getattr(entity, "end", 0)),
                            "score": float(getattr(entity, "score", 0.0))
                        }
                except Exception as format_error:
                    logging.warning(f"Error formatting entity: {format_error}")
                    print(f"⚠️  Error formatting entity: {format_error}")
                    continue
                
                if entity_dict:  # Only append if we successfully formatted the entity
                    results.append({
                        "text": entity_dict.get("text", ""),
                        "label": entity_dict.get("label", ""),
                        "start": entity_dict.get("start", 0),
                        "end": entity_dict.get("end", 0),
                        "confidence": entity_dict.get("score", 0.0)
                    })
            
            if results:
                logging.info(f"🎯 GLiNER detected {len(results)} entities")
                print(f"🎯 GLiNER detected {len(results)} entities")
                for i, result in enumerate(results):
                    logging.debug(f"  Entity {i+1}: {result['label']} - {result['text']} (confidence: {result['confidence']})")
            else:
                logging.debug("GLiNER detected no entities")
            
            return results
            
        except Exception as e:
            logging.error(f"❌ Error analyzing text with GLiNER: {e}")
            print(f"❌ Error analyzing text with GLiNER: {e}")
            # Fallback to rule-based analysis
            return self._rule_based_analysis(text, labels)
    
    def _rule_based_analysis(self, text: str, labels: List[str] = None) -> List[Dict[str, Any]]:
        """Rule-based analysis as fallback when GLiNER model is not available"""
        import re
        
        if labels is None:
            labels = ["person", "name", "email", "phone number", "address", "organization"]
        
        results = []
        text_lower = text.lower()
        
        # Simple regex patterns for common PII
        patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b[\+]?[0-9\s\-\(\)]{10,}\b',
            "person": r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
        }
        
        for label in labels:
            if label in patterns and re.search(patterns[label], text):
                match = re.search(patterns[label], text)
                results.append({
                    "text": match.group(),
                    "label": label,
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.7  # Lower confidence for rule-based
                })
        
        if results:
            logging.info(f"🔧 Rule-based detected {len(results)} entities")
            print(f"🔧 Rule-based detected {len(results)} entities")
        
        return results
    
    def is_pii(self, text: str, labels: List[str] = None) -> Tuple[bool, List[str]]:
        """
        Check if text contains any PII entities
        
        Args:
            text: Text to check
            labels: List of entity labels to detect
            
        Returns:
            Tuple of (has_pii, pii_types)
        """
        entities = self.analyze_text(text, labels)
        pii_types = list(set([entity["label"] for entity in entities]))
        return len(entities) > 0, pii_types
    
    def get_pii_summary(self, text: str, labels: List[str] = None) -> Dict[str, Any]:
        """
        Get PII summary for text using GLiNER
        
        Args:
            text: Text to analyze
            labels: List of entity labels to detect
            
        Returns:
            Dictionary with PII summary
        """
        entities = self.analyze_text(text, labels)
        
        if not entities:
            return {
                "has_pii": False,
                "pii_types": [],
                "entities": [],
                "confidence_scores": []
            }
        
        pii_types = list(set([entity["label"] for entity in entities]))
        confidence_scores = [entity["confidence"] for entity in entities]
        
        return {
            "has_pii": True,
            "pii_types": pii_types,
            "entities": entities,
            "confidence_scores": confidence_scores,
            "avg_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        }
    
    def map_to_presidio_entities(self, gliner_labels: List[str]) -> List[str]:
        """
        Map GLiNER labels to Presidio entity types
        
        Args:
            gliner_labels: List of GLiNER entity labels
            
        Returns:
            List of mapped Presidio entity types
        """
        # Mapping dictionary
        label_mapping = {
            "person": "PERSON",
            "name": "PERSON",
            "email": "EMAIL_ADDRESS",
            "phone number": "PHONE_NUMBER",
            "phone": "PHONE_NUMBER",
            "address": "ADDRESS",
            "location": "LOCATION",
            "organization": "ORGANIZATION",
            "company": "ORGANIZATION",
            "id": "ID",
            "identifier": "ID",
            "number": "ID",
            "date": "DATE_TIME",
            "birth date": "DATE_TIME",
            "age": "AGE",
            "gender": "GENDER",
            "title": "TITLE",
            "profession": "PROFESSION"
        }
        
        mapped_entities = []
        for label in gliner_labels:
            mapped_entity = label_mapping.get(label.lower(), label.upper())
            mapped_entities.append(mapped_entity)
        
        return mapped_entities
    
    def combine_with_presidio(self, presidio_results: List[Dict], gliner_results: List[Dict]) -> List[Dict]:
        """
        Combine GLiNER results with Presidio results
        
        Args:
            presidio_results: Results from Presidio engine
            gliner_results: Results from GLiNER engine
            
        Returns:
            Combined results
        """
        if not presidio_results and not gliner_results:
            return []
        
        if not presidio_results:
            # Only GLiNER results
            combined = []
            for entity in gliner_results:
                mapped_label = self.map_to_presidio_entities([entity["label"]])[0]
                combined.append({
                    "type": mapped_label,
                    "start": entity["start"],
                    "end": entity["end"],
                    "value": entity["text"],
                    "confidence": entity["confidence"],
                    "source": "gliner"
                })
            return combined
        
        if not gliNER_results:
            # Only Presidio results
            return presidio_results.copy()
        
        combined = presidio_results.copy()
        
        # Map GLiNER labels to Presidio entities
        for entity in gliner_results:
            mapped_label = self.map_to_presidio_entities([entity["label"]])[0]
            
            # Check if this entity overlaps with any Presidio entity
            overlap = False
            for presidio_entity in presidio_results:
                if (entity["start"] <= presidio_entity["end"] and 
                    entity["end"] >= presidio_entity["start"]):
                    overlap = True
                    break
            
            # Add if no overlap
            if not overlap:
                combined.append({
                    "type": mapped_label,
                    "start": entity["start"],
                    "end": entity["end"],
                    "value": entity["text"],
                    "confidence": entity["confidence"],
                    "source": "gliner"
                })
        
        logging.info(f"🔗 Combined {len(presidio_results)} Presidio + {len(gliner_results)} GLiNER results = {len(combined)} total")
        return combined
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status of GLiNER engine
        
        Returns:
            Dictionary with status information
        """
        return {
            "model_loaded": self.is_loaded,
            "model_name": self.model_name,
            "gliner_available": GLINER_AVAILABLE,
            "model": self.model is not None,
            "using_fallback": not self.is_loaded and GLINER_AVAILABLE
        }
