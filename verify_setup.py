#!/usr/bin/env python3
"""
Setup Verification Script
Checks if everything is configured correctly for ultra safe mode
"""

import os
import json
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def check_file(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        print(f"✅ {description}: Found")
        return True
    else:
        print(f"❌ {description}: NOT FOUND")
        return False

def check_json_file(filepath, description, required_keys=None):
    """Check if JSON file exists and has required keys"""
    if not Path(filepath).exists():
        print(f"❌ {description}: NOT FOUND")
        return False
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        if required_keys:
            missing_keys = [key for key in required_keys if key not in data]
            if missing_keys:
                print(f"⚠️  {description}: Missing keys: {missing_keys}")
                return False
        
        print(f"✅ {description}: Valid")
        return True
    except json.JSONDecodeError:
        print(f"❌ {description}: Invalid JSON")
        return False
    except Exception as e:
        print(f"❌ {description}: Error - {e}")
        return False

def check_whitelist():
    """Check whitelist configuration"""
    filepath = "whitelist.json"
    if not Path(filepath).exists():
        print(f"⚠️  whitelist.json: Not found (will be created)")
        return True
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        if "whitelisted_uids" in data:
            uid_count = len(data["whitelisted_uids"])
            print(f"✅ whitelist.json: {uid_count} UID(s) whitelisted")
            
            if uid_count == 0:
                print(f"⚠️  No UIDs whitelisted yet - Add your UID!")
            else:
                print(f"   UIDs: {list(data['whitelisted_uids'].keys())[:5]}")
            return True
        else:
            print(f"⚠️  whitelist.json: No 'whitelisted_uids' key")
            return False
    except Exception as e:
        print(f"❌ whitelist.json: Error - {e}")
        return False

def check_safe_mode_config():
    """Check safe mode configuration"""
    filepath = "safe_mode_config.json"
    if not Path(filepath).exists():
        print(f"⚠️  safe_mode_config.json: Not found (will use defaults)")
        return True
    
    try:
        with open(filepath, 'r') as f:
            config = json.load(f)
        
        ultra_safe = config.get("ultra_safe_mode", False)
        block_ranked = config.get("settings", {}).get("block_all_ranked", False)
        
        if ultra_safe and block_ranked:
            print(f"✅ safe_mode_config.json: ULTRA SAFE MODE ENABLED")
            print(f"   - ultra_safe_mode: {ultra_safe}")
            print(f"   - block_all_ranked: {block_ranked}")
            return True
        else:
            print(f"⚠️  safe_mode_config.json: NOT IN ULTRA SAFE MODE")
            print(f"   - ultra_safe_mode: {ultra_safe} (should be true)")
            print(f"   - block_all_ranked: {block_ranked} (should be true)")
            return False
    except Exception as e:
        print(f"❌ safe_mode_config.json: Error - {e}")
        return False

def check_certificates():
    """Check if certificates exist"""
    cert_dir = Path("certs")
    if not cert_dir.exists():
        print(f"❌ certs/ directory: NOT FOUND")
        return False
    
    required_certs = [
        "mitmproxy-ca-cert.pem",
        "mitmproxy-ca-cert.cer"
    ]
    
    all_found = True
    for cert in required_certs:
        cert_path = cert_dir / cert
        if cert_path.exists():
            print(f"✅ {cert}: Found")
        else:
            print(f"❌ {cert}: NOT FOUND")
            all_found = False
    
    return all_found

def main():
    print_header("🛡️ ULTRA SAFE MODE - SETUP VERIFICATION")
    
    checks = []
    
    # Check core files
    print_header("Core Files")
    checks.append(check_file("main.py", "main.py"))
    checks.append(check_file("mitmproxyutils.py", "mitmproxyutils.py"))
    checks.append(check_file("ultra_safe_mode.py", "ultra_safe_mode.py"))
    checks.append(check_file("whitelist_bot.py", "whitelist_bot.py"))
    
    # Check configuration files
    print_header("Configuration Files")
    checks.append(check_json_file("bot_config.json", "bot_config.json"))
    checks.append(check_whitelist())
    checks.append(check_safe_mode_config())
    
    # Check certificates
    print_header("Certificates")
    checks.append(check_certificates())
    
    # Check crypto modules
    print_header("Crypto Modules")
    checks.append(check_file("crypto/encryption_utils.py", "encryption_utils.py"))
    checks.append(check_file("crypto/__init__.py", "crypto/__init__.py"))
    
    # Check protocol modules
    print_header("Protocol Modules")
    checks.append(check_file("protocols/protobuf_utils.py", "protobuf_utils.py"))
    checks.append(check_file("protocols/__init__.py", "protocols/__init__.py"))
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    passed = sum(checks)
    total = len(checks)
    percentage = (passed / total) * 100 if total > 0 else 0
    
    print(f"Checks Passed: {passed}/{total} ({percentage:.1f}%)")
    
    if percentage == 100:
        print(f"\n✅ ALL CHECKS PASSED!")
        print(f"\n🚀 Your system is ready to use!")
        print(f"\nNext steps:")
        print(f"1. Add your UID to whitelist")
        print(f"2. Install certificate on device")
        print(f"3. Configure proxy settings")
        print(f"4. Run: python main.py")
    elif percentage >= 80:
        print(f"\n⚠️  MOSTLY READY - Fix minor issues")
        print(f"\nCheck the warnings above and fix them.")
    else:
        print(f"\n❌ SETUP INCOMPLETE")
        print(f"\nPlease fix the errors above before proceeding.")
    
    # Additional recommendations
    print_header("RECOMMENDATIONS")
    
    # Check if ultra safe mode is enabled
    if Path("safe_mode_config.json").exists():
        try:
            with open("safe_mode_config.json", 'r') as f:
                config = json.load(f)
            
            if not config.get("ultra_safe_mode", False):
                print(f"⚠️  ENABLE ULTRA SAFE MODE for maximum protection")
                print(f"   Edit safe_mode_config.json:")
                print(f'   "ultra_safe_mode": true')
        except:
            pass
    
    # Check whitelist
    if Path("whitelist.json").exists():
        try:
            with open("whitelist.json", 'r') as f:
                data = json.load(f)
            
            if not data.get("whitelisted_uids"):
                print(f"\n⚠️  ADD YOUR UID to whitelist")
                print(f"   Use Discord bot: /add <uid> <server> <days>")
                print(f"   Or edit whitelist.json manually")
        except:
            pass
    
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    main()
