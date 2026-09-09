import bcrypt
from itsdangerous import URLSafeSerializer, BadSignature
from fastapi import Request, Response
from app.database import get_connection

SECRET_KEY = "lifeos-change-this-to-a-long-random-secret"
serializer = URLSafeSerializer(SECRET_KEY, salt="lifeos-session")


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except Exception:
        return False


def create_user(username: str, password: str):
    username = (username or "").strip().lower()
    password = password or ""

    if not username or not password:
        return None, "Username and password required"
    if len(username) < 3:
        return None, "Username too short"
    if len(password) < 4:
        return None, "Password too short"

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hash_password(password)),
        )
        conn.commit()
        user_id = cur.lastrowid
    except Exception:
        conn.close()
        return None, "Username already exists"
    conn.close()
    return {"id": user_id, "username": username}, None


def authenticate(username: str, password: str):
    username = (username or "").strip().lower()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    user = dict(row)
    if not verify_password(password or "", user["password_hash"]):
        return None

    return {"id": user["id"], "username": user["username"]}


def set_session(response: Response, user: dict):
    token = serializer.dumps({"id": user["id"], "username": user["username"]})
    response.set_cookie(
        key="lifeos_session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )


def clear_session(response: Response):
    response.delete_cookie("lifeos_session")


def get_current_user(request: Request):
    token = request.cookies.get("lifeos_session")
    if not token:
        return None
    try:
        data = serializer.loads(token)
        if not data.get("id") or not data.get("username"):
            return None
        return {"id": int(data["id"]), "username": data["username"]}
    except BadSignature:
        return None