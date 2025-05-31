"""Base collector class for all layer collectors."""

from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import logging

class BaseCollector(ABC):
    """Base class for all layer collectors."""
    
    def __init__(self, device_type: str = 'cisco_ios'):
        """Initialize the collector.
        
        Args:
            device_type: The type of device (cisco_ios, cisco_iosxe, cisco_iosxr)
        """
        self.device_type = device_type.lower()
        self.logger = logging.getLogger(f'rr4_collector.{self.__class__.__name__}')
        self.success = False
        self.commands = self._get_device_commands()
        
    @abstractmethod
    def _get_device_commands(self) -> Dict[str, List[str]]:
        """Get the list of commands for each device type.
        
        Returns:
            Dict mapping device types to lists of commands
        """
        pass
    
    def get_commands(self) -> List[str]:
        """Get the list of commands for the current device type.
        
        Returns:
            List of commands to execute
        """
        return self.commands.get(self.device_type, [])
    
    def save_command_output(self, command: str, output: str, output_dir: str) -> None:
        """Save command output to a file.
        
        Args:
            command: The command that was executed
            output: The command output
            output_dir: Directory to save the output
        """
        try:
            # Convert command to filename
            filename = command.replace(' ', '_').replace('|', '__pipe__') + '.txt'
            filepath = f"{output_dir}/{filename}"
            
            with open(filepath, 'w') as f:
                f.write(output)
            
            self.logger.debug(f"Saved output for command '{command}' to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to save command output: {e}")
            raise
    
    def process_output(self, outputs: Dict[str, str]) -> Dict[str, Any]:
        """Process the command outputs and extract relevant data.
        
        Args:
            outputs: Dict mapping commands to their outputs
            
        Returns:
            Dict containing processed data
        """
        try:
            processed_data = {}
            for command, output in outputs.items():
                if output:
                    # Basic processing - override in subclasses
                    processed_data[command] = {
                        'raw_output': output,
                        'success': True
                    }
                else:
                    processed_data[command] = {
                        'raw_output': '',
                        'success': False,
                        'error': 'No output received'
                    }
            
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Failed to process command outputs: {e}")
            raise
    
    def validate_outputs(self, outputs: Dict[str, str]) -> bool:
        """Validate that all required outputs were collected.
        
        Args:
            outputs: Dict mapping commands to their outputs
            
        Returns:
            True if all required outputs are present and valid
        """
        try:
            # Check if we have output for all commands
            expected_commands = set(self.get_commands())
            received_commands = set(outputs.keys())
            
            if not expected_commands.issubset(received_commands):
                missing = expected_commands - received_commands
                self.logger.warning(f"Missing outputs for commands: {missing}")
                return False
            
            # Check if outputs are non-empty
            for command, output in outputs.items():
                if not output or output.isspace():
                    self.logger.warning(f"Empty output for command: {command}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to validate outputs: {e}")
            return False
    
    def collect(self, connection: Any, output_dir: str) -> Dict[str, Any]:
        """Collect data from the device.
        
        Args:
            connection: Device connection object
            output_dir: Directory to save command outputs
            
        Returns:
            Dict containing collection results
        """
        try:
            outputs = {}
            commands = self.get_commands()
            
            if not commands:
                self.logger.warning(f"No commands defined for device type: {self.device_type}")
                return {'success': False, 'error': f"No commands for {self.device_type}"}
            
            # Execute commands
            for command in commands:
                try:
                    output = connection.send_command(command)
                    outputs[command] = output
                    self.save_command_output(command, output, output_dir)
                except Exception as e:
                    self.logger.error(f"Failed to execute command '{command}': {e}")
                    outputs[command] = ''
            
            # Validate and process outputs
            if self.validate_outputs(outputs):
                processed_data = self.process_output(outputs)
                self.success = True
                return {
                    'success': True,
                    'data': processed_data
                }
            else:
                return {
                    'success': False,
                    'error': "Failed to collect all required data"
                }
            
        except Exception as e:
            self.logger.error(f"Collection failed: {e}")
            return {
                'success': False,
                'error': str(e)
            } 