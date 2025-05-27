#!/usr/bin/env python3
"""
Unit tests for the Credential Manager module
"""

import unittest
import os
import base64
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from credential_manager import CredentialManager

class TestCredentialManager(unittest.TestCase):
    """Test cases for the CredentialManager class"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temp directory for test salt file
        self.test_dir = tempfile.TemporaryDirectory()
        self.salt_file_path = os.path.join(self.test_dir.name, '.salt')
        
        # Create credential manager with test master password and patch its salt_file attribute
        self.manager = CredentialManager()
        self.manager.salt_file = self.salt_file_path
        self.manager.initialize("test_master_password")
        
    def tearDown(self):
        """Clean up after tests"""
        self.test_dir.cleanup()
    
    def test_initialize_creates_salt_file(self):
        """Test that initialize creates a salt file if it doesn't exist"""
        # The salt file should have been created in setUp
        self.assertTrue(os.path.exists(self.salt_file_path))
        
        # Check that the salt file has content
        with open(self.salt_file_path, 'rb') as f:
            salt_data = f.read()
        self.assertTrue(len(salt_data) > 0)
    
    def test_initialize_loads_existing_salt(self):
        """Test that initialize loads an existing salt file"""
        # Create a new salt file with known content
        test_salt = b'test_salt_data_12345'
        with open(self.salt_file_path, 'wb') as f:
            f.write(test_salt)
        
        # Create a new manager and point it to our test salt file
        new_manager = CredentialManager()
        new_manager.salt_file = self.salt_file_path
        new_manager.initialize("test_master_password")
        
        # Verify the salt was loaded from the file
        self.assertEqual(new_manager.salt, test_salt)
    
    def test_encrypt_decrypt(self):
        """Test the encryption and decryption functionality"""
        # Test with a simple string
        plaintext = "cisco_password123"
        encrypted = self.manager.encrypt(plaintext)
        
        # Verify encrypted text is not the same as plaintext
        self.assertNotEqual(encrypted, plaintext)
        
        # Verify we can decrypt it back to the original
        decrypted = self.manager.decrypt(encrypted)
        self.assertEqual(decrypted, plaintext)
    
    def test_encrypt_decrypt_none(self):
        """Test encrypt and decrypt with None values"""
        # None should return None for both encrypt and decrypt
        self.assertIsNone(self.manager.encrypt(None))
        self.assertIsNone(self.manager.decrypt(None))
    
    def test_decrypt_invalid_data(self):
        """Test decrypting invalid data returns None and logs error"""
        with patch('logging.error') as mock_log:
            result = self.manager.decrypt("invalid_encrypted_data")
            self.assertIsNone(result)
            mock_log.assert_called_once()
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "secure_password"
        
        # Test with auto-generated salt
        hash1, salt1 = self.manager.hash_password(password)
        self.assertTrue(len(hash1) > 0)
        self.assertTrue(len(salt1) > 0)
        
        # Test with provided salt
        salt2 = "fixed_salt_for_testing"
        hash2, salt2_returned = self.manager.hash_password(password, salt2)
        self.assertEqual(salt2, salt2_returned)
        
        # Test same password with same salt gives same hash
        hash3, _ = self.manager.hash_password(password, salt2)
        self.assertEqual(hash2, hash3)
        
        # Test different password with same salt gives different hash
        hash4, _ = self.manager.hash_password("different_password", salt2)
        self.assertNotEqual(hash2, hash4)
    
    def test_verify_password(self):
        """Test password verification"""
        password = "test_verification_pw"
        hash_value, salt = self.manager.hash_password(password)
        
        # Correct password should verify
        self.assertTrue(self.manager.verify_password(password, hash_value, salt))
        
        # Incorrect password should fail
        self.assertFalse(self.manager.verify_password("wrong_password", hash_value, salt))
    
    def test_initialization_required(self):
        """Test that operations fail if not initialized"""
        # Create an uninitialized manager
        uninitialized = CredentialManager()
        
        # Trying to encrypt or decrypt should raise ValueError
        with self.assertRaises(ValueError):
            uninitialized.encrypt("test")
            
        with self.assertRaises(ValueError):
            uninitialized.decrypt("test")

if __name__ == "__main__":
    unittest.main()
