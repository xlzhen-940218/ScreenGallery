import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any

class MemoManager:
    def __init__(self, db_path="data/memos.db"):
        self.db_path = db_path
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    text TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    is_completed BOOLEAN NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def add_memo(self, date: str, text: str, priority: str = "NORMAL") -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO memos (date, text, priority, is_completed) VALUES (?, ?, ?, ?)',
                (date, text, priority, False)
            )
            conn.commit()
            return cursor.lastrowid

    def update_memo_status(self, memo_id: int, is_completed: bool):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE memos SET is_completed = ? WHERE id = ?',
                (is_completed, memo_id)
            )
            conn.commit()

    def delete_memo(self, memo_id: int):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM memos WHERE id = ?', (memo_id,))
            conn.commit()

    def get_memos_by_date(self, date: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM memos WHERE date = ?', (date,))
            rows = cursor.fetchall()
            
            memos = [dict(row) for row in rows]
            
            # Sort:
            # 1. Incomplete first
            # 2. HIGH priority first
            # 3. Created time (oldest first or newest first, let's say oldest first)
            memos.sort(key=lambda m: (
                m['is_completed'],  # False (0) before True (1)
                0 if m['priority'] == 'HIGH' else 1,
                m['created_at']
            ))
            return memos

    def get_dates_with_memos(self) -> List[str]:
        """Returns a list of dates that have incomplete memos to show dots on calendar."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT date FROM memos WHERE is_completed = 0')
            return [row[0] for row in cursor.fetchall()]
