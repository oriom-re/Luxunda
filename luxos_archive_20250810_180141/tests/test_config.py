
"""
LuxDB Test Configuration
========================

Configuration settings and environment setup for tests.
"""

import os
from typing import Dict, Any

class TestConfig:
    """Test configuration class"""
    
    # Database configuration
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'luxdb_test'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'password')
    }
    
    # Test timeouts (seconds)
    TIMEOUTS = {
        'connection': 10,
        'query': 30,
        'bulk_operation': 60,
        'performance_test': 180
    }
    
    # Performance thresholds
    PERFORMANCE_THRESHOLDS = {
        'bulk_create_time': 30,  # seconds for 100 items
        'memory_increase_mb': 100,  # max memory increase
        'query_time': 10,  # seconds for 30 queries
        'concurrent_operations_time': 15  # seconds for 20 operations
    }
    
    # Success criteria
    SUCCESS_CRITERIA = {
        'min_success_rate': 90,  # minimum % of tests that must pass
        'max_errors': 5,  # maximum number of errors allowed
        'min_concurrent_success_rate': 80  # % for concurrent operations
    }
    
    # Test data sizes
    TEST_DATA_SIZES = {
        'small': 10,
        'medium': 50,
        'large': 100,
        'stress': 500
    }

def get_test_config() -> Dict[str, Any]:
    """Get complete test configuration"""
    return {
        'database': TestConfig.DB_CONFIG,
        'timeouts': TestConfig.TIMEOUTS,
        'performance': TestConfig.PERFORMANCE_THRESHOLDS,
        'success_criteria': TestConfig.SUCCESS_CRITERIA,
        'data_sizes': TestConfig.TEST_DATA_SIZES
    }

def validate_test_environment() -> Dict[str, Any]:
    """Validate test environment setup"""
    validation = {
        'valid': True,
        'issues': [],
        'warnings': []
    }
    
    # Check required environment variables
    required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    for var in required_vars:
        if not os.getenv(var):
            validation['warnings'].append(f"Environment variable {var} not set, using default")
    
    # Check database connection parameters
    if TestConfig.DB_CONFIG['host'] == 'localhost' and TestConfig.DB_CONFIG['database'] == 'luxdb_test':
        validation['warnings'].append("Using default test database configuration")
    
    # Check for OpenAI API key (optional for some tests)
    if not os.getenv('OPENAI_API_KEY'):
        validation['warnings'].append("OPENAI_API_KEY not set - some AI tests may be skipped")
    
    return validation
