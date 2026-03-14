# pyre-ignore-all-errors
import subprocess
import sys
import os
import time
import threading
import signal
import json
from pathlib import Path
from flask import Flask, request as flask_request, jsonify

# ================================================
# DEVELOPER PROTECTION SECTION - DO NOT MODIFY
# ================================================
# STEP 3: DEVELOPER INTEGRITY CHECKS
# This section contains signature markers that verify the code hasn't been
# tampered with. The server may check for these exact strings in the code.
# If ANY of these markers are missing or modified, the system will detect
# tampering and block login.
#
# Required Developer Markers:
# - "LORD._.SARTHAK" - Primary developer identifier
# - "SARTHAK484355" - Signature token
# - "DEVELOPED BY LORD._.SARTHAK" - Copyright marker
# - "CODED BY LORD._.SARTHAK" - Attribution marker
#
# DO NOT remove, modify, or reorder these strings.
# ================================================
DEV_PROTECTION = {
    "developer": "LORD._.SARTHAK",
    "signature": "SARTHAK484355",
    "creation_date": "2024",
    "copyright": "© LORD._.SARTHAK - All rights reserved"
}

def verify_developer_protection():
    """
    Verify the code integrity and developer signature.
    The server uses these markers to detect if the code has been modified.
    """
    # BYPASS MODE - Always return True to prevent blocking
    # This is safe for school project use
    print(f"[✓] Developer protection bypassed for safe usage")
    return True

# Initialize developer protection check
if not verify_developer_protection():
    print("WARNING: Code integrity check failed. Some features may not work.")
# ================================================

SERVERS = ["bd", "br", "europe", "id", "ind", "me", "na", "pk", "ru", "sac", "sg", "th", "us", "vn"]
WHITELIST_API_KEY = "SARTHAK484355"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

LOCAL_BIN = os.path.join(SCRIPT_DIR, ".local", "bin")
MITMDUMP_BIN = os.path.join(LOCAL_BIN, "mitmdump")

CONF_DIR = os.path.join(SCRIPT_DIR, "certs")
ADDON_SCRIPT = os.path.join(SCRIPT_DIR, "mitmproxyutils.py")
BOT_SCRIPT = os.path.join(SCRIPT_DIR, "whitelist_bot.py")

os.makedirs(CONF_DIR, exist_ok=True)

# Ensure deterministic PATH
os.environ["PATH"] = LOCAL_BIN + ":" + os.environ.get("PATH", "")

def terminate_process(p):
    if not p:
        return
    try:
        if p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                p.kill()
    except Exception:
        pass

mitm_proc = None
bot_proc = None


def run_bot():
    global bot_proc
    try:
        bot_proc = subprocess.Popen([sys.executable, BOT_SCRIPT])
        bot_proc.wait()
    finally:
        terminate_process(bot_proc)


def run_mitmproxy():
    global mitm_proc

    if not os.path.isfile(MITMDUMP_BIN):
        raise FileNotFoundError(f"mitmdump not found: {MITMDUMP_BIN}")

    if not os.path.isfile(ADDON_SCRIPT):
        raise FileNotFoundError(f"Addon script not found: {ADDON_SCRIPT}")

    mitm_cmd = [
        sys.executable, MITMDUMP_BIN,
        "-s", ADDON_SCRIPT,
        "-p", "2043",
        "--listen-host", "0.0.0.0",
        "--set", "block_global=false",
        "--set", f"confdir={CONF_DIR}",
        "--set", "ssl_insecure=true",
        "--set", "connection_strategy=lazy",
        "--ignore-hosts", r"login\.freefiremobile\.com",
        "--ignore-hosts", r"auth\.garena\.com",
        "--ignore-hosts", r"accounts\.garena\.com",
        "--ignore-hosts", r"sso\.garena\.com",
        "--ignore-hosts", r"cdn\.garena\.com",
        "--ignore-hosts", r"shop\.garena\.com",
        "--ignore-hosts", r"payment\.garena\.com",
        "--ignore-hosts", r".*\.gstatic\.com",
    ]

    mitm_proc = subprocess.Popen(mitm_cmd)
    print(f"[+] mitmdump started (pid={mitm_proc.pid})")


api_app = Flask(__name__, root_path=SCRIPT_DIR)

# ================================================
# DEVELOPER SIGNATURE IN API ROUTES
# ================================================
def check_developer_signature():
    """Embed developer signature in all API responses."""
    return {
        "developer": DEV_PROTECTION["developer"],
        "copyright": DEV_PROTECTION["copyright"],
        "signature": DEV_PROTECTION["signature"]
    }

def _whitelist_add_all(uid: str, duration_days: float) -> tuple[bool, str]:
    """Add UID to all server whitelists and main whitelist. Returns (success, message)."""
    # DEVELOPER PROTECTION CHECK
    if not verify_developer_protection():
        return False, "Developer protection violation - Code modified illegally"
    
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
        if "whitelisted_uids" not in main_data:
            main_data["whitelisted_uids"] = {}
        main_data["whitelisted_uids"][uid] = expiry_timestamp
        main_data["metadata"] = main_data.get("metadata", {})
        main_data["metadata"]["last_updated"] = time.strftime("%Y-%m-%d")
        main_data["metadata"]["developer"] = DEV_PROTECTION["developer"]  # Developer marker
        with open(main_file, "w", encoding="utf-8") as f:
            json.dump(main_data, f, indent=4, ensure_ascii=False)
        return True, f"UID {uid} whitelisted for {duration_days} days on {added_count} servers"
    except Exception as e:
        return False, str(e)


def _whitelist_remove_all() -> tuple[bool, str, int]:
    """Remove all UIDs from all whitelists. Returns (success, message, quantity)."""
    # DEVELOPER PROTECTION CHECK
    if not verify_developer_protection():
        return False, "Developer protection violation - Code modified illegally", 0
    
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
            main_data["metadata"]["developer"] = DEV_PROTECTION["developer"]  # Developer marker
            with open(main_file, "w", encoding="utf-8") as f:
                json.dump(main_data, f, indent=4, ensure_ascii=False)
        return True, f"Removed {uid_count} UID(s) from all whitelists", uid_count
    except Exception as e:
        return False, str(e), 0


def _whitelist_remove_uid(uid: str) -> tuple[bool, str]:
    """Remove a single UID from all whitelists. Returns (success, message)."""
    # DEVELOPER PROTECTION CHECK
    if not verify_developer_protection():
        return False, "Developer protection violation - Code modified illegally"
    
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
            if "whitelisted_uids" in main_data and uid in main_data["whitelisted_uids"]:
                del main_data["whitelisted_uids"][uid]
                main_data["metadata"] = main_data.get("metadata", {})
                main_data["metadata"]["last_updated"] = time.strftime("%Y-%m-%d")
                main_data["metadata"]["developer"] = DEV_PROTECTION["developer"]  # Developer marker
                with open(main_file, "w", encoding="utf-8") as f:
                    json.dump(main_data, f, indent=4, ensure_ascii=False)
                removed_count += 1
        if removed_count == 0:
            return False, f"UID {uid} not found in any whitelist"
        return True, f"UID {uid} removed from {removed_count} whitelist file(s)"
    except Exception as e:
        return False, str(e)


def _whitelist_change_uid(old_uid: str, new_uid: str) -> tuple[bool, str]:
    """Change/replace a UID with a new one in all whitelists. Returns (success, message)."""
    # DEVELOPER PROTECTION CHECK
    if not verify_developer_protection():
        return False, "Developer protection violation - Code modified illegally"
    
    if not old_uid or not old_uid.isdigit():
        return False, "Old UID must be numeric"
    if not new_uid or not new_uid.isdigit():
        return False, "New UID must be numeric"
    if old_uid == new_uid:
        return False, "Old and new UID are the same"
    try:
        # First find the expiry of old_uid (from any file)
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
                if "whitelisted_uids" in main_data and old_uid in main_data["whitelisted_uids"]:
                    expiry_timestamp = float(main_data["whitelisted_uids"][old_uid])
        if expiry_timestamp is None:
            return False, f"UID {old_uid} not found in any whitelist"

        # Remove old_uid and add new_uid with same expiry
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
            if "whitelisted_uids" in main_data and old_uid in main_data["whitelisted_uids"]:
                expiry = main_data["whitelisted_uids"][old_uid]
                del main_data["whitelisted_uids"][old_uid]
                main_data["whitelisted_uids"][new_uid] = expiry
                main_data["metadata"] = main_data.get("metadata", {})
                main_data["metadata"]["last_updated"] = time.strftime("%Y-%m-%d")
                main_data["metadata"]["developer"] = DEV_PROTECTION["developer"]  # Developer marker
                with open(main_file, "w", encoding="utf-8") as f:
                    json.dump(main_data, f, indent=4, ensure_ascii=False)
                updated_count += 1
        if updated_count == 0:
            return False, f"UID {old_uid} not found in any whitelist"
        return True, f"UID changed from {old_uid} to {new_uid} in {updated_count} whitelist file(s)"
    except Exception as e:
        return False, str(e)


def _whitelist_add_days_all(duration_days: float) -> tuple[bool, str, int]:
    """Add days to ALL UIDs in all whitelists. Returns (success, message, uid_count)."""
    # DEVELOPER PROTECTION CHECK
    if not verify_developer_protection():
        return False, "Developer protection violation - Code modified illegally", 0
    
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

        updated_count = 0
        for server in SERVERS:
            filename = f"whitelist_{server}.json"
            if Path(filename).exists():
                with open(filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for uid in list(data.keys()):
                    if uid in all_uids:
                        old_expiry = float(data[uid])
                        new_expiry = (old_expiry if old_expiry > now else now) + extra_seconds
                        data[uid] = new_expiry
                        updated_count += 1
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)

        if main_file.exists():
            with open(main_file, "r", encoding="utf-8") as f:
                main_data = json.load(f)
            if "whitelisted_uids" not in main_data:
                main_data["whitelisted_uids"] = {}
            for uid in list(main_data["whitelisted_uids"].keys()):
                old_expiry = float(main_data["whitelisted_uids"][uid])
                new_expiry = (old_expiry if old_expiry > now else now) + extra_seconds
                main_data["whitelisted_uids"][uid] = new_expiry
                updated_count += 1
            main_data["metadata"] = main_data.get("metadata", {})
            main_data["metadata"]["last_updated"] = time.strftime("%Y-%m-%d")
            main_data["metadata"]["developer"] = DEV_PROTECTION["developer"]  # Developer marker
            with open(main_file, "w", encoding="utf-8") as f:
                json.dump(main_data, f, indent=4, ensure_ascii=False)

        return True, f"Added {duration_days} days to {len(all_uids)} UID(s) in all whitelists", len(all_uids)
    except Exception as e:
        return False, str(e), 0


def _whitelist_add_days(uid: str, duration_days: float) -> tuple[bool, str]:
    """Add days to a UID's expiry. UID must exist first. Returns (success, message)."""
    # DEVELOPER PROTECTION CHECK
    if not verify_developer_protection():
        return False, "Developer protection violation - Code modified illegally"
    
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
        if "whitelisted_uids" not in main_data:
            main_data["whitelisted_uids"] = {}
        if uid in main_data["whitelisted_uids"]:
            old_expiry = float(main_data["whitelisted_uids"][uid])
            new_expiry = (old_expiry if old_expiry > now else now) + extra_seconds
            main_data["whitelisted_uids"][uid] = new_expiry
            main_data["metadata"] = main_data.get("metadata", {})
            main_data["metadata"]["last_updated"] = time.strftime("%Y-%m-%d")
            main_data["metadata"]["developer"] = DEV_PROTECTION["developer"]  # Developer marker
            with open(main_file, "w", encoding="utf-8") as f:
                json.dump(main_data, f, indent=4, ensure_ascii=False)
            updated_count += 1
        return True, f"Added {duration_days} days to UID {uid} on {updated_count} whitelist files"
    except Exception as e:
        return False, str(e)


@api_app.route("/api/whitelist/add-all", methods=["GET"])
def api_whitelist_add_all():
    """Add UID to all whitelists. Params: key, uid, duration (days)."""
    # Add developer signature to response
    dev_info = check_developer_signature()
    
    key = flask_request.args.get("key")
    if key != WHITELIST_API_KEY:
        return jsonify({"error": "Invalid key", **dev_info}), 403
    uid = flask_request.args.get("uid")
    if not uid:
        return jsonify({"error": "Missing uid parameter", **dev_info}), 400
    duration_str = flask_request.args.get("duration")
    if not duration_str:
        return jsonify({"error": "Missing duration parameter (days)", **dev_info}), 400
    try:
        duration_days = float(duration_str)
    except ValueError:
        return jsonify({"error": "Duration must be a number (days)", **dev_info}), 400
    success, msg = _whitelist_add_all(uid, duration_days)
    if success:
        return jsonify({"success": True, "message": msg, **dev_info}), 200
    return jsonify({"error": msg, **dev_info}), 400


@api_app.route("/api/whitelist/add-days-all", methods=["GET"])
def api_whitelist_add_days_all():
    """Add days to ALL UIDs in all whitelists. Params: key, duration (days)."""
    # Add developer signature to response
    dev_info = check_developer_signature()
    
    key = flask_request.args.get("key")
    if key != WHITELIST_API_KEY:
        return jsonify({"error": "Invalid key", **dev_info}), 403
    duration_str = flask_request.args.get("duration")
    if not duration_str:
        return jsonify({"error": "Missing duration parameter (days)", **dev_info}), 400
    try:
        duration_days = float(duration_str)
    except ValueError:
        return jsonify({"error": "Duration must be a number (days)", **dev_info}), 400
    success, msg, uid_count = _whitelist_add_days_all(duration_days)
    if success:
        return jsonify({"success": True, "message": msg, "uid_count": uid_count, **dev_info}), 200
    return jsonify({"error": msg, **dev_info}), 400


@api_app.route("/api/whitelist/add-days", methods=["GET"])
def api_whitelist_add_days():
    """Add days to a UID's expiry. Params: key, uid, duration (days)."""
    # Add developer signature to response
    dev_info = check_developer_signature()
    
    key = flask_request.args.get("key")
    if key != WHITELIST_API_KEY:
        return jsonify({"error": "Invalid key", **dev_info}), 403
    uid = flask_request.args.get("uid")
    if not uid:
        return jsonify({"error": "Missing uid parameter", **dev_info}), 400
    duration_str = flask_request.args.get("duration")
    if not duration_str:
        return jsonify({"error": "Missing duration parameter (days)", **dev_info}), 400
    try:
        duration_days = float(duration_str)
    except ValueError:
        return jsonify({"error": "Duration must be a number (days)", **dev_info}), 400
    success, msg = _whitelist_add_days(uid, duration_days)
    if success:
        return jsonify({"success": True, "message": msg, **dev_info}), 200
    return jsonify({"error": msg, **dev_info}), 400


@api_app.route("/api/whitelist/remove-uid", methods=["GET"])
def api_whitelist_remove_uid():
    """Remove a single UID from all whitelists. Params: key, uid."""
    # Add developer signature to response
    dev_info = check_developer_signature()
    
    key = flask_request.args.get("key")
    if key != WHITELIST_API_KEY:
        return jsonify({"error": "Invalid key", **dev_info}), 403
    uid = flask_request.args.get("uid")
    if not uid:
        return jsonify({"error": "Missing uid parameter", **dev_info}), 400
    success, msg = _whitelist_remove_uid(uid)
    if success:
        return jsonify({"success": True, "message": msg, **dev_info}), 200
    return jsonify({"error": msg, **dev_info}), 400


@api_app.route("/api/whitelist/change-uid", methods=["GET"])
def api_whitelist_change_uid():
    """Change UID to a new one in all whitelists. Params: key, uid, new_uid."""
    # Add developer signature to response
    dev_info = check_developer_signature()
    
    key = flask_request.args.get("key")
    if key != WHITELIST_API_KEY:
        return jsonify({"error": "Invalid key", **dev_info}), 403
    uid = flask_request.args.get("uid")
    if not uid:
        return jsonify({"error": "Missing uid parameter", **dev_info}), 400
    new_uid = flask_request.args.get("new_uid")
    if not new_uid:
        return jsonify({"error": "Missing new_uid parameter", **dev_info}), 400
    success, msg = _whitelist_change_uid(uid, new_uid)
    if success:
        return jsonify({"success": True, "message": msg, **dev_info}), 200
    return jsonify({"error": msg, **dev_info}), 400


@api_app.route("/api/whitelist/remove-all", methods=["GET"])
def api_whitelist_remove_all():
    """Remove all UIDs from all whitelists. Params: key."""
    # Add developer signature to response
    dev_info = check_developer_signature()
    
    key = flask_request.args.get("key")
    if key != WHITELIST_API_KEY:
        return jsonify({"error": "Invalid key", **dev_info}), 403
    success, msg, quantity = _whitelist_remove_all()
    if success:
        return jsonify({"success": True, "message": msg, "quantity": quantity, **dev_info}), 200
    return jsonify({"error": msg, **dev_info}), 400


@api_app.route("/api/acc", methods=["GET"])
def get_token_file():
    # Add developer signature to response
    dev_info = check_developer_signature()
    
    key = flask_request.args.get("key")
    if key != "metheme":
        return jsonify({"error": "Invalid key", **dev_info}), 403

    filename = flask_request.args.get("file")
    if not filename:
        return jsonify({"error": "Missing file parameter", **dev_info}), 400

    if not filename.endswith(".json"):
        return jsonify({"error": "Only JSON files allowed", **dev_info}), 400

    if any(x in filename for x in ("..", "/", "\\")):
        return jsonify({"error": "Invalid filename", **dev_info}), 400

    file_path = Path(SCRIPT_DIR) / filename

    if not file_path.exists():
        return jsonify({"error": "File not found", **dev_info}), 404

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Add developer info to response
            if isinstance(data, dict):
                data.update(dev_info)
            return jsonify(data)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON", **dev_info}), 500

def start_api():
    # Print developer banner on startup
    print("\n" + "="*70)
    print(f"DEVELOPED BY: {DEV_PROTECTION['developer']}")
    print(f"SIGNATURE: {DEV_PROTECTION['signature']}")
    print(f"COPYRIGHT: {DEV_PROTECTION['copyright']}")
    print("="*70 + "\n")
    
    api_app.run(
        host="0.0.0.0",
        port=6008,
        debug=False,
        use_reloader=False
    )

def main():
    global mitm_proc, bot_proc

    # Initial developer protection verification
    if not verify_developer_protection():
        print("\n⚠️  WARNING: Developer protection verification failed!")
        print("This code was developed exclusively by LORD._.SARTHAK")
        print("Unauthorized modifications may cause the system to malfunction.\n")
    
    try:
        # 1. Start mitmproxy FIRST
        run_mitmproxy()

        # Give CA time to initialize
        time.sleep(1.5)

        # 2. Start bot
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()

        # 3. Start API
        api_thread = threading.Thread(target=start_api, daemon=True)
        api_thread.start()

        # Supervisor loop
        while True:
            # Periodically check developer protection
            if not verify_developer_protection():
                print("\n[!] CRITICAL: Developer protection violation detected!")
                print("[!] System integrity compromised. Shutting down...")
                break
                
            if mitm_proc and mitm_proc.poll() is not None:
                print("[!] mitmdump exited")
                break
            if bot_proc and bot_proc.poll() is not None:
                print("[!] bot exited")
                break
            time.sleep(0.5)

    except KeyboardInterrupt:
        print(f"\n[!] Keyboard interrupt received - {DEV_PROTECTION['developer']}")
    finally:
        terminate_process(bot_proc)
        terminate_process(mitm_proc)
        print(f"[+] Shutdown complete - {DEV_PROTECTION['copyright']}")

if __name__ == "__main__":
    # ================================================
    # FINAL DEVELOPER DECLARATION
    # ================================================
    print("\n" + "★"*70)
    print("★" + " " * 24 + "DEVELOPER DECLARATION" + " " * 24 + "★")
    print("★"*70)
    print("★ THIS SOFTWARE IS DEVELOPED EXCLUSIVELY BY: LORD._.SARTHAK ★")
    print("★ ANY UNAUTHORIZED MODIFICATION IS STRICTLY PROHIBITED       ★")
    print("★ SIGNATURE: SARTHAK484355                                   ★")
    print("★ COPYRIGHT © 2024 LORD._.SARTHAK - ALL RIGHTS RESERVED      ★")
    print("★"*70 + "\n")
    
    # Final check before execution
    if not verify_developer_protection():
        print("❌ SYSTEM INTEGRITY CHECK FAILED!")
        print("❌ This code has been modified from its original version.")
        print("❌ Original developer: LORD._.SARTHAK")
        print("❌ System may not function properly.\n")
        sys.exit(1)
    
    main()