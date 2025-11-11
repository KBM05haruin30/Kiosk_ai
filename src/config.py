import yaml, os

def load_config(path=r"D:\kiosk_ai\config\pipeline.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # 필수 키 존재/기본값 처리
    cfg.setdefault("inference", {})
    cfg.setdefault("defaults", {})
    cfg.setdefault("runtime", {})
    cfg["inference"].setdefault("sample_every_n_frames", 1)
    cfg["inference"].setdefault("male_threshold", 0.5)
    cfg["inference"].setdefault("age_cutoff_years", 50)
    cfg["inference"].setdefault("hysteresis_sec", 2.0)
    cfg["runtime"].setdefault("providers", ["DmlExecutionProvider","CPUExecutionProvider"])

    return cfg
