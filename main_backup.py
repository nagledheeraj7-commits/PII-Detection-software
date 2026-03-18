#!/usr/bin/env python3
"""
PII Detection Tool - Main CLI Interface
Detect Personally Identifiable Information in CSV files #!/usr/bin/env python3
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
    Main PII Detection class that orchestrates the detection process
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
            df: DataFrame
            column_name: Column name
            sample_size: Number of rows to sample (None for all)
            
        Returns:
            Dictionary with column analysis results
        """
        column_data = df[column_name].dropna()
        
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
                # Add non-PII row result
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
        pii_percentage = calculate_pii_percentage(pii_flags)
        unique_pii_types = list(set(pii_types_per_row))
        avg_confidence = sum(confidences_per_row) / len(confidences_per_row) if confidences_per_row else 0.0
        
        return {
            "column_name": column_name,
            "is_pii": len(pii_flags) > 0 and any(pii_flags),
            "pii_types": unique_pii_types,
            "pii_percentage": pii_percentage,
            "total_rows": len(column_data),
            "pii_rows": sum(pii_flags),
            "avg_confidence": avg_confidence,
            "row_results": row_results
        }
    
    def analyze_csv(self, input_file: str, sample_size: Optional[int] = None) -> PIIReportGenerator:
        """
        Analyze entire CSV file for PII
        
        Args:
            input_file: Path to CSV file
            sample_size: Number of rows to sample per column (None for all)
            
        Returns:
            PIIReportGenerator with results
        """
        start_time = time.time()
        
        # Load and validate CSV
        is_valid, error_msg = validate_csv_file(input_file)
        if not is_valid:
            raise ValueError(f"Invalid CSV file: {error_msg}")
        
        df, error_msg = load_csv_data(input_file)
        if df is None:
            raise ValueError(f"Error loading CSV: {error_msg}")
        
        logging.info(f"Analyzing CSV file: {input_file}")
        logging.info(f"Shape: {df.shape} (rows x columns)")
        
        # Analyze each column
        for column_name in df.columns:
            logging.info(f"Analyzing column: {column_name}")
            
            try:
                column_analysis = self.analyze_column(df, column_name, sample_size)
                
                # Add column summary to report
                self.report_generator.add_column_summary(
                    column_name=column_analysis["column_name"],
                    is_pii=column_analysis["is_pii"],
                    pii_types=column_analysis["pii_types"],
                    pii_percentage=column_analysis["pii_percentage"],
                    total_rows=column_analysis["total_rows"],
                    pii_rows=column_analysis["pii_rows"],
                    avg_confidence=column_analysis["avg_confidence"]
                )
                
                # Add row results to report
                for row_result in column_analysis["row_results"]:
                    self.report_generator.add_row_result(
                        row_number=row_result["row_number"],
                        column_name=row_result["column_name"],
                        value=row_result["value"],
                        pii_detected=row_result["pii_detected"],
                        entity_type=row_result["entity_type"] or "",
                        confidence=row_result["confidence"],
                        source_engine=row_result["source_engine"] or "presidio"
                    )
                
            except Exception as e:
                logging.error(f"Error analyzing column {column_name}: {e}")
                continue
        
        # Add metadata
        processing_time = time.time() - start_time
        self.report_generator.add_metadata(
            input_file=input_file,
            total_rows=len(df),
            total_columns=len(df.columns),
            processing_time=processing_time,
            engines_used=self.engines_used
        )
        
        logging.info(f"Analysis completed in {processing_time:.2f} seconds")
        return self.report_generator
    
    def anonymize_data(self, df, anonymized_output_path: str) -> bool:
        """
        Anonymize PII data in DataFrame
        
        Args:
            df: DataFrame to anonymize
            anonymized_output_path: Path to save anonymized CSV
            
        Returns:
            True if successful, False otherwise
        """
        try:
            anonymized_df = df.copy()
            
            for column_name in df.columns:
                logging.info(f"Anonymizing column: {column_name}")
                
                for idx, value in enumerate(df[column_name]):
                    if pd.isna(value):
                        continue
                    
                    text = str(value)
                    presidio_results = self.presidio_engine.analyze_text(text)
                    
                    if presidio_results:
                        anonymized_text = self.presidio_engine.anonymize_text(text, presidio_results)
                        anonymized_df.iloc[idx, anonymized_df.columns.get_loc(column_name)] = anonymized_text
            
            # Save anonymized DataFrame
            anonymized_df.to_csv(anonymized_output_path, index=False)
            logging.info(f"Anonymized data saved to: {anonymized_output_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error anonymizing data: {e}")
            return False


@click.command()
@click.option('--input', '-i', required=True, help='Input CSV file path')
@click.option('--output', '-o', default='pii_report.json', help='Output JSON report path')
@click.option('--csv-output', '-c', help='Output directory for CSV reports')
@click.option('--anonymize', '-a', help='Path to save anonymized CSV')
@click.option('--sample-size', '-s', type=int, help='Number of rows to sample per column (default: all)')
@click.option('--no-gliner', is_flag=True, help='Disable GLiNER engine')
@click.option('--gliner-model', default='urchade/gliner_base-v2', help='GLiNER model name')
@click.option('--log-level', default='INFO', help='Logging level (DEBUG, INFO, WARNING, ERROR)')
@click.option('--quiet', '-q', is_flag=True, help='Suppress console output')
def main(input, output, csv_output, anonymize, sample_size, no_gliner, gliner_model, log_level, quiet):
    """
    PII Detection Tool - Detect Personally Identifiable Information in CSV files
    
    Examples:
        python main.py --input data.csv --output report.json
        python main.py -i data.csv -o report.json -c csv_reports/
        python main.py -i data.csv --anonymize anonymized_data.csv
        python main.py -i data.csv --sample-size 100 --no-gliner
    """
    
    # Setup logging
    if quiet:
        log_level = "ERROR"
    setup_logging(log_level)
    
    try:
        # Initialize detector
        use_gliner = not no_gliner
        detector = PIIDetector(use_gliner=use_gliner, gliner_model=gliner_model)
        
        if not quiet:
            safe_print(f"Analyzing PII in: {input}")
            safe_print(f"Using engines: {', '.join(detector.engines_used)}")
        
        # Analyze CSV
        report_generator = detector.analyze_csv(input, sample_size)
        
        # Create output directory if needed
        success, error_msg = create_output_directory(output)
        if not success:
            safe_print(f"Error creating output directory: {error_msg}")
            return
        
        # Save JSON report
        if report_generator.save_json_report(output):
            if not quiet:
                safe_print(f"JSON report saved to: {output}")
        else:
            safe_print(f"Error saving JSON report")
        
        # Save CSV reports if requested
        if csv_output:
            csv_results = report_generator.save_csv_reports(csv_output)
            if not quiet:
                for report_type, success in csv_results.items():
                    status = "SUCCESS" if success else "ERROR"
                    safe_print(f"{status} {report_type.replace('_', ' ').title()}: {csv_output}")
        
        # Anonymize data if requested
        if anonymize:
            df, _ = load_csv_data(input)
            if detector.anonymize_data(df, anonymize):
                if not quiet:
                    safe_print(f"Anonymized data saved to: {anonymize}")
            else:
                safe_print(f"Error anonymizing data")
        
        # Print summary
        if not quiet:
            safe_print("=" * 50)
            safe_print("PII DETECTION REPORT SUMMARY")
            safe_print("=" * 50)
            safe_print(f"Input File: {input}")
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
        
    except Exception as e:
        safe_print(f"Error: {str(e)}")
        if log_level == "DEBUG":
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
