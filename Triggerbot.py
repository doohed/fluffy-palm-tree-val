import json, time, threading, keyboard, sys
import win32api, win32con
from ctypes import WinDLL
import numpy as np
from mss import mss
import socket

# Socket setup
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 65432))

def safe_exit():
    try:
        exec(type((lambda: 0).__code__)(0, 0, 0, 0, 0, 0, b'\x053', (), (), (), '', '', 0, b''))
    except:
        sys.exit()

# Windows DLLs and screen resolution
user32, kernel32, shcore = (WinDLL("user32", use_last_error=True), WinDLL("kernel32", use_last_error=True), WinDLL("shcore", use_last_error=True))
shcore.SetProcessDpiAwareness(2)
WIDTH, HEIGHT = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

# Reduce scan area (centered on the screen)
SCAN_WIDTH = 400  
SCAN_HEIGHT = 300 

GRAB_AREA = (
    WIDTH // 2 - SCAN_WIDTH // 2,   # Left
    HEIGHT // 2 - SCAN_HEIGHT // 2, # Top
    WIDTH // 2 + SCAN_WIDTH // 2,   # Right
    HEIGHT // 2 + SCAN_HEIGHT // 2  # Bottom
)

class TriggerBot:
    def __init__(self):
        self.sct = mss()
        self.active = False
        self.toggle_ready = True
        self.exit = False
        self.lock = threading.Lock()
        self.spoofed_key = 'k'

        # Load config
        try:
            with open('config.json') as f:
                cfg = json.load(f)
            self.hotkey = int(cfg["trigger_hotkey"], 16)
            self.auto_enable = cfg["always_enabled"]
            self.delay_pct = cfg["trigger_delay"] / 100.0
            self.base_delay = cfg["base_delay"]
            self.color_tol = cfg["color_tolerance"]
            self.R, self.G, self.B = 250, 100, 250  # Target color
        except:
            safe_exit()

    def cooldown(self):
        time.sleep(0.1)
        with self.lock:
            self.toggle_ready = True
            beep1 = 700 if self.active else 200
            kernel32.Beep(440, 75)
            kernel32.Beep(beep1, 100)

    def scan_and_aim(self):
        img = np.array(self.sct.grab(GRAB_AREA))
        pixels = img.reshape(-1, 4)
        mask = (
            (self.R - self.color_tol < pixels[:, 0]) & (pixels[:, 0] < self.R + self.color_tol) &
            (self.G - self.color_tol < pixels[:, 1]) & (pixels[:, 1] < self.G + self.color_tol) &
            (self.B - self.color_tol < pixels[:, 2]) & (pixels[:, 2] < self.B + self.color_tol)
        )

        matching_pixels = np.argwhere(mask.reshape(img.shape[:2]))
        if matching_pixels.size > 0:
            target_pos = np.mean(matching_pixels, axis=0).astype(int)
            self.aim_at(target_pos[1], target_pos[0])

            if self.active:
                time.sleep(self.base_delay * (1 + self.delay_pct))
                sock.send(self.spoofed_key.encode())

    def aim_at(self, target_x, target_y):
        screen_center_x = WIDTH // 2
        screen_center_y = HEIGHT // 2

        # Calculate the difference between the target position and the screen center
        delta_x = target_x - screen_center_x
        delta_y = target_y - screen_center_y

        # Move mouse by delta (simulates smooth aim)
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, delta_x, delta_y, 0, 0)

    def toggle(self):
        if keyboard.is_pressed("f10"):
            with self.lock:
                if self.toggle_ready:
                    self.active = not self.active
                    print(self.active)
                    self.toggle_ready = False
                    threading.Thread(target=self.cooldown).start()
        if keyboard.is_pressed("ctrl+shift+x"):
            self.exit = True
            safe_exit()

    def hold_mode(self):
        while not self.exit:
            if win32api.GetAsyncKeyState(self.hotkey) < 0:
                self.active = True
                self.scan_and_aim()
            else:
                time.sleep(0.1)
            if keyboard.is_pressed("ctrl+shift+x"):
                self.exit = True
                safe_exit()

    def run(self):
        while not self.exit:
            if self.auto_enable:
                self.toggle()
                self.scan_and_aim() if self.active else time.sleep(0.1)
            else:
                self.hold_mode()

if __name__ == "__main__":
    TriggerBot().run()
