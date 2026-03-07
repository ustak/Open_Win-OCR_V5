# Win OCR v5

A Windows desktop screenshot recognition tool based on Python, PySide6, and PaddleOCR (PP-OCRv5).

## Features

- **Quick Screenshot Recognition**: Quickly trigger screenshots and perform OCR via the UI button or global hotkeys.
- **High-Precision Engine**: Utilizes the PP-OCRv5 model developed by Baidu for extremely high recognition accuracy.
- **Multi-language Support**: Supports Chinese-English mixed, pure English, Japanese, and Korean recognition.
- **Global Hotkeys**: Supports customizable global hotkeys (default `Alt+Q`), allowing quick access even when the app is minimized.
- **Automatic Processing**: Recognition results can be set to automatically copy to the clipboard.
- **Engine Switching**: Supports switching between CPU and GPU (CUDA) engines to adapt to different hardware environments.
- **Direction Correction**: Built-in text direction classifier supports accurate recognition of rotated text.

## UI Preview

![UI Preview](https://via.placeholder.com/600x400?text=Win+OCR+v5+Preview)

## Requirements

- OS: Windows 10/11
- Python 3.10+ (if running from source)
- NVIDIA GPU (optional, for GPU acceleration)

## Quick Start

### Running from Source

1. Clone the repository:

   ```bash
   git clone https://github.com/ustak/Win-OCR_V5.git
   cd Win-OCR_V5
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:

   ```bash
   python main.py
   ```

## Usage

1. After launching the program, the main interface shows the recognition preview and results.
2. Click "Screenshot Recognition" or use the hotkey `Alt+Q` to enter screenshot mode.
3. Drag the mouse to select the area for recognition; it will automatically start OCR after release.
4. Recognition results will appear in the text box below, and will be auto-copied based on your settings.
5. In "Settings," you can change the recognition language, hotkeys, engine mode, and more.

## Contribution

Issues and Pull Requests are welcome to improve this project.

## License

[MIT License](LICENSE)
