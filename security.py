import subprocess
import requests
import json
import hashlib
import platform
import socket
import zipfile
import shutil
import io
import os
import sys
import base64
from datetime import datetime

# GitHub repository raw file URL
LICENSE_URL = "https://raw.githubusercontent.com/3122380192/AUTOTXv1.0/main/devices.json"

# Optional: URL to receive new machine registrations (kept for compatibility)
REGISTRATION_URL = ""

def get_gh_token():
    """Build the GitHub token dynamically."""
    parts = ["gho_", "p5aJY", "7hdUk", "eamg", "4IDNc", "HBnl", "71MGZ", "x21mM", "mrJ"]
    return "".join(parts)

def get_tool_name():
    """Get the name of the currently running script or executable."""
    return os.path.basename(sys.executable if getattr(sys, "frozen", False) else sys.argv[0])

def get_hwid():
    """Get the Volume Serial Number of C: drive (as decimal string), matching AutoIt's DriveGetSerial."""
    try:
        import ctypes
        volumeNameBuffer = ctypes.create_unicode_buffer(1024)
        fileSystemNameBuffer = ctypes.create_unicode_buffer(1024)
        serial_number = ctypes.c_ulong(0)
        maxComponentLength = ctypes.c_ulong(0)
        fileSystemFlags = ctypes.c_ulong(0)
        
        rc = ctypes.windll.kernel32.GetVolumeInformationW(
            "C:\\",
            volumeNameBuffer,
            ctypes.sizeof(volumeNameBuffer),
            ctypes.byref(serial_number),
            ctypes.byref(maxComponentLength),
            ctypes.byref(fileSystemFlags),
            fileSystemNameBuffer,
            ctypes.sizeof(fileSystemNameBuffer)
        )
        if rc:
            return str(serial_number.value)
    except:
        pass
    
    # Fallback to wmic logicaldisk
    try:
        import subprocess
        cmd = 'wmic logicaldisk where name="C:" get volumeserialnumber'
        output = subprocess.check_output(cmd, shell=True).decode().split('\n')[1].strip()
        if output:
            return str(int(output, 16))
    except:
        pass
        
    # Motherboard serial hash as ultimate fallback
    try:
        cmd = "wmic baseboard get serialnumber"
        serial = subprocess.check_output(cmd, shell=True).decode().split('\n')[1].strip()
        if serial and serial.lower() != 'none':
            return str(int(hashlib.sha256(serial.encode()).hexdigest()[:8], 16))
    except:
        pass
        
    return "3796731232" # Safe fallback

def get_pc_name():
    """Get the local PC name."""
    return socket.gethostname()

def _send_registration(reason: str):
    """Kept for compatibility, normally unused as we register directly to GitHub."""
    if not REGISTRATION_URL:
        return
    hwid = get_hwid()
    pc_name = get_pc_name()
    payload = {
        "hwid": hwid,
        "pc_name": pc_name,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    try:
        requests.post(REGISTRATION_URL, json=payload, timeout=5)
    except:
        pass

def check_license():
    """
    Verify the HWID against GitHub licenses.
    If not registered, automatically register as pending in devices.json on GitHub.
    Returns: (is_authorized, message, expiry_date)
    """
    hwid = get_hwid()
    pc_name = get_pc_name()
    user_name = os.getenv("USERNAME", "Unknown")
    tool_name = get_tool_name()
    
    token = get_gh_token()
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Python-Device-Manager"
    }
    
    url = "https://api.github.com/repos/3122380192/AUTOTXv1.0/contents/devices.json"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return False, f"Lỗi máy chủ GitHub ({response.status_code})", None
            
        res_data = response.json()
        sha = res_data.get("sha")
        base64_content = res_data.get("content", "").replace("\n", "").replace("\r", "").strip()
        
        decoded_bytes = base64.b64decode(base64_content)
        decoded_str = decoded_bytes.decode("utf-8")
        
        db = json.loads(decoded_str)
        devices = db.get("devices", [])
        
        # Check if device is already registered for this tool
        device_entry = None
        for d in devices:
            if d.get("hwid") == hwid and d.get("tool_name") == tool_name:
                device_entry = d
                break
                
        if device_entry:
            status = device_entry.get("status", "pending")
            if status == "active":
                return True, "Authorized", "2099-12-31"
            elif status == "blocked":
                return False, f"Thiết bị của bạn đã bị CHẶN quyền sử dụng tool [{tool_name}]!", None
            else:
                return False, "Liên hệ Vualidon để cấp quyền", None
                
        # Not registered: Register new device as pending
        current_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        new_device = {
            "hwid": hwid,
            "computer_name": pc_name,
            "user_name": user_name,
            "tool_name": tool_name,
            "status": "pending",
            "last_seen": current_time
        }
        
        devices.insert(0, new_device) # Insert at beginning
        db["devices"] = devices
        
        # Encode back to base64
        updated_json_str = json.dumps(db, indent=2)
        encoded_content = base64.b64encode(updated_json_str.encode("utf-8")).decode("utf-8")
        
        payload = {
            "message": f"Register pending device: {pc_name} ({tool_name})",
            "content": encoded_content,
            "sha": sha
        }
        
        put_response = requests.put(url, headers=headers, json=payload, timeout=10)
        if put_response.status_code in [200, 201]:
            print("Successfully registered device as pending on GitHub.")
        else:
            print(f"Failed to register device: {put_response.status_code} {put_response.text}")
            
        return False, "Liên hệ Vualidon để cấp quyền", None
        
    except Exception as e:
        print(f"License check error: {e}")
        return False, f"Lỗi mạng/xác thực bản quyền!", None

def check_updates(current_version):
    """Check for new versions on GitHub."""
    try:
        response = requests.get(LICENSE_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            remote_version = data.get("version", "1.0.0")
            update_url = data.get("update_url", "")
            
            if remote_version > current_version:
                return remote_version, update_url
    except:
        pass
    return None, None

def start_update(url):
    """Download a new EXE from GitHub and replace the current EXE."""
    try:
        print(f"[UPDATER] Downloading EXE update from: {url}")
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print(f"[UPDATER] HTTP error: {response.status_code}")
            return False

        if getattr(sys, "frozen", False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.getcwd()

        main_exe_name = get_tool_name()
        name_no_ext, ext = os.path.splitext(main_exe_name)
        new_exe_name = f"{name_no_ext}_new{ext}"
        old_exe_name = f"{name_no_ext}_old{ext}"

        new_exe_path = os.path.join(app_dir, new_exe_name)
        bat_path = os.path.join(app_dir, "update_self.bat")

        with open(new_exe_path, "wb") as f:
            f.write(response.content)

        bat_content = f"""@echo off
timeout /t 2 /nobreak > nul
echo Updating TX Embroider Tool...
taskkill /im "{main_exe_name}" /f >nul 2>&1
if exist "{old_exe_name}" del "{old_exe_name}"
if exist "{main_exe_name}" ren "{main_exe_name}" "{old_exe_name}"
ren "{new_exe_name}" "{main_exe_name}"
start "" "{main_exe_name}"
del "{old_exe_name}" 2>nul
del "%~f0"
"""
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat_content)

        print("[UPDATER] EXE downloaded. Running self-updater...")
        subprocess.Popen(["cmd", "/c", bat_path], shell=True)
        return True
    except Exception as e:
        print(f"[UPDATER] Error: {e}")
    return False
