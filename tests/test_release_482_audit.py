import importlib.util
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / "gerenciador_ferias.py"


def load_app(tmp_path, monkeypatch):
    monkeypatch.setenv("GERENCIADOR_FERIAS_DATA_DIR", str(tmp_path / "data"))
    spec = importlib.util.spec_from_file_location("gerenciador_ferias_audit_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module._init_banco()
    return module


def test_audit_triggers_capture_insert_update_delete(tmp_path, monkeypatch):
    app = load_app(tmp_path, monkeypatch)
    app.SESSAO.update(login="auditor", nome="Usuário Auditor", nivel="admin")
    con = app._conn()
    con.execute("INSERT INTO setores(nome) VALUES (?)", ("SETIC",))
    con.commit()
    con.execute("UPDATE setores SET nome=? WHERE nome=?", ("TIC", "SETIC"))
    con.commit()
    con.execute("DELETE FROM setores WHERE nome=?", ("TIC",))
    con.commit()
    rows = con.execute(
        "SELECT usuario_login, usuario_nome, acao, entidade, detalhes "
        "FROM trilha_auditoria ORDER BY id"
    ).fetchall()
    con.close()

    assert [row["acao"] for row in rows] == ["INSERT", "UPDATE", "DELETE"]
    assert all(row["usuario_login"] == "auditor" for row in rows)
    assert all(row["usuario_nome"] == "Usuário Auditor" for row in rows)
    assert rows[1]["entidade"] == "setores"
    assert '"antes"' in rows[1]["detalhes"]
    assert '"depois"' in rows[1]["detalhes"]


def test_audit_excludes_password_hash_and_records_explicit_events(tmp_path, monkeypatch):
    app = load_app(tmp_path, monkeypatch)
    app.SESSAO.update(login="admin", nome="Administrador", nivel="admin")
    con = app._conn()
    con.execute(
        "INSERT INTO usuarios(login,nome,senha_hash,nivel) VALUES (?,?,?,?)",
        ("novo", "Novo usuário", "HASH_PRIVADO_NAO_REGISTRAR", "usuario"),
    )
    con.commit()
    details = " ".join(
        row["detalhes"]
        for row in con.execute("SELECT detalhes FROM trilha_auditoria").fetchall()
    )
    con.close()

    assert "HASH_PRIVADO_NAO_REGISTRAR" not in details
    app._auditar_evento("LOGIN", "autenticacao", "Acesso autenticado com sucesso.")
    con = app._conn()
    event = con.execute(
        "SELECT usuario_login, acao, entidade FROM trilha_auditoria "
        "WHERE acao='LOGIN' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    con.close()
    assert tuple(event) == ("admin", "LOGIN", "autenticacao")
