import os
import random
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect, QPushButton, QFileDialog, QStackedWidget
from PyQt6.QtGui import QPixmap, QImage, QPalette, QBrush, QPainter, QPainterPath
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, pyqtProperty, pyqtSignal, QEvent
from utils.i18n import tr

class PhotoWidget(QWidget):
    photo_changed = pyqtSignal(QPixmap)

    def __init__(self, config, interval_ms=10000, parent=None):
        super().__init__(parent)
        self.config = config
        self.interval_ms = interval_ms
        self.photos = []
        self.current_index = -1
        
        # For long press detection
        self.press_timer = QTimer(self)
        self.press_timer.setSingleShot(True)
        self.press_timer.timeout.connect(self.on_long_press)
        
        # UI Setup
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Stack to switch between button and photo
        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)
        
        # Accept touch events
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        
        # Page 1: Empty state / Browse button
        self.empty_page = QWidget()
        empty_layout = QVBoxLayout(self.empty_page)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.empty_label = QLabel(tr("No photos selected or folder is empty."))
        self.empty_label.setStyleSheet("color: white; font-size: 24px; margin-bottom: 20px;")
        empty_layout.addWidget(self.empty_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.browse_btn = QPushButton(tr("Browse Folder"))
        self.browse_btn.setFixedSize(200, 50)
        self.browse_btn.setStyleSheet("font-size: 18px;")
        self.browse_btn.clicked.connect(self.select_folder)
        empty_layout.addWidget(self.browse_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.stack.addWidget(self.empty_page)
        
        # Page 2: Photo Display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(1, 1)
        self.stack.addWidget(self.image_label)
        
        # Effect for fade transition
        self.opacity_effect = QGraphicsOpacityEffect(self.image_label)
        self.image_label.setGraphicsEffect(self.opacity_effect)
        
        self.fade_out_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_anim.setDuration(800)
        self.fade_out_anim.setStartValue(1.0)
        self.fade_out_anim.setEndValue(0.0)
        self.fade_out_anim.finished.connect(self._on_fade_out_finished)
        
        self.fade_in_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_anim.setDuration(800)
        self.fade_in_anim.setStartValue(0.0)
        self.fade_in_anim.setEndValue(1.0)

        # Timer for rotation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_photo)
        
        self.load_photos()

    def select_folder(self):
        # Open folder dialog
        directory = QFileDialog.getExistingDirectory(self, tr("Select Photo Directory"), self.config.get_photo_dir() or os.path.expanduser("~"))
        if directory:
            self.config.set_photo_dir(directory)
            self.load_photos()

    def load_photos(self):
        self.photos = []
        photo_dir = self.config.get_photo_dir()
        
        if photo_dir and os.path.exists(photo_dir):
            valid_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.bmp')
            for f in os.listdir(photo_dir):
                if f.lower().endswith(valid_extensions):
                    self.photos.append(os.path.join(photo_dir, f))
                    
        if self.photos:
            random.shuffle(self.photos)
            self.stack.setCurrentWidget(self.image_label)
            self.current_index = 0
            self._set_image(self.photos[0])
            self.timer.start(self.interval_ms)
        else:
            self.timer.stop()
            self.stack.setCurrentWidget(self.empty_page)

    def next_photo(self):
        if not self.photos:
            return
        self.fade_out_anim.start()

    def _on_fade_out_finished(self):
        self.current_index = (self.current_index + 1) % len(self.photos)
        self._set_image(self.photos[self.current_index])
        self.fade_in_anim.start()

    def _set_image(self, path):
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            # Scale to fit while keeping aspect ratio and expanding to fill
            scaled_pixmap = pixmap.scaled(
                self.size(), 
                Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Crop to center
            x_offset = max(0, (scaled_pixmap.width() - self.width()) // 2)
            y_offset = max(0, (scaled_pixmap.height() - self.height()) // 2)
            cropped_pixmap = scaled_pixmap.copy(x_offset, y_offset, self.width(), self.height())
            
            # Apply rounded corners
            rounded_pixmap = QPixmap(self.width(), self.height())
            rounded_pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(rounded_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            path = QPainterPath()
            path.addRoundedRect(0, 0, self.width(), self.height(), 8, 8) # Match the 8px from QSS
            
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, cropped_pixmap)
            painter.end()
            
            self.image_label.setPixmap(rounded_pixmap)
            self.photo_changed.emit(cropped_pixmap) # Pass unrounded for background blur
        else:
            # If load fails, try next one immediately
            self.next_photo()

    def resizeEvent(self, event):
        # Refresh current image scale on resize
        if self.photos and self.current_index >= 0:
            self._set_image(self.photos[self.current_index])
        super().resizeEvent(event)

    # Long Press Implementation
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.press_timer.start(1000) # 1 second long press
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.press_timer.isActive():
                self.press_timer.stop()
        super().mouseReleaseEvent(event)

    def event(self, event):
        if event.type() == QEvent.Type.TouchBegin:
            self.press_timer.start(1000)
            return True
        elif event.type() in (QEvent.Type.TouchEnd, QEvent.Type.TouchCancel):
            if self.press_timer.isActive():
                self.press_timer.stop()
            return True
        return super().event(event)
        
    def on_long_press(self):
        self.select_folder()
