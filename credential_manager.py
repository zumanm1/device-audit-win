#!/usr/bin/env python3
"""
Credential Manager for Router Audit Tool
Provides encryption, decryption, and password hashing functionality
"""

import os
import base64
import hashlib
import secrets
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

class CredentialManager:
    """
    Handles encryption and decryption of sensitive credentials
    Uses Fernet symmetric encryption with a key derived from a master password
    """
    def __init__(self, master_password=None):
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
        # Create or load salt
        if os.path.exists(self.salt_file):
            with open(self.salt_file, 'rb') as f:
                self.salt = f.read()
        else:
            self.salt = secrets.token_bytes(16)  # Generate new salt
            with open(self.salt_file, 'wb') as f:
                f.write(self.salt)
        
        # Derive key from password and salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        
        # Create the key and cipher suite
        self.key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        self.cipher_suite = Fernet(self.key)
    
    def encrypt(self, plaintext):
        """
        Encrypt a string and return a base64-encoded encrypted value
        """
        if not self.cipher_suite:
            raise ValueError("Encryption not initialized. Call initialize() first.")
        
        if not plaintext:
            return None
            
        encrypted = self.cipher_suite.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_text):
        """
        Decrypt a base64-encoded encrypted value and return the plaintext
        """
        if not self.cipher_suite:
            raise ValueError("Encryption not initialized. Call initialize() first.")
        
        if not encrypted_text:
            return None
            
        try:
            decoded = base64.urlsafe_b64decode(encrypted_text.encode())
            decrypted = self.cipher_suite.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logging.error(f"Decryption error: {e}")
            return None
    
    def hash_password(self, password, salt=None):
        """
        Generate a secure hash of a password with an optional salt
        Returns (hash, salt) tuple
        """
        if not salt:
            salt = secrets.token_hex(16)
        
        # Create a hash with the password and salt
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode(), 
            salt.encode(), 
            100000
        )
        password_hash = hash_obj.hex()
        
        return password_hash, salt
    
    def verify_password(self, password, stored_hash, salt):
        """
        Verify a password against a stored hash and salt
        """
        hash_to_check, _ = self.hash_password(password, salt)
        return hash_to_check == stored_hash


if __name__ == "__main__":
    # Demo the credential manager
    print("Credential Manager Demo")
    manager = CredentialManager()
    
    # Get a master password
    master_password = input("Enter a master password: ")
    manager.initialize(master_password)
    
    # Test encryption
    plaintext = input("Enter text to encrypt: ")
    encrypted = manager.encrypt(plaintext)
    print(f"Encrypted: {encrypted}")
    
    # Test decryption
    decrypted = manager.decrypt(encrypted)
    print(f"Decrypted: {decrypted}")
    
    # Test password hashing
    password = input("Enter a password to hash: ")
    hash_value, salt = manager.hash_password(password)
    print(f"Hash: {hash_value}")
    print(f"Salt: {salt}")
    
    # Test password verification
    verify_password = input("Enter the password again to verify: ")
    verified = manager.verify_password(verify_password, hash_value, salt)
    print(f"Password verified: {verified}")
