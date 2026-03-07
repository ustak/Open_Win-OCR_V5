from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtGui import QPainter, QColor, QPen, QScreen, QPixmap
from PySide6.QtCore import Qt, QRect, Signal

class ScreenshotWidget(QWidget):
    screenshot_taken = Signal(QPixmap)

    def __init__(self):
        super().__init__()
        # Set window flags to cover screen, stay on top, and no frame
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)

        self.start_pos = None
        self.end_pos = None
        self.is_drawing = False

        # Capture the entire primary screen
        screen = QApplication.primaryScreen()
        self.original_pixmap = screen.grabWindow(0)
        self.setGeometry(screen.geometry())

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # 1. Draw the original background
        painter.drawPixmap(0, 0, self.original_pixmap)
        
        # 2. Draw a semi-transparent black overlay
        dim_color = QColor(0, 0, 0, 100)
        painter.fillRect(self.rect(), dim_color)

        # 3. If drawing, clear the selected area and draw border
        if self.is_drawing and self.start_pos and self.end_pos:
            rect = QRect(self.start_pos, self.end_pos).normalized()
            
            # Use CompositionMode to clear the dim overlay in the selection
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(rect, Qt.GlobalColor.transparent)
            
            # Redraw that part of original snapshot
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.drawPixmap(rect, self.original_pixmap, rect)
            
            # Draw blue border with v5 style
            painter.setPen(QPen(QColor(0, 150, 255), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.position().toPoint()
            self.end_pos = self.start_pos
            self.is_drawing = True
            self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            self.close() # Cancel screenshot on right-click

    def mouseMoveEvent(self, event):
        if self.is_drawing:
            self.end_pos = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_drawing:
            self.end_pos = event.position().toPoint()
            self.is_drawing = False
            
            rect = QRect(self.start_pos, self.end_pos).normalized()
            # Ensure the selection is not too small
            if rect.width() > 10 and rect.height() > 10:
                captured_pixmap = self.original_pixmap.copy(rect)
                self.screenshot_taken.emit(captured_pixmap)
            
            self.close()
            
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
