import tkinter as tk
from tkinter import ttk, messagebox
from collections import Counter
import threading, traceback
import pystray
from PIL import Image, ImageDraw
from pynput import keyboard, mouse

# 标准全尺寸键盘：主键区 + 导航区 + 数字小键盘
LAYOUT = [
[("ESC","esc",0,1),("F1","f1",2,1),("F2","f2",3,1),("F3","f3",4,1),("F4","f4",5,1),("F5","f5",7,1),("F6","f6",8,1),("F7","f7",9,1),("F8","f8",10,1),("F9","f9",12,1),("F10","f10",13,1),("F11","f11",14,1),("F12","f12",15,1),("PRT","print_screen",17,1),("SCR","scroll_lock",18,1),("PAU","pause",19,1)],
[("`","`",0,1),("1","1",1,1),("2","2",2,1),("3","3",3,1),("4","4",4,1),("5","5",5,1),("6","6",6,1),("7","7",7,1),("8","8",8,1),("9","9",9,1),("0","0",10,1),("-","-",11,1),("=","=",12,1),("BACK","backspace",13,2),("INS","insert",17,1),("HOME","home",18,1),("PGUP","page_up",19,1),("NUM","num_lock",21,1),("/","num_divide",22,1),("*","num_multiply",23,1),("-","num_subtract",24,1)],
[("TAB","tab",0,1.5),("Q","q",1.5,1),("W","w",2.5,1),("E","e",3.5,1),("R","r",4.5,1),("T","t",5.5,1),("Y","y",6.5,1),("U","u",7.5,1),("I","i",8.5,1),("O","o",9.5,1),("P","p",10.5,1),("[","[",11.5,1),("] ","]",12.5,1),("\\","\\",13.5,1.5),("DEL","delete",17,1),("END","end",18,1),("PGDN","page_down",19,1),("7","num7",21,1),("8","num8",22,1),("9","num9",23,1),("+","num_add",24,1)],
[("CAPS","caps_lock",0,1.8),("A","a",1.8,1),("S","s",2.8,1),("D","d",3.8,1),("F","f",4.8,1),("G","g",5.8,1),("H","h",6.8,1),("J","j",7.8,1),("K","k",8.8,1),("L","l",9.8,1),(";",";",10.8,1),("'","'",11.8,1),("ENTER","enter",12.8,2.2),("4","num4",21,1),("5","num5",22,1),("6","num6",23,1)],
[("SHIFT","shift",0,2.3),("Z","z",2.3,1),("X","x",3.3,1),("C","c",4.3,1),("V","v",5.3,1),("B","b",6.3,1),("N","n",7.3,1),("M","m",8.3,1),(",",",",9.3,1),(".", ".",10.3,1),("/","/",11.3,1),("SHIFT","shift_r",12.3,2.7),("↑","up",18,1),("1","num1",21,1),("2","num2",22,1),("3","num3",23,1),("ENT","num_enter",24,1)],
[("CTRL","ctrl",0,1.5),("WIN","cmd",1.5,1.2),("ALT","alt",2.7,1.2),("SPACE","space",3.9,6),("ALT","alt_r",9.9,1.2),("FN","fn",11.1,1),("CTRL","ctrl_r",12.1,1.5),("←","left",17,1),("↓","down",18,1),("→","right",19,1),("0","num0",21,2),(".","num_decimal",23,1)]
]
SPECIAL = {keyboard.Key.esc:"esc", keyboard.Key.tab:"tab", keyboard.Key.caps_lock:"caps_lock",
 keyboard.Key.shift:"shift",keyboard.Key.shift_r:"shift_r",keyboard.Key.ctrl:"ctrl",keyboard.Key.ctrl_r:"ctrl_r",
 keyboard.Key.alt:"alt",keyboard.Key.alt_r:"alt_r",keyboard.Key.cmd:"cmd",keyboard.Key.cmd_r:"cmd",
 keyboard.Key.space:"space",keyboard.Key.enter:"enter",keyboard.Key.backspace:"backspace",
 keyboard.Key.delete:"delete",keyboard.Key.insert:"insert",keyboard.Key.home:"home",keyboard.Key.end:"end",
 keyboard.Key.page_up:"page_up",keyboard.Key.page_down:"page_down",keyboard.Key.left:"left",
 keyboard.Key.right:"right",keyboard.Key.up:"up",keyboard.Key.down:"down",keyboard.Key.print_screen:"print_screen",
 keyboard.Key.scroll_lock:"scroll_lock",keyboard.Key.pause:"pause",keyboard.Key.num_lock:"num_lock",
 **{getattr(keyboard.Key,f"f{i}"):f"f{i}" for i in range(1,13)}}

class App:
 def __init__(self):
  self.lock=threading.RLock(); self.counts=Counter(); self.total=0; self.last="—"
  self.x=self.y=0; self.left=self.right=self.middle=self.wheel=0; self.last_mouse="—"; self.event="尚未收到事件"
  self.errors=[]; self.key_status="启动中"; self.mouse_status="启动中"; self.widgets={}; self.running=True
 def kid(self,k):
  if k in SPECIAL:return SPECIAL[k]
  if isinstance(k,keyboard.KeyCode):
   if k.char:return k.char.lower()
   vk=getattr(k,"vk",None)
   if vk is not None:return {96:"num0",97:"num1",98:"num2",99:"num3",100:"num4",101:"num5",102:"num6",103:"num7",104:"num8",105:"num9",106:"num_multiply",107:"num_add",109:"num_subtract",110:"num_decimal",111:"num_divide"}.get(vk,f"vk_{vk}")
  return str(k).replace("Key.","").lower()
 def on_key(self,k):
  try:
   n=self.kid(k)
   with self.lock:self.counts[n]+=1;self.total+=1;self.last=n.upper();self.event="键盘："+n.upper()
  except Exception as e:self.err("键盘",e)
 def err(self,who,e):
  with self.lock:self.errors.append(f"{who}: {type(e).__name__}: {e}");self.errors=self.errors[-3:]
 def on_move(self,x,y):
  with self.lock:self.x=int(x);self.y=int(y);self.event=f"鼠标移动：{int(x)},{int(y)}"
 def on_click(self,x,y,b,p):
  if not p:return
  with self.lock:
   if b==mouse.Button.left:self.left+=1;self.last_mouse="左键"
   elif b==mouse.Button.right:self.right+=1;self.last_mouse="右键"
   elif b==mouse.Button.middle:self.middle+=1;self.last_mouse="中键"
   self.event="鼠标："+self.last_mouse
 def on_scroll(self,x,y,dx,dy):
  with self.lock:self.wheel+=1;self.last_mouse="滚轮上滚" if dy>0 else "滚轮下滚";self.event="鼠标："+self.last_mouse
 def add_key(self,parent,label,kid,col,row,span=1):
  # Tkinter 的 row/column 必须是整数；布局坐标允许半键宽，因此先换算为整数网格
  grid_col = int(round(col * 2))
  grid_span = max(1, int(round(span * 2)))
  f=tk.Frame(parent,bg="#e8edf2",highlightthickness=1,highlightbackground="#bac6d2")
  f.grid(row=row,column=grid_col,columnspan=grid_span,padx=2,pady=2,sticky="nsew")
  f.configure(height=48);f.grid_propagate(False)
  a=tk.Label(f,text=label,bg="#e8edf2",fg="#26394b",font=("Segoe UI",8,"bold"));a.pack(anchor="w",padx=4,pady=(3,0))
  b=tk.Label(f,text="0",bg="#e8edf2",fg="#657586",font=("Segoe UI",10,"bold"));b.pack(side="bottom",anchor="e",padx=4,pady=(0,3))
  self.widgets[kid]=(f,a,b)
 def build_keys(self,parent):
  for c in range(52):parent.grid_columnconfigure(c,weight=1,uniform="key")
  for r,row in enumerate(LAYOUT):
   for label,kid,col,span in row:self.add_key(parent,label,kid,col,r,span)
 def refresh(self):
  if not self.running:return
  with self.lock:
   counts=self.counts.copy();total=self.total;last=self.last;x,y=self.x,self.y
   l,r,m,w=self.left,self.right,self.middle,self.wheel;lm=self.last_mouse;ev=self.event;errs=list(self.errors)
  self.summary.set(f"键盘总次数：{total}    最近按键：{last}")
  self.mouseinfo.set(f"鼠标坐标：X={x}  Y={y}    最近操作：{lm}    左键 {l}  右键 {r}  中键 {m}  滚轮 {w}")
  self.eventinfo.set("最近事件："+ev);self.errorinfo.set("错误："+("；".join(errs) if errs else "无"))
  for kid,(f,a,b) in self.widgets.items():
   n=counts.get(kid,0);bg="#d9f0df" if n else "#e8edf2"
   f.configure(bg=bg);a.configure(bg=bg);b.configure(bg=bg,fg="#176b35" if n else "#657586");b.configure(text=str(n))
  self.root.after(100,self.refresh)
 def icon_image(self):
  im=Image.new("RGB",(64,64),(35,55,75));d=ImageDraw.Draw(im);d.rounded_rectangle((12,6,52,58),radius=9,fill="white");d.line((32,12,32,25),fill="#2878be",width=3);return im
 def show(self,icon=None,item=None):self.root.after(0,lambda:(self.root.deiconify(),self.root.lift()))
 def hide(self):self.root.withdraw()
 def reset(self,icon=None,item=None):
  with self.lock:self.counts.clear();self.total=0;self.last="—";self.left=self.right=self.middle=self.wheel=0;self.event="统计已重置"
 def quit(self,icon=None,item=None):
  self.running=False
  try:self.kl.stop();self.ml.stop();self.tray.stop()
  except Exception:pass
  self.root.after(0,self.root.destroy)
 def run(self):
  self.root=tk.Tk();self.root.title("鼠标键盘实时监控");self.root.geometry("1250x520");self.root.minsize(1050,480)
  outer=ttk.Frame(self.root,padding=12);outer.pack(fill="both",expand=True)
  ttk.Label(outer,text="鼠标 & 键盘实时监控",font=("Microsoft YaHei UI",16,"bold")).pack(anchor="w")
  self.summary=tk.StringVar();self.mouseinfo=tk.StringVar();self.eventinfo=tk.StringVar();self.errorinfo=tk.StringVar()
  for v in (self.summary,self.mouseinfo,self.eventinfo):ttk.Label(outer,textvariable=v).pack(anchor="w",pady=2)
  box=ttk.LabelFrame(outer,text="全键盘按键次数（每个键帽显示累计次数）",padding=6);box.pack(fill="both",expand=True,pady=8)
  self.build_keys(box)
  ttk.Label(outer,text="灰色：尚未按过    浅绿色：已有按键记录    关闭窗口隐藏到系统托盘").pack(anchor="w")
  ttk.Label(outer,textvariable=self.errorinfo,foreground="#a33").pack(anchor="w")
  self.root.protocol("WM_DELETE_WINDOW",self.hide)
  self.kl=keyboard.Listener(on_press=self.on_key);self.kl.start();self.key_status="已启动"
  self.ml=mouse.Listener(on_move=self.on_move,on_click=self.on_click,on_scroll=self.on_scroll);self.ml.start();self.mouse_status="已启动"
  menu=pystray.Menu(pystray.MenuItem("打开监控窗口",self.show,default=True),pystray.MenuItem("重置统计",self.reset),pystray.MenuItem("退出",self.quit))
  self.tray=pystray.Icon("MouseKeyboardMonitor",self.icon_image(),"鼠标键盘监控",menu)
  threading.Thread(target=self.tray.run,daemon=True).start();self.refresh();self.root.mainloop()

if __name__=="__main__":
 try:App().run()
 except Exception:
  with open("MouseKeyboardMonitor_error.txt","w",encoding="utf-8") as f:f.write(traceback.format_exc())
  try:messagebox.showerror("启动失败","程序启动失败，已生成 MouseKeyboardMonitor_error.txt")
  except Exception:pass
