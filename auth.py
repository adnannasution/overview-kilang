import hashlib
import hmac
import re


def _initials(username: str) -> str:
    local = re.sub(r'@.*', '', username)
    parts = re.split(r'[.\-_]', local)
    ini = ''.join(p[0] for p in parts if p).upper()[:2]
    return ini or (username[0].upper() if username else '')


def verify_password(plain: str, stored: str) -> bool:
    try:
        salt_hex, dk_hex = stored.split(':', 1)
        dk = hashlib.pbkdf2_hmac('sha256', plain.encode(), bytes.fromhex(salt_hex), 200_000)
        return hmac.compare_digest(dk, bytes.fromhex(dk_hex))
    except Exception:
        return False


def authenticate_user(username: str, password: str):
    from db import get_conn
    conn = get_conn()
    try:
        row = conn.execute(
            'SELECT username, hashed_password, role, is_active FROM users WHERE username = %s',
            (username,)
        ).fetchone()
    except Exception:
        return None
    finally:
        conn.close()
    if not row or not row['is_active']:
        return None
    if not verify_password(password, row['hashed_password']):
        return None
    return {'username': row['username'], 'role': row['role']}
