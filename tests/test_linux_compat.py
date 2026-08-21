import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_modules_are_flat():
    expected = ["app.py", "business.py", "core.py", "dashboard.py", "database.py", "menus.py", "runtime.py"]
    assert all((ROOT / name).is_file() for name in expected)
    assert not (ROOT / "src").exists()
    assert not (ROOT / "gerenciador_ferias").is_dir()

def test_database_is_next_to_program_and_independent_of_cwd(tmp_path):
    env = os.environ.copy()
    env.pop("XDG_DATA_HOME", None)
    env.pop("GERENCIADOR_FERIAS_DATA_DIR", None)
    code = (
        "import core; core.preparar_ambiente(); "
        "print(core.APP_DIR); print(core.BANCO_DADOS); print(core.BACKUP_DIR)"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=tmp_path, env={**env, "PYTHONPATH": str(ROOT)},
        text=True, capture_output=True, check=True
    )
    lines = result.stdout.strip().splitlines()
    assert Path(lines[0]).resolve() == ROOT.resolve()
    assert Path(lines[1]).resolve() == ROOT.resolve() / "dados_ferias.db"
    assert Path(lines[2]).resolve() == ROOT.resolve()

def test_execution_from_other_directory(tmp_path):
    import shutil

    app_dir = tmp_path / "app"
    app_dir.mkdir()
    for source in ROOT.glob("*.py"):
        shutil.copy2(source, app_dir / source.name)

    work_dir = tmp_path / "work"
    work_dir.mkdir()
    env = os.environ.copy()
    env.pop("XDG_DATA_HOME", None)
    env.pop("GERENCIADOR_FERIAS_DATA_DIR", None)

    # Cria o administrador inicial, autentica e encerra pelo menu principal.
    input_data = "admin\nAdministrador\nSenha123!\nSenha123!\nadmin\nSenha123!\n0\n"
    result = subprocess.run(
        [sys.executable, str(app_dir / "gerenciador_ferias.py")],
        cwd=work_dir, env=env, input=input_data, text=True, capture_output=True, timeout=15
    )
    assert result.returncode == 0
    assert (app_dir / "dados_ferias.db").exists()
    assert not (work_dir / "dados_ferias.db").exists()

def test_no_runtime_xdg_dependency():
    core = (ROOT / "core.py").read_text(encoding="utf-8")
    assert "XDG_DATA_HOME" not in core
    assert "GERENCIADOR_FERIAS_DATA_DIR" not in core
