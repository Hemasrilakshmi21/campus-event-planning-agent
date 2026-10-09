import sqlite3
import json
from pathlib import Path

DB_PATH = Path("event_memory.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS event_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name TEXT NOT NULL,
            event_date TEXT NOT NULL,
            budget REAL NOT NULL,
            venue TEXT NOT NULL,
            audience INTEGER NOT NULL,
            activities TEXT,
            start_time TEXT,
            end_time TEXT,
            plan_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

def save_event_plan(requirements, result):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO event_plans
        (event_name, event_date, budget, venue, audience, activities,
         start_time, end_time, plan_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        requirements["event_name"],
        requirements["event_date"],
        requirements["budget"],
        requirements["venue"],
        requirements["audience"],
        json.dumps(requirements["activities"]),
        requirements["start_time"],
        requirements["end_time"],
        json.dumps(result),
    ))

    conn.commit()
    conn.close()

def get_past_plans():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT event_name, event_date, budget, venue, audience, created_at
        FROM event_plans
        ORDER BY id DESC
        LIMIT 10
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def has_duplicate_event(event_name, event_date):
    conn = get_connection()
    row = conn.execute("""
        SELECT id FROM event_plans
        WHERE lower(event_name) = lower(?) AND event_date = ?
        LIMIT 1
    """, (event_name, event_date)).fetchone()
    conn.close()
    return row is not None

def get_events_on_date(event_date):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT event_name, venue, start_time, end_time
        FROM event_plans
        WHERE event_date = ?
    """, (event_date,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]
