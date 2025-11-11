# D:\kiosk_ai\src\player\video_utils.py
import os
from typing import List

VIDEO_EXTS = (".mp4", ".mov", ".mkv", ".avi")

def abspath(p: str) -> str:
    return os.path.abspath(p)

def list_videos(folder: str) -> List[str]:
    files = [os.path.join(folder, f) for f in os.listdir(folder)
             if f.lower().endswith(VIDEO_EXTS)]
    files.sort()
    return files
