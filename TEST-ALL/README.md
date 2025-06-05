# NetAuditPro Router Auditing Application - Test Suite

This directory contains comprehensive unit tests for the NetAuditPro Router Auditing Application, providing test coverage for core functionality including inventory management, enhanced features, utility functions, and web routes.

## Test Suite Overview

### Test Files

1. **`test_basic.py`** - Basic utility functions and core operations
2. **`test_inventory_management.py`** - CSV parsing, validation, and inventory management
3. **`test_enhanced_features.py`** - Enhanced features like command logging and device tracking
4. **`test_web_routes.py`** - Flask web application routes and endpoints
5. **`conftest.py`** - Test configuration and shared fixtures

### Test Coverage

- **Total Tests:** 34+
- **Core Functions:** 20+ functions tested
- **Estimated Coverage:** 65-75% of application code
- **Success Rate:** ~80% (with minor test adjustments needed)

## Prerequisites

### Install Test Dependencies

```bash
pip install pytest pytest-cov pytest-mock coverage
```

Or install from requirements file:

```bash
pip install -r requirements-test.txt
```

## Running Tests

### Basic Test Execution

Run all tests:
```bash
python3 -m pytest
```

Run with verbose output:
```bash
python3 -m pytest -v
```

Run specific test file:
```bash
python3 -m pytest test_basic.py -v
```

### Coverage Testing

Run tests with coverage reporting:
```bash
python3 -m pytest --cov=../rr4-router-complete-enhanced-v2 --cov-report=term-missing
```

Generate HTML coverage report:
```bash
python3 -m pytest --cov=../rr4-router-complete-enhanced-v2 --cov-report=html:coverage_html
```

### Using the Test Runner

Use the comprehensive test runner:
```bash
python3 run_tests.py --coverage --verbose --html
```

Available options:
- `--coverage` - Enable coverage reporting
- `--verbose` - Verbose test output
- `--html` - Generate HTML coverage report
- `--xml` - Generate XML coverage report
- `--target-coverage N` - Set target coverage percentage (default: 80)

## Test Categories

### 1. Basic Utility Functions (`test_basic.py`)

Tests core utility functions:
- ANSI escape sequence removal
- IP address validation
- Hostname validation
- Local ping operations
- Function existence checks

### 2. Inventory Management (`test_inventory_management.py`)

Tests inventory handling:
- CSV data validation
- Router dictionary to CSV conversion
- CSV parsing and generation
- Individual row validation
- Header extraction
- Data format conversion

### 3. Enhanced Features (`test_enhanced_features.py`)

Tests enhanced functionality:
- Command logging system
- Device status tracking
- Connection status updates
- Progress tracking
- Audit progress management
- Placeholder configuration generation

### 4. Web Routes (`test_web_routes.py`)

Tests Flask web application:
- Basic route responses
- Settings management
- Inventory management routes
- Audit control endpoints
- Command log routes
- Error handling

## Test Results Summary

### Passing Tests (27/34)
- ✅ All inventory management functions
- ✅ Most basic utility functions
- ✅ Command logging functionality
- ✅ Device status tracking
- ✅ Core enhanced features

### Known Test Issues (7/34)
- IP validation edge case behavior
- Progress tracking data structure differences
- Utility function output format variations
- Test expectation mismatches

## Mocking and Fixtures

The test suite uses comprehensive mocking for:
- SSH connections (`paramiko`)
- Network operations (`subprocess.run`)
- File operations (`builtins.open`)
- Flask application context
- Global state management

## Continuous Integration

The test suite is designed to work with CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    cd TEST-ALL
    python3 -m pytest --cov=../rr4-router-complete-enhanced-v2 --cov-report=xml
```

## Contributing

When adding new features to the main application:

1. Add corresponding tests in the appropriate test file
2. Ensure tests cover both success and failure cases
3. Update test documentation
4. Run the full test suite before submitting changes

### Test Naming Convention

- Test files: `test_<module_name>.py`
- Test classes: `Test<FeatureName>`
- Test methods: `test_<specific_functionality>`

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the main application file path is correct in test files
2. **Coverage Issues**: The hyphenated filename may cause coverage collection problems
3. **Mock Failures**: Verify mock patches match actual function signatures

### Debug Mode

Run tests with Python debugging:
```bash
python3 -m pytest --pdb
```

Run specific test with debugging:
```bash
python3 -m pytest test_basic.py::test_ip_validation --pdb
```

## Reports

Test execution generates several reports:
- Console output with pass/fail status
- Coverage reports (terminal, HTML, XML)
- Test summary in `test_summary_report.md`

## Future Enhancements

Planned test improvements:
- Integration tests for complete audit workflow
- Performance and stress testing
- Enhanced error condition testing
- Network operation testing with better mocks
- Report generation testing 