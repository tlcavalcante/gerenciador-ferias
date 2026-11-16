import ast
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "gerenciador_ferias.py"


def load_app(tmp_path, monkeypatch):
    monkeypatch.setenv("GERENCIADOR_FERIAS_DATA_DIR", str(tmp_path / "data"))
    spec = importlib.util.spec_from_file_location("gerenciador_ferias_selection_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_employee_selection_label_contains_all_fields_in_order(tmp_path, monkeypatch):
    app = load_app(tmp_path, monkeypatch)
    monkeypatch.setattr(app, "_c_menu", lambda value: value)
    monkeypatch.setattr(app, "_c_muted", lambda value: value)

    label = app._rotulo_funcionario_selecao({
        "nome": "Ana Maria",
        "setor": "TIC",
        "subsetor": "Redes",
        "vinculo": "Estatutário",
    })

    assert label == "Ana Maria | TIC | Redes | Estatutário"


def test_employee_selection_label_handles_missing_fields(tmp_path, monkeypatch):
    app = load_app(tmp_path, monkeypatch)
    monkeypatch.setattr(app, "_c_menu", lambda value: value)
    monkeypatch.setattr(app, "_c_muted", lambda value: value)

    label = app._rotulo_funcionario_selecao({"nome": "João"})

    assert label == "João | Sem setor | Sem subsetor | Sem vínculo"


def test_all_single_employee_selectors_use_the_shared_format():
    source = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    selector_defs = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "sel_func"
    ]
    assert len(selector_defs) == 1
    assert [arg.arg for arg in selector_defs[0].args.args] == ["d", "msg"]

    calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "sel_func"
    ]
    assert calls
    assert all(
        keyword.arg != "setor_mesma_linha"
        for call in calls
        for keyword in call.keywords
    )
