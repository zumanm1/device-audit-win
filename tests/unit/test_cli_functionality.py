try:
    # Import CLI module
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    from rr4_complete_enchanced_v4_cli import (
        cli, DependencyChecker, Logger, ProjectStructure, 
        collect, ProgressMonitor
    )
    CLI_MODULE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: CLI module not available: {e}")
    CLI_MODULE_AVAILABLE = False 