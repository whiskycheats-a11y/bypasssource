#!/usr/bin/env python3
"""
ULTIMATE SAFE LAUNCHER
Choose and launch the best method for your needs
"""

import os
import sys
import subprocess

def print_banner():
    print("="*70)
    print("🚀 ULTIMATE SAFE METHOD LAUNCHER")
    print("="*70)
    print()

def print_methods():
    print("Available Methods:")
    print()
    print("1. Transparent Proxy (SSL Passthrough)")
    print("   - Stealth: ⭐⭐⭐")
    print("   - Setup: Medium")
    print("   - Best for: Testing")
    print()
    print("2. SOCKS5 Selective Routing ⭐ RECOMMENDED")
    print("   - Stealth: ⭐⭐⭐⭐")
    print("   - Setup: Easy")
    print("   - Best for: Most users")
    print()
    print("3. VPN Tunnel + Packet Filtering")
    print("   - Stealth: ⭐⭐⭐⭐")
    print("   - Setup: Hard (requires root)")
    print("   - Best for: Advanced users")
    print()
    print("4. DNS Hijacking ⭐⭐ MOST STEALTH")
    print("   - Stealth: ⭐⭐⭐⭐⭐")
    print("   - Setup: Medium (requires root)")
    print("   - Best for: Maximum safety")
    print()
    print("5. Original MITM Proxy (Ultra Safe Mode)")
    print("   - Your current setup")
    print()
    print("0. Exit")
    print()

def launch_method_1():
    """Launch Transparent Proxy"""
    print("\n[Method 1] Starting Transparent Proxy...")
    print("="*70)
    
    if not os.path.exists("transparent_proxy.py"):
        print("[Error] transparent_proxy.py not found!")
        return
    
    print("\n[Setup Instructions]")
    print("1. This will start transparent proxy on port 2130")
    print("2. Configure device proxy:")
    print("   - Type: HTTP")
    print("   - Host: <server_ip>")
    print("   - Port: 2130")
    print("3. SSL passthrough enabled for game traffic")
    print()
    
    input("Press Enter to start...")
    
    try:
        subprocess.run([
            "mitmdump",
            "-s", "transparent_proxy.py",
            "--mode", "transparent",
            "--set", "block_global=false",
            "-p", "2130"
        ])
    except KeyboardInterrupt:
        print("\n[Stopped] Transparent proxy stopped")
    except FileNotFoundError:
        print("[Error] mitmdump not found. Install mitmproxy first.")

def launch_method_2():
    """Launch SOCKS5 Proxy"""
    print("\n[Method 2] Starting SOCKS5 Selective Routing...")
    print("="*70)
    
    if not os.path.exists("method2_socks_proxy.py"):
        print("[Error] method2_socks_proxy.py not found!")
        return
    
    print("\n[Setup Instructions]")
    print("1. This will start SOCKS5 proxy on port 1080")
    print("2. Configure device proxy:")
    print("   - Type: SOCKS5")
    print("   - Host: <server_ip>")
    print("   - Port: 1080")
    print("3. Login traffic → Through proxy (UID bypass)")
    print("4. Ranked traffic → Direct connection (No detection!)")
    print()
    
    input("Press Enter to start...")
    
    try:
        subprocess.run([sys.executable, "method2_socks_proxy.py"])
    except KeyboardInterrupt:
        print("\n[Stopped] SOCKS5 proxy stopped")

def launch_method_3():
    """Launch VPN Tunnel"""
    print("\n[Method 3] Starting VPN Tunnel + Packet Filtering...")
    print("="*70)
    
    # Check root
    if os.name != 'nt' and os.geteuid() != 0:
        print("[Error] This method requires root privileges!")
        print("[Error] Run with: sudo python ultimate_launcher.py")
        return
    
    if not os.path.exists("method3_vpn_tunnel.py"):
        print("[Error] method3_vpn_tunnel.py not found!")
        return
    
    print("\n[Setup Instructions]")
    print("1. This will start packet filtering")
    print("2. Requires root/admin privileges")
    print("3. Requires scapy: pip install scapy")
    print("4. Login packets → Modified (UID bypass)")
    print("5. Game packets → Unchanged (No detection!)")
    print()
    
    input("Press Enter to start...")
    
    try:
        subprocess.run([sys.executable, "method3_vpn_tunnel.py"])
    except KeyboardInterrupt:
        print("\n[Stopped] VPN tunnel stopped")

def launch_method_4():
    """Launch DNS Hijacking"""
    print("\n[Method 4] Starting DNS Hijacking + Selective Routing...")
    print("="*70)
    
    # Check root
    if os.name != 'nt' and os.geteuid() != 0:
        print("[Error] This method requires root privileges for DNS (port 53)!")
        print("[Error] Run with: sudo python ultimate_launcher.py")
        return
    
    if not os.path.exists("method4_dns_hijack.py"):
        print("[Error] method4_dns_hijack.py not found!")
        return
    
    print("\n[Setup Instructions]")
    print("1. This will start DNS server on port 53")
    print("2. This will start HTTP proxy on port 8888")
    print("3. Configure device DNS ONLY:")
    print("   - Primary DNS: <server_ip>")
    print("   - Secondary DNS: 8.8.8.8")
    print("   - NO PROXY CONFIGURATION NEEDED!")
    print("4. Login domains → Hijacked (UID bypass)")
    print("5. Game domains → Normal DNS (No detection!)")
    print()
    print("[MOST STEALTH METHOD - Hardest to detect!]")
    print()
    
    input("Press Enter to start...")
    
    try:
        subprocess.run([sys.executable, "method4_dns_hijack.py"])
    except KeyboardInterrupt:
        print("\n[Stopped] DNS hijacking stopped")

def launch_method_5():
    """Launch Original MITM Proxy"""
    print("\n[Method 5] Starting Original MITM Proxy (Ultra Safe Mode)...")
    print("="*70)
    
    if not os.path.exists("main.py"):
        print("[Error] main.py not found!")
        return
    
    print("\n[Your Current Setup]")
    print("1. Ultra Safe Mode enabled")
    print("2. Ranked match modifications blocked")
    print("3. UID bypass at login")
    print()
    
    input("Press Enter to start...")
    
    try:
        subprocess.run([sys.executable, "main.py"])
    except KeyboardInterrupt:
        print("\n[Stopped] MITM proxy stopped")

def main():
    print_banner()
    
    while True:
        print_methods()
        
        try:
            choice = input("Select method (0-5): ").strip()
            
            if choice == "0":
                print("\n[Exit] Goodbye!")
                break
            elif choice == "1":
                launch_method_1()
            elif choice == "2":
                launch_method_2()
            elif choice == "3":
                launch_method_3()
            elif choice == "4":
                launch_method_4()
            elif choice == "5":
                launch_method_5()
            else:
                print("\n[Error] Invalid choice. Please select 0-5.")
            
            print("\n" + "="*70 + "\n")
            
        except KeyboardInterrupt:
            print("\n\n[Exit] Goodbye!")
            break
        except Exception as e:
            print(f"\n[Error] {e}")

if __name__ == "__main__":
    main()
