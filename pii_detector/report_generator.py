"""
Report Generator for PII Detection Results
"""

import json
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from pathlib import Path


class PIIReportGenerator:
    """
    Generate comprehensive PII detection reports in JSON and CSV formats
    """
    
    def __init__(self):
        """Initialize report generator"""
        self.report_data = {
            "metadata": {},
            "columns": [],
            "rows": [],
            "summary": {}
        }
    
    def add_metadata(self, input_file: str, total_rows: int, total_columns: int, 
                     processing_time: float, engines_used: List[str]):
        """
        Add metadata to the report
        
        Args:
            input_file: Input CSV file path
            total_rows: Total number of rows processed
            total_columns: Total number of columns processed
            processing_time: Total processing time in seconds
            engines_used: List of engines used for detection
        """
        self.report_data["metadata"] = {
            "input_file": input_file,
            "total_rows": total_rows,
            "total_columns": total_columns,
            "processing_time_seconds": round(processing_time, 2),
            "engines_used": engines_used,
            "report_generated_at": datetime.now().isoformat(),
            "report_version": "1.0"
        }
    
    def add_column_summary(self, column_name: str, is_pii: bool, pii_types: List[str], 
                          pii_percentage: float, total_rows: int, pii_rows: int,
                          avg_confidence: float = 0.0):
        """
        Add column-level PII summary
        
        Args:
            column_name: Name of the column
            is_pii: Whether column contains PII
            pii_types: List of PII types detected
            pii_percentage: Percentage of rows with PII
            total_rows: Total rows in column
            pii_rows: Number of rows with PII
            avg_confidence: Average confidence score
        """
        column_summary = {
            "name": column_name,
            "is_pii": is_pii,
            "pii_types": pii_types if pii_types else [],
            "pii_percentage": round(pii_percentage, 2),
            "total_rows": total_rows,
            "pii_rows": pii_rows,
            "non_pii_rows": total_rows - pii_rows,
            "avg_confidence": round(avg_confidence, 3) if avg_confidence > 0 else None
        }
        
        self.report_data["columns"].append(column_summary)
    
    def add_row_result(self, row_number: int, column_name: str, value: str,
                      pii_detected: bool, entity_type: str, confidence: float,
                      source_engine: str = "presidio"):
        """
        Add row-level PII detection result
        
        Args:
            row_number: Row number (1-based)
            column_name: Column name
            value: Cell value
            pii_detected: Whether PII was detected
            entity_type: Type of PII entity detected
            confidence: Confidence score
            source_engine: Engine that detected the PII
        """
        row_result = {
            "row": row_number,
            "column": column_name,
            "value": value,
            "pii_detected": pii_detected,
            "entity": entity_type if pii_detected else None,
            "confidence": round(confidence, 3) if pii_detected else None,
            "source_engine": source_engine
        }
        
        self.report_data["rows"].append(row_result)
    
    def generate_summary(self):
        """Generate overall summary statistics"""
        columns = self.report_data["columns"]
        rows = self.report_data["rows"]
        
        # Column statistics
        total_columns = len(columns)
        pii_columns = sum(1 for col in columns if col["is_pii"])
        
        # Row statistics
        total_rows = len(set(row["row"] for row in rows))
        pii_detections = sum(1 for row in rows if row["pii_detected"])
        
        # PII type distribution
        pii_types = {}
        for row in rows:
            if row["pii_detected"] and row["entity"]:
                entity_type = row["entity"]
                pii_types[entity_type] = pii_types.get(entity_type, 0) + 1
        
        # Confidence statistics
        confidences = [row["confidence"] for row in rows if row["confidence"] is not None]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        self.report_data["summary"] = {
            "total_columns": total_columns,
            "pii_columns": pii_columns,
            "non_pii_columns": total_columns - pii_columns,
            "pii_column_percentage": round((pii_columns / total_columns) * 100, 2) if total_columns > 0 else 0,
            "total_rows_processed": total_rows,
            "total_pii_detections": pii_detections,
            "pii_type_distribution": pii_types,
            "avg_confidence_score": round(avg_confidence, 3),
            "most_common_pii_type": max(pii_types.items(), key=lambda x: x[1])[0] if pii_types else None
        }
    
    def save_json_report(self, output_path: str) -> bool:
        """
        Save report as JSON file
        
        Args:
            output_path: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate summary before saving
            self.generate_summary()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.report_data, f, indent=2, ensure_ascii=False)
            
            logging.info(f"JSON report saved to: {output_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving JSON report: {e}")
            return False
    
    def save_csv_reports(self, output_dir: str) -> Dict[str, bool]:
        """
        Save reports as CSV files (column summary and row details)
        
        Args:
            output_dir: Output directory path
            
        Returns:
            Dictionary with success status for each file
        """
        results = {}
        
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Generate summary before saving
            self.generate_summary()
            
            # Save column summary CSV
            if self.report_data["columns"]:
                column_df = pd.DataFrame(self.report_data["columns"])
                column_csv_path = output_path / "pii_column_summary.csv"
                column_df.to_csv(column_csv_path, index=False)
                results["column_summary"] = True
                logging.info(f"Column summary CSV saved to: {column_csv_path}")
            else:
                results["column_summary"] = False
            
            # Save row details CSV
            if self.report_data["rows"]:
                row_df = pd.DataFrame(self.report_data["rows"])
                row_csv_path = output_path / "pii_row_details.csv"
                row_df.to_csv(row_csv_path, index=False)
                results["row_details"] = True
                logging.info(f"Row details CSV saved to: {row_csv_path}")
            else:
                results["row_details"] = False
            
            # Save summary statistics CSV
            if self.report_data["summary"]:
                # Convert summary to flat format for CSV
                summary_data = []
                for key, value in self.report_data["summary"].items():
                    if key == "pii_type_distribution":
                        for pii_type, count in value.items():
                            summary_data.append({
                                "metric": f"pii_type_{pii_type}",
                                "value": count
                            })
                    else:
                        summary_data.append({
                            "metric": key,
                            "value": value
                        })
                
                summary_df = pd.DataFrame(summary_data)
                summary_csv_path = output_path / "pii_summary_stats.csv"
                summary_df.to_csv(summary_csv_path, index=False)
                results["summary_stats"] = True
                logging.info(f"Summary statistics CSV saved to: {summary_csv_path}")
            else:
                results["summary_stats"] = False
            
            return results
            
        except Exception as e:
            logging.error(f"Error saving CSV reports: {e}")
            return {"column_summary": False, "row_details": False, "summary_stats": False}
    
    def print_summary(self):
        """Print a summary of the report to console"""
        if not self.report_data["summary"]:
            self.generate_summary()
        
        summary = self.report_data["summary"]
        metadata = self.report_data["metadata"]
        
        print("\n" + "="*50)
        print("PII DETECTION REPORT SUMMARY")
        print("="*50)
        
        print(f"Input File: {metadata.get('input_file', 'N/A')}")
        print(f"Processing Time: {metadata.get('processing_time_seconds', 0)} seconds")
        print(f"Engines Used: {', '.join(metadata.get('engines_used', []))}")
        
        print(f"\nColumn Statistics:")
        print(f"  Total Columns: {summary['total_columns']}")
        print(f"  PII Columns: {summary['pii_columns']} ({summary['pii_column_percentage']}%)")
        print(f"  Non-PII Columns: {summary['non_pii_columns']}")
        
        print(f"\nRow Statistics:")
        print(f"  Total Rows Processed: {summary['total_rows_processed']}")
        print(f"  Total PII Detections: {summary['total_pii_detections']}")
        print(f"  Average Confidence: {summary['avg_confidence_score']}")
        
        if summary['pii_type_distribution']:
            print(f"\nPII Type Distribution:")
            for pii_type, count in sorted(summary['pii_type_distribution'].items(), 
                                        key=lambda x: x[1], reverse=True):
                print(f"  {pii_type}: {count}")
        
        print("="*50)
    
    def get_high_risk_columns(self, threshold_percentage: float = 50.0) -> List[Dict]:
        """
        Get columns with high PII risk
        
        Args:
            threshold_percentage: Minimum PII percentage to consider high risk
            
        Returns:
            List of high-risk column summaries
        """
        high_risk_columns = []
        
        for column in self.report_data["columns"]:
            if column["is_pii"] and column["pii_percentage"] >= threshold_percentage:
                high_risk_columns.append(column)
        
        return high_risk_columns
    
    def get_pii_type_coverage(self) -> Dict[str, Dict]:
        """
        Get coverage statistics for each PII type
        
        Returns:
            Dictionary with PII type coverage statistics
        """
        coverage = {}
        
        for column in self.report_data["columns"]:
            if column["is_pii"]:
                for pii_type in column["pii_types"]:
                    if pii_type not in coverage:
                        coverage[pii_type] = {
                            "columns_affected": 0,
                            "total_detections": 0,
                            "avg_confidence": []
                        }
                    
                    coverage[pii_type]["columns_affected"] += 1
                    if column["avg_confidence"]:
                        coverage[pii_type]["avg_confidence"].append(column["avg_confidence"])
        
        # Calculate totals and averages
        for row in self.report_data["rows"]:
            if row["pii_detected"] and row["entity"]:
                entity_type = row["entity"]
                if entity_type in coverage:
                    coverage[entity_type]["total_detections"] += 1
        
        # Calculate average confidence
        for pii_type in coverage:
            confidences = coverage[pii_type]["avg_confidence"]
            if confidences:
                coverage[pii_type]["avg_confidence"] = sum(confidences) / len(confidences)
            else:
                coverage[pii_type]["avg_confidence"] = 0
        
        return coverage
