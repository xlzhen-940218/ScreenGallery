import os
import random
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, QPoint, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QIcon
from utils.i18n import tr

def get_asset_path(filename):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, filename)

# Tetromino shapes
SHAPES = [
    [], # Empty
    [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]], # I
    [[2, 0, 0], [2, 2, 2], [0, 0, 0]], # J
    [[0, 0, 3], [3, 3, 3], [0, 0, 0]], # L
    [[4, 4], [4, 4]], # O
    [[0, 5, 5], [5, 5, 0], [0, 0, 0]], # S
    [[0, 6, 0], [6, 6, 6], [0, 0, 0]], # T
    [[7, 7, 0], [0, 7, 7], [0, 0, 0]]  # Z
]

COLORS = [
    QColor(0, 0, 0, 0), # Empty
    QColor(0, 255, 255), # I (Cyan)
    QColor(0, 0, 255), # J (Blue)
    QColor(255, 165, 0), # L (Orange)
    QColor(255, 255, 0), # O (Yellow)
    QColor(0, 255, 0), # S (Green)
    QColor(128, 0, 128), # T (Purple)
    QColor(255, 0, 0) # Z (Red)
]

class TetrisWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("metro_tile")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.cols = 14
        self.rows = 20
        
        self.board = []
        self.score = 0
        self.is_playing = True
        
        self.current_piece = None
        self.current_x = 0
        self.current_y = 0
        
        self.target_x = 0
        self.target_rotation = 0
        
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
        
        self.score_label = QLabel(f"{tr('Score: ')}0")
        self.score_label.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
        
        top_layout.addWidget(self.play_btn)
        top_layout.addStretch()
        top_layout.addWidget(self.score_label)
        
        overlay_layout.addLayout(top_layout)
        overlay_layout.addStretch()
        
        # Game Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.game_tick)
        self.timer.start(100) # Fast tick for AI
        
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
        self.board = [[0] * self.cols for _ in range(self.rows)]
        self.score = 0
        self.score_label.setText(f"{tr('Score: ')}{self.score}")
        self.spawn_piece()
        
    def rotate_piece(self, piece):
        return [list(row) for row in zip(*piece[::-1])]
        
    def check_collision(self, piece, offset_x, offset_y):
        for y, row in enumerate(piece):
            for x, cell in enumerate(row):
                if cell:
                    board_x = offset_x + x
                    board_y = offset_y + y
                    if board_x < 0 or board_x >= self.cols or board_y >= self.rows:
                        return True
                    if board_y >= 0 and self.board[board_y][board_x]:
                        return True
        return False
        
    def spawn_piece(self):
        shape_idx = random.randint(1, 7)
        self.current_piece = SHAPES[shape_idx]
        self.current_x = self.cols // 2 - len(self.current_piece[0]) // 2
        self.current_y = 0
        
        if self.check_collision(self.current_piece, self.current_x, self.current_y):
            self.reset_game()
            return
            
        self.compute_best_move()
        
    def clear_lines(self):
        lines_cleared = 0
        new_board = []
        for row in self.board:
            if all(cell != 0 for cell in row):
                lines_cleared += 1
            else:
                new_board.append(row)
                
        while len(new_board) < self.rows:
            new_board.insert(0, [0] * self.cols)
            
        self.board = new_board
        if lines_cleared > 0:
            self.score += [0, 40, 100, 300, 1200][lines_cleared]
            self.score_label.setText(f"{tr('Score: ')}{self.score}")
            
    def merge_piece(self):
        for y, row in enumerate(self.current_piece):
            for x, cell in enumerate(row):
                if cell:
                    board_y = self.current_y + y
                    board_x = self.current_x + x
                    if 0 <= board_y < self.rows and 0 <= board_x < self.cols:
                        self.board[board_y][board_x] = cell
        self.clear_lines()
        self.spawn_piece()
        
    def evaluate_board(self, test_board):
        # Heuristics
        heights = [0] * self.cols
        holes = 0
        for x in range(self.cols):
            block_found = False
            for y in range(self.rows):
                if test_board[y][x]:
                    if not block_found:
                        heights[x] = self.rows - y
                        block_found = True
                elif block_found:
                    holes += 1
                    
        aggregate_height = sum(heights)
        bumpiness = sum(abs(heights[i] - heights[i+1]) for i in range(self.cols - 1))
        
        lines_cleared = 0
        for row in test_board:
            if all(cell != 0 for cell in row):
                lines_cleared += 1
                
        # Weights (standard tetris AI heuristic)
        a = -0.510066
        b = 0.760666
        c = -0.35663
        d = -0.184483
        
        return (a * aggregate_height) + (b * lines_cleared) + (c * holes) + (d * bumpiness)
        
    def compute_best_move(self):
        best_score = -999999
        best_x = self.current_x
        best_rot = 0
        best_rot_piece = self.current_piece
        
        # Test all rotations
        test_piece = self.current_piece
        for rot in range(4):
            # Test all columns
            for x in range(-2, self.cols):
                if not self.check_collision(test_piece, x, 0):
                    # Drop piece
                    drop_y = 0
                    while not self.check_collision(test_piece, x, drop_y + 1):
                        drop_y += 1
                        
                    # Create test board
                    test_board = [list(row) for row in self.board]
                    for py, row in enumerate(test_piece):
                        for px, cell in enumerate(row):
                            if cell:
                                by = drop_y + py
                                bx = x + px
                                if 0 <= by < self.rows and 0 <= bx < self.cols:
                                    test_board[by][bx] = cell
                                    
                    score = self.evaluate_board(test_board)
                    if score > best_score:
                        best_score = score
                        best_x = x
                        best_rot = rot
                        best_rot_piece = test_piece
                        
            test_piece = self.rotate_piece(test_piece)
            
        self.target_x = best_x
        self.target_rotation = best_rot
        
    def game_tick(self):
        if not self.is_playing:
            return
            
        if not self.current_piece:
            return
            
        action_taken = False
        
        # 1. Rotate towards target
        if self.target_rotation > 0:
            rotated = self.rotate_piece(self.current_piece)
            if not self.check_collision(rotated, self.current_x, self.current_y):
                self.current_piece = rotated
                self.target_rotation -= 1
                action_taken = True
                
        # 2. Move towards target X
        elif self.current_x < self.target_x:
            if not self.check_collision(self.current_piece, self.current_x + 1, self.current_y):
                self.current_x += 1
                action_taken = True
        elif self.current_x > self.target_x:
            if not self.check_collision(self.current_piece, self.current_x - 1, self.current_y):
                self.current_x -= 1
                action_taken = True
                
        # 3. If x and rotation are correct, drop fast, otherwise drop normal
        if not action_taken:
            if not self.check_collision(self.current_piece, self.current_x, self.current_y + 1):
                # Hard drop logic for AI to make it look fast
                while not self.check_collision(self.current_piece, self.current_x, self.current_y + 1):
                    self.current_y += 1
                self.merge_piece()
            else:
                self.merge_piece()
        else:
            # Gravity still applies while moving
            if not self.check_collision(self.current_piece, self.current_x, self.current_y + 1):
                self.current_y += 1
            else:
                self.merge_piece()
                
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw Metro Background
        painter.setBrush(QBrush(QColor(0, 0, 0, 128)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)
        
        padding = 40
        w = self.width() - padding * 2
        h = self.height() - padding * 2
        
        cell_size = min(w / self.cols, h / self.rows)
        
        offset_x = padding + (w - cell_size * self.cols) / 2
        offset_y = padding + (h - cell_size * self.rows) / 2
        
        # Draw Board
        for y in range(self.rows):
            for x in range(self.cols):
                if self.board[y][x]:
                    color = COLORS[self.board[y][x]]
                    painter.setBrush(QBrush(color))
                    painter.drawRoundedRect(int(offset_x + x * cell_size), 
                                            int(offset_y + y * cell_size), 
                                            int(cell_size - 1), int(cell_size - 1), 2, 2)
                                            
        # Draw Current Piece
        if self.current_piece:
            for y, row in enumerate(self.current_piece):
                for x, cell in enumerate(row):
                    if cell:
                        color = COLORS[cell]
                        painter.setBrush(QBrush(color))
                        painter.drawRoundedRect(int(offset_x + (self.current_x + x) * cell_size), 
                                                int(offset_y + (self.current_y + y) * cell_size), 
                                                int(cell_size - 1), int(cell_size - 1), 2, 2)
                                                
        painter.end()
