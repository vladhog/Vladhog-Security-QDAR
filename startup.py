import os.path
import pathlib
import random
import traceback
import argparse
import shutil
from winreg import OpenKey, HKEY_CURRENT_USER, KEY_WOW64_64KEY, KEY_READ, EnumValue

import psutil
from urllib3.util import connection
from dns import message, query
import requests
import zipfile
from pathlib import Path

from vladhog_filetype import VDF
import json
import ctypes, sys
from utils import is_admin, change_protection_state

dir_path = "C:\\Program Files (x86)\\Vladhog Security QDAR\\"
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_TERMINATE = 1
key = OpenKey(HKEY_CURRENT_USER, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\User Shell Folders", 0,
                     KEY_WOW64_64KEY | KEY_READ)

i = 0
while True:
    try:
        a = EnumValue(key, i)
        if a[0] == "Desktop":
            b = pathlib.Path(a[1])
            c = pathlib.Path(*b.parts[1:])
        i += 1
    except OSError:
        break
desktop = os.path.join(os.path.join(os.path.expanduser('~')), c)


if is_admin():
    from utils import logger, create_shortcut

    try:
        parser = argparse.ArgumentParser('Vladhog Security QDAR')
        parser.add_argument('--update', action='store_true')
        args = parser.parse_args()
        if os.getcwd() != "C:\\Program Files (x86)\\Vladhog Security QDAR":
            Path(f"C:/Program Files (x86)/Vladhog Security QDAR/").mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy(os.getcwd() + "\\startup.exe", "C:\\Program Files (x86)\\Vladhog Security QDAR")
            except Exception:
                pass
            os.chdir("C:\\Program Files (x86)\\Vladhog Security QDAR")
            if args.update:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", dir_path + "startup.exe", "--update", None, 1)
            else:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", dir_path + "startup.exe", "", None, 1)
            sys.exit()

        Path(f"C:/Program Files (x86)/Vladhog Security QDAR/").mkdir(parents=True, exist_ok=True)

        _orig_create_connection = connection.create_connection

        logger.info("Checking settings file...")
        if not os.path.isfile("settings.vdf"):
            logger.info("Settings file not found, making new one")
            with open("settings.vdf", "wb") as file:
                template = {"ProtectionEnabled": True}
                t = json.dumps(template, ensure_ascii=False, indent=2)
                data = VDF.encrypt(t.encode())
                file.write(data)


        def patched_create_connection(address, *args, **kwargs):
            """Wrap urllib3's create_connection to resolve the name elsewhere"""
            # resolve hostname to an ip address; use your own
            # resolver here, as otherwise the system resolver will be used.
            host, port = address
            q = message.make_query(host, 'A')
            hostname = str(random.choice(query.tcp(q, '1.1.1.1', port=53).answer[0]))

            return _orig_create_connection((hostname, port), *args, **kwargs)


        connection.create_connection = patched_create_connection

        if not args.update:
            try:
                # download program
                logger.info("Downloading QDAR...")
                with requests.get("https://vladhog.ru/download/qdar.zip", stream=True) as r:
                    r.raise_for_status()
                    with open(str(os.getenv("tmp")) + "/qdar.zip", 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)

                # extract
                logger.info("Extracting...")
                with zipfile.ZipFile(str(os.getenv("tmp")) + "/qdar.zip", 'r') as archive:
                    archive.extractall(dir_path)

                os.system(f'schtasks /create /tn "Vladhog Security Quick DNS Antivirus Responder" /xml "{dir_path}setup.xml"')
                create_shortcut(desktop + "\\Vladhog Security QDAR.lnk", dir_path + "qdarc.exe", dir_path)

                os.remove(str(os.getenv("tmp")) + "/qdar.zip")
                logger.info("Done! Starting qdar.exe")
                ctypes.windll.shell32.ShellExecuteW(None, "runas", dir_path + "qdar.exe", "", None, 1)
                ctypes.windll.shell32.ShellExecuteW(None, "runas", dir_path + "qdarc.exe", "", None, 1)
                change_protection_state(True)
            except Exception:
                logger.error(traceback.format_exc())
        else:
            try:
                update_done = False

                try:
                    os.remove(dir_path + "qdar.exe")
                except Exception:
                    for proc in psutil.process_iter():
                        if proc.name().lower() == "qdar.exe":
                            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE | PROCESS_QUERY_INFORMATION,
                                                                        False,
                                                                        int(proc.pid))
                            ctypes.windll.kernel32.TerminateProcess(handle, -1)
                            ctypes.windll.kernel32.CloseHandle(handle)
                            break
                    os.remove(dir_path + "qdar.exe")
                try:
                    os.remove(dir_path + "qdarc.exe")
                except Exception:
                    for proc in psutil.process_iter():
                        if proc.name().lower() == "qdarc.exe":
                            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE | PROCESS_QUERY_INFORMATION,
                                                                        False,
                                                                        int(proc.pid))
                            ctypes.windll.kernel32.TerminateProcess(handle, -1)
                            ctypes.windll.kernel32.CloseHandle(handle)
                            break
                    os.remove(dir_path + "qdarc.exe")

                logger.info("Updating qdar...")
                with requests.get("https://vladhog.ru/download/qdar.zip", stream=True) as r:
                    r.raise_for_status()
                    with open(str(os.getenv("tmp")) + "/qdar.zip", 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)

                # extract
                logger.info("Extracting...")
                with zipfile.ZipFile(str(os.getenv("tmp")) + "/qdar.zip", 'r') as archive:
                    archive.extractall(dir_path)
                    update_done = True

                os.remove(str(os.getenv("tmp")) + "/qdar.zip")
                logger.info("Done! Starting qdar.exe")

                if update_done:
                    ctypes.windll.shell32.ShellExecuteW(None, "runas", dir_path + "qdar.exe", "", None, 1)
            except Exception:
                logger.error(traceback.format_exc())
    except Exception:
        print(traceback.format_exc())
else:
    # Re-run the program with admin rights
    ctypes.windll.shell32.ShellExecuteW(None, "runas", os.getcwd() + "\\startup.exe", "", None, 1)
