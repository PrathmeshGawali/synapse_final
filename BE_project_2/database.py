# database.py
import sqlite3
import json
from datetime import datetime

def init_db():
    conn = sqlite3.connect('synapseiq.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS outputs
                 (id TEXT PRIMARY KEY,
                  feature TEXT,
                  content TEXT,
                  created_at TIMESTAMP)''')
    conn.commit()
    return conn

def save_output(output_id, feature, content):
    conn = init_db()
    c = conn.cursor()
    c.execute("INSERT INTO outputs VALUES (?, ?, ?, ?)",
              (output_id, feature, json.dumps(content), datetime.now()))
    conn.commit()

def get_output(output_id):
    conn = init_db()
    c = conn.cursor()
    c.execute("SELECT feature, content FROM outputs WHERE id=?", (output_id,))
    row = c.fetchone()
    if row:
        feature, content = row
        return feature, json.loads(content)
    return None, None
