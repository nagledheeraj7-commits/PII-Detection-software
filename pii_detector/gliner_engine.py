"""
GLiNER Engine for Generalized Named Entity Recognition
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
    
    def __init__(self, model_name: str = "gliner_base"):
        """
        Initialize GLiNER engine
        
        Args:
            model_name: HuggingFace model name for GLiNER
        """
        self.model_name = model_name
        self.model = None
        self.is_loaded = False
        self.load_model()
    
    def load_model(self):
        """Load GLiNER model with proper error handling"""
        if not GLINER_AVAILABLE:
            logging.error("GLiNER is not available. Install with: pip install gliner")
            self.model = None
            self.is_loaded = False
            return
        
        try:
            logging.info(f"🤖 Loading GLiNER model: {self.model_name}")
            print(f"🤖 Loading GLiNER model: {self.model_name}")
            
            # Try to load model with correct API (including required parameters)
            self.model = GLiNER.from_pretrained(
                self.model_name,
                local_files_only=False,
                force_download=False
            )
            self.is_loaded = True
            
            logging.info("✅ GLiNER model loaded successfully")
            print("✅ GLiNER model loaded successfully")
                
        except Exception as e:
            logging.error(f"❌ Error loading GLiNER model: {e}")
            print(f"❌ Error loading GLiNER model: {e}")
            self.model = None
            self.is_loaded = False
            
            # Try fallback model
            if self.model_name != "gliner_base":
                try:
                    logging.info("Attempting fallback model: gliner_base")
                    print("🔄 Attempting fallback model: gliner_base")
                    
                    self.model = GLiNER.from_pretrained(
                        "gliner_base",
                        local_files_only=False,
                        force_download=False
                    )
                    self.model_name = "gliner_base"
                    self.is_loaded = True
                    
                    logging.info("✅ Fallback GLiNER model loaded successfully")
                    print("✅ Fallback GLiNER model loaded successfully")
                except Exception as fallback_error:
                    logging.error(f"❌ Fallback model also failed: {fallback_error}")
                    print(f"❌ Fallback model also failed: {fallback_error}")
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
        if not self.is_loaded or not self.model:
            logging.warning("GLiNER model not loaded - skipping GLiNER analysis")
            return []
        
        if not text or not isinstance(text, str):
            return []
        
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
                # Handle both dict and object formats
                if isinstance(entity, dict):
                    entity_dict = entity
                else:
                    # Handle object format
                    entity_dict = {
                        "text": getattr(entity, "text", ""),
                        "label": getattr(entity, "label", ""),
                        "start": getattr(entity, "start", 0),
                        "end": getattr(entity, "end", 0),
                        "score": getattr(entity, "score", 0.0)
                    }
                
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
            return []
    
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
        
        if not gliner_results:
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
        Get the status of GLiNER engine
        
        Returns:
            Dictionary with status information
        """
        return {
            "model_loaded": self.is_loaded,
            "model_name": self.model_name,
            "gliner_available": GLINER_AVAILABLE,
            "model": self.model is not None
        }
