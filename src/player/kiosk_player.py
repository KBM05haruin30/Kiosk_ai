# D:\kiosk_ai\src\player\kiosk_player.py
from typing import List, Optional
from .fullscreen import FullscreenWindow
from .vlc_controller import VlcController
from .video_utils import list_videos, abspath

class KioskPlayer:
    def __init__(self, target_monitor_index: int | None = None, topmost: bool = True, volume: int = 100):
        self.win = FullscreenWindow(target_monitor_index, topmost)
        self.vlc = VlcController(self.win.hwnd, volume=volume)

        self._current_folder: Optional[str] = None
        self.win.bind_escape_to(self.close)

    # 콜백
    def set_on_end(self, cb): self.vlc.set_on_end(cb)

    # 내부
    def _play_files(self, files: List[str], start_index: int, loop: bool, volume: int):
        self.vlc.apply_files(files, start_index=start_index, loop=loop, volume=volume)

    # 공개 API (기존과 동일)
    def play_files(self, files: List[str], start_index: int = 0, volume: int = 100, *, loop: bool = True):
        if not files:
            raise FileNotFoundError("재생할 파일 목록이 비어 있습니다.")
        self._play_files(files, start_index, loop, volume)

    def play_folder(self, folder: str, start_index: int = 0, volume: int = 100, *, loop: bool = True):
        folder_abs = abspath(folder)
        files = list_videos(folder_abs)
        if not files:
            raise FileNotFoundError(f"폴더에 재생할 영상이 없습니다: {folder_abs}")
        if loop and self._current_folder == folder_abs and self.vlc.is_looping():
            return
        self._current_folder = folder_abs
        self._play_files(files, start_index, loop, volume)

    def play_folder_once(self, folder: str, start_index: int = 0, volume: int = 100):
        self.play_folder(folder, start_index=start_index, volume=volume, loop=False)

    def switch_folder(self, folder: str, start_index: int = 0, volume: int = 100, *, once: bool = False):
        folder_abs = abspath(folder)
        if not once and self._current_folder == folder_abs and self.vlc.is_looping():
            return
        if once:
            self.play_folder_once(folder_abs, start_index=start_index, volume=volume)
        else:
            self.play_folder(folder_abs, start_index=start_index, volume=volume, loop=True)

    def is_looping(self) -> bool: return self.vlc.is_looping()
    def next(self): self.vlc.next()
    def previous(self): self.vlc.previous()
    def pause(self): self.vlc.pause()
    def resume(self): self.vlc.resume()
    def set_volume(self, v: int): self.vlc.set_volume(v)

    def close(self):
        self.vlc.close()
        self.win.close()

    def run(self):
        self.win.run()
