"""
TRANSPARENT PROXY MODE - NEW METHOD
Instead of MITM, use transparent proxy with SSL passthrough
Server won't detect certificate changes
"""

from mitmproxy import http, ctx
from mitmproxy.proxy import mode_specs
import json
import time

# Domains to passthrough (don't intercept SSL)
PASSTHROUGH_DOMAINS = [
    # Free Fire game servers - Let SSL pass through
    "*.ff.garena.com",
    "*.freefire.com",
    "*.garena.com",
    "*.garenanow.com",
    # Anti-cheat domains
    "*anticheat*",
    "*security*",
    "*verify*"
]

# Only intercept these for UID bypass
INTERCEPT_DOMAINS = [
    "*login*",
    "*auth*",
    "*account*"
]

class TransparentProxy:
    """
    Transparent proxy that selectively intercepts traffic.
    Ranked match traffic passes through untouched.
    """
    
    def __init__(self):
        self.passthrough_mode = False
        self.intercepted_count = 0
        self.passthrough_count = 0
    
    def should_passthrough(self, host: str) -> bool:
        """Check if we should let SSL pass through"""
        host_lower = host.lower()
        
        # Check if it's a game server
        game_keywords = ["ff.garena", "freefire", "game", "match", "battle"]
        for keyword in game_keywords:
            if keyword in host_lower:
                return True
        
        # Check if it's anti-cheat
        anticheat_keywords = ["anticheat", "security", "verify", "check"]
        for keyword in anticheat_keywords:
            if keyword in host_lower:
                return True
        
        return False
    
    def should_intercept(self, host: str) -> bool:
        """Check if we should intercept for UID bypass"""
        host_lower = host.lower()
        
        # Only intercept login/auth
        intercept_keywords = ["login", "auth", "account"]
        for keyword in intercept_keywords:
            if keyword in host_lower:
                return True
        
        return False

    def tls_clienthello(self, data):
        """
        Called when client initiates TLS connection.
        Decide whether to intercept or passthrough.
        """
        try:
            server_name = data.context.server.address[0]
            
            if self.should_passthrough(server_name):
                # Let SSL pass through - don't intercept
                data.ignore_connection = True
                self.passthrough_count += 1
                print(f"[🔓 PASSTHROUGH] {server_name} - SSL not intercepted")
                return
            
            if self.should_intercept(server_name):
                # Intercept for UID bypass
                self.intercepted_count += 1
                print(f"[🔍 INTERCEPT] {server_name} - Checking for UID bypass")
                return
            
            # Default: passthrough
            data.ignore_connection = True
            self.passthrough_count += 1
            
        except Exception as e:
            print(f"[Error] TLS decision error: {e}")
            # On error, passthrough to be safe
            data.ignore_connection = True

    def request(self, flow: http.HTTPFlow):
        """Handle intercepted requests"""
        if flow.request.pretty_host:
            print(f"[→] Request: {flow.request.method} {flow.request.pretty_url}")
    
    def response(self, flow: http.HTTPFlow):
        """Handle intercepted responses - Only for login/auth"""
        if flow.request.pretty_host:
            print(f"[←] Response: {flow.response.status_code} {flow.request.pretty_url}")
            
            # Only modify login responses
            if "login" in flow.request.path.lower():
                print(f"[UID] Login response detected - Apply UID bypass here")
                # Your UID bypass logic here

addons = [TransparentProxy()]
