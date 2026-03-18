#!/usr/bin/env python3
"""
Production Monitoring and Resource Management System
"""

import time
import threading
import psutil
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import queue
from contextlib import contextmanager

from config_simple import config
from logger import get_logger

logger = get_logger("Monitoring")

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    timestamp: float
    operation: str
    duration: float
    memory_usage_mb: float
    cpu_percent: float
    rows_processed: int
    entities_found: int
    success: bool
    error_message: Optional[str] = None

@dataclass
class ResourceMetrics:
    """Resource usage metrics"""
    timestamp: float
    memory_percent: float
    memory_available_gb: float
    cpu_percent: float
    disk_usage_percent: float
    active_threads: int

class MetricsCollector:
    """Production metrics collector"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.performance_history: deque = deque(maxlen=max_history)
        self.resource_history: deque = deque(maxlen=max_history)
        self.operation_counts: Dict[str, int] = defaultdict(int)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.start_time = time.time()
        self._lock = threading.Lock()
    
    def record_performance(self, metrics: PerformanceMetrics):
        """Record performance metrics"""
        with self._lock:
            self.performance_history.append(metrics)
            self.operation_counts[metrics.operation] += 1
            if not metrics.success:
                self.error_counts[metrics.operation] += 1
    
    def record_resource_usage(self):
        """Record current resource usage"""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent()
            disk = psutil.disk_usage('.')
            
            metrics = ResourceMetrics(
                timestamp=time.time(),
                memory_percent=memory.percent,
                memory_available_gb=memory.available / (1024**3),
                cpu_percent=cpu_percent,
                disk_usage_percent=disk.percent,
                active_threads=threading.active_count()
            )
            
            with self._lock:
                self.resource_history.append(metrics)
                
        except Exception as e:
            logger.error("Failed to record resource metrics", exception=e)
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for specified time period"""
        cutoff_time = time.time() - (hours * 3600)
        
        with self._lock:
            recent_metrics = [m for m in self.performance_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {"message": "No recent performance data"}
        
        # Calculate statistics
        operations = defaultdict(list)
        for metric in recent_metrics:
            operations[metric.operation].append(metric)
        
        summary = {
            "period_hours": hours,
            "total_operations": len(recent_metrics),
            "operations_by_type": {},
            "average_durations": {},
            "success_rates": {},
            "throughput": {}
        }
        
        for op_name, op_metrics in operations.items():
            successful = [m for m in op_metrics if m.success]
            durations = [m.duration for m in successful]
            total_rows = sum(m.rows_processed for m in successful)
            total_entities = sum(m.entities_found for m in successful)
            
            summary["operations_by_type"][op_name] = len(op_metrics)
            summary["success_rates"][op_name] = len(successful) / len(op_metrics) * 100 if op_metrics else 0
            
            if durations:
                summary["average_durations"][op_name] = {
                    "mean": sum(durations) / len(durations),
                    "min": min(durations),
                    "max": max(durations)
                }
                summary["throughput"][op_name] = {
                    "rows_per_second": total_rows / sum(durations) if sum(durations) > 0 else 0,
                    "entities_per_second": total_entities / sum(durations) if sum(durations) > 0 else 0
                }
        
        return summary
    
    def get_resource_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get resource usage summary"""
        cutoff_time = time.time() - (hours * 3600)
        
        with self._lock:
            recent_metrics = [m for m in self.resource_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {"message": "No recent resource data"}
        
        memory_values = [m.memory_percent for m in recent_metrics]
        cpu_values = [m.cpu_percent for m in recent_metrics]
        
        return {
            "period_hours": hours,
            "samples": len(recent_metrics),
            "memory": {
                "average_percent": sum(memory_values) / len(memory_values),
                "max_percent": max(memory_values),
                "min_percent": min(memory_values)
            },
            "cpu": {
                "average_percent": sum(cpu_values) / len(cpu_values),
                "max_percent": max(cpu_values),
                "min_percent": min(cpu_values)
            },
            "current": asdict(recent_metrics[-1]) if recent_metrics else None
        }
    
    def export_metrics(self, file_path: str, hours: int = 24):
        """Export metrics to file"""
        cutoff_time = time.time() - (hours * 3600)
        
        with self._lock:
            performance_data = [asdict(m) for m in self.performance_history if m.timestamp >= cutoff_time]
            resource_data = [asdict(m) for m in self.resource_history if m.timestamp >= cutoff_time]
        
        export_data = {
            "export_timestamp": time.time(),
            "period_hours": hours,
            "performance_metrics": performance_data,
            "resource_metrics": resource_data,
            "operation_counts": dict(self.operation_counts),
            "error_counts": dict(self.error_counts),
            "system_start_time": self.start_time
        }
        
        try:
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            logger.info(f"Metrics exported to {file_path}")
        except Exception as e:
            logger.error("Failed to export metrics", exception=e, file_path=file_path)

class ResourceManager:
    """Production resource manager"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.start_memory = self.process.memory_info().rss / (1024 * 1024)  # MB
        self.peak_memory = self.start_memory
        self.operation_start_time: Optional[float] = None
        self.operation_start_memory: Optional[float] = None
    
    def start_operation(self, operation_name: str):
        """Start monitoring an operation"""
        self.operation_start_time = time.time()
        self.operation_start_memory = self.process.memory_info().rss / (1024 * 1024)
        logger.debug(f"Started monitoring: {operation_name}", 
                    memory_mb=self.operation_start_memory)
    
    def end_operation(self, operation_name: str, rows_processed: int = 0, 
                     entities_found: int = 0, success: bool = True, 
                     error_message: Optional[str] = None) -> PerformanceMetrics:
        """End monitoring and return metrics"""
        if self.operation_start_time is None:
            logger.warning("end_operation called without start_operation")
            return PerformanceMetrics(0, operation_name, 0, 0, 0, 0, 0, False)
        
        end_time = time.time()
        duration = end_time - self.operation_start_time
        end_memory = self.process.memory_info().rss / (1024 * 1024)
        memory_usage = end_memory - (self.operation_start_memory or 0)
        
        # Update peak memory
        if end_memory > self.peak_memory:
            self.peak_memory = end_memory
        
        # Get current CPU usage
        cpu_percent = psutil.cpu_percent()
        
        metrics = PerformanceMetrics(
            timestamp=end_time,
            operation=operation_name,
            duration=duration,
            memory_usage_mb=memory_usage,
            cpu_percent=cpu_percent,
            rows_processed=rows_processed,
            entities_found=entities_found,
            success=success,
            error_message=error_message
        )
        
        logger.log_performance(operation_name, duration,
                             memory_delta_mb=memory_usage,
                             rows_processed=rows_processed,
                             entities_found=entities_found)
        
        # Reset operation tracking
        self.operation_start_time = None
        self.operation_start_memory = None
        
        return metrics
    
    def check_resource_limits(self) -> Dict[str, Any]:
        """Check if resource limits are exceeded"""
        memory = psutil.virtual_memory()
        current_memory = self.process.memory_info().rss / (1024 * 1024)  # MB
        
        warnings = []
        errors = []
        
        # Memory checks
        if current_memory > config.processing.memory_limit_mb:
            errors.append(f"Memory limit exceeded: {current_memory:.1f}MB > {config.processing.memory_limit_mb}MB")
        elif current_memory > config.processing.memory_limit_mb * 0.8:
            warnings.append(f"High memory usage: {current_memory:.1f}MB")
        
        # System memory check
        if memory.available < 1024 * 1024 * 1024:  # Less than 1GB
            warnings.append("Low system memory available")
        
        # Processing time check
        if self.operation_start_time:
            elapsed = time.time() - self.operation_start_time
            if elapsed > config.processing.max_processing_time_seconds:
                errors.append(f"Processing time limit exceeded: {elapsed:.1f}s > {config.processing.max_processing_time_seconds}s")
            elif elapsed > config.processing.max_processing_time_seconds * 0.8:
                warnings.append(f"Long processing time: {elapsed:.1f}s")
        
        return {
            "current_memory_mb": current_memory,
            "peak_memory_mb": self.peak_memory,
            "memory_limit_mb": config.processing.memory_limit_mb,
            "system_memory_available_gb": memory.available / (1024**3),
            "warnings": warnings,
            "errors": errors,
            "resource_status": "critical" if errors else "warning" if warnings else "healthy"
        }
    
    def get_process_info(self) -> Dict[str, Any]:
        """Get detailed process information"""
        try:
            memory_info = self.process.memory_info()
            cpu_times = self.process.cpu_times()
            
            return {
                "pid": self.process.pid,
                "memory_rss_mb": memory_info.rss / (1024 * 1024),
                "memory_vms_mb": memory_info.vms / (1024 * 1024),
                "cpu_percent": self.process.cpu_percent(),
                "cpu_time_user": cpu_times.user,
                "cpu_time_system": cpu_times.system,
                "num_threads": self.process.num_threads(),
                "create_time": self.process.create_time(),
                "status": self.process.status(),
                "peak_memory_mb": self.peak_memory,
                "memory_delta_mb": (memory_info.rss / (1024 * 1024)) - self.start_memory
            }
        except Exception as e:
            logger.error("Failed to get process info", exception=e)
            return {"error": str(e)}

class RateLimiter:
    """Simple rate limiter for operations"""
    
    def __init__(self, max_operations_per_minute: int = 10):
        self.max_operations = max_operations_per_minute
        self.operation_times: deque = deque(maxlen=max_operations_per_minute * 2)
    
    def can_proceed(self) -> bool:
        """Check if operation can proceed"""
        now = time.time()
        cutoff = now - 60  # 1 minute ago
        
        # Remove old entries
        while self.operation_times and self.operation_times[0] < cutoff:
            self.operation_times.popleft()
        
        return len(self.operation_times) < self.max_operations
    
    def record_operation(self):
        """Record an operation"""
        self.operation_times.append(time.time())
    
    def wait_time(self) -> float:
        """Get time to wait before next operation"""
        if self.can_proceed():
            return 0
        
        oldest = self.operation_times[0]
        wait_time = 60 - (time.time() - oldest)
        return max(0, wait_time)

# Global instances
metrics_collector = MetricsCollector()
resource_manager = ResourceManager()
rate_limiter = RateLimiter()

def start_monitoring():
    """Start background monitoring"""
    def monitor_resources():
        while True:
            try:
                metrics_collector.record_resource_usage()
                time.sleep(30)  # Record every 30 seconds
            except Exception as e:
                logger.error("Background monitoring error", exception=e)
                time.sleep(60)
    
    monitor_thread = threading.Thread(target=monitor_resources, daemon=True)
    monitor_thread.start()
    logger.info("Background monitoring started")

@contextmanager
def monitor_operation(operation_name: str):
    """Context manager for operation monitoring"""
    resource_manager.start_operation(operation_name)
    success = False
    error_message = None
    
    try:
        yield
        success = True
    except Exception as e:
        error_message = str(e)
        raise
    finally:
        metrics = resource_manager.end_operation(
            operation_name, 
            success=success, 
            error_message=error_message
        )
        metrics_collector.record_performance(metrics)
