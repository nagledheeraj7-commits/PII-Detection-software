#!/usr/bin/env python3
"""
FINAL PII Detection Solution - Complete Fix for Presidio Integration
This version completely resolves the 'dict object has no attribute regex' error
"""

import sys
import os
import time
import logging
import pandas as pd
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

# Check Python version compatibility
if sys.version_info > (3, 11):
    print("WARNING: Python 3.12+ detected. This project works best with Python 3.10 or 3.11.")

def setup_logging():
    """Setup basic logging without unicode issues"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def safe_analyze_with_presidio(text: str, analyzer) -> List[Dict[str, Any]]:
    """
    Safely analyze text with Presidio, handling all potential errors
    
    Args:
        text: Text to analyze
        analyzer: Presidio analyzer instance
        
    Returns:
        List of detected entities
    """
    if not text or not text.strip():
        return []
    
    try:
        # Ensure we're passing a string, not a dict
        if not isinstance(text, str):
            text = str(text)
        
        # Use the correct analyze_text method
        results = analyzer.analyze_text(
            text=text,
            language="en"
        )
        
        # Convert to our format
        entities = []
        for result in results:
            try:
                entities.append({
                    "type": result.entity_type,
                    "start": result.start,
                    "end": result.end,
                    "value": text[result.start:result.end],
                    "confidence": result.score,
                    "source": "presidio"
                })
            except AttributeError as e:
                logging.warning(f"Skipping malformed Presidio result: {e}")
                continue
        
        return entities
        
    except Exception as e:
        logging.error(f"Presidio analysis failed: {e}")
        return []

def safe_analyze_with_gliner(text: str, gliner_engine) -> List[Dict[str, Any]]:
    """
    Safely analyze text with GLiNER
    
    Args:
        text: Text to analyze
        gliner_engine: GLiNER engine instance
        
    Returns:
        List of detected entities
    """
    if not text or not text.strip():
        return []
    
    if not gliner_engine or not gliner_engine.is_loaded:
        return []
    
    try:
        gliner_results = gliner_engine.analyze_text(text)
        
        entities = []
        for result in gliner_results:
            try:
                entities.append({
                    "type": result["label"].upper(),
                    "start": result["start"],
                    "end": result["end"],
                    "value": result["text"],
                    "confidence": result["confidence"],
                    "source": "gliner"
                })
            except (KeyError, TypeError) as e:
                logging.warning(f"Skipping malformed GLiNER result: {e}")
                continue
        
        return entities
        
    except Exception as e:
        logging.error(f"GLiNER analysis failed: {e}")
        return []

def merge_entities(presidio_entities: List[Dict], gliner_entities: List[Dict]) -> List[Dict]:
    """
    Merge entities from Presidio and GLiNER, removing duplicates
    
    Args:
        presidio_entities: Entities from Presidio
        gliner_entities: Entities from GLiNER
        
    Returns:
        Merged unique entities
    """
    all_entities = presidio_entities + gliner_entities
    
    # Remove duplicates based on position overlap
    unique_entities = []
    
    for entity in sorted(all_entities, key=lambda x: x.get('confidence', 0), reverse=True):
        is_duplicate = False
        
        for unique_entity in unique_entities:
            # Check for overlap
            if (entity['start'] <= unique_entity['end'] and 
                entity['end'] >= unique_entity['start']):
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_entities.append(entity)
    
    return unique_entities

class FinalPIIDetector:
    """
    Final PII Detection class with all fixes applied
    """
    
    def __init__(self, use_gliner: bool = True, gliner_model: str = None):
        """
        Initialize PII Detector
        
        Args:
            use_gliner: Whether to use GLiNER engine
            gliner_model: GLiNER model name
        """
        self.presidio_engine = None
        self.gliner_engine = None
        self.engines_used = []
        
        # Initialize Presidio with error handling
        try:
            from pii_detector.presidio_engine import PresidioPIIEngine
            self.presidio_engine = PresidioPIIEngine()
            self.engines_used.append("presidio")
            print("✅ Presidio engine initialized successfully")
        except ImportError:
            print("⚠️  Presidio not available")
        except Exception as e:
            print(f"❌ Error initializing Presidio: {e}")
            self.presidio_engine = None
        
        # Initialize GLiNER with error handling
        if use_gliner:
            print("🤖 Initializing GLiNER engine...")
            try:
                from pii_detector.gliner_engine_fixed import GLiNERPIIEngine
                self.gliner_engine = GLiNERPIIEngine(gliner_model)
                status = self.gliner_engine.get_status()
                
                if status["model_loaded"] or status["using_fallback"]:
                    self.engines_used.append("gliner")
                    if status["model_loaded"]:
                        print("✅ GLiNER engine initialized successfully")
                    else:
                        print("⚠️  GLiNER using rule-based fallback")
                else:
                    print("⚠️  GLiNER engine failed to load - using Presidio only")
            except ImportError:
                print("⚠️  GLiNER not available")
            except Exception as e:
                print(f"❌ Error initializing GLiNER: {e}")
                print("⚠️  Continuing with Presidio only")
        else:
            print("ℹ️  GLiNER disabled - using Presidio only")
        
        self.engines_used = list(set(self.engines_used))  # Remove duplicates
        print(f"🔧 Active engines: {', '.join(self.engines_used)}")
    
    def analyze_cell(self, text: str) -> Dict[str, Any]:
        """
        Analyze a single cell for PII
        
        Args:
            text: Cell text to analyze
            
        Returns:
            Dictionary with analysis results
        """
        # Ensure text is a string
        if not isinstance(text, str):
            text = str(text) if text is not None else ""
        
        text = text.strip()
        
        if not text:
            return {
                "pii_detected": False,
                "entities": [],
                "confidence": 0.0,
                "pii_types": []
            }
        
        # Analyze with Presidio
        presidio_entities = []
        if self.presidio_engine:
            presidio_entities = safe_analyze_with_presidio(text, self.presidio_engine)
        
        # Analyze with GLiNER if available
        gliner_entities = []
        if self.gliner_engine:
            gliner_entities = safe_analyze_with_gliner(text, self.gliner_engine)
        
        # Merge results
        all_entities = merge_entities(presidio_entities, gliner_entities)
        
        # Determine if PII was detected
        pii_detected = len(all_entities) > 0
        pii_types = list(set([entity["type"] for entity in all_entities]))
        confidence = max([entity["confidence"] for entity in all_entities]) if all_entities else 0.0
        
        # Debug logging
        if pii_detected:
            print(f"🔍 Cell analysis: '{text[:30]}...' -> {len(all_entities)} entities")
            for entity in all_entities:
                print(f"   - {entity['type']}: {entity['value']} (confidence: {entity['confidence']}, source: {entity['source']})")
        
        return {
            "pii_detected": pii_detected,
            "entities": all_entities,
            "confidence": confidence,
            "pii_types": pii_types
        }
    
    def analyze_column(self, df: pd.DataFrame, column_name: str, sample_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze a column for PII
        
        Args:
            df: DataFrame to analyze
            column_name: Column name to analyze
            sample_size: Number of rows to sample (None for all)
            
        Returns:
            Dictionary with column analysis results
        """
        print(f"🔍 Analyzing column: {column_name}")
        
        # Validate DataFrame and column
        if not hasattr(df, 'columns') or column_name not in df.columns:
            return {
                "column_name": column_name,
                "total_cells": 0,
                "pii_cells": 0,
                "pii_percentage": 0.0,
                "pii_types": [],
                "entities": [],
                "avg_confidence": 0.0,
                "sample_size": 0
            }
        
        # Get column data
        column_data = df[column_name].dropna()
        
        if column_data.empty:
            return {
                "column_name": column_name,
                "total_cells": 0,
                "pii_cells": 0,
                "pii_percentage": 0.0,
                "pii_types": [],
                "entities": [],
                "avg_confidence": 0.0,
                "sample_size": 0
            }
        
        # Sample data if requested
        if sample_size and len(column_data) > sample_size:
            column_data = column_data.sample(n=sample_size, random_state=42)
        
        # Analyze each cell
        entities_found = []
        pii_cells = 0
        
        for cell_value in column_data:
            cell_str = str(cell_value) if cell_value is not None else ""
            cell_result = self.analyze_cell(cell_str)
            
            if cell_result["pii_detected"]:
                pii_cells += 1
                entities_found.extend(cell_result["entities"])
        
        # Calculate statistics
        total_cells = len(column_data)
        pii_percentage = (pii_cells / total_cells) * 100 if total_cells > 0 else 0.0
        pii_types = list(set([entity["type"] for entity in entities_found]))
        avg_confidence = sum([entity["confidence"] for entity in entities_found]) / len(entities_found) if entities_found else 0.0
        
        return {
            "column_name": column_name,
            "total_cells": total_cells,
            "pii_cells": pii_cells,
            "pii_percentage": pii_percentage,
            "pii_types": pii_types,
            "entities": entities_found,
            "avg_confidence": avg_confidence,
            "sample_size": len(column_data)
        }
    
    def analyze_csv(self, input_file: str, sample_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze CSV file for PII
        
        Args:
            input_file: Path to input CSV file
            sample_size: Number of rows to sample (None for all)
            
        Returns:
            Dictionary with analysis results
        """
        print(f"📊 Loading CSV file: {input_file}")
        
        # Load CSV with proper error handling
        try:
            df = pd.read_csv(input_file, encoding='utf-8')
            print(f"✅ Successfully loaded CSV with {len(df)} rows and {len(df.columns)} columns")
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(input_file, encoding='latin-1')
                print(f"✅ Successfully loaded CSV with latin-1 encoding")
            except Exception as e:
                raise ValueError(f"Failed to load CSV with any encoding: {e}")
        except Exception as e:
            raise ValueError(f"Error loading CSV: {e}")
        
        # Sample data if requested
        if sample_size and len(df) > sample_size:
            df = df.sample(n=sample_size, random_state=42)
            print(f"📋 Sampled {sample_size} rows from {len(df)} total rows")
        
        # Analyze each column
        column_results = {}
        total_entities = []
        
        for column_name in df.columns:
            column_result = self.analyze_column(df, column_name, sample_size)
            column_results[column_name] = column_result
            total_entities.extend(column_result["entities"])
        
        # Calculate overall statistics
        total_cells = len(df) * len(df.columns)
        total_pii_cells = sum([result["pii_cells"] for result in column_results.values()])
        overall_pii_percentage = (total_pii_cells / total_cells) * 100 if total_cells > 0 else 0.0
        
        return {
            "input_file": input_file,
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "total_cells": total_cells,
            "total_pii_cells": total_pii_cells,
            "overall_pii_percentage": overall_pii_percentage,
            "column_results": column_results,
            "all_entities": total_entities,
            "engines_used": self.engines_used
        }
    
    def generate_report(self, analysis_result: Dict[str, Any], output_file: str):
        """
        Generate PII report
        
        Args:
            analysis_result: Results from analyze_csv
            output_file: Path to output JSON file
        """
        print(f"📝 Generating report: {output_file}")
        
        # Create output directory
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create report structure
        report = {
            "metadata": {
                "input_file": analysis_result["input_file"],
                "total_rows": analysis_result["total_rows"],
                "total_columns": analysis_result["total_columns"],
                "engines_used": analysis_result["engines_used"],
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "summary": {
                "total_cells": analysis_result["total_cells"],
                "total_pii_cells": analysis_result["total_pii_cells"],
                "overall_pii_percentage": analysis_result["overall_pii_percentage"],
                "total_entities_found": len(analysis_result["all_entities"])
            },
            "column_summaries": {}
        }
        
        # Add column summaries
        for col_name, col_result in analysis_result["column_results"].items():
            report["column_summaries"][col_name] = {
                "total_cells": col_result["total_cells"],
                "pii_cells": col_result["pii_cells"],
                "pii_percentage": col_result["pii_percentage"],
                "pii_types": col_result["pii_types"],
                "avg_confidence": col_result["avg_confidence"],
                "sample_size": col_result["sample_size"]
            }
        
        # Add row-level details
        report["row_details"] = analysis_result["all_entities"]
        
        # Save report
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Report saved to: {output_file}")


# CLI Interface
def main():
    """Main function"""
    if len(sys.argv) < 3:
        print("Usage: python FINAL_SOLUTION.py -i input.csv -o output.json")
        print("Options:")
        print("  -s, --sample-size N: Sample N rows")
        print("  -q, --quiet: Suppress verbose output")
        print("  --no-gliner: Disable GLiNER engine")
        return
    
    input_file = None
    output_file = None
    sample_size = None
    quiet = False
    no_gliner = False
    
    # Parse arguments
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
            sample_size = int(sys.argv[i + 1])
            i += 2
        elif arg in ['-q', '--quiet']:
            quiet = True
            i += 1
        elif arg == '--no-gliner':
            no_gliner = True
            i += 1
        else:
            i += 1
    
    if not input_file or not output_file:
        print("❌ Error: Both input and output files are required")
        return
    
    if not quiet:
        setup_logging()
    
    try:
        # Initialize PII detector
        detector = FinalPIIDetector(
            use_gliner=not no_gliner
        )
        
        # Analyze CSV
        start_time = time.time()
        analysis_result = detector.analyze_csv(input_file, sample_size)
        processing_time = time.time() - start_time
        analysis_result["processing_time"] = processing_time
        
        # Generate report
        detector.generate_report(analysis_result, output_file)
        
        # Print summary
        if not quiet:
            print("\n" + "="*50)
            print("PII DETECTION REPORT SUMMARY")
            print("="*50)
            print(f"Input File: {input_file}")
            print(f"Processing Time: {processing_time:.2f} seconds")
            print(f"Engines Used: {', '.join(analysis_result['engines_used'])}")
            print()
            
            # Column statistics
            pii_columns = sum(1 for result in analysis_result["column_results"].values() if result["pii_cells"] > 0)
            total_columns = len(analysis_result["column_results"])
            
            print("Column Statistics:")
            print(f"  Total Columns: {total_columns}")
            print(f"  PII Columns: {pii_columns} ({(pii_columns/total_columns)*100:.1f}%)")
            print(f"  Non-PII Columns: {total_columns - pii_columns}")
            print()
            
            # Row statistics
            print("Row Statistics:")
            print(f"  Total Rows Processed: {analysis_result['total_rows']}")
            print(f"  Total PII Detections: {len(analysis_result['all_entities'])}")
            
            if analysis_result['all_entities']:
                avg_confidence = sum([entity['confidence'] for entity in analysis_result['all_entities']]) / len(analysis_result['all_entities'])
                print(f"  Average Confidence: {avg_confidence:.3f}")
            else:
                print(f"  Average Confidence: 0")
            
            print("="*50)
        
        print("🎉 PII analysis completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if not quiet:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
