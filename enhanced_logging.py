"""
Enhanced logging system with structured logging, error recovery, and monitoring
"""

import structlog
import logging
import json
import traceback
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from functools import wraps
import psutil
import os
from pathlib import Path

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

class ErrorRecovery:
    """Error recovery and retry mechanisms"""
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.logger = structlog.get_logger("error_recovery")
    
    def retry_on_failure(self, func: Callable, *args, **kwargs):
        """Retry a function on failure with exponential backoff"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait_time = self.backoff_factor * (2 ** attempt)
                    self.logger.warning(
                        "Function failed, retrying",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_retries=self.max_retries,
                        wait_time=wait_time,
                        error=str(e)
                    )
                    time.sleep(wait_time)
                else:
                    self.logger.error(
                        "Function failed after all retries",
                        function=func.__name__,
                        attempts=self.max_retries + 1,
                        error=str(e)
                    )
        
        raise last_exception

class HealthMonitor:
    """System health monitoring and metrics collection"""
    
    def __init__(self):
        self.logger = structlog.get_logger("health_monitor")
        self.metrics = {}
        self.start_time = time.time()
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            return {
                "timestamp": datetime.now().isoformat(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent,
                "process_count": len(psutil.pids()),
                "uptime": time.time() - self.start_time,
                "python_memory": self._get_python_memory_usage()
            }
        except Exception as e:
            self.logger.error("Failed to get system metrics", error=str(e))
            return {}
    
    def _get_python_memory_usage(self) -> Dict[str, Any]:
        """Get Python-specific memory usage"""
        try:
            import sys
            return {
                "objects_count": len(sys.modules),
                "memory_usage_mb": sys.getsizeof(sys.modules) / 1024 / 1024
            }
        except Exception:
            return {}
    
    def check_health(self) -> Dict[str, Any]:
        """Check overall system health"""
        metrics = self.get_system_metrics()
        
        health_status = "healthy"
        warnings = []
        errors = []
        
        # Check CPU usage
        if metrics.get("cpu_percent", 0) > 90:
            health_status = "critical"
            errors.append("High CPU usage")
        elif metrics.get("cpu_percent", 0) > 70:
            health_status = "warning"
            warnings.append("Elevated CPU usage")
        
        # Check memory usage
        if metrics.get("memory_percent", 0) > 90:
            health_status = "critical"
            errors.append("High memory usage")
        elif metrics.get("memory_percent", 0) > 70:
            health_status = "warning"
            warnings.append("Elevated memory usage")
        
        # Check disk usage
        if metrics.get("disk_percent", 0) > 95:
            health_status = "critical"
            errors.append("High disk usage")
        elif metrics.get("disk_percent", 0) > 85:
            health_status = "warning"
            warnings.append("Elevated disk usage")
        
        return {
            "status": health_status,
            "metrics": metrics,
            "warnings": warnings,
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }

class EnhancedLogger:
    """Enhanced logger with structured logging and context management"""
    
    def __init__(self, name: str = "ashley_ai"):
        self.logger = structlog.get_logger(name)
        self.context = {}
        self.error_recovery = ErrorRecovery()
        self.health_monitor = HealthMonitor()
    
    def set_context(self, **kwargs):
        """Set logging context"""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear logging context"""
        self.context.clear()
    
    def info(self, message: str, **kwargs):
        """Log info message with context"""
        self.logger.info(message, **self.context, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context"""
        self.logger.warning(message, **self.context, **kwargs)
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message with context and exception details"""
        error_data = {
            "message": message,
            **self.context,
            **kwargs
        }
        
        if exception:
            error_data.update({
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
                "traceback": traceback.format_exc()
            })
        
        self.logger.error("Error occurred", **error_data)
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log critical message with context"""
        error_data = {
            "message": message,
            **self.context,
            **kwargs
        }
        
        if exception:
            error_data.update({
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
                "traceback": traceback.format_exc()
            })
        
        self.logger.critical("Critical error occurred", **error_data)
    
    def performance(self, operation: str, duration: float, **kwargs):
        """Log performance metrics"""
        self.logger.info(
            "Performance metric",
            operation=operation,
            duration_ms=duration * 1000,
            **self.context,
            **kwargs
        )
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        return self.health_monitor.check_health()
    
    def retry_on_failure(self, max_retries: int = 3):
        """Decorator for retrying functions on failure"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return self.error_recovery.retry_on_failure(func, *args, **kwargs)
            return wrapper
        return decorator

class LoggingManager:
    """Centralized logging management"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.loggers = {}
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        # Create log files
        log_files = {
            "main": self.log_dir / "ashley_ai.log",
            "errors": self.log_dir / "errors.log",
            "performance": self.log_dir / "performance.log",
            "health": self.log_dir / "health.log"
        }
        
        # Configure file handlers
        for name, log_file in log_files.items():
            handler = logging.FileHandler(log_file)
            handler.setLevel(logging.DEBUG)
            
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            
            logger = logging.getLogger(name)
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG)
            
            self.loggers[name] = logger
    
    def get_logger(self, name: str = "main") -> EnhancedLogger:
        """Get an enhanced logger instance"""
        return EnhancedLogger(name)
    
    def log_health_check(self):
        """Log current health status"""
        logger = self.get_logger("health")
        health_status = logger.get_health_status()
        
        if health_status["status"] == "critical":
            logger.critical("System health is critical", **health_status)
        elif health_status["status"] == "warning":
            logger.warning("System health warning", **health_status)
        else:
            logger.info("System health check", **health_status)

# Global logging manager instance
logging_manager = LoggingManager()

def get_enhanced_logger(name: str = "main") -> EnhancedLogger:
    """Get an enhanced logger instance"""
    return logging_manager.get_logger(name)

def log_performance(operation: str):
    """Decorator for logging performance metrics"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_enhanced_logger()
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.performance(operation, duration, function=func.__name__)
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Performance logging error for {operation}",
                    exception=e,
                    duration_ms=duration * 1000,
                    function=func.__name__
                )
                raise
        return wrapper
    return decorator

def log_errors(speak_error: bool = True, default_return=None):
    """Enhanced error handling decorator"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_enhanced_logger()
            logger.set_context(function=func.__name__)
            
            try:
                result = func(*args, **kwargs)
                logger.info(f"Function {func.__name__} completed successfully")
                return result
            except Exception as e:
                logger.error(f"Function {func.__name__} failed", exception=e)
                
                if speak_error:
                    try:
                        from tts import speak
                        speak("I encountered an error. Let me try to continue.")
                    except Exception:
                        pass
                
                return default_return
        return wrapper
    return decorator

# Example usage and testing
if __name__ == "__main__":
    # Test the enhanced logging system
    logger = get_enhanced_logger("test")
    
    # Test basic logging
    logger.info("Testing enhanced logging system")
    logger.warning("This is a warning message")
    
    # Test error logging
    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.error("Test error occurred", exception=e)
    
    # Test performance logging
    @log_performance("test_operation")
    def test_function():
        time.sleep(0.1)
        return "success"
    
    result = test_function()
    print(f"Test function result: {result}")
    
    # Test health monitoring
    health = logger.get_health_status()
    print(f"Health status: {health['status']}")
    print(f"System metrics: {health['metrics']}")

