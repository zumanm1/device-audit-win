# Define test files based on the new organized structure
test_files = []

if args.core or args.all:
    test_files.extend([
        'tests/unit/test_core_modules.py',
        'tests/unit/test_cli_functionality.py'
    ])

if args.tasks or args.all:
    test_files.extend([
        'tests/unit/test_layer_collectors.py'
    ])

if args.integration or args.all:
    test_files.extend([
        'tests/integration/test_integration.py'
    ])

if args.performance or args.all:
    test_files.extend([
        'tests/performance/test_performance_stress.py'
    ]) 