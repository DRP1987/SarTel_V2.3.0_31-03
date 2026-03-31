"""Test security system in development mode."""

import os
from utils.security import security_manager

print("="*60)
print("SECURITY SYSTEM TEST")
print("="*60)

# Test 1: Get hardware ID
print("\n1. Hardware ID Test:")
hw_id = security_manager.get_hardware_id()
print(f"   Your Hardware ID: {hw_id}")
print(f"   ℹ️  Give this to customers for license binding")

# Test 2: Bypass license for development
print("\n2. Development Mode:")
print("   Bypassing license check for testing...")
security_manager.license_valid = True
print("   ✅ License check bypassed (development only)")

# Test 3: Test file decryption
print("\n3. Testing File Decryption:")
try:
    encrypted_config = "config/configurations.json.enc"
    
    if not os.path.exists(encrypted_config):
        print(f"   ❌ File not found: {encrypted_config}")
        print(f"   Run:  python encrypt_files.py")
    else:
        decrypted = security_manager.decrypt_file(encrypted_config)
        import json
        data = json.loads(decrypted. decode('utf-8'))
        print(f"   ✅ Decryption successful!")
        print(f"   Found {len(data.  get('configurations', []))} configurations")
        
except Exception as e:
    print(f"   ❌ Decryption failed: {e}")
    import traceback
    traceback. print_exc()

# Test 4: Test config loader
print("\n4. Testing Configuration Loader:")
try:
    from config.config_loader import ConfigurationLoader
    loader = ConfigurationLoader()
    configs = loader.load_configurations()
    print(f"   ✅ Loaded {len(configs)} configurations successfully")
    
    if configs:
        print(f"   First config: {configs[0].  get('name', 'Unnamed')}")
        
except Exception as e:
    print(f"   ❌ Config loader failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Anti-debug check
print("\n5. Security Checks:")
if security_manager. check_anti_debug():
    print("   ⚠️  Debugger detected!")
else:
    print("   ✅ No debugger detected")

if security_manager.verify_integrity():
    print("   ✅ Integrity check passed")
else:
    print("   ⚠️  Integrity check failed")

print("\n" + "="*60)
print("✅ ALL TESTS COMPLETE!")
print("="*60)
print("\nNext steps:")
print("1. Update main.py to add license validation")
print("2. Update GUI to handle encrypted PDFs")
print("3. Build executable")

input("\nPress Enter to exit...")