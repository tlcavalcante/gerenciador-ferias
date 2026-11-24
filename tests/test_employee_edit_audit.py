import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "gerenciador_ferias.py"


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("GERENCIADOR_FERIAS_DATA_DIR", str(tmp_path / "data"))
    spec = importlib.util.spec_from_file_location("gerenciador_ferias_edit_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module._init_banco()
    return module


def preparar_colaborador(app, segundo=False):
    con = app._conn()
    try:
        con.execute(
            "INSERT INTO usuarios(login,nome,senha_hash,nivel) VALUES(?,?,?,?)",
            ("admin", "Administrador", "hash-de-teste", "admin"),
        )
        cursor = con.execute(
            "INSERT INTO funcionarios(nome,setor,subsetor,vinculo,data_admissao) "
            "VALUES(?,?,?,?,?)",
            ("Ana", "Administrativo", "Pessoal", "Servidor", "10/01/2020"),
        )
        funcionario_id = cursor.lastrowid
        con.execute(
            "INSERT INTO ferias(funcionario_id,inicio,fim,venda_ferias) VALUES(?,?,?,?)",
            (funcionario_id, "01/07/2026", "10/07/2026", 0),
        )
        con.execute(
            "INSERT INTO banco_horas(funcionario_id,data,tipo,minutos,motivo,usuario_id,criado_em) "
            "VALUES(?,?,?,?,?,?,?)",
            (funcionario_id, "01/11/2026", "C", 90, "Crédito de teste", None, "2026-11-01T12:00:00-03:00"),
        )
        if segundo:
            con.execute(
                "INSERT INTO funcionarios(nome,setor,subsetor,vinculo,data_admissao) "
                "VALUES(?,?,?,?,?)",
                ("Ana", "Tecnologia", "Redes", "", ""),
            )
        con.execute("DELETE FROM trilha_auditoria")
        con.commit()
    finally:
        con.close()

    app.SESSAO.update({"login": "admin", "nome": "Administrador", "nivel": "admin"})
    funcionario = {
        "_id": funcionario_id, "nome": "Ana", "setor": "Administrativo",
        "subsetor": "Pessoal", "vinculo": "Servidor",
        "data_admissao": "10/01/2020",
        "ferias": [{"inicio": "01/07/2026", "fim": "10/07/2026"}],
    }
    return funcionario, funcionario_id


def consultar(app, sql, params=()):
    con = app._conn()
    try:
        return con.execute(sql, params).fetchall()
    finally:
        con.close()


def test_edicao_audita_dados_anteriores_novos_motivo_e_preserva_historicos(app):
    funcionario, funcionario_id = preparar_colaborador(app)
    ferias_antes = consultar(app, "SELECT id, funcionario_id FROM ferias WHERE funcionario_id=?", (funcionario_id,))
    banco_antes = consultar(app, "SELECT id, funcionario_id, minutos FROM banco_horas WHERE funcionario_id=?", (funcionario_id,))
    novos = {
        "nome": "Ana Maria", "setor": "Tecnologia", "subsetor": "Redes",
        "vinculo": "CLT", "data_admissao": "11/01/2020",
    }
    assert app._gravar_edicao_funcionario(funcionario, novos, "Correção do cadastro")
    eventos = consultar(
        app,
        "SELECT acao, entidade, registro_id, usuario_login, detalhes "
        "FROM trilha_auditoria WHERE entidade='funcionarios' AND registro_id=? ORDER BY id",
        (funcionario_id,),
    )
    por_acao = {evento["acao"]: evento for evento in eventos}
    assert set(por_acao) == {"UPDATE", "ATUALIZACAO_CADASTRO"}
    automatico = json.loads(por_acao["UPDATE"]["detalhes"])
    assert automatico["antes"]["nome"] == "Ana"
    assert automatico["depois"]["nome"] == "Ana Maria"
    assert automatico["antes"]["setor"] == "Administrativo"
    assert automatico["depois"]["setor"] == "Tecnologia"
    explicito = json.loads(por_acao["ATUALIZACAO_CADASTRO"]["detalhes"])
    assert explicito["motivo"] == "Correção do cadastro"
    assert explicito["alteracoes"]["nome"] == {"antes": "Ana", "depois": "Ana Maria"}
    assert explicito["historicos_preservados"] == ["ferias", "banco_horas"]
    assert por_acao["ATUALIZACAO_CADASTRO"]["usuario_login"] == "admin"
    ferias_depois = consultar(app, "SELECT id, funcionario_id FROM ferias WHERE funcionario_id=?", (funcionario_id,))
    banco_depois = consultar(app, "SELECT id, funcionario_id, minutos FROM banco_horas WHERE funcionario_id=?", (funcionario_id,))
    assert [tuple(row) for row in ferias_depois] == [tuple(row) for row in ferias_antes]
    assert [tuple(row) for row in banco_depois] == [tuple(row) for row in banco_antes]
    assert funcionario["nome"] == "Ana Maria"
    assert funcionario["_id"] == funcionario_id


def test_usuario_sem_perfil_administrador_nao_pode_editar(app):
    funcionario, funcionario_id = preparar_colaborador(app)
    app.SESSAO["nivel"] = "usuario"
    novos = dict(funcionario, nome="Ana Atualizada")
    assert not app._gravar_edicao_funcionario(funcionario, novos, "Motivo válido")
    registro = consultar(app, "SELECT nome FROM funcionarios WHERE id=?", (funcionario_id,))[0]
    assert registro["nome"] == "Ana"
    assert consultar(app, "SELECT id FROM trilha_auditoria WHERE acao IN ('UPDATE','ATUALIZACAO_CADASTRO')") == []


def test_edicao_impede_nome_duplicado_no_destino_sem_diferenciar_caixa(app):
    funcionario, funcionario_id = preparar_colaborador(app, segundo=True)
    novos = {
        "nome": "ana", "setor": "Tecnologia", "subsetor": "Redes",
        "vinculo": "", "data_admissao": "10/01/2020",
    }
    assert not app._gravar_edicao_funcionario(funcionario, novos, "Ajuste de lotação")
    registro = consultar(app, "SELECT nome, setor, subsetor FROM funcionarios WHERE id=?", (funcionario_id,))[0]
    assert tuple(registro) == ("Ana", "Administrativo", "Pessoal")
    assert consultar(app, "SELECT id FROM trilha_auditoria WHERE acao IN ('UPDATE','ATUALIZACAO_CADASTRO')") == []


def test_edicao_nao_aceita_motivo_vazio_ou_curto(app):
    funcionario, funcionario_id = preparar_colaborador(app)
    novos = dict(funcionario, nome="Ana Atualizada")
    assert not app._gravar_edicao_funcionario(funcionario, novos, "abc")
    registro = consultar(app, "SELECT nome FROM funcionarios WHERE id=?", (funcionario_id,))[0]
    assert registro["nome"] == "Ana"


def test_falha_ao_gravar_evento_explicitamente_reverte_update_e_trigger(app):
    funcionario, funcionario_id = preparar_colaborador(app)
    con = app._conn()
    try:
        con.execute("""
            CREATE TRIGGER falhar_evento_edicao
            BEFORE INSERT ON trilha_auditoria
            WHEN NEW.acao = 'ATUALIZACAO_CADASTRO'
            BEGIN
                SELECT RAISE(ABORT, 'falha simulada');
            END
        """)
        con.commit()
    finally:
        con.close()

    novos = dict(funcionario, nome="Ana Atualizada")
    assert not app._gravar_edicao_funcionario(funcionario, novos, "Ajuste cadastral")
    registro = consultar(app, "SELECT nome FROM funcionarios WHERE id=?", (funcionario_id,))[0]
    assert registro["nome"] == "Ana"
    assert consultar(app, "SELECT id FROM trilha_auditoria WHERE acao IN ('UPDATE','ATUALIZACAO_CADASTRO')") == []
