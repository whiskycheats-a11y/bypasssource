#!/usr/bin/env python3
"""
START ULTIMATE SAFE PROXY
Single command to start everything on port 2130
"""

import subprocess
import sys
import os

def print_banner():
    print("="*70)
    print("🚀 ULTIMATE SAFE PROXY LAUNCHER")
    print("="*70)
    print()
    print("✅ Port: 2130 (Single port for everything)")
    print("✅ Login: UID Bypass enabled")
    print("✅ Ranked: Zero modifications (100% safe)")
    print("✅ All methods combined in one!")
    print()
    print("="*70)
    print()

def check_files():
    """Check if required files exist"""
    required_files = [
        'ULTIMATE_SAFE_PROXY.py',
        'mitmproxyutils.py',
        'protocols/protobuf_utils.py',
        'whitelist.json'
    ]
    
    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)
    
    if missing:
        print("❌ Missing required files:")
        for file in missing:
            print(f"   - {file}")
        print()
        return False
    
    print("✅ All required files found")
    print()
    return True

def start_proxy():
    """Start the ultimate safe proxy"""
    print("Starting Ultimate Safe Proxy on port 2130...")
    print()
    
    try:
        # Start mitmdump with ULTIMATE_SAFE_PROXY.py
        subprocess.run([
            'mitmdump',
            '-s', 'ULTIMATE_SAFE_PROXY.py',
            '-p', '2130',
            '--listen-host', '0.0.0.0',
            '--set', 'block_global=false',
            '--set', f'confdir=certs'
        ])
    except KeyboardInterrupt:
        print("\n\n[Stopped] Ultimate Safe Proxy stopped")
    except FileNotFoundError:
        print("❌ Error: mitmdump not found!")
        print("   Install mitmproxy: pip install mitmproxy")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print_banner()
    
    if not check_files():
        print("Please ensure all files are uploaded to VexaNode")
        return
    
    print("="*70)
    print("DEVICE CONFIGURATION")
    print("="*70)
    print()
    print("Configure your device proxy:")
    print("  Proxy Type: HTTP/HTTPS")
    print("  Host: <vexanode_ip>")
    print("  Port: 2130")
    print()
    print("="*70)
    print()
    
    input("Press Enter to start the proxy...")
    print()
    
    start_proxy()

if __name__ == "__main__":
    main()
