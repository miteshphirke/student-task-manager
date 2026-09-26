"""
models.py
---------
Handles all SQLite database logic for the Student Task Management System.
Kept deliberately simple (raw sqlite3, no ORM) so beginners can read every line.
"""

import sqlite3
import os

# The database file lives next to this script by default.
# DB_PATH can be overridden with an environment variable (useful for tests / Docker volumes).
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "tasks.db"))


def get_db_connection():
    """Create a new SQLite connection with row access by column name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the tasks table if it does not already exist."""
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            due_date TEXT,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def get_all_tasks():
    conn = get_db_connection()
    tasks = conn.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
    conn.close()
    return tasks


def get_task(task_id):
    conn = get_db_connection()
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return task


def add_task(student_name, title, description, due_date, status="Pending"):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO tasks (student_name, title, description, due_date, status) VALUES (?, ?, ?, ?, ?)",
        (student_name, title, description, due_date, status),
    )
    conn.commit()
    conn.close()


def update_task(task_id, student_name, title, description, due_date, status):
    conn = get_db_connection()
    conn.execute(
        """UPDATE tasks
           SET student_name = ?, title = ?, description = ?, due_date = ?, status = ?
           WHERE id = ?""",
        (student_name, title, description, due_date, status, task_id),
    )
    conn.commit()
    conn.close()


def delete_task(task_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
