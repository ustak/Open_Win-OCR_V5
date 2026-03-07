import sys
import os
import ctypes
import ctypes.wintypes

# Set env vars before Paddle/OpenCV import.
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QTextEdit,
    QLabel,
    QHBoxLayout,
    QMessageBox,
    QDialog,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QLineEdit,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap

from screenshot_widget import ScreenshotWidget
from ocr_worker import OCRWorker
from config import load_config, save_config

user32 = ctypes.windll.user32
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
WM_HOTKEY = 0x0312


def parse_hotkey(hotkey_str):
    mods = 0
    vk = 0
    parts = hotkey_str.upper().split("+")
    for part in parts:
        part = part.strip()
        if part == "ALT":
            mods |= MOD_ALT
        elif part == "CTRL":
            mods |= MOD_CONTROL
        elif part == "SHIFT":
            mods |= MOD_SHIFT
        elif part == "WIN":
            mods |= MOD_WIN
        else:
            if len(part) == 1:
                vk = ord(part)
            elif part.startswith("F") and part[1:].isdigit():
                vk = 0x70 + int(part[1:]) - 1
    return mods, vk


class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Win OCR v5 - 设置")
        self.config = config
        self.resize(400, 260)

        layout = QFormLayout(self)

        self.chk_auto_copy = QCheckBox("识别后自动复制结果")
        self.chk_auto_copy.setChecked(config.get("auto_copy", True))

        self.txt_hotkey = QLineEdit()
        self.txt_hotkey.setText(config.get("hotkey", "Alt+Q"))
        self.txt_hotkey.setPlaceholderText("例如：Alt+Q / Ctrl+Shift+Q / F4")

        self.cmb_lang = QComboBox()
        self.cmb_lang.addItems(
            [
                "en（英文，速度快）",
                "ch（中英混合）",
                "japan（日文）",
                "korean（韩文）",
            ]
        )
        lang_map = {"en": 0, "ch": 1, "japan": 2, "korean": 3}
        self.cmb_lang.setCurrentIndex(lang_map.get(config.get("lang", "en"), 0))

        self.chk_angle = QCheckBox("启用文字方向校正")
        self.chk_angle.setChecked(config.get("use_angle_cls", False))

        self.cmb_engine = QComboBox()
        self.cmb_engine.addItems(
            [
                "CPU（稳定，速度较慢）",
                "GPU（更快，需已配置 CUDA + GPU 版 Paddle）",
            ]
        )
        current_mode = config.get("ocr_mode")
        if current_mode not in ("cpu", "gpu"):
            current_mode = "gpu" if config.get("use_gpu", False) else "cpu"
        self.cmb_engine.setCurrentIndex(1 if current_mode == "gpu" else 0)

        layout.addRow("自动复制：", self.chk_auto_copy)
        layout.addRow("全局热键：", self.txt_hotkey)
        layout.addRow("识别语言：", self.cmb_lang)
        layout.addRow("方向校正：", self.chk_angle)
        layout.addRow("引擎模式：", self.cmb_engine)

        btn_save = QPushButton("保存设置")
        btn_save.setMinimumHeight(36)
        btn_save.clicked.connect(self.save_and_close)
        layout.addRow("", btn_save)

    def save_and_close(self):
        lang_values = ["en", "ch", "japan", "korean"]
        self.config["auto_copy"] = self.chk_auto_copy.isChecked()
        self.config["hotkey"] = self.txt_hotkey.text().strip()
        self.config["lang"] = lang_values[self.cmb_lang.currentIndex()]
        self.config["use_angle_cls"] = self.chk_angle.isChecked()
        selected_mode = "gpu" if self.cmb_engine.currentIndex() == 1 else "cpu"
        self.config["ocr_mode"] = selected_mode
        self.config["use_gpu"] = selected_mode == "gpu"
        save_config(self.config)
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Win OCR v5 (PP-OCRv5)")
        self.resize(600, 680)

        self.config = load_config()
        self.screenshot_widget = None
        self.ocr_worker = None
        self.hotkey_registered = False
        self.last_engine_warn = ""

        mode = self.config.get("ocr_mode")
        if mode not in ("cpu", "gpu"):
            mode = "gpu" if self.config.get("use_gpu", False) else "cpu"
        self.current_engine_mode = mode.upper()

        self.init_ui()
        self.register_hotkey()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self.lbl_preview = QLabel("")
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview.setStyleSheet(
            """
            QLabel {
                background-color: #f8f9fa;
                border: 2px dashed #0078d7;
                border-radius: 8px;
                color: #555;
                font-size: 14px;
                font-weight: bold;
            }
        """
        )
        self.lbl_preview.setMinimumHeight(180)
        self.update_preview_label()
        layout.addWidget(self.lbl_preview)

        btn_layout = QHBoxLayout()
        self.btn_screenshot = QPushButton("截图识别")
        self.btn_screenshot.setMinimumHeight(45)
        self.btn_screenshot.setStyleSheet(
            """
            QPushButton {
                background-color: #0078d7;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #005a9e; }
        """
        )
        self.btn_screenshot.clicked.connect(self.start_screenshot)

        self.btn_copy = QPushButton("复制文本")
        self.btn_copy.setMinimumHeight(45)
        self.btn_copy.setStyleSheet(
            """
            QPushButton {
                background-color: #2b88d8;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #1e71b8; }
        """
        )
        self.btn_copy.clicked.connect(self.copy_to_clipboard)

        self.btn_settings = QPushButton("设置")
        self.btn_settings.setMinimumHeight(45)
        self.btn_settings.setStyleSheet(
            """
            QPushButton {
                font-weight: bold;
                border-radius: 6px;
                font-size: 14px;
            }
        """
        )
        self.btn_settings.clicked.connect(self.open_settings)

        btn_layout.addWidget(self.btn_screenshot)
        btn_layout.addWidget(self.btn_copy)
        btn_layout.addWidget(self.btn_settings)
        layout.addLayout(btn_layout)

        hotkey_hint = self.config.get("hotkey", "Alt+Q")
        self.txt_result = QTextEdit()
        self.txt_result.setPlaceholderText(
            f"欢迎使用 Win OCR v5。\n\n"
            f"提示：最小化后可按 {hotkey_hint} 进行截图识别。\n\n"
            f"识别结果会显示在这里。"
        )
        self.txt_result.setStyleSheet(
            """
            QTextEdit {
                font-size: 15px;
                line-height: 1.6;
                border-radius: 6px;
                border: 1px solid #ccc;
                padding: 5px;
            }
        """
        )
        layout.addWidget(self.txt_result)

    def register_hotkey(self):
        if self.hotkey_registered:
            user32.UnregisterHotKey(int(self.winId()), 1)
            self.hotkey_registered = False

        hotkey_str = self.config.get("hotkey", "Alt+Q")
        if not hotkey_str:
            return

        mods, vk = parse_hotkey(hotkey_str)
        if vk != 0:
            if user32.RegisterHotKey(int(self.winId()), 1, mods, vk):
                self.hotkey_registered = True

        self.txt_result.setPlaceholderText(
            f"欢迎使用 Win OCR v5。\n\n"
            f"提示：最小化后可按 {hotkey_str} 进行截图识别。\n\n"
            f"识别结果会显示在这里。"
        )

    def _requested_engine_mode(self):
        mode = self.config.get("ocr_mode")
        if mode not in ("cpu", "gpu"):
            mode = "gpu" if self.config.get("use_gpu", False) else "cpu"
        return mode.upper()

    def update_preview_label(self):
        lang = self.config.get("lang", "en").upper()
        req_mode = self._requested_engine_mode()
        self.lbl_preview.setText(
            f"截图预览区\n引擎: PP-OCRv5 | 语言: {lang}\n请求模式: {req_mode} | 实际运行: {self.current_engine_mode}"
        )

    def open_settings(self):
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            self.current_engine_mode = self._requested_engine_mode()
            self.register_hotkey()
            self.update_preview_label()

    def start_screenshot(self):
        if self.screenshot_widget is not None and self.screenshot_widget.isVisible():
            return
        self.hide()
        QTimer.singleShot(200, self._show_screenshot_overlay)

    def _show_screenshot_overlay(self):
        self.screenshot_widget = ScreenshotWidget()
        self.screenshot_widget.screenshot_taken.connect(self.process_screenshot)
        self.screenshot_widget.destroyed.connect(self.show)
        self.screenshot_widget.show()

    def process_screenshot(self, pixmap: QPixmap):
        try:
            self.screenshot_widget.destroyed.disconnect(self.show)
        except Exception:
            pass
        self.show()
        self.activateWindow()

        scaled_pixmap = pixmap.scaled(
            self.lbl_preview.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.lbl_preview.setPixmap(scaled_pixmap)

        self.txt_result.setText("正在识别，请稍候...")
        self.btn_screenshot.setEnabled(False)
        self.btn_screenshot.setText("识别中...")

        self.ocr_worker = OCRWorker(pixmap, self.config)
        self.ocr_worker.result_ready.connect(self.on_ocr_success)
        self.ocr_worker.error_occurred.connect(self.on_ocr_error)
        self.ocr_worker.engine_info.connect(self.on_engine_info)
        self.ocr_worker.finished.connect(self.on_worker_finished)
        self.ocr_worker.start()

    def on_ocr_success(self, text):
        self.txt_result.setText(text)
        if self.config.get("auto_copy", True):
            self.copy_to_clipboard(silent=True)

    def on_ocr_error(self, err_msg):
        QMessageBox.critical(self, "识别错误", f"OCR 发生错误：\n{err_msg}")
        self.txt_result.setText("")

    def on_engine_info(self, info):
        if info.startswith("ENGINE_MODE:"):
            self.current_engine_mode = info.split(":", 1)[1].strip().upper()
            self.update_preview_label()
        elif info.startswith("ENGINE_WARN:"):
            msg = info.split(":", 1)[1].strip()
            if msg != self.last_engine_warn:
                self.last_engine_warn = msg
                QMessageBox.warning(self, "引擎回退", msg)

    def on_worker_finished(self):
        self.btn_screenshot.setEnabled(True)
        self.btn_screenshot.setText("截图识别")

    def copy_to_clipboard(self, silent=False):
        clipboard = QApplication.clipboard()
        text = self.txt_result.toPlainText()
        if text.strip():
            clipboard.setText(text)
            original_text = self.btn_copy.text()
            self.btn_copy.setText("已复制")
            QTimer.singleShot(1500, lambda: self.btn_copy.setText(original_text))

    def nativeEvent(self, eventType, message):
        try:
            msg = ctypes.wintypes.MSG.from_address(message.__int__())
            if msg.message == WM_HOTKEY and msg.wParam == 1:
                self.start_screenshot()
                return True, 0
        except Exception:
            pass
        return super().nativeEvent(eventType, message)

    def closeEvent(self, event):
        if self.hotkey_registered:
            user32.UnregisterHotKey(int(self.winId()), 1)
        event.accept()


if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
