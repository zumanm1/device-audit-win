#!/usr/bin/env python3
"""
Unit Tests for Quick Stats Functionality
Tests the updated Quick Stats section with Violations KPI
"""

import unittest
import sys
import os
import json
import time
from unittest.mock import patch, MagicMock
import threading
import importlib.util

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the main application
try:
    spec = importlib.util.spec_from_file_location("main_app", "rr4-router-complete-enhanced-v3.py")
    main_app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_app)
    
    # Import required objects
    app = main_app.app
    audit_results_summary = main_app.audit_results_summary
    enhanced_progress = main_app.enhanced_progress
    active_inventory_data = main_app.active_inventory_data
    inject_globals = main_app.inject_globals
    
except Exception as e:
    print(f"Import error: {e}")
    print("Make sure the main application file is available")
    sys.exit(1)

class TestQuickStatsUnit(unittest.TestCase):
    """Unit tests for Quick Stats functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
    def test_inject_globals_contains_audit_results_summary(self):
        """Test that inject_globals includes audit_results_summary"""
        with self.app.app_context():
            globals_dict = inject_globals()
            
            # Verify audit_results_summary is included
            self.assertIn('audit_results_summary', globals_dict)
            self.assertIsInstance(globals_dict['audit_results_summary'], dict)
            
    def test_audit_results_summary_structure(self):
        """Test that audit_results_summary has the expected structure"""
        with self.app.app_context():
            globals_dict = inject_globals()
            summary = globals_dict['audit_results_summary']
            
            # Check if telnet_enabled_count exists (may be 0 initially)
            if summary:  # Only test if summary is populated
                expected_keys = [
                    'total_devices', 'successful_devices', 'failed_devices',
                    'telnet_enabled_count', 'risk_counts'
                ]
                for key in expected_keys:
                    if key in summary:
                        self.assertIsInstance(summary[key], (int, dict))
                        
    def test_enhanced_progress_structure(self):
        """Test that enhanced_progress has status_counts"""
        with self.app.app_context():
            globals_dict = inject_globals()
            progress = globals_dict['enhanced_progress']
            
            self.assertIn('status_counts', progress)
            status_counts = progress['status_counts']
            self.assertIn('success', status_counts)
            self.assertIsInstance(status_counts['success'], int)
            
    def test_active_inventory_data_structure(self):
        """Test that active_inventory_data has data array"""
        with self.app.app_context():
            globals_dict = inject_globals()
            inventory = globals_dict['active_inventory_data']
            
            # Should have 'data' key even if empty
            if inventory:  # Only test if inventory is not empty
                self.assertIn('data', inventory)
                self.assertIsInstance(inventory['data'], list)
            else:
                # If inventory is empty, that's also valid for initial state
                self.assertIsInstance(inventory, dict)
            
    def test_dashboard_route_accessibility(self):
        """Test that dashboard route is accessible"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
    def test_quick_stats_template_variables(self):
        """Test that Quick Stats template variables are available"""
        with self.app.app_context():
            globals_dict = inject_globals()
            
            # Test all three Quick Stats variables
            self.assertIn('active_inventory_data', globals_dict)
            self.assertIn('enhanced_progress', globals_dict)
            self.assertIn('audit_results_summary', globals_dict)
            
            # Test data structure for template rendering
            inventory = globals_dict['active_inventory_data']
            progress = globals_dict['enhanced_progress']
            summary = globals_dict['audit_results_summary']
            
            # These should be safe for template rendering
            self.assertIsInstance(inventory.get('data', []), list)
            self.assertIsInstance(progress.get('status_counts', {}), dict)
            self.assertIsInstance(summary, dict)

class TestQuickStatsIntegration(unittest.TestCase):
    """Integration tests for Quick Stats with mock audit data"""
    
    def setUp(self):
        """Set up test environment with mock data"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
    def test_quick_stats_with_mock_data(self):
        """Test Quick Stats with realistic mock data"""
        
        # Create mock data directly
        mock_inventory_data = {
            'data': [
                {'hostname': 'router1', 'ip_address': '192.168.1.1'},
                {'hostname': 'router2', 'ip_address': '192.168.1.2'},
                {'hostname': 'router3', 'ip_address': '192.168.1.3'},
                {'hostname': 'router4', 'ip_address': '192.168.1.4'},
                {'hostname': 'router5', 'ip_address': '192.168.1.5'},
                {'hostname': 'router6', 'ip_address': '192.168.1.6'}
            ]
        }
        
        mock_progress_data = {
            'status_counts': {
                'success': 4,
                'warning': 1,
                'failure': 1
            },
            'current_device': 'router6',
            'completed_devices': 6,
            'total_devices': 6,
            'percent_complete': 100
        }
        
        mock_summary_data = {
            'total_devices': 6,
            'successful_devices': 4,
            'failed_devices': 2,
            'telnet_enabled_count': 2,  # 2 violations found
            'risk_counts': {'high': 1, 'medium': 1, 'low': 0},
            'audit_duration': 45.2
        }
        
        # Temporarily replace global variables
        original_inventory = main_app.active_inventory_data
        original_progress = main_app.enhanced_progress
        original_summary = main_app.audit_results_summary
        
        try:
            main_app.active_inventory_data = mock_inventory_data
            main_app.enhanced_progress = mock_progress_data
            main_app.audit_results_summary = mock_summary_data
            
            # Test that dashboard loads with mock data
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)
            
            # Verify template context has expected values
            with self.app.app_context():
                globals_dict = inject_globals()
                
                # Total Devices: 6
                self.assertEqual(len(globals_dict['active_inventory_data']['data']), 6)
                
                # Successful: 4
                self.assertEqual(globals_dict['enhanced_progress']['status_counts']['success'], 4)
                
                # Violations: 2
                self.assertEqual(globals_dict['audit_results_summary']['telnet_enabled_count'], 2)
                
        finally:
            # Restore original values
            main_app.active_inventory_data = original_inventory
            main_app.enhanced_progress = original_progress
            main_app.audit_results_summary = original_summary

class TestQuickStatsEdgeCases(unittest.TestCase):
    """Test edge cases for Quick Stats"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
    def test_empty_audit_results_summary(self):
        """Test Quick Stats with empty audit results"""
        with self.app.app_context():
            globals_dict = inject_globals()
            summary = globals_dict['audit_results_summary']
            
            # Should handle empty summary gracefully
            violations = summary.get('telnet_enabled_count', 0)
            self.assertIsInstance(violations, int)
            self.assertGreaterEqual(violations, 0)
            
    def test_missing_telnet_enabled_count(self):
        """Test handling when telnet_enabled_count is missing"""
        with self.app.app_context():
            globals_dict = inject_globals()
            summary = globals_dict['audit_results_summary']
            
            # Template should handle missing key with 'or 0' fallback
            violations = summary.get('telnet_enabled_count') or 0
            self.assertIsInstance(violations, int)
            
    def test_zero_violations(self):
        """Test Quick Stats when no violations are found"""
        with self.app.app_context():
            globals_dict = inject_globals()
            
            # Should handle zero violations correctly
            summary = globals_dict['audit_results_summary']
            if 'telnet_enabled_count' in summary:
                violations = summary['telnet_enabled_count']
                self.assertIsInstance(violations, int)
                self.assertGreaterEqual(violations, 0)

def run_unit_tests():
    """Run all unit tests"""
    print("🧪 Running Quick Stats Unit Tests...")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestQuickStatsUnit,
        TestQuickStatsIntegration,
        TestQuickStatsEdgeCases
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"🧪 Unit Tests Summary:")
    print(f"   • Tests run: {result.testsRun}")
    print(f"   • Failures: {len(result.failures)}")
    print(f"   • Errors: {len(result.errors)}")
    print(f"   • Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   • {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\n🚨 Errors:")
        for test, traceback in result.errors:
            print(f"   • {test}: {traceback.split('Exception:')[-1].strip()}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_unit_tests()
    sys.exit(0 if success else 1) 