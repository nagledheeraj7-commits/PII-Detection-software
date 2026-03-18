#!/usr/bin/env python3
"""
Simple PII Detector - Works without heavy ML dependencies
Uses regex patterns for basic PII detection
"""

import pandas as pd
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime


class SimplePIIDetector:
    """
    Simple PII detection using regex patterns
    """
    
    def __init__(self):
        """Initialize PII patterns"""
        self.patterns = {
            'EMAIL': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'PHONE_US': r'^(\+1[\s-]?)?\(?[0-9]{3}\)?[\s-]?[0-9]{3}[\s-]?[0-9]{4}$',
            'PHONE_IN': r'^(\+91[\s-]?)?[0-9]{10}$',
            'PHONE_GENERAL': r'^[\+]?[0-9\s\-\(\)]{10,}$',
            'AADHAAR': r'^[2-9]\d{11}$',
            'PAN': r'^[A-Z]{5}\d{4}[A-Z]$',
            'NAME': r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',
            'ZIP_US': r'^\d{5}(-\d{4})?$',
            'DATE': r'\b(0[1-9]|1[0-2])/(0[1-9]|[12][0-9]|3[01])/\d{4}\b'
        }
    
    def detect_pii(self, text: str) -> Dict[str, Any]:
        """
        Detect PII in text using regex patterns
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with PII detection results
        """
        if pd.isna(text) or text == "":
            return {
                "has_pii": False,
                "pii_types": [],
                "entities": [],
                "confidence": 0.0
            }
        
        text = str(text).strip()
        detected_entities = []
        pii_types = []
        
        for pii_type, pattern in self.patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                detected_entities.append({
                    "type": pii_type,
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.85  # Fixed confidence for regex
                })
                pii_types.append(pii_type)
        
        return {
            "has_pii": len(detected_entities) > 0,
            "pii_types": list(set(pii_types)),
            "entities": detected_entities,
            "confidence": max([e["confidence"] for e in detected_entities], default=0.0)
        }
    
    def analyze_column(self, df: pd.DataFrame, column_name: str) -> Dict[str, Any]:
        """
        Analyze a column for PII
        
        Args:
            df: DataFrame
            column_name: Column name
            
        Returns:
            Dictionary with column analysis results
        """
        column_data = df[column_name].dropna()
        pii_flags = []
        pii_types_per_row = []
        confidences = []
        row_results = []
        
        for idx, value in enumerate(column_data):
            row_num = idx + 1
            analysis = self.detect_pii(str(value))
            
            pii_flags.append(analysis["has_pii"])
            pii_types_per_row.extend(analysis["pii_types"])
            
            if analysis["has_pii"]:
                confidences.append(analysis["confidence"])
            
            # Add row result for each detected entity
            if analysis["entities"]:
                for entity in analysis["entities"]:
                    row_results.append({
                        "row": row_num,
                        "column": column_name,
                        "value": str(value),
                        "pii_detected": True,
                        "entity": entity["type"],
                        "confidence": entity["confidence"]
                    })
            else:
                row_results.append({
                    "row": row_num,
                    "column": column_name,
                    "value": str(value),
                    "pii_detected": False,
                    "entity": None,
                    "confidence": 0.0
                })
        
        # Calculate statistics
        total_rows = len(column_data)
        pii_rows = sum(pii_flags)
        pii_percentage = (pii_rows / total_rows * 100) if total_rows > 0 else 0
        unique_pii_types = list(set(pii_types_per_row))
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return {
            "column_name": column_name,
            "is_pii": pii_rows > 0,
            "pii_types": unique_pii_types,
            "pii_percentage": round(pii_percentage, 2),
            "total_rows": total_rows,
            "pii_rows": pii_rows,
            "avg_confidence": round(avg_confidence, 3),
            "row_results": row_results
        }
    
    def analyze_csv(self, input_file: str) -> Dict[str, Any]:
        """
        Analyze entire CSV file for PII
        
        Args:
            input_file: Path to CSV file
            
        Returns:
            Dictionary with complete analysis results
        """
        print(f"🔍 Analyzing PII in: {input_file}")
        
        # Load CSV
        try:
            df = pd.read_csv(input_file)
            print(f"📊 Loaded CSV: {df.shape} (rows x columns)")
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return {}
        
        start_time = datetime.now()
        
        # Analyze each column
        all_columns = []
        all_rows = []
        pii_types_count = {}
        
        for column_name in df.columns:
            print(f"🔍 Analyzing column: {column_name}")
            
            column_analysis = self.analyze_column(df, column_name)
            
            # Add column summary
            all_columns.append({
                "name": column_analysis["column_name"],
                "is_pii": column_analysis["is_pii"],
                "pii_types": column_analysis["pii_types"],
                "pii_percentage": column_analysis["pii_percentage"],
                "total_rows": column_analysis["total_rows"],
                "pii_rows": column_analysis["pii_rows"],
                "avg_confidence": column_analysis["avg_confidence"]
            })
            
            # Add row results
            all_rows.extend(column_analysis["row_results"])
            
            # Count PII types
            for pii_type in column_analysis["pii_types"]:
                pii_types_count[pii_type] = pii_types_count.get(pii_type, 0) + column_analysis["pii_rows"]
        
        # Calculate summary
        processing_time = (datetime.now() - start_time).total_seconds()
        total_columns = len(all_columns)
        pii_columns = sum(1 for col in all_columns if col["is_pii"])
        total_pii_detections = len([row for row in all_rows if row["pii_detected"]])
        
        result = {
            "metadata": {
                "input_file": input_file,
                "total_rows": len(df),
                "total_columns": total_columns,
                "processing_time_seconds": round(processing_time, 2),
                "engines_used": ["regex_patterns"],
                "report_generated_at": datetime.now().isoformat(),
                "report_version": "1.0"
            },
            "columns": all_columns,
            "rows": all_rows,
            "summary": {
                "total_columns": total_columns,
                "pii_columns": pii_columns,
                "non_pii_columns": total_columns - pii_columns,
                "pii_column_percentage": round((pii_columns / total_columns) * 100, 2) if total_columns > 0 else 0,
                "total_rows_processed": len(df),
                "total_pii_detections": total_pii_detections,
                "pii_type_distribution": pii_types_count,
                "most_common_pii_type": max(pii_types_count.items(), key=lambda x: x[1])[0] if pii_types_count else None
            }
        }
        
        return result
    
    def save_report(self, result: Dict[str, Any], output_file: str):
        """Save analysis result to JSON file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"✅ Report saved to: {output_file}")
        except Exception as e:
            print(f"❌ Error saving report: {e}")
    
    def print_summary(self, result: Dict[str, Any]):
        """Print analysis summary"""
        if not result:
            return
        
        summary = result["summary"]
        metadata = result["metadata"]
        
        print("\n" + "="*50)
        print("PII DETECTION REPORT SUMMARY")
        print("="*50)
        
        print(f"Input File: {metadata['input_file']}")
        print(f"Processing Time: {metadata['processing_time_seconds']} seconds")
        print(f"Engine Used: {', '.join(metadata['engines_used'])}")
        
        print(f"\nColumn Statistics:")
        print(f"  Total Columns: {summary['total_columns']}")
        print(f"  PII Columns: {summary['pii_columns']} ({summary['pii_column_percentage']}%)")
        print(f"  Non-PII Columns: {summary['non_pii_columns']}")
        
        print(f"\nRow Statistics:")
        print(f"  Total Rows Processed: {summary['total_rows_processed']}")
        print(f"  Total PII Detections: {summary['total_pii_detections']}")
        
        if summary['pii_type_distribution']:
            print(f"\nPII Type Distribution:")
            for pii_type, count in sorted(summary['pii_type_distribution'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {pii_type}: {count}")
        
        # Show high-risk columns
        high_risk_columns = [col for col in result["columns"] if col["pii_percentage"] >= 50]
        if high_risk_columns:
            print(f"\n⚠️  High-Risk Columns (>50% PII):")
            for col in high_risk_columns:
                print(f"   - {col['name']}: {col['pii_percentage']}% PII ({', '.join(col['pii_types'])})")
        
        print("="*50)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Simple PII Detection Tool")
    parser.add_argument('-i', '--input', required=True, help='Input CSV file path')
    parser.add_argument('-o', '--output', default='pii_report.json', help='Output JSON report path')
    parser.add_argument('-q', '--quiet', action='store_true', help='Suppress console output')
    
    args = parser.parse_args()
    
    # Initialize detector
    detector = SimplePIIDetector()
    
    # Analyze CSV
    result = detector.analyze_csv(args.input)
    
    if result:
        # Save report
        detector.save_report(result, args.output)
        
        # Print summary
        if not args.quiet:
            detector.print_summary(result)
        
        print(f"\n🎉 Analysis completed successfully!")
    else:
        print("❌ Analysis failed!")


if __name__ == "__main__":
    main()
