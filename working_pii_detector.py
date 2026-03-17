#!/usr/bin/env python3
"""
Working PII Detector - Simple and Reliable
"""

import sys
import os
import time
import re
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional

def setup_logging():
    """Setup basic logging"""
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def validate_csv_file(file_path: str) -> bool:
    """Validate CSV file exists and is readable"""
    try:
        path = Path(file_path)
        return path.exists() and path.is_file() and file_path.endswith('.csv')
    except:
        return False

def load_csv_data(file_path: str) -> pd.DataFrame:
    """Load CSV data"""
    try:
        return pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        return pd.read_csv(file_path, encoding='latin-1')
    except Exception as e:
        raise ValueError(f"Error loading CSV: {e}")

def clean_text_data(text: str) -> str:
    """Clean text data"""
    if pd.isna(text):
        return ""
    return str(text).strip()

def detect_pii_patterns(text: str) -> List[Dict[str, Any]]:
    """Detect PII using regex patterns"""
    if not text or not isinstance(text, str):
        return []
    
    entities = []
    
    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_matches = re.finditer(email_pattern, text, re.IGNORECASE)
    for match in email_matches:
        entities.append({
            "type": "EMAIL_ADDRESS",
            "start": match.start(),
            "end": match.end(),
            "value": match.group(),
            "confidence": 0.95,
            "source": "regex"
        })
    
    # Phone pattern
    phone_pattern = r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'
    phone_matches = re.finditer(phone_pattern, text)
    for match in phone_matches:
        entities.append({
            "type": "PHONE_NUMBER",
            "start": match.start(),
            "end": match.end(),
            "value": match.group(),
            "confidence": 0.85,
            "source": "regex"
        })
    
    # Indian phone pattern
    indian_phone_pattern = r'\+91[6-9]\d{9}'
    indian_matches = re.finditer(indian_phone_pattern, text)
    for match in indian_matches:
        entities.append({
            "type": "PHONE_NUMBER",
            "start": match.start(),
            "end": match.end(),
            "value": match.group(),
            "confidence": 0.90,
            "source": "regex"
        })
    
    # Aadhaar pattern
    aadhaar_pattern = r'\b[2-9]\d{11}\b'
    aadhaar_matches = re.finditer(aadhaar_pattern, text)
    for match in aadhaar_matches:
        entities.append({
            "type": "AADHAAR",
            "start": match.start(),
            "end": match.end(),
            "value": match.group(),
            "confidence": 0.95,
            "source": "regex"
        })
    
    # PAN pattern
    pan_pattern = r'\b[A-Z]{5}\d{4}[A-Z]\b'
    pan_matches = re.finditer(pan_pattern, text)
    for match in pan_matches:
        entities.append({
            "type": "PAN",
            "start": match.start(),
            "end": match.end(),
            "value": match.group(),
            "confidence": 0.98,
            "source": "regex"
        })
    
    # Name pattern (simple)
    name_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
    name_matches = re.finditer(name_pattern, text)
    for match in name_matches:
        entities.append({
            "type": "PERSON",
            "start": match.start(),
            "end": match.end(),
            "value": match.group(),
            "confidence": 0.75,
            "source": "regex"
        })
    
    return entities

def analyze_cell(text: str) -> Dict[str, Any]:
    """Analyze a single cell for PII"""
    text = clean_text_data(text)
    
    if not text:
        return {
            "pii_detected": False,
            "entities": [],
            "confidence": 0.0,
            "pii_types": []
        }
    
    entities = detect_pii_patterns(text)
    pii_detected = len(entities) > 0
    pii_types = list(set([entity["type"] for entity in entities]))
    confidence = max([entity["confidence"] for entity in entities]) if entities else 0.0
    
    if pii_detected:
        print(f"🔍 Cell: '{text[:30]}...' -> {len(entities)} entities")
        for entity in entities:
            print(f"   - {entity['type']}: {entity['value']} (confidence: {entity['confidence']})")
    
    return {
        "pii_detected": pii_detected,
        "entities": entities,
        "confidence": confidence,
        "pii_types": pii_types
    }

def analyze_column(df: pd.DataFrame, column_name: str, sample_size: Optional[int] = None) -> Dict[str, Any]:
    """Analyze a column for PII"""
    print(f"🔍 Analyzing column: {column_name}")
    
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
    
    if sample_size and len(column_data) > sample_size:
        column_data = column_data.sample(n=sample_size, random_state=42)
    
    entities_found = []
    pii_cells = 0
    
    for cell_value in column_data:
        cell_result = analyze_cell(str(cell_value))
        
        if cell_result["pii_detected"]:
            pii_cells += 1
            entities_found.extend(cell_result["entities"])
    
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

def analyze_csv(input_file: str, sample_size: Optional[int] = None) -> Dict[str, Any]:
    """Analyze CSV file for PII"""
    print(f"📊 Loading CSV file: {input_file}")
    
    if not validate_csv_file(input_file):
        raise ValueError(f"Invalid CSV file: {input_file}")
    
    df = load_csv_data(input_file)
    
    if sample_size and len(df) > sample_size:
        df = df.sample(n=sample_size, random_state=42)
        print(f"📋 Sampled {sample_size} rows from {len(df)} total rows")
    
    column_results = {}
    total_entities = []
    
    for column_name in df.columns:
        column_result = analyze_column(df, column_name, sample_size)
        column_results[column_name] = column_result
        total_entities.extend(column_result["entities"])
    
    total_cells = sum([result["total_cells"] for result in column_results.values()])
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
        "engines_used": ["regex_patterns"]
    }

def generate_report(analysis_result: Dict[str, Any], output_file: str):
    """Generate PII report"""
    print(f"📝 Generating report: {output_file}")
    
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
    import json
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Report saved to: {output_file}")

def main():
    """Main function"""
    if len(sys.argv) < 3:
        print("Usage: python working_pii_detector.py -i input.csv -o output.json")
        print("Options:")
        print("  -s, --sample-size N: Sample N rows")
        print("  -q, --quiet: Suppress verbose output")
        return
    
    input_file = None
    output_file = None
    sample_size = None
    quiet = False
    
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
        else:
            i += 1
    
    if not input_file or not output_file:
        print("❌ Error: Both input and output files are required")
        return
    
    if not quiet:
        setup_logging()
    
    try:
        start_time = time.time()
        analysis_result = analyze_csv(input_file, sample_size)
        processing_time = time.time() - start_time
        analysis_result["processing_time"] = processing_time
        
        generate_report(analysis_result, output_file)
        
        if not quiet:
            print("\n" + "="*50)
            print("PII DETECTION REPORT SUMMARY")
            print("="*50)
            print(f"Input File: {input_file}")
            print(f"Processing Time: {processing_time:.2f} seconds")
            print(f"Engines Used: {', '.join(analysis_result['engines_used'])}")
            print()
            
            pii_columns = sum(1 for result in analysis_result["column_results"].values() if result["pii_cells"] > 0)
            total_columns = len(analysis_result["column_results"])
            
            print("Column Statistics:")
            print(f"  Total Columns: {total_columns}")
            print(f"  PII Columns: {pii_columns} ({(pii_columns/total_columns)*100:.1f}%)")
            print(f"  Non-PII Columns: {total_columns - pii_columns}")
            print()
            
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
