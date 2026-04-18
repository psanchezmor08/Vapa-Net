"""
VapaNet — Gestor de base de datos SQLite
"""

import sqlite3
import os
from datetime import datetime


def get_db_path() -> str:
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "vapanet.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS speed_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            download_mbps REAL,
            upload_mbps REAL,
            ping_ms REAL,
            server TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS ping_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            host TEXT NOT NULL,
            avg_ms REAL,
            packet_loss REAL,
            status TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS sentinel_hosts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host TEXT UNIQUE NOT NULL,
            alias TEXT,
            is_active INTEGER DEFAULT 1,
            last_status TEXT DEFAULT 'pending',
            last_check TEXT,
            response_ms REAL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS monitor_urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            alias TEXT,
            is_active INTEGER DEFAULT 1,
            last_status_code INTEGER,
            last_status TEXT DEFAULT 'pending',
            last_check TEXT,
            response_ms REAL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS batch_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            batch_name TEXT,
            host TEXT NOT NULL,
            status TEXT,
            avg_ms REAL,
            packet_loss REAL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS dns_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            domain TEXT NOT NULL,
            record_type TEXT,
            result TEXT,
            resolve_ms REAL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS port_scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            host TEXT NOT NULL,
            port INTEGER,
            status TEXT,
            service TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    defaults = [
        ("theme", "dark"),
        ("ping_count", "4"),
        ("ping_timeout", "1"),
        ("monitor_interval", "60"),
        ("sentinel_interval", "30"),
        ("port_timeout", "0.5"),
        ("company_name", "Vapa"),
    ]
    for key, val in defaults:
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))

    conn.commit()
    conn.close()


def get_setting(key: str, default: str = "") -> str:
    try:
        conn = get_connection()
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        conn.close()
        return row["value"] if row else default
    except Exception:
        return default


def set_setting(key: str, value: str):
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


def insert_speed_result(download: float, upload: float, ping: float, server: str = ""):
    conn = get_connection()
    conn.execute(
        "INSERT INTO speed_history (timestamp, download_mbps, upload_mbps, ping_ms, server) VALUES (?,?,?,?,?)",
        (datetime.now().isoformat(), download, upload, ping, server)
    )
    conn.commit()
    conn.close()


def get_speed_history(limit: int = 20) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM speed_history ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_ping_result(host: str, avg_ms: float, loss: float, status: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO ping_history (timestamp, host, avg_ms, packet_loss, status) VALUES (?,?,?,?,?)",
        (datetime.now().isoformat(), host, avg_ms, loss, status)
    )
    conn.commit()
    conn.close()


def get_ping_history(limit: int = 50) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM ping_history ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_sentinel_hosts() -> list:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM sentinel_hosts ORDER BY alias, host").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_sentinel_host(host: str, alias: str = ""):
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO sentinel_hosts (host, alias) VALUES (?, ?)",
        (host, alias or host)
    )
    conn.commit()
    conn.close()


def update_sentinel_status(host: str, status: str, ms: float):
    conn = get_connection()
    conn.execute(
        "UPDATE sentinel_hosts SET last_status=?, last_check=?, response_ms=? WHERE host=?",
        (status, datetime.now().isoformat(), ms, host)
    )
    conn.commit()
    conn.close()


def delete_sentinel_host(host_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM sentinel_hosts WHERE id=?", (host_id,))
    conn.commit()
    conn.close()


def get_monitor_urls() -> list:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM monitor_urls ORDER BY alias, url").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_monitor_url(url: str, alias: str = ""):
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO monitor_urls (url, alias) VALUES (?, ?)",
        (url, alias or url)
    )
    conn.commit()
    conn.close()


def update_monitor_status(url: str, status: str, code: int, ms: float):
    conn = get_connection()
    conn.execute(
        "UPDATE monitor_urls SET last_status=?, last_status_code=?, last_check=?, response_ms=? WHERE url=?",
        (status, code, datetime.now().isoformat(), ms, url)
    )
    conn.commit()
    conn.close()


def delete_monitor_url(url_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM monitor_urls WHERE id=?", (url_id,))
    conn.commit()
    conn.close()


def insert_batch_results(batch_name: str, results: list):
    conn = get_connection()
    ts = datetime.now().isoformat()
    for r in results:
        conn.execute(
            "INSERT INTO batch_results (timestamp, batch_name, host, status, avg_ms, packet_loss) VALUES (?,?,?,?,?,?)",
            (ts, batch_name, r["host"], r["status"], r.get("avg_ms", 0), r.get("loss", 0))
        )
    conn.commit()
    conn.close()


def get_batch_history(limit: int = 100) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM batch_results ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_dns_result(domain: str, rtype: str, result: str, ms: float):
    conn = get_connection()
    conn.execute(
        "INSERT INTO dns_history (timestamp, domain, record_type, result, resolve_ms) VALUES (?,?,?,?,?)",
        (datetime.now().isoformat(), domain, rtype, result, ms)
    )
    conn.commit()
    conn.close()


def get_dns_history(limit: int = 30) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM dns_history ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_port_scan(host: str, results: list):
    conn = get_connection()
    ts = datetime.now().isoformat()
    for r in results:
        conn.execute(
            "INSERT INTO port_scan_history (timestamp, host, port, status, service) VALUES (?,?,?,?,?)",
            (ts, host, r["port"], r["status"], r.get("service", ""))
        )
    conn.commit()
    conn.close()


def get_port_scan_history(limit: int = 200) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM port_scan_history ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
