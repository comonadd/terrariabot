import subprocess
import sys
from PIL import Image, ImageDraw
import socket
from threading import Thread
import struct
from enum import Enum
from dataclasses import dataclass, field
from typing import List
import zlib
import numpy as np
from PIL import Image
import random
import time
import win32gui
import win32ui
from ctypes import windll
import pygame
import action_controller as ac
import keyboard
import copy
from logger import logger
from win32 import win32gui
from win32 import win32api
from win32 import win32process
import time
import psutil

def screenshot_window(hwnd):
    # Change the line below depending on whether you want the whole window
    # or just the client area.
    #left, top, right, bot = win32gui.GetClientRect(hwnd)
    left, top, right, bot = win32gui.GetWindowRect(hwnd)
    w = right - left
    h = bot - top

    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC  = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()

    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)

    saveDC.SelectObject(saveBitMap)

    # Change the line below depending on whether you want the whole window
    # or just the client area.
    #result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 1)
    result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0)
    print (result)

    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)

    im = Image.frombuffer(
        'RGB',
        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        bmpstr, 'raw', 'BGRX', 0, 1)

    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)

    if result == 1:
        return im
    return None

def focus_on_window(hwnd):
    win32gui.SetForegroundWindow(hwnd)

def process_main_window_name(strCmd, on_result):
    mID2Handle={}
    def get_all_hwnd(hwnd,mouse):
        if win32gui.IsWindow(hwnd) and win32gui.IsWindowEnabled(hwnd) and win32gui.IsWindowVisible(hwnd):
            nID=win32process.GetWindowThreadProcessId(hwnd)
            #print(nID,win32gui.GetWindowText(hwnd))
            del nID[0]
            for abc in nID:
                try:
                    pro=psutil.Process(abc).name()
                except psutil.NoSuchProcess:
                    pass
            else:
                #print(abc,win32gui.GetWindowText(hwnd))
                if pro == strCmd:
                    on_result(hwnd)
                mID2Handle[abc]=hwnd
    win32gui.EnumWindows(get_all_hwnd, 0)
    return None
