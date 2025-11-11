# Warning: This is real web service. Hacking is strictly forbidden.
import base64
import os
from flask import Flask, redirect, render_template, jsonify, request, make_response, url_for, flash
import sqlite3, os, time, json
import jwt
from jwt import InvalidTokenError, ExpiredSignatureError
from config import DB_PATH, PRIVATE_KEY_PATH, PUBLIC_KEY_PATH
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

app = Flask(__name__)
app.secret_key = os.urandom(32)

def read_key(path):
    with open(path, "rb") as f:
        return f.read()

def get_db():
    return sqlite3.connect(DB_PATH)

def init():
    os.makedirs("keys", exist_ok=True)
    os.makedirs("static", exist_ok=True)

    priv = ed25519.Ed25519PrivateKey.generate()

    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    pub_ssh = priv.public_key().public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    )

    with open("keys/ed25519_private.pem", "wb") as f:
        f.write(priv_pem)

    with open("static/ed25519_public.pub", "wb") as f:
        f.write(pub_ssh)

def _verify_and_decode_eddsa(token):
    if not token:
        raise InvalidTokenError("missing token")
    header_b64 = token.split('.')[0]
    padding = '=' * (-len(header_b64) % 4)
    header_bytes = base64.urlsafe_b64decode(header_b64 + padding)
    header = json.loads(header_bytes)
    alg = header.get("alg", "EdDSA")
    pubkey = read_key(PUBLIC_KEY_PATH)
    if isinstance(pubkey, bytes):
        pubkey = pubkey.decode("utf-8")
    # 취약점: 알고리즘을 제한하지 않아 HS256 등으로 위조된 토큰도 통과함.
    return jwt.decode(token, key=pubkey, algorithms=jwt.algorithms.get_default_algorithms())

def _get_token_from_request():
    token = request.cookies.get("token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()
    return token

def _verify_token(token):
    if not token:
        raise InvalidTokenError("missing token")
    pubkey = read_key(PUBLIC_KEY_PATH)
    if isinstance(pubkey, bytes):
        pubkey = pubkey.decode("utf-8")
    return jwt.decode(token, key=pubkey, algorithms=jwt.algorithms.get_default_algorithms())

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # This service is live. Please refrain from real-world exploitation.
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, username, is_admin FROM users WHERE username = ? AND password = ?", (username, password))
        row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        return render_template("login.html", error="Invalid credentials")

    uid, uname, is_admin = row

    now = int(time.time())
    private_key = read_key(PRIVATE_KEY_PATH)
    if isinstance(private_key, bytes):
        private_key = private_key.decode("utf-8")

    payload = {
        "uid": str(uid),
        "uname": uname,
        "iat": now,
        "exp": now + 3600,
    }
    token = jwt.encode(payload, private_key, algorithm="EdDSA")
    resp = redirect(url_for("profile"))
    # 취약점: JWT를 HttpOnly/secure 없이 발급해 XSS로 쉽게 탈취 가능.
    resp.set_cookie("token", token, httponly=False, samesite="Lax", secure=False)
    return resp

@app.route("/profile", methods=["GET", "POST"])
def profile():
    try:
        claims = _verify_and_decode_eddsa(_get_token_from_request())
        uid = claims.get("uid")
        uname = claims.get("uname")
    except:
        return redirect(url_for("login"))
    conn = get_db()
    cur = conn.cursor()

    print(claims, uid, uname, flush=True)

    if request.method == "POST":
        action = request.form.get("action")
        if action == "create":
            content = request.form.get("content", "").strip()
            if content:
                cur.execute("INSERT INTO notes (owner_id, content) VALUES (?, ?)", (uid, content))
                conn.commit()
        elif action == "delete":
            note_id = request.form.get("note_id")
            try:
                nid = int(note_id)
                cur.execute("DELETE FROM notes WHERE id = ? AND owner_id = ?", (nid, uid))
                conn.commit()
            except Exception:
                pass
        conn.close()
        return redirect(url_for("profile"))

    # 취약점: uid를 그대로 문자열 보간해 SQL 인젝션이 가능함.
    cur.execute(f"SELECT id, content FROM notes WHERE owner_id = {uid} ORDER BY id DESC LIMIT 50")
    rows = cur.fetchall()
    conn.close()
    notes = [{"id": r[0], "content": r[1]} for r in rows]

    return render_template("profile.html", uname=uname, notes=notes)

@app.route("/logout", methods=["POST","GET"])
def logout():
    resp = redirect(url_for("login"))
    resp.delete_cookie("token")
    return resp

@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    init()
    app.run(host="0.0.0.0", port=8000)
