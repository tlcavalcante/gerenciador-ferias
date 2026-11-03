import importlib.util
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "gerenciador_ferias.py"


def load_app(data_dir):
    os.environ["GERENCIADOR_FERIAS_DATA_DIR"] = str(data_dir)
    spec = importlib.util.spec_from_file_location("gerenciador_ferias_under_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_standalone_v430_source_exists():
    assert SOURCE.is_file()
    source = SOURCE.read_text(encoding="utf-8")
    import re
    match = re.search(r"^APP_VERSION = ['\"]([^'\"]+)['\"]$", source, re.MULTILINE)
    assert match is not None
    assert match.group(1).startswith("4.")


def test_database_uses_configured_data_dir_and_ignores_cwd(tmp_path, monkeypatch):
    data_dir = tmp_path / "app-data"
    work_dir = tmp_path / "elsewhere"
    work_dir.mkdir()
    monkeypatch.chdir(work_dir)
    monkeypatch.setenv("GERENCIADOR_FERIAS_DATA_DIR", str(data_dir))
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    app = load_app(data_dir)
    app._init_banco()
    assert app.BANCO_DADOS == data_dir / "dados_ferias.db"
    assert app.BANCO_DADOS.is_file()
    assert not (work_dir / "dados_ferias.db").exists()


def test_historical_modules_remain_available():
    for name in ("app.py", "business.py", "core.py", "dashboard.py", "database.py", "menus.py", "runtime.py"):
        assert (ROOT / name).is_file()
