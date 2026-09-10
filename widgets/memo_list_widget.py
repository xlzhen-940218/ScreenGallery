from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QScrollArea, QPushButton, QSizePolicy
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QPropertyAnimation, QParallelAnimationGroup
from PyQt6.QtGui import QFont

class MemoItemWidget(QWidget):
    status_changed = pyqtSignal(int, bool) # memo_id, is_completed

    def __init__(self, memo, parent=None):
        super().__init__(parent)
        self.memo = memo
        self.memo_id = memo['id']
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        
        self.label = QLabel(memo['text'])
        self.label.setWordWrap(True)
        self.label.setStyleSheet("font-size: 20px;")
        self.label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.layout.addWidget(self.label, stretch=1)
        
        self.priority_label = QLabel()
        if memo['priority'] == 'HIGH':
            self.priority_label.setText("★ HIGH")
            self.priority_label.setStyleSheet("color: #ff6b6b; font-weight: bold; font-size: 16px;")
        else:
            self.priority_label.setText("NORMAL")
            self.priority_label.setStyleSheet("color: #a5b1c2; font-size: 16px;")
        self.layout.addWidget(self.priority_label)
        
        self.complete_btn = QPushButton()
        self.complete_btn.clicked.connect(self._on_complete_clicked)
        self.layout.addWidget(self.complete_btn)
        
        self.update_style()
        
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
            self.label.setStyleSheet("color: #718093; font-size: 20px;") # Gray out
            self.complete_btn.setText("✔")
            self.complete_btn.setStyleSheet("""
                QPushButton {
                    font-size: 20px; 
                    font-weight: bold; 
                    padding: 8px 12px; 
                    border-radius: 6px;
                    color: #2ecc71;
                    background-color: rgba(46, 204, 113, 0.2);
                    border: 1px solid rgba(46, 204, 113, 0.4);
                }
                QPushButton:hover { background-color: rgba(46, 204, 113, 0.3); }
            """)
        else:
            font.setStrikeOut(False)
            self.label.setFont(font)
            self.label.setStyleSheet("color: #f5f6fa; font-size: 20px;") # Normal color
            self.complete_btn.setText("Complete")
            self.complete_btn.setStyleSheet("""
                QPushButton {
                    font-size: 20px; 
                    font-weight: bold; 
                    padding: 8px 12px; 
                    border-radius: 6px;
                    color: white;
                    background-color: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }
                QPushButton:hover { background-color: rgba(255, 255, 255, 0.2); }
            """)


class MemoListWidget(QWidget):
    def __init__(self, memo_manager, parent=None):
        super().__init__(parent)
        self.memo_manager = memo_manager
        self.current_date = QDate.currentDate().toString("yyyy-MM-dd")
        self.setObjectName("metro_tile")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        title_layout = QHBoxLayout()
        title_label = QLabel("Today's Priority Tasks")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #f5f6fa;")
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
