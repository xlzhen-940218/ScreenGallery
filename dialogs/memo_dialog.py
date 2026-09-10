from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QListWidget, QListWidgetItem, QWidget)
from PyQt6.QtCore import Qt
from utils.i18n import tr

class MemoDialog(QDialog):
    def __init__(self, date_str, memo_manager, parent=None):
        super().__init__(parent)
        self.date_str = date_str
        self.memo_manager = memo_manager
        
        self.setWindowTitle(f"{tr('Tasks for ')}{date_str}")
        self.setMinimumSize(450, 350)
        
        self.layout = QVBoxLayout(self)
        
        # Header
        header = QLabel(f"{tr('Manage Tasks for ')}{date_str}")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        self.layout.addWidget(header)
        
        # Task List
        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)
        
        # New Task Input Area
        input_layout = QHBoxLayout()
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText(tr("Enter new task..."))
        self.text_input.setStyleSheet("font-size: 16px;")
        input_layout.addWidget(self.text_input)
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItems([tr("NORMAL"), tr("HIGH")])
        self.priority_combo.setStyleSheet("font-size: 16px;")
        input_layout.addWidget(self.priority_combo)
        
        self.add_btn = QPushButton(tr("Add"))
        self.add_btn.setStyleSheet("font-size: 16px;")
        self.add_btn.clicked.connect(self.add_task)
        input_layout.addWidget(self.add_btn)
        
        self.layout.addLayout(input_layout)
        
        # Close Button
        self.close_btn = QPushButton(tr("Close"))
        self.close_btn.setStyleSheet("font-size: 16px;")
        self.close_btn.clicked.connect(self.accept)
        self.layout.addWidget(self.close_btn)
        
        self.refresh_list()

    def refresh_list(self):
        self.list_widget.clear()
        memos = self.memo_manager.get_memos_by_date(self.date_str)
        
        for memo in memos:
            item = QListWidgetItem()
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(5, 5, 5, 5)
            
            # Title
            title_lbl = QLabel(memo['text'])
            title_lbl.setStyleSheet("font-size: 16px;")
            if memo['is_completed']:
                font = title_lbl.font()
                font.setStrikeOut(True)
                title_lbl.setFont(font)
                title_lbl.setStyleSheet("color: gray; font-size: 16px;")
            layout.addWidget(title_lbl, stretch=1)
            
            # Priority
            if memo['priority'] == 'HIGH':
                pri_lbl = QLabel(tr("★ HIGH"))
                pri_lbl.setStyleSheet("color: #ff6b6b; font-weight: bold; font-size: 14px;")
                layout.addWidget(pri_lbl)
                
            # Delete button
            del_btn = QPushButton(tr("Del"))
            del_btn.setFixedSize(50, 28)
            del_btn.setStyleSheet("font-size: 14px;")
            # Use lambda with default arg to capture memo id
            del_btn.clicked.connect(lambda checked, m_id=memo['id']: self.delete_task(m_id))
            layout.addWidget(del_btn)
            
            item.setSizeHint(widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

    def add_task(self):
        text = self.text_input.text().strip()
        if text:
            display_priority = self.priority_combo.currentText()
            # Map translated back to internal 'HIGH' or 'NORMAL'
            priority = 'HIGH' if display_priority == tr("HIGH") else 'NORMAL'
            self.memo_manager.add_memo(self.date_str, text, priority)
            self.text_input.clear()
            self.refresh_list()

    def delete_task(self, memo_id):
        self.memo_manager.delete_memo(memo_id)
        self.refresh_list()
