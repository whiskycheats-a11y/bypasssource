"""
METHOD 4: DNS HIJACKING + SELECTIVE ROUTING (BEST METHOD!)
Hijack DNS for login servers only
Ranked servers resolve normally
Server can't detect because DNS is legitimate!
"""

import socket
import struct
from dnslib import DNSRecord, DNSHeader, RR, A, QTYPE
from dnslib.server import DNSServer, BaseResolver
import threading

class SelectiveDNSResolver(BaseResolver):
    """
    DNS resolver that hijacks only login domains.
    Game/ranked domains resolve normally.
    """
    
    def __init__(self):
        # Domains to hijack (redirect to our proxy)
        self.hijack_domains = [
            'login.ff.garena.com',
            'auth.garena.com',
            'account.garena.com',
            'signin.freefire.com'
        ]
        
        # Our proxy server IP
        self.proxy_ip = '127.0.0.1'
        
        # Real DNS server for normal resolution
        self.real_dns = '8.8.8.8'
        
        self.hijacked_count = 0
        self.normal_count = 0
    
    def should_hijack(self, domain: str) -> bool:
        """Check if domain should be hijacked"""
        domain_lower = domain.lower().rstrip('.')
        
        # Exact match
        if domain_lower in self.hijack_domains:
            return True
        
        # Keyword match for login
        login_keywords = ['login', 'auth', 'account', 'signin']
        for keyword in login_keywords:
            if keyword in domain_lower:
                return True
        
        return False
    
    def resolve(self, request, handler):
        """Resolve DNS request"""
        try:
            qname = str(request.q.qname)
            qtype = QTYPE[request.q.qtype]
            
            if self.should_hijack(qname):
                # Hijack - return our proxy IP
                self.hijacked_count += 1
                print(f"[🎯 HIJACK] {qname} → {self.proxy_ip}")
                
                reply = request.reply()
                reply.add_answer(RR(qname, QTYPE.A, rdata=A(self.proxy_ip), ttl=60))
                return reply
                
            else:
                # Normal resolution - use real DNS
                self.normal_count += 1
                print(f"[✓ NORMAL] {qname} → Real DNS")
                
                # Forward to real DNS
                return self.forward_to_real_dns(request)
                
        except Exception as e:
            print(f"[Error] DNS resolution error: {e}")
            return request.reply()
    
    def forward_to_real_dns(self, request):
        """Forward request to real DNS server"""
        try:
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            
            # Send to real DNS
            sock.sendto(request.pack(), (self.real_dns, 53))
            
            # Get response
            data, _ = sock.recvfrom(512)
            sock.close()
            
            # Parse and return
            return DNSRecord.parse(data)
            
        except Exception as e:
            print(f"[Error] DNS forward error: {e}")
            return request.reply()

class HijackProxy:
    """
    HTTP proxy that handles hijacked traffic.
    Only modifies login requests, passes game traffic.
    """
    
    def __init__(self, port=8888):
        self.port = port
        self.server = None
    
    def handle_client(self, client_socket):
        """Handle hijacked HTTP request"""
        try:
            # Receive request
            request = client_socket.recv(4096)
            
            if b'login' in request.lower() or b'auth' in request.lower():
                # Login request - apply UID bypass
                print(f"[PROXY] Login request - Applying UID bypass")
                modified_request = self.apply_uid_bypass(request)
                
                # Forward modified request
                response = self.forward_request(modified_request)
                client_socket.sendall(response)
                
            else:
                # Other request - pass through
                print(f"[PROXY] Normal request - Passing through")
                response = self.forward_request(request)
                client_socket.sendall(response)
                
        except Exception as e:
            print(f"[Error] Proxy error: {e}")
        finally:
            client_socket.close()
    
    def apply_uid_bypass(self, request):
        """Apply UID bypass to request"""
        # Your UID bypass logic here
        return request
    
    def forward_request(self, request):
        """Forward request to real server"""
        try:
            # Parse request to get host
            lines = request.split(b'\r\n')
            host = None
            for line in lines:
                if line.startswith(b'Host:'):
                    host = line.split(b': ')[1].decode()
                    break
            
            if not host:
                return b"HTTP/1.1 400 Bad Request\r\n\r\n"
            
            # Connect to real server
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, 80))
            sock.sendall(request)
            
            # Get response
            response = b""
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                response += data
            
            sock.close()
            return response
            
        except Exception as e:
            print(f"[Error] Forward error: {e}")
            return b"HTTP/1.1 500 Internal Server Error\r\n\r\n"
    
    def start(self):
        """Start proxy server"""
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('0.0.0.0', self.port))
        self.server.listen(100)
        
        print(f"[PROXY] HTTP proxy listening on port {self.port}")
        
        while True:
            client, addr = self.server.accept()
            thread = threading.Thread(target=self.handle_client, args=(client,))
            thread.daemon = True
            thread.start()

def start_dns_server():
    """Start DNS server"""
    resolver = SelectiveDNSResolver()
    server = DNSServer(resolver, port=53, address='0.0.0.0')
    
    print(f"[DNS] DNS server listening on port 53")
    print(f"[DNS] Login domains → Hijacked")
    print(f"[DNS] Game domains → Normal resolution")
    
    server.start_thread()
    return server

def start_http_proxy():
    """Start HTTP proxy"""
    proxy = HijackProxy(port=8888)
    
    thread = threading.Thread(target=proxy.start)
    thread.daemon = True
    thread.start()
    
    return proxy

if __name__ == "__main__":
    import os
    
    # Check root privileges
    if os.name != 'nt' and os.geteuid() != 0:
        print("[Error] This script requires root privileges for DNS (port 53)")
        print("[Error] Run with: sudo python method4_dns_hijack.py")
        exit(1)
    
    print("="*60)
    print("METHOD 4: DNS HIJACKING + SELECTIVE ROUTING")
    print("="*60)
    print()
    
    # Start DNS server
    dns_server = start_dns_server()
    
    # Start HTTP proxy
    http_proxy = start_http_proxy()
    
    print()
    print("="*60)
    print("SYSTEM READY!")
    print("="*60)
    print()
    print("Configure device DNS to this server's IP")
    print("Login traffic will be hijacked for UID bypass")
    print("Game/ranked traffic will resolve normally")
    print()
    print("Press Ctrl+C to stop")
    print("="*60)
    
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Shutdown] Stopping servers...")
