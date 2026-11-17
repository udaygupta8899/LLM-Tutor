"""
Learner Memory and Student Mastery Profile Tracking.
Stores student interactions, mastery levels, quiz scores, and preferred explanation depth.
"""

from typing import Dict, Any, List, Optional
import time
import json
import sqlite3
import os


class LearnerMemory:
    """
    SQLite-backed Learner Memory and Progression Tracker.
    """

    def __init__(self, db_path: str = "./learner_memory.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learners (
                    student_id TEXT PRIMARY KEY,
                    mastery_level TEXT DEFAULT 'intermediate',
                    preferred_depth TEXT DEFAULT 'detailed',
                    topics_studied TEXT DEFAULT '[]',
                    quiz_scores TEXT DEFAULT '[]',
                    last_active REAL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interaction_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT,
                    timestamp REAL,
                    question TEXT,
                    complexity TEXT,
                    tutor_mode TEXT,
                    answer TEXT,
                    grounded INTEGER
                )
            """)
            conn.commit()

    def get_profile(self, student_id: str) -> Dict[str, Any]:
        """Retrieves or creates learner profile."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT mastery_level, preferred_depth, topics_studied, quiz_scores FROM learners WHERE student_id = ?", (student_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "student_id": student_id,
                    "mastery_level": row[0],
                    "preferred_depth": row[1],
                    "topics_studied": json.loads(row[2]),
                    "quiz_scores": json.loads(row[3])
                }
            else:
                # Default new profile
                cursor.execute(
                    "INSERT INTO learners (student_id, mastery_level, preferred_depth, topics_studied, quiz_scores, last_active) VALUES (?, ?, ?, ?, ?, ?)",
                    (student_id, "beginner", "standard", json.dumps([]), json.dumps([]), time.time())
                )
                conn.commit()
                return {
                    "student_id": student_id,
                    "mastery_level": "beginner",
                    "preferred_depth": "standard",
                    "topics_studied": [],
                    "quiz_scores": []
                }

    def record_interaction(
        self,
        student_id: str,
        question: str,
        complexity: str,
        tutor_mode: str,
        answer: str,
        grounded: bool = True,
        topic: Optional[str] = None
    ):
        """Records student query interaction and updates topics studied."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO interaction_history (student_id, timestamp, question, complexity, tutor_mode, answer, grounded) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (student_id, time.time(), question, complexity, tutor_mode, answer, 1 if grounded else 0)
            )
            
            # Update topics studied
            if topic:
                cursor.execute("SELECT topics_studied FROM learners WHERE student_id = ?", (student_id,))
                row = cursor.fetchone()
                if row:
                    topics = json.loads(row[0])
                    if topic not in topics:
                        topics.append(topic)
                        cursor.execute("UPDATE learners SET topics_studied = ?, last_active = ? WHERE student_id = ?", (json.dumps(topics), time.time(), student_id))
            conn.commit()

    def get_recent_history(self, student_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetches recent conversation interactions."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT question, answer, complexity, tutor_mode, timestamp FROM interaction_history WHERE student_id = ? ORDER BY id DESC LIMIT ?",
                (student_id, limit)
            )
            rows = cursor.fetchall()
            return [
                {"question": r[0], "answer": r[1], "complexity": r[2], "tutor_mode": r[3], "timestamp": r[4]}
                for r in reversed(rows)
            ]
