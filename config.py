import json
import os

CONFIG_FILE = "settings.json"

DEFAULT_CONFIG = {
    "auto_copy": True,
    "hotkey": "Alt+Q",
    "lang": "en", # 默认使用英文，因为用户强调英文识别
    "use_angle_cls": False,
    "use_gpu": False,
    "ocr_mode": "cpu"
}

def load_config():
    # Ensure relative to the script path
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE)
    if not os.path.exists(config_path):
        return DEFAULT_CONFIG.copy()
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            merged = DEFAULT_CONFIG.copy()
            merged.update(config)
            if "ocr_mode" not in config:
                merged["ocr_mode"] = "gpu" if merged.get("use_gpu", False) else "cpu"
            elif merged.get("ocr_mode") not in ("cpu", "gpu"):
                merged["ocr_mode"] = "gpu" if merged.get("use_gpu", False) else "cpu"
            return merged
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config):
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
