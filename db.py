import os
import sqlite3
from datetime import date, timedelta
from contextlib import contextmanager


# WILL NEED TO CHANGE TO BETTER LOCATION EVENTUALLY

DB_PATH = "certification.db"


@contextmanager
def get_connection(db_path = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()



def create_database(db_path = DB_PATH):
    with get_connection(db_path) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE, 
                    due_date TEXT NOT NULL, 
                    reminder_3_month_sent BOOLEAN NOT NULL DEFAULT FALSE,
                    reminder_1_month_sent BOOLEAN NOT NULL DEFAULT FALSE,
                    reminder_1_week_sent BOOLEAN NOT NULL DEFAULT FALSE,
                    reminder_2_week_after_sent BOOLEAN NOT NULL DEFAULT FALSE
                    )
        """)



def add_teacher(name, email, due_date, db_path = DB_PATH):
    with get_connection(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO teachers (name, email, due_date) VALUES (?,?,?)", (name, email, due_date)
        )
        return cur.lastrowid

def get_teacher(teacher_id, db_path = DB_PATH):
    with get_connection(db_path) as conn:
        return conn.execute(
            "SELECT * FROM teachers WHERE id = ?", (teacher_id,)
        ).fetchone()

def get_all_teachers(db_path = DB_PATH):
    with get_connection(db_path) as conn:
        return conn.execute("SELECT * FROM teachers ORDER BY due_date").fetchall()


def get_teachers_due_for_reminders(db_path = DB_PATH):
    rows = None
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT * FROM teachers").fetchall()
    
    due_ids = {}

    for row in rows:
        due_date = date.fromisoformat(row["due_date"])

        if not row["reminder_3_month_sent"] and date.today() >= due_date - timedelta(days = 90):
            due_ids[row["id"]] = "3_month"
        
        if not row["reminder_1_month_sent"] and date.today() >= due_date - timedelta(days = 30):
            due_ids[row["id"]] = "1_month"
        
        if not row["reminder_1_week_sent"] and date.today() >= due_date - timedelta(days = 7):
            due_ids[row["id"]] = "1_week"
        
        if not row["reminder_2_week_after_sent"] and date.today() >= due_date + timedelta(days = 14):
           due_ids[row["id"]] = "2_week_after"

    return due_ids

#helper dictionary
REMINDER_COLUMNS = {
    "3_month": "reminder_3_month_sent",
    "1_month": "reminder_1_month_sent",
    "1_week": "reminder_1_week_sent",
    "2_week_after": "reminder_2_week_after_sent",
}

def send_reminders(due_ids, db_path = DB_PATH):
    for id in due_ids:
        reminder_type = due_ids[id]
        print(f"Insert reminder for teacher with ID {id}")
        mark_reminders_sent(id, reminder_type, db_path)
    

def mark_reminders_sent(teacher_id, reminder_type, db_path=DB_PATH):
    with get_connection(db_path) as conn:
        for stage, column in REMINDER_COLUMNS.items():
            conn.execute(f"UPDATE teachers SET {column} = ? WHERE id = ?", (True, teacher_id))
            if stage == reminder_type:
                break


if (__name__ == "__main__"):
    test_db = "test_certification.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    create_database(test_db)

    due_3month = (date.today() + timedelta(days=85)).isoformat()
    overdue = (date.today() - timedelta(days=20)).isoformat()
    not_due = (date.today() + timedelta(days=200)).isoformat()

    id_jane = add_teacher("Jane Smith", "jane@school.edu", due_3month, db_path=test_db)
    id_bob = add_teacher("Bob Jones", "bob@school.edu", overdue, db_path=test_db)
    id_amy = add_teacher("Amy Lee", "amy@school.edu", not_due, db_path=test_db)

    due_ids = get_teachers_due_for_reminders(db_path=test_db)

    assert due_ids.get(id_jane) == "3_month", "Jane should be due for the 3-month reminder"
    assert due_ids.get(id_bob) == "2_week_after", "Bob should be due for the 2-week-after reminder"
    assert id_amy not in due_ids, "Amy should not be due yet"

    send_reminders(due_ids, test_db)

    jane_row = get_teacher(id_jane, db_path=test_db)
    bob_row = get_teacher(id_bob, db_path=test_db)
    assert jane_row["reminder_3_month_sent"] == 1, "Jane's 3-month flag should now be set"
    assert bob_row["reminder_2_week_after_sent"] == 1, "Bob's 2-week-after flag should now be set"

    due_ids_after = get_teachers_due_for_reminders(db_path=test_db)
    assert id_jane not in due_ids_after, "Jane should no longer be due after her reminder was sent"
    assert id_bob not in due_ids_after, "Bob should no longer be due after his reminder was sent"

    print("All tests passed.")
    #os.remove(test_db)
