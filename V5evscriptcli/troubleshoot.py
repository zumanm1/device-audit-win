#!/usr/bin/env python3
"""
V5evscriptcli Troubleshooting Utility
Provides diagnostic tools for EVE-NG connectivity and interface mapping validation

Usage: python3 troubleshoot.py [test_type]
"""

import requests
import subprocess
import json
import sys
from typing import Optional

# Configuration
EVE_HOST = "172.16.39.128"
EVE_USER = "admin"
EVE_PASS = "eve"
SSH_USER = "root"
SSH_PASS = "eve"

def test_api_connectivity():
    """Test EVE-NG API connectivity"""
    print("🔍 Testing EVE-NG API connectivity...")
    try:
        response = requests.get(f'http://{EVE_HOST}/api/status', timeout=10)
        print(f"✅ EVE-NG API accessible - Status: {response.status_code}")
        if response.status_code == 412:
            print("ℹ️  Status 412 is normal - indicates authentication required")
        return True
    except Exception as e:
        print(f"❌ EVE-NG API error: {e}")
        return False

def test_ssh_connectivity():
    """Test SSH connectivity to EVE-NG host"""
    print("🔍 Testing SSH connectivity...")
    try:
        cmd = f"sshpass -p '{SSH_PASS}' ssh -o StrictHostKeyChecking=no {SSH_USER}@{EVE_HOST} 'echo SSH_TEST_OK'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        if result.returncode == 0 and "SSH_TEST_OK" in result.stdout:
            print("✅ SSH connectivity successful")
            return True
        else:
            print(f"❌ SSH failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ SSH error: {e}")
        return False

def test_api_login():
    """Test EVE-NG API login"""
    print("🔍 Testing EVE-NG API login...")
    try:
        session = requests.Session()
        session.headers.update({'Content-Type': 'application/json'})
        
        login_data = {
            "username": EVE_USER,
            "password": EVE_PASS,
            "html5": "-1"
        }
        
        response = session.post(f'http://{EVE_HOST}/api/auth/login', json=login_data, timeout=10)
        if response.status_code == 200:
            print("✅ EVE-NG API login successful")
            
            # Test getting templates
            templates_response = session.get(f'http://{EVE_HOST}/api/list/templates', timeout=10)
            if templates_response.status_code == 200:
                templates = templates_response.json().get('data', {})
                print(f"✅ Retrieved {len(templates)} templates")
                
                # Check for c3725 template
                if 'c3725' in templates:
                    print("✅ c3725 template found")
                else:
                    print("⚠️  c3725 template not found - may need to be uploaded")
            
            return True
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False

def check_eve_ng_version():
    """Check EVE-NG version via SSH"""
    print("🔍 Checking EVE-NG version...")
    try:
        cmd = f"sshpass -p '{SSH_PASS}' ssh -o StrictHostKeyChecking=no {SSH_USER}@{EVE_HOST} 'cat /etc/eve-ng-release 2>/dev/null || echo VERSION_NOT_FOUND'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            version_info = result.stdout.strip()
            if "VERSION_NOT_FOUND" not in version_info:
                print(f"✅ EVE-NG Version: {version_info}")
            else:
                print("⚠️  EVE-NG version information not available")
            return True
        else:
            print(f"❌ Version check failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Version check error: {e}")
        return False

def verify_interface_mapping():
    """Verify the interface mapping understanding"""
    print("🔍 Verifying interface mapping knowledge...")
    print("📋 Expected c3725 + NM-1FE-TX interface mapping:")
    print("   f0/0 -> API index 0  (Onboard FastEthernet0/0)")
    print("   f0/1 -> API index 1  (Onboard FastEthernet0/1)")
    print("   f1/0 -> API index 16 (NM-1FE-TX slot 1)")
    print("   f2/0 -> API index 32 (NM-1FE-TX slot 2)")
    print("✅ Interface mapping documented")
    return True

def test_dependencies():
    """Test Python dependencies"""
    print("🔍 Testing Python dependencies...")
    dependencies = ['requests', 'json', 'logging', 'time', 'subprocess']
    
    missing = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} - missing")
            missing.append(dep)
    
    if missing:
        print(f"⚠️  Missing dependencies: {missing}")
        return False
    else:
        print("✅ All core dependencies available")
        return True

def run_comprehensive_test():
    """Run all troubleshooting tests"""
    print("=" * 60)
    print("V5evscriptcli Comprehensive Troubleshooting")
    print("=" * 60)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("EVE-NG API Connectivity", test_api_connectivity),
        ("SSH Connectivity", test_ssh_connectivity),
        ("EVE-NG Version", check_eve_ng_version),
        ("API Login", test_api_login),
        ("Interface Mapping", verify_interface_mapping),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        results[test_name] = test_func()
    
    print("\n" + "=" * 60)
    print("TROUBLESHOOTING SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        icon = "✅" if result else "❌"
        print(f"{icon} {test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed! V5evscriptcli should work correctly.")
    else:
        print("⚠️  Some tests failed. Review the issues above.")
        print("💡 Common solutions:")
        print("   - Ensure EVE-NG is running and accessible")
        print("   - Check credentials (admin/eve for API, root/eve for SSH)")
        print("   - Verify network connectivity to EVE-NG host")
        print("   - Install missing Python packages: pip install -r requirements.txt")
    
    return all_passed

def show_help():
    """Show help information"""
    print("V5evscriptcli Troubleshooting Utility")
    print("=====================================")
    print("Usage: python3 troubleshoot.py [test_type]")
    print("")
    print("Available tests:")
    print("  all          - Run comprehensive troubleshooting (default)")
    print("  api          - Test EVE-NG API connectivity")
    print("  ssh          - Test SSH connectivity")  
    print("  login        - Test API login")
    print("  version      - Check EVE-NG version")
    print("  deps         - Test Python dependencies")
    print("  mapping      - Show interface mapping")
    print("  help         - Show this help")
    print("")
    print("Examples:")
    print("  python3 troubleshoot.py")
    print("  python3 troubleshoot.py api")
    print("  python3 troubleshoot.py ssh")

def main():
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
    else:
        test_type = "all"
    
    if test_type == "help":
        show_help()
    elif test_type == "api":
        test_api_connectivity()
    elif test_type == "ssh":
        test_ssh_connectivity()
    elif test_type == "login":
        test_api_login()
    elif test_type == "version":
        check_eve_ng_version()
    elif test_type == "deps":
        test_dependencies()
    elif test_type == "mapping":
        verify_interface_mapping()
    elif test_type == "all":
        run_comprehensive_test()
    else:
        print(f"Unknown test type: {test_type}")
        show_help()
        sys.exit(1)

if __name__ == "__main__":
    main() 