import time
from categories import to_category

def run(engine, cfg, paths, player, frame_q, state, stop_flag):
    INF = cfg["inference"]
    TH_MALE = INF["male_threshold"]; AGE_CUT = INF["age_cutoff_years"]; HYST_SEC = INF["hysteresis_sec"]
    PRESENCE_WARMUP_SEC, PRESENCE_ON_FRAMES, PRESENCE_OFF_FRAMES = 1.0, 3, 6
    POST_END_SCAN_SEC, POST_END_NEED_ON, POST_END_MIN_STABLE = 1.2, 2, 0.6

    fallback = paths["fallback_path"]
    last_cat, stable_since = None, None
    current_playing_cat = cfg["defaults"]["fallback_category"]
    present_count = absent_count = 0
    in_presence = False
    presence_since = 0.0

    ema_male, ema_age, ALPHA = 0.5, 30.0, 0.25

    # post-scan temp vars
    post_present_run, post_candidate, post_candidate_since = 0, None, 0.0

    while not stop_flag["flag"]:
        # consume frame
        frame = frame_q.get()
        now = time.time()

        # on_end 플래그 소거 (즉시 폴백 안함 — post_scan에서 판단)
        with state.lock:
            if state.ended:
                state.ended = False

        best_box, best_attrs, all_boxes = engine.attrs_for_largest(frame)
        with state.lock:
            state.faces = all_boxes
            in_post = state.post_scan
            post_deadline = state.post_deadline

        # post-scan
        if in_post:
            if best_box is None:
                present_count = 0
            else:
                present_count += 1
                cat_now = to_category(best_attrs["male_prob"], best_attrs["age_years"], TH_MALE, AGE_CUT)
                if cat_now != post_candidate:
                    post_candidate, post_candidate_since, post_present_run = cat_now, now, 1
                    print(f"[post-scan] candidate='{cat_now}' (collecting...)")
                else:
                    post_present_run += 1

            decision_ready = (post_candidate is not None and
                              post_present_run >= POST_END_NEED_ON and
                              (now - post_candidate_since) >= POST_END_MIN_STABLE)
            timeout = (now >= post_deadline)

            if decision_ready or timeout:
                with state.lock:
                    state.post_scan = False

                if post_candidate is None or present_count == 0:
                    print("[post-scan] no person → fallback")
                    player.switch_folder(fallback)
                    current_playing_cat = cfg["defaults"]["fallback_category"]
                    with state.lock: state.current_cat = current_playing_cat
                else:
                    target = post_candidate
                    print(f"[post-scan] decision='{target}' (once)")
                    player.switch_folder(paths["cats"][target], once=True)
                    current_playing_cat = target
                    with state.lock:
                        state.current_cat = target
                        state.locked = True

                post_candidate, post_candidate_since, post_present_run, present_count = None, 0.0, 0, 0
            continue

        # 일반 모드
        if best_box is None:
            present_count = 0
            absent_count += 1
            if in_presence and absent_count >= PRESENCE_OFF_FRAMES:
                in_presence = False
                print("[presence] now ABSENT")
            continue

        absent_count = 0
        present_count += 1
        if not in_presence and present_count >= PRESENCE_ON_FRAMES:
            in_presence = True
            presence_since = now
            print("[presence] now PRESENT (warmup)")

        male_p = float(best_attrs["male_prob"]); age_y = float(best_attrs["age_years"])
        ema_male = (1-ALPHA)*ema_male + ALPHA*male_p
        ema_age  = (1-ALPHA)*ema_age  + ALPHA*age_y
        with state.lock:
            state.ema_male, state.ema_age = ema_male, ema_age

        cat = to_category(ema_male, ema_age, TH_MALE, AGE_CUT)

        if cat != last_cat:
            last_cat, stable_since = cat, now
            print(f"[hys] candidate='{cat}' (stabilizing...)")
            continue

        if (now - presence_since) < PRESENCE_WARMUP_SEC:
            continue

        if stable_since and (now - stable_since) >= HYST_SEC:
            with state.lock:
                if state.locked:
                    continue
            if current_playing_cat != cat:
                print(f"[switch] {current_playing_cat} -> {cat} (once)")
                player.switch_folder(paths["cats"][cat], once=True)
                current_playing_cat = cat
                with state.lock:
                    state.current_cat = cat
                    state.locked = True
