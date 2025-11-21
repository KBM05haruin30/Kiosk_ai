# D:\kiosk_ai\src\player\vlc_controller.py
import time
import threading
from typing import List, Optional, Callable
import vlc

from .video_utils import abspath

class VlcController:
    def __init__(self, hwnd, volume: int = 100):
        self.instance = vlc.Instance("--no-video-title-show")
        self.media_player = self.instance.media_player_new()
        self.media_player.set_hwnd(hwnd)

        self.mlp = self.instance.media_list_player_new()
        self.mlp.set_media_player(self.media_player)
        self.mlp.set_playback_mode(vlc.PlaybackMode.loop)

        self._current_list: Optional[vlc.MediaList] = None
        self._current_files: List[str] = []
        self._looping = True
        self._on_end: Optional[Callable[[], None]] = None
        self.media_player.audio_set_volume(volume)

        em = self.media_player.event_manager()
        em.event_attach(vlc.EventType.MediaPlayerEndReached, self._handle_end)

        self._stop_flag = False
        threading.Thread(target=self._guard_loop, daemon=True).start()

    # events/guard
    def set_on_end(self, cb: Callable[[], None] | None):
        self._on_end = cb

    def _handle_end(self, evt):
        print("[vlc] MediaPlayerEndReached")
        # once 모드일 때만 on_end 콜백 호출

        if self._on_end and not self._looping:
            try: self._on_end()
            except Exception as e: 
                print(f"[vlc] on_end callback error: {e}")

    def _guard_loop(self):
        while not self._stop_flag:
            st = self.media_player.get_state()

            # 상태 전이 로그
            if st != self._last_state:
                print(f"[vlc] state changed: {self._last_state} → {st}")
                self._last_state = st

            if st == vlc.State.Error:
                print("[vlc] ERROR detected in guard loop")
                if self._auto_recover and self._current_files:
                    print("[vlc] (auto-recover ON) would reload current list here")

            # 라즈베리 파이에서 중간 재시작이 Error 감지 -> 재적재 떄문인지 확인
            
            # if self.media_player.get_state() == vlc.State.Error and self._current_files:
            #     try:
            #         self.apply_files(self._current_files, 0, self._looping,
            #                          self.media_player.audio_get_volume())
            #     except Exception:
            #         pass
            time.sleep(0.5)

    # playlist
    def apply_files(self, files: List[str], start_index: int, loop: bool, volume: int):
        self._current_files = [abspath(p) for p in files]
        self.media_player.audio_set_volume(volume)

        if self._current_list:
            try: self.mlp.stop()
            except Exception: pass
            try: self._current_list.release()
            except Exception: pass
            self._current_list = None

        ml = self.instance.media_list_new([])
        for path in self._current_files:
            m = self.instance.media_new(path)
            m.add_option(":no-video-title-show")
            ml.add_media(m)

        self._current_list = ml
        self.mlp.set_media_list(ml)
        self._looping = bool(loop)
        self.mlp.set_playback_mode(vlc.PlaybackMode.loop if loop else vlc.PlaybackMode.default)
        self.mlp.play_item_at_index(max(0, min(start_index, len(self._current_files) - 1)))

    # controls
    def is_looping(self) -> bool: return self._looping
    def next(self):      
        try: self.mlp.next()
        except Exception: pass
    def previous(self):
        try: self.mlp.previous()
        except Exception: pass
    def pause(self):
        try: self.mlp.pause()
        except Exception: pass
    def resume(self):
        try: self.mlp.play()
        except Exception: pass
    def set_volume(self, v: int):
        self.media_player.audio_set_volume(max(0, min(100, int(v))))

    def close(self):
        self._stop_flag = True
        try: self.mlp.stop()
        except Exception: pass
