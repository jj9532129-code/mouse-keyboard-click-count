import threading
import tkinter as tk
from tkinter import ttk
from collections import Counter
from datetime import datetime

import pystray
from PIL import Image, ImageDraw
from pynput import keyboard, mouse


class MonitorApp:
    def __init__(self):
        self.lock = threading.Lock()
        self.running = True
        self.key_count = 0
        self.key_counts = Counter()
        self.last_key = "—"
        self.mouse_x = 0
        self.mouse_y = 0
        self.left_clicks = 0
        self.right_clicks = 0
        self.middle_clicks = 0
        self.scroll_count = 0
        self.last_mouse_action = "—"
        self.key_listener = None
        self.mouse_listener = None
        self.root = None
        self.tray = None
        self.status_var = None
        self.key_var = None
        self.mouse_var = None
        self.count_var = None
        self.detail_var = None

    @staticmethod
    def key_name(key):
        try:
            if isinstance(key, keyboard.KeyCode):
                # Show only the key identity; never read or store typed text.
                return key.char.upper() if key.char and key.char.isprintable() else "Key"
            name = str(key).replace("Key.", "")
            return name.upper()
        except Exception:
            return "Unknown"

    def on_key_press(self, key):
        with self.lock:
            self.key_count += 1
            name = self.key_name(key)
            self.last_key = name
            self.key_counts[name] += 1

    def on_move(self, x, y):
        with self.lock:
            self.mouse_x, self.mouse_y = int(x), int(y)

    def on_click(self, x, y, button, pressed):
        if not pressed:
            return
        with self.lock:
            if button == mouse.Button.left:
                self.left_clicks += 1
                self.last_mouse_action = "Left click"
            elif button == mouse.Button.right:
                self.right_clicks += 1
                self.last_mouse_action = "Right click"
            elif button == mouse.Button.middle:
                self.middle_clicks += 1
                self.last_mouse_action = "Middle click"

    def on_scroll(self, x, y, dx, dy):
        with self.lock:
            self.scroll_count += 1
            self.last_mouse_action = "Wheel up" if dy > 0 else "Wheel down"

    def snapshot(self):
        with self.lock:
            top = self.key_counts.most_common(8)
            return {
                "key_count": self.key_count,
                "last_key": self.last_key,
                "top": top,
                "x": self.mouse_x, "y": self.mouse_y,
                "left": self.left_clicks, "right": self.right_clicks,
                "middle": self.middle_clicks, "scroll": self.scroll_count,
                "last_mouse": self.last_mouse_action,
            }

    def start_listeners(self):
        self.key_listener = keyboard.Listener(on_press=self.on_key_press)
        self.mouse_listener = mouse.Listener(
            on_move=self.on_move, on_click=self.on_click, on_scroll=self.on_scroll
        )
        self.key_listener.start()
        self.mouse_listener.start()

    def make_icon(self):
        image = Image.new("RGB", (64, 64), (32, 45, 62))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((7, 8, 57, 56), radius=9, fill=(40, 125, 190))
        draw.rectangle((15, 17, 49, 42), fill=(235, 242, 248))
        for x in (20, 28, 36, 44):
            draw.rectangle((x, 22, x + 4, 27), fill=(40, 125, 190))
        draw.rectangle((24, 32, 40, 36), fill=(40, 125, 190))
        return image

    def create_tray(self):
        menu = pystray.Menu(
            pystray.MenuItem("打开监控窗口", self.show_window, default=True),
            pystray.MenuItem("重置统计", self.reset_stats),
            pystray.MenuItem("退出", self.quit_app),
        )
        self.tray = pystray.Icon("MouseKeyboardMonitor", self.make_icon(),
                                 "鼠标键盘监控", menu)
        threading.Thread(target=self.tray.run, daemon=True).start()

    def show_window(self, icon=None, item=None):
        if self.root:
            self.root.after(0, self._show_window)

    def _show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def hide_window(self):
        self.root.withdraw()

    def reset_stats(self, icon=None, item=None):
        with self.lock:
            self.key_count = 0
            self.key_counts.clear()
            self.last_key = "—"
            self.left_clicks = self.right_clicks = self.middle_clicks = 0
            self.scroll_count = 0
            self.last_mouse_action = "—"

    def quit_app(self, icon=None, item=None):
        self.running = False
        try:
            if self.key_listener:
                self.key_listener.stop()
            if self.mouse_listener:
                self.mouse_listener.stop()
            if self.tray:
                self.tray.stop()
        finally:
            if self.root:
                self.root.after(0, self.root.destroy)

    def update_ui(self):
        if not self.running:
            return
        s = self.snapshot()
        self.key_var.set(f"最近按键：{s['last_key']}    按键总次数：{s['key_count']}")
        self.mouse_var.set(f"鼠标坐标：X={s['x']}  Y={s['y']}    最近操作：{s['last_mouse']}")
        self.count_var.set(
            f"左键：{s['left']}    右键：{s['right']}    中键：{s['middle']}    滚轮：{s['scroll']}"
        )
        top_text = "按键统计（前 8 项）：\n" + (
            "\n".join(f"  {name}: {count}" for name, count in s["top"]) or "  暂无按键记录"
        )
        self.detail_var.set(top_text)
        self.status_var.set("监控中 · 仅统计按键名称和次数，不保存输入内容")
        self.root.after(150, self.update_ui)

    def run(self):
        self.root = tk.Tk()
        self.root.title("鼠标键盘实时监控")
        self.root.geometry("520x330")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

        frame = ttk.Frame(self.root, padding=16)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="鼠标 & 键盘实时监控", font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w")
        ttk.Separator(frame).pack(fill="x", pady=10)

        self.key_var = tk.StringVar()
        self.mouse_var = tk.StringVar()
        self.count_var = tk.StringVar()
        self.detail_var = tk.StringVar()
        self.status_var = tk.StringVar()

        ttk.Label(frame, textvariable=self.key_var, font=("Microsoft YaHei UI", 10)).pack(anchor="w", pady=4)
        ttk.Label(frame, textvariable=self.mouse_var, font=("Microsoft YaHei UI", 10)).pack(anchor="w", pady=4)
        ttk.Label(frame, textvariable=self.count_var, font=("Microsoft YaHei UI", 10)).pack(anchor="w", pady=4)
        ttk.Separator(frame).pack(fill="x", pady=8)
        ttk.Label(frame, textvariable=self.detail_var, font=("Consolas", 10), justify="left").pack(anchor="w")
        ttk.Separator(frame).pack(fill="x", pady=8)
        ttk.Label(frame, textvariable=self.status_var, foreground="#16803c").pack(anchor="w")
        ttk.Label(frame, text="关闭窗口会最小化到系统托盘；右键托盘图标可重置或退出。",
                  foreground="#666666").pack(anchor="w", pady=(6, 0))

        self.create_tray()
        self.update_ui()
        self.root.mainloop()


if __name__ == "__main__":
    MonitorApp().run()
