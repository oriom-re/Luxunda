
# LuxDB Test Suite

Comprehensive testing framework for the LuxDB library ensuring 100% reliability.

## Overview

The LuxDB test suite consists of multiple test categories designed to verify every aspect of the library:

- **Core Functionality Tests**: Database operations, Soul/Being management, relationships
- **Integration Tests**: Complete workflows, AI integration, multi-user scenarios
- **Performance Tests**: Load testing, memory usage, concurrent operations
- **Data Integrity Tests**: Consistency, transactions, foreign key constraints

## Quick Start

### Run All Tests
```bash
python run_tests.py
```

### Run Specific Test Categories
```bash
# Core functionality only
python run_tests.py --core-only

# Integration tests only
python run_tests.py --integration-only

# Save detailed report
python run_tests.py --save-report
```

### Run Individual Test Modules
```bash
# Core functionality tests
python tests/test_core_functionality.py

# Integration tests
python tests/test_integration.py
```

## Test Categories

### 1. Core Functionality Tests (`test_core_functionality.py`)

Tests all basic LuxDB operations:

- **Soul Operations**
  - Genotype validation
  - Soul creation and loading
  - Schema evolution

- **Being Operations**
  - Being creation with various data types
  - Attribute updates and queries
  - Bulk operations
  - Being deletion

- **Relationship Operations**
  - Relationship creation and management
  - Complex relationship queries
  - Relationship updates and deletion

- **Performance & Stress Tests**
  - Bulk creation performance (100+ items)
  - Concurrent operations (20+ simultaneous)
  - Memory usage monitoring
  - Query performance

- **Data Integrity Tests**
  - Foreign key constraints
  - Transaction rollback
  - Concurrent update handling
  - Data consistency validation

### 2. Integration Tests (`test_integration.py`)

Tests complete workflows and system integration:

- **AI Workflow Testing**
  - Message processing with AI
  - Similarity detection
  - Automatic relationship creation
  - Knowledge graph building

- **Multi-User Scenarios**
  - Concurrent user operations
  - Data isolation verification
  - Conflict resolution
  - Performance under load

- **Data Migration Workflows**
  - Schema evolution
  - Data migration procedures
  - Backward compatibility
  - Version management

## Environment Setup

### Database Configuration

Set environment variables for test database:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=luxdb_test
export DB_USER=postgres
export DB_PASSWORD=password
```

### Optional Configuration

```bash
# For AI integration tests
export OPENAI_API_KEY=your_openai_key_here

# For custom test configuration
export LUXDB_TEST_CONFIG=production
```

### Test Database Setup

1. Create test database:
```sql
CREATE DATABASE luxdb_test;
```

2. Ensure test user has required permissions:
```sql
GRANT ALL PRIVILEGES ON DATABASE luxdb_test TO postgres;
```

## Test Results and Certification

### Success Criteria

For library certification, tests must meet:

- **95%+ test success rate**
- **Less than 5 total errors**
- **Core functionality 100% working**
- **Performance within thresholds**
- **Data integrity verified**

### Certification Levels

1. **100% RELIABLE** ✅
   - All tests pass
   - No critical errors
   - Performance acceptable
   - Ready for production

2. **PARTIAL SUCCESS** ⚠️
   - Core tests pass
   - Some integration issues
   - Requires fixes for production

3. **FAILED** ❌
   - Critical functionality broken
   - Multiple system failures
   - Not ready for production

### Test Reports

Test results are saved as JSON files with detailed information:

- Test execution times
- Error details and stack traces
- Performance metrics
- Environment information
- Specific recommendations for fixes

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```
   Solution: Check PostgreSQL is running and connection parameters
   ```

2. **Missing Tables**
   ```
   Solution: Run database initialization: await db.initialize()
   ```

3. **Performance Issues**
   ```
   Solution: Check system resources and database configuration
   ```

4. **Permission Errors**
   ```
   Solution: Verify database user has DDL/DML permissions
   ```

### Debug Mode

Run tests with additional debugging:

```bash
# Enable verbose logging
export LUXDB_LOG_LEVEL=DEBUG
python run_tests.py

# Run with Python debugger
python -m pdb run_tests.py
```

## Contributing to Tests

### Adding New Tests

1. Create test functions in appropriate module
2. Follow naming convention: `test_feature_name`
3. Include error handling and cleanup
4. Add to test runner if needed

### Test Structure Template

```python
async def test_new_feature(self) -> Dict[str, Any]:
    """Test new feature functionality"""
    results = {
        'feature_test': False,
        'errors': []
    }
    
    try:
        # Test implementation
        # ...
        
        if success_condition:
            results['feature_test'] = True
            print("✅ New feature test passed")
        else:
            results['errors'].append("Feature test failed")
            print("❌ New feature test failed")
            
    except Exception as e:
        results['errors'].append(f"Error: {str(e)}")
        print(f"❌ Error: {str(e)}")
    
    return results
```

### Performance Test Guidelines

- Set realistic performance thresholds
- Test with various data sizes
- Monitor system resources
- Include cleanup procedures
- Document expected performance ranges

## Continuous Integration

For CI/CD integration:

```yaml
# Example GitHub Actions
name: LuxDB Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v2
      - name: Run LuxDB Tests
        run: python run_tests.py
```

## License

Same as LuxDB library license.
