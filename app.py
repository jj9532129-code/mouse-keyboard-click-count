import threading
import tkinter as tk
from tkinter import ttk, messagebox
from collections import Counter
import traceback
import pystray
from PIL import Image, ImageDraw
from pynput import keyboard, mouse

class App:
    def __init__(self):
        self.lock = threading.RLock()
        self.running = True
        self.keys = Counter()
        self.key_total = 0
        self.last_key = "—"
        self.x = self.y = 0
        self.left = self.right = self.middle = self.wheel = 0
        self.last_mouse = "—"
        self.last_event = "尚未收到事件"
        self.key_status = "正在启动"
        self.mouse_status = "正在启动"
        self.errors = []
        self.root = None

    def error(self, who, exc):
        with self.lock:
            self.errors.append(f"{who}: {type(exc).__name__}: {exc}")
            self.errors = self.errors[-4:]
            if who.startswith("键盘"):
                self.key_status = "监听错误"
            if who.startswith("鼠标"):
                self.mouse_status = "监听错误"

    def key_name(self, key):
        if key == keyboard.Key.space: return "SPACE"
        if key == keyboard.Key.enter: return "ENTER"
        if key == keyboard.Key.tab: return "TAB"
        if key == keyboard.Key.backspace: return "BACKSPACE"
        if key == keyboard.Key.esc: return "ESC"
        if isinstance(key, keyboard.KeyCode):
            return key.char.upper() if key.char and key.char.isprintable() else "按键"
        return str(key).replace("Key.", "").upper()

    def on_key(self, key):
        try:
            name = self.key_name(key)
            with self.lock:
                self.key_total += 1
                self.keys[name] += 1
                self.last_key = name
                self.last_event = "键盘：" + name
        except Exception as e: self.error("键盘回调", e)

    def on_move(self, x, y):
        with self.lock:
            self.x, self.y = int(x), int(y)
            self.last_event = f"鼠标移动：{int(x)},{int(y)}"

    def on_click(self, x, y, button, pressed):
        if not pressed: return
        with self.lock:
            if button == mouse.Button.left:
                self.left += 1; self.last_mouse = "左键"
            elif button == mouse.Button.right:
                self.right += 1; self.last_mouse = "右键"
            elif button == mouse.Button.middle:
                self.middle += 1; self.last_mouse = "中键"
            self.last_event = "鼠标：" + self.last_mouse

    def on_scroll(self, x, y, dx, dy):
        with self.lock:
            self.wheel += 1
            self.last_mouse = "滚轮上滚" if dy > 0 else "滚轮下滚"
            self.last_event = "鼠标：" + self.last_mouse

    def start_hooks(self):
        try:
            self.kl = keyboard.Listener(on_press=self.on_key)
            self.kl.start()
            self.key_status = "已启动，等待按键"
        except Exception as e: self.error("键盘监听启动", e)
        try:
            self.ml = mouse.Listener(on_move=self.on_move, on_click=self.on_click, on_scroll=self.on_scroll)
            self.ml.start()
            self.mouse_status = "已启动，等待鼠标操作"
        except Exception as e: self.error("鼠标监听启动", e)

    def snapshot(self):
        with self.lock:
            return (self.key_total, self.last_key, self.keys.most_common(8),
                    self.x, self.y, self.left, self.right, self.middle, self.wheel,
                    self.last_mouse, self.last_event, self.key_status, self.mouse_status,
                    list(self.errors))

    def icon_image(self):
        im = Image.new("RGB", (64,64), (35,55,75))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((12,6,52,58), radius=9, fill=(240,245,250))
        d.line((32,12,32,25), fill=(30,120,190), width=3)
        d.line((14,29,50,29), fill=(30,120,190), width=2)
        return im

    def show(self, icon=None, item=None):
        if self.root: self.root.after(0, self._show)
    def _show(self):
        self.root.deiconify(); self.root.lift(); self.root.focus_force()
    def hide(self): self.root.withdraw()

    def reset(self, icon=None, item=None):
        with self.lock:
            self.keys.clear(); self.key_total = 0; self.last_key = "—"
            self.left = self.right = self.middle = self.wheel = 0
            self.last_mouse = "—"; self.last_event = "统计已重置"

    def quit(self, icon=None, item=None):
        self.running = False
        try:
            self.kl.stop(); self.ml.stop(); self.tray.stop()
        except Exception: pass
        if self.root: self.root.after(0, self.root.destroy)

    def refresh(self):
        if not self.running: return
        s = self.snapshot()
        (kt, lk, top, x, y, l, r, m, w, lm, le, ks, ms, errs) = s
        self.key_var.set(f"键盘：最近按键 {lk}    总次数 {kt}")
        self.mouse_var.set(f"鼠标坐标：X={x}  Y={y}    最近操作：{lm}")
        self.count_var.set(f"左键 {l}    右键 {r}    中键 {m}    滚轮 {w}")
        self.event_var.set("最近事件：" + le)
        self.top_var.set("按键次数统计：\n" + ("\n".join(f"  {a}: {b}" for a,b in top) or "  暂无按键记录"))
        self.status_var.set(f"键盘监听：{ks}    |    鼠标监听：{ms}")
        self.error_var.set("监听错误：" + ("；".join(errs) if errs else "无"))
        self.root.after(100, self.refresh)

    def run(self):
        self.root = tk.Tk()
        self.root.title("鼠标键盘实时监控")
        self.root.geometry("600x410")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.hide)
        f = ttk.Frame(self.root, padding=16); f.pack(fill="both", expand=True)
        ttk.Label(f, text="鼠标 & 键盘实时监控", font=("Microsoft YaHei UI",15,"bold")).pack(anchor="w")
        ttk.Separator(f).pack(fill="x", pady=9)
        self.key_var=tk.StringVar(); self.mouse_var=tk.StringVar(); self.count_var=tk.StringVar()
        self.event_var=tk.StringVar(); self.top_var=tk.StringVar(); self.status_var=tk.StringVar(); self.error_var=tk.StringVar()
        for v in (self.key_var,self.mouse_var,self.count_var,self.event_var):
            ttk.Label(f,textvariable=v).pack(anchor="w",pady=4)
        ttk.Separator(f).pack(fill="x",pady=7)
        ttk.Label(f,textvariable=self.top_var,font=("Consolas",10),justify="left").pack(anchor="w")
        ttk.Separator(f).pack(fill="x",pady=7)
        ttk.Label(f,textvariable=self.status_var,foreground="#176b35").pack(anchor="w",pady=3)
        ttk.Label(f,textvariable=self.error_var,foreground="#a33",wraplength=560).pack(anchor="w",pady=3)
        ttk.Label(f,text="关闭窗口会隐藏到托盘；右键托盘图标可重置或退出。").pack(anchor="w",pady=5)
        menu=pystray.Menu(pystray.MenuItem("打开监控窗口",self.show,default=True),
                          pystray.MenuItem("重置统计",self.reset),pystray.MenuItem("退出",self.quit))
        self.tray=pystray.Icon("MouseKeyboardMonitor",self.icon_image(),"鼠标键盘监控",menu)
        self.start_hooks()
        threading.Thread(target=self.tray.run,daemon=True).start()
        self.refresh()
        self.root.mainloop()

if __name__ == "__main__":
    try: App().run()
    except Exception:
        with open("MouseKeyboardMonitor_error.txt","w",encoding="utf-8") as f: f.write(traceback.format_exc())
        try: messagebox.showerror("启动失败","程序启动失败，已生成 MouseKeyboardMonitor_error.txt")
        except Exception: pass
