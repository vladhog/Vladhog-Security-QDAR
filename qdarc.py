import ctypes
import os
import time
import tkinter
import threading
import traceback
from tkinter import Label

from utils import get_engine_status, change_protection_state, change_settings, get_settings, is_admin, logger

protection_state_list = ["On", "Off"]
if is_admin():
    try:
        def update_qdar_status():
            while True:
                time.sleep(5)
                if get_engine_status():
                    status_text.config(text="QDAR Engine: Working")
                else:
                    status_text.config(text="QDAR Engine: Not working")


        def update_protection_settings(*args):
            if protection_var.get() == "On":
                change_settings("ProtectionEnabled", True)
                change_protection_state(True)
            else:
                change_settings("ProtectionEnabled", False)
                change_protection_state(False)


        window = tkinter.Tk()
        window.resizable(width=False, height=False)
        window.geometry("240x120")
        window.title("Vladhog Security QDAR")
        window.iconbitmap(default='Icon.ico')

        status_text = Label(window, text="QDAR Engine: Checking...", font=("Helvetic", 12))
        status_text.place(x=30, y=20)
        protection_menu_text = Label(window, text="Enable protection", font=("Helvetic", 12))
        protection_menu_text.place(x=10, y=54)

        protection_var = tkinter.StringVar(window)
        if get_settings("ProtectionEnabled"):
            protection_var.set(protection_state_list[0])
        else:
            protection_var.set(protection_state_list[1])
        protection_menu = tkinter.OptionMenu(window, protection_var, *protection_state_list)
        protection_menu.config(width=2, font=('Helvetica', 10))
        protection_menu.place(x=160, y=50)
        protection_var.trace("w", update_protection_settings)

        threading.Thread(target=update_qdar_status).start()
        window.mainloop()
    except Exception:
        logger.error(traceback.format_exc())
        logger.error(os.getcwd())
else:
# Re-run the program with admin rights
    ctypes.windll.shell32.ShellExecuteW(None, "runas", os.getcwd() + "\\qdarc.exe", "", None, 1)
