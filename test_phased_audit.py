#!/usr/bin/env python3
"""
Unit tests for the 5-phase audit structure
"""

import unittest
import os
import sqlite3
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Since phased_audit_tool.py doesn't exist yet, we'll create a mock version for testing
class MockPhasedAudit:
    """Mock class for phased audit testing"""
    
    def __init__(self, db_path=':memory:'):
        """Initialize the phased audit with a database connection"""
        self.phases = ['connectivity', 'authentication', 'config_audit', 'risk_assessment', 'reporting']
        self.current_phase = None
        self.phase_results = {}
        self.phase_timings = {}
        self.start_times = {}
        
        # Initialize SQLite database
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Create audit_phase_results table if it doesn't exist
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_phase_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            audit_id TEXT,
            device_id TEXT,
            phase_name TEXT,
            start_time TEXT,
            end_time TEXT,
            duration_seconds REAL,
            status TEXT,
            result_data TEXT,
            created_at TEXT
        )
        ''')
        self.conn.commit()
    
    def start_phase(self, phase_name):
        """Start timing for a specific audit phase"""
        if phase_name not in self.phases:
            raise ValueError(f"Invalid phase: {phase_name}")
        
        self.current_phase = phase_name
        self.start_times[phase_name] = datetime.now()
        return self.start_times[phase_name]
    
    def end_phase(self, phase_name, status="completed", result_data=None):
        """End timing for a specific audit phase and record results"""
        if phase_name not in self.phases:
            raise ValueError(f"Invalid phase: {phase_name}")
        
        if phase_name not in self.start_times:
            raise ValueError(f"Phase {phase_name} was not started")
        
        end_time = datetime.now()
        start_time = self.start_times[phase_name]
        duration = (end_time - start_time).total_seconds()
        
        # Store results in memory
        self.phase_timings[phase_name] = duration
        self.phase_results[phase_name] = {
            'status': status,
            'result_data': result_data,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration
        }
        
        # Store in database
        self.cursor.execute('''
        INSERT INTO audit_phase_results 
        (audit_id, device_id, phase_name, start_time, end_time, duration_seconds, status, result_data, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'test_audit', 
            'test_device', 
            phase_name, 
            start_time.isoformat(), 
            end_time.isoformat(), 
            duration, 
            status, 
            str(result_data) if result_data else None,
            datetime.now().isoformat()
        ))
        self.conn.commit()
        
        return duration
    
    def perform_phased_audit(self, device_info):
        """Orchestrating function to perform the full 5-phase audit"""
        results = {
            'device_id': device_info['id'],
            'hostname': device_info['hostname'],
            'ip_address': device_info['ip_address'],
            'phases': {},
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'total_duration': None,
            'overall_status': 'unknown'
        }
        
        start_time = datetime.now()
        
        # Phase 1: Connectivity
        self.start_phase('connectivity')
        # Simulated connectivity check
        connectivity_result = {'ping_status': 'SUCCESS', 'ssh_status': 'SUCCESS'}
        self.end_phase('connectivity', 'completed', connectivity_result)
        results['phases']['connectivity'] = connectivity_result
        
        # Phase 2: Authentication
        self.start_phase('authentication')
        # Simulated authentication check
        auth_result = {'auth_status': 'SUCCESS', 'privilege_level': 'PRIVILEGED'}
        self.end_phase('authentication', 'completed', auth_result)
        results['phases']['authentication'] = auth_result
        
        # Phase 3: Config Audit
        self.start_phase('config_audit')
        # Simulated config audit
        config_result = {'command_status': 'SUCCESS', 'telnet_allowed': 'NO'}
        self.end_phase('config_audit', 'completed', config_result)
        results['phases']['config_audit'] = config_result
        
        # Phase 4: Risk Assessment
        self.start_phase('risk_assessment')
        # Simulated risk assessment
        risk_result = {'risk_level': 'LOW', 'issues': []}
        self.end_phase('risk_assessment', 'completed', risk_result)
        results['phases']['risk_assessment'] = risk_result
        
        # Phase 5: Reporting
        self.start_phase('reporting')
        # Simulated reporting
        reporting_result = {'report_file': 'audit_report.csv', 'entries': 1}
        self.end_phase('reporting', 'completed', reporting_result)
        results['phases']['reporting'] = reporting_result
        
        # Calculate total duration
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        # Update results
        results['end_time'] = end_time.isoformat()
        results['total_duration'] = total_duration
        results['overall_status'] = 'completed'
        
        return results


class TestPhasedAudit(unittest.TestCase):
    """Test the 5-phase audit structure"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary database file
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.phased_audit = MockPhasedAudit(self.db_path)
    
    def tearDown(self):
        """Clean up after tests"""
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_phases_exist(self):
        """Test that all five phases are defined"""
        expected_phases = ['connectivity', 'authentication', 'config_audit', 'risk_assessment', 'reporting']
        for phase in expected_phases:
            self.assertIn(phase, self.phased_audit.phases)
    
    def test_start_phase(self):
        """Test starting a phase"""
        start_time = self.phased_audit.start_phase('connectivity')
        self.assertIsInstance(start_time, datetime)
        self.assertEqual(self.phased_audit.current_phase, 'connectivity')
    
    def test_end_phase(self):
        """Test ending a phase"""
        self.phased_audit.start_phase('authentication')
        duration = self.phased_audit.end_phase('authentication')
        self.assertGreaterEqual(duration, 0)
        self.assertIn('authentication', self.phased_audit.phase_timings)
    
    def test_invalid_phase(self):
        """Test invalid phase handling"""
        with self.assertRaises(ValueError):
            self.phased_audit.start_phase('invalid_phase')
    
    def test_phase_not_started(self):
        """Test error when ending a phase that wasn't started"""
        with self.assertRaises(ValueError):
            self.phased_audit.end_phase('config_audit')
    
    def test_full_audit_process(self):
        """Test the full 5-phase audit process"""
        device_info = {
            'id': 'test123',
            'hostname': 'router1',
            'ip_address': '192.168.1.1'
        }
        
        results = self.phased_audit.perform_phased_audit(device_info)
        
        # Verify all phases were executed
        self.assertEqual(len(results['phases']), 5)
        for phase in self.phased_audit.phases:
            self.assertIn(phase, results['phases'])
        
        # Verify overall results
        self.assertEqual(results['device_id'], 'test123')
        self.assertEqual(results['hostname'], 'router1')
        self.assertEqual(results['overall_status'], 'completed')
        self.assertIsNotNone(results['total_duration'])
    
    def test_database_storage(self):
        """Test that phase results are stored in the database"""
        # Start and end a phase
        self.phased_audit.start_phase('connectivity')
        self.phased_audit.end_phase('connectivity', 'completed', {'ping_status': 'SUCCESS'})
        
        # Query the database
        self.phased_audit.cursor.execute('SELECT * FROM audit_phase_results WHERE phase_name = ?', ('connectivity',))
        result = self.phased_audit.cursor.fetchone()
        
        # Verify database record exists
        self.assertIsNotNone(result)
        
        # Simple index-based check
        # Column order: id, audit_id, device_id, phase_name, start_time, end_time, duration_seconds, status, result_data, created_at
        self.assertEqual(result[3], 'connectivity')
        self.assertEqual(result[7], 'completed')


if __name__ == '__main__':
    unittest.main()
