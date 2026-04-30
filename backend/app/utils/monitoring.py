"""
Monitoring and Logging Module
Handles request/response logging, error tracking, and performance metrics
"""

import logging
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps
from app.core.supabase import get_supabase


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class RequestLogger:
    """Logs API requests and responses"""
    
    @staticmethod
    def log_request(
        user_id: str,
        endpoint: str,
        method: str,
        parameters: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Log API request
        
        Args:
            user_id: User ID
            endpoint: API endpoint
            method: HTTP method
            parameters: Request parameters
            timestamp: Request timestamp
        """
        timestamp = timestamp or datetime.utcnow()
        
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "user_id": user_id,
            "endpoint": endpoint,
            "method": method,
            "parameters": json.dumps(parameters, default=str),
            "event_type": "request"
        }
        
        logger.info(f"Request: {endpoint} by user {user_id}")
        
        # Store in database for audit trail
        try:
            supabase = get_supabase()
            supabase.table("activity_logs").insert(log_entry).execute()
        except Exception as e:
            logger.error(f"Failed to log request to database: {str(e)}")
    
    @staticmethod
    def log_response(
        user_id: str,
        endpoint: str,
        status_code: int,
        response_time_ms: float,
        response_size_bytes: int,
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Log API response
        
        Args:
            user_id: User ID
            endpoint: API endpoint
            status_code: HTTP status code
            response_time_ms: Response time in milliseconds
            response_size_bytes: Response size in bytes
            timestamp: Response timestamp
        """
        timestamp = timestamp or datetime.utcnow()
        
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "user_id": user_id,
            "endpoint": endpoint,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "response_size_bytes": response_size_bytes,
            "event_type": "response"
        }
        
        logger.info(
            f"Response: {endpoint} - Status: {status_code} - Time: {response_time_ms}ms"
        )
        
        # Store in database for audit trail
        try:
            supabase = get_supabase()
            supabase.table("activity_logs").insert(log_entry).execute()
        except Exception as e:
            logger.error(f"Failed to log response to database: {str(e)}")


class ErrorLogger:
    """Logs errors with full context"""
    
    @staticmethod
    def log_error(
        user_id: str,
        endpoint: str,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        context: Optional[Dict] = None,
        error_id: Optional[str] = None
    ) -> str:
        """
        Log error with full context
        
        Args:
            user_id: User ID
            endpoint: API endpoint
            error_type: Type of error
            error_message: Error message
            stack_trace: Stack trace (optional)
            context: Additional context (optional)
            error_id: Unique error ID (optional)
            
        Returns:
            Error ID for support reference
        """
        import uuid
        error_id = error_id or str(uuid.uuid4())
        
        log_entry = {
            "error_id": error_id,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "endpoint": endpoint,
            "error_type": error_type,
            "error_message": error_message,
            "stack_trace": stack_trace,
            "context": json.dumps(context or {}, default=str)
        }
        
        logger.error(
            f"Error ID: {error_id} - Type: {error_type} - Message: {error_message}"
        )
        
        if stack_trace:
            logger.error(f"Stack trace:\n{stack_trace}")
        
        # Store in database for error tracking
        try:
            supabase = get_supabase()
            supabase.table("error_logs").insert(log_entry).execute()
        except Exception as e:
            logger.error(f"Failed to log error to database: {str(e)}")
        
        return error_id


class PerformanceMetrics:
    """Collects and tracks performance metrics"""
    
    @staticmethod
    def log_generation_metrics(
        user_id: str,
        content_type: str,
        generation_time_ms: float,
        quality_score: float,
        success: bool,
        batch_id: Optional[str] = None
    ) -> None:
        """
        Log generation performance metrics
        
        Args:
            user_id: User ID
            content_type: Type of content generated
            generation_time_ms: Time taken in milliseconds
            quality_score: Quality score (0-100)
            success: Whether generation was successful
            batch_id: Batch ID if part of batch generation
        """
        metric_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "content_type": content_type,
            "generation_time_ms": generation_time_ms,
            "quality_score": quality_score,
            "success": success,
            "batch_id": batch_id,
            "metric_type": "generation"
        }
        
        logger.info(
            f"Generation metrics - Type: {content_type}, Time: {generation_time_ms}ms, "
            f"Score: {quality_score}, Success: {success}"
        )
        
        # Store in database for analytics
        try:
            supabase = get_supabase()
            supabase.table("performance_metrics").insert(metric_entry).execute()
        except Exception as e:
            logger.error(f"Failed to log performance metrics: {str(e)}")
    
    @staticmethod
    def log_cache_metrics(
        cache_type: str,
        hit: bool,
        retrieval_time_ms: float
    ) -> None:
        """
        Log cache performance metrics
        
        Args:
            cache_type: Type of cache (trending, preferences, stats)
            hit: Whether cache hit occurred
            retrieval_time_ms: Time to retrieve from cache
        """
        metric_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "cache_type": cache_type,
            "hit": hit,
            "retrieval_time_ms": retrieval_time_ms,
            "metric_type": "cache"
        }
        
        logger.info(
            f"Cache metrics - Type: {cache_type}, Hit: {hit}, Time: {retrieval_time_ms}ms"
        )
        
        # Store in database for analytics
        try:
            supabase = get_supabase()
            supabase.table("performance_metrics").insert(metric_entry).execute()
        except Exception as e:
            logger.error(f"Failed to log cache metrics: {str(e)}")


class ActivityAuditTrail:
    """Tracks user activity for audit purposes"""
    
    @staticmethod
    def log_activity(
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> None:
        """
        Log user activity for audit trail
        
        Args:
            user_id: User ID
            action: Action performed (created, updated, deleted, viewed, etc.)
            resource_type: Type of resource (content, batch, preference, etc.)
            resource_id: ID of resource (optional)
            details: Additional details (optional)
        """
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": json.dumps(details or {}, default=str)
        }
        
        logger.info(
            f"Audit: User {user_id} - Action: {action} - Resource: {resource_type} - ID: {resource_id}"
        )
        
        # Store in database for audit trail
        try:
            supabase = get_supabase()
            supabase.table("audit_trail").insert(audit_entry).execute()
        except Exception as e:
            logger.error(f"Failed to log audit trail: {str(e)}")


class MonitoringDecorators:
    """Decorators for automatic monitoring"""
    
    @staticmethod
    def monitor_performance(func):
        """Decorator to monitor function performance"""
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                elapsed_ms = (time.time() - start_time) * 1000
                logger.info(f"{func.__name__} completed in {elapsed_ms:.2f}ms")
                return result
            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000
                logger.error(f"{func.__name__} failed after {elapsed_ms:.2f}ms: {str(e)}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.time() - start_time) * 1000
                logger.info(f"{func.__name__} completed in {elapsed_ms:.2f}ms")
                return result
            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000
                logger.error(f"{func.__name__} failed after {elapsed_ms:.2f}ms: {str(e)}")
                raise
        
        # Return appropriate wrapper based on function type
        if hasattr(func, '__await__'):
            return async_wrapper
        else:
            return sync_wrapper
    
    @staticmethod
    def monitor_errors(func):
        """Decorator to monitor and log errors"""
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                raise
        
        # Return appropriate wrapper based on function type
        if hasattr(func, '__await__'):
            return async_wrapper
        else:
            return sync_wrapper


# Create singleton instances
request_logger = RequestLogger()
error_logger = ErrorLogger()
performance_metrics = PerformanceMetrics()
activity_audit_trail = ActivityAuditTrail()
monitoring_decorators = MonitoringDecorators()
