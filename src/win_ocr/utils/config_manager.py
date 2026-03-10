import json
import os
import sys

CONFIG_FILE = "settings.json"

DEFAULT_CONFIG = {
    "auto_copy": True,
    "hotkey": "Alt+Q",
    "lang": "en",  # 默认使用英文
    "use_angle_cls": False,
    "use_gpu": False,
    "ocr_mode": "cpu"
}

def get_config_path():
    """Get the absolute path to settings.json in the project root."""
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        # File is at src/win_ocr/utils/config_manager.py, root is 3 levels up
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    return os.path.join(base_dir, CONFIG_FILE)

def load_config():
    config_path = get_config_path()
    if not os.path.exists(config_path):
        return DEFAULT_CONFIG.copy()
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            merged = DEFAULT_CONFIG.copy()
            merged.update(config)
            # Compatibility check
            if "ocr_mode" not in config:
                merged["ocr_mode"] = "gpu" if merged.get("use_gpu", False) else "cpu"
            elif merged.get("ocr_mode") not in ("cpu", "gpu"):
                merged["ocr_mode"] = "gpu" if merged.get("use_gpu", False) else "cpu"
            return merged
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config):
    config_path = get_config_path()
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception:
        pass
