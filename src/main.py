import os, time, threading, queue, cv2
from config import load_config
from player import KioskPlayer
from ai_insight import InsightfaceEngine
from runtime_state import SharedState, VIDEO_EXTS
from loops import run_capture, run_infer, run_preview

def valid_folder_or_fallback(base, cats_map, fallback_key):
    def has_video(folder):
        try:
            return any(f.lower().endswith(VIDEO_EXTS) for f in os.listdir(folder))
        except: return False
    paths = {"cats": {}}
    for k, v in cats_map.items():
        folder = os.path.join(base, v)
        paths["cats"][k] = folder if has_video(folder) else os.path.join(base, cats_map[fallback_key])
    paths["fallback_path"] = os.path.join(base, cats_map[fallback_key])
    return paths

def open_camera(candidates, w,h,fps):
    for idx in candidates:
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH,  w)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
            cap.set(cv2.CAP_PROP_FPS,          fps)
            return cap, idx
        if cap: cap.release()
    raise RuntimeError("웹캠 오픈 실패: camera.index_candidates 확인")

def main():
    cfg = load_config()
    base, cats_map = cfg["videos"]["base"], cfg["videos"]["categories"]
    paths = valid_folder_or_fallback(base, cats_map, cfg["defaults"]["fallback_category"])

    player = KioskPlayer(target_monitor_index=cfg["display"]["target_monitor_index"], volume=6)
    player.play_folder(paths["fallback_path"])

    cam = cfg["camera"]; cap, cam_idx = open_camera(cam["index_candidates"], cam["width"], cam["height"], cam["fps"])
    print(f"[init] camera index={cam_idx}")

    providers = tuple(cfg.get("runtime", {}).get("providers", ["DmlExecutionProvider","CPUExecutionProvider"]))
    engine = InsightfaceEngine(providers=providers, det_size=(320,320), male_prob_hard=0.9)

    frame_q = queue.Queue(maxsize=4)
    stop = {"flag": False}
    state = SharedState(cfg["defaults"]["fallback_category"])

    # on_end → post-scan 진입
    def _on_end():
        import time
        with state.lock:
            state.ended = True
            state.post_scan = True
            state.post_deadline = time.time() + 1.2
            state.locked = False
        print("[end] user video ended → post-end scan window opened")
    player.set_on_end(_on_end)

    t_cap = threading.Thread(target=run_capture, args=(cap, frame_q, state, stop, cfg["inference"]["sample_every_n_frames"]), daemon=True)
    t_inf = threading.Thread(target=run_infer,    args=(engine, cfg, paths, player, frame_q, state, stop), daemon=True)
    t_cap.start(); t_inf.start()
    threading.Thread(target=run_preview, args=(state, stop), daemon=True).start()

    try:
        player.run()
    finally:
        stop["flag"] = True
        cap.release()
        try: cv2.destroyAllWindows()
        except: pass

if __name__ == "__main__":
    main()
