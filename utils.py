import ctypes
import json
import logging
import traceback
import socket
import psutil
import winreg
from win32com.client import Dispatch
import netifaces
from vladhog_filetype import VDF

# Get local IP
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
local_ip = s.getsockname()[0]
s.close()

logging.basicConfig(filename="log.log", filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger("Vladhog_Security_QDAR")
logger.setLevel(logging.INFO)

def create_shortcut(file_name, target, work_dir, arguments=''):
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(file_name)
    shortcut.TargetPath = target
    shortcut.Arguments = arguments
    shortcut.WorkingDirectory = work_dir
    shortcut.save()

def get_engine_status():
    return any(p.name() == "qdar.exe" for p in psutil.process_iter())

def change_protection_state(state):
    global interface
    for i in netifaces.interfaces():
        try:
            if netifaces.ifaddresses(i).get(netifaces.AF_INET):
                if netifaces.ifaddresses(i)[netifaces.AF_INET][0]['addr'] == local_ip:
                    interface = i
                    break
        except Exception:
            pass
    key_path = F"SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces\\{interface}"
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
        new_dns = "127.0.0.1,1.1.1.1" if state else ""
        winreg.SetValueEx(key, 'NameServer', None, winreg.REG_SZ, new_dns)
    logger.info(f"Changed interface {interface} dns server to QDAR dns" if state else f"Changed interface {interface} dns server to default dns")

def get_settings(name):
    try:
        with open("settings.vdf", "rb") as file:
            data = VDF.decrypt(file.read()).decode()
            data = json.loads(data)
            return data.get(name)
    except Exception:
        logger.error(traceback.format_exc())

def change_settings(name, value):
    try:
        with open("settings.vdf", "rb") as file:
            data = VDF.decrypt(file.read()).decode()
            data = json.loads(data)
            data[name] = value
        with open("settings.vdf", "wb") as file:
            t = json.dumps(data, ensure_ascii=False, indent=2)
            data = VDF.encrypt(t.encode())
            file.write(data)
    except Exception:
        logger.error(traceback.format_exc())

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False