import os
import random
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect, QPushButton, QFileDialog, QStackedWidget
from PyQt6.QtGui import QPixmap, QImage, QPalette, QBrush, QPainter, QPainterPath, QIcon
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, pyqtProperty, pyqtSignal, QEvent, QUrl, QSize, QRectF
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from utils.i18n import tr

def get_asset_path(filename):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, filename)

class ScrollableImageWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = None
        self.scroll_y = 0.0
        
    def setPixmap(self, pixmap):
        self.pixmap = pixmap
        self.update()
        
    def setScrollY(self, y):
        self.scroll_y = y
        self.update()
        
    def paintEvent(self, event):
        if not self.pixmap:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        path_shape = QPainterPath()
        path_shape.addRoundedRect(0, 0, self.width(), self.height(), 8, 8)
        painter.setClipPath(path_shape)
        
        x_offset = max(0, (self.pixmap.width() - self.width()) // 2)
        target_rect = QRectF(0, 0, self.width(), self.height())
        source_rect = QRectF(float(x_offset), float(self.scroll_y), float(self.width()), float(self.height()))
        painter.drawPixmap(target_rect, self.pixmap, source_rect)
        painter.end()

class PhotoWidget(QWidget):
    photo_changed = pyqtSignal(QPixmap)
    
    def _get_scroll_y(self):
        if not hasattr(self, '_scroll_y'):
            self._scroll_y = 0.0
        return self._scroll_y
        
    def _set_scroll_y(self, val):
        self._scroll_y = val
        if hasattr(self, 'image_label') and isinstance(self.image_label, ScrollableImageWidget):
            self.image_label.setScrollY(val)
        
    scroll_y = pyqtProperty(float, fget=_get_scroll_y, fset=_set_scroll_y)

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
        
        # Scroll animation for vertical photos
        self.scroll_anim = QPropertyAnimation(self, b"scroll_y")
        self.scroll_anim.finished.connect(self.next_photo)
        self.current_scaled_pixmap = None
        
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
        
        # Page 2: Photo/Video Display
        self.media_page = QWidget()
        media_layout = QVBoxLayout(self.media_page)
        media_layout.setContentsMargins(0, 0, 0, 0)
        
        # We need a stack for switching between image and video smoothly
        self.media_stack = QStackedWidget()
        media_layout.addWidget(self.media_stack)
        
        self.image_label = ScrollableImageWidget()
        self.image_label.setMinimumSize(1, 1)
        self.media_stack.addWidget(self.image_label)
        
        self.video_widget = QVideoWidget()
        self.media_stack.addWidget(self.video_widget)
        
        self.stack.addWidget(self.media_page)
        
        # Setup Video Player
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)
        
        # Global Mute State
        self.is_muted = True
        self.audio_output.setVolume(0.0)
        
        # End of media triggers next
        self.player.mediaStatusChanged.connect(self.on_media_status_changed)
        
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
            valid_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.mp4')
            for f in os.listdir(photo_dir):
                if f.lower().endswith(valid_extensions):
                    self.photos.append(os.path.join(photo_dir, f))
                    
        if self.photos:
            random.shuffle(self.photos)
            self.stack.setCurrentWidget(self.media_page)
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
        # Stop animations and timers first
        self.timer.stop()
        self.scroll_anim.stop()
        self.fade_out_anim.stop()
        self.fade_in_anim.stop()
        self.opacity_effect.setOpacity(1.0)
        
        # Determine if path is video or image
        if path.lower().endswith('.mp4'):
            self.media_stack.setCurrentWidget(self.video_widget)
            self.player.setSource(QUrl.fromLocalFile(path))
            self.player.play()
        else:
            self.media_stack.setCurrentWidget(self.image_label)
            self.player.stop()
            
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                # Scale to fit while keeping aspect ratio and expanding to fill
                self.current_scaled_pixmap = pixmap.scaled(
                    self.size(), 
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # Emit unrounded pixmap for background blur ONCE per photo
                self.photo_changed.emit(self.current_scaled_pixmap)
                
                # Check if it's a vertical photo
                img_aspect = self.current_scaled_pixmap.height() / self.current_scaled_pixmap.width()
                widget_aspect = self.height() / self.width()
                
                if img_aspect > widget_aspect * 1.2: 
                    # It's a vertical photo, animate scroll
                    max_scroll = max(0, self.current_scaled_pixmap.height() - self.height())
                    duration = max(5000, min(max_scroll * 10, 15000)) # e.g. 5 to 15 seconds
                    self.scroll_anim.setDuration(duration)
                    self.scroll_anim.setStartValue(0.0)
                    self.scroll_anim.setEndValue(float(max_scroll))
                    self.scroll_anim.start()
                else:
                    # Normal photo, static crop
                    y_offset = max(0, (self.current_scaled_pixmap.height() - self.height()) // 2)
                    self.scroll_y = y_offset
                    self.timer.start(self.interval_ms)
                    
                self.image_label.setPixmap(self.current_scaled_pixmap)
            else:
                # If load fails, try next one immediately
                self.next_photo()
                
    def on_media_status_changed(self, status):
        from PyQt6.QtMultimedia import QMediaPlayer
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.next_photo()

    def resizeEvent(self, event):
        # Refresh current image scale on resize
        if self.photos and self.current_index >= 0:
            current_path = self.photos[self.current_index]
            if not current_path.lower().endswith('.mp4'):
                self._set_image(current_path)
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
