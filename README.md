# Win OCR v5

一个基于 Python、PySide6 和 PaddleOCR (PP-OCRv5) 开发的 Windows 桌面截图识别工具。

## 功能特点

- **快速截图识别**：通过界面按钮或全局热键快速触发截图并进行 OCR 识别。
- **高精度引擎**：使用百度开发的 PP-OCRv5 模型，提供极高的识别准确率。
- **多语言支持**：支持中英文混合、纯英文、日文以及韩文识别。
- **全局热键**：支持自定义全局热键（默认 `Alt+Q`），即使程序最小化也可快速调用。
- **自动处理**：识别结果可设置自动复制到剪贴板。
- **引擎切换**：支持 CPU 和 GPU (CUDA) 引擎切换，适应不同硬件环境。
- **方向校正**：内置文字方向分类器，支持旋转文字的准确识别。

## 软件界面

![软件预览](https://via.placeholder.com/600x400?text=Win+OCR+v5+Preview)

## 环境要求

- 操作系统：Windows 10/11
- Python 3.10+ (如果从源码运行)
- NVIDIA GPU (可选，用于 GPU 加速)

## 快速开始

### 源码运行

1. 克隆仓库：
   ```bash
   git clone https://github.com/ustak/Win-OCR_V5.git
   cd Win-OCR_V5
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 运行程序：
   ```bash
   python main.py
   ```

## 使用说明

1. 启动程序后，主界面显示识别预览和结果。
2. 点击“截图识别”或使用热键 `Alt+Q` 进入截图模式。
3. 拖动鼠标选择识别区域，松开后自动进行识别。
4. 识别结果将显示在下方的文本框中，并根据设置决定是否自动复制。
5. 在“设置”中可以更改识别语言、热键、引擎模式等。

## 贡献

欢迎提交 Issue 或 Pull Request 来改进本项目。

## 授权

[MIT License](LICENSE)
