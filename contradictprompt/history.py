"""Opt-in local audit history. Parameterized SQL, no credentials stored."""
import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path

def record(path: str,event: str,payload: dict):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(path) as con:
        con.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, created TEXT, event TEXT, payload TEXT)')
        con.execute('INSERT INTO events(created,event,payload) VALUES (?,?,?)',
                    (datetime.now(timezone.utc).isoformat(),event,json.dumps(payload,ensure_ascii=False)))

def read(path: str):
    if not Path(path).exists(): return []
    with sqlite3.connect(path) as con:
        return [dict(zip(['id','created','event','payload'],row)) for row in con.execute('SELECT * FROM events ORDER BY id DESC LIMIT 100')]
