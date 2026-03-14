"""
METHOD 2: SOCKS5 PROXY + SELECTIVE ROUTING
Route only login traffic through proxy, ranked traffic direct
"""

import socket
import select
import threading
import struct

class SOCKS5Proxy:
    """
    SOCKS5 proxy that routes traffic selectively.
    Login traffic → Through proxy (UID bypass)
    Ranked traffic → Direct connection (no detection)
    """
    
    def __init__(self, host='0.0.0.0', port=1080):
        self.host = host
        self.port = port
        self.server = None
        
        # Domains to route through proxy
        self.proxy_domains = [
            'login', 'auth', 'account', 'signin'
        ]
        
        # Domains to route direct (bypass proxy)
        self.direct_domains = [
            'match', 'game', 'battle', 'ranked', 'anticheat'
        ]
    
    def should_proxy(self, domain: str) -> bool:
        """Decide if traffic should go through proxy"""
        domain_lower = domain.lower()
        
        # Check if it's ranked/game traffic - go direct
        for keyword in self.direct_domains:
            if keyword in domain_lower:
                print(f"[DIRECT] {domain} - Bypassing proxy")
                return False
        
        # Check if it's login traffic - use proxy
        for keyword in self.proxy_domains:
            if keyword in domain_lower:
                print(f"[PROXY] {domain} - Routing through proxy")
                return True
        
        # Default: direct
        return False
    
    def handle_client(self, client_socket):
        """Handle SOCKS5 client connection"""
        try:
            # SOCKS5 handshake
            version, nmethods = struct.unpack("!BB", client_socket.recv(2))
            methods = client_socket.recv(nmethods)
            
            # No authentication
            client_socket.sendall(struct.pack("!BB", 5, 0))
            
            # Get request
            version, cmd, _, address_type = struct.unpack("!BBBB", client_socket.recv(4))
            
            if address_type == 1:  # IPv4
                address = socket.inet_ntoa(client_socket.recv(4))
            elif address_type == 3:  # Domain name
                domain_length = client_socket.recv(1)[0]
                address = client_socket.recv(domain_length).decode()
            
            port = struct.unpack('!H', client_socket.recv(2))[0]
            
            # Decide routing
            if self.should_proxy(address):
                # Route through proxy with UID bypass
                self.handle_proxied_connection(client_socket, address, port)
            else:
                # Direct connection - no interception
                self.handle_direct_connection(client_socket, address, port)
                
        except Exception as e:
            print(f"[Error] SOCKS5 error: {e}")
        finally:
            client_socket.close()
    
    def handle_direct_connection(self, client_socket, address, port):
        """Direct connection - no modification"""
        try:
            # Connect directly to target
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.connect((address, port))
            
            # Send success
            reply = struct.pack("!BBBBIH", 5, 0, 0, 1, 0, 0)
            client_socket.sendall(reply)
            
            # Relay traffic without modification
            self.relay_traffic(client_socket, remote)
            
        except Exception as e:
            print(f"[Error] Direct connection failed: {e}")
    
    def handle_proxied_connection(self, client_socket, address, port):
        """Proxied connection - apply UID bypass"""
        try:
            # Connect to target
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.connect((address, port))
            
            # Send success
            reply = struct.pack("!BBBBIH", 5, 0, 0, 1, 0, 0)
            client_socket.sendall(reply)
            
            # Relay with modification capability
            self.relay_with_modification(client_socket, remote)
            
        except Exception as e:
            print(f"[Error] Proxied connection failed: {e}")
    
    def relay_traffic(self, client, remote):
        """Relay traffic without modification"""
        sockets = [client, remote]
        while True:
            readable, _, _ = select.select(sockets, [], [], 1)
            if not readable:
                continue
            
            for sock in readable:
                data = sock.recv(4096)
                if not data:
                    return
                
                if sock is client:
                    remote.sendall(data)
                else:
                    client.sendall(data)
    
    def relay_with_modification(self, client, remote):
        """Relay traffic with UID bypass capability"""
        # Similar to relay_traffic but can modify data
        # Add your UID bypass logic here
        self.relay_traffic(client, remote)
    
    def start(self):
        """Start SOCKS5 proxy server"""
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))
        self.server.listen(100)
        
        print(f"[SOCKS5] Proxy listening on {self.host}:{self.port}")
        print(f"[SOCKS5] Login traffic → Proxy (UID bypass)")
        print(f"[SOCKS5] Ranked traffic → Direct (No detection)")
        
        while True:
            client, addr = self.server.accept()
            print(f"[SOCKS5] Connection from {addr}")
            thread = threading.Thread(target=self.handle_client, args=(client,))
            thread.daemon = True
            thread.start()

if __name__ == "__main__":
    proxy = SOCKS5Proxy(port=1080)
    proxy.start()
