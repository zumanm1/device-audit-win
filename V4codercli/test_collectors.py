#!/usr/bin/env python3
"""
Systematic Collector Testing Script
Tests all collectors and provides detailed diagnostics
"""
import sys
import traceback
sys.path.append('.')

def test_collectors():
    """Test all collectors systematically."""
    try:
        print("🔧 Loading task system...")
        from rr4_complete_enchanced_v4_cli_tasks import get_layer_collector, get_available_layers
        
        layers = get_available_layers()
        print(f"📋 Available layers: {layers}")
        
        failed = []
        success = []
        
        for i, layer in enumerate(layers, 1):
            try:
                print(f"[{i}/{len(layers)}] Testing {layer}...", end="")
                collector = get_layer_collector(layer)
                print(f" ✅ {collector.__name__}")
                success.append(layer)
            except Exception as e:
                print(f" ❌ FAILED: {e}")
                failed.append((layer, str(e)))
        
        print(f"\n📊 RESULTS:")
        print(f"✅ Success: {len(success)}/{len(layers)} ({len(success)/len(layers)*100:.1f}%)")
        print(f"❌ Failed: {len(failed)}/{len(layers)} ({len(failed)/len(layers)*100:.1f}%)")
        
        if failed:
            print(f"\n🔍 FAILURE DETAILS:")
            for layer, error in failed:
                print(f"  - {layer}: {error}")
        
        return len(failed) == 0
            
    except Exception as e:
        print(f"❌ CRITICAL FAILURE: {e}")
        traceback.print_exc()
        return False

def test_environment():
    """Test environment configuration."""
    print("🔧 Testing environment...")
    try:
        from rr4_complete_enchanced_v4_cli_core.connection_manager import get_jump_host_config
        config = get_jump_host_config()
        print(f"✅ Environment loaded: Jump host = {config['hostname']}")
        return True
    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        return False

def test_main_scripts():
    """Test main script imports."""
    print("🔧 Testing main scripts...")
    scripts = [
        'start_rr4_cli_enhanced.py',
        'rr4-complete-enchanced-v4-cli.py'
    ]
    
    for script in scripts:
        try:
            print(f"  Testing {script}...", end="")
            # Just check if file exists and is readable
            with open(script, 'r') as f:
                content = f.read()
                if 'def main' in content or 'if __name__' in content:
                    print(" ✅")
                else:
                    print(" ⚠️ (No main function)")
        except Exception as e:
            print(f" ❌ {e}")

if __name__ == "__main__":
    print("🎯 SYSTEMATIC COLLECTOR TESTING")
    print("=" * 50)
    
    env_ok = test_environment()
    test_main_scripts()
    collectors_ok = test_collectors()
    
    print("\n" + "=" * 50)
    if env_ok and collectors_ok:
        print("🎉 ALL TESTS PASSED - System Ready!")
    else:
        print("⚠️ ISSUES DETECTED - Requires attention") 