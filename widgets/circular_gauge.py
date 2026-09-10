import sys
from PyQt6.QtWidgets import QWidget, QApplication, QVBoxLayout, QHBoxLayout
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QPen, QFont, QFontDatabase
from PyQt6.QtCore import Qt, QPropertyAnimation, pyqtProperty, pyqtSignal, QRectF

class CircularGauge(QWidget):
    def __init__(self, title="CPU", color=QColor(85, 170, 255), warning_color=QColor(255, 85, 85), parent=None):
        super().__init__(parent)
        self.title = title
        self.default_color = color
        self.warning_color = warning_color
        
        self._value = 0
        self._animated_value = 0.0
        self.thickness = 15
        
        self.animation = QPropertyAnimation(self, b"animated_value")
        self.animation.setDuration(1000) # 1 second smooth transition
        
        self.setMinimumSize(120, 120)

    def set_value(self, val):
        self._value = max(0, min(val, 100))
        
        self.animation.stop()
        self.animation.setStartValue(self._animated_value)
        self.animation.setEndValue(float(self._value))
        self.animation.start()

    @pyqtProperty(float)
    def animated_value(self):
        return self._animated_value

    @animated_value.setter
    def animated_value(self, val):
        self._animated_value = val
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        size = min(width, height) - self.thickness * 2
        
        rect = QRectF(
            (width - size) / 2,
            (height - size) / 2,
            size,
            size
        )

        # Draw background ring (transparent/dark)
        bg_pen = QPen(QColor(255, 255, 255, 30))
        bg_pen.setWidth(self.thickness)
        bg_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(bg_pen)
        painter.drawArc(rect, 0, 360 * 16)

        # Decide color based on value
        current_color = self.warning_color if self._animated_value >= 85 else self.default_color

        # Draw progress ring
        prog_pen = QPen(current_color)
        prog_pen.setWidth(self.thickness)
        prog_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(prog_pen)
        
        # Qt drawArc angles are in 1/16th of a degree. 90 degrees starts at 3 o'clock.
        # We want to start at 90 degrees (12 o'clock) and go clockwise (negative angle).
        # Actually in Qt, 0 is 3 o'clock, 90 is 12 o'clock, 180 is 9 o'clock.
        # Wait, Qt angles: 0 is 3 o'clock, positive is counter-clockwise.
        # So 90 is 12 o'clock. We want to draw clockwise, so negative span angle.
        start_angle = 90 * 16
        span_angle = int(-self._animated_value * 3.6 * 16)
        painter.drawArc(rect, start_angle, span_angle)

        # Draw Text
        painter.setPen(QColor(255, 255, 255, 220))
        
        # Value Text
        font_value = self.font()
        font_value.setPointSize(max(10, int(size / 4.5)))
        font_value.setBold(True)
        painter.setFont(font_value)
        value_rect = QRectF(rect.x(), rect.y() + size * 0.1, rect.width(), rect.height() * 0.6)
        painter.drawText(value_rect, Qt.AlignmentFlag.AlignCenter, f"{int(self._animated_value)}%")

        # Title Text
        font_title = self.font()
        font_title.setPointSize(max(8, int(size / 8)))
        font_title.setBold(False)
        painter.setFont(font_title)
        title_rect = QRectF(rect.x(), rect.y() + size * 0.55, rect.width(), rect.height() * 0.4)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self.title)

        painter.end()

class SystemMonitorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("metro_tile")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # CPU Gauge - blue/purple theme
        self.cpu_gauge = CircularGauge("CPU", color=QColor(138, 43, 226)) # BlueViolet
        
        # RAM Gauge - green/teal theme
        self.ram_gauge = CircularGauge("RAM", color=QColor(0, 206, 209)) # DarkTurquoise
        
        layout.addWidget(self.cpu_gauge)
        layout.addWidget(self.ram_gauge)
        
    def update_stats(self, cpu_percent, ram_percent):
        self.cpu_gauge.set_value(cpu_percent)
        self.ram_gauge.set_value(ram_percent)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = SystemMonitorWidget()
    w.setStyleSheet("background-color: #1e1e1e;")
    w.resize(400, 200)
    w.show()
    w.update_stats(45, 88)
    sys.exit(app.exec())
