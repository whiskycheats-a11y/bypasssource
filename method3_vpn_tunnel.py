"""
METHOD 3: VPN TUNNEL + PACKET FILTERING
Create VPN tunnel, filter only login packets
Ranked packets go through normal VPN (no modification)
"""

import os
import subprocess
from scapy.all import *
from scapy.layers.inet import IP, TCP

class SelectiveVPNTunnel:
    """
    VPN tunnel that filters packets selectively.
    Only modifies login packets, rest pass through unchanged.
    """
    
    def __init__(self):
        self.login_ports = [80, 443, 8080]  # Ports for login traffic
        self.game_ports = [39003, 39004, 39005]  # Free Fire game ports
        
        # Packet counters
        self.login_packets = 0
        self.game_packets = 0
        self.modified_packets = 0
    
    def is_login_packet(self, packet) -> bool:
        """Check if packet is login-related"""
        if packet.haslayer(TCP):
            # Check destination port
            dport = packet[TCP].dport
            
            # Check if it's HTTP/HTTPS (login)
            if dport in [80, 443, 8080]:
                # Check payload for login keywords
                if packet.haslayer(Raw):
                    payload = packet[Raw].load
                    login_keywords = [b'login', b'auth', b'signin', b'account']
                    for keyword in login_keywords:
                        if keyword in payload.lower():
                            return True
        
        return False
    
    def is_game_packet(self, packet) -> bool:
        """Check if packet is game/ranked traffic"""
        if packet.haslayer(TCP):
            dport = packet[TCP].dport
            
            # Free Fire game ports
            if dport in self.game_ports:
                return True
            
            # Check payload for game keywords
            if packet.haslayer(Raw):
                payload = packet[Raw].load
                game_keywords = [b'match', b'game', b'battle', b'ranked']
                for keyword in game_keywords:
                    if keyword in payload.lower():
                        return True
        
        return False
    
    def process_packet(self, packet):
        """Process each packet"""
        try:
            if self.is_login_packet(packet):
                # Login packet - can modify for UID bypass
                self.login_packets += 1
                print(f"[LOGIN] Packet detected - Applying UID bypass")
                
                # Modify packet here for UID bypass
                modified_packet = self.apply_uid_bypass(packet)
                self.modified_packets += 1
                
                # Send modified packet
                send(modified_packet, verbose=0)
                
            elif self.is_game_packet(packet):
                # Game packet - pass through unchanged
                self.game_packets += 1
                print(f"[GAME] Packet detected - Passing through unchanged")
                
                # Send original packet unchanged
                send(packet, verbose=0)
                
            else:
                # Other traffic - pass through
                send(packet, verbose=0)
                
        except Exception as e:
            print(f"[Error] Packet processing error: {e}")
    
    def apply_uid_bypass(self, packet):
        """Apply UID bypass to login packet"""
        # Your UID bypass logic here
        # Modify packet payload
        return packet
    
    def start_sniffing(self, interface="eth0"):
        """Start packet sniffing"""
        print(f"[VPN] Starting selective packet filtering on {interface}")
        print(f"[VPN] Login packets → Modified (UID bypass)")
        print(f"[VPN] Game packets → Unchanged (No detection)")
        
        # Sniff packets
        sniff(iface=interface, prn=self.process_packet, store=0)
    
    def print_stats(self):
        """Print statistics"""
        print(f"\n[STATS] Packet Statistics:")
        print(f"  Login packets: {self.login_packets}")
        print(f"  Game packets: {self.game_packets}")
        print(f"  Modified packets: {self.modified_packets}")

if __name__ == "__main__":
    # Requires root/admin privileges
    if os.geteuid() != 0:
        print("[Error] This script requires root privileges")
        print("[Error] Run with: sudo python method3_vpn_tunnel.py")
        exit(1)
    
    tunnel = SelectiveVPNTunnel()
    
    try:
        tunnel.start_sniffing()
    except KeyboardInterrupt:
        tunnel.print_stats()
