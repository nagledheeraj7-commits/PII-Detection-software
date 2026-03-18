#!/usr/bin/env python3
"""
PII Detection Tool - Fixed Presidio Version
Main CLI interface for detecting PII in CSV files using Presidio and GLiNER
"""

import sys
import os
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Check Python version compatibility
if sys.version_info > (3, 11):
    print("WARNING: Python 3.12+ detected. This project works best with Python 3.10 or 3.11.")
    print("Some dependencies may have compatibility issues with newer Python versions.")
    print("Consider using Python 3.10 or 3.11 for best results.")
    print()

from pii_detector.presidio_engine import PresidioPIIEngine
from pii_detector.gliner_engine_fixed import GLiNERPIIEngine
from pii_detector.report_generator import PIIReportGenerator
from pii_detector.utils import (
    validate_csv_file, load_csv_data, clean_text_data,
    calculate_pii_percentage, merge_detection_results,
    create_output_directory, setup_logging
)

# Import click for CLI
try:
    import click
    CLICK_AVAILABLE = True
except ImportError:
    CLICK_AVAILABLE = False
    print("❌ Click not available")


class PIIDetector:
    """
    Main PII Detection class that orchestrates the detection process
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
        
        # Initialize Presidio
        try:
            self.presidio_engine = PresidioPIIEngine()
            self.engines_used.append("presidio")
            print("✅ Presidio engine initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing Presidio: {e}")
            import traceback
            traceback.print_exc()
        
        # Initialize GLiNER
        if use_gliner:
            print("🤖 Initializing GLiNER engine...")
            try:
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
            except Exception as e:
                print(f"❌ Error initializing GLiNER: {e}")
                print("⚠️  Continuing with Presidio only")
        else:
            print("ℹ️  GLiNER disabled - using Presidio only")
        
        self.report_generator = PIIReportGenerator()
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
        
        text = clean_text_data(text)
        
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
            try:
                presidio_results = self.presidio_engine.analyze_text(text)
                presidio_entities = [{
                    "type": result.entity_type,
                    "start": result.start,
                    "end": result.end,
                    "value": text[result.start:result.end],
                    "confidence": result.score,
                    "source": "presidio"
                } for result in presidio_results]
            except Exception as e:
                logging.error(f"Presidio analysis error: {e}")
                print(f"❌ Presidio analysis error: {e}")
        
        # Analyze with GLiNER if available
        gliner_entities = []
        if self.gliner_engine and self.gliner_engine.is_loaded:
            try:
                gliner_results = self.gliner_engine.analyze_text(text)
                gliner_entities = [{
                    "type": result["label"].upper(),
                    "start": result["start"],
                    "end": result["end"],
                    "value": result["text"],
                    "confidence": result["confidence"],
                    "source": "gliner"
                } for result in gliner_results]
            except Exception as e:
                logging.error(f"GLiNER analysis error: {e}")
                print(f"❌ GLiNER analysis error: {e}")
        
        # Merge results
        all_entities = merge_detection_results(presidio_entities, gliner_entities)
        
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
        print(f"🔍 Analyzing column: {column_name}")
        
        # Get column data safely
        try:
            # Ensure df is a pandas DataFrame
            if not hasattr(df, 'columns'):
                logging.error(f"Invalid DataFrame object: {type(df)}")
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
            
            if column_name not in df.columns:
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
            
            for idx, cell_value in enumerate(column_data):
                # Convert to string safely
                cell_str = str(cell_value) if cell_value is not None else ""
                
                cell_result = self.analyze_cell(cell_str)
                
                if cell_result["pii_detected"]:
                    entities_found.extend(cell_result["entities"])
            
            # Calculate statistics
            total_cells = len(column_data)
            pii_cells = sum(1 for result in row_results if result["pii_detected"])
            pii_percentage = calculate_pii_percentage([result["pii_detected"] for result in row_results])
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
            
        except Exception as e:
            logging.error(f"Error analyzing column {column_name}: {e}")
            print(f"❌ Error analyzing column {column_name}: {e}")
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
        
        # Validate and load CSV
        validation_result = validate_csv_file(input_file)
        if not validation_result[0]:
            raise ValueError(f"Invalid CSV file: {validation_result[1]}")
        
        df = load_csv_data(input_file)
        if df is None:
            raise ValueError(f"Failed to load CSV file")
        
        # load_csv_data returns (df, error_message), we need just the df
        if isinstance(df, tuple):
            df = df[0]
        
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
        total_cells = sum([result["total_cells"] for result in column_results.values()])
        total_pii_cells = sum([result["pii_cells"] for result in column_results.values()])
        
        # Fix the calculate_pii_percentage call - it expects boolean flags
        pii_flags = [result["pii_cells"] > 0 for result in column_results.values()]
        overall_pii_percentage = calculate_pii_percentage(pii_flags)
        
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
    
    def generate_report(self, analysis_result: Dict[str, Any], output_file: str, csv_output: Optional[str] = None):
        """
        Generate PII report
        
        Args:
            analysis_result: Results from analyze_csv
            output_file: Path to output JSON file
            csv_output: Path to output CSV file (optional)
        """
        print(f"📝 Generating report: {output_file}")
        
        # Create output directory
        success, error = create_output_directory(output_file)
        if not success:
            raise ValueError(f"Cannot create output directory: {error}")
        
        # Generate report
        self.report_generator.generate_json_report(analysis_result, output_file)
        
        if csv_output:
            success, error = create_output_directory(csv_output)
            if not success:
                raise ValueError(f"Cannot create CSV output directory: {error}")
            self.report_generator.generate_csv_report(analysis_result, csv_output)
        
        print(f"✅ Report saved to: {output_file}")
        if csv_output:
            print(f"✅ CSV report saved to: {csv_output}")


# CLI Interface
@click.command()
@click.option('--input', '-i', required=True, help='Input CSV file to analyze')
@click.option('--output', '-o', required=True, help='Output JSON report file')
@click.option('--csv-output', '-c', help='Output CSV report file (optional)')
@click.option('--sample-size', '-s', type=int, help='Number of rows to sample (optional)')
@click.option('--no-gliner', is_flag=True, help='Disable GLiNER engine')
@click.option('--gliner-model', help='GLiNER model to use')
@click.option('--anonymize', help='Anonymize data and save to specified file')
@click.option('--quiet', '-q', is_flag=True, help='Suppress verbose output')
def main(input, output, csv_output, sample_size, no_gliner, gliner_model, anonymize, quiet):
    """
    PII Detection Tool - Detect Personally Identifiable Information in CSV files
    
    This tool analyzes CSV files to detect various types of PII including:
    - Personal names
    - Email addresses
    - Phone numbers
    - Address information
    - ID numbers (Aadhaar, PAN, etc.)
    - Organization names
    - Date/time information
    
    Example:
        python main.py -i data.csv -o report.json -c report.csv
    """
    
    # Setup logging
    if not quiet:
        setup_logging()
    
    try:
        # Initialize PII detector
        detector = PIIDetector(
            use_gliner=not no_gliner,
            gliner_model=gliner_model
        )
        
        # Analyze CSV
        start_time = time.time()
        analysis_result = detector.analyze_csv(input, sample_size)
        processing_time = time.time() - start_time
        
        analysis_result["processing_time"] = processing_time
        
        # Generate report
        detector.generate_report(analysis_result, output, csv_output)
        
        # Handle anonymization
        if anonymize:
            print(f"🔒 Anonymizing data to: {anonymize}")
            # This would require additional implementation
            print("⚠️  Anonymization not implemented in this version")
        
        # Print summary
        if not quiet:
            print("\n" + "="*50)
            print("PII DETECTION REPORT SUMMARY")
            print("="*50)
            print(f"Input File: {input}")
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
    if not CLICK_AVAILABLE:
        print("❌ Click is not available. Please install with: pip install click")
        sys.exit(1)
    
    main()
