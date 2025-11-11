# D:\kiosk_ai\src\player\fullscreen.py
import tkinter as tk
from screeninfo import get_monitors

class FullscreenWindow:
    def __init__(self, target_monitor_index: int | None = None, topmost: bool = True):
        mons = get_monitors()
        if not mons:
            raise RuntimeError("모니터 정보를 가져올 수 없습니다.")
        if target_monitor_index is None:
            target_monitor_index = 1 if len(mons) > 1 else 0
        self.mon = mons[target_monitor_index]

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.geometry(f"{self.mon.width}x{self.mon.height}+{self.mon.x}+{self.mon.y}")
        if topmost:
            self.root.lift()
            self.root.attributes("-topmost", True)

    @property
    def hwnd(self):
        return self.root.winfo_id()

    def bind_escape_to(self, fn):
        self.root.bind("<Escape>", lambda e: fn())

    def close(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def run(self):
        self.root.mainloop()
