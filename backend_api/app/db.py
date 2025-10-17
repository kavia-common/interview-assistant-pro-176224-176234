import threading
from typing import Any, Dict, List, Optional, Tuple
import pymysql
from pymysql.cursors import DictCursor

_pool_lock = threading.Lock()
_pool: Dict[str, Any] = {}


def init_db_pool(host: str, port: int, user: str, password: str, db: str, min_conn: int = 1, max_conn: int = 5):
    """Initialize a simple connection pool stored globally."""
    with _pool_lock:
        if _pool.get("initialized"):
            return
        _pool["params"] = {"host": host, "port": port, "user": user, "password": password, "db": db}
        _pool["initialized"] = True
        _pool["max_conn"] = max_conn
        _pool["active"] = 0


def _new_conn():
    params = _pool.get("params", {})
    return pymysql.connect(
        host=params.get("host"),
        port=params.get("port"),
        user=params.get("user"),
        password=params.get("password"),
        database=params.get("db"),
        cursorclass=DictCursor,
        autocommit=False,
        charset="utf8mb4",
    )


def get_conn():
    """Get a new connection; simplistic pooling by limiting concurrent connections."""
    with _pool_lock:
        if _pool.get("active", 0) < _pool.get("max_conn", 5):
            _pool["active"] = _pool.get("active", 0) + 1
            return _new_conn()
    # Fallback: still return a connection (could implement waiting/queueing)
    return _new_conn()


def release_conn(conn):
    try:
        conn.close()
    finally:
        with _pool_lock:
            _pool["active"] = max(0, _pool.get("active", 0) - 1)


def close_db_pool():
    # Connections are closed on release; nothing persistent to close
    pass


# PUBLIC_INTERFACE
def query_one(sql: str, params: Tuple = ()) -> Optional[Dict]:
    """Execute a SELECT and return one row as dict."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
        conn.commit()
        return row
    except Exception:
        conn.rollback()
        raise
    finally:
        release_conn(conn)


# PUBLIC_INTERFACE
def query_all(sql: str, params: Tuple = ()) -> List[Dict]:
    """Execute a SELECT and return all rows as dict list."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        conn.commit()
        return rows
    except Exception:
        conn.rollback()
        raise
    finally:
        release_conn(conn)


# PUBLIC_INTERFACE
def execute(sql: str, params: Tuple = ()) -> int:
    """Execute an INSERT/UPDATE/DELETE and return lastrowid if available, else affected rows."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            last_id = cur.lastrowid or cur.rowcount
        conn.commit()
        return int(last_id) if last_id is not None else 0
    except Exception:
        conn.rollback()
        raise
    finally:
        release_conn(conn)
