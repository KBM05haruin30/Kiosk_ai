import threading

VIDEO_EXTS = (".mp4", ".mov", ".mkv", ".avi")

class SharedState:
    def __init__(self, fallback):
        self.lock = threading.Lock()
        self.last_frame = None
        self.faces = []
        self.current_cat = fallback
        self.ema_male = 0.5
        self.ema_age = 30.0
        self.locked = False
        self.ended = False
        self.post_scan = False
        self.post_deadline = 0.0
