#!/usr/bin/env python3
"""
SSH Command Handler for Router Audit Tool
Provides improved command execution with timeouts and error handling
"""

import time
import logging
from colorama import Fore, Style

class SSHCommandHandler:
    """
    Enhanced SSH command execution with proper timeout handling and detailed status reporting
    """
    def __init__(self, connection, timeout=5):
        """
        Initialize the command handler with a connection and default timeout
        
        Args:
            connection: An established SSH connection (Netmiko connection or similar)
            timeout: Default timeout in seconds for commands (default: 5)
        """
        self.connection = connection
        self.default_timeout = timeout
        self.last_error = None
        self.command_history = {}
        
    def execute_command(self, command, timeout=None, wait_for_prompt=True, expect_strings=None):
        """
        Execute a command with proper timeout handling and return detailed results
        
        Args:
            command: The command to execute
            timeout: Timeout in seconds (overrides default if provided)
            wait_for_prompt: Whether to wait for a prompt character (>, #) to consider command complete
            expect_strings: List of strings to look for in output to consider command complete
            
        Returns:
            dict: Command execution results including:
                - success: Boolean indicating if command executed successfully
                - output: The command output (if any)
                - duration: How long the command took to execute
                - timed_out: Boolean indicating if command timed out
                - error: Error message (if any)
        """
        if timeout is None:
            timeout = self.default_timeout
            
        if expect_strings is None and wait_for_prompt:
            expect_strings = ['>', '#']
            
        # Prepare result structure
        result = {
            'success': False,
            'output': '',
            'duration': 0,
            'timed_out': False,
            'error': None
        }
        
        # Send the command
        print(f"{Fore.YELLOW}📤 Sending command: {command}{Style.RESET_ALL}")
        self.connection.write_channel(command + '\n')
        
        # Track command execution time and output
        start_time = time.time()
        command_output = ""
        command_complete = False
        
        # Show progress indicator
        print(f"{Fore.YELLOW}⏳ Waiting for response", end="", flush=True)
        
        # Loop until timeout or command completion
        while time.time() - start_time < timeout:
            time.sleep(0.5)  # Check every half second
            print(".", end="", flush=True)
            new_output = self.connection.read_channel()
            command_output += new_output
            
            # Check for command completion indicators
            if expect_strings:
                for indicator in expect_strings:
                    if indicator in command_output:
                        command_complete = True
                        break
                        
            # Check if command is in output (echo) and also a prompt is present
            if command in command_output and wait_for_prompt:
                for prompt in ['>', '#']:
                    if prompt in command_output:
                        command_complete = True
                        break
                        
            if command_complete:
                break
                
        # Calculate execution duration
        duration = time.time() - start_time
        result['duration'] = duration
        
        # Determine result status
        if command_complete and len(command_output.strip()) > 10:
            print(f" {Fore.GREEN}Received! ({len(command_output)} chars in {duration:.1f}s){Style.RESET_ALL}")
            result['success'] = True
            result['output'] = command_output
        else:
            if duration >= timeout:
                print(f" {Fore.RED}Timed out after {timeout}s!{Style.RESET_ALL}")
                result['timed_out'] = True
                result['error'] = f"Command timed out after {timeout} seconds"
            else:
                print(f" {Fore.RED}Failed! (Insufficient or unexpected output){Style.RESET_ALL}")
                result['error'] = "Command failed to return sufficient data"
        
        # Store command result in history
        self.command_history[command] = result
        
        return result
        
    def execute_multiple_commands(self, commands, stop_on_error=False):
        """
        Execute multiple commands in sequence
        
        Args:
            commands: List of commands to execute
            stop_on_error: Whether to stop execution if a command fails
            
        Returns:
            dict: Results for all commands
        """
        results = {}
        success_count = 0
        failure_count = 0
        
        for cmd in commands:
            result = self.execute_command(cmd)
            results[cmd] = result
            
            if result['success']:
                success_count += 1
            else:
                failure_count += 1
                if stop_on_error:
                    break
        
        # Add summary information
        results['summary'] = {
            'total_commands': len(commands),
            'successful': success_count,
            'failed': failure_count,
            'all_succeeded': failure_count == 0,
            'status': 'SUCCESS' if failure_count == 0 else 'PARTIAL' if success_count > 0 else 'FAILED'
        }
        
        return results
        
    def get_command_failures(self):
        """
        Get a list of commands that failed
        
        Returns:
            list: Commands that failed
        """
        failures = []
        for cmd, result in self.command_history.items():
            if not result['success']:
                failures.append(cmd)
        return failures


if __name__ == "__main__":
    # This module is not meant to be run directly
    print("This module provides SSH command handling with timeout features.")
    print("Import it into your main router audit script.")
