import os
import random
from collections import deque
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, QPoint, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QIcon

def get_asset_path(filename):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, filename)

class SnakeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("metro_tile")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.grid_width = 20
        self.grid_height = 20
        self.cell_size = 15 # will scale dynamically in paintEvent, but use logic coords
        
        self.snake = []
        self.food = QPoint(0, 0)
        self.direction = QPoint(1, 0)
        self.score = 0
        self.is_playing = True
        
        # UI Overlays
        overlay_layout = QVBoxLayout(self)
        overlay_layout.setContentsMargins(10, 10, 10, 10)
        
        top_layout = QHBoxLayout()
        self.play_btn = QPushButton()
        self.play_btn.setIcon(QIcon(get_asset_path("暂停.svg")))
        self.play_btn.setIconSize(QSize(24, 24))
        self.play_btn.setFixedSize(40, 40)
        self.play_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.play_btn.setStyleSheet("background-color: transparent; border: none; outline: none;")
        self.play_btn.clicked.connect(self.toggle_play)
        
        self.score_label = QLabel("Score: 0")
        self.score_label.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
        
        top_layout.addWidget(self.play_btn)
        top_layout.addStretch()
        top_layout.addWidget(self.score_label)
        
        overlay_layout.addLayout(top_layout)
        overlay_layout.addStretch()
        
        # Game Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.game_tick)
        self.timer.start(100) # 10 ticks per second
        
        self.reset_game()
        
    def toggle_play(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.play_btn.setIcon(QIcon(get_asset_path("暂停.svg")))
            self.timer.start(100)
        else:
            self.play_btn.setIcon(QIcon(get_asset_path("播放.svg")))
            self.timer.stop()
            
    def reset_game(self):
        self.snake = [QPoint(5, 5), QPoint(4, 5), QPoint(3, 5)]
        self.direction = QPoint(1, 0)
        self.score = 0
        self.score_label.setText(f"Score: {self.score}")
        self.spawn_food()
        
    def spawn_food(self):
        while True:
            x = random.randint(0, self.grid_width - 1)
            y = random.randint(0, self.grid_height - 1)
            p = QPoint(x, y)
            if p not in self.snake:
                self.food = p
                break
                
    def get_path_to(self, target):
        # BFS to find path to target
        queue = deque([(self.snake[0], [])])
        visited = set([QPoint(p.x(), p.y()) for p in self.snake[:-1]]) # Tail might move, but be conservative
        
        while queue:
            curr, path = queue.popleft()
            if curr == target:
                return path
            
            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nx, ny = curr.x() + dx, curr.y() + dy
                if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                    np = QPoint(nx, ny)
                    if np not in visited:
                        visited.add(np)
                        queue.append((np, path + [QPoint(dx, dy)]))
        return None
        
    def ai_choose_direction(self):
        head = self.snake[0]
        # 1. Try to find path to food
        path = self.get_path_to(self.food)
        if path and len(path) > 0:
            return path[0]
            
        # 2. If no path to food, try to find path to tail
        path = self.get_path_to(self.snake[-1])
        if path and len(path) > 0:
            return path[0]
            
        # 3. If totally trapped, just pick any valid open adjacent square to survive longest
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = head.x() + dx, head.y() + dy
            if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                if QPoint(nx, ny) not in self.snake[:-1]:
                    return QPoint(dx, dy)
                    
        # 4. Dead end
        return self.direction
        
    def game_tick(self):
        if not self.is_playing:
            return
            
        self.direction = self.ai_choose_direction()
        
        head = self.snake[0]
        new_head = QPoint(head.x() + self.direction.x(), head.y() + self.direction.y())
        
        # Check collision with walls or self
        if (new_head.x() < 0 or new_head.x() >= self.grid_width or 
            new_head.y() < 0 or new_head.y() >= self.grid_height or 
            new_head in self.snake[:-1]):
            self.reset_game()
            self.update()
            return
            
        self.snake.insert(0, new_head)
        
        if new_head == self.food:
            self.score += 10
            self.score_label.setText(f"Score: {self.score}")
            self.spawn_food()
        else:
            self.snake.pop()
            
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw Metro Background
        painter.setBrush(QBrush(QColor(0, 0, 0, 128)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)
        
        # Calculate cell size based on actual widget dimensions
        # Add some padding
        padding = 40
        w = self.width() - padding * 2
        h = self.height() - padding * 2
        
        cell_w = w / self.grid_width
        cell_h = h / self.grid_height
        
        offset_x = padding + (w - cell_w * self.grid_width) / 2
        offset_y = padding + (h - cell_h * self.grid_height) / 2
        
        # Draw Food
        painter.setBrush(QBrush(QColor(231, 76, 60))) # Red
        food_rect = (offset_x + self.food.x() * cell_w, 
                     offset_y + self.food.y() * cell_h, 
                     cell_w - 1, cell_h - 1)
        painter.drawRoundedRect(int(food_rect[0]), int(food_rect[1]), int(food_rect[2]), int(food_rect[3]), 3, 3)
        
        # Draw Snake
        for i, p in enumerate(self.snake):
            if i == 0:
                painter.setBrush(QBrush(QColor(46, 204, 113))) # Head is brighter green
            else:
                painter.setBrush(QBrush(QColor(39, 174, 96))) # Body is darker green
                
            rect = (offset_x + p.x() * cell_w, 
                    offset_y + p.y() * cell_h, 
                    cell_w - 1, cell_h - 1)
            painter.drawRoundedRect(int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3]), 3, 3)
            
        painter.end()
