import sys
import psutil
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QGraphicsBlurEffect, QApplication, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, QDate
from PyQt6.QtGui import QPixmap, QIcon

from widgets.photo_widget import PhotoWidget
from widgets.circular_gauge import SystemMonitorWidget
from widgets.calendar_widget import CalendarWidget
from widgets.memo_list_widget import MemoListWidget
from dialogs.memo_dialog import MemoDialog
from models.memo_manager import MemoManager
from utils.config import Config

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.config = Config()
        self.memo_manager = MemoManager()
        
        self.setWindowTitle("Smart Digital Photo Frame")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.showFullScreen()
        
        import os
        if os.path.exists("icon.ico"):
            self.setWindowIcon(QIcon("icon.ico"))
            
        # Base Widget and Layout
        base_widget = QWidget(self)
        self.setCentralWidget(base_widget)
        base_layout = QVBoxLayout(base_widget)
        base_layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Blurred Background Layer
        self.bg_label = QLabel(base_widget)
        self.bg_label.setScaledContents(True)
        # We need the bg_label to cover the entire window underneath everything else.
        # Since it's absolutely positioned, we will handle resizing in resizeEvent.
        self.bg_label.lower()
        
        self.blur_effect = QGraphicsBlurEffect(self.bg_label)
        self.blur_effect.setBlurRadius(80) # High blur for frosted glass effect
        self.bg_label.setGraphicsEffect(self.blur_effect)
        
        # 2. Main Overlay Layout
        self.overlay_widget = QWidget(base_widget)
        base_layout.addWidget(self.overlay_widget)
        
        main_layout = QHBoxLayout(self.overlay_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(25)
        
        # Detect screen aspect ratio
        screen = QApplication.primaryScreen().geometry()
        aspect_ratio = screen.width() / screen.height()
        
        # Left Panel Container
        self.left_panel = QWidget()
        self.left_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.left_panel.setMinimumSize(1, 1)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(25)
        
        # 1. Top Half (Photo Gallery)
        self.photo_panel = QFrame()
        self.photo_panel.setObjectName("metro_tile")
        self.photo_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        photo_layout = QVBoxLayout(self.photo_panel)
        photo_layout.setContentsMargins(0, 0, 0, 0)
        
        self.photo_widget = PhotoWidget(self.config)
        self.photo_widget.photo_changed.connect(self.update_background)
        photo_layout.addWidget(self.photo_widget)
        
        left_layout.addWidget(self.photo_panel, stretch=1)
        
        # 2. Bottom Half (Games)
        self.games_container = QWidget()
        self.games_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        games_layout = QHBoxLayout(self.games_container)
        games_layout.setContentsMargins(0, 0, 0, 0)
        games_layout.setSpacing(25)
        
        from widgets.snake_widget import SnakeWidget
        self.snake_widget = SnakeWidget()
        games_layout.addWidget(self.snake_widget, stretch=1)
        
        from widgets.tetris_widget import TetrisWidget
        self.tetris_widget = TetrisWidget()
        games_layout.addWidget(self.tetris_widget, stretch=1)
        
        left_layout.addWidget(self.games_container, stretch=1)
        
        main_layout.addWidget(self.left_panel, stretch=7)
        
        # Right Panel (Dashboard)
        self.right_panel = QFrame()
        self.right_panel.setObjectName("right_panel")
        self.right_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.right_panel.setMinimumSize(1, 1)
        
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(25) # Increase spacing between tiles
        
        # 1. System Monitors Tile
        sys_tile = QFrame()
        sys_tile.setObjectName("metro_tile")
        sys_layout = QVBoxLayout(sys_tile)
        sys_layout.setContentsMargins(0, 0, 0, 0)
        self.sys_monitor = SystemMonitorWidget()
        sys_layout.addWidget(self.sys_monitor)
        right_layout.addWidget(sys_tile, stretch=2)
        
        # 2. Today's Tasks Tile
        memo_tile = QFrame()
        memo_tile.setObjectName("metro_tile")
        memo_layout = QVBoxLayout(memo_tile)
        memo_layout.setContentsMargins(0, 0, 0, 0)
        self.memo_list = MemoListWidget(self.memo_manager)
        memo_layout.addWidget(self.memo_list)
        right_layout.addWidget(memo_tile, stretch=5)
        
        # 3. Calendar Tile
        cal_tile = QFrame()
        cal_tile.setObjectName("metro_tile")
        cal_layout = QVBoxLayout(cal_tile)
        cal_layout.setContentsMargins(15, 15, 15, 15)
        self.calendar = CalendarWidget(self.memo_manager)
        self.calendar.date_clicked.connect(self.open_memo_dialog)
        cal_layout.addWidget(self.calendar)
        right_layout.addWidget(cal_tile, stretch=3)
        
        main_layout.addWidget(self.right_panel, stretch=3)
        
        # System stats update timer
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self.update_system_stats)
        self.stats_timer.start(2000) # Every 2 seconds
        self.update_system_stats()

    def update_background(self, pixmap: QPixmap):
        # Update the background with the current photo
        self.bg_label.setPixmap(pixmap)
        # Re-apply geometry in case it didn't fill
        self.bg_label.setGeometry(self.rect())

    def update_system_stats(self):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        self.sys_monitor.update_stats(cpu, ram)

    def open_memo_dialog(self, date: QDate):
        date_str = date.toString("yyyy-MM-dd")
        dialog = MemoDialog(date_str, self.memo_manager, self)
        dialog.exec()
        
        # After dialog closes, refresh calendar dots and memo list if it's today
        self.calendar.refresh_dots()
        if date_str == QDate.currentDate().toString("yyyy-MM-dd"):
            self.memo_list.refresh_list()
        
        if self.memo_list.current_date == date_str:
            self.memo_list.refresh_list()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'bg_label'):
            self.bg_label.setGeometry(self.rect())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)
