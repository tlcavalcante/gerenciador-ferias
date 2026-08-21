from datetime import datetime
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import app


def make_func(nome="Ana", adm="01/01/2026", ferias=None, setor="TI", subsetor="Suporte", vinculo="CLT"):
    return {
        "_id": 1,
        "nome": nome,
        "setor": setor,
        "subsetor": subsetor,
        "vinculo": vinculo,
        "data_admissao": adm,
        "ferias": ferias or [],
    }


def make_data(funcionarios=None, regras=None):
    regras_base = app._regras_padrao()
    if regras:
        regras_base["global"].update(regras)
    return {
        "setores": {"TI": {"subsetores": ["Suporte"]}},
        "funcionarios": funcionarios or [],
        "vinculos": ["CLT", "PJ"],
        "regras": regras_base,
        "config": dict(app.CONFIG_PADRAO),
    }


def test_calc_dias_inclusive_and_invalid_dates():
    assert app.calc_dias("01/08/2026", "01/08/2026") == 1
    assert app.calc_dias("01/08/2026", "05/08/2026") == 5
    assert app.calc_dias("31/02/2026", "05/03/2026") == 0


def test_sobrepoem_detects_overlap_and_touching_ranges():
    a1, a2 = datetime(2026, 8, 1), datetime(2026, 8, 10)
    assert app.sobrepoem(a1, a2, datetime(2026, 8, 10), datetime(2026, 8, 20))
    assert app.sobrepoem(a1, a2, datetime(2026, 8, 5), datetime(2026, 8, 6))
    assert not app.sobrepoem(a1, a2, datetime(2026, 8, 11), datetime(2026, 8, 20))


def test_add_months_handles_month_lengths_and_year_rollover():
    assert app.add_meses(datetime(2026, 1, 31), 1) == datetime(2026, 2, 28)
    assert app.add_meses(datetime(2028, 1, 31), 1) == datetime(2028, 2, 29)
    assert app.add_meses(datetime(2026, 12, 31), 1) == datetime(2027, 1, 31)
    assert app.add_meses(datetime(2026, 3, 31), -1) == datetime(2026, 2, 28)


def test_current_acquisition_period_is_derived_from_admission_anniversary():
    func = make_func(adm="01/01/2025")
    ini, fim, numero = app.periodo_aquisitivo_atual(func)
    assert ini == datetime(2026, 1, 1)
    assert fim == datetime(2027, 1, 1)
    assert numero == 2


def test_days_in_acquisition_period_do_not_count_the_end_boundary():
    ini = datetime(2025, 1, 1)
    fim = datetime(2026, 1, 1)
    ferias = {"inicio": "20/12/2025", "fim": "10/01/2026"}
    assert app.dias_no_periodo(ferias, ini, fim) == 12


def test_days_in_calendar_year_clip_cross_year_vacation():
    ferias = {"inicio": "20/12/2025", "fim": "10/01/2026"}
    assert app.dias_no_ano_civil(ferias, 2025) == 12
    assert app.dias_no_ano_civil(ferias, 2026) == 10


def test_all_acquisition_periods_are_generated_until_current_period():
    func = make_func(adm="01/01/2024")
    periodos = app.todos_periodos_aquisitivos(func)
    assert len(periodos) >= 3
    assert periodos[0]["ini"] == datetime(2024, 1, 1)
    assert periodos[0]["fim"] == datetime(2025, 1, 1)
    assert periodos[0]["numero"] == 1
    assert periodos[1]["ini"] == datetime(2025, 1, 1)
    assert periodos[2]["ini"] == datetime(2026, 1, 1)


def test_rule_precedence_subsetor_over_sector_vinculo_and_global():
    d = make_data()
    d["regras"]["global"]["max_dias_ano"] = 30
    d["regras"]["por_vinculo"]["CLT"] = {"max_dias_ano": 28}
    d["regras"]["por_setor"]["TI"] = {"max_dias_ano": 25}
    d["regras"]["por_subsetor"]["TI::Suporte"] = {"max_dias_ano": 20}

    assert app.obter_regra(d, "max_dias_ano", "TI", "Suporte", "CLT") == 20
    assert app.obter_regra(d, "max_dias_ano", "TI", "Outro", "CLT") == 25
    assert app.obter_regra(d, "max_dias_ano", "Outro", "Outro", "CLT") == 28
    assert app.obter_regra(d, "max_dias_ano", "Outro", "Outro", "PJ") == 30


def test_validation_rejects_period_shorter_than_minimum():
    func = make_func(adm="01/01/2026")
    d = make_data([func])
    erros = app.validar_agendamento(d, func, datetime(2026, 9, 1), datetime(2026, 9, 4))
    assert any("Período mínimo de 5" in e for e in erros)


def test_validation_rejects_excess_days_in_acquisition_period():
    ferias = [
        {"inicio": "01/03/2026", "fim": "20/03/2026", "venda_ferias": False},
    ]
    func = make_func(adm="01/01/2026", ferias=ferias)
    d = make_data([func])
    erros = app.validar_agendamento(d, func, datetime(2026, 9, 1), datetime(2026, 9, 15))
    assert any("Limite de 30 dias" in e for e in erros)


def test_validation_rejects_too_many_periods():
    ferias = [
        {"inicio": "01/03/2026", "fim": "10/03/2026", "venda_ferias": False},
        {"inicio": "01/05/2026", "fim": "10/05/2026", "venda_ferias": False},
        {"inicio": "01/07/2026", "fim": "10/07/2026", "venda_ferias": False},
    ]
    func = make_func(adm="01/01/2026", ferias=ferias)
    d = make_data([func])
    erros = app.validar_agendamento(d, func, datetime(2026, 9, 1), datetime(2026, 9, 5))
    assert any("Limite de 3 período(s)" in e for e in erros)


def test_validation_rejects_concurrent_vacation_in_same_subsector():
    ana = make_func(nome="Ana", adm="01/01/2026")
    bruno = make_func(
        nome="Bruno",
        adm="01/01/2026",
        ferias=[{"inicio": "10/09/2026", "fim": "20/09/2026", "venda_ferias": False}],
    )
    d = make_data([ana, bruno])
    erros = app.validar_agendamento(d, ana, datetime(2026, 9, 15), datetime(2026, 9, 19))
    assert any("Férias simultâneas não permitidas" in e for e in erros)


def test_validation_allows_concurrent_vacation_when_rule_enabled():
    ana = make_func(nome="Ana", adm="01/01/2026")
    bruno = make_func(
        nome="Bruno",
        adm="01/01/2026",
        ferias=[{"inicio": "10/09/2026", "fim": "20/09/2026", "venda_ferias": False}],
    )
    d = make_data([ana, bruno], {"permite_concomitantes": True, "max_concomitantes": 2})
    erros = app.validar_agendamento(d, ana, datetime(2026, 9, 15), datetime(2026, 9, 19))
    assert not any("Férias simultâneas não permitidas" in e for e in erros)


def test_validation_respects_maximum_concurrent_employees():
    ana = make_func(nome="Ana", adm="01/01/2026")
    bruno = make_func(nome="Bruno", adm="01/01/2026", ferias=[{"inicio": "10/09/2026", "fim": "20/09/2026", "venda_ferias": False}])
    carla = make_func(nome="Carla", adm="01/01/2026", ferias=[{"inicio": "12/09/2026", "fim": "18/09/2026", "venda_ferias": False}])
    d = make_data([ana, bruno, carla], {"permite_concomitantes": True, "max_concomitantes": 1})
    erros = app.validar_agendamento(d, ana, datetime(2026, 9, 15), datetime(2026, 9, 19))
    assert any("Máximo de 1 simultâneo(s)" in e for e in erros)


def test_validation_rejects_advance_notice_when_configured():
    func = make_func(adm="01/01/2026")
    d = make_data([func], {"aviso_previo_dias": 30})
    inicio = datetime.today() + app.timedelta(days=10)
    fim = inicio + app.timedelta(days=4)
    erros = app.validar_agendamento(d, func, inicio, fim)
    assert any("Antecedência mínima de 30" in e for e in erros)


def test_audit_detects_sale_of_vacation_when_not_allowed():
    func = make_func(
        adm="01/01/2026",
        ferias=[{"inicio": "01/09/2026", "fim": "10/09/2026", "venda_ferias": True}],
    )
    d = make_data([func])
    pendencias = app.auditar_func(d, func)
    assert any("Venda de férias marcada" in erro for p in pendencias for erro in p["erros"])


def test_audit_detects_excess_periods_and_days():
    ferias = [
        {"inicio": "01/03/2026", "fim": "15/03/2026", "venda_ferias": False},
        {"inicio": "01/05/2026", "fim": "15/05/2026", "venda_ferias": False},
        {"inicio": "01/07/2026", "fim": "15/07/2026", "venda_ferias": False},
        {"inicio": "01/09/2026", "fim": "05/09/2026", "venda_ferias": False},
    ]
    func = make_func(adm="01/01/2026", ferias=ferias)
    d = make_data([func])
    pendencias = app.auditar_func(d, func)
    textos = [erro for p in pendencias for erro in p["erros"]]
    assert any("período(s)" in erro and "máximo: 3" in erro for erro in textos)
    assert any("dia(s) no prd.aquisitivo" in erro and "máximo: 30" in erro for erro in textos)
