from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QScrollArea, QPushButton, QSizePolicy
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QPropertyAnimation, QParallelAnimationGroup, QTimer, QEvent
from PyQt6.QtGui import QFont
from utils.i18n import tr

class MemoItemWidget(QWidget):
    status_changed = pyqtSignal(int, bool) # memo_id, is_completed

    def __init__(self, memo, parent=None):
        super().__init__(parent)
        self.memo = memo
        self.memo_id = memo['id']
        
        # For long press detection
        self.press_timer = QTimer(self)
        self.press_timer.setSingleShot(True)
        self.press_timer.timeout.connect(self._on_complete_clicked)
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        
        self.label = QLabel(memo['text'])
        self.label.setWordWrap(True)
        self.label.setStyleSheet("font-size: 18px;")
        self.label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.layout.addWidget(self.label, stretch=1)
        
        self.priority_label = QLabel()
        if memo['priority'] == 'HIGH':
            self.priority_label.setText(tr("★ HIGH"))
            self.priority_label.setStyleSheet("color: #ff6b6b; font-weight: bold; font-size: 14px;")
        else:
            self.priority_label.setText(tr("NORMAL"))
            self.priority_label.setStyleSheet("color: #a5b1c2; font-size: 14px;")
        self.layout.addWidget(self.priority_label)
        
        self.update_style()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.press_timer.start(800) # 800ms long press
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.press_timer.isActive():
                self.press_timer.stop()
        super().mouseReleaseEvent(event)

    def event(self, event):
        if event.type() == QEvent.Type.TouchBegin:
            self.press_timer.start(800)
            return True
        elif event.type() in (QEvent.Type.TouchEnd, QEvent.Type.TouchCancel):
            if self.press_timer.isActive():
                self.press_timer.stop()
            return True
        return super().event(event)
        
    def _on_complete_clicked(self):
        is_completed = not self.memo.get('is_completed', False)
        self.memo['is_completed'] = is_completed
        self.update_style()
        self.status_changed.emit(self.memo_id, is_completed)

    def update_style(self):
        font = self.label.font()
        if self.memo.get('is_completed', False):
            font.setStrikeOut(True)
            self.label.setFont(font)
            self.label.setStyleSheet("color: #718093; font-size: 18px;") # Gray out
        else:
            font.setStrikeOut(False)
            self.label.setFont(font)
            self.label.setStyleSheet("color: #f5f6fa; font-size: 18px;") # Normal color


class MemoListWidget(QWidget):
    def __init__(self, memo_manager, parent=None):
        super().__init__(parent)
        self.memo_manager = memo_manager
        self.current_date = QDate.currentDate().toString("yyyy-MM-dd")
        self.setObjectName("metro_tile")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        title_layout = QHBoxLayout()
        title_label = QLabel(tr("Today's Priority Tasks"))
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #f5f6fa;")
        title_layout.addWidget(title_label)
        main_layout.addLayout(title_layout)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; } QWidget#scroll_content { background: transparent; }")
        
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("scroll_content")
        self.list_layout = QVBoxLayout(self.scroll_content)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)
        
        self.refresh_list()

    def set_date(self, date_str):
        self.current_date = date_str
        self.refresh_list()

    def refresh_list(self):
        # Clear current list
        while self.list_layout.count():
            child = self.list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        memos = self.memo_manager.get_memos_by_date(self.current_date)
        for memo in memos:
            item = MemoItemWidget(memo)
            item.status_changed.connect(self._on_item_status_changed)
            self.list_layout.addWidget(item)

    def _on_item_status_changed(self, memo_id, is_completed):
        self.memo_manager.update_memo_status(memo_id, is_completed)
        # Re-sort list visually by simply refreshing it for now
        # A more complex smooth sliding reorder animation could be added here
        self.refresh_list()
