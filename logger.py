#!/usr/bin/env python3
"""
Production-Grade Logging System for PII Detection
"""

import logging
import logging.handlers
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, Optional
from contextlib import contextmanager
from functools import wraps
import json

from config_simple import config, LogLevel

class PIIDetectionLogger:
    """Production-grade logger for PII detection system"""
    
    def __init__(self, name: str = "PII_Detection"):
        self.name = name
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger with production configuration"""
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set log level
        self.logger.setLevel(getattr(logging, config.logging.level.value))
        
        # Create formatter
        formatter = logging.Formatter(config.logging.log_format)
        
        # File handler with rotation
        if config.logging.log_file:
            log_path = Path(config.logging.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_path,
                maxBytes=config.logging.max_log_size_mb * 1024 * 1024,
                backupCount=config.logging.backup_count
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Console handler
        if config.logging.enable_console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def _sanitize_data(self, data: Any) -> Any:
        """Sanitize sensitive data for logging"""
        if not config.log_sensitive_data:
            if isinstance(data, str):
                # Mask potential PII patterns
                import re
                # Email patterns
                data = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', data)
                # Phone patterns
                data = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', data)
                # SSN patterns
                data = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', data)
                # Credit card patterns
                data = re.sub(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', '[CARD]', data)
            elif isinstance(data, dict):
                return {k: self._sanitize_data(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [self._sanitize_data(item) for item in data]
        
        return data
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        sanitized_message = self._sanitize_data(message)
        if kwargs:
            sanitized_kwargs = self._sanitize_data(kwargs)
            self.logger.debug(f"{sanitized_message} | {sanitized_kwargs}")
        else:
            self.logger.debug(sanitized_message)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        sanitized_message = self._sanitize_data(message)
        if kwargs:
            sanitized_kwargs = self._sanitize_data(kwargs)
            self.logger.info(f"{sanitized_message} | {sanitized_kwargs}")
        else:
            self.logger.info(sanitized_message)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        sanitized_message = self._sanitize_data(message)
        if kwargs:
            sanitized_kwargs = self._sanitize_data(kwargs)
            self.logger.warning(f"{sanitized_message} | {sanitized_kwargs}")
        else:
            self.logger.warning(sanitized_message)
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message with exception details"""
        sanitized_message = self._sanitize_data(message)
        
        if exception:
            error_details = {
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'traceback': traceback.format_exc()
            }
            if kwargs:
                error_details.update(self._sanitize_data(kwargs))
            self.logger.error(f"{sanitized_message} | {error_details}")
        else:
            if kwargs:
                sanitized_kwargs = self._sanitize_data(kwargs)
                self.logger.error(f"{sanitized_message} | {sanitized_kwargs}")
            else:
                self.logger.error(sanitized_message)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        sanitized_message = self._sanitize_data(message)
        if kwargs:
            sanitized_kwargs = self._sanitize_data(kwargs)
            self.logger.critical(f"{sanitized_message} | {sanitized_kwargs}")
        else:
            self.logger.critical(sanitized_message)
    
    def log_performance(self, operation: str, duration: float, **metrics):
        """Log performance metrics"""
        self.info(f"Performance: {operation}", 
                 duration_seconds=duration, 
                 **metrics)
    
    def log_file_operation(self, operation: str, file_path: str, **details):
        """Log file operations"""
        self.info(f"File {operation}: {file_path}", **details)
    
    def log_validation_result(self, validation_type: str, result: bool, **details):
        """Log validation results"""
        status = "PASSED" if result else "FAILED"
        self.info(f"Validation {status}: {validation_type}", **details)
    
    @contextmanager
    def log_context(self, operation: str, **context):
        """Context manager for operation logging"""
        start_time = time.time()
        self.info(f"Starting: {operation}", **context)
        
        try:
            yield
            duration = time.time() - start_time
            self.info(f"Completed: {operation}", 
                     duration_seconds=duration, 
                     **context)
        except Exception as e:
            duration = time.time() - start_time
            self.error(f"Failed: {operation}", 
                      exception=e, 
                      duration_seconds=duration, 
                      **context)
            raise

def log_execution(logger: PIIDetectionLogger = None):
    """Decorator for logging function execution"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger()
            
            func_name = f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            try:
                logger.debug(f"Executing: {func_name}")
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.debug(f"Success: {func_name}", duration_seconds=duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Error in {func_name}", 
                           exception=e, 
                           duration_seconds=duration,
                           args_count=len(args),
                           kwargs_keys=list(kwargs.keys()))
                raise
        return wrapper
    return decorator

# Global logger instance
_global_logger: Optional[PIIDetectionLogger] = None

def get_logger(name: str = "PII_Detection") -> PIIDetectionLogger:
    """Get or create logger instance"""
    global _global_logger
    if _global_logger is None or _global_logger.name != name:
        _global_logger = PIIDetectionLogger(name)
    return _global_logger

def setup_logging():
    """Setup logging system (call this at application startup)"""
    logger = get_logger()
    logger.info("Logging system initialized", 
               level=config.logging.level.value,
               log_file=config.logging.log_file,
               console_output=config.logging.enable_console_output)
