#!/usr/bin/env python3
"""
Production Configuration Management for PII Detection System
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
    memory_limit_mb: int = 2048
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

class ConfigManager:
    """Production configuration manager"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config = SystemConfig()
        self._load_from_file(config_file)
        self._load_from_environment()
    
    def _load_from_file(self, config_file: Optional[str]):
        """Load configuration from file"""
        if config_file and Path(config_file).exists():
            try:
                import json
                with open(config_file, 'r') as f:
                    data = json.load(f)
                self._update_config_from_dict(data)
            except Exception as e:
                print(f"Warning: Could not load config file {config_file}: {e}")
    
    def _load_from_environment(self):
        """Load configuration from environment variables"""
        env_mappings = {
            'PII_MAX_FILE_SIZE_MB': ('file_validation', 'max_file_size_mb', int),
            'PII_MAX_ROWS': ('file_validation', 'max_rows', int),
            'PII_MAX_COLUMNS': ('file_validation', 'max_columns', int),
            'PII_DEFAULT_SAMPLE_SIZE': ('processing', 'default_sample_size', int),
            'PII_MAX_PROCESSING_TIME': ('processing', 'max_processing_time_seconds', int),
            'PII_LOG_LEVEL': ('logging', 'level', str),
            'PII_LOG_FILE': ('logging', 'log_file', str),
            'PII_ENABLE_PRESIDIO': ('enable_presidio', bool),
            'PII_ENABLE_GLINER': ('enable_gliner', bool),
            'PII_ENABLE_CONSOLE_LOG': ('logging', 'enable_console_output', bool),
            'PII_RATE_LIMIT_PER_MINUTE': ('system', 'rate_limit_per_minute', int),
        }
        
        for env_var, (section, key, type_func) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    if type_func == bool:
                        value = value.lower() in ('true', '1', 'yes', 'on')
                    elif type_func == str:
                        if section == 'logging' and key == 'level':
                            value = LogLevel(value.upper())
                        else:
                            value = str(value)
                    else:
                        value = type_func(value)
                    
                    # Handle system-level config
                    if section == 'system':
                        setattr(self.config, key, value)
                    elif hasattr(getattr(self.config, section), key):
                        setattr(getattr(self.config, section), key, value)
                except Exception as e:
                    print(f"Warning: Invalid environment variable {env_var}={value}: {e}")
    
    def _update_config_from_dict(self, data: Dict[str, Any]):
        """Update configuration from dictionary"""
        if 'file_validation' in data:
            for key, value in data['file_validation'].items():
                if hasattr(self.config.file_validation, key):
                    setattr(self.config.file_validation, key, value)
        
        if 'processing' in data:
            for key, value in data['processing'].items():
                if hasattr(self.config.processing, key):
                    setattr(self.config.processing, key, value)
        
        if 'logging' in data:
            for key, value in data['logging'].items():
                if key == 'level' and isinstance(value, str):
                    value = LogLevel(value.upper())
                if hasattr(self.config.logging, key):
                    setattr(self.config.logging, key, value)
        
        # System config
        for key in ['enable_presidio', 'enable_gliner', 'fallback_to_presidio_only', 
                   'enable_data_sanitization', 'log_sensitive_data', 'rate_limit_per_minute']:
            if key in data:
                setattr(self.config, key, data[key])
        
        # Handle system section from environment variables
        for key, value in self.config.__dict__.items():
            if key.startswith('system_') and hasattr(self.config, key.replace('system_', '')):
                setattr(self.config, key.replace('system_', ''), value)

# Global configuration instance
config_manager = ConfigManager()
config = config_manager.config

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
