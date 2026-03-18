#!/usr/bin/env python3
"""
Simple Configuration Management for PII Detection System
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class FileValidationConfig:
    """File validation configuration"""
    max_file_size_mb: int = 100
    max_rows: int = 100000
    max_columns: int = 1000
    allowed_extensions: list = field(default_factory=lambda: ['.csv'])
    min_rows: int = 1
    min_columns: int = 1
    max_cell_length: int = 50000

@dataclass
class ProcessingConfig:
    """Processing configuration"""
    default_sample_size: int = 10000
    max_processing_time_seconds: int = 300
    memory_limit_mb: int = 4096
    enable_parallel_processing: bool = False
    max_workers: int = 4

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: LogLevel = LogLevel.INFO
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = "pii_detection.log"
    max_log_size_mb: int = 50
    backup_count: int = 5
    enable_console_output: bool = True

@dataclass
class SystemConfig:
    """System-wide configuration"""
    file_validation: FileValidationConfig = field(default_factory=FileValidationConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # Engine configuration
    enable_presidio: bool = True
    enable_gliner: bool = True
    fallback_to_presidio_only: bool = True
    
    # Security settings
    enable_data_sanitization: bool = True
    log_sensitive_data: bool = False
    
    # Rate limiting
    rate_limit_per_minute: int = 10

# Global configuration instance
config = SystemConfig()

def setup_logging():
    """Setup logging system (call this at application startup)"""
    try:
        from logger import get_logger
        logger = get_logger("Config")
        logger.info("Logging system initialized", 
                   level=config.logging.level.value,
                   log_file=config.logging.log_file,
                   console_output=config.logging.enable_console_output)
    except ImportError:
        # Logger not available yet, use basic print
        print(f"Logging configured: {config.logging.level.value}, file: {config.logging.log_file}")
