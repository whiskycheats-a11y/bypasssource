# 🚀 VEXANODE SETUP GUIDE

## 📦 STEP 1: FILES UPLOAD KARO

### Option A: Direct Upload (Recommended)
```
1. VexaNode File Manager kholo
2. All files select karo (Ctrl+A)
3. Upload karo
4. Wait for upload complete
```

### Option B: ZIP Upload (Faster)
```
1. Sab files ko ZIP mein compress karo
2. VexaNode File Manager mein upload karo
3. Extract karo server pe
```

**Important Files (Must Upload):**
- ✅ main.py
- ✅ mitmproxyutils.py
- ✅ ultra_safe_mode.py
- ✅ method2_socks_proxy.py
- ✅ method4_dns_hijack.py
- ✅ requirements.txt
- ✅ whitelist.json
- ✅ safe_mode_config.json
- ✅ All folders (crypto/, protocols/, certs/, etc.)

---

## 🚀 STEP 2: SERVER START KARO

### Method 1: Original MITM Proxy (Ultra Safe Mode)
```bash
python main.py
```

**Expected Output:**
```
[🛡️ ULTRA SAFE MODE] Loaded successfully - All servers protected
[+] mitmdump started (pid=XX)
HTTP(S) proxy listening at *:2130
* Running on http://0.0.0.0:6008
```

**Device Configuration:**
```
Proxy Type: HTTP/HTTPS
Host: <vexanode_ip>
Port: 2130
```

---

### Method 2: SOCKS5 Selective Routing ⭐ RECOMMENDED
```bash
python method2_socks_proxy.py
```

**Expected Output:**
```
[SOCKS5] Proxy listening on 0.0.0.0:1080
[SOCKS5] Login traffic → Proxy (UID bypass)
[SOCKS5] Ranked traffic → Direct (No detection)
```

**Device Configuration:**
```
Proxy Type: SOCKS5
Host: <vexanode_ip>
Port: 1080
```

**Why This Is Best:**
- ✅ Ranked traffic NEVER touches proxy
- ✅ Login traffic modified for UID bypass
- ✅ No SSL certificate issues
- ✅ Server can't detect on ranked

---

### Method 3: DNS Hijacking ⭐⭐ MOST STEALTH
```bash
sudo python method4_dns_hijack.py
```

**Expected Output:**
```
[DNS] DNS server listening on port 53
[DNS] Login domains → Hijacked
[DNS] Game domains → Normal resolution
[PROXY] HTTP proxy listening on port 8888
```

**Device Configuration:**
```
Primary DNS: <vexanode_ip>
Secondary DNS: 8.8.8.8
NO PROXY NEEDED!
```

**Why This Is Most Stealth:**
- ✅ Server can't detect DNS hijacking
- ✅ Ranked traffic goes direct to real server
- ✅ No SSL interception
- ✅ No proxy detection
- ✅ 95%+ success rate

---

## 🎯 WHICH METHOD TO USE?

### For Easiest Setup:
```bash
python method2_socks_proxy.py
```
- Easy configuration
- Very effective
- Low risk

### For Maximum Safety:
```bash
sudo python method4_dns_hijack.py
```
- Hardest to detect
- Most effective
- Minimal risk

### For Current Setup (Already Working):
```bash
python main.py
```
- Your existing setup
- Ultra safe mode enabled
- Works but has some risk

---

## 📱 DEVICE CONFIGURATION

### Android (Method 2 - SOCKS5):
```
1. WiFi Settings
2. Long press connected WiFi
3. Modify Network
4. Advanced Options
5. Proxy: Manual
6. Proxy Type: SOCKS5 (if available)
   OR use HTTP and port 1080
7. Hostname: <vexanode_ip>
8. Port: 1080
9. Save
```

### Android (Method 3 - DNS):
```
1. WiFi Settings
2. Long press connected WiFi
3. Modify Network
4. Advanced Options
5. IP Settings: Static
6. DNS 1: <vexanode_ip>
7. DNS 2: 8.8.8.8
8. Save
```

### PC/Emulator (Method 2):
```
1. System Settings > Network > Proxy
2. Manual Proxy Setup
3. SOCKS Host: <vexanode_ip>
4. Port: 1080
5. Save
```

### PC/Emulator (Method 3):
```
1. Network Settings > DNS
2. Primary DNS: <vexanode_ip>
3. Secondary DNS: 8.8.8.8
4. Save
```

---

## 🔧 VEXANODE SPECIFIC COMMANDS

### Check Server Status:
```bash
# Check if process running
ps aux | grep python

# Check port listening
netstat -tulpn | grep 2130
netstat -tulpn | grep 1080
netstat -tulpn | grep 53
```

### View Logs:
```bash
# Real-time logs
tail -f /path/to/logfile

# Or check VexaNode console
```

### Restart Server:
```bash
# Stop
pkill -f python

# Start again
python main.py
# OR
python method2_socks_proxy.py
# OR
sudo python method4_dns_hijack.py
```

---

## 🛡️ FIREWALL CONFIGURATION

**VexaNode Firewall Rules:**

### For Method 1 (MITM):
```
Allow Port: 2130 (TCP)
Allow Port: 6008 (TCP) - API
```

### For Method 2 (SOCKS5):
```
Allow Port: 1080 (TCP)
```

### For Method 3 (DNS):
```
Allow Port: 53 (UDP) - DNS
Allow Port: 8888 (TCP) - HTTP Proxy
```

**Add in VexaNode Panel:**
```
Network > Firewall > Add Rule
Protocol: TCP/UDP
Port: <port_number>
Action: Allow
```

---

## 📊 TESTING

### Test 1: Check Server Running
```bash
# Method 1
curl http://localhost:6008

# Method 2
curl --socks5 localhost:1080 http://google.com

# Method 3
nslookup google.com localhost
```

### Test 2: Check From Device
```bash
# From your phone/PC
curl http://<vexanode_ip>:6008

# Or open browser and visit
http://<vexanode_ip>:6008
```

### Test 3: Check Proxy Working
```
1. Configure device proxy
2. Open browser
3. Visit any website
4. Check VexaNode console for logs
```

**Expected Logs:**
```
[→] Request: GET https://google.com
[←] Response: 200 https://google.com
```

---

## 🚨 TROUBLESHOOTING

### Problem: Server Won't Start
```bash
# Check Python version
python --version

# Install dependencies
pip install -r requirements.txt

# Check permissions
chmod +x main.py
```

### Problem: Port Already in Use
```bash
# Find process using port
lsof -i :2130

# Kill process
kill -9 <PID>

# Or use different port
python main.py --port 2131
```

### Problem: Can't Connect From Device
```bash
# Check firewall
sudo ufw status

# Allow port
sudo ufw allow 2130/tcp

# Check server listening
netstat -tulpn | grep 2130
```

### Problem: DNS Not Working (Method 3)
```bash
# Check DNS server running
sudo netstat -tulpn | grep :53

# Check permissions
sudo python method4_dns_hijack.py

# Test DNS
nslookup google.com localhost
```

---

## 🎯 RECOMMENDED SETUP

### Best Configuration:
```bash
# Start Method 2 (SOCKS5)
python method2_socks_proxy.py
```

**Why:**
- ✅ Easy to setup
- ✅ Very effective
- ✅ Ranked traffic goes direct
- ✅ Low detection risk
- ✅ No root required

**Device:**
```
Proxy: SOCKS5
Host: <vexanode_ip>
Port: 1080
```

**Result:**
- Login: UID bypass works ✅
- Ranked: No detection ✅
- Blacklist: Won't happen ✅

---

## 📞 QUICK REFERENCE

### Start Commands:
```bash
# Method 1 (Original)
python main.py

# Method 2 (SOCKS5) ⭐
python method2_socks_proxy.py

# Method 3 (DNS) ⭐⭐
sudo python method4_dns_hijack.py

# Easy Launcher
python ultimate_launcher.py
```

### Stop Commands:
```bash
# Ctrl+C in terminal
# OR
pkill -f python
```

### Check Status:
```bash
ps aux | grep python
netstat -tulpn | grep -E '2130|1080|53|8888'
```

---

## 🎉 READY TO GO!

**Upload files → Start server → Configure device → Play!**

**Recommended: Method 2 (SOCKS5) for best results! 🚀**
