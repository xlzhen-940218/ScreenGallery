from PyQt6.QtWidgets import QCalendarWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
from PyQt6.QtCore import Qt, QDate, pyqtSignal

class CalendarWidget(QCalendarWidget):
    date_clicked = pyqtSignal(QDate)

    def __init__(self, memo_manager, parent=None):
        super().__init__(parent)
        self.memo_manager = memo_manager
        self.dates_with_memos = []
        self.setGridVisible(False)
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.ShortDayNames)
        self.setObjectName("metro_tile")
        
        # Force transparency on the calendar table view
        from PyQt6.QtWidgets import QTableView
        from PyQt6.QtGui import QPalette
        view = self.findChild(QTableView, "qt_calendar_calendarview")
        if view:
            view.setAutoFillBackground(False)
            view.viewport().setAutoFillBackground(False)
            palette = view.palette()
            palette.setColor(QPalette.ColorRole.Base, Qt.GlobalColor.transparent)
            view.setPalette(palette)
        
        # Connect internal clicked signal to our custom one
        self.clicked.connect(self.date_clicked.emit)
        
        self.refresh_dots()

    def refresh_dots(self):
        # Refresh the list of dates that have incomplete memos
        date_strings = self.memo_manager.get_dates_with_memos()
        self.dates_with_memos = [QDate.fromString(ds, "yyyy-MM-dd") for ds in date_strings]
        self.updateCells()

    def paintCell(self, painter, rect, date):
        super().paintCell(painter, rect, date)
        
        # If this date has an active memo, draw a small dot indicator below the number
        if date in self.dates_with_memos:
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            dot_color = QColor(255, 100, 100) # Red-ish dot
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(dot_color))
            
            # Position dot at bottom center
            dot_radius = 3
            center_x = rect.x() + rect.width() / 2
            center_y = rect.y() + rect.height() - 6
            
            painter.drawEllipse(int(center_x - dot_radius), int(center_y - dot_radius), dot_radius * 2, dot_radius * 2)
            
            painter.restore()
