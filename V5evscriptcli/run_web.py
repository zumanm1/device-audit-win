#!/usr/bin/env python3
"""
V5evscriptcli Web Dashboard Runner
This script starts the web dashboard application.
"""

import os
import sys
import argparse
import logging

def setup_logging():
    """Setup basic logging for the web application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def parse_args():
    parser = argparse.ArgumentParser(description='V5evscriptcli Web Dashboard')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to listen on')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--test', action='store_true', help='Run in test mode (no EVE-NG connection required)')
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Ensure we're in the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Create necessary directories
    os.makedirs('topologies', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    logger.info("Created necessary directories")
    
    # Import the web application
    try:
        from web_app import app, socketio
        logger.info("Web application imported successfully")
    except ImportError as e:
        logger.error(f"Failed to import web application: {e}")
        sys.exit(1)
    
    # Configure test mode if requested
    if args.test:
        app.config['TESTING'] = True
        logger.info("Running in test mode")
    
    logger.info(f"Starting V5evscriptcli Web Dashboard on {args.host}:{args.port}")
    logger.info("Default credentials: admin/admin")
    logger.info("Press Ctrl+C to stop the server")
    
    try:
        socketio.run(app, 
                    host=args.host, 
                    port=args.port, 
                    debug=args.debug,
                    allow_unsafe_werkzeug=True,
                    use_reloader=False)  # Disable reloader to prevent issues
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        print("\nShutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start web server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 