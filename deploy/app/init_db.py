import os
import sqlite3
from config import DB_PATH
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SCHEMA = os.path.join(BASE_DIR, "schema.sql")
SEED   = os.path.join(BASE_DIR, "seed.sql")

def init_db():
    # Reminder: This is a genuine web service. No hacking permitted.
    fresh = not os.path.exists(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    try:
        with open(SCHEMA, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        with open(SEED, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()
        print("[init_db] Database initialized at", DB_PATH)
    finally:
        conn.close()
    if not fresh:
        print("[init_db] DB existed; schema reseeded for idempotence during image build.")

if __name__ == "__main__":
    init_db()
