"""
SAFE MODE FOR RANKED MATCHES - INDIAN SERVER
This prevents modifications during ranked matches to avoid blacklisting
"""

# Add these endpoints that should NOT be modified
RANKED_MATCH_ENDPOINTS = [
    "/MatchStart",
    "/EnterMatch",
    "/RankedMatchStart", 
    "/BattleRoyaleStart",
    "/RankedGameStart",
    "/CSRankedMatch",
    "/EnterBattleRoyale"
]

# Endpoints that indicate you're IN a ranked match
IN_MATCH_ENDPOINTS = [
    "/PlayerEliminated",
    "/MatchUpdate",
    "/RankedMatchUpdate",
    "/BattleUpdate"
]

def is_ranked_match_request(path: str) -> bool:
    """
    Check if the request is related to ranked matches.
    Returns True if we should NOT modify this request.
    """
    path_lower = path.lower()
    
    # Check for ranked match keywords
    ranked_keywords = ["ranked", "matchstart", "battleroyale", "entermatch"]
    
    for keyword in ranked_keywords:
        if keyword in path_lower:
            return True
    
    # Check specific endpoints
    for endpoint in RANKED_MATCH_ENDPOINTS + IN_MATCH_ENDPOINTS:
        if endpoint.lower() in path_lower:
            return True
    
    return False

def should_allow_modification(flow) -> bool:
    """
    Determine if we should modify this request/response.
    Returns False for ranked matches (safe mode).
    """
    path = flow.request.path
    
    # SAFE MODE: Don't modify ranked matches
    if is_ranked_match_request(path):
        print(f"[SAFE MODE] Ranked match detected: {path}")
        print(f"[SAFE MODE] NO MODIFICATIONS - Preventing blacklist")
        return False
    
    # Allow modifications for other requests
    return True

# Example usage in mitmproxyutils.py:
"""
from safe_mode_ranked import should_allow_modification

def response(flow: http.HTTPFlow) -> None:
    # CHECK FIRST - Don't modify ranked matches
    if not should_allow_modification(flow):
        return  # Exit immediately, no modifications
    
    # Your existing code for other modifications...
"""
