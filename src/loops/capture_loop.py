def run(cap, frame_q, state, stop_flag, sample_every):
    f_i = 0
    while not stop_flag["flag"]:
        ok, frame = cap.read()
        if not ok: continue
        f_i += 1
        with state.lock:
            state.last_frame = frame.copy()
        if f_i % sample_every == 0 and not frame_q.full():
            frame_q.put(frame)
