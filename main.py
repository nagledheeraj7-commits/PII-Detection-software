#!/usr/bin/env python3
"""
<<<<<<< HEAD
PII Detection Main Script - Production Version
=======
PII Detection Main Script - Clean Working Version
>>>>>>> e9dfd611ba2d0e633a07f1d79609d174e7f631f8
"""

import sys
import os
import time
import logging
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
<<<<<<< HEAD
from contextlib import contextmanager

# Import production components
from config_simple import config, setup_logging
from logger import get_logger, log_execution
from validators import validate_all, ValidationResult
from monitoring import monitor_operation, metrics_collector, resource_manager, rate_limiter

# Setup logging at import time
setup_logging()
logger = get_logger("Main")
=======
>>>>>>> e9dfd611ba2d0e633a07f1d79609d174e7f631f8

# Setup safe encoding first
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

def safe_print(*args):
    """Safe print function that handles Unicode encoding errors"""
    try:
        print(*args)
    except UnicodeEncodeError:
        safe_msg = ' '.join(str(arg).encode("utf-8", errors="ignore").decode() for arg in args)
        print(safe_msg)
    except Exception:
        pass

def parse_arguments():
    """Parse command line arguments"""
    input_file = None
    output_file = None
    sample_size = None
    no_gliner = False
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ['-i', '--input'] and i + 1 < len(sys.argv):
            input_file = sys.argv[i + 1]
            i += 2
        elif arg in ['-o', '--output'] and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]
            i += 2
        elif arg in ['-s', '--sample-size'] and i + 1 < len(sys.argv):
            try:
                sample_size = int(sys.argv[i + 1])
            except ValueError:
                safe_print("Error: Sample size must be a number")
                return None, None, None, True
            i += 2
        elif arg == '--no-gliner':
            no_gliner = True
            i += 1
        else:
            i += 1
    
    if not input_file or not output_file:
        safe_print("Usage: python main.py --input input.csv --output output.json")
        safe_print("Options:")
        safe_print("  --sample-size N: Sample N rows")
        safe_print("  --no-gliner: Disable GLiNER engine")
        return None, None, None, True
    
    return input_file, output_file, sample_size, no_gliner

def safe_string(value) -> str:
<<<<<<< HEAD
    """Convert any value to a safe string for analysis - CRITICAL FIX"""
    if value is None:
        return ""
    
    # Handle pandas special types first - use try-catch for isna
    try:
        if pd.isna(value):
            return ""
    except (ValueError, TypeError):
        # isna doesn't work on all types, continue with other checks
        pass
    
    if isinstance(value, dict):
        return " ".join(str(v) for v in value.values() if v is not None and str(v).strip())
    
    if isinstance(value, list):
        return " ".join(str(v) for v in value if v is not None and str(v).strip())
    
    # Handle other types
    try:
        result = str(value).strip()
        return result if result else ""
    except Exception:
        return ""

class SimplePIIDetector:
    """Production-ready PII detector using Presidio and optional GLiNER"""
    
    def __init__(self, use_gliner=True, use_presidio=True):
=======
    """Convert any value to a safe string for analysis"""
    if value is None:
        return ""
    
    if isinstance(value, dict):
        return " ".join(str(v) for v in value.values() if v is not None)
    
    if isinstance(value, list):
        return " ".join(str(v) for v in value if v is not None)
    
    # Handle pandas NaN/NaT values
    if pd.isna(value):
        return ""
    
    return str(value).strip()

class SimplePIIDetector:
    """Simple PII detector using Presidio and optional GLiNER"""
    
    def __init__(self, use_gliner=True):
>>>>>>> e9dfd611ba2d0e633a07f1d79609d174e7f631f8
        self.presidio_engine = None
        self.gliner_engine = None
        self.engines_used = []
        
        # Initialize Presidio
<<<<<<< HEAD
        if use_presidio and config.enable_presidio:
            try:
                from presidio_analyzer import AnalyzerEngine
                self.presidio_engine = AnalyzerEngine()
                self.engines_used.append("presidio")
                logger.info("Presidio engine initialized successfully")
            except Exception as e:
                logger.error("Error initializing Presidio", exception=e)
                if not config.fallback_to_presidio_only:
                    logger.warning("Continuing without Presidio")
        
        # Initialize GLiNER if requested
        if use_gliner and config.enable_gliner:
=======
        try:
            from presidio_analyzer import AnalyzerEngine
            self.presidio_engine = AnalyzerEngine()
            self.engines_used.append("presidio")
            safe_print("Presidio engine initialized successfully")
        except Exception as e:
            safe_print(f"Error initializing Presidio: {e}")
        
        # Initialize GLiNER if requested
        if use_gliner:
>>>>>>> e9dfd611ba2d0e633a07f1d79609d174e7f631f8
            try:
                from pii_detector.gliner_engine_fixed import GLiNERPIIEngine
                self.gliner_engine = GLiNERPIIEngine()
                status = self.gliner_engine.get_status()
                
                if status["model_loaded"] or status["using_fallback"]:
                    self.engines_used.append("gliner")
                    if status["model_loaded"]:
<<<<<<< HEAD
                        logger.info("GLiNER engine initialized successfully")
                    else:
                        logger.info("GLiNER using rule-based fallback")
                else:
                    logger.warning("GLiNER engine failed to load")
            except Exception as e:
                logger.error("Error initializing GLiNER", exception=e)
                logger.warning("Continuing with available engines")
        
        logger.info(f"Active engines: {', '.join(self.engines_used)}")
=======
                        safe_print("GLiNER engine initialized successfully")
                    else:
                        safe_print("GLiNER using rule-based fallback")
                else:
                    safe_print("GLiNER engine failed to load - using Presidio only")
            except Exception as e:
                safe_print(f"Error initializing GLiNER: {e}")
                safe_print("Continuing with Presidio only")
        
        safe_print(f"Active engines: {', '.join(self.engines_used)}")
>>>>>>> e9dfd611ba2d0e633a07f1d79609d174e7f631f8
    
    def analyze_text(self, text: str) -> List[Dict[str, Any]]:
        """Analyze text for PII"""
        text = safe_string(text)
        
        if not text:
            return []
        
        entities = []
        
        # Analyze with Presidio
        if self.presidio_engine:
            try:
                results = self.presidio_engine.analyze(
                    text=text,
                    language="en"
                )
                for result in results:
<<<<<<< HEAD
                    # Safe confidence comparison - CRITICAL FIX
                    confidence = result.score if result.score is not None else 0.0
=======
>>>>>>> e9dfd611ba2d0e633a07f1d79609d174e7f631f8
                    entities.append({
                        "type": result.entity_type,
                        "start": result.start,
                        "end": result.end,
                        "value": text[result.start:result.end],
<<<<<<< HEAD
                        "confidence": confidence,
=======
                        "confidence": result.score,
>>>>>>> e9dfd611ba2d0e633a07f1d79609d174e7f631f8
                        "source": "presidio"
                    })
            except Exception as e:
                safe_print(f"Presidio analysis error: {e}")
                # Continue with empty results rather than crashing
        
        # Analyze with GLiNER if available
        if self.gliner_engine and self.gliner_engine.is_loaded:
            try:
                gliner_results = self.gliner_engine.analyze_text(text)
                for result in gliner_results:
<<<<<<< HEAD
                    # Safe confidence comparison - CRITICAL FIX
                    confidence = result.get("confidence")
                    if confidence is None:
                        confidence = 0.0
=======
>>>>>>> e9dfd611ba2d0e633a07f1d79609d174e7f631f8
                    entities.append({
                        "type": result["label"].upper(),
                        "start": result["start"],
                        "end": result["end"],
                        "value": result["text"],
<<<<<<< HEAD
                        "confidence": confidence,
=======
                        "confidence": result["confidence"],
>>>>>>> e9dfd611ba2d0e633a07f1d79609d174e7f631f8
                        "source": "gliner"
                    })
            except Exception as e:
                safe_print(f"GLiNER analysis error: {e}")
        
        return entities
    
    def analyze_csv(self, input_file: str, sample_size: Optional[int] = None) -> Dict[str, Any]:
<<<<<<< HEAD
        """Analyze CSV file for PII with production safety"""
        logger.info(f"Loading CSV file: {input_file}")
        
        try:
            # Load CSV with error handling
            try:
                df = pd.read_csv(input_file, encoding='utf-8')
                logger.info(f"Successfully loaded CSV with {len(df)} rows and {len(df.columns)} columns")
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(input_file, encoding='latin-1')
                    logger.info("Successfully loaded CSV with latin-1 encoding")
                except Exception as e:
                    logger.error("Error loading CSV with latin-1", exception=e)
                    raise Exception(f"Could not read CSV file: {e}")
            except Exception as e:
                logger.error("Error loading CSV", exception=e)
                raise Exception(f"Could not read CSV file: {e}")
        
            # Handle missing values - CRITICAL FIX
            df = df.fillna("")
            
            # Sample data if requested
            if sample_size and len(df) > sample_size:
                df = df.sample(n=sample_size, random_state=42)
                logger.info(f"Sampled {sample_size} rows")
            
            # Check resource limits before processing
            resource_check = resource_manager.check_resource_limits()
            if resource_check["errors"]:
                raise Exception(f"Resource limits exceeded before processing: {'; '.join(resource_check['errors'])}")
            
            # Analyze each cell
            all_entities = []
            column_results = {}
            total_cells = len(df) * len(df.columns)
            processed_cells = 0
            
            for column_name in df.columns:
                logger.debug(f"Analyzing column: {column_name}")
                
                try:
                    column_entities = []
                    pii_cells = 0
                    
                    for idx, value in enumerate(df[column_name]):
                        # Skip empty values - CRITICAL FIX
                        if pd.isna(value) or value == "":
                            continue
                        
                        # Safe text processing - CRITICAL FIX
                        text_value = str(value) if value is not None else ""
                        if not text_value.strip():
                            continue
                            
                        entities = self.analyze_text(text_value)
                        
                        if entities:
                            pii_cells += 1
                            for entity in entities:
                                entity.update({
                                    "row_number": idx + 1,
                                    "column_name": column_name,
                                    "original_value": str(value)
                                })
                                column_entities.append(entity)
                                all_entities.append(entity)
                        
                        processed_cells += 1
                        
                        # Check resource limits periodically
                        if processed_cells % 1000 == 0:
                            resource_check = resource_manager.check_resource_limits()
                            if resource_check["errors"]:
                                logger.warning(f"Resource limits during processing: {resource_check['errors']}")
                                break
                    
                    column_results[column_name] = {
                        "total_cells": len(df[column_name].dropna()),
                        "pii_cells": pii_cells,
                        "pii_percentage": (pii_cells / len(df[column_name].dropna())) * 100 if len(df[column_name].dropna()) > 0 else 0,
                        "entities": column_entities
                    }
                    
                except Exception as e:
                    logger.error(f"Error processing column {column_name}", exception=e)
                    # Add safe default values for failed columns
                    column_results[column_name] = {
                        "total_cells": len(df[column_name]),
                        "pii_cells": 0,
                        "pii_percentage": 0,
                        "entities": []
                    }
            
            # Create result
            result = {
                "metadata": {
                    "input_file": input_file,
                    "total_rows": len(df),
                    "total_columns": len(df.columns),
                    "engines_used": self.engines_used,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                },
                "summary": {
                    "total_cells": total_cells,
                    "total_pii_cells": sum(result["pii_cells"] for result in column_results.values() if result.get("pii_cells") is not None),
                    "total_entities_found": len(all_entities),
                    "overall_pii_percentage": (sum(result["pii_cells"] for result in column_results.values() if result.get("pii_cells") is not None) / total_cells) * 100 if total_cells > 0 else 0
                },
                "column_results": column_results,
                "all_entities": all_entities
            }
            
            logger.info(f"CSV analysis completed", 
                       rows=len(df), 
                       columns=len(df.columns),
                       entities_found=len(all_entities),
                       pii_cells=result["summary"]["total_pii_cells"])
            
            return result
            
        except Exception as e:
            logger.error("CSV analysis failed", exception=e, input_file=input_file)
            raise

@log_execution(logger)
def run_pii_detection(file_path: str, use_gliner: bool = True, sample_size: Optional[int] = None) -> Dict[str, Any]:
    """
    Production-ready PII detection function
    
    Args:
        file_path: Path to the CSV file to analyze
        use_gliner: Whether to use GLiNER engine (default: True)
        sample_size: Optional limit on number of rows to analyze
    
    Returns:
        Dictionary containing detection results
    
    Raises:
        Exception: If detection fails
    """
    # Rate limiting check
    if not rate_limiter.can_proceed():
        wait_time = rate_limiter.wait_time()
        logger.warning(f"Rate limit reached, waiting {wait_time:.1f}s")
        time.sleep(wait_time)
    
    rate_limiter.record_operation()
    
    # Comprehensive validation
    file_result, csv_result, processing_result, system_result = validate_all(
        file_path, sample_size, use_gliner, config.enable_presidio
    )
    
    # Check validation results
    if not file_result.is_valid:
        raise Exception(f"File validation failed: {'; '.join(file_result.errors)}")
    
    if not csv_result.is_valid:
        raise Exception(f"CSV validation failed: {'; '.join(csv_result.errors)}")
    
    if not processing_result.is_valid:
        raise Exception(f"Processing validation failed: {'; '.join(processing_result.errors)}")
    
    if not system_result.is_valid:
        logger.warning(f"System validation warnings: {'; '.join(system_result.warnings)}")
    
    # Log validation metadata
    logger.info("Validation completed", 
               file_metadata=file_result.metadata,
               csv_metadata=csv_result.metadata)
    
    try:
        with monitor_operation("pii_detection"):
            # Initialize detector
            detector = SimplePIIDetector(
                use_gliner=use_gliner and config.enable_gliner,
                use_presidio=config.enable_presidio
            )
            
            if not detector.engines_used:
                raise Exception("No PII detection engines available")
            
            # Check resource limits
            resource_check = resource_manager.check_resource_limits()
            if resource_check["errors"]:
                raise Exception(f"Resource limits exceeded: {'; '.join(resource_check['errors'])}")
            
            if resource_check["warnings"]:
                logger.warning("Resource warnings", warnings=resource_check["warnings"])
            
            # Analyze CSV
            start_time = time.time()
            result = detector.analyze_csv(file_path, sample_size)
            processing_time = time.time() - start_time
            
            if not result:
                raise Exception("PII analysis failed")
            
            result["processing_time"] = processing_time
            result["validation_metadata"] = {
                "file_validation": file_result.metadata,
                "csv_validation": csv_result.metadata,
                "system_validation": system_result.metadata
            }
            
            logger.info("PII detection completed successfully",
                       processing_time=processing_time,
                       engines_used=detector.engines_used,
                       total_entities=result.get("summary", {}).get("total_entities_found", 0),
                       rows_analyzed=result.get("metadata", {}).get("total_rows", 0))
            
            return result
            
    except Exception as e:
        logger.error("PII detection failed", exception=e, file_path=file_path)
        raise Exception(f"PII detection failed: {str(e)}")
=======
        """Analyze CSV file for PII"""
        safe_print(f"Loading CSV file: {input_file}")
        
        try:
            # Load CSV
            df = pd.read_csv(input_file, encoding='utf-8')
            safe_print(f"Successfully loaded CSV with {len(df)} rows and {len(df.columns)} columns")
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(input_file, encoding='latin-1')
                safe_print("Successfully loaded CSV with latin-1 encoding")
            except Exception as e:
                safe_print(f"Error loading CSV: {e}")
                return {}
        except Exception as e:
            safe_print(f"Error loading CSV: {e}")
            return {}
        
        # Sample data if requested
        if sample_size and len(df) > sample_size:
            df = df.sample(n=sample_size, random_state=42)
            safe_print(f"Sampled {sample_size} rows")
        
        # Analyze each cell
        all_entities = []
        column_results = {}
        
        for column_name in df.columns:
            safe_print(f"Analyzing column: {column_name}")
            
            column_entities = []
            pii_cells = 0
            
            for idx, value in enumerate(df[column_name]):
                # Skip NaN values
                if pd.isna(value):
                    continue
                
                entities = self.analyze_text(str(value))
                
                if entities:
                    pii_cells += 1
                    for entity in entities:
                        entity.update({
                            "row_number": idx + 1,
                            "column_name": column_name,
                            "original_value": str(value)
                        })
                        column_entities.append(entity)
                        all_entities.append(entity)
            
            column_results[column_name] = {
                "total_cells": len(df[column_name].dropna()),
                "pii_cells": pii_cells,
                "pii_percentage": (pii_cells / len(df[column_name].dropna())) * 100 if len(df[column_name].dropna()) > 0 else 0,
                "entities": column_entities
            }
        
        # Create result
        result = {
            "metadata": {
                "input_file": input_file,
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "engines_used": self.engines_used,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "summary": {
                "total_cells": len(df) * len(df.columns),
                "total_pii_cells": sum(result["pii_cells"] for result in column_results.values()),
                "total_entities_found": len(all_entities),
                "overall_pii_percentage": (sum(result["pii_cells"] for result in column_results.values()) / (len(df) * len(df.columns))) * 100 if len(df) * len(df.columns) > 0 else 0
            },
            "column_results": column_results,
            "all_entities": all_entities
        }
        
        return result
>>>>>>> e9dfd611ba2d0e633a07f1d79609d174e7f631f8

def main():
    """Main function"""
    # Parse arguments
    input_file, output_file, sample_size, no_gliner = parse_arguments()
    
    if input_file is None:
        return
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        safe_print("=" * 50)
        safe_print("PII Detection Tool")
        safe_print("=" * 50)
        
<<<<<<< HEAD
        # Use the reusable function
        result = run_pii_detection(input_file, use_gliner=not no_gliner, sample_size=sample_size)
=======
        # Initialize detector
        detector = SimplePIIDetector(use_gliner=not no_gliner)
        
        if not detector.engines_used:
            safe_print("Error: No engines available")
            return
        
        # Analyze CSV
        start_time = time.time()
        result = detector.analyze_csv(input_file, sample_size)
        processing_time = time.time() - start_time
        
        if not result:
            safe_print("Error: Analysis failed")
            return
        
        result["processing_time"] = processing_time
>>>>>>> e9dfd611ba2d0e633a07f1d79609d174e7f631f8
        
        # Create output directory
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save report
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        safe_print(f"Report saved to: {output_file}")
        
        # Print summary
        safe_print("=" * 50)
        safe_print("PII DETECTION REPORT SUMMARY")
        safe_print("=" * 50)
        safe_print(f"Input File: {input_file}")
<<<<<<< HEAD
        safe_print(f"Processing Time: {result['processing_time']:.2f} seconds")
=======
        safe_print(f"Processing Time: {processing_time:.2f} seconds")
>>>>>>> e9dfd611ba2d0e633a07f1d79609d174e7f631f8
        safe_print(f"Engines Used: {', '.join(result['metadata']['engines_used'])}")
        safe_print(f"Total Rows: {result['metadata']['total_rows']}")
        safe_print(f"Total Columns: {result['metadata']['total_columns']}")
        safe_print(f"Total PII Entities: {result['summary']['total_entities_found']}")
        safe_print(f"Overall PII Percentage: {result['summary']['overall_pii_percentage']:.2f}%")
        safe_print("=" * 50)
        safe_print("PII analysis completed successfully!")
        
    except Exception as e:
        safe_print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
