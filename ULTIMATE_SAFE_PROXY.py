"""
ULTIMATE SAFE PROXY - ALL IN ONE, PORT 2130
Best of all methods combined, single port, maximum safety
"""

from mitmproxy import http
import json
import time
from pathlib import Path

class UltimateSafeProxy:
    """
    Ultimate safe proxy - All methods combined
    Port 2130, maximum safety, intelligent routing
    """
    
    def __init__(self):
        self.stats = {
            'login_requests': 0,
            'ranked_requests': 0,
            'blocked_modifications': 0,
            'uid_bypasses': 0
        }
        
        print("\n" + "="*70)
        print("🚀 ULTIMATE SAFE PROXY - PORT 2130")
        print("="*70)
        print("✅ Single Port: 2130 (Everything on one port!)")
        print("✅ Login Traffic: UID Bypass enabled")
        print("✅ Ranked Traffic: Zero modifications (100% safe)")
        print("✅ Ultra Safe Mode: Active")
        print("="*70 + "\n")
    
    def is_login_request(self, flow: http.HTTPFlow) -> bool:
        """Check if request is login-related"""
        path = flow.request.path.lower()
        host = flow.request.pretty_host.lower()
        
        login_keywords = ['login', 'auth', 'signin', 'account', 'majorlogin']
        
        for keyword in login_keywords:
            if keyword in path or keyword in host:
                return True
        
        return False
    
    def is_ranked_request(self, flow: http.HTTPFlow) -> bool:
        """Check if request is ranked match"""
        path = flow.request.path.lower()
        host = flow.request.pretty_host.lower()
        
        ranked_keywords = [
            'match', 'ranked', 'battle', 'game',
            'elimination', 'anticheat', 'security', 'verify'
        ]
        
        for keyword in ranked_keywords:
            if keyword in path or keyword in host:
                return True
        
        return False
    
    def request(self, flow: http.HTTPFlow):
        """Handle incoming requests"""
        # Check if ranked traffic
        if self.is_ranked_request(flow):
            self.stats['ranked_requests'] += 1
            print(f"[🛡️ RANKED] {flow.request.method} {flow.request.pretty_url}")
            print(f"[🛡️ SAFE] No modifications - Passing through clean")
            return
        
        # Check if login traffic
        if self.is_login_request(flow):
            self.stats['login_requests'] += 1
            print(f"[✓ LOGIN] {flow.request.method} {flow.request.pretty_url}")
    
    def response(self, flow: http.HTTPFlow):
        """Handle responses"""
        
        # CRITICAL: Check if ranked traffic - DON'T MODIFY
        if self.is_ranked_request(flow):
            self.stats['blocked_modifications'] += 1
            return  # Exit immediately
        
        # Check if login response - Apply UID bypass
        if self.is_login_request(flow) and "/MajorLogin" in flow.request.path:
            print(f"[UID] Login response detected - Checking UID")
            
            try:
                # Import existing functions
                from mitmproxyutils import checkUIDExists, add_uid_to_main_whitelist
                from protocols.protobuf_utils import get_available_room
                
                resp_bytes = flow.response.content
                resp_hex = resp_bytes.hex()
                
                try:
                    proto_json = get_available_room(resp_hex)
                    proto_fields = json.loads(proto_json)
                    
                    # Extract UID
                    uid_from_response = None
                    for field_num in ["1", "2", "3"]:
                        if field_num in proto_fields and isinstance(proto_fields[field_num], dict):
                            if "data" in proto_fields[field_num]:
                                potential_uid = str(proto_fields[field_num]["data"])
                                if potential_uid.isdigit() and len(potential_uid) > 5:
                                    uid_from_response = potential_uid
                                    break
                    
                    if uid_from_response:
                        print(f"[UID] Extracted: {uid_from_response}")
                        
                        # Check whitelist
                        if checkUIDExists(uid_from_response):
                            print(f"[✓ AUTHORIZED] UID {uid_from_response} is whitelisted")
                            add_uid_to_main_whitelist(uid_from_response)
                            self.stats['uid_bypasses'] += 1
                        else:
                            print(f"[❌ BLOCKED] UID {uid_from_response} not whitelisted")
                            # Block with message
                            block_msg = (
                                f"[FF0000]UID NOT AUTHORIZED\n"
                                f"[FFFFFF]UID: {uid_from_response}\n"
                                f"[FFFF00]Contact admin to whitelist"
                            ).encode()
                            flow.response.content = block_msg
                            flow.response.status_code = 403
                
                except Exception as e:
                    print(f"[Error] UID extraction failed: {e}")
            
            except Exception as e:
                print(f"[Error] UID bypass error: {e}")
    
    def print_stats(self):
        """Print statistics"""
        print(f"\n{'='*70}")
        print(f"📊 ULTIMATE SAFE PROXY - Statistics")
        print(f"{'='*70}")
        print(f"Login Requests: {self.stats['login_requests']}")
        print(f"Ranked Requests: {self.stats['ranked_requests']}")
        print(f"Blocked Modifications: {self.stats['blocked_modifications']}")
        print(f"UID Bypasses: {self.stats['uid_bypasses']}")
        print(f"{'='*70}\n")

# Create global instance
ultimate_proxy = UltimateSafeProxy()

# Mitmproxy addon
addons = [ultimate_proxy]

# Periodic stats printing
def print_stats_periodically():
    """Print stats every 60 seconds"""
    import threading
    def _print():
        while True:
            time.sleep(60)
            ultimate_proxy.print_stats()
    
    thread = threading.Thread(target=_print, daemon=True)
    thread.start()

print_stats_periodically()
