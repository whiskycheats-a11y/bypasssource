# pyre-ignore-all-errors
import random
import time
import re
import json
from typing import Dict, List, Optional
from pathlib import Path

try:
    from mitmproxy import http
except ImportError:
    http = None


EMULATOR_CONFIG_PATH = Path("emulator_config.json")


def load_emulator_config() -> dict:
    try:
        if EMULATOR_CONFIG_PATH.exists():
            with open(EMULATOR_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[EMU CONFIG] Error loading emulator config: {e}")
    return {}


BLUESTACKS_FINGERPRINTS = [
    {
        "user_agent": "Dalvik/2.1.0 (Linux; U; Android 13; SM-S918B Build/TP1A.220624.014)",
        "build_model": "SM-S918B",
        "build_brand": "samsung",
        "build_manufacturer": "samsung",
        "build_product": "dm3q",
        "build_device": "dm3q",
        "build_fingerprint": "samsung/dm3q/dm3q:13/TP1A.220624.014/S918BXXS3BWK1:user/release-keys",
        "build_hardware": "qcom",
        "build_board": "kalama",
        "android_version": "13",
        "sdk_version": "33",
        "screen_density": "420",
        "screen_resolution": "1080x2340",
        "gl_renderer": "Adreno (TM) 740",
        "gl_vendor": "Qualcomm",
    },
    {
        "user_agent": "Dalvik/2.1.0 (Linux; U; Android 14; Pixel 8 Pro Build/UD1A.230803.041)",
        "build_model": "Pixel 8 Pro",
        "build_brand": "google",
        "build_manufacturer": "Google",
        "build_product": "husky",
        "build_device": "husky",
        "build_fingerprint": "google/husky/husky:14/UD1A.230803.041/10808477:user/release-keys",
        "build_hardware": "tensor",
        "build_board": "zuma",
        "android_version": "14",
        "sdk_version": "34",
        "screen_density": "420",
        "screen_resolution": "1344x2992",
        "gl_renderer": "Mali-G715 Immortalis MC10",
        "gl_vendor": "ARM",
    },
]

MSI_FINGERPRINTS = [
    {
        "user_agent": "Dalvik/2.1.0 (Linux; U; Android 13; Redmi Note 12 Pro Build/TKQ1.220829.002)",
        "build_model": "23021RAAEG",
        "build_brand": "Redmi",
        "build_manufacturer": "Xiaomi",
        "build_product": "ruby",
        "build_device": "ruby",
        "build_fingerprint": "Redmi/ruby_global/ruby:13/TKQ1.220829.002/V14.0.6.0.TMOMIXM:user/release-keys",
        "build_hardware": "mt6781",
        "build_board": "mt6781",
        "android_version": "13",
        "sdk_version": "33",
        "screen_density": "440",
        "screen_resolution": "1080x2400",
        "gl_renderer": "Mali-G76 MC4",
        "gl_vendor": "ARM",
    },
    {
        "user_agent": "Dalvik/2.1.0 (Linux; U; Android 13; V2250 Build/TP1A.220624.014)",
        "build_model": "V2250",
        "build_brand": "vivo",
        "build_manufacturer": "vivo",
        "build_product": "PD2250F_EX",
        "build_device": "PD2250F_EX",
        "build_fingerprint": "vivo/PD2250F_EX/PD2250F_EX:13/TP1A.220624.014/V2250_13.1.12.8:user/release-keys",
        "build_hardware": "qcom",
        "build_board": "taro",
        "android_version": "13",
        "sdk_version": "33",
        "screen_density": "440",
        "screen_resolution": "1080x2400",
        "gl_renderer": "Adreno (TM) 730",
        "gl_vendor": "Qualcomm",
    },
]

MEMU_FINGERPRINTS = [
    {
        "user_agent": "Dalvik/2.1.0 (Linux; U; Android 12; SM-A536B Build/SP1A.210812.016)",
        "build_model": "SM-A536B",
        "build_brand": "samsung",
        "build_manufacturer": "samsung",
        "build_product": "a53xnsxx",
        "build_device": "a53x",
        "build_fingerprint": "samsung/a53xnsxx/a53x:12/SP1A.210812.016/A536BXXU5CWK3:user/release-keys",
        "build_hardware": "exynos",
        "build_board": "s5e8825",
        "android_version": "12",
        "sdk_version": "31",
        "screen_density": "400",
        "screen_resolution": "1080x2400",
        "gl_renderer": "Mali-G68 MC4",
        "gl_vendor": "ARM",
    },
]

LDPLAYER_FINGERPRINTS = [
    {
        "user_agent": "Dalvik/2.1.0 (Linux; U; Android 13; RMX3630 Build/TP1A.220905.001)",
        "build_model": "RMX3630",
        "build_brand": "realme",
        "build_manufacturer": "realme",
        "build_product": "RMX3630",
        "build_device": "RE58B2L1",
        "build_fingerprint": "realme/RMX3630/RE58B2L1:13/TP1A.220905.001/R.16e5890_1:user/release-keys",
        "build_hardware": "mt6789",
        "build_board": "mt6789",
        "android_version": "13",
        "sdk_version": "33",
        "screen_density": "400",
        "screen_resolution": "1080x2400",
        "gl_renderer": "Mali-G57 MC2",
        "gl_vendor": "ARM",
    },
]

EMULATOR_POOL_MAP = {
    "bluestacks": BLUESTACKS_FINGERPRINTS,
    "msi": MSI_FINGERPRINTS,
    "msi_app": MSI_FINGERPRINTS,
    "memu": MEMU_FINGERPRINTS,
    "ldplayer": LDPLAYER_FINGERPRINTS,
    "ld": LDPLAYER_FINGERPRINTS,
    "nox": BLUESTACKS_FINGERPRINTS,
    "gameloop": MSI_FINGERPRINTS,
    "tencent": MSI_FINGERPRINTS,
}

ALL_FINGERPRINTS = BLUESTACKS_FINGERPRINTS + MSI_FINGERPRINTS + MEMU_FINGERPRINTS + LDPLAYER_FINGERPRINTS


class AdvancedAntiCheat:
    def __init__(self):
        self.emu_config = load_emulator_config()

        self.emulator_header_patterns = [
            re.compile(r"^x-bs-", re.IGNORECASE),
            re.compile(r"^x-bluestacks", re.IGNORECASE),
            re.compile(r"^x-bst-", re.IGNORECASE),
            re.compile(r"^x-msi-", re.IGNORECASE),
            re.compile(r"^x-memu-", re.IGNORECASE),
            re.compile(r"^x-nox-", re.IGNORECASE),
            re.compile(r"^x-ld-", re.IGNORECASE),
            re.compile(r"^x-ldplayer", re.IGNORECASE),
            re.compile(r"^x-emulator", re.IGNORECASE),
            re.compile(r"^x-vm-", re.IGNORECASE),
            re.compile(r"^x-vbox-", re.IGNORECASE),
            re.compile(r"^x-android-emu", re.IGNORECASE),
        ]

        self.emulator_ua_keywords = [
            "bluestacks", "bst-", "bstk", "nox", "memu",
            "ldplayer", "ldmutiplayer", "tiantian", "msi app player",
            "msi_app", "gameloop", "tencent", "windroye", "droid4x",
            "andy", "genymotion", "virtualbox", "vbox",
            "x86", "x86_64", "sdk_gphone", "google_sdk",
            "goldfish", "ranchu", "generic_x86",
        ]

        self.emulator_body_keywords = [
            b"bluestacks", b"bst-", b"nox", b"memu",
            b"ldplayer", b"msi_app", b"gameloop",
            b"vbox86p", b"goldfish", b"ranchu",
            b"generic_x86", b"sdk_gphone",
            b"x86_64", b"android sdk",
            b"ttVM_Hdragon", b"generic/vbox",
            b"google_sdk/google_sdk",
        ]

        self.suspicious_headers = [
            'x-forwarded-for', 'x-real-ip', 'via', 'forwarded',
            'proxy-connection', 'x-proxy-id', 'client-ip',
            'true-client-ip', 'cf-connecting-ip', 'x-cluster-client-ip',
            'x-ssl-cipher', 'x-ssl-cert',
            'x-unity-version',
        ]

        self.build_fingerprint_keys = [
            'x-build-fingerprint', 'x-device-fingerprint',
            'x-android-fingerprint', 'build-fingerprint',
            'device-fingerprint', 'x-build-fp',
            'x-ro-build-fingerprint', 'x-system-fingerprint',
        ]

        self.build_prop_keys = {
            'x-build-model': 'build_model',
            'x-build-brand': 'build_brand',
            'x-build-manufacturer': 'build_manufacturer',
            'x-build-product': 'build_product',
            'x-build-device': 'build_device',
            'x-build-hardware': 'build_hardware',
            'x-build-board': 'build_board',
            'x-android-version': 'android_version',
            'x-sdk-version': 'sdk_version',
            'x-gl-renderer': 'gl_renderer',
            'x-gl-vendor': 'gl_vendor',
            'x-screen-density': 'screen_density',
        }

        self.emulator_fingerprint_markers = [
            b"generic/vbox86p/vbox86p",
            b"google/sdk_gphone",
            b"generic_x86",
            b"generic/sdk_gphone64",
            b"Android/sdk_gphone64",
            b"vbox86p",
            b"goldfish",
            b"ranchu",
            b"BlueStacks",
            b"bst-",
            b"HD-Player",
            b"MSI App Player",
            b"nox",
            b"MEmu",
            b"LDPlayer",
            b"ttVM_Hdragon",
            b"unknown/generic_x86",
        ]

        self._detected_emulator = None
        self._active_fingerprint = random.choice(ALL_FINGERPRINTS)
        self._fingerprint_rotate_time = time.time()
        self._fingerprint_rotate_interval = 300
        self._ssl_error_counts = {}
        self._ssl_max_retries = self.emu_config.get("ssl_config", {}).get("max_ssl_retries", 3)
        self._dynamic_passthrough_hosts = set()

        emu_block_cfg = self.emu_config.get("detection_endpoints_block", {})
        if emu_block_cfg.get("enabled", False):
            extra_patterns = emu_block_cfg.get("patterns", [])
            for pat in extra_patterns:
                compiled = re.compile(r"^x-" + re.escape(pat), re.IGNORECASE)
                self.emulator_header_patterns.append(compiled)

        self._ssl_config = self.emu_config.get("ssl_config", {})

    def _detect_emulator_type(self, ua: str) -> Optional[str]:
        ua_lower = ua.lower()
        if "bluestacks" in ua_lower or "bst-" in ua_lower or "bstk" in ua_lower:
            return "bluestacks"
        if "msi app player" in ua_lower or "msi_app" in ua_lower:
            return "msi"
        if "memu" in ua_lower:
            return "memu"
        if "ldplayer" in ua_lower or "ldmutiplayer" in ua_lower:
            return "ldplayer"
        if "nox" in ua_lower:
            return "nox"
        if "gameloop" in ua_lower or "tencent" in ua_lower:
            return "gameloop"
        if any(kw in ua_lower for kw in ["vbox", "virtualbox", "goldfish", "ranchu", "sdk_gphone", "generic_x86", "x86_64", "google_sdk"]):
            return "bluestacks"
        return None

    def _get_fingerprint_for_emulator(self, emu_type: Optional[str]) -> dict:
        if emu_type and emu_type in EMULATOR_POOL_MAP:
            pool = EMULATOR_POOL_MAP[emu_type]
        else:
            pool = ALL_FINGERPRINTS
        return random.choice(pool)

    def _get_active_fingerprint(self) -> dict:
        now = time.time()
        if now - self._fingerprint_rotate_time > self._fingerprint_rotate_interval:
            self._active_fingerprint = self._get_fingerprint_for_emulator(self._detected_emulator)
            self._fingerprint_rotate_time = now
            print(f"[EMU SHIELD] Fingerprint rotated to {self._active_fingerprint['build_model']}")
        return self._active_fingerprint

    def add_network_jitter(self):
        base_delay = random.uniform(0.01, 0.05)
        spike_chance = random.random()

        if spike_chance > 0.95:
            delay = random.uniform(0.1, 0.3)
        elif spike_chance > 0.8:
            delay = random.uniform(0.05, 0.1)
        else:
            delay = base_delay

        time.sleep(delay)

    def block_heuristic_telemetry(self, path: str, host: str) -> bool:
        ml_telemetry_patterns = [
            r'log/crash', r'ml_metrics', r'device_fingerprint',
            r'environment_check', r'root_status', r'emulator_detect',
            r'sensor_data', r'battery_stats', r'app_list', r'anomaly_scan',
            r'ml/telemetry',
            r'device/check', r'device/verify', r'device_info',
            r'client_env', r'env_report', r'platform_check',
            r'hw_info', r'hardware_check', r'gpu_check',
            r'vm_detect', r'virtual_check', r'sandbox_check',
            r'emu_check', r'emulator_report', r'emu_verify',
            r'integrity_check', r'safetynet', r'play_integrity',
            r'attestation', r'device_attestation',
            r'fingerprint_report', r'device_fp',
            r'anti_fraud', r'risk_check', r'trust_check',
            r'client_report', r'client_telemetry',
            r'sys_info', r'system_report',
            r'build_info', r'build_report',
            r'screen_info', r'display_check',
            r'sensor_report', r'accelerometer',
            r'gyroscope', r'magnetometer',
        ]

        emu_block_cfg = self.emu_config.get("detection_endpoints_block", {})
        if emu_block_cfg.get("enabled", False):
            for pat in emu_block_cfg.get("patterns", []):
                if pat not in ml_telemetry_patterns:
                    ml_telemetry_patterns.append(pat)

        url = f"{host}{path}".lower()
        for pattern in ml_telemetry_patterns:
            if re.search(pattern, url):
                print(f"[EMU SHIELD] Blocked detection endpoint: {pattern} on {url}")
                return True
        return False

    def _is_emulator_user_agent(self, ua: str) -> bool:
        ua_lower = ua.lower()
        for keyword in self.emulator_ua_keywords:
            if keyword in ua_lower:
                return True
        return False

    def _strip_emulator_headers(self, flow) -> int:
        removed = 0
        for key in list(flow.request.headers.keys()):
            key_lower = key.lower()
            if key_lower in self.suspicious_headers:
                del flow.request.headers[key]
                removed += 1
                continue
            for pattern in self.emulator_header_patterns:
                if pattern.match(key):
                    del flow.request.headers[key]
                    removed += 1
                    break
        return removed

    def _spoof_user_agent(self, flow) -> bool:
        ua = flow.request.headers.get("User-Agent", "")
        emu_type = self._detect_emulator_type(ua)
        if emu_type:
            self._detected_emulator = emu_type
            fp = self._get_fingerprint_for_emulator(emu_type)
            self._active_fingerprint = fp
            self._fingerprint_rotate_time = time.time()
            flow.request.headers["User-Agent"] = fp["user_agent"]
            print(f"[EMU SHIELD] Detected {emu_type} -> Spoofed to {fp['build_model']}")
            return True
        if "Dalvik" in ua:
            fp = self._get_active_fingerprint()
            flow.request.headers["User-Agent"] = fp["user_agent"]
            return True
        return False

    def _scrub_request_body(self, flow) -> bool:
        if not flow.request.content:
            return False

        content = flow.request.content
        modified = False
        fp = self._get_active_fingerprint()

        content, fp_modified = self._replace_fingerprint_in_body(content, fp)
        if fp_modified:
            modified = True
            print(f"[EMU SHIELD] Replaced Build.FINGERPRINT markers in request body")

        for keyword in self.emulator_body_keywords:
            if keyword in content:
                replacement = fp["build_model"].encode()
                try:
                    content = content.replace(keyword, replacement)
                    modified = True
                except Exception:
                    pass

        if modified:
            flow.request.content = content
            print(f"[EMU SHIELD] Scrubbed emulator markers from request body")

        return modified

    def _replace_build_fingerprint_headers(self, flow) -> int:
        fp = self._get_active_fingerprint()
        replaced = 0

        for key in self.build_fingerprint_keys:
            for hdr in list(flow.request.headers.keys()):
                if hdr.lower() == key:
                    flow.request.headers[hdr] = fp["build_fingerprint"]
                    replaced += 1

        for hdr_key, fp_field in self.build_prop_keys.items():
            for hdr in list(flow.request.headers.keys()):
                if hdr.lower() == hdr_key:
                    flow.request.headers[hdr] = fp.get(fp_field, "")
                    replaced += 1

        if replaced > 0:
            print(f"[EMU SHIELD] Replaced {replaced} Build.FINGERPRINT headers with {fp['build_model']}")
        return replaced

    def _replace_fingerprint_in_body(self, content: bytes, fp: dict) -> tuple:
        modified = False
        spoofed_fp = fp["build_fingerprint"].encode()

        for marker in self.emulator_fingerprint_markers:
            if marker in content:
                content = content.replace(marker, spoofed_fp)
                modified = True

        return content, modified

    def _inject_device_headers(self, flow):
        fp = self._get_active_fingerprint()
        header_map = {
            "X-Device-Model": fp["build_model"],
            "X-Device-Brand": fp["build_brand"],
            "X-Device-Manufacturer": fp["build_manufacturer"],
            "X-Android-Version": fp["android_version"],
            "X-SDK-Version": fp["sdk_version"],
            "X-Screen-Density": fp["screen_density"],
            "X-GL-Renderer": fp["gl_renderer"],
            "X-GL-Vendor": fp["gl_vendor"],
        }
        for hdr, val in header_map.items():
            if hdr in flow.request.headers:
                flow.request.headers[hdr] = val

    def should_ssl_passthrough(self, host: str) -> bool:
        host_lower = host.lower()

        if host_lower in self._dynamic_passthrough_hosts:
            return True

        if self._ssl_config.get("ssl_error_passthrough", True):
            passthrough_hosts = [
                "play.googleapis.com",
                "android.googleapis.com",
                "safebrowsing.googleapis.com",
                "play.google.com",
            ]
            for ph in passthrough_hosts:
                if ph in host_lower:
                    return True
        return False

    def process_request(self, flow) -> bool:
        host = flow.request.pretty_host
        path = flow.request.path

        if self.block_heuristic_telemetry(path, host):
            return False

        if "login" not in path.lower():
            self.add_network_jitter()

        removed = self._strip_emulator_headers(flow)
        if removed > 0:
            print(f"[EMU SHIELD] Stripped {removed} emulator/proxy headers")

        spoofed = self._spoof_user_agent(flow)
        if spoofed:
            fp = self._get_active_fingerprint()
            print(f"[EMU SHIELD] UA spoofed to {fp['build_model']}")

        self._replace_build_fingerprint_headers(flow)

        self._inject_device_headers(flow)

        self._scrub_request_body(flow)

        return True

    def handle_ssl_error(self, host: str, error_msg: str) -> str:
        count = self._ssl_error_counts.get(host, 0) + 1
        self._ssl_error_counts[host] = count

        if count <= self._ssl_max_retries:
            print(f"[EMU SSL] SSL error #{count} for {host}: {error_msg} — will retry")
            return "retry"

        self._dynamic_passthrough_hosts.add(host.lower())
        print(f"[EMU SSL] SSL errors exceeded for {host} ({count}) — added to dynamic passthrough")
        return "passthrough"

    def reset_ssl_errors(self, host: str):
        self._ssl_error_counts.pop(host, None)

    def process_response(self, flow) -> None:
        if not flow.response or not flow.response.content:
            return

        content = flow.response.content
        fp = self._get_active_fingerprint()
        modified = False

        content, fp_modified = self._replace_fingerprint_in_body(content, fp)
        if fp_modified:
            modified = True

        for keyword in self.emulator_body_keywords:
            if keyword in content:
                replacement = fp["build_model"].encode()
                try:
                    content = content.replace(keyword, replacement)
                    modified = True
                except Exception:
                    pass

        if modified:
            flow.response.content = content
            print(f"[EMU SHIELD] Scrubbed emulator markers from response body")

        host = flow.request.pretty_host
        if host in self._ssl_error_counts:
            self.reset_ssl_errors(host)


advanced_ac = AdvancedAntiCheat()
