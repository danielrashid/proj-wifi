import base64
import io
import os
import secrets
import sqlite3
import string
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

import qrcode
from dotenv import load_dotenv
from flask import Flask, abort, g, jsonify, redirect, render_template, request

from mikrotik import MikroTikClient, MikroTikConfig, MikroTikError

load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")


class Settings:
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", "8080"))
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8080").rstrip("/")

    ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "troque_este_token")

    DB_PATH = Path(os.getenv("DB_PATH", "./data/vouchers.db"))

    HOTSPOT_LOGIN_URL = os.getenv("HOTSPOT_LOGIN_URL", "http://login.wifi.local/login")
    HOTSPOT_DST = os.getenv("HOTSPOT_DST", "https://www.google.com")

    MT_CFG = MikroTikConfig(
        host=os.getenv("MT_HOST", "192.168.88.1"),
        port=int(os.getenv("MT_PORT", "8728")),
        username=os.getenv("MT_USERNAME", "admin"),
        password=os.getenv("MT_PASSWORD", ""),
        use_ssl=os.getenv("MT_USE_SSL", "false").lower() == "true",
        hotspot_server=os.getenv("MT_HOTSPOT_SERVER", "hotspot1"),
        hotspot_profile=os.getenv("MT_HOTSPOT_PROFILE", "perfil_1h"),
    )


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        Settings.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(Settings.DB_PATH)
        connection.row_factory = sqlite3.Row
        g.db = connection
    return g.db


@app.teardown_appcontext
def close_db(_: Exception | None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS vouchers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            qr_url TEXT NOT NULL,
            created_at TEXT NOT NULL,
            mikrotik_created INTEGER NOT NULL DEFAULT 0,
            used INTEGER NOT NULL DEFAULT 0,
            used_at TEXT
        );
        """
    )
    db.commit()


def require_admin_token() -> bool:
    auth_header = request.headers.get("Authorization", "")
    query_token = request.args.get("token")

    if query_token and query_token == Settings.ADMIN_TOKEN:
        return True

    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        return token == Settings.ADMIN_TOKEN

    return False


def random_credential(length: int = 8) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_qr_data_uri(data: str) -> str:
    image = qrcode.make(data)
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    encoded = base64.b64encode(stream.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def create_voucher_record() -> sqlite3.Row:
    db = get_db()

    for _ in range(10):
        token = secrets.token_urlsafe(16)
        username = f"u{random_credential(7)}"
        password = random_credential(8)
        qr_url = f"{Settings.BASE_URL}/v/{token}"
        created_at = datetime.now(timezone.utc).isoformat()

        try:
            with closing(db.cursor()) as cursor:
                cursor.execute(
                    """
                    INSERT INTO vouchers (token, username, password, qr_url, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (token, username, password, qr_url, created_at),
                )
                db.commit()

                cursor.execute("SELECT * FROM vouchers WHERE id = ?", (cursor.lastrowid,))
                row = cursor.fetchone()

            if row is None:
                raise RuntimeError("Falha ao criar voucher")
            return row
        except sqlite3.IntegrityError:
            continue

    raise RuntimeError("Não foi possível gerar voucher único após várias tentativas")


def ensure_mikrotik_user(voucher: sqlite3.Row):
    if voucher["mikrotik_created"] == 1:
        return

    client = MikroTikClient(Settings.MT_CFG)
    client.ensure_user_profile()
    client.create_hotspot_user(voucher["username"], voucher["password"])

    db = get_db()
    db.execute("UPDATE vouchers SET mikrotik_created = 1 WHERE id = ?", (voucher["id"],))
    db.commit()


@app.route("/")
def index():
    if not require_admin_token():
        abort(401, "Token admin inválido. Use ?token=SEU_TOKEN")

    db = get_db()
    rows = db.execute(
        """
        SELECT id, token, username, password, qr_url, created_at, mikrotik_created, used, used_at
        FROM vouchers
        ORDER BY id DESC
        LIMIT 50
        """
    ).fetchall()

    latest_voucher = None
    history_vouchers = []

    for index_pos, row in enumerate(rows):
        voucher = dict(row)
        if index_pos == 0:
            voucher["qr_data_uri"] = generate_qr_data_uri(voucher["qr_url"])
            latest_voucher = voucher
        else:
            history_vouchers.append(voucher)

    admin_panel_url = f"{Settings.BASE_URL}/?token={Settings.ADMIN_TOKEN}"

    return render_template(
        "index.html",
        latest_voucher=latest_voucher,
        history_vouchers=history_vouchers,
        admin_panel_url=admin_panel_url,
        admin_panel_qr_data_uri=generate_qr_data_uri(admin_panel_url),
    )


@app.route("/api/v1/vouchers", methods=["POST"])
def create_voucher_api():
    if not require_admin_token():
        abort(401, "Não autorizado")

    try:
        voucher = create_voucher_record()
        ensure_mikrotik_user(voucher)

        data = {
            "id": voucher["id"],
            "token": voucher["token"],
            "username": voucher["username"],
            "password": voucher["password"],
            "qr_url": voucher["qr_url"],
        }
        return jsonify(data), 201
    except MikroTikError as exc:
        abort(500, f"Erro MikroTik: {exc}")


@app.route("/api/v1/vouchers/<token>/qrcode")
def qrcode_api(token: str):
    if not require_admin_token():
        abort(401, "Não autorizado")

    db = get_db()
    row = db.execute("SELECT * FROM vouchers WHERE token = ?", (token,)).fetchone()
    if row is None:
        abort(404, "Voucher não encontrado")

    return jsonify(
        {
            "token": row["token"],
            "qr_url": row["qr_url"],
            "qrcode_data_uri": generate_qr_data_uri(row["qr_url"]),
        }
    )


@app.route("/admin/create", methods=["POST"])
def create_voucher_form():
    if not require_admin_token():
        abort(401, "Não autorizado")

    try:
        voucher = create_voucher_record()
        ensure_mikrotik_user(voucher)
    except MikroTikError as exc:
        return f"Erro ao criar usuário no MikroTik: {exc}", 500

    return redirect(f"/?token={Settings.ADMIN_TOKEN}")


@app.route("/v/<token>")
def voucher_login(token: str):
    db = get_db()
    row = db.execute("SELECT * FROM vouchers WHERE token = ?", (token,)).fetchone()
    if row is None:
        abort(404, "Voucher inválido")

    if row["used"] == 1:
        return render_template("used.html")

    return render_template(
        "voucher_login.html",
        hotspot_login_url=Settings.HOTSPOT_LOGIN_URL,
        dst=Settings.HOTSPOT_DST,
        username=row["username"],
        password=row["password"],
        token=row["token"],
    )


@app.route("/v/<token>/mark-used", methods=["POST"])
def mark_voucher_used(token: str):
    db = get_db()
    row = db.execute("SELECT id, used FROM vouchers WHERE token = ?", (token,)).fetchone()
    if row is None:
        abort(404, "Voucher inválido")

    if row["used"] == 0:
        db.execute(
            "UPDATE vouchers SET used = 1, used_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), row["id"]),
        )
        db.commit()

    return jsonify({"ok": True})


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


def startup_checks():
    init_db()


if __name__ == "__main__":
    with app.app_context():
        startup_checks()
    app.run(host=Settings.APP_HOST, port=Settings.APP_PORT, debug=False)
