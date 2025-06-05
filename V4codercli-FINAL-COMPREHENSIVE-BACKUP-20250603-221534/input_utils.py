#!/usr/bin/env python3
"""
Input Handling Utilities for V4CODERCLI
Robust input handling with EOF, automation, and validation support
"""

from typing import List, Optional
import sys

class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'

def print_error(message: str):
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")

def safe_input(prompt: str, valid_choices: List[str] = None, default: str = None, max_attempts: int = 50) -> Optional[str]:
    """
    Safe input function with EOF handling and validation
    
    Args:
        prompt: Input prompt to display
        valid_choices: List of valid input choices (optional)
        default: Default value on EOF or empty input
        max_attempts: Maximum input attempts before giving up
    
    Returns:
        User input or default value, None if cancelled
    """
    attempts = 0
    while attempts < max_attempts:
        try:
            user_input = input(prompt).strip()
            
            # Handle empty input
            if not user_input and default is not None:
                return default
            
            # Validate against choices if provided
            if valid_choices is not None:
                if user_input in valid_choices:
                    return user_input
                else:
                    if len(valid_choices) <= 10:  # Show choices if not too many
                        valid_str = ', '.join(valid_choices)
                        print_error(f"Invalid choice. Please enter one of: {valid_str}")
                    else:
                        print_error(f"Invalid choice. Please enter a valid option.")
                    attempts += 1
                    continue
            
            return user_input
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Operation cancelled by user.{Colors.RESET}")
            return None
            
        except EOFError:
            # Handle EOF gracefully (automation/piped input)
            if default is not None:
                print(f"\n{Colors.YELLOW}End of input reached. Using default: {default}{Colors.RESET}")
                return default
            else:
                print(f"\n{Colors.YELLOW}End of input reached. Operation cancelled.{Colors.RESET}")
                return None
                
        except Exception as e:
            print_error(f"Input error: {str(e)}")
            attempts += 1
            if attempts >= max_attempts:
                print_error("Too many input errors. Operation cancelled.")
                return None
    
    print_error("Maximum input attempts reached. Operation cancelled.")
    return None

def safe_yes_no_input(prompt: str, default: str = None) -> Optional[bool]:
    """
    Safe yes/no input with EOF handling
    
    Args:
        prompt: Input prompt to display
        default: Default value ('y' or 'n') on EOF or empty input
    
    Returns:
        True for yes, False for no, None if cancelled
    """
    result = safe_input(prompt, valid_choices=['y', 'yes', 'n', 'no'], default=default)
    
    if result is None:
        return None
    
    return result.lower() in ['y', 'yes']

def safe_choice_input(prompt: str, choices: List[str], default: str = None) -> Optional[str]:
    """
    Safe choice input with validation
    
    Args:
        prompt: Input prompt to display
        choices: List of valid choices
        default: Default choice on EOF or empty input
    
    Returns:
        Selected choice or None if cancelled
    """
    return safe_input(prompt, valid_choices=choices, default=default)

def safe_numeric_input(prompt: str, min_val: int = None, max_val: int = None, default: int = None) -> Optional[int]:
    """
    Safe numeric input with range validation
    
    Args:
        prompt: Input prompt to display
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        default: Default value on EOF or empty input
    
    Returns:
        Integer value or None if cancelled
    """
    attempts = 0
    max_attempts = 50
    
    while attempts < max_attempts:
        try:
            user_input = input(prompt).strip()
            
            # Handle empty input
            if not user_input and default is not None:
                return default
            
            # Convert to integer
            value = int(user_input)
            
            # Validate range
            if min_val is not None and value < min_val:
                print_error(f"Value must be at least {min_val}")
                attempts += 1
                continue
                
            if max_val is not None and value > max_val:
                print_error(f"Value must be at most {max_val}")
                attempts += 1
                continue
            
            return value
            
        except ValueError:
            print_error("Please enter a valid number.")
            attempts += 1
            continue
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Operation cancelled by user.{Colors.RESET}")
            return None
            
        except EOFError:
            # Handle EOF gracefully (automation/piped input)
            if default is not None:
                print(f"\n{Colors.YELLOW}End of input reached. Using default: {default}{Colors.RESET}")
                return default
            else:
                print(f"\n{Colors.YELLOW}End of input reached. Operation cancelled.{Colors.RESET}")
                return None
                
        except Exception as e:
            print_error(f"Input error: {str(e)}")
            attempts += 1
            if attempts >= max_attempts:
                print_error("Too many input errors. Operation cancelled.")
                return None
    
    print_error("Maximum input attempts reached. Operation cancelled.")
    return None 