"""
Utility functions for PII detection and data processing
"""

import pandas as pd
import numpy as np
import os
from typing import Dict, List, Any, Tuple, Optional
import logging
from pathlib import Path


def validate_csv_file(file_path: str) -> Tuple[bool, str]:
    """
    Validate if the file is a proper CSV file
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            return False, f"File not found: {file_path}"
        
        # Check if it's a file
        if not path.is_file():
            return False, f"Path is not a file: {file_path}"
        
        # Check file extension
        if path.suffix.lower() != '.csv':
            return False, f"File is not a CSV file: {file_path}"
        
        # Try to read CSV
        try:
            df = pd.read_csv(file_path, nrows=1)
            if df.empty:
                return False, f"CSV file is empty: {file_path}"
        except pd.errors.EmptyDataError:
            return False, f"CSV file is empty: {file_path}"
        except pd.errors.ParserError as e:
            return False, f"CSV parsing error: {str(e)}"
        except Exception as e:
            return False, f"Error reading CSV file: {str(e)}"
        
        return True, ""
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def load_csv_data(file_path: str, encoding: str = 'utf-8') -> Tuple[Optional[pd.DataFrame], str]:
    """
    Load CSV data with proper error handling
    
    Args:
        file_path: Path to the CSV file
        encoding: File encoding
        
    Returns:
        Tuple of (dataframe, error_message)
    """
    try:
        # Try different encodings if utf-8 fails
        encodings = [encoding, 'latin-1', 'cp1252', 'iso-8859-1']
        
        for enc in encodings:
            try:
                df = pd.read_csv(file_path, encoding=enc)
                logging.info(f"Successfully loaded CSV with encoding: {enc}")
                return df, ""
            except UnicodeDecodeError:
                continue
            except Exception as e:
                return None, f"Error reading CSV: {str(e)}"
        
        return None, f"Could not read CSV with any of the encodings: {encodings}"
        
    except Exception as e:
        return None, f"Unexpected error loading CSV: {str(e)}"


def clean_text_data(text: Any) -> str:
    """
    Clean and normalize text data
    
    Args:
        text: Raw text data
        
    Returns:
        Cleaned text string
    """
    if pd.isna(text) or text is None:
        return ""
    
    # Convert to string
    text = str(text).strip()
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    return text


def calculate_pii_percentage(pii_flags: List[bool]) -> float:
    """
    Calculate percentage of rows containing PII
    
    Args:
        pii_flags: List of boolean flags indicating PII presence
        
    Returns:
        Percentage of rows with PII (0-100)
    """
    if not pii_flags:
        return 0.0
    
    pii_count = sum(pii_flags)
    total_count = len(pii_flags)
    
    return round((pii_count / total_count) * 100, 2)


def get_column_statistics(df: pd.DataFrame, column_name: str) -> Dict[str, Any]:
    """
    Get basic statistics for a column
    
    Args:
        df: DataFrame
        column_name: Column name
        
    Returns:
        Dictionary with column statistics
    """
    if column_name not in df.columns:
        return {}
    
    series = df[column_name]
    
    stats = {
        "total_rows": len(series),
        "non_null_rows": series.count(),
        "null_rows": series.isnull().sum(),
        "unique_values": series.nunique(),
        "data_type": str(series.dtype)
    }
    
    # Add text-specific stats
    if series.dtype == 'object':
        non_null_series = series.dropna()
        if not non_null_series.empty:
            text_lengths = non_null_series.astype(str).str.len()
            stats.update({
                "avg_text_length": round(text_lengths.mean(), 2),
                "min_text_length": int(text_lengths.min()),
                "max_text_length": int(text_lengths.max())
            })
    
    return stats


def detect_column_data_type(df: pd.DataFrame, column_name: str) -> str:
    """
    Detect the likely data type of a column
    
    Args:
        df: DataFrame
        column_name: Column name
        
    Returns:
        Detected data type as string
    """
    if column_name not in df.columns:
        return "unknown"
    
    series = df[column_name].dropna()
    
    if series.empty:
        return "empty"
    
    # Sample first few non-null values
    sample_size = min(100, len(series))
    sample_values = series.head(sample_size).astype(str)
    
    # Check for common patterns
    email_pattern = sample_values.str.contains(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', case=False, na=False)
    if email_pattern.any():
        return "email"
    
    phone_pattern = sample_values.str.contains(r'^[\+]?[0-9\s\-\(\)]{10,}$', case=False, na=False)
    if phone_pattern.any():
        return "phone"
    
    # Check if all are numeric
    try:
        pd.to_numeric(sample_values)
        return "numeric"
    except:
        pass
    
    # Check if all are dates
    try:
        pd.to_datetime(sample_values, errors='raise')
        return "date"
    except:
        pass
    
    # Check for ID patterns
    try:
        id_pattern = sample_values.str.match(r'^[A-Z0-9]{6,}$', case=False, na=False)
        if id_pattern.any():
            return "id"
    except:
        pass
    
    return "text"


def merge_detection_results(presidio_results: List[Dict], gliner_results: List[Dict]) -> List[Dict]:
    """
    Merge detection results from Presidio and GLiNER
    
    Args:
        presidio_results: Results from Presidio engine
        gliner_results: Results from GLiNER engine
        
    Returns:
        Merged results
    """
    if not presidio_results and not gliner_results:
        return []
    
    if not presidio_results:
        return gliner_results
    
    if not gliner_results:
        return presidio_results
    
    # Combine results and remove duplicates
    all_results = presidio_results + gliner_results
    
    # Remove overlapping entities (keep the one with higher confidence)
    unique_results = []
    
    for result in sorted(all_results, key=lambda x: x.get('confidence', 0), reverse=True):
        is_duplicate = False
        
        for unique_result in unique_results:
            # Check for overlap
            if (result['start'] <= unique_result['end'] and 
                result['end'] >= unique_result['start']):
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_results.append(result)
    
    return unique_results


def format_confidence_score(score: float) -> str:
    """
    Format confidence score as percentage string
    
    Args:
        score: Confidence score (0-1)
        
    Returns:
        Formatted percentage string
    """
    if score is None:
        return "N/A"
    
    return f"{round(score * 100, 1)}%"


def create_output_directory(output_path: str) -> Tuple[bool, str]:
    """
    Create output directory if it doesn't exist
    
    Args:
        output_path: Output file path
        
    Returns:
        Tuple of (success, error_message)
    """
    try:
        path = Path(output_path)
        parent_dir = path.parent
        
        if not parent_dir.exists():
            parent_dir.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created output directory: {parent_dir}")
        
        return True, ""
        
    except Exception as e:
        return False, f"Error creating output directory: {str(e)}"


def validate_file_permissions(file_path: str, mode: str = 'r') -> Tuple[bool, str]:
    """
    Validate file permissions
    
    Args:
        file_path: File path to check
        mode: Permission mode ('r' for read, 'w' for write)
        
    Returns:
        Tuple of (has_permission, error_message)
    """
    try:
        path = Path(file_path)
        
        if mode == 'r':
            if not path.exists():
                return False, "File does not exist"
            if not os.access(file_path, os.R_OK):
                return False, "No read permission"
        elif mode == 'w':
            parent_dir = path.parent
            if not parent_dir.exists():
                return False, "Parent directory does not exist"
            if not os.access(parent_dir, os.W_OK):
                return False, "No write permission"
        
        return True, ""
        
    except Exception as e:
        return False, f"Permission check error: {str(e)}"


def setup_logging(log_level: str = "INFO") -> None:
    """
    Setup logging configuration
    
    Args:
        log_level: Logging level
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('pii_detection.log')
        ]
    )
