import sqlite3
import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt

SECRET_KEY = "vas-analytics-secret-key-2025"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def init_auth_db(db_path="outputs/auth.db"):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'viewer'
        )
    """)
    # Seed default admin if no users exist
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count == 0:
        hashed = pwd_context.hash("admin123")
        conn.execute(
            "INSERT INTO users (username, hashed_password, role) VALUES (?, ?, ?)",
            ("admin", hashed, "admin")
        )
        print("[Auth] Default admin created — username: admin, password: admin123")
    conn.commit()
    conn.close()


def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)


def hash_password(plain):
    return pwd_context.hash(plain)


def get_user(username: str, db_path="outputs/auth.db"):
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT username, hashed_password, role FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    conn.close()
    if row:
        return {"username": row[0], "hashed_password": row[1], "role": row[2]}
    return None


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_all_users(db_path="outputs/auth.db"):
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT id, username, role FROM users"
    ).fetchall()
    conn.close()
    return [{"id": r[0], "username": r[1], "role": r[2]} for r in rows]


def create_user(username: str, password: str, role: str, db_path="outputs/auth.db"):
    try:
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO users (username, hashed_password, role) VALUES (?, ?, ?)",
            (username, hash_password(password), role)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def delete_user(username: str, db_path="outputs/auth.db"):
    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()