#!/usr/bin/env python3
"""
Secure Password Module for Router Audit Tool

This module handles secure credential management for the router audit tool
including user-defined master password setup and validation.
"""

import os
import base64
import getpass
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

try:
    from colorama import Fore, Style
    colorama_available = True
except ImportError:
    # Create mock Fore and Style if colorama not available
    class MockColor:
        def __getattr__(self, name):
            return ""
    Fore = Style = MockColor()
    colorama_available = False

class CredentialManager:
    """
    Handles encryption and decryption of sensitive credentials
    Uses Fernet symmetric encryption with a key derived from a master password
    """
    
    def __init__(self, master_password=None):
        """Initialize credential manager with optional master password"""
        self.salt = None
        self.key = None
        self.cipher_suite = None
        self.salt_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.salt')
        
        # Initialize with master password if provided
        if master_password:
            self.initialize(master_password)
    
    def initialize(self, master_password):
        """
        Initialize the encryption with a master password
        Will create a new salt if none exists or load existing one
        """
        if os.path.exists(self.salt_file):
            # Load existing salt
            with open(self.salt_file, 'rb') as f:
                self.salt = f.read()
        else:
            # Generate new salt
            self.salt = os.urandom(16)
            # Save salt to file with secure permissions
            with open(self.salt_file, 'wb') as f:
                f.write(self.salt)
            os.chmod(self.salt_file, 0o600)  # Only user can read/write
        
        # Generate key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        
        # Derive the key from the password
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        self.cipher_suite = Fernet(key)
    
    def encrypt(self, plaintext):
        """
        Encrypt a string and return a base64-encoded encrypted value
        """
        if not self.cipher_suite:
            raise ValueError("Credential manager not initialized with a master password")
            
        if not plaintext:
            return ""
            
        return self.cipher_suite.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, encrypted_text):
        """
        Decrypt a base64-encoded encrypted value and return the plaintext
        """
        if not self.cipher_suite:
            raise ValueError("Credential manager not initialized with a master password")
            
        if not encrypted_text:
            return ""
            
        try:
            return self.cipher_suite.decrypt(encrypted_text.encode()).decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")
    
    def hash_password(self, password, salt=None):
        """
        Generate a secure hash of a password with an optional salt
        Returns (hash, salt) tuple
        """
        if not salt:
            salt = os.urandom(16)
            
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        password_hash = kdf.derive(password.encode())
        return base64.b64encode(password_hash).decode(), base64.b64encode(salt).decode()
    
    def verify_password(self, password, stored_hash, salt):
        """
        Verify a password against a stored hash and salt
        """
        password_hash, _ = self.hash_password(
            password, 
            base64.b64decode(salt)
        )
        return password_hash == stored_hash


def prompt_for_master_password(confirm=True):
    """
    Prompt user for a secure master password with confirmation
    Returns the entered password
    """
    print(f"\n{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}🔐 SECURITY SETUP - MASTER PASSWORD REQUIRED 🔐{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}This password will be used to encrypt all sensitive information.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}It will not be stored anywhere - please remember it!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
    
    while True:
        master_password = getpass.getpass(f"\n{Fore.CYAN}Enter your master password: {Style.RESET_ALL}")
        
        if not master_password:
            print(f"{Fore.RED}Password cannot be empty. Please try again.{Style.RESET_ALL}")
            continue
            
        # Skip confirmation if not required
        if not confirm:
            return master_password
            
        confirm_password = getpass.getpass(f"{Fore.CYAN}Confirm your master password: {Style.RESET_ALL}")
        
        if master_password != confirm_password:
            print(f"{Fore.RED}Passwords do not match. Please try again.{Style.RESET_ALL}")
        else:
            break
    
    print(f"\n{Fore.GREEN}✅ Master password successfully set{Style.RESET_ALL}")
    return master_password


# Example usage
if __name__ == "__main__":
    # Get master password from user
    password = prompt_for_master_password()
    
    # Initialize credential manager
    cred_manager = CredentialManager(password)
    
    # Example encryption
    secret_value = "super_secret_password123"
    encrypted = cred_manager.encrypt(secret_value)
    print(f"Encrypted: {encrypted}")
    
    # Example decryption
    decrypted = cred_manager.decrypt(encrypted)
    print(f"Decrypted: {decrypted}")
    
    # Verify roundtrip
    print(f"Original matches decrypted: {secret_value == decrypted}")
