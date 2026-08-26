"""Minimal PostgreSQL connection for the Overview Kilang dashboard."""
import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "")


def get_conn():
    url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    return psycopg.connect(url, row_factory=dict_row)


def get_user_by_username(username: str):
    """Ambil user by username, tanpa cek password — dipakai untuk bootstrap SSO
    (identitas sudah diverifikasi lewat token dari central login)."""
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT username, role, is_active FROM users WHERE username = %s",
            (username,)
        ).fetchone()
    finally:
        conn.close()
