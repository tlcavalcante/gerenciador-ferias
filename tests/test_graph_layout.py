import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "gerenciador_ferias.py"


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("GERENCIADOR_FERIAS_DATA_DIR", str(tmp_path / "data"))
    spec = importlib.util.spec_from_file_location("gerenciador_ferias_graph_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_horizontal_bar_respects_width_and_clamps_values(app):
    empty = app._barra_grafico(0, 10, 12)
    half = app._barra_grafico(5, 10, 12)
    above_scale = app._barra_grafico(15, 10, 12)
    negative = app._barra_grafico(-5, 10, 12)

    assert all(len(bar) == 12 for bar in (empty, half, above_scale, negative))
    assert half.count("▰") == 6
    assert above_scale.count("▰") == 12
    assert negative.count("▰") == 0


def test_horizontal_bar_handles_zero_scale_and_invalid_values(app):
    assert len(app._barra_grafico(8, 0, 9)) == 9
    assert app._barra_grafico("invalid", 10, 9).count("▰") == 0


def test_diverging_balance_bar_separates_negative_zero_and_positive(app):
    negative = app._barra_saldo_bh(-100, 100, 8)
    zero = app._barra_saldo_bh(0, 100, 8)
    positive = app._barra_saldo_bh(100, 100, 8)

    assert negative.index("│") == 8
    assert positive.index("│") == 8
    assert negative[:8].count("▰") == 8
    assert negative[9:].count("▰") == 0
    assert zero.count("▰") == 0
    assert positive[:8].count("▰") == 0
    assert positive[9:].count("▰") == 8


def test_diverging_balance_bar_clamps_to_common_scale(app):
    bar = app._barra_saldo_bh(150, 100, 6)
    assert bar[7:].count("▰") == 6


def test_indicator_layout_wraps_at_terminal_width(app, monkeypatch):
    rendered = []
    monkeypatch.setattr(app, "_larg", lambda: 62)
    monkeypatch.setattr(app, "_ln", lambda value="", align="left": rendered.append(str(value)))
    monkeypatch.setattr(app, "_vis", lambda value: len(str(value)))
    monkeypatch.setattr(app, "_c_muted", lambda value: str(value))
    monkeypatch.setattr(app, "_c", lambda value, *args, **kwargs: str(value))

    app._grafico_indicadores([
        ("Período", "24 meses", "cyan"),
        ("Dias agendados", "120 dias", "success"),
        ("Meses ativos", "12/24", "purple"),
        ("Média mensal", "5 dias", "accent"),
    ])

    assert len(rendered) > 1
    assert all(len(line) <= 62 for line in rendered)
