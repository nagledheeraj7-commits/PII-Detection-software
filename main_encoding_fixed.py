#!/usr/bin/env python3
"""
PII Detection Main Script - Fixed encoding version
"""

import sys
import os
import time
import logging
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# Setup safe encoding first
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

# Import safe print helper
from safe_print_helper import safe_print, setup_safe_encoding

# Setup safe encoding
setup_safe_encoding()

# Check Python version compatibility
if sys.version_info > (3, 11):
    safe_print("WARNING: Python 3.12+ detected. This project works best with Python 3.10 or 3.11.")
    safe_print("Some dependencies may have compatibility issues with newer Python versions.")
    safe_print("Consider using Python 3.10 or 3.11 for best results.")
    safe_print("")

from pii_detector.presidio_engine_simple import SimplePresidioPIIEngine as PresidioPIIEngine, safe_string
from pii_detector.gliner_engine_fixed import GLiNERPIIEngine
from pii_detector.report_generator import PIIReportGenerator
from pii_detector.utils import (
    validate_csv_file, load_csv_data, clean_text_data,
    calculate_pii_percentage, merge_detection_results,
    create_output_directory, setup_logging
)


class PIIDetector:
    """
    PII Detection class using Presidio and GLiNER
    """
    
    def __init__(self, use_gliner: bool = True, gliner_model: str = None):
        """
        Initialize PII Detector
        
        Args:
            use_gliner: Whether to use GLiNER engine
            gliner_model: GLiNER model name
        """
        self.presidio_engine = PresidioPIIEngine()
        self.gliner_engine = None
        self.engines_used = ["presidio"]
        
        if use_gliner:
            safe_print("Initializing GLiNER engine...")
            try:
                self.gliner_engine = GLiNERPIIEngine(gliner_model)
                status = self.gliner_engine.get_status()
                
                if status["model_loaded"] or status["using_fallback"]:
                    self.engines_used.append("gliner")
                    if status["model_loaded"]:
                        safe_print("GLiNER engine initialized successfully")
                    else:
                        safe_print("GLiNER using rule-based fallback")
                else:
                    safe_print("GLiNER engine failed to load - using Presidio only")
            except Exception as e:
                safe_print(f"Error initializing GLiNER: {e}")
                safe_print("Continuing with Presidio only")
        else:
            safe_print("GLiNER disabled - using Presidio only")
        
        self.report_generator = PIIReportGenerator()
        safe_print(f"Active engines: {', '.join(self.engines_used)}")
    
    def analyze_cell(self, text: Any) -> Dict[str, Any]:
        """
        Analyze a single cell for PII
        
        Args:
            text: Cell text to analyze (any type)
            
        Returns:
            Dictionary with analysis results
        """
        # Use safe_string to handle all input types including NaN
        text = safe_string(text)
        
        # Additional cleaning
        text = clean_text_data(text)
        
        if not text:
            return {
                "pii_detected": False,
                "entities": [],
                "confidence": 0.0,
                "pii_types": []
            }
        
        # Analyze with Presidio
        presidio_results = self.presidio_engine.analyze_text(text)
        presidio_entities = [{
            "type": result.entity_type,
            "start": result.start,
            "end": result.end,
            "value": text[result.start:result.end],
            "confidence": result.score,
            "source": "presidio"
        } for result in presidio_results]
        
        # Analyze with GLiNER if available
        gliner_entities = []
        if self.gliner_engine and self.gliner_engine.is_loaded:
            gliner_results = self.gliner_engine.analyze_text(text)
            gliner_entities = [{
                "type": result["label"].upper(),
                "start": result["start"],
                "end": result["end"],
                "value": result["text"],
                "confidence": result["confidence"],
                "source": "gliner"
            } for result in gliner_results]
        
        # Merge results
        all_entities = merge_detection_results(presidio_entities, gliner_entities)
        
        # Determine if PII was detected
        pii_detected = len(all_entities) > 0
        pii_types = list(set([entity["type"] for entity in all_entities]))
        confidence = max([entity["confidence"] for entity in all_entities]) if all_entities else 0.0
        
        # Debug logging
        if pii_detected:
            safe_print(f"Cell analysis: '{text[:30]}...' -> {len(all_entities)} entities")
            for entity in all_entities:
                safe_print(f"   - {entity['type']}: {entity['value']} (confidence: {entity['confidence']}, source: {entity['source']})")
        
        return {
            "pii_detected": pii_detected,
            "entities": all_entities,
            "confidence": confidence,
            "pii_types": pii_types
        }
    
    def analyze_column(self, df, column_name: str, sample_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze a column for PII
        
        Args:
            df: DataFrame to analyze
            column_name: Column name to analyze
            sample_size: Number of rows to sample (None for all)
            
        Returns:
            Dictionary with column analysis results
        """
        safe_print(f"Analyzing column: {column_name}")
        
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
            column_data = column_data.head(sample_size)
        
        pii_flags = []
        pii_types_per_row = []
        confidences_per_row = []
        row_results = []
        
        for idx, value in enumerate(column_data):
            row_num = idx + 1  # 1-based indexing
            
            # Skip NaN values using pandas isna
            try:
                import pandas as pd
                if pd.isna(value):
                    continue  # Skip NaN values
            except ImportError:
                pass
            
            analysis = self.analyze_cell(value)  # Pass raw value, safe_string will handle it
            
            pii_flags.append(analysis["pii_detected"])
            pii_types_per_row.extend(analysis["pii_types"])
            
            if analysis["pii_detected"]:
                confidences_per_row.append(analysis["confidence"])
                
                # Add each detected entity as a separate row result
                for entity in analysis["entities"]:
                    row_results.append({
                        "row_number": row_num,
                        "column_name": column_name,
                        "value": str(value),
                        "pii_detected": True,
                        "entity_type": entity["type"],
                        "confidence": entity["confidence"],
                        "source_engine": entity["source"]
                    })
            else:
                row_results.append({
                    "row_number": row_num,
                    "column_name": column_name,
                    "value": str(value),
                    "pii_detected": False,
                    "entity_type": None,
                    "confidence": 0.0,
                    "source_engine": None
                })
        
        # Calculate column statistics
        total_cells = len(column_data)
        pii_cells = sum(pii_flags)
        pii_percentage = calculate_pii_percentage(pii_flags)
        avg_confidence = sum(confidences_per_row) / len(confidences_per_row) if confidences_per_row else 0.0
        
        return {
            "column_name": column_name,
            "total_cells": total_cells,
            "pii_cells": pii_cells,
            "pii_percentage": pii_percentage,
            "pii_types": list(set(pii_types_per_row)),
            "entities": row_results,
            "avg_confidence": avg_confidence,
            "sample_size": len(column_data)
        }
    
    def analyze_csv(self, input_file: str, sample_size: Optional[int] = None) -> PIIReportGenerator:
        """
        Analyze CSV file for PII
        
        Args:
            input_file: Path to input CSV file
            sample_size: Number of rows to sample (None for all)
            
        Returns:
            PIIReportGenerator instance with results
        """
        safe_print(f"Analyzing PII in: {input_file}")
        safe_print(f"Using engines: {', '.join(self.engines_used)}")
        
        # Validate input file
        if not validate_csv_file(input_file):
            raise ValueError(f"Invalid input file: {input_file}")
        
        # Load CSV data
        df, error_msg = load_csv_data(input_file)
        if error_msg:
            raise ValueError(f"Error loading CSV: {error_msg}")
        
        safe_print(f"Successfully loaded CSV with encoding: utf-8")
        safe_print(f"Analyzing CSV file: {input_file}")
        safe_print(f"Shape: ({len(df)} rows, {len(df.columns)} columns)")
        
        # Sample data if requested
        if sample_size and len(df) > sample_size:
            df = df.sample(n=sample_size, random_state=42)
            safe_print(f"Sampled {sample_size} rows from {len(df)} total rows")
        
        # Initialize report generator
        report_generator = PIIReportGenerator()
        report_generator.input_file = input_file
        report_generator.total_rows = len(df)
        report_generator.total_columns = len(df.columns)
        report_generator.engines_used = self.engines_used
        report_generator.processing_start_time = time.time()
        
        # Analyze each column
        column_summaries = []
        all_entities = []
        
        for column_name in df.columns:
            safe_print(f"Analyzing column: {column_name}")
            
            column_result = self.analyze_column(df, column_name, sample_size)
            
            # Create column summary
            column_summary = {
                "name": column_name,
                "total_cells": column_result["total_cells"],
                "pii_cells": column_result["pii_cells"],
                "pii_percentage": column_result["pii_percentage"],
                "pii_types": column_result["pii_types"],
                "avg_confidence": column_result["avg_confidence"],
                "is_pii": column_result["pii_cells"] > 0
            }
            
            column_summaries.append(column_summary)
            
            # Collect all entities
            for entity in column_result["entities"]:
                if entity["pii_detected"]:
                    all_entities.append({
                        "row_number": entity["row_number"],
                        "column_name": entity["column_name"],
                        "value": entity["value"],
                        "entity_type": entity["entity_type"],
                        "confidence": entity["confidence"],
                        "source_engine": entity["source_engine"]
                    })
        
        # Update report generator
        report_generator.column_summaries = column_summaries
        report_generator.all_entities = all_entities
        report_generator.total_entities = len(all_entities)
        report_generator.processing_time = time.time() - report_generator.processing_start_time
        
        safe_print(f"Analysis completed in {report_generator.processing_time:.2f} seconds")
        
        return report_generator
    
    def anonymize_data(self, df: pd.DataFrame, output_file: str) -> bool:
        """
        Anonymize PII data in DataFrame
        
        Args:
            df: DataFrame to anonymize
            output_file: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            anonymized_df = df.copy()
            
            for column_name in df.columns:
                for idx, value in enumerate(df[column_name]):
                    analysis = self.analyze_cell(value)
                    
                    if analysis["pii_detected"]:
                        # Replace PII with placeholder
                        anonymized_value = f"[REDACTED_{analysis['pii_types'][0]}]"
                        anonymized_df.at[idx, column_name] = anonymized_value
            
            # Save anonymized data
            anonymized_df.to_csv(output_file, index=False)
            return True
            
        except Exception as e:
            safe_print(f"Error anonymizing data: {e}")
            return False


def main():
    """Main function"""
    if len(sys.argv) < 3:
        safe_print("Usage: python main_encoding_fixed.py -i input.csv -o output.json")
        safe_print("Options:")
        safe_print("  -s, --sample-size N: Sample N rows")
        safe_print("  -q, --quiet: Suppress verbose output")
        safe_print("  --no-gliner: Disable GLiNER engine")
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
        safe_print("Error: Both input and output files are required")
        return
    
    setup_logging("ERROR" if quiet else "INFO")
    
    try:
        # Initialize detector
        detector = PIIDetector(use_gliner=not no_gliner)
        
        if not quiet:
            safe_print(f"Analyzing PII in: {input_file}")
            safe_print(f"Using engines: {', '.join(detector.engines_used)}")
        
        # Analyze CSV
        report_generator = detector.analyze_csv(input_file, sample_size)
        
        # Create output directory if needed
        success, error_msg = create_output_directory(output_file)
        if not success:
            safe_print(f"Error creating output directory: {error_msg}")
            return
        
        # Save JSON report
        if report_generator.save_json_report(output_file):
            if not quiet:
                safe_print(f"JSON report saved to: {output_file}")
        else:
            safe_print(f"Error saving JSON report")
        
        # Print summary
        if not quiet:
            safe_print("=" * 50)
            safe_print("PII DETECTION REPORT SUMMARY")
            safe_print("=" * 50)
            safe_print(f"Input File: {input_file}")
            safe_print(f"Processing Time: {report_generator.processing_time:.2f} seconds")
            safe_print(f"Engines Used: {', '.join(detector.engines_used)}")
            safe_print()
            
            # Column statistics
            pii_columns = sum(1 for col in report_generator.column_summaries if col['pii_percentage'] > 0)
            total_columns = len(report_generator.column_summaries)
            
            safe_print("Column Statistics:")
            safe_print(f"  Total Columns: {total_columns}")
            safe_print(f"  PII Columns: {pii_columns} ({(pii_columns/total_columns)*100:.1f}%)")
            safe_print(f"  Non-PII Columns: {total_columns - pii_columns}")
            safe_print()
            
            # Row statistics
            safe_print("Row Statistics:")
            safe_print(f"  Total Rows Processed: {report_generator.total_rows}")
            safe_print(f"  Total PII Detections: {report_generator.total_entities}")
            
            if report_generator.total_entities > 0:
                avg_confidence = sum(entity['confidence'] for entity in report_generator.all_entities) / len(report_generator.all_entities)
                safe_print(f"  Average Confidence: {avg_confidence:.3f}")
            else:
                safe_print(f"  Average Confidence: 0")
            
            safe_print("=" * 50)
        
        safe_print("PII analysis completed successfully!")
        
    except Exception as e:
        safe_print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
