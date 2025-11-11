import cv2

def run(state, stop_flag):
    win = "camera_preview"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win, 640, 360)
    last_title = None
    while not stop_flag["flag"]:
        with state.lock:
            frame = None if state.last_frame is None else state.last_frame.copy()
            faces = list(state.faces)
            title = state.current_cat
            em, ea = state.ema_male, state.ema_age

        if frame is not None:
            for (x1,y1,x2,y2,_) in faces:
                cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 2)
            cv2.putText(frame, title, (10,28), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)
            cv2.putText(frame, f"male={em:.2f}  age~{ea:.1f}", (10,54), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
            cv2.imshow(win, frame)

        if title != last_title:
            try: cv2.setWindowTitle(win, title)
            except: pass
            last_title = title

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    try: cv2.destroyWindow(win)
    except: pass
