import hashlib
import os
import sys
import sqlite3
from datetime import datetime

HERE = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, HERE)
import app
import database as db
import menus as ui_menus


def test_password_hash_is_salted_and_verifiable():
    h1 = app._hash("Senha-Forte-123")
    h2 = app._hash("Senha-Forte-123")
    assert h1 != h2
    assert app._verificar_senha("Senha-Forte-123", h1) == (True, False)
    assert app._verificar_senha("errada", h1) == (False, False)


def test_legacy_sha256_is_accepted_for_migration():
    legacy = hashlib.sha256("admin123".encode()).hexdigest()
    assert app._verificar_senha("admin123", legacy) == (True, True)
    assert app._verificar_senha("outra", legacy) == (False, True)


def test_add_months_preserves_end_of_month():
    assert app.add_meses(datetime(2026, 1, 31), 1) == datetime(2026, 2, 28)
    assert app.add_meses(datetime(2028, 1, 31), 1) == datetime(2028, 2, 29)
    assert app.add_meses(datetime(2026, 3, 31), -1) == datetime(2026, 2, 28)


def test_database_migration_and_no_default_user(tmp_path):
    old = db.BANCO_DADOS
    db.BANCO_DADOS = str(tmp_path / "dados_ferias.db")
    try:
        app._init_banco()
        con = app._conn()
        cols = {r[1] for r in con.execute("PRAGMA table_info(usuarios)")}
        users = con.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
        con.close()
        assert {"failed_attempts", "locked_until", "last_login"} <= cols
        assert users == 0
    finally:
        db.BANCO_DADOS = old


def test_sqlite_backup_api(tmp_path):
    old = app.BANCO_DADOS
    old_backup = ui_menus.BACKUP_DIR
    old_db = db.BANCO_DADOS
    db.BANCO_DADOS = str(tmp_path / "dados_ferias.db")
    ui_menus.BANCO_DADOS = db.BANCO_DADOS
    ui_menus.BACKUP_DIR = str(tmp_path / "backups")
    try:
        app._init_banco()
        con = app._conn()
        con.execute("INSERT INTO usuarios (login,nome,senha_hash,nivel) VALUES (?,?,?,?)", ("teste", "Teste", app._hash("x"), "admin"))
        con.commit(); con.close()
        backup = app._fazer_backup()
        assert backup and os.path.exists(backup)
        bcon = sqlite3.connect(backup)
        assert bcon.execute("SELECT login FROM usuarios").fetchone()[0] == "teste"
        assert bcon.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        bcon.close()
    finally:
        db.BANCO_DADOS = old
        app.BACKUP_DIR = old_backup
