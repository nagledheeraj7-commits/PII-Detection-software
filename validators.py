#!/usr/bin/env python3
"""
Production-Grade Input Validation System for PII Detection
"""

import os
import pandas as pd
import mimetypes
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import hashlib

from config_simple import config
from logger import get_logger

logger = get_logger("Validator")

@dataclass
class ValidationResult:
    """Validation result container"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]

class FileValidator:
    """Production-grade file validator"""
    
    def __init__(self):
        self.max_file_size = config.file_validation.max_file_size_mb * 1024 * 1024
        self.allowed_extensions = config.file_validation.allowed_extensions
    
    def validate_file(self, file_path: str) -> ValidationResult:
        """Comprehensive file validation"""
        errors = []
        warnings = []
        metadata = {}
        
        try:
            path = Path(file_path)
            
            # 1. File existence
            if not path.exists():
                errors.append(f"File does not exist: {file_path}")
                return ValidationResult(False, errors, warnings, metadata)
            
            # 2. File size
            file_size = path.stat().st_size
            metadata['file_size_bytes'] = file_size
            metadata['file_size_mb'] = file_size / (1024 * 1024)
            
            if file_size > self.max_file_size:
                errors.append(f"File too large: {metadata['file_size_mb']:.2f}MB (max: {config.file_validation.max_file_size_mb}MB)")
            elif file_size == 0:
                errors.append("File is empty")
            
            # 3. File extension
            file_extension = path.suffix.lower()
            metadata['file_extension'] = file_extension
            
            if file_extension not in self.allowed_extensions:
                errors.append(f"Invalid file extension: {file_extension} (allowed: {', '.join(self.allowed_extensions)})")
            
            # 4. MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            metadata['mime_type'] = mime_type
            
            if mime_type and mime_type != 'text/csv':
                warnings.append(f"Unexpected MIME type: {mime_type}")
            
            # 5. File permissions
            if not os.access(file_path, os.R_OK):
                errors.append("File is not readable")
            
            # 6. File hash (for integrity)
            try:
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.md5()
                    for chunk in iter(lambda: f.read(4096), b""):
                        file_hash.update(chunk)
                    metadata['file_hash'] = file_hash.hexdigest()
            except Exception as e:
                warnings.append(f"Could not calculate file hash: {e}")
            
            logger.log_validation_result("file_validation", len(errors) == 0, 
                                        file_path=file_path, 
                                        metadata=metadata)
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            logger.error("File validation failed", exception=e, file_path=file_path)
        
        return ValidationResult(len(errors) == 0, errors, warnings, metadata)

class CSVValidator:
    """CSV-specific validator"""
    
    def validate_csv(self, file_path: str, sample_size: Optional[int] = None) -> ValidationResult:
        """Comprehensive CSV validation"""
        errors = []
        warnings = []
        metadata = {}
        
        try:
            # Try different encodings
            df = None
            encoding_used = None
            
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(file_path, encoding=encoding, nrows=sample_size)
                    encoding_used = encoding
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    errors.append(f"Error reading CSV with {encoding}: {str(e)}")
                    break
            
            if df is None:
                errors.append("Could not read CSV with any supported encoding")
                return ValidationResult(False, errors, warnings, metadata)
            
            metadata['encoding_used'] = encoding_used
            metadata['total_rows'] = len(df)
            metadata['total_columns'] = len(df.columns)
            metadata['column_names'] = list(df.columns)
            
            # 1. Row count validation
            if len(df) < config.file_validation.min_rows:
                errors.append(f"Too few rows: {len(df)} (min: {config.file_validation.min_rows})")
            elif len(df) > config.file_validation.max_rows:
                warnings.append(f"Large dataset: {len(df)} rows (consider sampling)")
            
            # 2. Column count validation
            if len(df.columns) < config.file_validation.min_columns:
                errors.append(f"Too few columns: {len(df.columns)} (min: {config.file_validation.min_columns})")
            elif len(df.columns) > config.file_validation.max_columns:
                warnings.append(f"Many columns: {len(df.columns)} (max: {config.file_validation.max_columns})")
            
            # 3. Column name validation
            invalid_columns = []
            duplicate_columns = []
            seen_columns = set()
            
            for col in df.columns:
                # Check for invalid column names
                if not isinstance(col, str) or not col.strip():
                    invalid_columns.append(str(col))
                
                # Check for duplicates
                col_str = str(col).strip()
                if col_str in seen_columns:
                    duplicate_columns.append(col_str)
                seen_columns.add(col_str)
            
            if invalid_columns:
                errors.append(f"Invalid column names: {invalid_columns}")
            
            if duplicate_columns:
                warnings.append(f"Duplicate column names: {duplicate_columns}")
            
            # 4. Data quality checks
            null_counts = df.isnull().sum()
            metadata['null_counts'] = null_counts.to_dict()
            metadata['null_percentage'] = (null_counts / len(df) * 100).round(2).to_dict()
            
            # Check for completely empty columns
            empty_columns = [col for col, count in null_counts.items() if count == len(df)]
            if empty_columns:
                warnings.append(f"Completely empty columns: {empty_columns}")
            
            # Check for columns with high null percentages
            high_null_columns = [col for col, pct in metadata['null_percentage'].items() if pct > 90]
            if high_null_columns:
                warnings.append(f"High null percentage columns: {high_null_columns}")
            
            # 5. Cell content validation
            max_cell_length = 0
            total_cells = 0
            empty_cells = 0
            
            for col in df.columns:
                for value in df[col]:
                    total_cells += 1
                    if pd.isna(value) or str(value).strip() == '':
                        empty_cells += 1
                    else:
                        cell_length = len(str(value))
                        if cell_length > max_cell_length:
                            max_cell_length = cell_length
            
            metadata['total_cells'] = total_cells
            metadata['empty_cells'] = empty_cells
            metadata['empty_cell_percentage'] = (empty_cells / total_cells * 100) if total_cells > 0 else 0
            metadata['max_cell_length'] = max_cell_length
            
            if max_cell_length > config.file_validation.max_cell_length:
                warnings.append(f"Very long cells detected: {max_cell_length} characters")
            
            # 6. Data type analysis
            column_types = {}
            for col in df.columns:
                # Get non-null values
                non_null_values = df[col].dropna()
                if len(non_null_values) > 0:
                    # Analyze data types
                    numeric_count = sum(1 for v in non_null_values if str(v).replace('.', '').replace('-', '').isdigit())
                    string_count = len(non_null_values) - numeric_count
                    
                    column_types[col] = {
                        'numeric_ratio': numeric_count / len(non_null_values),
                        'string_ratio': string_count / len(non_null_values),
                        'unique_count': non_null_values.nunique(),
                        'unique_ratio': non_null_values.nunique() / len(non_null_values)
                    }
            
            metadata['column_types'] = column_types
            
            logger.log_validation_result("csv_validation", len(errors) == 0,
                                        file_path=file_path,
                                        encoding=encoding_used,
                                        rows=len(df),
                                        columns=len(df.columns))
            
        except Exception as e:
            errors.append(f"CSV validation error: {str(e)}")
            logger.error("CSV validation failed", exception=e, file_path=file_path)
        
        return ValidationResult(len(errors) == 0, errors, warnings, metadata)

class ProcessingValidator:
    """Processing parameter validator"""
    
    def validate_processing_params(self, 
                                  sample_size: Optional[int] = None,
                                  use_gliner: bool = True,
                                  use_presidio: bool = True) -> ValidationResult:
        """Validate processing parameters"""
        errors = []
        warnings = []
        metadata = {}
        
        # Sample size validation
        if sample_size is not None:
            if sample_size <= 0:
                errors.append("Sample size must be positive")
            elif sample_size > config.processing.default_sample_size:
                warnings.append(f"Large sample size: {sample_size} (default: {config.processing.default_sample_size})")
            
            metadata['sample_size'] = sample_size
        
        # Engine validation
        if not use_gliner and not use_presidio:
            errors.append("At least one detection engine must be enabled")
        
        if not config.enable_gliner and use_gliner:
            warnings.append("GLiNER is disabled in configuration")
        
        if not config.enable_presidio and use_presidio:
            warnings.append("Presidio is disabled in configuration")
        
        metadata['use_gliner'] = use_gliner
        metadata['use_presidio'] = use_presidio
        
        return ValidationResult(len(errors) == 0, errors, warnings, metadata)

class SystemValidator:
    """System health validator"""
    
    def validate_system(self) -> ValidationResult:
        """Validate system health and dependencies"""
        errors = []
        warnings = []
        metadata = {}
        
        try:
            # 1. Memory check
            import psutil
            memory = psutil.virtual_memory()
            metadata['memory_total_gb'] = memory.total / (1024**3)
            metadata['memory_available_gb'] = memory.available / (1024**3)
            metadata['memory_usage_percent'] = memory.percent
            
            if memory.available < config.processing.memory_limit_mb * 1024 * 1024:
                warnings.append(f"Low available memory: {metadata['memory_available_gb']:.2f}GB")
            
            # 2. Disk space check
            disk = psutil.disk_usage('.')
            metadata['disk_free_gb'] = disk.free / (1024**3)
            
            if disk.free < 1024**3:  # Less than 1GB
                warnings.append("Low disk space")
            
            # 3. Engine availability
            engines_status = {}
            
            # Presidio check
            try:
                from presidio_analyzer import AnalyzerEngine
                analyzer = AnalyzerEngine()
                engines_status['presidio'] = 'available'
            except Exception as e:
                engines_status['presidio'] = f'unavailable: {str(e)}'
                if config.enable_presidio:
                    warnings.append(f"Presidio not available: {e}")
            
            # GLiNER check
            try:
                from pii_detector.gliner_engine_fixed import GLiNERPIIEngine
                gliner = GLiNERPIIEngine()
                status = gliner.get_status()
                engines_status['gliner'] = 'available' if status['model_loaded'] or status['using_fallback'] else 'unavailable'
            except Exception as e:
                engines_status['gliner'] = f'unavailable: {str(e)}'
                if config.enable_gliner:
                    warnings.append(f"GLiNER not available: {e}")
            
            metadata['engines_status'] = engines_status
            
            logger.log_validation_result("system_validation", len(errors) == 0, metadata=metadata)
            
        except ImportError as e:
            warnings.append(f"Optional dependency not available: {e}")
        except Exception as e:
            errors.append(f"System validation error: {str(e)}")
            logger.error("System validation failed", exception=e)
        
        return ValidationResult(len(errors) == 0, errors, warnings, metadata)

# Global validator instances
file_validator = FileValidator()
csv_validator = CSVValidator()
processing_validator = ProcessingValidator()
system_validator = SystemValidator()

def validate_all(file_path: str, 
                sample_size: Optional[int] = None,
                use_gliner: bool = True,
                use_presidio: bool = True) -> Tuple[ValidationResult, ValidationResult, ValidationResult, ValidationResult]:
    """Run all validations"""
    
    file_result = file_validator.validate_file(file_path)
    csv_result = csv_validator.validate_csv(file_path, sample_size)
    processing_result = processing_validator.validate_processing_params(sample_size, use_gliner, use_presidio)
    system_result = system_validator.validate_system()
    
    return file_result, csv_result, processing_result, system_result
