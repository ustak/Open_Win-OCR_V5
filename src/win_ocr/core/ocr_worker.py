import os
import sys
import tempfile
import traceback
import logging
from pathlib import Path


def _inject_cuda_dll_search_paths():
    """Ensure Paddle can locate NVIDIA DLLs in source and PyInstaller modes."""
    candidate_roots = []
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            candidate_roots.append(Path(meipass))
    current_file_path = Path(__file__).resolve()
    # Now in src/win_ocr/core, root is 3 levels up
    project_root = current_file_path.parents[3] if current_file_path.parts[-4:] == ('src', 'win_ocr', 'core', 'ocr_worker.py') else current_file_path.parent
    candidate_roots.append(project_root)


    rel_dirs = [
        Path("nvidia") / "cuda_runtime" / "bin",
        Path("nvidia") / "cudnn" / "bin",
        Path("nvidia") / "cublas" / "bin",
        Path("nvidia") / "cufft" / "bin",
        Path("nvidia") / "curand" / "bin",
        Path("nvidia") / "cusolver" / "bin",
        Path("nvidia") / "cusparse" / "bin",
        Path("nvidia") / "nvjitlink" / "bin",
    ]

    added = []
    for root in candidate_roots:
        for base in [root, root / "python64" / "Lib" / "site-packages"]:
            for rel in rel_dirs:
                dll_dir = (base / rel).resolve()
                if dll_dir.exists():
                    added.append(str(dll_dir))

    if added:
        os.environ["PATH"] = os.pathsep.join(added + [os.environ.get("PATH", "")])
        for dll_dir in added:
            try:
                os.add_dll_directory(dll_dir)
            except Exception:
                pass


_inject_cuda_dll_search_paths()

import cv2
import numpy as np
import paddle
from paddleocr import PaddleOCR
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage, QPixmap
# Suppress debug logs from PaddleOCR to clear the console
logging.getLogger("ppocr").setLevel(logging.WARNING)
os.environ["FLAGS_use_mkldnn"] = "0"  # Prevent deep learning math pipeline generic crashes


def _patch_paddlex_dependency_check_for_frozen():
    """
    In PyInstaller onefile mode, importlib metadata may be incomplete, which can
    make paddlex extra-dependency checks fail even when modules are bundled.
    """
    if not getattr(sys, "frozen", False):
        return
    try:
        import paddlex.utils.deps as pdx_deps

        def _no_extra_check(*args, **kwargs):
            return

        pdx_deps.require_extra = _no_extra_check
    except Exception:
        pass


def _setup_offline_models():
    """
    Configure PaddleOCR and PaddleX to use bundled local models when running in
    PyInstaller frozen mode. This prevents the engine from trying to download
    models from the network.
    """
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            models_root = os.path.join(meipass, "models")
            
            # For PaddleX: expects models in {PADDLEX_HOME}/official_models
            paddlex_home = os.path.join(models_root, "paddlex")
            os.environ["PADDLEX_HOME"] = paddlex_home
            
            # For PaddleOCR: expects models in {PADDLE_HOME}/.paddleocr/whl
            paddle_home = os.path.join(models_root, "paddleocr")
            os.environ["PADDLE_HOME"] = paddle_home
            
            # Optional: ensure Paddle doesn't try to use any other paths
            # (Paddle often uses ~/.paddle_hook or similar, but PADDLE_HOME is the main one)


class OCREngine:
    """ Singleton for PaddleOCR to avoid reloading the model on every inference """
    _instances = {}
    _runtime_devices = {}
    _runtime_messages = {}

    @staticmethod
    def _is_gpu_available():
        try:
            if not paddle.device.is_compiled_with_cuda():
                return False, "当前安装的是 CPU 版 Paddle（非 GPU 版）"
            gpu_count = paddle.device.cuda.device_count()
            if gpu_count < 1:
                return False, "未检测到可用的 CUDA 显卡"
            return True, ""
        except Exception as e:
            return False, str(e)
    
    @classmethod
    def get_instance(cls, lang="en", use_angle_cls=False, engine_mode="cpu"):
        config_tuple = (lang, use_angle_cls, engine_mode)
        if config_tuple not in cls._instances:
            _setup_offline_models()
            _patch_paddlex_dependency_check_for_frozen()
            requested_device = "gpu" if engine_mode == "gpu" else "cpu"
            runtime_device = requested_device
            runtime_message = ""

            if requested_device == "gpu":
                gpu_ok, reason = cls._is_gpu_available()
                if not gpu_ok:
                    runtime_device = "cpu"
                    runtime_message = ("GPU 模式不可用，已自动切换到 CPU。\n" f"原因：{reason}\n" "如需启用 GPU，请安装与 CUDA/cuDNN 匹配的 paddlepaddle-gpu。")

            try:
                instance = PaddleOCR(
                    ocr_version="PP-OCRv5",
                    lang=lang,
                    device=runtime_device,
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False
                )
            except Exception as e:
                if runtime_device == "gpu":
                    runtime_device = "cpu"
                    runtime_message = ("GPU 初始化失败，已自动切换到 CPU。\n" f"原因：{e}\n" "请检查 CUDA/cuDNN 与 paddlepaddle-gpu 版本是否匹配。")
                    instance = PaddleOCR(
                        ocr_version="PP-OCRv5",
                        lang=lang,
                        device="cpu",
                        use_doc_orientation_classify=False,
                        use_doc_unwarping=False
                    )
                else:
                    raise
            cls._instances[config_tuple] = instance
            cls._runtime_devices[config_tuple] = runtime_device
            cls._runtime_messages[config_tuple] = runtime_message
        return (
            cls._instances[config_tuple],
            cls._runtime_devices.get(config_tuple, "cpu"),
            cls._runtime_messages.get(config_tuple, "")
        )

class OCRWorker(QThread):
    result_ready = Signal(str)
    error_occurred = Signal(str)
    engine_info = Signal(str)

    def __init__(self, pixmap: QPixmap, config: dict, parent=None):
        super().__init__(parent)
        self.image = pixmap.toImage()
        self.config = config
        self.init_error = None
        self.init_warning = None
        self.runtime_device = "cpu"
        self.ocr = None
        # Pre-initialize engine in the MAIN GUI thread to prevent PySide6 ONE-DNN multithreading crashes
        try:
            mode = self.config.get("ocr_mode")
            if mode not in ("cpu", "gpu"):
                mode = "gpu" if self.config.get("use_gpu", False) else "cpu"
            self.ocr, self.runtime_device, self.init_warning = OCREngine.get_instance(
                lang=self.config.get("lang", "en"),
                use_angle_cls=self.config.get("use_angle_cls", False),
                engine_mode=mode
            )
        except Exception as e:
            self.init_error = str(e)
            try:
                log_path = os.path.join(tempfile.gettempdir(), "win_ocr_v5_error.log")
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(traceback.format_exc())
            except Exception:
                pass

    def run(self):
        try:
            if self.init_error:
                self.error_occurred.emit(f"OCR 引擎初始化失败：{self.init_error}")
                return
            self.engine_info.emit(f"ENGINE_MODE:{self.runtime_device.upper()}")
            if self.init_warning:
                self.engine_info.emit(f"ENGINE_WARN:{self.init_warning}")

            # Convert QImage to RGB888 format
            formatted_image = self.image.convertToFormat(QImage.Format.Format_RGB888)
            
            width = formatted_image.width()
            height = formatted_image.height()
            
            ptr = formatted_image.constBits()
            bpl = formatted_image.bytesPerLine()
            
            arr = np.frombuffer(ptr, np.uint8)
            arr = arr.reshape((height, bpl))[:, :width * 3]
            img_rgb = arr.reshape((height, width, 3))
            
            # PaddleOCR internally uses cv2 which expects BGR, so we convert RGB to BGR
            img_bgr = img_rgb[:, :, ::-1].copy()
            
            # Preprocessing: Optional scaling to help with extremely small texts
            # With v5, the base accuracy is very high, but 1.5x scaling still helps
            # on high DPI displays capturing small text.
            img_bgr = cv2.resize(img_bgr, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)

            # Predict (V5 API uses predict instead of ocr)
            # `predict` yields a generator of results, one per image. Since we passed 1 image, we get the first item.
            prediction_list = list(self.ocr.predict(img_bgr))
            
            # Parse results (V5 PaddleX OCRResult format)
            text_lines = []
            if prediction_list and len(prediction_list) > 0:
                result = prediction_list[0]
                # The text sequences are stored in 'rec_texts' (or 'rec_text' in some versions)
                rec_texts = result.get("rec_texts", []) or result.get("rec_text", [])
                for text in rec_texts:
                    if text:
                        text_lines.append(text)
                    
            final_text = "\n".join(text_lines)
            if not final_text:
                final_text = "未检测到文字"
                
            self.result_ready.emit(final_text)

        except Exception as e:
            try:
                log_path = os.path.join(tempfile.gettempdir(), "win_ocr_v5_error.log")
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(traceback.format_exc())
            except Exception:
                pass
            self.error_occurred.emit(f"OCR 运行失败：{e}")


