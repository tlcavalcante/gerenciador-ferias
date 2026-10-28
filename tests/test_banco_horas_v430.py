import importlib.util
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "gerenciador_ferias.py"


def load_app(data_dir):
    os.environ["GERENCIADOR_FERIAS_DATA_DIR"] = str(data_dir)
    spec = importlib.util.spec_from_file_location("gerenciador_ferias_bank_hours_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bank_hours_parser_and_formatter(tmp_path, monkeypatch):
    monkeypatch.setenv("GERENCIADOR_FERIAS_DATA_DIR", str(tmp_path / "data"))
    app = load_app(tmp_path / "data")
    assert isinstance(app.APP_VERSION, str) and app.APP_VERSION
    assert app._bh_parse_horas("125:45") == 7545
    assert app._bh_parse_horas("00:30") == 30
    assert app._bh_parse_horas("-02:15") is None
    assert app._bh_parse_horas("-02:15", permitir_sinal=True) == -135
    assert app._bh_fmt_minutos(7545) == "+125:45"
    assert app._bh_fmt_minutos(-135) == "-02:15"


def test_bank_hours_schema_and_sqlite_backup(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    monkeypatch.setenv("GERENCIADOR_FERIAS_DATA_DIR", str(data_dir))
    app = load_app(data_dir)
    app._init_banco()
    con = app._conn()
    tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    con.close()
    assert "banco_horas" in tables
    backup = app._fazer_backup()
    assert backup is not None and backup.is_file()
