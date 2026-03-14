"""
ULTRA SAFE MODE - ALL SERVERS PROTECTION
Prevents blacklisting on ALL servers during ranked matches
Works for: IND, NA, EU, BR, SG, TH, VN, ME, RU, SAC, PK, BD, ID
Includes emulator protection for BlueStacks, MSI, MEmu, LD Player
"""

import time
import json
from pathlib import Path

# ================================================
# COMPREHENSIVE RANKED MATCH DETECTION
# ================================================

# All possible ranked match endpoints across all servers
RANKED_ENDPOINTS = [
    # Match Start/Entry
    "/MatchStart", "/EnterMatch", "/RankedMatchStart", "/BattleRoyaleStart",
    "/RankedGameStart", "/CSRankedMatch", "/EnterBattleRoyale", "/StartRankedGame",
    "/JoinRankedMatch", "/RankedLobby", "/EnterRanked", "/RankedEntry",
    
    # In-Match Updates (CRITICAL - Don't modify these!)
    "/PlayerEliminated", "/MatchUpdate", "/RankedMatchUpdate", "/BattleUpdate",
    "/PlayerKilled", "/EliminationUpdate", "/MatchStatus", "/GameUpdate",
    "/RankedStatus", "/BattleStatus", "/MatchProgress", "/GameProgress",
    
    # Match End
    "/MatchEnd", "/RankedMatchEnd", "/BattleEnd", "/GameEnd",
    "/MatchResult", "/RankedResult", "/BattleResult",
    
    # Rank/Rating Updates
    "/RankUpdate", "/RatingUpdate", "/TierUpdate", "/PointsUpdate",
    "/RankedPoints", "/RankChange", "/TierChange",
    
    # Anti-Cheat Related (NEVER MODIFY!)
    "/AntiCheat", "/SecurityCheck", "/IntegrityCheck", "/ValidationCheck",
    "/VerifyClient", "/ClientValidation", "/SecurityValidation",

    # Emulator/Device Detection (BLOCK these - they trigger 3-sec elimination)
    "/DeviceCheck", "/EmulatorCheck", "/EnvironmentCheck",
    "/PlatformValidation", "/DeviceIntegrity", "/HardwareCheck",
    "/SensorValidation", "/GPUValidation", "/DeviceReport",
    "/ClientEnvironment", "/DeviceFingerprint", "/VMDetection",
    "/SandboxCheck", "/PlayIntegrity", "/SafetyNet",
    "/DeviceAttestation", "/TrustCheck", "/RiskAssessment",
]

# Keywords that indicate ranked match activity
RANKED_KEYWORDS = [
    "ranked", "rank", "tier", "rating", "matchstart", "battleroyale",
    "entermatch", "rankedgame", "csranked", "playereliminated",
    "matchupdate", "elimination", "anticheat", "security", "integrity",
    "validation", "verify", "check",
]

# Keywords for emulator detection (block these silently)
EMULATOR_DETECTION_KEYWORDS = [
    "emulator", "emu_check", "vm_detect", "virtual", "sandbox",
    "device_fingerprint", "device_check", "hardware_check",
    "gpu_check", "sensor_report", "environment_check",
    "platform_check", "play_integrity", "safetynet",
    "attestation", "device_report", "build_info",
    "sys_info", "screen_info", "accelerometer",
    "gyroscope", "magnetometer",
]

# Safe endpoints - These can be modified without risk
SAFE_ENDPOINTS = [
    "/Login", "/MajorLogin", "/GetAccountInfo", "/GetProfile",
    "/GetInventory", "/GetItems", "/Shop", "/Store",
    "/Friends", "/Social", "/Chat", "/Lobby",
    "/GetAccountBriefInfoBeforeLogin"
]

class SafeModeManager:
    """Manages safe mode state and decisions"""
    
    def __init__(self):
        self.safe_mode_active = False
        self.last_ranked_detection = 0
        self.ranked_match_count = 0
        self.blocked_modifications = 0
        self.india_extra = {}
        self.load_config()
    
    def load_config(self):
        """Load safe mode configuration"""
        try:
            config_path = Path("safe_mode_config.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = {
                    "ultra_safe_mode": True,
                    "allow_login_modifications": True,
                    "allow_profile_modifications": False,
                    "block_all_ranked": True,
                    "log_detections": True
                }
                self.save_config()
            self.india_extra = self.config.get("india_server_extra", {})
            emu_prot = self.config.get("emulator_protection", {})
            if emu_prot.get("enabled", False):
                print("[🛡️ SAFE MODE] Emulator protection enabled from config")
                if emu_prot.get("block_emulator_detection_endpoints", False):
                    print("[🛡️ SAFE MODE] Emulator detection endpoint blocking active")
        except Exception as e:
            print(f"[Safe Mode] Error loading config: {e}")
            self.config = {"ultra_safe_mode": True}
    
    def save_config(self):
        """Save safe mode configuration"""
        try:
            with open("safe_mode_config.json", 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"[Safe Mode] Error saving config: {e}")
    
    def is_emulator_detection_request(self, path: str) -> bool:
        """
        Check if request is an emulator/device detection request.
        These trigger the 3-second elimination on BlueStacks/MSI.
        Returns True if this is a detection request that should be blocked.
        """
        path_lower = path.lower()

        for keyword in EMULATOR_DETECTION_KEYWORDS:
            if keyword in path_lower:
                self.log_detection(path, f"Emulator detection blocked: {keyword}")
                return True

        normalized = path_lower.replace("/", "").replace("-", "").replace("_", "")
        emu_normalized = [
            "devicecheck", "emulatorcheck", "environmentcheck",
            "hardwarecheck", "gpucheck", "sensorcheck",
            "platformcheck", "vmdetection", "sandboxcheck",
            "playintegrity", "safetynet", "deviceattestation",
            "trustcheck", "riskcheck", "devicereport",
            "devicefingerprint", "sensorvalidation", "gpuvalidation",
            "deviceintegrity", "clientenvironment", "riskassessment",
        ]
        for term in emu_normalized:
            if term in normalized:
                self.log_detection(path, f"Emulator detection (normalized) blocked: {term}")
                return True

        if self.india_extra:
            india_checks = []
            if self.india_extra.get("block_device_report", False):
                india_checks.append("devicereport")
            if self.india_extra.get("block_environment_check", False):
                india_checks.append("environmentcheck")
                india_checks.append("envcheck")
            if self.india_extra.get("block_emulator_fingerprint", False):
                india_checks.append("emulatorfingerprint")
                india_checks.append("emufingerprint")
            if self.india_extra.get("block_sensor_telemetry", False):
                india_checks.append("sensortelemetry")
                india_checks.append("sensorlog")
            if self.india_extra.get("block_gpu_check", False):
                india_checks.append("gpureport")
                india_checks.append("gpuinfo")
            if self.india_extra.get("block_play_integrity", False):
                india_checks.append("integritytoken")
                india_checks.append("integrityverdict")
            for term in india_checks:
                if term in normalized:
                    self.log_detection(path, f"India server extra block: {term}")
                    return True

        return False

    def is_ranked_match(self, path: str) -> bool:
        """
        Comprehensive check if request is ranked match related.
        Returns True if we should NOT modify this request.
        """
        path_lower = path.lower()
        
        # Check exact endpoint matches
        for endpoint in RANKED_ENDPOINTS:
            if endpoint.lower() in path_lower:
                self.log_detection(path, "Exact endpoint match")
                return True
        
        # Check keyword matches
        for keyword in RANKED_KEYWORDS:
            if keyword in path_lower:
                self.log_detection(path, f"Keyword match: {keyword}")
                return True
        
        return False
    
    def is_safe_to_modify(self, path: str) -> bool:
        """
        Check if it's safe to modify this request.
        Returns True only if explicitly safe.
        """
        # If ultra safe mode, only allow specific safe endpoints
        if self.config.get("ultra_safe_mode", True):
            path_lower = path.lower()
            
            # Check if it's in safe list
            for safe_endpoint in SAFE_ENDPOINTS:
                if safe_endpoint.lower() in path_lower:
                    # Additional check - make sure it's not also ranked
                    if not self.is_ranked_match(path):
                        return True
            
            # Not in safe list - block modification
            return False
        
        # Normal mode - allow if not ranked
        return not self.is_ranked_match(path)
    
    def log_detection(self, path: str, reason: str):
        """Log ranked match detection"""
        if self.config.get("log_detections", True):
            self.last_ranked_detection = time.time()
            self.ranked_match_count += 1
            print(f"\n{'='*60}")
            print(f"[🛡️ ULTRA SAFE MODE] RANKED MATCH DETECTED")
            print(f"{'='*60}")
            print(f"Path: {path}")
            print(f"Reason: {reason}")
            print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Total Detections: {self.ranked_match_count}")
            print(f"{'='*60}\n")
    
    def log_blocked_modification(self, path: str):
        """Log when a modification is blocked"""
        self.blocked_modifications += 1
        print(f"\n[🛡️ SAFE MODE] MODIFICATION BLOCKED")
        print(f"Path: {path}")
        print(f"Total Blocked: {self.blocked_modifications}")
        print(f"[🛡️ SAFE MODE] Request passed through unmodified\n")
    
    def get_stats(self) -> dict:
        """Get safe mode statistics"""
        return {
            "ranked_detections": self.ranked_match_count,
            "blocked_modifications": self.blocked_modifications,
            "last_detection": self.last_ranked_detection,
            "safe_mode_active": self.safe_mode_active
        }

# Global safe mode manager instance
safe_mode = SafeModeManager()

def should_modify_request(flow) -> bool:
    """
    Main function to check if request should be modified.
    Use this in mitmproxyutils.py response() function.
    
    Returns:
        True: Safe to modify
        False: DON'T modify (ranked match or unsafe)
    """
    path = flow.request.path
    
    # Check if it's safe to modify
    if not safe_mode.is_safe_to_modify(path):
        safe_mode.log_blocked_modification(path)
        return False
    
    return True

def should_block_emulator_detection(flow) -> bool:
    """
    Check if this request is an emulator detection request.
    These are the requests that trigger 3-second elimination on BlueStacks/MSI.
    
    Returns:
        True: This is an emulator detection request - BLOCK IT
        False: Normal request - let it through
    """
    path = flow.request.path
    return safe_mode.is_emulator_detection_request(path)

def is_login_request(path: str) -> bool:
    """Check if request is login-related (usually safe to modify)"""
    login_keywords = ["login", "majorlogin", "getaccountinfo"]
    path_lower = path.lower()
    
    for keyword in login_keywords:
        if keyword in path_lower:
            # Make sure it's not also ranked
            if not safe_mode.is_ranked_match(path):
                return True
    
    return False
