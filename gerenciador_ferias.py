#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerenciador de Férias — aplicação CLI para equipes Linux.

Versão: 4.3.0

Aplicação local, sem dependências externas, baseada em SQLite. O programa
mantém o histórico de férias, regras, usuários, relatórios, validações,
calendário, painel e backups em um único banco de dados.

Compatibilidade:
    Python 3.9+ e terminais Linux compatíveis com ANSI/UTF-8.

Armazenamento:
    Por padrão em ~/.local/share/gerenciador-ferias/. É possível alterar o
    diretório com GERENCIADOR_FERIAS_DATA_DIR ou XDG_DATA_HOME.
"""

import getpass
import hashlib
import json
import locale
import re
import os
import secrets
import shutil
import sqlite3
import sys
import time
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        pass
for _locale_name in ('pt_BR.UTF-8', 'pt_BR'):
    try:
        locale.setlocale(locale.LC_ALL, _locale_name)
        break
    except locale.Error:
        continue
APP_NAME = 'gerenciador-ferias'
APP_VERSION = '4.3.0'

def _data_dir() -> Path:
    configured = os.environ.get('GERENCIADOR_FERIAS_DATA_DIR')
    if configured:
        return Path(configured).expanduser().resolve()
    xdg_data_home = os.environ.get('XDG_DATA_HOME')
    if xdg_data_home:
        return Path(xdg_data_home).expanduser() / APP_NAME
    return Path.home() / '.local' / 'share' / APP_NAME
DATA_DIR = _data_dir()
DATA_DIR.mkdir(parents=True, exist_ok=True)
BANCO_DADOS = DATA_DIR / 'dados_ferias.db'
BACKUP_DIR = DATA_DIR / 'backups'
LARGURA_MIN = 62
LARGURA_MAX = 110
SEP = '::'
SESSAO = {'login': None, 'nome': None, 'nivel': None}

# ---------------------------------------------------------------------------
# Tema visual da interface CLI
# ---------------------------------------------------------------------------
# Paleta baseada em azul/teal, com contraste moderado para uso prolongado.
# Hierarquia: bordas azul, títulos ciano, opções claras, entradas azul-claro,
# mensagens de sucesso verde, alerta amarelo e erro vermelho.
# Pode ser desativada com NO_COLOR=1 ou automaticamente em terminais sem ANSI.
RESET = '\x1b[0m'
BOLD = '\x1b[1m'
DIM = '\x1b[2m'
FG = {
    'text': '\x1b[38;5;252m',
    'muted': '\x1b[38;5;245m',
    'border': '\x1b[38;5;39m',
    'title': '\x1b[1;38;5;45m',
    'menu': '\x1b[38;5;255m',
    'accent': '\x1b[38;5;51m',
    'success': '\x1b[38;5;78m',
    'warning': '\x1b[38;5;220m',
    'error': '\x1b[38;5;203m',
    'input': '\x1b[38;5;81m',
}

def _cores_ativas():
    return sys.stdout.isatty() and os.environ.get('TERM') != 'dumb' and 'NO_COLOR' not in os.environ

def _c(texto, cor='text', forte=False):
    if not _cores_ativas():
        return str(texto)
    prefix = BOLD if forte else ''
    return prefix + FG.get(cor, FG['text']) + str(texto) + RESET

def _c_border(texto): return _c(texto, 'border')
def _c_title(texto): return _c(texto, 'title', True)
def _c_menu(texto): return _c(texto, 'menu')
def _c_muted(texto): return _c(texto, 'muted')
def _c_success(texto): return _c(texto, 'success', True)
def _c_warning(texto): return _c(texto, 'warning', True)
def _c_error(texto): return _c(texto, 'error', True)
def _c_input(texto): return _c(texto, 'input', True)

def _colorize_line(texto):
    texto = str(texto)
    return texto if ANSI_RE.search(texto) else _c(texto)
_FLASH = {'msg': None, 'erro': False}
_IDIOMA = ['pt']
_BUF = None

# ---------------------------------------------------------------------------
# Estado da interface e internacionalização
# ---------------------------------------------------------------------------

def flash(msg, erro=False):
    _FLASH['msg'] = msg
    _FLASH['erro'] = erro

def _get_flash():
    msg = _FLASH['msg']
    _FLASH['msg'] = None
    return (msg, _FLASH['erro'])
T = {'sim': {'pt': 's', 'en': 'y'}, 'nao': {'pt': 'n', 'en': 'n'}, 'cancelar': {'pt': 'Cancelar', 'en': 'Cancel'}, 'voltar': {'pt': 'Voltar', 'en': 'Back'}, 'sair': {'pt': 'Sair', 'en': 'Exit'}, 'salvar_voltar': {'pt': 'Salvar e Voltar', 'en': 'Save and Back'}, 'opcao': {'pt': 'Opção:', 'en': 'Option:'}, 'enter': {'pt': '[ENTER para continuar...]', 'en': '[ENTER to continue...]'}, 'invalido': {'pt': 'Opção inválida.', 'en': 'Invalid option.'}, 'so_numero': {'pt': 'Digite apenas um número.', 'en': 'Numbers only.'}, 'fora_intervalo': {'pt': 'Número fora do intervalo.', 'en': 'Number out of range.'}, 'nome_vazio': {'pt': 'O nome não pode ser vazio.', 'en': 'Name cannot be empty.'}, 'sem_ferias': {'pt': 'Sem férias agendadas.', 'en': 'No vacations scheduled.'}, 'nenhum_setor': {'pt': 'Nenhum setor cadastrado.', 'en': 'No department registered.'}, 'nenhum_sub': {'pt': 'Nenhum subsetor cadastrado.', 'en': 'No sub-dept registered.'}, 'nenhum_func': {'pt': 'Nenhum funcionário cadastrado.', 'en': 'No employee registered.'}, 'nenhum_vinculo': {'pt': 'Nenhum vínculo cadastrado.', 'en': 'No contract type registered.'}, 'sem_sub': {'pt': '(sem subsetores)', 'en': '(no sub-departments)'}, 'sem_func': {'pt': '(sem funcionários)', 'en': '(no employees)'}, 'excluir_cancel': {'pt': 'Exclusão cancelada.', 'en': 'Deletion cancelled.'}, 'confirmar_excl': {'pt': 'Confirmar exclusão? (s/n):', 'en': 'Confirm deletion? (y/n):'}, 'pag_pag': {'pt': 'Página', 'en': 'Page'}, 'pag_de': {'pt': 'de', 'en': 'of'}, 'pag_itens': {'pt': 'itens', 'en': 'items'}, 'pag_nav_ambas': {'pt': '[A]=Anterior  [P]=Próxima  [N]=Ir para  [0]=Sair', 'en': '[A]=Prev  [P]=Next  [N]=Go  [0]=Exit'}, 'pag_nav_prox': {'pt': '[P]=Próxima  [N]=Ir para  [0]=Sair', 'en': '[P]=Next  [N]=Go  [0]=Exit'}, 'pag_nav_ant': {'pt': '[A]=Anterior  [N]=Ir para  [0]=Sair', 'en': '[A]=Prev  [N]=Go  [0]=Exit'}, 'pag_nav_unica': {'pt': '[0]=Sair', 'en': '[0]=Exit'}, 'pag_cmd': {'pt': 'Navegar:', 'en': 'Navigate:'}, 'pag_ir_para': {'pt': 'Ir para (1–{n}):', 'en': 'Go to (1–{n}):'}, 'graf_titulo': {'pt': 'GRÁFICO DE EVOLUÇÃO MENSAL', 'en': 'MONTHLY EVOLUTION CHART'}, 'm_grafico': {'pt': 'Gráfico de evolução mensal', 'en': 'Monthly evolution chart'}, 'graf_escolha_tipo': {'pt': 'Tipo de gráfico:', 'en': 'Chart type:'}, 'graf_empresa': {'pt': 'Empresa completa', 'en': 'Whole company'}, 'graf_setor': {'pt': 'Por setor', 'en': 'By department'}, 'graf_subsetor': {'pt': 'Por subsetor', 'en': 'By sub-department'}, 'graf_funcionario': {'pt': 'Por funcionário', 'en': 'By employee'}, 'graf_periodo': {'pt': 'Período', 'en': 'Period'}, 'graf_total_periodo': {'pt': 'Total no período', 'en': 'Total in period'}, 'graf_meses_ativos': {'pt': 'Meses com férias', 'en': 'Months with vacations'}, 'graf_sem_dados': {'pt': 'Sem dados para o período selecionado.', 'en': 'No data for selected period.'}, 'graf_3m': {'pt': 'Últimos  3 meses', 'en': 'Last  3 months'}, 'graf_6m': {'pt': 'Últimos  6 meses', 'en': 'Last  6 months'}, 'graf_12m': {'pt': 'Últimos 12 meses  [padrão]', 'en': 'Last 12 months  [default]'}, 'graf_24m': {'pt': 'Últimos 24 meses', 'en': 'Last 24 months'}, 'graf_detalhe': {'pt': '[P]=Detalhado por funcionário', 'en': '[P]=Detailed by employee'}, 'menu_nenhum_agora': {'pt': 'Ninguém em férias agora', 'en': 'Nobody on vacation now'}, 'menu_inicio_label': {'pt': 'Próximos {n} dias', 'en': 'Next {n} days'}, 'menu_nenhum_prox': {'pt': 'Nenhuma entrada nos próximos {n} dias', 'en': 'No starts in the next {n} days'}, 'rel_saldo': {'pt': 'Saldo de dias de férias', 'en': 'Vacation days balance'}, 'rel_saldo_titulo': {'pt': 'SALDO DE DIAS DE FÉRIAS', 'en': 'VACATION DAYS BALANCE'}, 'rel_saldo_todos': {'pt': 'Todos os funcionários', 'en': 'All employees'}, 'rel_saldo_setor': {'pt': 'Por setor', 'en': 'By department'}, 'rel_saldo_sub': {'pt': 'Por subsetor', 'en': 'By sub-department'}, 'rel_saldo_ok': {'pt': 'Regular', 'en': 'Regular'}, 'rel_saldo_neg': {'pt': 'EXCEDIDO', 'en': 'EXCEEDED'}, 'rel_saldo_sem_lim': {'pt': 'Ilimitado', 'en': 'Unlimited'}, 'rel_saldo_usando': {'pt': 'usando ano civil', 'en': 'using calendar year'}, 'rel_saldo_tot_func': {'pt': 'Total de funcionários', 'en': 'Total employees'}, 'rel_saldo_excedidos': {'pt': 'Com saldo excedido', 'en': 'Exceeded balance'}, 'rel_saldo_sem_saldo': {'pt': 'Com saldo disponível', 'en': 'Available balance'}, 'rel_saldo_total_dias': {'pt': 'Total de dias tirados', 'en': 'Total days taken'}, 'pa_atual': {'pt': 'Período aquisitivo atual', 'en': 'Current acquisition period'}, 'pa_tirados': {'pt': 'Tirados', 'en': 'Taken'}, 'pa_restantes': {'pt': 'Restantes', 'en': 'Remaining'}, 'pa_progresso': {'pt': 'Progresso', 'en': 'Progress'}, 'pa_ilimitado': {'pt': '(sem limite definido)', 'en': '(no limit defined)'}, 'pa_dias': {'pt': 'dias', 'en': 'days'}, 'pa_sem_admissao': {'pt': '(sem data de admissão — usando ano civil)', 'en': '(no hire date — using calendar year)'}, 'rel_titulo': {'pt': 'RELATÓRIOS', 'en': 'REPORTS'}, 'rel_pa_menu': {'pt': 'Por período aquisitivo', 'en': 'By acquisition period'}, 'rel_pa_titulo': {'pt': 'RELATÓRIO POR PERÍODO AQUISITIVO', 'en': 'REPORT BY ACQUISITION PERIOD'}, 'rel_pa_todos': {'pt': 'Todos os funcionários', 'en': 'All employees'}, 'rel_pa_setor': {'pt': 'Por setor', 'en': 'By department'}, 'rel_pa_sub': {'pt': 'Por subsetor', 'en': 'By sub-department'}, 'rel_pa_func': {'pt': 'Por funcionário', 'en': 'By employee'}, 'rel_pa_filtro': {'pt': 'Filtrar por:', 'en': 'Filter by:'}, 'rel_individual': {'pt': 'Relatório individual', 'en': 'Individual report'}, 'rel_individual_t': {'pt': 'RELATÓRIO INDIVIDUAL DE FUNCIONÁRIO', 'en': 'INDIVIDUAL EMPLOYEE REPORT'}, 'rel_multi': {'pt': 'Múltiplos funcionários', 'en': 'Multiple employees'}, 'rel_multi_titulo': {'pt': 'RELATÓRIO — FUNCIONÁRIOS SELECIONADOS', 'en': 'REPORT — SELECTED EMPLOYEES'}, 'rel_multi_lista': {'pt': 'Funcionários selecionados:', 'en': 'Selected employees:'}, 'rel_multi_vazio': {'pt': 'Nenhum funcionário selecionado.', 'en': 'No employees selected.'}, 'rel_multi_dup': {'pt': 'Funcionário já adicionado à seleção.', 'en': 'Employee already in selection.'}, 'rel_multi_gerenciar': {'pt': '[A]=Adicionar  [R]=Remover  [G]=Gerar  [0]=Cancelar', 'en': '[A]=Add  [R]=Remove  [G]=Generate  [0]=Cancel'}, 'rel_selecionados': {'pt': 'selecionado(s)', 'en': 'selected'}, 'rel_geral': {'pt': 'Geral — toda a empresa', 'en': 'General — whole company'}, 'rel_setor': {'pt': 'Por setor', 'en': 'By department'}, 'rel_sub': {'pt': 'Por subsetor', 'en': 'By sub-department'}, 'rel_periodo': {'pt': 'Por período de datas', 'en': 'By date range'}, 'rel_situacao': {'pt': 'Situação de férias', 'en': 'Vacation status'}, 'rel_vencidas': {'pt': 'Férias vencidas', 'en': 'Overdue vacations'}, 'rel_ano': {'pt': 'Por ano civil (complemento)', 'en': 'By calendar year'}, 'rel_ano_titulo': {'pt': 'RELATÓRIO POR ANO CIVIL', 'en': 'VACATION REPORT BY CALENDAR YEAR'}, 'rel_ano_pedir': {'pt': 'Ano (ex: 2026) ou ENTER para o ano atual:', 'en': 'Year (e.g. 2026) or ENTER for current year:'}, 'rel_ano_inv': {'pt': 'Ano inválido. Use entre 2000 e {max}.', 'en': 'Invalid year. Use between 2000 and {max}.'}, 'rel_ano_todos': {'pt': 'Todos os funcionários', 'en': 'All employees'}, 'rel_ano_setor': {'pt': 'Por setor', 'en': 'By department'}, 'rel_ano_sub': {'pt': 'Por subsetor', 'en': 'By sub-department'}, 'rel_ano_func': {'pt': 'Por funcionário', 'en': 'By employee'}, 'rel_ano_vazio': {'pt': 'Nenhuma férias encontrada para {ano}.', 'en': 'No vacations found for {ano}.'}, 'rel_ano_label': {'pt': 'Ano consultado', 'en': 'Queried year'}, 'rel_ano_total': {'pt': 'Total de dias no ano civil', 'en': 'Total days in calendar year'}, 'rel_ano_cruzou': {'pt': '(cruza ano)', 'en': '(crosses year)'}, 'rel_data': {'pt': 'Data do relatório', 'en': 'Report date'}, 'rel_periodo_c': {'pt': 'Período consultado', 'en': 'Queried period'}, 'rel_encontrados': {'pt': 'Funcionários encontrados', 'en': 'Employees found'}, 'rel_nenhum_p': {'pt': 'Nenhum funcionário com férias neste período.', 'en': 'No employees with vacations in this period.'}, 'rel_set_cad': {'pt': 'Setores cadastrados', 'en': 'Departments'}, 'rel_subs': {'pt': 'Subsetores', 'en': 'Sub-departments'}, 'rel_total_func': {'pt': 'Total de funcionários', 'en': 'Total employees'}, 'rel_com_ferias': {'pt': 'Com férias', 'en': 'With vacations'}, 'rel_sem_ferias': {'pt': 'Sem férias', 'en': 'Without vacations'}, 'rel_tot_dias': {'pt': 'Total de dias de férias', 'en': 'Total vacation days'}, 'rel_dias_per': {'pt': 'dias no período', 'en': 'days in period'}, 'rel_tot_per': {'pt': 'Total de dias no período', 'en': 'Total days in period'}, 'rel_periodos': {'pt': 'Períodos agendados', 'en': 'Scheduled periods'}, 'rel_total_label': {'pt': 'Total', 'en': 'Total'}, 'rel_dias_unit': {'pt': 'dias', 'en': 'days'}, 'rel_vinculo': {'pt': 'Vínculo', 'en': 'Contract'}, 'rel_nome': {'pt': 'Nome', 'en': 'Name'}, 'rel_setor_l': {'pt': 'Setor', 'en': 'Department'}, 'rel_sub_l': {'pt': 'Subsetor', 'en': 'Sub-dept'}, 'rel_inicio': {'pt': 'Início', 'en': 'Start'}, 'rel_termino': {'pt': 'Término', 'en': 'End'}, 'rel_dias': {'pt': 'Dias', 'en': 'Days'}, 'rel_status': {'pt': 'Status', 'en': 'Status'}, 'rel_venda': {'pt': 'Venda férias', 'en': 'Vacation sale'}, 'rel_andamento': {'pt': 'EM ANDAMENTO', 'en': 'IN PROGRESS'}, 'rel_futuro': {'pt': 'FUTURO', 'en': 'UPCOMING'}, 'rel_concluido': {'pt': 'CONCLUÍDO', 'en': 'COMPLETED'}, 'rel_interv': {'pt': 'Informe o intervalo de datas:', 'en': 'Enter the date range:'}, 'rel_agendamentos': {'pt': 'Agendamentos:', 'en': 'Schedules:'}, 'rel_funclist': {'pt': 'Funcionários:', 'en': 'Employees:'}, 'dias_restantes': {'pt': 'Restantes', 'en': 'Remaining'}, 'dias_ilimitado': {'pt': '(sem limite anual)', 'en': '(no annual limit)'}, 'periodos_passados': {'pt': 'Períodos concluídos', 'en': 'Completed periods'}, 'periodos_futuros': {'pt': 'Períodos futuros', 'en': 'Upcoming periods'}, 'ferias_em_dia': {'pt': 'Em dia', 'en': 'Up to date'}, 'ferias_vencidas': {'pt': 'FÉRIAS VENCIDAS', 'en': 'OVERDUE VACATION'}, 'ferias_a_vencer': {'pt': 'A vencer', 'en': 'Expiring soon'}, 'ferias_pendentes': {'pt': 'Pendente', 'en': 'Pending'}, 'sem_admissao': {'pt': '(sem data de admissão)', 'en': '(no hire date)'}, 'data_admissao': {'pt': 'Data de admissão:', 'en': 'Hire date:'}, 'periodo_aquisitivo': {'pt': 'Período aquisitivo', 'en': 'Acquisition period'}, 'periodo_concessivo': {'pt': 'Período concessivo até', 'en': 'Concession deadline'}, 'nenhum_vencido': {'pt': 'Nenhum funcionário com férias vencidas.', 'en': 'No employees with overdue vacations.'}, 'vencida_em': {'pt': 'Venceu em', 'en': 'Expired on'}, 'dias_para_vencer': {'pt': 'dias para vencer', 'en': 'days to expire'}, 'admissao_inv': {'pt': 'Data de admissão inválida. Use DD/MM/AAAA.', 'en': 'Invalid hire date. Use DD/MM/YYYY.'}, 'situacao_label': {'pt': 'Situação', 'en': 'Status'}, 'rel_sit_titulo': {'pt': 'SITUAÇÃO DE FÉRIAS — TODOS', 'en': 'VACATION STATUS — ALL'}, 'func_vencidas': {'pt': 'Funcionários com Férias Vencidas', 'en': 'Employees with Overdue Vacations'}, 'dir_asc_curto': {'pt': 'A→Z', 'en': 'A→Z'}, 'dir_desc_curto': {'pt': 'Z→A', 'en': 'Z→A'}, 'login_titulo': {'pt': 'LOGIN DO SISTEMA', 'en': 'SYSTEM LOGIN'}, 'login_usuario': {'pt': 'Usuário:', 'en': 'Username:'}, 'login_senha': {'pt': 'Senha:', 'en': 'Password:'}, 'login_erro': {'pt': 'Usuário ou senha incorretos. Tente novamente.', 'en': 'Incorrect credentials. Try again.'}, 'login_bloq': {'pt': 'Conta bloqueada após 3 tentativas.', 'en': 'Account locked after 3 attempts.'}, 'nivel_admin': {'pt': 'Administrador', 'en': 'Administrator'}, 'nivel_usuario': {'pt': 'Usuário', 'en': 'User'}, 'acesso_negado': {'pt': 'Acesso restrito ao Administrador.', 'en': 'Administrator access only.'}, 'menu_titulo': {'pt': 'GERENCIAMENTO DE FÉRIAS  v4.2.0', 'en': 'VACATION MANAGEMENT SYSTEM  v3.8.1'}, 'm_setores': {'pt': 'Setores e subsetores', 'en': 'Departments'}, 'm_funcs': {'pt': 'Funcionários e vínculos', 'en': 'Employees & contracts'}, 'm_ferias': {'pt': 'Férias', 'en': 'Vacations'}, 'm_relat': {'pt': 'Relatórios', 'en': 'Reports'}, 'm_regras': {'pt': 'Regras de férias', 'en': 'Vacation rules'}, 'm_valid': {'pt': 'Validação automática', 'en': 'Auto validation'}, 'm_config': {'pt': 'Configurações de exibição', 'en': 'Display settings'}, 'm_admin': {'pt': 'Administração do sistema', 'en': 'System administration'}, 'm_painel': {'pt': 'Painel de férias', 'en': 'Vacation panel'}, 'status_ok': {'pt': 'Sistema sem pendências.', 'en': 'No issues found.'}, 'status_pend': {'pt': 'ATENÇÃO: {n} pendência(s) detectada(s)', 'en': 'WARNING: {n} issue(s) detected'}, 'logado': {'pt': 'Logado como:', 'en': 'Logged in as:'}, 'exibicao': {'pt': 'Exibição:', 'en': 'Display:'}, 'ferias_venc_alerta': {'pt': 'FÉRIAS VENCIDAS: {n} funcionário(s)', 'en': 'OVERDUE: {n} employee(s)'}, 'painel_titulo': {'pt': 'PAINEL DE FÉRIAS', 'en': 'VACATION PANEL'}, 'painel_agora': {'pt': 'EM FÉRIAS AGORA', 'en': 'ON VACATION NOW'}, 'painel_30dias': {'pt': 'PRÓXIMOS 30 DIAS', 'en': 'STARTING WITHIN 30 DAYS'}, 'painel_nenhum_ag': {'pt': 'Nenhum funcionário em férias no momento.', 'en': 'No employees on vacation right now.'}, 'painel_nenhum_30': {'pt': 'Nenhum funcionário entra de férias nos próximos 30 dias.', 'en': 'No employees starting vacation in the next 30 days.'}, 'painel_termina': {'pt': 'Termina em', 'en': 'Ends in'}, 'painel_inicia': {'pt': 'Inicia em', 'en': 'Starts in'}, 'painel_dias_rest': {'pt': 'dia(s) restante(s)', 'en': 'day(s) remaining'}, 'painel_dias_ini': {'pt': 'dia(s) para iniciar', 'en': 'day(s) to start'}, 'painel_em_ferias': {'pt': 'Em férias agora', 'en': 'On vacation now'}, 'painel_em_30d': {'pt': 'Iniciam em até 30 dias', 'en': 'Starting within 30 days'}, 'painel_alerta': {'pt': 'Em férias: {agora}  |  Próximos 30 dias: {em30}', 'en': 'On vacation: {agora}  |  Next 30 days: {em30}'}, 'adm_titulo': {'pt': 'ADMINISTRAÇÃO DO SISTEMA', 'en': 'SYSTEM ADMINISTRATION'}, 'adm_usuarios': {'pt': 'Usuários do sistema', 'en': 'System users'}, 'adm_backup': {'pt': 'Backup e restauração', 'en': 'Backup & restore'}, 'adm_apagar': {'pt': 'Apagar todos os dados', 'en': 'Delete all data'}, 'adm_idioma': {'pt': 'Idioma / Language', 'en': 'Idioma / Language'}, 'usr_titulo': {'pt': 'USUÁRIOS DO SISTEMA', 'en': 'SYSTEM USERS'}, 'usr_listar': {'pt': 'Listar usuários', 'en': 'List users'}, 'usr_criar': {'pt': 'Criar usuário', 'en': 'Create user'}, 'usr_senha': {'pt': 'Alterar senha', 'en': 'Change password'}, 'usr_excluir': {'pt': 'Excluir usuário', 'en': 'Delete user'}, 'usr_nova_senha': {'pt': 'Nova senha:', 'en': 'New password:'}, 'usr_conf_senha': {'pt': 'Confirme a senha:', 'en': 'Confirm password:'}, 'usr_nivel': {'pt': 'Nível (1=Admin / 2=Usuário):', 'en': 'Level (1=Admin / 2=User):'}, 'usr_senha_dif': {'pt': 'As senhas não conferem.', 'en': 'Passwords do not match.'}, 'usr_ja_existe': {'pt': 'Login já cadastrado.', 'en': 'Login already exists.'}, 'usr_ultimo_adm': {'pt': 'Não é possível excluir o único administrador.', 'en': 'Cannot delete the only administrator.'}, 'usr_proprio': {'pt': 'Não é possível excluir seu próprio usuário.', 'en': 'Cannot delete your own account.'}, 'usr_nenhum': {'pt': 'Nenhum usuário cadastrado.', 'en': 'No users registered.'}, 'usr_criado': {'pt': 'Usuário criado com sucesso!', 'en': 'User created successfully!'}, 'usr_excluido': {'pt': 'Usuário excluído com sucesso!', 'en': 'User deleted successfully!'}, 'usr_senha_ok': {'pt': 'Senha alterada com sucesso!', 'en': 'Password changed successfully!'}, 'bkp_titulo': {'pt': 'BACKUP E RESTAURAÇÃO', 'en': 'BACKUP & RESTORE'}, 'bkp_fazer': {'pt': 'Fazer backup agora', 'en': 'Create backup now'}, 'bkp_restaurar': {'pt': 'Restaurar backup', 'en': 'Restore backup'}, 'bkp_listar': {'pt': 'Listar backups', 'en': 'List backups'}, 'bkp_ok': {'pt': 'Backup criado: ', 'en': 'Backup created: '}, 'bkp_rest_ok': {'pt': 'Backup restaurado com sucesso!', 'en': 'Backup restored successfully!'}, 'bkp_nenhum': {'pt': 'Nenhum backup encontrado.', 'en': 'No backups found.'}, 'bkp_confirma': {'pt': 'Restaurar substituirá os dados atuais. Confirmar? (s/n):', 'en': 'Restore will replace current data. Confirm? (y/n):'}, 'bkp_cancel': {'pt': 'Restauração cancelada.', 'en': 'Restore cancelled.'}, 'apg_titulo': {'pt': 'APAGAR TODOS OS DADOS', 'en': 'DELETE ALL DATA'}, 'apg_aviso1': {'pt': 'ATENÇÃO: Esta ação é IRREVERSÍVEL!', 'en': 'WARNING: This action is IRREVERSIBLE!'}, 'apg_aviso2': {'pt': 'Todos os dados serão apagados permanentemente.', 'en': 'All data will be permanently deleted.'}, 'apg_instrucao': {'pt': 'Digite CONFIRMAR para prosseguir:', 'en': 'Type CONFIRM to proceed:'}, 'apg_palavra': {'pt': 'CONFIRMAR', 'en': 'CONFIRM'}, 'apg_ok': {'pt': 'Todos os dados foram apagados.', 'en': 'All data has been deleted.'}, 'apg_cancel': {'pt': 'Operação cancelada.', 'en': 'Operation cancelled.'}, 'idioma_titulo': {'pt': 'IDIOMA / LANGUAGE', 'en': 'IDIOMA / LANGUAGE'}, 'idioma_atual': {'pt': 'Idioma atual:', 'en': 'Current language:'}, 'idioma_pt': {'pt': 'Português (PT-BR)', 'en': 'Portuguese (PT-BR)'}, 'idioma_en': {'pt': 'English (EN)', 'en': 'English (EN)'}, 'idioma_ok': {'pt': 'Idioma alterado!', 'en': 'Language changed!'}, 'set_titulo': {'pt': 'SETORES E SUBSETORES', 'en': 'DEPARTMENTS'}, 'set_listar': {'pt': 'Listar setores', 'en': 'List departments'}, 'set_novo': {'pt': 'Novo setor', 'en': 'New department'}, 'set_excluir': {'pt': 'Excluir setor', 'en': 'Delete department'}, 'set_novo_sub': {'pt': 'Novo subsetor', 'en': 'New sub-department'}, 'set_excluir_sub': {'pt': 'Excluir subsetor', 'en': 'Delete sub-department'}, 'set_nome': {'pt': 'Nome do setor:', 'en': 'Department name:'}, 'sub_nome': {'pt': 'Nome do subsetor:', 'en': 'Sub-dept name:'}, 'set_ja_existe': {'pt': 'Setor já cadastrado.', 'en': 'Department already exists.'}, 'sub_ja_existe': {'pt': 'Subsetor já cadastrado.', 'en': 'Sub-dept already exists.'}, 'set_criado': {'pt': 'Setor criado com sucesso!', 'en': 'Department created!'}, 'sub_criado': {'pt': 'Subsetor criado com sucesso!', 'en': 'Sub-dept created!'}, 'set_excluido': {'pt': 'Setor excluído com sucesso!', 'en': 'Department deleted!'}, 'sub_excluido': {'pt': 'Subsetor excluído com sucesso!', 'en': 'Sub-dept deleted!'}, 'set_vinculados': {'pt': 'Não é possível excluir: {n} funcionário(s) vinculado(s).', 'en': 'Cannot delete: {n} linked employee(s).'}, 'set_disponiveis': {'pt': 'Setores disponíveis:', 'en': 'Available departments:'}, 'sub_disponiveis': {'pt': 'Subsetores de', 'en': 'Sub-departments of'}, 'vin_titulo': {'pt': 'VÍNCULOS', 'en': 'CONTRACT TYPES'}, 'vin_listar': {'pt': 'Listar vínculos', 'en': 'List contract types'}, 'vin_novo': {'pt': 'Novo vínculo', 'en': 'New contract type'}, 'vin_excluir': {'pt': 'Excluir vínculo', 'en': 'Delete contract type'}, 'vin_nome': {'pt': 'Nome do vínculo (ex: CLT, PJ):', 'en': 'Contract type:'}, 'vin_ja_existe': {'pt': 'Vínculo já cadastrado.', 'en': 'Contract type already exists.'}, 'vin_criado': {'pt': 'Vínculo criado com sucesso!', 'en': 'Contract type created!'}, 'vin_excluido': {'pt': 'Vínculo excluído com sucesso!', 'en': 'Contract type deleted!'}, 'vin_em_uso': {'pt': 'Não é possível excluir: {n} funcionário(s) com este vínculo.', 'en': 'Cannot delete: {n} employee(s) with this contract.'}, 'vin_disponiveis': {'pt': 'Vínculos disponíveis:', 'en': 'Available contracts:'}, 'vin_sem': {'pt': '0. Sem vínculo', 'en': '0. No contract type'}, 'fun_titulo': {'pt': 'FUNCIONÁRIOS', 'en': 'EMPLOYEES'}, 'fun_listar': {'pt': 'Listar funcionários', 'en': 'List employees'}, 'fun_por_setor': {'pt': 'Listar por setor e subsetor', 'en': 'List by department & sub-dept'}, 'fun_novo': {'pt': 'Novo funcionário', 'en': 'New employee'}, 'fun_excluir': {'pt': 'Excluir funcionário', 'en': 'Delete employee'}, 'fun_vinculos': {'pt': 'Gerenciar vínculos', 'en': 'Manage contracts'}, 'fun_nome': {'pt': 'Nome do funcionário:', 'en': 'Employee name:'}, 'fun_vinculo_sel': {'pt': 'Vínculo do funcionário:', 'en': 'Employee contract:'}, 'fun_ja_existe': {'pt': 'Funcionário já cadastrado neste subsetor.', 'en': 'Employee already registered in this sub-dept.'}, 'fun_criado': {'pt': 'Funcionário cadastrado com sucesso!', 'en': 'Employee registered!'}, 'fun_excluido': {'pt': 'Funcionário excluído com sucesso!', 'en': 'Employee deleted!'}, 'fun_lista': {'pt': 'Funcionários:', 'en': 'Employees:'}, 'fer_titulo': {'pt': 'FÉRIAS', 'en': 'VACATIONS'}, 'fer_agendar': {'pt': 'Agendar férias', 'en': 'Schedule vacation'}, 'fer_cancelar': {'pt': 'Cancelar férias', 'en': 'Cancel vacation'}, 'fer_calendario': {'pt': 'Calendário por subsetor', 'en': 'Calendar by sub-dept'}, 'fer_inicio': {'pt': 'Data de início   (DD/MM/AAAA):', 'en': 'Start date (DD/MM/YYYY):'}, 'fer_fim': {'pt': 'Data de término  (DD/MM/AAAA):', 'en': 'End date   (DD/MM/YYYY):'}, 'fer_data_inv': {'pt': 'Data inválida! Use DD/MM/AAAA.', 'en': 'Invalid date! Use DD/MM/YYYY.'}, 'fer_data_ord': {'pt': 'Início posterior ao término.', 'en': 'Start date is after end date.'}, 'fer_bloqueado': {'pt': 'AGENDAMENTO BLOQUEADO — regras violadas:', 'en': 'SCHEDULING BLOCKED — rules violated:'}, 'fer_venda_info': {'pt': 'Venda de férias (abono pecuniário) permitida.', 'en': 'Vacation sale (cash allowance) permitted.'}, 'fer_venda_marcar': {'pt': 'Marcar venda de 1/3? (s/n):', 'en': 'Mark 1/3 vacation sale? (y/n):'}, 'fer_ok': {'pt': 'Férias agendadas com sucesso!', 'en': 'Vacation scheduled!'}, 'fer_removida': {'pt': 'Férias removidas com sucesso!', 'en': 'Vacation removed!'}, 'fer_sem': {'pt': 'não possui férias agendadas.', 'en': 'has no vacations scheduled.'}, 'fer_remover_num': {'pt': 'Número a remover:', 'en': 'Number to remove:'}, 'fer_cal_titulo': {'pt': 'CALENDÁRIO DE FÉRIAS', 'en': 'VACATION CALENDAR'}, 'fer_com_venda': {'pt': '[com venda]', 'en': '[with sale]'}, 'fer_venda_lbl': {'pt': '[venda]', 'en': '[sale]'}, 'reg_titulo': {'pt': 'REGRAS DE FÉRIAS', 'en': 'VACATION RULES'}, 'reg_ver': {'pt': 'Ver todas as regras', 'en': 'View all rules'}, 'reg_global': {'pt': 'Regras globais', 'en': 'Global rules'}, 'reg_vinculo': {'pt': 'Regras por vínculo', 'en': 'Rules by contract'}, 'reg_setor': {'pt': 'Regras por setor', 'en': 'Rules by department'}, 'reg_subsetor': {'pt': 'Regras por subsetor', 'en': 'Rules by sub-department'}, 'reg_hier': {'pt': 'Hierarquia: Subsetor > Setor > Vínculo > Global', 'en': 'Hierarchy: Sub-dept > Dept > Contract > Global'}, 'reg_editar': {'pt': 'EDITAR REGRA', 'en': 'EDIT RULE'}, 'reg_campo': {'pt': 'Campo', 'en': 'Field'}, 'reg_dica': {'pt': 'Dica', 'en': 'Tip'}, 'reg_atual': {'pt': 'Atual', 'en': 'Current'}, 'reg_herdar': {'pt': 'Herdar', 'en': 'Inherit'}, 'reg_herdado': {'pt': 'Herdado', 'en': 'Inherited'}, 'reg_niv_sup': {'pt': 'nível superior', 'en': 'upper level'}, 'reg_s_n_h': {'pt': 's=Sim / n=Não / ENTER=herdar:', 'en': 'y=Yes / n=No / ENTER=inherit:'}, 'reg_s_n_m': {'pt': 's=Sim / n=Não / ENTER=manter:', 'en': 'y=Yes / n=No / ENTER=keep:'}, 'reg_num_h': {'pt': 'Número / ENTER=herdar:', 'en': 'Number / ENTER=inherit:'}, 'reg_num_m': {'pt': 'Número / ENTER=manter:', 'en': 'Number / ENTER=keep:'}, 'reg_herdar_nota': {'pt': '  * ENTER = herdar do nível superior', 'en': '  * ENTER = inherit from upper level'}, 'reg_salvas': {'pt': 'Regras salvas com sucesso!', 'en': 'Rules saved!'}, 'reg_gl_s': {'pt': '▸ GLOBAIS', 'en': '▸ GLOBAL'}, 'reg_vin_s': {'pt': '▸ POR VÍNCULO', 'en': '▸ BY CONTRACT'}, 'reg_set_s': {'pt': '▸ POR SETOR', 'en': '▸ BY DEPARTMENT'}, 'reg_sub_s': {'pt': '▸ POR SUBSETOR', 'en': '▸ BY SUB-DEPARTMENT'}, 'reg_sem_vin': {'pt': '(nenhuma regra específica por vínculo)', 'en': '(no specific rules per contract)'}, 'reg_sem_set': {'pt': '(nenhuma regra específica por setor)', 'en': '(no specific rules per department)'}, 'reg_sem_sub': {'pt': '(nenhuma regra específica por subsetor)', 'en': '(no specific rules per sub-department)'}, 'reg_sel_sub': {'pt': 'Selecione o subsetor para configurar as regras:', 'en': 'Select the sub-department to configure rules:'}, 'val_titulo': {'pt': 'VALIDAÇÃO AUTOMÁTICA', 'en': 'AUTO VALIDATION'}, 'val_ok': {'pt': 'Nenhuma pendência encontrada!', 'en': 'No issues found!'}, 'val_pend': {'pt': 'pendência(s) encontrada(s)', 'en': 'issue(s) found'}, 'val_ver': {'pt': 'Ver todas as pendências', 'en': 'View all issues'}, 'val_por_func': {'pt': 'Validar por funcionário', 'en': 'Validate by employee'}, 'val_por_setor': {'pt': 'Validar por setor', 'en': 'Validate by department'}, 'val_revalid': {'pt': 'Revalidar sistema', 'en': 'Revalidate system'}, 'val_geral_t': {'pt': 'PENDÊNCIAS — SISTEMA COMPLETO', 'en': 'ISSUES — FULL SYSTEM'}, 'val_func_t': {'pt': 'VALIDAÇÃO POR FUNCIONÁRIO', 'en': 'VALIDATE BY EMPLOYEE'}, 'val_setor_t': {'pt': 'VALIDAÇÃO POR SETOR', 'en': 'VALIDATE BY DEPARTMENT'}, 'val_data': {'pt': 'Data da verificação', 'en': 'Verification date'}, 'val_c_pend': {'pt': 'Funcionários com pendências', 'en': 'Employees with issues'}, 'val_total': {'pt': 'Total de pendências', 'en': 'Total issues'}, 'val_conform': {'pt': 'Todos os agendamentos estão em conformidade!', 'en': 'All schedules are compliant!'}, 'val_periodos': {'pt': 'Períodos de férias', 'en': 'Vacation periods'}, 'val_pendencias': {'pt': 'Pendências', 'en': 'Issues'}, 'val_c_pend2': {'pt': 'Com pendências', 'en': 'With issues'}, 'val_revalid_t': {'pt': 'REVALIDANDO SISTEMA...', 'en': 'REVALIDATING...'}, 'val_verificando': {'pt': 'Verificando todos os funcionários e períodos...', 'en': 'Checking all employees and periods...'}, 'val_detalhe': {'pt': "Veja 'Ver Todas as Pendências'.", 'en': "See 'View All Issues'."}, 'cfg_titulo': {'pt': 'CONFIGURAÇÕES DE EXIBIÇÃO', 'en': 'DISPLAY SETTINGS'}, 'cfg_desc': {'pt': 'Ordenação aplicada em todas as telas e relatórios.', 'en': 'Sorting applied across all screens.'}, 'cfg_atual': {'pt': 'Configuração atual:', 'en': 'Current setting:'}, 'cfg_atual_m': {'pt': '[atual]', 'en': '[current]'}, 'cfg_alterar': {'pt': 'ALTERAR:', 'en': 'CHANGE:'}, 'cfg_escolha': {'pt': 'Opção:', 'en': 'Option:'}, 'cfg_salvo': {'pt': 'Configurações salvas!', 'en': 'Settings saved!'}, 'bkp_exportar': {'pt': 'Exportar backup para outro local', 'en': 'Export backup to another location'}, 'bkp_exportar_caminho': {'pt': 'Informe o diretório ou arquivo de destino:', 'en': 'Enter destination directory or file:'}, 'bkp_exportar_ok': {'pt': 'Backup exportado com sucesso:', 'en': 'Backup exported successfully:'}, 'bkp_exportar_erro': {'pt': 'Não foi possível exportar o backup:', 'en': 'Could not export backup:'}, 'bkp_exportar_cancel': {'pt': 'Exportação cancelada.', 'en': 'Export cancelled.'}, 'bkp_local': {'pt': 'Dados locais:', 'en': 'Local data:'}, 'bkp_data_dir': {'pt': 'Diretório de dados', 'en': 'Data directory'}}

T.update({
    'm_cadastros': {'pt': 'Cadastros', 'en': 'Registrations'},
    'ui_menu_principal': {'pt': 'MENU PRINCIPAL', 'en': 'MAIN MENU'},
    'ui_status': {'pt': 'STATUS', 'en': 'STATUS'},
    'ui_agenda': {'pt': 'AGENDA', 'en': 'AGENDA'},
})

# ── Banco de horas ─────────────────────────────────────
T.update({
    'm_banco_horas': {'pt': 'Banco de horas', 'en': 'Time bank'},
    'bh_titulo': {'pt': 'BANCO DE HORAS', 'en': 'TIME BANK'},
    'bh_desc': {'pt': 'Controle de créditos e débitos informados — não é controle de ponto.', 'en': 'Manual credits and debits — not time-clock tracking.'},
    'bh_saldo': {'pt': 'Consultar saldo', 'en': 'View balance'},
    'bh_credito': {'pt': 'Registrar crédito', 'en': 'Record credit'},
    'bh_debito': {'pt': 'Registrar débito', 'en': 'Record debit'},
    'bh_extrato': {'pt': 'Consultar extrato', 'en': 'View statement'},
    'bh_relatorio': {'pt': 'Relatórios e indicadores', 'en': 'Reports and indicators'},
    'bh_ajuste': {'pt': 'Ajustar saldo', 'en': 'Adjust balance'},
    'bh_data': {'pt': 'Data do lançamento (automática):', 'en': 'Entry date (automatic):'},
    'bh_horas': {'pt': 'Quantidade de horas (HH:MM):', 'en': 'Hours quantity (HH:MM):'},
    'bh_ajuste_horas': {'pt': 'Ajuste (+HH:MM ou -HH:MM):', 'en': 'Adjustment (+HH:MM or -HH:MM):'},
    'bh_motivo': {'pt': 'Motivo:', 'en': 'Reason:'},
    'bh_data_inv': {'pt': 'Data inválida.', 'en': 'Invalid date.'},
    'bh_horas_inv': {'pt': 'Duração inválida. Use HH:MM.', 'en': 'Invalid duration. Use HH:MM.'},
    'bh_ajuste_inv': {'pt': 'Ajuste inválido. Use +HH:MM ou -HH:MM.', 'en': 'Invalid adjustment. Use +HH:MM or -HH:MM.'},
    'bh_motivo_inv': {'pt': 'O motivo é obrigatório.', 'en': 'Reason is required.'},
    'bh_sem_mov': {'pt': 'Nenhuma movimentação registrada.', 'en': 'No movements recorded.'},
    'bh_sem_func': {'pt': 'Nenhum funcionário cadastrado.', 'en': 'No employee registered.'},
    'bh_credito_ok': {'pt': 'Crédito registrado.', 'en': 'Credit recorded.'},
    'bh_debito_ok': {'pt': 'Débito registrado.', 'en': 'Debit recorded.'},
    'bh_ajuste_ok': {'pt': 'Ajuste registrado.', 'en': 'Adjustment recorded.'},
    'bh_tipo_credito': {'pt': 'Crédito', 'en': 'Credit'},
    'bh_tipo_debito': {'pt': 'Débito', 'en': 'Debit'},
    'bh_tipo_ajuste': {'pt': 'Ajuste', 'en': 'Adjustment'},
    'bh_total_creditos': {'pt': 'Total de créditos', 'en': 'Total credits'},
    'bh_total_debitos': {'pt': 'Total de débitos', 'en': 'Total debits'},
    'bh_saldo_atual': {'pt': 'Saldo atual', 'en': 'Current balance'},
    'bh_saldo_positivo': {'pt': 'Saldo positivo', 'en': 'Positive balance'},
    'bh_saldo_negativo': {'pt': 'Saldo negativo', 'en': 'Negative balance'},
    'bh_usuario': {'pt': 'Registrado em', 'en': 'Recorded at'},
    'bh_confirmar_ajuste': {'pt': 'Confirmar ajuste? (s/n):', 'en': 'Confirm adjustment? (y/n):'},
    'bh_somente_admin': {'pt': 'Somente administradores podem ajustar o saldo.', 'en': 'Only administrators can adjust the balance.'},
    'bh_historico_imutavel': {'pt': 'O histórico é mantido. Correções devem ser feitas por novo lançamento.', 'en': 'History is preserved. Corrections must be made with a new entry.'},
})


def set_idioma(lang):
    _IDIOMA[0] = lang if lang in ('pt', 'en') else 'pt'

def get_idioma():
    return _IDIOMA[0]

def t(chave, **kw):
    lang = get_idioma()
    txt = T.get(chave, {}).get(lang, T.get(chave, {}).get('pt', chave))
    return txt.format(**kw) if kw else txt

def _dir_curto(cfg):
    return t('dir_asc_curto') if cfg.get('direcao', 'asc') == 'asc' else t('dir_desc_curto')

def _campos_regras():
    lg = get_idioma()
    return {'permite_venda_ferias': {'label': {'pt': 'Permite venda de férias (abono)', 'en': 'Allow vacation sale'}[lg], 'tipo': 'bool', 'padrao': False, 'dica': {'pt': 'Vender até 1/3 das férias em dinheiro', 'en': 'Sell up to 1/3 as cash'}[lg]}, 'max_periodos_ano': {'label': {'pt': 'Máximo de períodos por prd.aquisitivo', 'en': 'Max periods per acquisition period'}[lg], 'tipo': 'int', 'padrao': 3, 'dica': {'pt': 'Limite por período aquisitivo (0=ilimitado)', 'en': 'Limit per acquisition period (0=unlimited)'}[lg]}, 'min_dias_periodo': {'label': {'pt': 'Mínimo de dias por período', 'en': 'Min days per period'}[lg], 'tipo': 'int', 'padrao': 5, 'dica': {'pt': 'Mínimo de dias corridos (0=sem restrição)', 'en': 'Min calendar days (0=none)'}[lg]}, 'max_dias_ano': {'label': {'pt': 'Máximo de dias (por período aquisitivo)', 'en': 'Max days (per acquisition period)'}[lg], 'tipo': 'int', 'padrao': 30, 'dica': {'pt': 'Total de dias por período de 12 meses (0=ilimitado)', 'en': 'Total days per 12-month period (0=unlimited)'}[lg]}, 'permite_concomitantes': {'label': {'pt': 'Permite férias simultâneas no subsetor', 'en': 'Allow concurrent vacations'}[lg], 'tipo': 'bool', 'padrao': False, 'dica': {'pt': 'Se Não, bloqueia sobreposição no subsetor', 'en': 'If No, blocks sub-dept overlap'}[lg]}, 'max_concomitantes': {'label': {'pt': 'Máx. funcionários simultâneos', 'en': 'Max concurrent employees'}[lg], 'tipo': 'int', 'padrao': 1, 'dica': {'pt': 'Aplica se simultâneas forem permitidas (0=ilimitado)', 'en': 'Applies if concurrent allowed (0=unlimited)'}[lg]}, 'aviso_previo_dias': {'label': {'pt': 'Antecedência mínima (dias)', 'en': 'Min advance notice (days)'}[lg], 'tipo': 'int', 'padrao': 0, 'dica': {'pt': 'Dias de antecedência exigidos (0=sem restrição)', 'en': 'Required advance days (0=none)'}[lg]}}
CONFIG_PADRAO = {'ordem_setores': 'nome', 'ordem_subsetores': 'nome', 'ordem_vinculos': 'nome', 'ordem_funcionarios': 'nome', 'ordem_ferias': 'inicio', 'direcao': 'asc'}

def _config_opcoes():
    lg = get_idioma()
    return {'ordem_setores': {'label': {'pt': 'Ordenação de setores', 'en': 'Department sorting'}[lg], 'opcoes': {'nome': {'pt': 'Alfabética', 'en': 'Alphabetical'}[lg], 'cadastro': {'pt': 'Por cadastro', 'en': 'By registration'}[lg]}}, 'ordem_subsetores': {'label': {'pt': 'Ordenação de subsetores', 'en': 'Sub-dept sorting'}[lg], 'opcoes': {'nome': {'pt': 'Alfabética', 'en': 'Alphabetical'}[lg], 'cadastro': {'pt': 'Por cadastro', 'en': 'By registration'}[lg]}}, 'ordem_vinculos': {'label': {'pt': 'Ordenação de vínculos', 'en': 'Contract sorting'}[lg], 'opcoes': {'nome': {'pt': 'Alfabética', 'en': 'Alphabetical'}[lg], 'cadastro': {'pt': 'Por cadastro', 'en': 'By registration'}[lg]}}, 'ordem_funcionarios': {'label': {'pt': 'Ordenação de funcionários', 'en': 'Employee sorting'}[lg], 'opcoes': {'nome': {'pt': 'Por nome', 'en': 'By name'}[lg], 'setor': {'pt': 'Por setor', 'en': 'By department'}[lg], 'subsetor': {'pt': 'Por subsetor', 'en': 'By sub-dept'}[lg], 'vinculo': {'pt': 'Por vínculo', 'en': 'By contract'}[lg], 'cadastro': {'pt': 'Por cadastro', 'en': 'By registration'}[lg]}}, 'ordem_ferias': {'label': {'pt': 'Ordenação de férias', 'en': 'Vacation sorting'}[lg], 'opcoes': {'inicio': {'pt': 'Por data de início', 'en': 'By start date'}[lg], 'fim': {'pt': 'Por data de término', 'en': 'By end date'}[lg], 'dias': {'pt': 'Por duração (dias)', 'en': 'By duration'}[lg], 'cadastro': {'pt': 'Por cadastro', 'en': 'By registration'}[lg]}}, 'direcao': {'label': {'pt': 'Direção da ordenação', 'en': 'Sort direction'}[lg], 'opcoes': {'asc': {'pt': 'Crescente  (A → Z)', 'en': 'Ascending  (A → Z)'}[lg], 'desc': {'pt': 'Decrescente (Z → A)', 'en': 'Descending (Z → A)'}[lg]}}}

# ---------------------------------------------------------------------------
# Renderização da interface CLI — tema e componentes
# ---------------------------------------------------------------------------

# A interface usa poucos componentes visuais, sempre com a mesma hierarquia:
# título > conteúdo > ação/navegação. Isso evita telas com estilos diferentes
# entre módulos e reduz espaços vazios ou divisores redundantes.
LARGURA_MIN = 68
LARGURA_MAX = 112
ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')

_UI = {'last': None, 'has_content': False}


def _cols():
    return shutil.get_terminal_size((80, 24)).columns


def _rows():
    return shutil.get_terminal_size((80, 24)).lines


def _larg():
    cols = _cols()
    # Em terminais estreitos, usa toda a largura disponível sem ultrapassar
    # as margens; em terminais largos, mantém uma coluna visual confortável.
    return max(52, min(LARGURA_MAX, max(52, cols - 4)))


def _recuo():
    return ' ' * max(0, (_cols() - _larg()) // 2)


def _vis(s):
    s = ANSI_RE.sub('', str(s))
    return sum(2 if unicodedata.east_asian_width(c) in ('W', 'F') else 1 for c in s)


def _pl(s, n):
    return s + ' ' * max(0, n - _vis(s))


def _pc(s, n):
    e = max(0, n - _vis(s))
    left = e // 2
    return ' ' * left + s + ' ' * (e - left)


def _wrap(txt, util):
    txt = str(txt)
    if not txt.strip():
        return ['']
    indent = len(txt) - len(txt.lstrip())
    pref = ' ' * indent
    words = txt.strip().split()
    lines, cur = [], pref
    for word in words:
        candidate = cur + ' ' + word if cur.strip() else pref + word
        if _vis(candidate) <= util:
            cur = candidate
        else:
            if cur.strip():
                lines.append(cur)
            # Uma palavra maior que a área útil precisa ser quebrada para
            # impedir desalinhamento ou vazamento para fora da caixa.
            if _vis(word) > util:
                raw = word
                while raw:
                    take, width = 0, 0
                    for ch in raw:
                        cw = 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1
                        if width + cw > util - len(pref):
                            break
                        width += cw
                        take += 1
                    if take <= 0:
                        take = 1
                    lines.append(pref + raw[:take])
                    raw = raw[take:]
                cur = pref
            else:
                cur = pref + word
    if cur.strip():
        lines.append(cur)
    return lines or ['']


def _ln(txt='', align='left'):
    global _BUF
    l = _larg()
    util = l - 4
    partes = _wrap(txt, util) if _vis(txt) > util else [str(txt)]
    for pp in partes:
        if align == 'center':
            c = _pc(pp, util)
        else:
            c = _pl(pp, util)
        if _BUF is not None:
            _BUF.append(('L', c))
        else:
            print(_recuo() + _c_border('│') + ' ' + _colorize_line(c) + ' ' + _c_border('│'))
        _UI['last'] = 'L'
        if pp.strip():
            _UI['has_content'] = True


def _lvz():
    global _BUF
    # Nunca empilha duas linhas vazias nem coloca uma linha vazia logo após
    # um divisor. Essa regra elimina grande parte dos espaços artificiais.
    last = _BUF[-1][0] if _BUF else _UI['last']
    if last in ('V', 'D'):
        return
    if _BUF is not None:
        _BUF.append(('V',))
    else:
        l = _larg()
        print(_recuo() + _c_border('│') + ' ' * (l - 2) + _c_border('│'))
    _UI['last'] = 'V'


def _dleve():
    global _BUF
    last = _BUF[-1][0] if _BUF else _UI['last']
    # Divisor duplicado não acrescenta informação visual.
    if last == 'D':
        return
    if _BUF is not None:
        _BUF.append(('D',))
    else:
        l = _larg()
        print(_recuo() + _c_border('├' + _c_muted('─' * (l - 2)) + '┤'))
    _UI['last'] = 'D'


def _print_buf(item):
    l = _larg()
    r = _recuo()
    if item[0] == 'L':
        print(r + _c_border('│') + ' ' + _colorize_line(item[1]) + ' ' + _c_border('│'))
    elif item[0] == 'V':
        print(r + _c_border('│') + ' ' * (l - 2) + _c_border('│'))
    elif item[0] == 'D':
        print(r + _c_border('├' + _c_muted('─' * (l - 2)) + '┤'))


def _capturar(fn, *args, **kwargs):
    global _BUF
    old_ui = dict(_UI)
    _BUF = []
    _UI['last'] = None
    _UI['has_content'] = False
    try:
        fn(*args, **kwargs)
        return list(_BUF)
    finally:
        _BUF = None
        _UI.update(old_ui)


def topo():
    l = _larg()
    print(_recuo() + _c_border('╭' + '─' * (l - 2) + '╮'))
    _UI['last'] = 'T'


def fundo():
    l = _larg()
    print(_recuo() + _c_border('╰' + '─' * (l - 2) + '╯'))
    _UI['last'] = 'F'


def _div():
    l = _larg()
    print(_recuo() + _c_border('├' + '─' * (l - 2) + '┤'))
    _UI['last'] = 'D'


def titulo_box(txt):
    topo()
    _ln(_c_title(str(txt).strip().upper()), 'center')
    _div()


def _lnd(chave, valor):
    """Linha de dados com dois campos visualmente estáveis."""
    chave, valor = str(chave), str(valor)
    l = _larg()
    util = l - 4
    # Usa uma coluna fixa apenas quando cabe; em telas estreitas, cai para
    # uma forma compacta sem produzir espaços enormes.
    chave_fmt = f'{chave}:'
    if _vis(chave_fmt) <= 28 and _vis(chave_fmt) + 3 + _vis(valor) <= util:
        gap = max(2, 28 - _vis(chave_fmt))
        _ln(f'  {chave_fmt}' + ' ' * gap + valor)
        return
    _ln(f'  {chave_fmt} {valor}')


def p(txt=''):
    r = _recuo()
    util = _larg() - 2
    if not txt:
        return
    for line in (_wrap(txt, util) if _vis(txt) > util else [str(txt)]):
        print(r + _c(line))


def inp(prompt):
    return input(_recuo() + '  ' + _c_input(str(prompt)) + ' ')


def inp_s(prompt):
    try:
        return getpass.getpass(_recuo() + '  ' + _c_input(str(prompt)) + ' ')
    except (EOFError, KeyboardInterrupt):
        raise
    except Exception:
        return inp(prompt)


def pausar():
    input(_recuo() + '  ' + _c_muted(t('enter')) + ' ')


def limpar():
    """Limpa o terminal sem executar shell externo."""
    if not sys.stdout.isatty() or os.environ.get('TERM') == 'dumb':
        return
    sys.stdout.write('\x1b[2J\x1b[H')
    sys.stdout.flush()


def _menu_rows(itens):
    """Normaliza itens de menu e calcula a coluna de alinhamento."""
    valid = [i for i in itens if i is not None]
    if not valid:
        return []
    width = max(_vis(str(i[0])) for i in valid)
    rows = []
    for item in itens:
        if item is None:
            rows.append(None)
        else:
            rows.append((str(item[0]).rjust(width), str(item[1])))
    return rows


def _render_menu(titulo, itens, rodape=None, info=None):
    limpar()
    titulo_box(titulo)
    rows = _menu_rows(itens)
    for row in rows:
        if row is None:
            _dleve()
            continue
        numero, label = row
        _ln(f'  {_c_input(numero)}  {_c_menu(label)}')
    if info:
        _dleve()
        for line in info:
            _ln(f'  {_c_muted(line)}')
    if rodape:
        _dleve()
        for item in _menu_rows(rodape):
            if item is not None:
                _ln(f'  {_c_input(item[0])}  {_c_menu(item[1])}')
    msg, erro = _get_flash()
    if msg:
        _dleve()
        texto = ('✗ ' + msg) if erro else ('✓ ' + msg)
        _ln(_c_error(texto) if erro else _c_success(texto))
    fundo()


def _available_rows(n_resumo=0):
    # Reserva título, resumo, navegação e bordas. A altura útil nunca é zero.
    total = _rows()
    fixo = 8
    resumo = n_resumo + 1 if n_resumo else 0
    return max(4, total - fixo - resumo)


def _build_pages(renders, available):
    pages, page, used = [], [], 0
    for render in renders:
        size = len(render)
        if page and used + size > available:
            pages.append(page)
            page, used = list(render), size
        else:
            page.extend(render)
            used += size
    if page:
        pages.append(page)
    return pages or [[]]


def _pagina_nav(idx, total):
    if total <= 1:
        return '0 = voltar'
    if idx == 0:
        return 'P = próxima   N = ir para   0 = voltar'
    if idx == total - 1:
        return 'A = anterior   N = ir para   0 = voltar'
    return 'A = anterior   P = próxima   N = ir para   0 = voltar'


def paginar(d, titulo, itens, render_item_fn, resumo_fn=None):
    if not itens:
        limpar()
        titulo_box(titulo)
        _ln('Nenhum registro encontrado.', 'center')
        fundo()
        pausar()
        return

    renders = [_capturar(render_item_fn, item) for item in itens]
    resumo_buf = _capturar(resumo_fn) if resumo_fn else []
    pag_idx = 0
    while True:
        available = _available_rows(len(resumo_buf))
        pages = _build_pages(renders, available)
        total = len(pages)
        pag_idx = min(pag_idx, total - 1)
        limpar()
        topo()
        _ln(_c_title(str(titulo).strip().upper()), 'center')
        _ln(f'{pag_idx + 1}/{total}  •  {len(itens)} {t("pag_itens")}', 'center')
        _div()
        for item in resumo_buf:
            _print_buf(item)
        if resumo_buf:
            _dleve()
        for item in pages[pag_idx]:
            _print_buf(item)
        _dleve()
        _ln(_c_muted(_pagina_nav(pag_idx, total)), 'center')
        fundo()
        cmd = inp(t('pag_cmd')).strip().lower()
        if cmd in ('0', ''):
            break
        if cmd in ('p', 'd'):
            if pag_idx < total - 1:
                pag_idx += 1
            else:
                flash('Você já está na última página.', erro=True)
        elif cmd in ('a', 'q'):
            if pag_idx > 0:
                pag_idx -= 1
            else:
                flash('Você já está na primeira página.', erro=True)
        elif cmd == 'n':
            try:
                num = int(inp(t('pag_ir_para', n=total)).strip())
                if 1 <= num <= total:
                    pag_idx = num - 1
                else:
                    flash(t('fora_intervalo'), erro=True)
            except ValueError:
                flash(t('so_numero'), erro=True)
        else:
            flash(t('invalido'), erro=True)

# ---------------------------------------------------------------------------
# Persistência SQLite e migração de dados
# ---------------------------------------------------------------------------

def _conn():
    con = sqlite3.connect(str(BANCO_DADOS))
    con.execute('PRAGMA foreign_keys = ON')
    con.row_factory = sqlite3.Row
    return con

def _migrar_banco_legado():
    """Migra automaticamente um banco antigo localizado junto ao programa.

    A migração ocorre somente quando o banco no diretório XDG ainda não existe.
    O arquivo original é preservado; nenhum dado é apagado.
    """
    if BANCO_DADOS.exists():
        return False
    candidatos = []
    try:
        candidato_script = Path(__file__).resolve().parent / 'dados_ferias.db'
        candidatos.append(candidato_script)
    except Exception:
        pass
    candidatos.append(Path.cwd() / 'dados_ferias.db')
    for origem in candidatos:
        try:
            origem = origem.resolve()
            if not origem.exists() or origem == BANCO_DADOS.resolve():
                continue
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            origem_con = sqlite3.connect(str(origem))
            destino_con = sqlite3.connect(str(BANCO_DADOS))
            try:
                origem_con.backup(destino_con)
            finally:
                destino_con.close()
                origem_con.close()
            return True
        except Exception:
            try:
                if BANCO_DADOS.exists() and BANCO_DADOS.stat().st_size == 0:
                    BANCO_DADOS.unlink()
            except Exception:
                pass
    return False

def _init_banco():
    con = _conn()
    con.executescript("\n        CREATE TABLE IF NOT EXISTS setores (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE);\n        CREATE TABLE IF NOT EXISTS subsetores (id INTEGER PRIMARY KEY AUTOINCREMENT, setor TEXT NOT NULL, nome TEXT NOT NULL, UNIQUE(setor,nome));\n        CREATE TABLE IF NOT EXISTS vinculos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE);\n        CREATE TABLE IF NOT EXISTS funcionarios (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, setor TEXT NOT NULL, subsetor TEXT NOT NULL, vinculo TEXT NOT NULL DEFAULT '', data_admissao TEXT NOT NULL DEFAULT '');\n        CREATE TABLE IF NOT EXISTS ferias (id INTEGER PRIMARY KEY AUTOINCREMENT, funcionario_id INTEGER NOT NULL, inicio TEXT NOT NULL, fim TEXT NOT NULL, venda_ferias INTEGER NOT NULL DEFAULT 0, FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id) ON DELETE CASCADE);\n        CREATE TABLE IF NOT EXISTS regras (id INTEGER PRIMARY KEY AUTOINCREMENT, nivel TEXT NOT NULL, referencia TEXT NOT NULL DEFAULT '', campo TEXT NOT NULL, valor TEXT NOT NULL, UNIQUE(nivel, referencia, campo));\n        CREATE TABLE IF NOT EXISTS configuracoes (chave TEXT PRIMARY KEY, valor TEXT NOT NULL);\n        CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, login TEXT NOT NULL UNIQUE, nome TEXT NOT NULL, senha_hash TEXT NOT NULL, nivel TEXT NOT NULL DEFAULT 'usuario');\n    ")
    con.execute("""CREATE TABLE IF NOT EXISTS banco_horas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        funcionario_id INTEGER NOT NULL,
        data TEXT NOT NULL,
        tipo TEXT NOT NULL CHECK(tipo IN ('C','D','A')),
        minutos INTEGER NOT NULL,
        motivo TEXT NOT NULL,
        usuario_id INTEGER,
        criado_em TEXT NOT NULL,
        FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id) ON DELETE CASCADE,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
    )""")
    con.execute("CREATE INDEX IF NOT EXISTS idx_banco_horas_func_data ON banco_horas(funcionario_id, data, id)")
    try:
        con.execute("ALTER TABLE funcionarios ADD COLUMN data_admissao TEXT NOT NULL DEFAULT ''")
        con.commit()
    except:
        pass
    con.commit()
    con.close()

def _hash(s):
    """Return a salted PBKDF2 password hash with an explicit format."""
    iterations = 600000
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', s.encode('utf-8'), salt, iterations)
    return f'pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}'

def _verify_password(password, stored_hash):
    """Verify PBKDF2 hashes and accept legacy SHA-256 hashes for migration."""
    if stored_hash.startswith('pbkdf2_sha256$'):
        try:
            _, iterations, salt_hex, digest_hex = stored_hash.split('$', 3)
            iterations = int(iterations)
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(digest_hex)
            actual = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
            return secrets.compare_digest(actual, expected)
        except (ValueError, TypeError):
            return False
    legacy = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return secrets.compare_digest(legacy, stored_hash)

def _regras_padrao():
    CR = _campos_regras()
    return {'global': {c: m['padrao'] for c, m in CR.items()}, 'por_vinculo': {}, 'por_setor': {}, 'por_subsetor': {}}

def _v2s(v):
    return 'true' if v is True else 'false' if v is False else str(v)

def _s2v(tipo, s):
    if tipo == 'bool':
        return s == 'true'
    try:
        return int(s)
    except:
        return 0

def _migrar_json():
    legacy_file = Path.cwd() / 'dados_ferias.json'
    JF = legacy_file if legacy_file.exists() else DATA_DIR / 'dados_ferias.json'
    if not JF.exists():
        return
    try:
        con = _conn()
        if con.execute('SELECT COUNT(*) as c FROM setores').fetchone()['c'] > 0:
            con.close()
            JF.rename(JF.with_name(JF.name + '.bak'))
            return
        con.close()
        with open(JF, 'r', encoding='utf-8') as f:
            ant = json.load(f)
        d = {'setores': ant.get('setores', {}), 'funcionarios': ant.get('funcionarios', []), 'vinculos': ant.get('vinculos', ['CLT', 'PJ', 'Estatutário']), 'regras': ant.get('regras', _regras_padrao()), 'config': CONFIG_PADRAO}
        d['regras'].setdefault('por_subsetor', {})
        salvar_dados(d)
        JF.rename(JF.with_name(JF.name + '.bak'))
    except:
        pass

def carregar_dados():
    """Carrega o estado da aplicação do SQLite para a estrutura em memória."""
    _init_banco()
    _migrar_json()
    con = _conn()
    c = con.cursor()
    c2 = con.cursor()
    setores = {}
    for r in c.execute('SELECT nome FROM setores ORDER BY id').fetchall():
        setores[r['nome']] = {'subsetores': []}
    for r in c.execute('SELECT setor,nome FROM subsetores ORDER BY id').fetchall():
        if r['setor'] in setores:
            setores[r['setor']]['subsetores'].append(r['nome'])
    vinculos = [r['nome'] for r in c.execute('SELECT nome FROM vinculos ORDER BY id')]
    if not vinculos:
        vinculos = ['CLT', 'PJ', 'Estatutário']
        for v in vinculos:
            c.execute('INSERT OR IGNORE INTO vinculos (nome) VALUES (?)', (v,))
        con.commit()
    funcs = []
    for fr in c.execute('SELECT id,nome,setor,subsetor,vinculo,data_admissao FROM funcionarios ORDER BY id').fetchall():
        ferias = []
        for pr in c2.execute('SELECT inicio,fim,venda_ferias FROM ferias WHERE funcionario_id=? ORDER BY id', (fr['id'],)):
            ferias.append({'inicio': pr['inicio'], 'fim': pr['fim'], 'venda_ferias': bool(pr['venda_ferias'])})
        funcs.append({'_id': fr['id'], 'nome': fr['nome'], 'setor': fr['setor'], 'subsetor': fr['subsetor'], 'vinculo': fr['vinculo'], 'data_admissao': fr['data_admissao'] or '', 'ferias': ferias})
    CR = _campos_regras()
    regras = _regras_padrao()
    for rr in c.execute('SELECT nivel,referencia,campo,valor FROM regras'):
        m = CR.get(rr['campo'])
        if not m:
            continue
        v = _s2v(m['tipo'], rr['valor'])
        if rr['nivel'] == 'global':
            regras['global'][rr['campo']] = v
        elif rr['nivel'] == 'vinculo':
            regras['por_vinculo'].setdefault(rr['referencia'], {})[rr['campo']] = v
        elif rr['nivel'] == 'setor':
            regras['por_setor'].setdefault(rr['referencia'], {})[rr['campo']] = v
        elif rr['nivel'] == 'subsetor':
            regras['por_subsetor'].setdefault(rr['referencia'], {})[rr['campo']] = v
    config = dict(CONFIG_PADRAO)
    for cr in c.execute('SELECT chave,valor FROM configuracoes'):
        if cr['chave'] in CONFIG_PADRAO:
            config[cr['chave']] = cr['valor']
        elif cr['chave'] == 'idioma':
            set_idioma(cr['valor'])
    con.close()
    return {'setores': setores, 'funcionarios': funcs, 'vinculos': vinculos, 'regras': regras, 'config': config}

def salvar_dados(d):
    """Persiste no SQLite o estado completo da aplicação."""
    con = _conn()
    c = con.cursor()
    ns = list(d['setores'].keys())
    c.execute(f"DELETE FROM setores WHERE nome NOT IN ({','.join('?' * len(ns))})" if ns else 'DELETE FROM setores', ns)
    for setor, info in d['setores'].items():
        c.execute('INSERT OR IGNORE INTO setores (nome) VALUES (?)', (setor,))
        subs = info.get('subsetores', [])
        c.execute(f"DELETE FROM subsetores WHERE setor=? AND nome NOT IN ({','.join('?' * len(subs))})" if subs else 'DELETE FROM subsetores WHERE setor=?', [setor] + subs if subs else [setor])
        for sub in subs:
            c.execute('INSERT OR IGNORE INTO subsetores (setor,nome) VALUES (?,?)', (setor, sub))
    nv = list(d.get('vinculos', []))
    c.execute(f"DELETE FROM vinculos WHERE nome NOT IN ({','.join('?' * len(nv))})" if nv else 'DELETE FROM vinculos', nv)
    for v in nv:
        c.execute('INSERT OR IGNORE INTO vinculos (nome) VALUES (?)', (v,))
    ids_ok = set()
    for func in d['funcionarios']:
        fid = func.get('_id')
        adm = func.get('data_admissao', '') or ''
        if fid:
            c.execute('UPDATE funcionarios SET nome=?,setor=?,subsetor=?,vinculo=?,data_admissao=? WHERE id=?', (func['nome'], func['setor'], func['subsetor'], func.get('vinculo', ''), adm, fid))
        else:
            c.execute('INSERT INTO funcionarios (nome,setor,subsetor,vinculo,data_admissao) VALUES (?,?,?,?,?)', (func['nome'], func['setor'], func['subsetor'], func.get('vinculo', ''), adm))
            fid = c.lastrowid
            func['_id'] = fid
        ids_ok.add(fid)
        c.execute('DELETE FROM ferias WHERE funcionario_id=?', (fid,))
        for f in func.get('ferias', []):
            c.execute('INSERT INTO ferias (funcionario_id,inicio,fim,venda_ferias) VALUES (?,?,?,?)', (fid, f['inicio'], f['fim'], 1 if f.get('venda_ferias') else 0))
    if ids_ok:
        c.execute(f"DELETE FROM funcionarios WHERE id NOT IN ({','.join('?' * len(ids_ok))})", list(ids_ok))
    else:
        c.execute('DELETE FROM funcionarios')
    c.execute('DELETE FROM regras')
    r = d['regras']
    for campo, val in r['global'].items():
        c.execute('INSERT INTO regras (nivel,referencia,campo,valor) VALUES (?,?,?,?)', ('global', '', campo, _v2s(val)))
    for vinc, bloco in r.get('por_vinculo', {}).items():
        for campo, val in bloco.items():
            c.execute('INSERT INTO regras (nivel,referencia,campo,valor) VALUES (?,?,?,?)', ('vinculo', vinc, campo, _v2s(val)))
    for setor, bloco in r.get('por_setor', {}).items():
        for campo, val in bloco.items():
            c.execute('INSERT INTO regras (nivel,referencia,campo,valor) VALUES (?,?,?,?)', ('setor', setor, campo, _v2s(val)))
    for ref, bloco in r.get('por_subsetor', {}).items():
        for campo, val in bloco.items():
            c.execute('INSERT INTO regras (nivel,referencia,campo,valor) VALUES (?,?,?,?)', ('subsetor', ref, campo, _v2s(val)))
    c.execute('DELETE FROM configuracoes')
    for chave, val in d.get('config', CONFIG_PADRAO).items():
        c.execute('INSERT INTO configuracoes (chave,valor) VALUES (?,?)', (chave, str(val)))
    c.execute('INSERT OR REPLACE INTO configuracoes (chave,valor) VALUES (?,?)', ('idioma', get_idioma()))
    con.commit()
    con.close()

# ---------------------------------------------------------------------------
# Datas, ordenação e regras de negócio
# ---------------------------------------------------------------------------

def conv_data(s):
    try:
        return datetime.strptime(s.strip(), '%d/%m/%Y')
    except:
        return None

def calc_dias(i, f):
    a, b = (conv_data(i), conv_data(f))
    return (b - a).days + 1 if a and b else 0

def sobrepoem(i1, f1, i2, f2):
    return i1 <= f2 and f1 >= i2

def fmt_bool(v):
    if v is None:
        return '—'
    return {'pt': 'Sim', 'en': 'Yes'}[get_idioma()] if v else {'pt': 'Não', 'en': 'No'}[get_idioma()]

def fmt_val(tipo, v):
    return fmt_bool(v) if tipo == 'bool' else '—' if v is None else str(v)

def _chave_sub(s, sub):
    return f'{s}{SEP}{sub}'

def add_meses(data, n):
    m = data.month + n
    a = data.year + (m - 1) // 12
    m = (m - 1) % 12 + 1
    try:
        return datetime(a, m, data.day)
    except:
        return datetime(a, m, 28)

def _rev(d):
    return d.get('config', CONFIG_PADRAO).get('direcao', 'asc') == 'desc'

def ord_setores(d):
    ns = list(d['setores'].keys())
    rev = _rev(d)
    return sorted(ns, key=lambda x: x.lower(), reverse=rev) if d.get('config', CONFIG_PADRAO).get('ordem_setores', 'nome') == 'nome' else list(reversed(ns)) if rev else ns

def ord_subs(d, setor):
    subs = list(d['setores'].get(setor, {}).get('subsetores', []))
    rev = _rev(d)
    return sorted(subs, key=lambda x: x.lower(), reverse=rev) if d.get('config', CONFIG_PADRAO).get('ordem_subsetores', 'nome') == 'nome' else list(reversed(subs)) if rev else subs

def ord_vinculos(d):
    vs = list(d.get('vinculos', []))
    rev = _rev(d)
    return sorted(vs, key=lambda x: x.lower(), reverse=rev) if d.get('config', CONFIG_PADRAO).get('ordem_vinculos', 'nome') == 'nome' else list(reversed(vs)) if rev else vs

def ord_funcs(d, lista=None):
    cfg = d.get('config', CONFIG_PADRAO)
    rev = _rev(d)
    funcs = list(lista if lista is not None else d['funcionarios'])
    chaves = {'nome': lambda f: f['nome'].lower(), 'setor': lambda f: (f['setor'].lower(), f['subsetor'].lower(), f['nome'].lower()), 'subsetor': lambda f: (f['subsetor'].lower(), f['nome'].lower()), 'vinculo': lambda f: (f.get('vinculo', '').lower(), f['nome'].lower()), 'cadastro': lambda f: f.get('_id', 0)}
    return sorted(funcs, key=chaves.get(cfg.get('ordem_funcionarios', 'nome'), chaves['nome']), reverse=rev)

def ord_ferias(d, ferias):
    cfg = d.get('config', CONFIG_PADRAO)
    rev = _rev(d)

    def _dt(s):
        try:
            pp = s.split('/')
            return (int(pp[2]), int(pp[1]), int(pp[0]))
        except:
            return (0, 0, 0)
    for i, f in enumerate(ferias):
        f['_idx'] = i
    chaves = {'inicio': lambda f: _dt(f.get('inicio', '')), 'fim': lambda f: _dt(f.get('fim', '')), 'dias': lambda f: calc_dias(f.get('inicio', ''), f.get('fim', '')), 'cadastro': lambda f: f.get('_idx', 0)}
    return sorted(ferias, key=chaves.get(cfg.get('ordem_ferias', 'inicio'), chaves['inicio']), reverse=rev)

def sel_setor(d):
    ns = ord_setores(d)
    if not ns:
        flash(t('nenhum_setor'), erro=True)
        return None
    limpar(); titulo_box(t('set_titulo'))
    _ln(t('set_disponiveis'), 'center'); _dleve()
    for i, nome in enumerate(ns, 1):
        _ln(f'  {_c_input(str(i).rjust(len(str(len(ns)))))}  {_c_menu(nome)}')
    _dleve(); _ln(f'  {_c_input("0")}  {_c_menu(t("cancelar"))}')
    fundo()
    try:
        e=int(inp(t('opcao')).strip())
    except ValueError:
        flash(t('so_numero'), erro=True); return None
    if e == 0: return None
    if 1 <= e <= len(ns): return ns[e-1]
    flash(t('fora_intervalo'), erro=True); return None

def sel_sub(d, setor):
    subs = ord_subs(d, setor)
    if not subs:
        flash(f"'{setor}': {t('nenhum_sub')}", erro=True)
        return None
    limpar(); titulo_box(t('set_novo_sub'))
    _ln(f'{t("sub_disponiveis")}  {setor}', 'center'); _dleve()
    for i, nome in enumerate(subs, 1):
        _ln(f'  {_c_input(str(i).rjust(len(str(len(subs)))))}  {_c_menu(nome)}')
    _dleve(); _ln(f'  {_c_input("0")}  {_c_menu(t("cancelar"))}')
    fundo()
    try:
        e=int(inp(t('opcao')).strip())
    except ValueError:
        flash(t('so_numero'), erro=True); return None
    if e == 0: return None
    if 1 <= e <= len(subs): return subs[e-1]
    flash(t('fora_intervalo'), erro=True); return None

def sel_func(d, msg=None):
    funcs = ord_funcs(d)
    if not funcs:
        flash(t('nenhum_func'), erro=True)
        return None
    msg = msg or t('opcao')
    limpar(); titulo_box(t('fun_titulo'))
    _ln(t('fun_lista'), 'center'); _dleve()
    for i, f in enumerate(funcs, 1):
        vinc = f" · {f.get('vinculo')}" if f.get('vinculo') else ''
        local = f"{f['setor']} / {f['subsetor']}"
        _ln(f'  {_c_input(str(i).rjust(len(str(len(funcs)))))}  {_c_menu(f["nome"])}{vinc}')
        _ln(f'     {_c_muted(local)}')
    _dleve(); _ln(f'  {_c_input("0")}  {_c_menu(t("cancelar"))}')
    fundo()
    try:
        e=int(inp(msg).strip())
    except ValueError:
        flash(t('so_numero'), erro=True); return None
    if e == 0: return None
    if 1 <= e <= len(funcs): return funcs[e-1]
    flash(t('fora_intervalo'), erro=True); return None

def sel_vinculo(d, permitir_nenhum=True):
    vs = ord_vinculos(d)
    if not vs:
        flash(t('nenhum_vinculo'), erro=True)
        return None
    limpar(); titulo_box(t('vin_titulo'))
    _ln(t('vin_disponiveis'), 'center'); _dleve()
    for i, nome in enumerate(vs, 1):
        _ln(f'  {_c_input(str(i).rjust(len(str(len(vs)))))}  {_c_menu(nome)}')
    _dleve()
    if permitir_nenhum:
        _ln(f'  {_c_input("0")}  {_c_menu(t("vin_sem"))}')
    else:
        _ln(f'  {_c_input("0")}  {_c_menu(t("cancelar"))}')
    fundo()
    try:
        e=int(inp(t('opcao')).strip())
    except ValueError:
        flash(t('so_numero'), erro=True); return None
    if e == 0: return None
    if 1 <= e <= len(vs): return vs[e-1]
    flash(t('fora_intervalo'), erro=True); return None

def periodo_aquisitivo_atual(func):
    adm = conv_data(func.get('data_admissao', ''))
    if not adm:
        return (None, None, None)
    hoje = datetime.today()
    ini = adm
    n = 0
    while True:
        fim = add_meses(ini, 12)
        n += 1
        if ini <= hoje < fim:
            return (ini, fim, n)
        if fim > hoje:
            return (ini, fim, n)
        ini = fim

def todos_periodos_aquisitivos(func):
    adm = conv_data(func.get('data_admissao', ''))
    if not adm:
        return []
    hoje = datetime.today()
    periodos = []
    ini = adm
    n = 0
    while True:
        fim = add_meses(ini, 12)
        n += 1
        periodos.append({'ini': ini, 'fim': fim, 'numero': n})
        if ini <= hoje < fim:
            break
        if fim > hoje:
            break
        ini = fim
    return periodos

def dias_no_periodo(f, ini_p, fim_p):
    try:
        fi = datetime.strptime(f['inicio'].strip(), '%d/%m/%Y')
        ff = datetime.strptime(f['fim'].strip(), '%d/%m/%Y')
        fim_inc = fim_p - timedelta(days=1)
        ie = max(fi, ini_p)
        fe = min(ff, fim_inc)
        return max(0, (fe - ie).days + 1)
    except:
        return 0

def ferias_no_periodo(ferias, ini_p, fim_p):
    fim_inc = fim_p - timedelta(days=1)
    return [f for f in ferias if conv_data(f['inicio']) and conv_data(f['fim']) and (conv_data(f['inicio']) <= fim_inc) and (conv_data(f['fim']) >= ini_p)]

def ferias_no_ano_civil(ferias, ano):
    res = []
    for f in ferias:
        try:
            fi = datetime.strptime(f['inicio'].strip(), '%d/%m/%Y')
            ff = datetime.strptime(f['fim'].strip(), '%d/%m/%Y')
            if fi.year <= ano <= ff.year:
                res.append(f)
        except:
            pass
    return res

def dias_no_ano_civil(f, ano):
    try:
        fi = datetime.strptime(f['inicio'].strip(), '%d/%m/%Y')
        ff = datetime.strptime(f['fim'].strip(), '%d/%m/%Y')
        ie = max(fi, datetime(ano, 1, 1))
        fe = min(ff, datetime(ano, 12, 31))
        return max(0, (fe - ie).days + 1)
    except:
        return 0

def analise_periodo_atual(d, func):
    ini, fim, n = periodo_aquisitivo_atual(func)
    setor = func['setor']
    subsetor = func['subsetor']
    vinculo = func.get('vinculo', '')
    max_d = obter_regra(d, 'max_dias_ano', setor, subsetor, vinculo)
    if ini is None:
        ano = datetime.today().year
        tirados = sum((dias_no_ano_civil(f, ano) for f in ferias_no_ano_civil(func['ferias'], ano)))
        restantes = max(0, max_d - tirados) if max_d and max_d > 0 else None
        return {'ini': None, 'fim': None, 'numero': None, 'tirados': tirados, 'max_dias': max_d, 'restantes': restantes, 'tipo': 'civil', 'ano_civil': ano}
    tirados = sum((dias_no_periodo(f, ini, fim) for f in ferias_no_periodo(func['ferias'], ini, fim)))
    restantes = max(0, max_d - tirados) if max_d and max_d > 0 else None
    return {'ini': ini, 'fim': fim, 'numero': n, 'tirados': tirados, 'max_dias': max_d, 'restantes': restantes, 'tipo': 'aquisitivo'}

def classificar_ferias(func):
    hoje = datetime.today()
    pas, atu, fut = ([], [], [])
    for f in func['ferias']:
        ini = conv_data(f['inicio'])
        fim = conv_data(f['fim'])
        if not ini or not fim:
            continue
        if fim < hoje:
            pas.append(f)
        elif ini <= hoje <= fim:
            atu.append(f)
        else:
            fut.append(f)
    return (pas, atu, fut)

def calc_periodos_aquisitivos(func):
    adm = conv_data(func.get('data_admissao', ''))
    if not adm:
        return []
    hoje = datetime.today()
    periodos = []
    ini = adm
    for _ in range(40):
        fim = add_meses(ini, 12)
        if fim > hoje:
            break
        fim_con = add_meses(fim, 12)
        ferias_p = ferias_no_periodo(func['ferias'], ini, fim)
        dias_t = sum((dias_no_periodo(f, ini, fim) for f in ferias_p))
        if dias_t > 0:
            status = 'ok'
        elif fim_con < hoje:
            status = 'vencida'
        elif (fim_con - hoje).days <= 60:
            status = 'a_vencer'
        else:
            status = 'pendente'
        periodos.append({'ini_aq': ini, 'fim_aq': fim, 'fim_con': fim_con, 'dias_tirados': dias_t, 'status': status, 'ferias_periodo': ferias_p})
        ini = fim
    return periodos

def situacao_geral_func(func):
    try:
        per = calc_periodos_aquisitivos(func)
        if not per:
            return 'sem_admissao'
        pri = {'vencida': 4, 'a_vencer': 3, 'pendente': 2, 'ok': 1}
        return max(per, key=lambda x: pri.get(x['status'], 0))['status']
    except:
        return 'sem_admissao'

def _contar_vencidas(d):
    try:
        return sum((1 for f in d['funcionarios'] if f.get('data_admissao', '') and situacao_geral_func(f) == 'vencida'))
    except:
        return 0

def _barra_progresso(tirados, max_d, largura=18):
    if not max_d or max_d <= 0:
        return None
    fill = round(min(tirados, max_d) / max_d * largura)
    barra = '█' * fill + '░' * (largura - fill)
    pct = round(min(tirados, max_d) / max_d * 100)
    return (barra, pct)

def _linha_periodo_atual(func, d):
    an = analise_periodo_atual(d, func)
    if an['tipo'] == 'civil':
        prefixo = f"Ano {an['ano_civil']}"
    else:
        ini_s = an['ini'].strftime('%d/%m/%Y')
        fim_s = (an['fim'] - timedelta(days=1)).strftime('%d/%m/%Y')
        prefixo = f"Prd.{an['numero']} ({ini_s}–{fim_s})"
    if an['max_dias'] and an['max_dias'] > 0:
        bp = _barra_progresso(an['tirados'], an['max_dias'], 14)
        if bp:
            barra, pct = bp
            return f"    {prefixo}: {an['tirados']}/{an['max_dias']} dias  [{barra}] {pct}%  Restam: {an['restantes']}"
    return f"    {prefixo}: {an['tirados']} dias  {t('pa_ilimitado')}"

def obter_regra(d, campo, setor=None, subsetor=None, vinculo=None):
    CR = _campos_regras()
    r = d['regras']
    if setor and subsetor:
        bloco = r.get('por_subsetor', {}).get(_chave_sub(setor, subsetor), {})
        if campo in bloco:
            return bloco[campo]
    if setor:
        bloco = r.get('por_setor', {}).get(setor, {})
        if campo in bloco:
            return bloco[campo]
    if vinculo:
        bloco = r.get('por_vinculo', {}).get(vinculo, {})
        if campo in bloco:
            return bloco[campo]
    return r['global'].get(campo, CR[campo]['padrao'])

def validar_agendamento(d, func, inicio, fim):
    """Valida um novo período de férias contra as regras configuradas."""
    setor = func['setor']
    subsetor = func['subsetor']
    vinculo = func.get('vinculo', '')
    dias_p = (fim - inicio).days + 1
    erros = []
    av = obter_regra(d, 'aviso_previo_dias', setor, subsetor, vinculo)
    if av and av > 0:
        diff = (inicio - datetime.today()).days
        if diff < av:
            erros.append(f'Antecedência mínima de {av} dia(s) não cumprida ({max(0, diff)} disponíveis).')
    mn = obter_regra(d, 'min_dias_periodo', setor, subsetor, vinculo)
    if mn and mn > 0 and (dias_p < mn):
        erros.append(f'Período mínimo de {mn} dia(s) (informado: {dias_p}).')
    ini_aq, fim_aq, n_aq = periodo_aquisitivo_atual(func)
    if ini_aq:
        ini_ref, fim_ref = (ini_aq, fim_aq)
        if inicio >= fim_aq:
            ini_ref = fim_aq
            fim_ref = add_meses(fim_aq, 12)
        mx = obter_regra(d, 'max_dias_ano', setor, subsetor, vinculo)
        if mx and mx > 0:
            usados = sum((dias_no_periodo(f, ini_ref, fim_ref) for f in ferias_no_periodo(func['ferias'], ini_ref, fim_ref)))
            dias_ef = dias_no_periodo({'inicio': inicio.strftime('%d/%m/%Y'), 'fim': fim.strftime('%d/%m/%Y')}, ini_ref, fim_ref)
            if usados + dias_ef > mx:
                label = f"{ini_ref.strftime('%d/%m/%Y')} – {fim_ref.strftime('%d/%m/%Y')}"
                erros.append(f'Limite de {mx} dias no período aquisitivo excedido (já: {usados} + novo: {dias_ef} = {usados + dias_ef}). Período: {label}.')
        mp = obter_regra(d, 'max_periodos_ano', setor, subsetor, vinculo)
        if mp and mp > 0:
            qtd = len(ferias_no_periodo(func['ferias'], ini_ref, fim_ref))
            if qtd >= mp:
                erros.append(f'Limite de {mp} período(s) no período aquisitivo atingido ({qtd} cadastrado(s)).')
    else:
        ano = inicio.year
        mx = obter_regra(d, 'max_dias_ano', setor, subsetor, vinculo)
        if mx and mx > 0:
            usados = sum((dias_no_ano_civil(f, ano) for f in ferias_no_ano_civil(func['ferias'], ano)))
            if usados + dias_p > mx:
                erros.append(f'Limite anual de {mx} dias excedido (já: {usados} + novo: {dias_p}).')
        mp = obter_regra(d, 'max_periodos_ano', setor, subsetor, vinculo)
        if mp and mp > 0:
            qtd = len(ferias_no_ano_civil(func['ferias'], ano))
            if qtd >= mp:
                erros.append(f'Limite de {mp} período(s)/ano atingido ({qtd} cadastrado(s)).')
    pc = obter_regra(d, 'permite_concomitantes', setor, subsetor, vinculo)
    mc = obter_regra(d, 'max_concomitantes', setor, subsetor, vinculo)
    cnt, nomes = ([], [])
    for o in d['funcionarios']:
        if o['nome'].lower() == func['nome'].lower():
            continue
        if o['setor'] != setor or o['subsetor'] != subsetor:
            continue
        for f in o['ferias']:
            io, fo = (conv_data(f['inicio']), conv_data(f['fim']))
            if io and fo and sobrepoem(inicio, fim, io, fo):
                cnt.append(o)
                nomes.append(o['nome'])
                break
    if not pc and cnt:
        erros.append(f"Férias simultâneas não permitidas no subsetor '{subsetor}'. Conflito: {', '.join(nomes)}.")
    elif pc and mc and (mc > 0) and (len(cnt) >= mc):
        erros.append(f"Máximo de {mc} simultâneo(s) atingido. Conflito: {', '.join(nomes)}.")
    return erros

def auditar_func(d, func):
    pends = []
    setor = func['setor']
    subsetor = func['subsetor']
    vinculo = func.get('vinculo', '')
    ini_aq, fim_aq, _ = periodo_aquisitivo_atual(func)
    for f in func['ferias']:
        ep = []
        ini, fim = (conv_data(f['inicio']), conv_data(f['fim']))
        if not ini or not fim:
            pends.append({'tipo': 'periodo', 'ref': f"{f.get('inicio', '?')} - {f.get('fim', '?')}", 'erros': ['Datas inválidas.']})
            continue
        dias = (fim - ini).days + 1
        mn = obter_regra(d, 'min_dias_periodo', setor, subsetor, vinculo)
        if mn and mn > 0 and (dias < mn):
            ep.append(f'Abaixo do mínimo de {mn} dia(s) ({dias} registrado(s)).')
        if f.get('venda_ferias') and (not obter_regra(d, 'permite_venda_ferias', setor, subsetor, vinculo)):
            ep.append('Venda de férias marcada, mas a regra não permite.')
        pc = obter_regra(d, 'permite_concomitantes', setor, subsetor, vinculo)
        mc = obter_regra(d, 'max_concomitantes', setor, subsetor, vinculo)
        cnt, nomes = (0, [])
        for o in d['funcionarios']:
            if o['nome'].lower() == func['nome'].lower():
                continue
            if o['setor'] != setor or o['subsetor'] != subsetor:
                continue
            for of in o['ferias']:
                io, fo = (conv_data(of['inicio']), conv_data(of['fim']))
                if io and fo and sobrepoem(ini, fim, io, fo):
                    cnt += 1
                    nomes.append(o['nome'])
                    break
        if not pc and cnt > 0:
            ep.append(f"Simultânea com {', '.join(nomes)} (não permitido).")
        elif pc and mc and (mc > 0) and (cnt >= mc):
            ep.append(f"Excede o máximo de {mc} simultâneo(s). Conflito: {', '.join(nomes)}.")
        if ep:
            pends.append({'tipo': 'periodo', 'ref': f"{f['inicio']} – {f['fim']} ({dias} dias)", 'erros': ep})
    todos = todos_periodos_aquisitivos(func) if ini_aq else []
    for prd in todos:
        ea = []
        ip = prd['ini']
        fp = prd['fim']
        mp = obter_regra(d, 'max_periodos_ano', setor, subsetor, vinculo)
        qtd = len(ferias_no_periodo(func['ferias'], ip, fp))
        if mp and mp > 0 and (qtd > mp):
            ea.append(f"{qtd} período(s) no prd.aquisitivo {ip.strftime('%d/%m/%Y')}–{fp.strftime('%d/%m/%Y')}, máximo: {mp}.")
        mx = obter_regra(d, 'max_dias_ano', setor, subsetor, vinculo)
        if mx and mx > 0:
            tot = sum((dias_no_periodo(f, ip, fp) for f in ferias_no_periodo(func['ferias'], ip, fp)))
            if tot > mx:
                ea.append(f'{tot} dia(s) no prd.aquisitivo, máximo: {mx}.')
        if ea:
            pends.append({'tipo': 'aquisitivo', 'ref': f"Prd.{prd['numero']} ({ip.strftime('%d/%m/%Y')}–{fp.strftime('%d/%m/%Y')})", 'erros': ea})
    if not ini_aq:
        anos = set()
        for f in func['ferias']:
            fi = conv_data(f['inicio'])
            if fi:
                anos.add(fi.year)
        for ano in sorted(anos):
            ea = []
            mp = obter_regra(d, 'max_periodos_ano', setor, subsetor, vinculo)
            qtd = len(ferias_no_ano_civil(func['ferias'], ano))
            if mp and mp > 0 and (qtd > mp):
                ea.append(f'{qtd} período(s) em {ano}, máximo: {mp}.')
            mx = obter_regra(d, 'max_dias_ano', setor, subsetor, vinculo)
            if mx and mx > 0:
                tot = sum((dias_no_ano_civil(f, ano) for f in ferias_no_ano_civil(func['ferias'], ano)))
                if tot > mx:
                    ea.append(f'{tot} dia(s) em {ano}, máximo: {mx}.')
            if ea:
                pends.append({'tipo': 'ano', 'ref': str(ano), 'erros': ea})
    return pends

def auditar_sistema(d):
    """Audita os períodos cadastrados e retorna as pendências encontradas."""
    return [{'func': f, 'pendencias': auditar_func(d, f)} for f in d['funcionarios'] if f['ferias'] and auditar_func(d, f)]

def contar_pends(d):
    return sum((len(auditar_func(d, f)) for f in d['funcionarios'] if f['ferias']))

def _status_ferias(func):
    hoje, tot, fut, em = (datetime.today(), 0, 0, 0)
    for f in func['ferias']:
        tot += calc_dias(f['inicio'], f['fim'])
        ini = conv_data(f['inicio'])
        fim = conv_data(f['fim'])
        if ini and fim:
            if ini <= hoje <= fim:
                em += 1
            elif ini > hoje:
                fut += 1
    return (tot, fut, em)

# ---------------------------------------------------------------------------
# Relatórios, gráficos e painel
# ---------------------------------------------------------------------------

def _render_func_simples(func, d):
    an = analise_periodo_atual(d, func)
    pas, atu, fut = classificar_ferias(func)
    v = f" [{func.get('vinculo', '')}]" if func.get('vinculo') else ''
    _lvz()
    _ln(f"  › {func['nome']}{v}")
    _ln(f"    {func['setor']}  →  {func['subsetor']}")
    _ln(_linha_periodo_atual(func, d))
    if atu:
        _ln(f"    Em férias: {atu[0]['inicio']} até {atu[0]['fim']}")
    elif fut:
        _ln(f"    Próximo: {fut[0]['inicio']} até {fut[0]['fim']}")
    if not func['ferias']:
        _ln('    ' + t('sem_ferias'))

def _render_func_individual(func, d):
    an = analise_periodo_atual(d, func)
    pas, atu, fut = classificar_ferias(func)
    per = calc_periodos_aquisitivos(func)
    sit = situacao_geral_func(func)
    v = f" [{func.get('vinculo', '')}]" if func.get('vinculo') else ''
    sit_txt = {'vencida': f"[!] {t('ferias_vencidas')}", 'a_vencer': f"[~] {t('ferias_a_vencer')}", 'pendente': f"[?] {t('ferias_pendentes')}", 'ok': f"[✓] {t('ferias_em_dia')}", 'sem_admissao': f"[–] {t('sem_admissao')}"}.get(sit, '')
    _dleve()
    _ln(f"  {func['nome']}{v}", 'center')
    _dleve()
    _ln(f"  {t('rel_setor_l')}: {func['setor']}  |  {t('rel_sub_l')}: {func['subsetor']}")
    if func.get('vinculo'):
        _ln(f"  {t('rel_vinculo')}: {func['vinculo']}")
    if func.get('data_admissao'):
        _ln(f"  {t('data_admissao')} {func['data_admissao']}")
    if sit_txt:
        _ln(f"  {t('situacao_label')}: {sit_txt}")
    _lvz()
    if an['tipo'] == 'aquisitivo':
        ini_s = an['ini'].strftime('%d/%m/%Y')
        fim_s = (an['fim'] - timedelta(days=1)).strftime('%d/%m/%Y')
        _ln(f"  [{t('pa_atual')} #{an['numero']}:  {ini_s} → {fim_s}]")
    else:
        _ln(f"  [Ano civil {an['ano_civil']}  {t('pa_sem_admissao')}]")
    if an['max_dias'] and an['max_dias'] > 0:
        bp = _barra_progresso(an['tirados'], an['max_dias'])
        if bp:
            barra, pct = bp
            _ln(f"    {t('pa_tirados')}  : {an['tirados']:>3} / {an['max_dias']} {t('pa_dias')}")
            _ln(f"    {t('pa_restantes')}: {an['restantes']:>3} {t('pa_dias')}")
            _ln(f"    {t('pa_progresso')}: [{barra}] {pct}%")
    else:
        _ln(f"    {t('pa_tirados')}: {an['tirados']} {t('pa_dias')}  ({t('pa_ilimitado')})")
    if atu:
        _lvz()
        _ln(f"  [{t('rel_andamento')}]")
        for f in atu:
            dias = calc_dias(f['inicio'], f['fim'])
            vd = ' ' + t('fer_venda_lbl') if f.get('venda_ferias') else ''
            _ln(f"    • {f['inicio']} até {f['fim']}  ({dias} {t('pa_dias')}){vd}")
    if fut:
        _lvz()
        _ln(f"  [{t('periodos_futuros')}: {len(fut)}]")
        for f in sorted(fut, key=lambda x: conv_data(x['inicio']) or datetime.min):
            dias = calc_dias(f['inicio'], f['fim'])
            vd = ' ' + t('fer_venda_lbl') if f.get('venda_ferias') else ''
            _ln(f"    • {f['inicio']} até {f['fim']}  ({dias} {t('pa_dias')}){vd}")
    if pas:
        _lvz()
        _ln(f"  [{t('periodos_passados')}: {len(pas)}]")
        for f in sorted(pas, key=lambda x: conv_data(x['inicio']) or datetime.min, reverse=True):
            dias = calc_dias(f['inicio'], f['fim'])
            vd = ' ' + t('fer_venda_lbl') if f.get('venda_ferias') else ''
            _ln(f"    • {f['inicio']} até {f['fim']}  ({dias} {t('pa_dias')}){vd}")
    if not func['ferias']:
        _lvz()
        _ln('    ' + t('sem_ferias'))
    if per:
        _lvz()
        _ln(f"  [{t('periodo_aquisitivo')} — histórico]")
        for i, pp in enumerate(per, 1):
            s_txt = {'ok': t('ferias_em_dia'), 'vencida': t('ferias_vencidas'), 'a_vencer': t('ferias_a_vencer'), 'pendente': t('ferias_pendentes')}.get(pp['status'], pp['status'])
            fim_s = (pp['fim_aq'] - timedelta(days=1)).strftime('%d/%m/%Y')
            _ln(f"    Prd.{i}: {pp['ini_aq'].strftime('%d/%m/%Y')} – {fim_s}  |  {pp['dias_tirados']} dias  |  {s_txt}")
            if pp['status'] == 'a_vencer':
                _ln(f"      ⚠ Concessivo vence em {(pp['fim_con'] - datetime.today()).days} {t('dias_para_vencer')}")
            elif pp['status'] == 'vencida':
                _ln(f"      ✗ {t('vencida_em')}: {pp['fim_con'].strftime('%d/%m/%Y')}")
    _lvz()
MESES_LABEL = {'pt': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'], 'en': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']}

def _mes_label(ano, mes):
    return f"{MESES_LABEL.get(get_idioma(), MESES_LABEL['pt'])[mes - 1]}/{str(ano)[2:]}"

def _dias_no_mes(f, ano, mes):
    try:
        fi = datetime.strptime(f['inicio'].strip(), '%d/%m/%Y')
        ff = datetime.strptime(f['fim'].strip(), '%d/%m/%Y')
        ini_m = datetime(ano, mes, 1)
        fim_m = (datetime(ano + 1, 1, 1) if mes == 12 else datetime(ano, mes + 1, 1)) - timedelta(days=1)
        ie = max(fi, ini_m)
        fe = min(ff, fim_m)
        return max(0, (fe - ie).days + 1)
    except:
        return 0

def _pico_mes(funcionarios, ano, mes):
    ini_m = datetime(ano, mes, 1)
    fim_m = datetime(ano + 1, 1, 1) if mes == 12 else datetime(ano, mes + 1, 1)
    pico = 0
    dia = ini_m
    while dia < fim_m:
        em = 0
        for func in funcionarios:
            for f in func.get('ferias', []):
                fi = conv_data(f['inicio'])
                ff = conv_data(f['fim'])
                if fi and ff and (fi <= dia <= ff):
                    em += 1
                    break
        pico = max(pico, em)
        dia += timedelta(days=1)
    return pico

def _evolucao_empresa(funcionarios, n_meses=12):
    hoje = datetime.today()
    cur = add_meses(datetime(hoje.year, hoje.month, 1), -(n_meses - 1))
    fim = datetime(hoje.year, hoje.month, 1)
    resultado = []
    while cur <= fim:
        ano, mes = (cur.year, cur.month)
        por_func = {func['nome']: d for func in funcionarios if (d := sum((_dias_no_mes(f, ano, mes) for f in func.get('ferias', [])))) > 0}
        total = sum(por_func.values())
        pico = _pico_mes(funcionarios, ano, mes) if por_func else 0
        resultado.append({'ano': ano, 'mes': mes, 'total_dias': total, 'n_func': len(por_func), 'pico': pico, 'por_func': por_func})
        cur = add_meses(cur, 1)
    return resultado

def _evolucao_func(func, n_meses=12):
    hoje = datetime.today()
    cur = add_meses(datetime(hoje.year, hoje.month, 1), -(n_meses - 1))
    fim = datetime(hoje.year, hoje.month, 1)
    resultado = []
    acum = 0
    while cur <= fim:
        ano, mes = (cur.year, cur.month)
        d = sum((_dias_no_mes(f, ano, mes) for f in func.get('ferias', [])))
        acum += d
        resultado.append({'ano': ano, 'mes': mes, 'dias': d, 'acumulado': acum})
        cur = add_meses(cur, 1)
    return resultado

def _barra_grafico(valor, max_val, largura=None):
    if largura is None:
        largura = max(10, (_larg() - 4) * 38 // 100)
    if max_val <= 0:
        return '░' * largura
    fill = round(min(valor, max_val) / max_val * largura)
    return '█' * fill + '░' * (largura - fill)

def _pedir_n_meses():
    limpar()
    titulo_box(t('graf_titulo'))
    _lvz()
    _ln('  Período do gráfico:')
    _dleve()
    _ln(f"  1. {t('graf_3m')}")
    _ln(f"  2. {t('graf_6m')}")
    _ln(f"  3. {t('graf_12m')}")
    _ln(f"  4. {t('graf_24m')}")
    _dleve()
    _ln(f"  0. {t('cancelar')}")
    fundo()
    p()
    op = inp(t('opcao')).strip()
    return {'1': 3, '2': 6, '3': 12, '4': 24, '': 12, '0': None}.get(op, 12)

def grafico_evolucao_mensal(d):
    """Exibe a evolução mensal das férias em gráfico textual."""
    """Gráfico de barras horizontais de evolução mensal de férias."""
    limpar()
    titulo_box(t('graf_titulo'))
    _lvz()
    _ln(f"  {t('graf_escolha_tipo')}")
    _dleve()
    _ln(f"  1. {t('graf_empresa')}")
    _ln(f"  2. {t('graf_setor')}")
    _ln(f"  3. {t('graf_subsetor')}")
    _ln(f"  4. {t('graf_funcionario')}")
    _dleve()
    _ln(f"  0. {t('cancelar')}")
    fundo()
    p()
    op = inp(t('opcao')).strip()
    if op == '0':
        return
    n_meses = _pedir_n_meses()
    if n_meses is None:
        return
    hoje = datetime.today()
    if op == '1':
        ev = _evolucao_empresa(d['funcionarios'], n_meses)
        tot = sum((m['total_dias'] for m in ev))
        n_c = sum((1 for m in ev if m['total_dias'] > 0))
        max_d = max((m['total_dias'] for m in ev), default=1) or 1
        bw = max(12, (_larg() - 4) * 38 // 100)
        limpar()
        titulo_box(f"{t('graf_titulo')} — {t('graf_empresa')}")

        def resumo_emp():
            _lnd(t('rel_data'), hoje.strftime('%d/%m/%Y %H:%M'))
            _lnd(t('graf_periodo'), f'{n_meses} meses')
            _lnd(t('rel_total_func'), str(len(d['funcionarios'])))
            _lnd(t('graf_total_periodo'), f"{tot} {t('pa_dias')}")
            _lnd(t('graf_meses_ativos'), f'{n_c} mês(es)')
            _lnd('Legenda', '█=Dias de férias  ◄=Mês atual')
        for item in _capturar(resumo_emp):
            _print_buf(item)
        _dleve()
        _ln(f"  {'Mês':7}  {'Dias de férias'.ljust(bw)}  {'Dias':5}  {'Func':5}  {'Pico':5}")
        _dleve()
        for m in ev:
            label = _mes_label(m['ano'], m['mes'])
            barra = _barra_grafico(m['total_dias'], max_d, bw)
            flag = '◄' if m['ano'] == hoje.year and m['mes'] == hoje.month else ' '
            _ln(f"  {label}{flag} [{barra}]  {m['total_dias']:4}d  {m['n_func']:4}   {m['pico']:4}")
        _dleve()
        _ln(f"  {t('graf_total_periodo')}: {tot} {t('pa_dias')}  |  {t('graf_meses_ativos')}: {n_c}")
        _ln(f"  {t('graf_detalhe')}")
        _dleve()
        fundo()
        p()
        op2 = inp(t('pag_cmd')).strip().lower()
        if op2 == 'p':
            meses_com = [m for m in ev if m['total_dias'] > 0]
            if not meses_com:
                flash(t('graf_sem_dados'), erro=True)
                return

            def render_mes(m):
                barra = _barra_grafico(m['total_dias'], max_d, bw)
                flag = '◄' if m['ano'] == hoje.year and m['mes'] == hoje.month else ' '
                _lvz()
                _ln(f"  {_mes_label(m['ano'], m['mes'])}{flag}  [{barra}]  {m['total_dias']}d  {m['n_func']}func  pico:{m['pico']}")
                if m['por_func']:
                    max_f = max(m['por_func'].values(), default=1)
                    bw2 = max(8, (_larg() - 4) * 22 // 100)
                    for nome, dias in sorted(m['por_func'].items(), key=lambda x: -x[1]):
                        b2 = _barra_grafico(dias, max_f, bw2)
                        _ln(f'    [{b2}] {nome}: {dias}d')
            paginar(d, f"{t('graf_titulo')} — detalhado", meses_com, render_mes, resumo_emp)
    elif op == '2':
        setores = ord_setores(d)
        if not setores:
            flash(t('nenhum_setor'), erro=True)
            return
        ev_map = {s: _evolucao_empresa([f for f in d['funcionarios'] if f['setor'] == s], n_meses) for s in setores}
        bw = max(10, (_larg() - 4) * 32 // 100)
        max_glob = max((m['total_dias'] for ev in ev_map.values() for m in ev), default=1) or 1

        def resumo_set():
            _lnd(t('rel_data'), hoje.strftime('%d/%m/%Y %H:%M'))
            _lnd(t('graf_periodo'), f'{n_meses} meses')
            _lnd(t('rel_set_cad'), str(len(setores)))
            _lnd('Legenda', '█=Dias  ◄=Mês atual  (escala global)')

        def render_set(setor):
            ev = ev_map[setor]
            _lvz()
            _ln(f'  ══ {setor} ══')
            _dleve()
            for m in ev:
                if m['total_dias'] == 0 and m['n_func'] == 0:
                    continue
                label = _mes_label(m['ano'], m['mes'])
                barra = _barra_grafico(m['total_dias'], max_glob, bw)
                flag = '◄' if m['ano'] == hoje.year and m['mes'] == hoje.month else ' '
                _ln(f"  {label}{flag} [{barra}]  {m['total_dias']:3}d  {m['n_func']}func")
        paginar(d, f"{t('graf_titulo')} — {t('graf_setor')}", setores, render_set, resumo_set)
    elif op == '3':
        setor = sel_setor(d)
        if not setor:
            return
        subs = ord_subs(d, setor)
        if not subs:
            flash(t('nenhum_sub'), erro=True)
            return
        ev_map = {s: _evolucao_empresa([f for f in d['funcionarios'] if f['setor'] == setor and f['subsetor'] == s], n_meses) for s in subs}
        bw = max(10, (_larg() - 4) * 32 // 100)
        max_glob = max((m['total_dias'] for ev in ev_map.values() for m in ev), default=1) or 1

        def resumo_sub():
            _lnd(t('rel_data'), hoje.strftime('%d/%m/%Y %H:%M'))
            _lnd(t('rel_setor_l'), setor)
            _lnd(t('graf_periodo'), f'{n_meses} meses')

        def render_sub(sub):
            ev = ev_map[sub]
            _lvz()
            _ln(f'  ══ {sub} ══')
            _dleve()
            for m in ev:
                if m['total_dias'] == 0 and m['n_func'] == 0:
                    continue
                label = _mes_label(m['ano'], m['mes'])
                barra = _barra_grafico(m['total_dias'], max_glob, bw)
                flag = '◄' if m['ano'] == hoje.year and m['mes'] == hoje.month else ' '
                _ln(f"  {label}{flag} [{barra}]  {m['total_dias']:3}d  {m['n_func']}func")
        paginar(d, f"{t('graf_titulo')} — {setor}", subs, render_sub, resumo_sub)
    elif op == '4':
        func = sel_func(d)
        if not func:
            return
        ev = _evolucao_func(func, n_meses)
        an = analise_periodo_atual(d, func)
        max_mes = max((m['dias'] for m in ev), default=1) or 1
        max_acum = max((m['acumulado'] for m in ev), default=1) or 1
        bw = max(10, (_larg() - 4) * 30 // 100)

        def resumo_func():
            _lnd(t('rel_data'), hoje.strftime('%d/%m/%Y %H:%M'))
            _lnd(t('rel_nome'), func['nome'])
            _lnd(t('rel_setor_l'), f"{func['setor']} → {func['subsetor']}")
            _lnd(t('graf_periodo'), f'{n_meses} meses')
            if func.get('data_admissao'):
                _lnd(t('data_admissao'), func['data_admissao'])
            if an['tipo'] == 'aquisitivo':
                ini_s = an['ini'].strftime('%d/%m/%Y')
                fim_s = (an['fim'] - timedelta(days=1)).strftime('%d/%m/%Y')
                _lnd(t('pa_atual') + f" #{an['numero']}", f'{ini_s} → {fim_s}')
                if an['max_dias'] and an['max_dias'] > 0:
                    bp = _barra_progresso(an['tirados'], an['max_dias'])
                    if bp:
                        barra, pct = bp
                        _lnd(t('pa_tirados'), f"{an['tirados']}/{an['max_dias']} {t('pa_dias')}  [{barra}] {pct}%  Restam: {an['restantes']}")
            _lnd('Legenda', 'Mês=barras mensais  Acumulado=total  ◄=Mês atual')

        def render_func_mes(m):
            label = _mes_label(m['ano'], m['mes'])
            b_mes = _barra_grafico(m['dias'], max_mes, bw)
            b_acum = _barra_grafico(m['acumulado'], max_acum, bw)
            flag = '◄' if m['ano'] == hoje.year and m['mes'] == hoje.month else ' '
            _lvz()
            _ln(f"  {label}{flag}  Mês      : [{b_mes}]  {m['dias']:3} {t('pa_dias')}")
            _ln(f"  {' ' * 6}{' '}  Acumulado: [{b_acum}]  {m['acumulado']:3} {t('pa_dias')}")
        paginar(d, f"{t('graf_titulo')} — {func['nome']}", ev, render_func_mes, resumo_func)
    else:
        flash(t('invalido'), erro=True)

def _calcular_painel(d):
    hoje = datetime.today()
    lim30 = datetime(hoje.year, hoje.month, hoje.day) + timedelta(days=30)
    hoje_d = datetime(hoje.year, hoje.month, hoje.day)
    em_ferias = []
    em_30dias = []
    for func in ord_funcs(d):
        v = f" [{func.get('vinculo', '')}]" if func.get('vinculo') else ''
        for f in func['ferias']:
            ini = conv_data(f['inicio'])
            fim = conv_data(f['fim'])
            if not ini or not fim:
                continue
            if ini <= hoje <= fim:
                em_ferias.append({'nome': func['nome'] + v, 'setor': func['setor'], 'subsetor': func['subsetor'], 'inicio': f['inicio'], 'fim': f['fim'], 'dias_rest': (fim - hoje_d).days + 1, 'venda': f.get('venda_ferias', False)})
                break
            if hoje_d < ini <= lim30:
                em_30dias.append({'nome': func['nome'] + v, 'setor': func['setor'], 'subsetor': func['subsetor'], 'inicio': f['inicio'], 'fim': f['fim'], 'dias_ini': (ini - hoje_d).days, 'venda': f.get('venda_ferias', False)})
                break
    em_ferias.sort(key=lambda x: x['dias_rest'])
    em_30dias.sort(key=lambda x: x['dias_ini'])
    return (em_ferias, em_30dias)

def _linhas_painel_menu(em_ferias, em_30dias, dias_alerta=7):
    linhas = []
    MAX = 3
    linhas.append(f"[{t('painel_agora')}]")
    if em_ferias:
        for r in em_ferias[:MAX]:
            linhas.append(f"  › {r['nome']}  —  até {r['fim']}  ({r['dias_rest']} {t('painel_dias_rest')})")
        if len(em_ferias) > MAX:
            linhas.append(f'  ... e mais {len(em_ferias) - MAX} funcionário(s)')
    else:
        linhas.append(f"  {t('menu_nenhum_agora')}")
    linhas.append(f"[{t('menu_inicio_label', n=dias_alerta)}]")
    proximos = [r for r in em_30dias if r['dias_ini'] <= dias_alerta]
    if proximos:
        for r in proximos[:MAX]:
            linhas.append(f"  › {r['nome']}  —  {r['inicio']}  (em {r['dias_ini']} {t('painel_dias_ini')})")
        if len(proximos) > MAX:
            linhas.append(f'  ... e mais {len(proximos) - MAX} funcionário(s)')
    else:
        linhas.append(f"  {t('menu_nenhum_prox', n=dias_alerta)}")
    return linhas

def painel_ferias(d):
    """Exibe o painel de férias atuais e dos próximos 30 dias."""
    em_ferias, em_30dias = _calcular_painel(d)
    hoje_str = datetime.today().strftime('%d/%m/%Y  %H:%M')
    itens = []
    itens.append({'tipo': 'secao', 'txt': t('painel_agora')})
    if em_ferias:
        for r in em_ferias:
            itens.append({'tipo': 'agora', **r})
    else:
        itens.append({'tipo': 'vazio_ag'})
    itens.append({'tipo': 'secao', 'txt': t('painel_30dias')})
    if em_30dias:
        for r in em_30dias:
            itens.append({'tipo': 'em30', **r})
    else:
        itens.append({'tipo': 'vazio_30'})

    def resumo():
        _lnd(t('rel_data'), hoje_str)
        _lnd(t('painel_em_ferias'), str(len(em_ferias)) + ' funcionário(s)')
        _lnd(t('painel_em_30d'), str(len(em_30dias)) + ' funcionário(s)')

    def render_item(item):
        tipo = item['tipo']
        if tipo == 'secao':
            _dleve()
            _ln(f"  {item['txt']}", 'center')
            _dleve()
        elif tipo == 'vazio_ag':
            _lvz()
            _ln(f"  {t('painel_nenhum_ag')}")
            _lvz()
        elif tipo == 'vazio_30':
            _lvz()
            _ln(f"  {t('painel_nenhum_30')}")
            _lvz()
        elif tipo == 'agora':
            vd = f"  {t('fer_venda_lbl')}" if item['venda'] else ''
            _lvz()
            _ln(f"  › {item['nome']}")
            _ln(f"    {item['setor']}  →  {item['subsetor']}")
            _ln(f"    {item['inicio']}  até  {item['fim']}{vd}")
            _ln(f"    {t('painel_termina')}: {item['dias_rest']} {t('painel_dias_rest')}")
        elif tipo == 'em30':
            vd = f"  {t('fer_venda_lbl')}" if item['venda'] else ''
            _lvz()
            _ln(f"  › {item['nome']}")
            _ln(f"    {item['setor']}  →  {item['subsetor']}")
            _ln(f"    {item['inicio']}  até  {item['fim']}{vd}")
            _ln(f"    {t('painel_inicia')}: {item['dias_ini']} {t('painel_dias_ini')}")
    paginar(d, t('painel_titulo'), itens, render_item, resumo)

# ---------------------------------------------------------------------------
# Cadastros e gerenciamento de férias
# ---------------------------------------------------------------------------

def menu_cadastros(d):
    """Hub único para cadastros, reduzindo a quantidade de opções no menu principal."""
    while True:
        itens = [(1, t('set_titulo')), (2, t('fun_titulo')), (3, t('vin_titulo'))]
        _render_menu('CADASTROS', itens, info=['Setores, funcionários e vínculos'], rodape=[(0, t('voltar'))])
        op=inp(t('opcao')).strip()
        if op == '1': menu_setores(d)
        elif op == '2': menu_funcionarios(d)
        elif op == '3': menu_vinculos(d)
        elif op == '0': break
        else: flash(t('invalido'), erro=True)

def menu_setores(d):
    while True:
        _render_menu(t('set_titulo'), [(1, t('set_listar')), (2, t('set_novo')), (3, t('set_excluir')), (4, t('set_novo_sub')), (5, t('set_excluir_sub'))], rodape=[(0, t('voltar'))])
        op = inp(t('opcao')).strip()
        if op == '1':
            listar_setores(d)
        elif op == '2':
            criar_setor(d)
        elif op == '3':
            excluir_setor(d)
        elif op == '4':
            criar_subsetor(d)
        elif op == '5':
            excluir_subsetor(d)
        elif op == '0':
            break
        else:
            flash(t('invalido'), erro=True)

def listar_setores(d):
    setores_ord = ord_setores(d)
    if not setores_ord:
        limpar()
        titulo_box(t('set_titulo'))
        _lvz()
        _ln('  ' + t('nenhum_setor'), 'center')
        _lvz()
        fundo()
        pausar()
        return

    def render(s):
        _lvz()
        _ln(f'  {s}')
        fs = [f for f in d['funcionarios'] if f['setor'] == s]
        _ln(f"    {t('rel_total_func')}: {len(fs)}")
        subs = ord_subs(d, s)
        if subs:
            for j, sub in enumerate(subs, 1):
                _ln(f'    {j}. {sub}')
        else:
            _ln('    ' + t('sem_sub'))

    def resumo():
        _lnd(t('rel_set_cad'), str(len(setores_ord)))
        _lnd(t('rel_subs'), str(sum((len(d['setores'][s]['subsetores']) for s in setores_ord))))
        _lnd(t('rel_total_func'), str(len(d['funcionarios'])))
    paginar(d, t('set_titulo'), setores_ord, render, resumo)

def criar_setor(d):
    limpar()
    titulo_box(t('set_novo'))
    _lvz()
    fundo()
    p()
    nome = inp(t('set_nome')).strip()
    if not nome:
        flash(t('nome_vazio'), erro=True)
        return
    if nome in d['setores']:
        flash(t('set_ja_existe'), erro=True)
        return
    d['setores'][nome] = {'subsetores': []}
    salvar_dados(d)
    flash(f"'{nome}' — " + t('set_criado'))

def excluir_setor(d):
    limpar()
    titulo_box(t('set_excluir'))
    _lvz()
    fundo()
    if not d['setores']:
        flash(t('nenhum_setor'), erro=True)
        return
    setor = sel_setor(d)
    if not setor:
        return
    vinc = [f for f in d['funcionarios'] if f['setor'] == setor]
    if vinc:
        flash(t('set_vinculados', n=len(vinc)), erro=True)
        return
    c = inp(t('confirmar_excl')).strip().lower()
    if c == t('sim'):
        del d['setores'][setor]
        d['regras']['por_setor'].pop(setor, None)
        for k in [k for k in d['regras']['por_subsetor'] if k.startswith(setor + SEP)]:
            d['regras']['por_subsetor'].pop(k, None)
        salvar_dados(d)
        flash(f"'{setor}' — " + t('set_excluido'))
    else:
        flash(t('excluir_cancel'))

def criar_subsetor(d):
    limpar()
    titulo_box(t('set_novo_sub'))
    _lvz()
    fundo()
    if not d['setores']:
        flash(t('nenhum_setor'), erro=True)
        return
    setor = sel_setor(d)
    if not setor:
        return
    p()
    nome = inp(f"{t('sub_nome')} ({setor}):").strip()
    if not nome:
        flash(t('nome_vazio'), erro=True)
        return
    if nome in d['setores'][setor]['subsetores']:
        flash(t('sub_ja_existe'), erro=True)
        return
    d['setores'][setor]['subsetores'].append(nome)
    salvar_dados(d)
    flash(f"'{nome}' — " + t('sub_criado'))

def excluir_subsetor(d):
    limpar()
    titulo_box(t('set_excluir_sub'))
    _lvz()
    fundo()
    if not d['setores']:
        flash(t('nenhum_setor'), erro=True)
        return
    setor = sel_setor(d)
    if not setor:
        return
    sub = sel_sub(d, setor)
    if not sub:
        return
    vinc = [f for f in d['funcionarios'] if f['setor'] == setor and f['subsetor'] == sub]
    if vinc:
        flash(t('set_vinculados', n=len(vinc)), erro=True)
        return
    c = inp(t('confirmar_excl')).strip().lower()
    if c == t('sim'):
        d['setores'][setor]['subsetores'].remove(sub)
        d['regras']['por_subsetor'].pop(_chave_sub(setor, sub), None)
        salvar_dados(d)
        flash(f"'{sub}' — " + t('sub_excluido'))
    else:
        flash(t('excluir_cancel'))

def menu_vinculos(d):
    while True:
        _render_menu(t('vin_titulo'), [(1, t('vin_listar')), (2, t('vin_novo')), (3, t('vin_excluir'))], rodape=[(0, t('voltar'))])
        op = inp(t('opcao')).strip()
        if op == '1':
            listar_vinculos(d)
        elif op == '2':
            criar_vinculo(d)
        elif op == '3':
            excluir_vinculo(d)
        elif op == '0':
            break
        else:
            flash(t('invalido'), erro=True)

def listar_vinculos(d):
    vs = ord_vinculos(d)
    if not vs:
        limpar()
        titulo_box(t('vin_titulo'))
        _lvz()
        _ln('  ' + t('nenhum_vinculo'), 'center')
        _lvz()
        fundo()
        pausar()
        return
    paginar(d, t('vin_titulo'), vs, lambda v: _ln(f'  › {v}'))

def criar_vinculo(d):
    limpar()
    titulo_box(t('vin_novo'))
    _lvz()
    fundo()
    p()
    nome = inp(t('vin_nome')).strip()
    if not nome:
        flash(t('nome_vazio'), erro=True)
        return
    if nome in d['vinculos']:
        flash(t('vin_ja_existe'), erro=True)
        return
    d['vinculos'].append(nome)
    salvar_dados(d)
    flash(f"'{nome}' — " + t('vin_criado'))

def excluir_vinculo(d):
    limpar()
    titulo_box(t('vin_excluir'))
    _lvz()
    fundo()
    if not d['vinculos']:
        flash(t('nenhum_vinculo'), erro=True)
        return
    v = sel_vinculo(d, permitir_nenhum=False)
    if not v:
        return
    em = [f for f in d['funcionarios'] if f.get('vinculo') == v]
    if em:
        flash(t('vin_em_uso', n=len(em)), erro=True)
        return
    c = inp(t('confirmar_excl')).strip().lower()
    if c == t('sim'):
        d['vinculos'].remove(v)
        d['regras']['por_vinculo'].pop(v, None)
        salvar_dados(d)
        flash(f"'{v}' — " + t('vin_excluido'))
    else:
        flash(t('excluir_cancel'))

def menu_funcionarios(d):
    while True:
        _render_menu(t('fun_titulo'), [(1, t('fun_listar')), (2, t('fun_por_setor')), (3, t('fun_novo')), (4, t('fun_excluir')), (5, t('fun_vinculos'))], rodape=[(0, t('voltar'))])
        op = inp(t('opcao')).strip()
        if op == '1':
            listar_funcionarios(d)
        elif op == '2':
            listar_funcionarios_por_setor(d)
        elif op == '3':
            cadastrar_funcionario(d)
        elif op == '4':
            excluir_funcionario(d)
        elif op == '5':
            menu_vinculos(d)
        elif op == '0':
            break
        else:
            flash(t('invalido'), erro=True)

def listar_funcionarios(d):
    funcs = ord_funcs(d)
    if not funcs:
        limpar()
        titulo_box(t('fun_titulo'))
        _lvz()
        _ln('  ' + t('nenhum_func'), 'center')
        _lvz()
        fundo()
        pausar()
        return
    cf = sum((1 for f in funcs if f['ferias']))

    def resumo():
        _lnd(t('rel_total_func'), str(len(funcs)))
        _lnd(t('rel_com_ferias'), str(cf))
        _lnd(t('rel_sem_ferias'), str(len(funcs) - cf))
    paginar(d, t('fun_titulo'), funcs, lambda func: _render_func_simples(func, d), resumo)

def listar_funcionarios_por_setor(d):
    setores_ord = ord_setores(d)
    if not setores_ord:
        limpar()
        titulo_box(t('fun_por_setor'))
        _lvz()
        _ln('  ' + t('nenhum_setor'), 'center')
        _lvz()
        fundo()
        pausar()
        return
    blocos = [{'setor': s, 'subs': [{'sub': sub, 'funcs': ord_funcs(d, [f for f in d['funcionarios'] if f['setor'] == s and f['subsetor'] == sub])} for sub in ord_subs(d, s)], 'total': sum((1 for f in d['funcionarios'] if f['setor'] == s))} for s in setores_ord]
    tf = len(d['funcionarios'])
    cf = sum((1 for f in d['funcionarios'] if f['ferias']))

    def resumo():
        _lnd(t('rel_total_func'), str(tf))
        _lnd(t('rel_com_ferias'), str(cf))
        _lnd(t('rel_set_cad'), str(len(setores_ord)))

    def render_b(bloco):
        _lvz()
        _ln(f"  ══  {bloco['setor']}  ({bloco['total']} func.)  ══")
        for sb in bloco['subs']:
            fs_sub = sb['funcs']
            c_fer = sum((1 for f in fs_sub if f['ferias']))
            _lvz()
            _ln(f"  +── {sb['sub']}")
            _ln(f"      Func: {len(fs_sub)}  |  {t('rel_com_ferias')}: {c_fer}  |  {t('rel_sem_ferias')}: {len(fs_sub) - c_fer}")
            _dleve()
            if not fs_sub:
                _ln('      ' + t('sem_func'))
            else:
                for func in fs_sub:
                    v = f" [{func.get('vinculo', '')}]" if func.get('vinculo') else ''
                    _ln(f"      › {func['nome']}{v}")
                    _ln(_linha_periodo_atual(func, d))
                    pas, atu, fut = classificar_ferias(func)
                    if atu:
                        _ln(f"        Em férias: {atu[0]['inicio']} até {atu[0]['fim']}")
                    elif fut:
                        _ln(f"        Próximo: {fut[0]['inicio']} até {fut[0]['fim']}")
    paginar(d, t('fun_por_setor'), blocos, render_b, resumo)

def cadastrar_funcionario(d):
    limpar()
    titulo_box(t('fun_novo'))
    _lvz()
    fundo()
    if not d['setores']:
        flash(t('nenhum_setor'), erro=True)
        return
    setor = sel_setor(d)
    if not setor:
        return
    sub = sel_sub(d, setor)
    if not sub:
        return
    p()
    p('  ' + t('fun_vinculo_sel'))
    vinculo = sel_vinculo(d, permitir_nenhum=True)
    p()
    nome = inp(t('fun_nome')).strip()
    if not nome:
        flash(t('nome_vazio'), erro=True)
        return
    if any((f['nome'].lower() == nome.lower() and f['setor'] == setor and (f['subsetor'] == sub) for f in d['funcionarios'])):
        flash(t('fun_ja_existe'), erro=True)
        return
    adm = inp(f"{t('data_admissao')} (DD/MM/AAAA ou ENTER para pular):").strip()
    if adm and (not conv_data(adm)):
        flash(t('admissao_inv'), erro=True)
        return
    d['funcionarios'].append({'nome': nome, 'setor': setor, 'subsetor': sub, 'vinculo': vinculo or '', 'data_admissao': adm, 'ferias': []})
    salvar_dados(d)
    flash(f"'{nome}' — " + t('fun_criado'))

def excluir_funcionario(d):
    limpar()
    titulo_box(t('fun_excluir'))
    _lvz()
    fundo()
    func = sel_func(d)
    if not func:
        return
    p()
    p(f"  {func['nome']} ({func['setor']} → {func['subsetor']})")
    c = inp(t('confirmar_excl')).strip().lower()
    if c == t('sim'):
        d['funcionarios'].remove(func)
        salvar_dados(d)
        flash(f"'{func['nome']}' — " + t('fun_excluido'))
    else:
        flash(t('excluir_cancel'))


def _bh_parse_horas(valor, permitir_sinal=False):
    """Converte HH:MM em minutos. Para ajuste, aceita sinal explícito."""
    if not valor:
        return None
    texto = valor.strip()
    sinal = 1
    if permitir_sinal and texto[:1] in ('+', '-'):
        sinal = -1 if texto[0] == '-' else 1
        texto = texto[1:]
    if not texto or texto.count(':') != 1:
        return None
    hh, mm = texto.split(':', 1)
    if not hh.isdigit() or not mm.isdigit():
        return None
    h, m = int(hh), int(mm)
    if m > 59 or h > 999:
        return None
    total = h * 60 + m
    if total <= 0:
        return None
    return sinal * total


def _bh_fmt_minutos(minutos, sinal=True):
    try:
        minutos = int(minutos)
    except (TypeError, ValueError):
        minutos = 0
    prefixo = '+' if minutos >= 0 else '-'
    total = abs(minutos)
    horas, mins = divmod(total, 60)
    return f'{prefixo if sinal else ""}{horas:02d}:{mins:02d}'


def _bh_resumo_func(func):
    con = _conn()
    try:
        row = con.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN tipo='C' THEN minutos ELSE 0 END),0) AS creditos,
                COALESCE(SUM(CASE WHEN tipo='D' THEN minutos ELSE 0 END),0) AS debitos,
                COALESCE(SUM(CASE WHEN tipo='A' THEN minutos ELSE 0 END),0) AS ajustes,
                COALESCE(SUM(CASE WHEN tipo='C' THEN minutos WHEN tipo='D' THEN -minutos ELSE minutos END),0) AS saldo,
                COUNT(*) AS movimentos
            FROM banco_horas WHERE funcionario_id=?
        """, (func['_id'],)).fetchone()
        return dict(row)
    finally:
        con.close()


def _bh_registrar(func, tipo, minutos, data_s, motivo):
    con = _conn()
    try:
        usuario_id = None
        if SESSAO.get('login'):
            row = con.execute('SELECT id FROM usuarios WHERE login=?', (SESSAO['login'],)).fetchone()
            usuario_id = row['id'] if row else None
        con.execute("""
            INSERT INTO banco_horas (funcionario_id,data,tipo,minutos,motivo,usuario_id,criado_em)
            VALUES (?,?,?,?,?,?,?)
        """, (func['_id'], data_s, tipo, minutos, motivo.strip(), usuario_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        con.commit()
    finally:
        con.close()


def _bh_render_saldo(func, detalhe=True):
    resumo = _bh_resumo_func(func)
    _lvz()
    _ln(f"  › {func['nome']}")
    _ln(f"    {func['setor']} → {func['subsetor']}")
    _lnd(t('bh_total_creditos'), _bh_fmt_minutos(resumo['creditos']))
    _lnd(t('bh_total_debitos'), _bh_fmt_minutos(-resumo['debitos']))
    if resumo['ajustes']:
        _lnd(t('bh_ajuste'), _bh_fmt_minutos(resumo['ajustes']))
    _lnd(t('bh_saldo_atual'), _bh_fmt_minutos(resumo['saldo']))
    _lnd('Movimentações', str(resumo['movimentos']))
    if detalhe and resumo['movimentos']:
        con = _conn()
        try:
            rows = con.execute("""
                SELECT data,tipo,minutos,motivo,criado_em
                FROM banco_horas WHERE funcionario_id=? ORDER BY data DESC, id DESC
            """, (func['_id'],)).fetchall()
        finally:
            con.close()
        _lvz()
        for r in rows:
            if r['tipo'] == 'C':
                tipo, valor = t('bh_tipo_credito'), _bh_fmt_minutos(r['minutos'])
            elif r['tipo'] == 'D':
                tipo, valor = t('bh_tipo_debito'), _bh_fmt_minutos(-r['minutos'])
            else:
                tipo, valor = t('bh_tipo_ajuste'), _bh_fmt_minutos(r['minutos'])
            _ln(f"    {r['data']} | {tipo:<9} | {valor:>8} | {r['motivo']}")


def bh_consultar_saldo(d):
    func = sel_func(d)
    if not func:
        return
    limpar(); titulo_box(t('bh_saldo'))
    _ln(t('bh_desc'), 'center'); _dleve()
    _bh_render_saldo(func, detalhe=True)
    _dleve(); fundo(); pausar()


def _bh_lancar(d, tipo):
    """Registra crédito ou débito por duração HH:MM; a data é apenas auditoria automática."""
    limpar(); titulo_box(t('bh_credito' if tipo == 'C' else 'bh_debito')); _lvz(); fundo()
    func = sel_func(d)
    if not func: return
    p(); p(f"  {func['nome']}  ({func['setor']} → {func['subsetor']})"); p()
    horas_s = inp(t('bh_horas')).strip()
    minutos = _bh_parse_horas(horas_s)
    if minutos is None:
        flash(t('bh_horas_inv'), erro=True); return
    motivo = inp(t('bh_motivo')).strip()
    if not motivo:
        flash(t('bh_motivo_inv'), erro=True); return
    data_s = datetime.today().strftime('%d/%m/%Y')
    _bh_registrar(func, tipo, minutos, data_s, motivo)
    sinal = minutos if tipo == 'C' else -minutos
    flash(f"{func['nome']}: {_bh_fmt_minutos(sinal)} — " + t('bh_credito_ok' if tipo == 'C' else 'bh_debito_ok'))

def bh_extrato(d):
    limpar(); titulo_box(t('bh_extrato')); _lvz(); fundo()
    func = sel_func(d)
    if not func: return
    con = _conn()
    try:
        rows = con.execute("""
            SELECT data,tipo,minutos,motivo,criado_em
            FROM banco_horas WHERE funcionario_id=? ORDER BY data DESC, id DESC
        """, (func['_id'],)).fetchall()
    finally:
        con.close()
    if not rows:
        limpar(); titulo_box(t('bh_extrato')); _lvz(); _ln(f"  {func['nome']}", 'center'); _lvz(); _ln('  ' + t('bh_sem_mov'), 'center'); _lvz(); fundo(); pausar(); return
    def resumo():
        r = _bh_resumo_func(func)
        _lnd(t('bh_saldo_atual'), _bh_fmt_minutos(r['saldo']))
        _lnd('Movimentações', str(r['movimentos']))
    def render(r):
        if r['tipo'] == 'C': tipo, valor = t('bh_tipo_credito'), _bh_fmt_minutos(r['minutos'])
        elif r['tipo'] == 'D': tipo, valor = t('bh_tipo_debito'), _bh_fmt_minutos(-r['minutos'])
        else: tipo, valor = t('bh_tipo_ajuste'), _bh_fmt_minutos(r['minutos'])
        _lvz(); _ln(f"  {r['data']} | {tipo} | {valor} | {r['motivo']}")
        _ln(f"    {t('bh_usuario')}: {r['criado_em']}")
    paginar(d, f"{t('bh_extrato')}: {func['nome']}", rows, render, resumo)


def _bh_todos_saldos(d):
    registros = []
    for func in ord_funcs(d):
        resumo = _bh_resumo_func(func)
        registros.append({'func': func, **resumo})
    return registros


def _bh_relatorio_resumo(registros):
    total = sum(r['saldo'] for r in registros)
    positivos = [r for r in registros if r['saldo'] > 0]
    negativos = [r for r in registros if r['saldo'] < 0]
    zerados = len(registros) - len(positivos) - len(negativos)
    _lnd('Funcionários analisados', str(len(registros)))
    _lnd('Saldo consolidado', _bh_fmt_minutos(total))
    _lnd('Com saldo positivo', str(len(positivos)))
    _lnd('Com saldo negativo', str(len(negativos)))
    _lnd('Com saldo zerado', str(zerados))
    _lnd('Créditos acumulados', _bh_fmt_minutos(sum(r['creditos'] for r in registros)))
    _lnd('Débitos acumulados', _bh_fmt_minutos(-sum(r['debitos'] for r in registros)))


def bh_relatorio(d):
    registros = _bh_todos_saldos(d)
    if not registros:
        flash(t('bh_sem_func'), erro=True); return
    limpar(); titulo_box('RELATÓRIOS DO BANCO DE HORAS'); _lvz(); _bh_relatorio_resumo(registros); _dleve()
    _ln('  1. Resumo geral')
    _ln('  2. Ranking de maiores saldos positivos')
    _ln('  3. Ranking de maiores saldos negativos')
    _ln('  4. Gráfico de saldos (barras)')
    _ln('  5. Alertas de saldo')
    _ln('  0. Voltar')
    _dleve()
    op = inp(t('opcao')).strip()
    if op == '0': return
    if op == '1':
        limpar(); titulo_box('RESUMO GERAL'); _bh_relatorio_resumo(registros)
    elif op in ('2', '3'):
        if op == '2':
            selecionados = sorted((r for r in registros if r['saldo'] > 0), key=lambda r: r['saldo'], reverse=True)[:10]
            titulo = 'RANKING — MAIORES SALDOS POSITIVOS'
        else:
            selecionados = sorted((r for r in registros if r['saldo'] < 0), key=lambda r: r['saldo'])[:10]
            titulo = 'RANKING — MAIORES SALDOS NEGATIVOS'
        limpar(); titulo_box(titulo)
        if not selecionados: _ln('  Nenhum funcionário nesta categoria.')
        for i, r in enumerate(selecionados, 1):
            _ln(f"  {i:>2}. {r['func']['nome']}")
            _ln(f"      {r['func']['setor']} → {r['func']['subsetor']} | {_bh_fmt_minutos(r['saldo'])}")
    elif op == '4':
        limpar(); titulo_box('GRÁFICO DE SALDOS — TOP 10 POR VALOR ABSOLUTO')
        top = sorted(registros, key=lambda r: abs(r['saldo']), reverse=True)[:10]
        max_abs = max((abs(r['saldo']) for r in top), default=0)
        if not max_abs: _ln('  Todos os saldos estão zerados.')
        for r in top:
            saldo = r['saldo']; largura = int(abs(saldo) * 30 / max_abs) if max_abs else 0
            barra = ('+' if saldo > 0 else '−' if saldo < 0 else '·') * largura
            _ln(f"  {r['func']['nome'][:22]:<22} {barra:<30} {_bh_fmt_minutos(saldo)}")
        _ln('  Escala relativa ao maior saldo absoluto exibido.')
    elif op == '5':
        limpar(); titulo_box('ALERTAS DE SALDO')
        # Faixas de atenção: 20h; saldo crítico: 40h, em qualquer direção.
        alertas = sorted((r for r in registros if abs(r['saldo']) >= 20*60), key=lambda r: abs(r['saldo']), reverse=True)
        _ln('  Atenção: saldo a partir de 20:00 | Crítico: a partir de 40:00')
        if not alertas: _ln('  Nenhum alerta: todos os saldos estão abaixo de 20:00.')
        for r in alertas:
            nivel = 'CRÍTICO' if abs(r['saldo']) >= 40*60 else 'ATENÇÃO'
            direcao = 'positivo' if r['saldo'] > 0 else 'negativo'
            _ln(f"  [{nivel}] {r['func']['nome']} — {_bh_fmt_minutos(r['saldo'])} ({direcao})")
    else:
        flash(t('invalido'), erro=True); return
    _dleve(); fundo(); pausar()


def bh_ajustar_saldo(d):
    if SESSAO.get('nivel') != 'admin':
        flash(t('bh_somente_admin'), erro=True); return
    limpar(); titulo_box(t('bh_ajuste')); _lvz(); _ln('  ' + t('bh_historico_imutavel')); _lvz(); fundo()
    func = sel_func(d)
    if not func: return
    p(); p(f"  {func['nome']}  ({func['setor']} → {func['subsetor']})"); p()
    horas_s = inp(t('bh_ajuste_horas')).strip()
    minutos = _bh_parse_horas(horas_s, permitir_sinal=True)
    if minutos is None:
        flash(t('bh_ajuste_inv'), erro=True); return
    motivo = inp(t('bh_motivo')).strip()
    if not motivo:
        flash(t('bh_motivo_inv'), erro=True); return
    p(); p(f"  {t('bh_saldo_atual')}: {_bh_fmt_minutos(_bh_resumo_func(func)['saldo'])}")
    p(f"  Ajuste informado: {_bh_fmt_minutos(minutos)}")
    if inp(t('bh_confirmar_ajuste')).strip().lower() != t('sim'):
        flash(t('excluir_cancel')); return
    data_s = datetime.today().strftime('%d/%m/%Y')
    _bh_registrar(func, 'A', minutos, data_s, motivo)
    flash(f"{func['nome']}: {_bh_fmt_minutos(minutos)} — " + t('bh_ajuste_ok'))


def bh_ranking_alertas(d):
    """Atalho para ranking e alertas, mantendo os dados consolidados em HH:MM."""
    bh_relatorio(d)


def menu_banco_horas(d):
    while True:
        itens = [(1, t('bh_saldo')), (2, t('bh_credito')), (3, t('bh_debito')), (4, t('bh_extrato')),
                 (5, t('bh_relatorio')), (7, 'Rankings, gráficos e alertas')]
        if SESSAO.get('nivel') == 'admin': itens.append((6, t('bh_ajuste')))
        _render_menu(t('bh_titulo'), itens, info=[t('bh_desc'), 'Saldos expressos em HH:MM, com sinal positivo ou negativo.'], rodape=[(0, t('voltar'))])
        op = inp(t('opcao')).strip()
        if op == '1': bh_consultar_saldo(d)
        elif op == '2': _bh_lancar(d, 'C')
        elif op == '3': _bh_lancar(d, 'D')
        elif op == '4': bh_extrato(d)
        elif op in ('5', '7'): bh_relatorio(d)
        elif op == '6' and SESSAO.get('nivel') == 'admin': bh_ajustar_saldo(d)
        elif op == '0': break
        else: flash(t('invalido'), erro=True)

def menu_ferias(d):
    while True:
        _render_menu(t('fer_titulo'), [(1, t('fer_agendar')), (2, t('fer_cancelar')), (3, t('fer_calendario'))], rodape=[(0, t('voltar'))])
        op = inp(t('opcao')).strip()
        if op == '1':
            agendar_ferias(d)
        elif op == '2':
            cancelar_ferias(d)
        elif op == '3':
            ver_calendario(d)
        elif op == '0':
            break
        else:
            flash(t('invalido'), erro=True)

def agendar_ferias(d):
    limpar()
    titulo_box(t('fer_agendar'))
    _lvz()
    fundo()
    func = sel_func(d)
    if not func:
        return
    v = f" [{func.get('vinculo', '')}]" if func.get('vinculo') else ''
    p()
    p(f"  {func['nome']}{v}  ({func['setor']} → {func['subsetor']})")
    p()
    ini_s = inp(t('fer_inicio')).strip()
    fim_s = inp(t('fer_fim')).strip()
    ini = conv_data(ini_s)
    fim = conv_data(fim_s)
    if not ini or not fim:
        flash(t('fer_data_inv'), erro=True)
        return
    if ini > fim:
        flash(t('fer_data_ord'), erro=True)
        return
    erros = validar_agendamento(d, func, ini, fim)
    if erros:
        limpar()
        titulo_box(t('fer_bloqueado'))
        _lvz()
        for i, e in enumerate(erros, 1):
            _ln(f'  {i}. {e}')
        _lvz()
        fundo()
        pausar()
        return
    venda = False
    if obter_regra(d, 'permite_venda_ferias', func['setor'], func['subsetor'], func.get('vinculo', '')):
        p()
        p('  ' + t('fer_venda_info'))
        venda = inp(t('fer_venda_marcar')).strip().lower() == t('sim')
    func['ferias'].append({'inicio': ini_s, 'fim': fim_s, 'venda_ferias': venda})
    salvar_dados(d)
    an = analise_periodo_atual(d, func)
    if an['tipo'] == 'aquisitivo':
        label = f"Prd.{an['numero']}: {an['tirados']} {t('pa_dias')} tirados"
    else:
        label = f"Ano {an['ano_civil']}: {an['tirados']} {t('pa_dias')} tirados"
    flash(f"{func['nome']}: {ini_s} → {fim_s}  |  {label} — " + t('fer_ok'))

def cancelar_ferias(d):
    limpar()
    titulo_box(t('fer_cancelar'))
    _lvz()
    fundo()
    func = sel_func(d)
    if not func:
        return
    if not func['ferias']:
        flash(f"{func['nome']} {t('fer_sem')}", erro=True)
        return
    pas, atu, fut = classificar_ferias(func)
    ferias_ord = ord_ferias(d, list(func['ferias']))

    def render_f(f):
        dias = calc_dias(f['inicio'], f['fim'])
        vd = ' ' + t('fer_venda_lbl') if f.get('venda_ferias') else ''
        ini = conv_data(f['inicio'])
        hoje = datetime.today()
        cat = f"[{t('rel_andamento')}]" if ini and ini <= hoje <= conv_data(f['fim']) else f"[{t('rel_futuro')}]" if ini and ini > hoje else f"[{t('rel_concluido')}]"
        _ln(f"  {f['inicio']}  até  {f['fim']}  ({dias} {t('pa_dias')}){vd}  {cat}")

    def resumo():
        _lnd(t('fun_lista')[:-1], func['nome'])
        _lnd(t('rel_andamento'), str(len(atu)) + ' período(s)' if atu else '—')
        _lnd(t('periodos_futuros'), str(len(fut)) + ' período(s)' if fut else '—')
        _lnd(t('periodos_passados'), str(len(pas)) + ' período(s)' if pas else '—')
    paginar(d, t('fer_cancelar'), ferias_ord, render_f, resumo)
    p()
    p('  Informe o número do período a cancelar:')
    for i, f in enumerate(ferias_ord, 1):
        p(f"    {i}. {f['inicio']} até {f['fim']}  ({calc_dias(f['inicio'], f['fim'])} {t('pa_dias')})")
    p(f"    0. {t('voltar')}")
    try:
        e = int(inp(t('fer_remover_num')))
        if e == 0:
            return
        idx = e - 1
        if 0 <= idx < len(ferias_ord):
            rm = ferias_ord[idx]
            func['ferias'] = [f for f in func['ferias'] if not (f['inicio'] == rm['inicio'] and f['fim'] == rm['fim'])]
            salvar_dados(d)
            flash(f"{rm['inicio']} → {rm['fim']} — " + t('fer_removida'))
        else:
            flash(t('fora_intervalo'), erro=True)
    except ValueError:
        flash(t('so_numero'), erro=True)

def ver_calendario(d):
    setores_ord = ord_setores(d)
    if not setores_ord:
        limpar()
        titulo_box(t('fer_cal_titulo'))
        _lvz()
        _ln('  ' + t('nenhum_setor'), 'center')
        _lvz()
        fundo()
        pausar()
        return
    blocos = [{'setor': s, 'subs': [{'sub': sub, 'funcs': ord_funcs(d, [f for f in d['funcionarios'] if f['setor'] == s and f['subsetor'] == sub])} for sub in ord_subs(d, s)]} for s in setores_ord]

    def render_cal(bloco):
        _lvz()
        _ln(f"  {bloco['setor']}")
        for sb in bloco['subs']:
            _ln(f"  +── {sb['sub']}")
            if not sb['funcs']:
                _ln('       ' + t('sem_func'))
            else:
                for func in sb['funcs']:
                    pas, atu, fut = classificar_ferias(func)
                    v = f" [{func.get('vinculo', '')}]" if func.get('vinculo') else ''
                    if atu:
                        f0 = atu[0]
                        vd = ' ' + t('fer_venda_lbl') if f0.get('venda_ferias') else ''
                        _ln(f"       [ANDAMENTO] {func['nome']}{v}: {f0['inicio']} até {f0['fim']}{vd}")
                    elif fut:
                        f0 = fut[0]
                        vd = ' ' + t('fer_venda_lbl') if f0.get('venda_ferias') else ''
                        _ln(f"       [FUTURO] {func['nome']}{v}: {f0['inicio']} até {f0['fim']}{vd}")
                    elif pas:
                        _ln(f"       [CONCLUÍDO] {func['nome']}{v}: último {pas[-1]['inicio']} até {pas[-1]['fim']}")
                    else:
                        _ln(f"       {func['nome']}{v}: {t('sem_ferias')}")
    paginar(d, t('fer_cal_titulo'), blocos, render_cal)

# ---------------------------------------------------------------------------
# Relatórios
# ---------------------------------------------------------------------------

def menu_relatorios(d):
    while True:
        _render_menu(t('rel_titulo'), [(1, t('rel_pa_menu')), (2, t('rel_saldo')), (3, t('rel_individual')), (4, t('rel_multi')), (5, t('rel_periodo')), (6, t('rel_geral')), (7, t('rel_setor')), (8, t('rel_sub')), (9, t('rel_situacao')), (10, t('rel_vencidas')), (11, t('rel_ano'))], rodape=[(0, t('voltar'))])
        op = inp(t('opcao')).strip()
        if op == '1':
            rel_por_periodo_aquisitivo(d)
        elif op == '2':
            rel_saldo_dias(d)
        elif op == '3':
            rel_individual(d)
        elif op == '4':
            rel_multiplos_funcionarios(d)
        elif op == '5':
            rel_periodo(d)
        elif op == '6':
            rel_geral(d)
        elif op == '7':
            rel_setor(d)
        elif op == '8':
            rel_sub(d)
        elif op == '9':
            rel_situacao(d)
        elif op == '10':
            rel_vencidas(d)
        elif op == '11':
            rel_por_ano_civil(d)
        elif op == '0':
            break
        else:
            flash(t('invalido'), erro=True)

def rel_por_periodo_aquisitivo(d):
    limpar()
    titulo_box(t('rel_pa_titulo'))
    _lvz()
    _ln(f"  {t('rel_pa_filtro')}")
    _dleve()
    _ln(f"  1. {t('rel_pa_todos')}")
    _ln(f"  2. {t('rel_pa_setor')}")
    _ln(f"  3. {t('rel_pa_sub')}")
    _ln(f"  4. {t('rel_pa_func')}")
    _dleve()
    _ln(f"  0. {t('cancelar')}")
    fundo()
    p()
    op = inp(t('opcao')).strip()
    filtro_label = ''
    funcs_base = []
    if op == '0':
        return
    elif op == '1':
        funcs_base = ord_funcs(d)
        filtro_label = t('rel_pa_todos')
    elif op == '2':
        setor = sel_setor(d)
        if not setor:
            return
        funcs_base = ord_funcs(d, [f for f in d['funcionarios'] if f['setor'] == setor])
        filtro_label = f"{t('rel_pa_setor')}: {setor}"
    elif op == '3':
        setor = sel_setor(d)
        if not setor:
            return
        sub = sel_sub(d, setor)
        if not sub:
            return
        funcs_base = ord_funcs(d, [f for f in d['funcionarios'] if f['setor'] == setor and f['subsetor'] == sub])
        filtro_label = f'{setor} → {sub}'
    elif op == '4':
        func = sel_func(d)
        if not func:
            return
        funcs_base = [func]
        filtro_label = func['nome']
    else:
        flash(t('invalido'), erro=True)
        return
    if not funcs_base:
        flash(t('nenhum_func'), erro=True)
        return
    hoje = datetime.today()

    def resumo():
        _lnd(t('rel_data'), hoje.strftime('%d/%m/%Y %H:%M'))
        _lnd(t('rel_pa_filtro')[:-1], filtro_label)
        _lnd(t('rel_total_func'), str(len(funcs_base)))
        n_adm = sum((1 for f in funcs_base if f.get('data_admissao', '')))
        _lnd(t('pa_atual'), f'{n_adm} com data de admissão  |  {len(funcs_base) - n_adm} sem')

    def render_pa(func):
        an = analise_periodo_atual(d, func)
        pas, atu, fut = classificar_ferias(func)
        v = f" [{func.get('vinculo', '')}]" if func.get('vinculo') else ''
        _dleve()
        _ln(f"  {func['nome']}{v}", 'center')
        _dleve()
        _ln(f"  {t('rel_setor_l')}: {func['setor']}  |  {t('rel_sub_l')}: {func['subsetor']}")
        if func.get('data_admissao'):
            _ln(f"  {t('data_admissao')} {func['data_admissao']}")
        _lvz()
        if an['tipo'] == 'aquisitivo':
            ini_s = an['ini'].strftime('%d/%m/%Y')
            fim_s = (an['fim'] - timedelta(days=1)).strftime('%d/%m/%Y')
            _ln(f"  [{t('pa_atual')} #{an['numero']}]  {ini_s} → {fim_s}")
        else:
            _ln(f"  [Ano civil {an['ano_civil']}  {t('pa_sem_admissao')}]")
        if an['max_dias'] and an['max_dias'] > 0:
            bp = _barra_progresso(an['tirados'], an['max_dias'])
            if bp:
                barra, pct = bp
                _ln(f"    {t('pa_tirados')}  : {an['tirados']:>3} / {an['max_dias']} {t('pa_dias')}")
                _ln(f"    {t('pa_restantes')}: {an['restantes']:>3} {t('pa_dias')}")
                _ln(f"    {t('pa_progresso')}: [{barra}] {pct}%")
        else:
            _ln(f"    {t('pa_tirados')}: {an['tirados']} {t('pa_dias')}  ({t('pa_ilimitado')})")
        if an['tipo'] == 'aquisitivo':
            ferias_prd = ferias_no_periodo(func['ferias'], an['ini'], an['fim'])
        else:
            ferias_prd = ferias_no_ano_civil(func['ferias'], an.get('ano_civil', datetime.today().year))
        if ferias_prd:
            _lvz()
            _ln(f'  [Férias no período ({len(ferias_prd)} registro(s))]')
            for f in sorted(ferias_prd, key=lambda x: conv_data(x['inicio']) or datetime.min):
                dias = calc_dias(f['inicio'], f['fim'])
                vd = ' ' + t('fer_venda_lbl') if f.get('venda_ferias') else ''
                ini = conv_data(f['inicio'])
                if ini and ini <= hoje <= conv_data(f['fim']):
                    cat = f"[{t('rel_andamento')}]"
                elif ini and ini > hoje:
                    cat = f"[{t('rel_futuro')}]"
                else:
                    cat = f"[{t('rel_concluido')}]"
                _ln(f"    {cat} {f['inicio']} até {f['fim']}  ({dias} {t('pa_dias')}){vd}")
        elif not func['ferias']:
            _lvz()
            _ln('    ' + t('sem_ferias'))
        else:
            _lvz()
            _ln(f'    (sem férias no período aquisitivo atual)')
        if fut:
            fut_fora = [f for f in fut if an['tipo'] != 'aquisitivo' or conv_data(f['inicio']) >= an['fim']]
            if fut_fora:
                _lvz()
                _ln(f"  [{t('periodos_futuros')} fora do prd. atual: {len(fut_fora)}]")
                for f in fut_fora[:3]:
                    dias = calc_dias(f['inicio'], f['fim'])
                    _ln(f"    • {f['inicio']} até {f['fim']}  ({dias} {t('pa_dias')})")
        _lvz()
    paginar(d, f"{t('rel_pa_titulo')}  |  {filtro_label}", funcs_base, render_pa, resumo)

def rel_saldo_dias(d):
    limpar()
    titulo_box(t('rel_saldo_titulo'))
    _lvz()
    _ln('  Filtrar por:')
    _dleve()
    _ln(f"  1. {t('rel_saldo_todos')}")
    _ln(f"  2. {t('rel_saldo_setor')}")
    _ln(f"  3. {t('rel_saldo_sub')}")
    _dleve()
    _ln(f"  0. {t('cancelar')}")
    fundo()
    p()
    op = inp(t('opcao')).strip()
    filtro_label = ''
    funcs_base = []
    if op == '0':
        return
    elif op == '1':
        funcs_base = ord_funcs(d)
        filtro_label = t('rel_saldo_todos')
    elif op == '2':
        setor = sel_setor(d)
        if not setor:
            return
        funcs_base = ord_funcs(d, [f for f in d['funcionarios'] if f['setor'] == setor])
        filtro_label = f'Setor: {setor}'
    elif op == '3':
        setor = sel_setor(d)
        if not setor:
            return
        sub = sel_sub(d, setor)
        if not sub:
            return
        funcs_base = ord_funcs(d, [f for f in d['funcionarios'] if f['setor'] == setor and f['subsetor'] == sub])
        filtro_label = f'{setor} → {sub}'
    else:
        flash(t('invalido'), erro=True)
        return
    if not funcs_base:
        flash(t('nenhum_func'), erro=True)
        return
    registros = []
    for func in funcs_base:
        an = analise_periodo_atual(d, func)
        tirados = an['tirados']
        max_d = an['max_dias']
        restantes = an['restantes']
        excedido = max_d and max_d > 0 and (tirados > max_d)
        registros.append({'func': func, 'an': an, 'tirados': tirados, 'max_d': max_d, 'restantes': restantes, 'excedido': excedido})

    def _sk(r):
        if r['excedido']:
            return (0, r['tirados'])
        if r['restantes'] is not None:
            return (1, r['restantes'])
        return (2, 0)
    registros.sort(key=_sk)
    n_exc = sum((1 for r in registros if r['excedido']))
    n_ok = sum((1 for r in registros if not r['excedido'] and r['restantes'] is not None))
    tot = sum((r['tirados'] for r in registros))

    def resumo():
        _lnd(t('rel_data'), datetime.today().strftime('%d/%m/%Y %H:%M'))
        _lnd('Filtro', filtro_label)
        _lnd(t('rel_saldo_tot_func'), str(len(registros)))
        _lnd(t('rel_saldo_excedidos'), str(n_exc) + ' funcionário(s)')
        _lnd(t('rel_saldo_sem_saldo'), str(n_ok) + ' funcionário(s)')
        _lnd(t('rel_saldo_total_dias'), f"{tot} {t('pa_dias')}")

    def render_saldo(reg):
        func = reg['func']
        an = reg['an']
        tirados = reg['tirados']
        max_d = reg['max_d']
        restantes = reg['restantes']
        excedido = reg['excedido']
        v = f" [{func.get('vinculo', '')}]" if func.get('vinculo') else ''
        if excedido:
            icone = '[✗]'
        elif restantes is not None and restantes == 0:
            icone = '[=]'
        elif restantes is not None and restantes <= 5:
            icone = '[!]'
        else:
            icone = '[✓]'
        _lvz()
        _ln(f"  {icone} {func['nome']}{v}")
        _ln(f"       {func['setor']}  →  {func['subsetor']}")
        if an['tipo'] == 'aquisitivo':
            ini_s = an['ini'].strftime('%d/%m/%Y')
            fim_s = (an['fim'] - timedelta(days=1)).strftime('%d/%m/%Y')
            _ln(f"       Prd.{an['numero']}: {ini_s} → {fim_s}")
        else:
            _ln(f"       Ano civil {an['ano_civil']}  ({t('rel_saldo_usando')})")
        if max_d and max_d > 0:
            saldo_str = f'-{tirados - max_d}' if excedido else str(restantes)
            status_str = t('rel_saldo_neg') if excedido else t('rel_saldo_ok')
            bp = _barra_progresso(tirados, max_d, 20)
            if bp:
                barra, pct = bp
                _ln(f'       Tirados: {tirados:>3}  |  Limite: {max_d}  |  Saldo: {saldo_str}  |  {status_str}')
                _ln(f'       [{barra}] {pct}%')
        else:
            _ln(f"       Tirados: {tirados}  |  Limite: {t('rel_saldo_sem_lim')}")
    paginar(d, f"{t('rel_saldo_titulo')}  |  {filtro_label}", registros, render_saldo, resumo)

def rel_individual(d):
    if not d['funcionarios']:
        flash(t('nenhum_func'), erro=True)
        return
    limpar()
    titulo_box(t('rel_individual_t'))
    _lvz()
    fundo()
    func = sel_func(d)
    if not func:
        return
    an = analise_periodo_atual(d, func)
    tot, _, __ = _status_ferias(func)
    per = calc_periodos_aquisitivos(func)

    def resumo():
        _lnd(t('rel_data'), datetime.today().strftime('%d/%m/%Y %H:%M'))
        _lnd(t('rel_nome'), func['nome'])
        _lnd(t('rel_vinculo'), func.get('vinculo', '—') or '—')
        _lnd(t('rel_setor_l'), func['setor'])
        _lnd(t('rel_sub_l'), func['subsetor'])
        if func.get('data_admissao'):
            _lnd(t('data_admissao'), func['data_admissao'])
        _lnd(t('rel_periodos'), str(len(func['ferias'])))
        _lnd(t('rel_tot_dias'), f"{tot} {t('pa_dias')} (histórico total)")
        if an['tipo'] == 'aquisitivo':
            ini_s = an['ini'].strftime('%d/%m/%Y')
            fim_s = (an['fim'] - timedelta(days=1)).strftime('%d/%m/%Y')
            _lnd(t('pa_atual') + f" #{an['numero']}", f'{ini_s} → {fim_s}')
            if an['max_dias'] and an['max_dias'] > 0:
                bp = _barra_progresso(an['tirados'], an['max_dias'])
                if bp:
                    barra, pct = bp
                    _lnd(t('pa_tirados'), f"{an['tirados']}/{an['max_dias']} {t('pa_dias')}  [{barra}] {pct}%  Restam: {an['restantes']}")
            else:
                _lnd(t('pa_tirados'), f"{an['tirados']} {t('pa_dias')}  ({t('pa_ilimitado')})")
        else:
            _lnd(f"Ano civil {an['ano_civil']}", f"{an['tirados']} {t('pa_dias')}  {t('pa_sem_admissao')}")
    itens = []
    for pp in per:
        itens.append({'tipo': 'aq', 'pp': pp})
    hoje = datetime.today()
    for i, f in enumerate(ord_ferias(d, list(func['ferias'])), 1):
        itens.append({'tipo': 'fer', 'f': f, 'idx': i})
    if not itens:
        limpar()
        titulo_box(f"{t('rel_individual_t')}: {func['nome']}")
        for item in _capturar(resumo):
            _print_buf(item)
        _dleve()
        _lvz()
        _ln('  ' + t('sem_ferias'), 'center')
        _lvz()
        fundo()
        pausar()
        return

    def render_item(item):
        if item['tipo'] == 'aq':
            pp = item['pp']
            s_txt = {'ok': t('ferias_em_dia'), 'vencida': t('ferias_vencidas'), 'a_vencer': t('ferias_a_vencer'), 'pendente': t('ferias_pendentes')}.get(pp['status'], pp['status'])
            fim_s = (pp['fim_aq'] - timedelta(days=1)).strftime('%d/%m/%Y')
            _lvz()
            _ln(f"  [Prd.Aquisitivo] {pp['ini_aq'].strftime('%d/%m/%Y')} – {fim_s}")
            _ln(f"    Concessivo até: {pp['fim_con'].strftime('%d/%m/%Y')}  |  Status: {s_txt}")
            _ln(f"    Dias tirados no período: {pp['dias_tirados']}")
            if pp['status'] == 'a_vencer':
                _ln(f"    ⚠ Vence em {(pp['fim_con'] - hoje).days} {t('dias_para_vencer')}")
            elif pp['status'] == 'vencida':
                _ln(f"    ✗ {t('vencida_em')}: {pp['fim_con'].strftime('%d/%m/%Y')}")
        else:
            f = item['f']
            dias = calc_dias(f['inicio'], f['fim'])
            ini = conv_data(f['inicio'])
            fim = conv_data(f['fim'])
            if ini and ini <= hoje <= fim:
                est = t('rel_andamento')
            elif ini and ini > hoje:
                est = t('rel_futuro')
            else:
                est = t('rel_concluido')
            vd = ' ' + t('fer_venda_lbl') if f.get('venda_ferias') else ''
            _lvz()
            _ln(f"  {t('rel_periodos')} {item['idx']}:  [{est}]")
            _ln(f"    {t('rel_inicio')}: {f['inicio']}  |  {t('rel_termino')}: {f['fim']}")
            _ln(f"    {t('rel_dias')}: {dias} {t('pa_dias')}{vd}")
    paginar(d, f"{t('rel_individual_t')}: {func['nome']}", itens, render_item, resumo)

def _tela_selecao_funcionarios(d):
    selecionados = []
    while True:
        limpar()
        titulo_box(t('rel_multi_titulo'))
        _lvz()
        _ln(f"  {t('rel_multi_lista')}  ({len(selecionados)} {t('rel_selecionados')})")
        _dleve()
        if not selecionados:
            _ln(f"  — {t('rel_multi_vazio')} —", 'center')
        else:
            for i, func in enumerate(selecionados, 1):
                v = f" [{func.get('vinculo', '')}]" if func.get('vinculo') else ''
                _ln(f"  {i}. {func['nome']}{v}  ({func['setor']} → {func['subsetor']})")
                _ln(_linha_periodo_atual(func, d))
        _lvz()
        _dleve()
        _ln(f"  {t('rel_multi_gerenciar')}")
        fundo()
        msg, erro = _get_flash()
        if msg:
            p(('  ✗ ' if erro else '  ✓ ') + msg)
        p()
        cmd = inp(t('opcao')).strip().lower()
        if cmd == 'a':
            todos = ord_funcs(d)
            ids_sel = {f.get('_id') for f in selecionados}
            limpar()
            titulo_box(t('rel_multi_titulo'))
            _lvz()
            for i, func in enumerate(todos, 1):
                v = f" [{func.get('vinculo', '')}]" if func.get('vinculo') else ''
                mrk = ' ✓' if func.get('_id') in ids_sel else ''
                _ln(f"  {i}. {func['nome']}{v}  ({func['setor']} → {func['subsetor']}){mrk}")
            _lvz()
            _dleve()
            _ln(f"  0. {t('voltar')}  |  * = selecionar todos")
            fundo()
            p()
            entrada = inp(t('opcao')).strip().lower()
            if entrada == '0':
                continue
            elif entrada == '*':
                ads = 0
                for func in todos:
                    if func.get('_id') not in ids_sel:
                        selecionados.append(func)
                        ads += 1
                flash(f'{ads} adicionado(s).')
            else:
                try:
                    nums = [int(x.strip()) for x in entrada.replace(',', ' ').split() if x.strip()]
                    ads = 0
                    for num in nums:
                        if 1 <= num <= len(todos):
                            func = todos[num - 1]
                            if func.get('_id') in {f.get('_id') for f in selecionados}:
                                flash(t('rel_multi_dup'), erro=True)
                            else:
                                selecionados.append(func)
                                ads += 1
                        else:
                            flash(t('fora_intervalo'), erro=True)
                    if ads:
                        flash(f'{ads} adicionado(s).')
                except ValueError:
                    flash(t('so_numero'), erro=True)
        elif cmd == 'r':
            if not selecionados:
                flash(t('rel_multi_vazio'), erro=True)
                continue
            limpar()
            titulo_box(t('rel_multi_titulo'))
            _lvz()
            for i, func in enumerate(selecionados, 1):
                v = f" [{func.get('vinculo', '')}]" if func.get('vinculo') else ''
                _ln(f"  {i}. {func['nome']}{v}")
            _lvz()
            _dleve()
            _ln(f"  0. {t('cancelar')}  |  * = limpar tudo")
            fundo()
            p()
            entrada = inp(t('opcao')).strip().lower()
            if entrada == '0':
                continue
            elif entrada == '*':
                selecionados.clear()
                flash('Seleção limpa.')
            else:
                try:
                    nums = sorted(set((int(x.strip()) for x in entrada.replace(',', ' ').split() if x.strip())), reverse=True)
                    rm = 0
                    for num in nums:
                        if 1 <= num <= len(selecionados):
                            selecionados.pop(num - 1)
                            rm += 1
                    flash(f'{rm} removido(s).')
                except ValueError:
                    flash(t('so_numero'), erro=True)
        elif cmd == 'g':
            if not selecionados:
                flash(t('rel_multi_vazio'), erro=True)
                continue
            return selecionados
        elif cmd in ('0', ''):
            return []
        else:
            flash(t('invalido'), erro=True)

def rel_multiplos_funcionarios(d):
    if not d['funcionarios']:
        flash(t('nenhum_func'), erro=True)
        return
    selecionados = _tela_selecao_funcionarios(d)
    if not selecionados:
        flash(t('rel_multi_vazio'))
        return
    n = len(selecionados)
    n_venc = sum((1 for f in selecionados if situacao_geral_func(f) == 'vencida'))
    n_atu = sum((1 for f in selecionados if classificar_ferias(f)[1]))
    n_fut = sum((1 for f in selecionados if classificar_ferias(f)[2]))
    tot = sum((analise_periodo_atual(d, f)['tirados'] for f in selecionados))

    def resumo():
        _lnd(t('rel_data'), datetime.today().strftime('%d/%m/%Y %H:%M'))
        _lnd(t('rel_total_func'), str(n))
        _lnd(t('pa_tirados') + ' (prd.atual total)', f"{tot} {t('pa_dias')}")
        _lnd(t('rel_andamento'), str(n_atu) + ' em férias agora')
        _lnd(t('periodos_futuros'), str(n_fut) + ' com férias agendadas')
        if n_venc:
            _lnd(t('ferias_vencidas'), str(n_venc) + ' funcionário(s) com férias vencidas')
    paginar(d, f"{t('rel_multi_titulo')}  ({n} {t('rel_selecionados')})", selecionados, lambda func: _render_func_individual(func, d), resumo)

def rel_geral(d):
    setores_ord = ord_setores(d)
    tf = len(d['funcionarios'])
    tc = sum((1 for f in d['funcionarios'] if f['ferias']))

    def resumo():
        _lnd(t('rel_data'), datetime.today().strftime('%d/%m/%Y %H:%M'))
        _lnd(t('rel_set_cad'), str(len(setores_ord)))
        _lnd(t('rel_subs'), str(sum((len(v['subsetores']) for v in d['setores'].values()))))
        _lnd(t('rel_total_func'), str(tf))
        _lnd(t('rel_com_ferias'), str(tc))
        _lnd(t('rel_sem_ferias'), str(tf - tc))

    def render_s(setor):
        fs = ord_funcs(d, [f for f in d['funcionarios'] if f['setor'] == setor])
        _lvz()
        _ln(f'  ══  {setor}  ══')
        _ln(f"  Func: {len(fs)}  |  Dias: {sum((_status_ferias(f)[0] for f in fs))} {t('pa_dias')} (histórico)")
        for sub in ord_subs(d, setor):
            fsub = ord_funcs(d, [f for f in fs if f['subsetor'] == sub])
            _lvz()
            _ln(f'  +── {sub}  ({len(fsub)} func.)')
            _dleve()
            if not fsub:
                _ln('      ' + t('sem_func'))
            else:
                for func in fsub:
                    _render_func_individual(func, d)
    paginar(d, t('rel_geral'), setores_ord, render_s, resumo)

def rel_setor(d):
    limpar()
    titulo_box(t('rel_setor'))
    _lvz()
    fundo()
    setor = sel_setor(d)
    if not setor:
        return
    fs = ord_funcs(d, [f for f in d['funcionarios'] if f['setor'] == setor])
    info = d['setores'][setor]

    def resumo():
        _lnd(t('rel_data'), datetime.today().strftime('%d/%m/%Y %H:%M'))
        _lnd(t('rel_setor_l'), setor)
        _lnd(t('rel_subs'), str(len(info['subsetores'])))
        _lnd(t('rel_total_func'), str(len(fs)))
        _lnd(t('rel_tot_dias'), str(sum((_status_ferias(f)[0] for f in fs))) + ' ' + t('pa_dias') + ' (histórico)')

    def render_sub(sub):
        fsub = ord_funcs(d, [f for f in fs if f['subsetor'] == sub])
        _lvz()
        _ln(f'  +── {sub}  ({len(fsub)} func.)')
        _dleve()
        if not fsub:
            _ln('      ' + t('sem_func'))
        else:
            for func in fsub:
                _render_func_individual(func, d)
    paginar(d, f"{t('rel_setor')}: {setor}", ord_subs(d, setor), render_sub, resumo)

def rel_sub(d):
    limpar()
    titulo_box(t('rel_sub'))
    _lvz()
    fundo()
    setor = sel_setor(d)
    if not setor:
        return
    sub = sel_sub(d, setor)
    if not sub:
        return
    fsub = ord_funcs(d, [f for f in d['funcionarios'] if f['setor'] == setor and f['subsetor'] == sub])
    c = sum((1 for f in fsub if f['ferias']))

    def resumo():
        _lnd(t('rel_data'), datetime.today().strftime('%d/%m/%Y %H:%M'))
        _lnd(t('rel_setor_l'), setor)
        _lnd(t('rel_sub_l'), sub)
        _lnd(t('rel_total_func'), str(len(fsub)))
        _lnd(t('rel_com_ferias'), str(c))
        _lnd(t('rel_sem_ferias'), str(len(fsub) - c))
        _lnd(t('rel_tot_dias'), str(sum((_status_ferias(f)[0] for f in fsub))) + ' ' + t('pa_dias') + ' (histórico)')
    paginar(d, f"{t('rel_sub')}: {sub}", fsub, lambda func: _render_func_individual(func, d), resumo)

def rel_periodo(d):
    limpar()
    titulo_box(t('rel_periodo'))
    _lvz()
    _ln('  ' + t('rel_interv'))
    _lvz()
    fundo()
    p()
    ini_s = inp(t('fer_inicio')).strip()
    fim_s = inp(t('fer_fim')).strip()
    ini = conv_data(ini_s)
    fim = conv_data(fim_s)
    if not ini or not fim:
        flash(t('fer_data_inv'), erro=True)
        return
    if ini > fim:
        flash(t('fer_data_ord'), erro=True)
        return
    resultado = []
    for func in d['funcionarios']:
        pok = [f for f in func['ferias'] if conv_data(f['inicio']) and conv_data(f['fim']) and sobrepoem(ini, fim, conv_data(f['inicio']), conv_data(f['fim']))]
        if pok:
            resultado.append({'func': func, 'periodos': pok})
    if not resultado:
        limpar()
        titulo_box(t('rel_periodo'))
        _lvz()
        _lnd(t('rel_periodo_c'), f'{ini_s}  até  {fim_s}')
        _lnd(t('rel_encontrados'), '0')
        _dleve()
        _lvz()
        _ln('  ' + t('rel_nenhum_p'), 'center')
        _lvz()
        fundo()
        pausar()
        return
    tot_g = sum((calc_dias(f['inicio'], f['fim']) for r in resultado for f in r['periodos']))

    def resumo():
        _lnd(t('rel_data'), datetime.today().strftime('%d/%m/%Y %H:%M'))
        _lnd(t('rel_periodo_c'), f'{ini_s}  até  {fim_s}')
        _lnd(t('rel_encontrados'), str(len(resultado)))
        _lnd(t('rel_tot_per'), f"{tot_g} {t('pa_dias')}")

    def render_r(r):
        func = r['func']
        v = f" [{func.get('vinculo', '')}]" if func.get('vinculo') else ''
        _lvz()
        _ln(f"  › {func['nome']}{v}  ({func['setor']} → {func['subsetor']})")
        for i, f in enumerate(ord_ferias(d, list(r['periodos'])), 1):
            dias = calc_dias(f['inicio'], f['fim'])
            ie = max(ini, conv_data(f['inicio']))
            fe = min(fim, conv_data(f['fim']))
            deff = (fe - ie).days + 1
            vd = ' ' + t('fer_venda_lbl') if f.get('venda_ferias') else ''
            _ln(f"    {i}. {f['inicio']} até {f['fim']}  ({dias} {t('pa_dias')} | {deff} {t('rel_dias_per')}){vd}")
    paginar(d, t('rel_periodo'), resultado, render_r, resumo)

def rel_situacao(d):
    funcs = ord_funcs(d)
    if not funcs:
        limpar()
        titulo_box(t('rel_sit_titulo'))
        _lvz()
        _ln('  ' + t('nenhum_func'), 'center')
        _lvz()
        fundo()
        pausar()
        return
    itens = [{'func': f, 'periodos': calc_periodos_aquisitivos(f), 'status': situacao_geral_func(f), 'an': analise_periodo_atual(d, f)} for f in funcs]
    pri = {'vencida': 4, 'a_vencer': 3, 'pendente': 2, 'sem_admissao': 1, 'ok': 0}
    itens.sort(key=lambda x: pri.get(x['status'], 0), reverse=True)
    n_venc = sum((1 for i in itens if i['status'] == 'vencida'))
    n_atenc = sum((1 for i in itens if i['status'] == 'a_vencer'))
    n_ok = sum((1 for i in itens if i['status'] == 'ok'))

    def resumo():
        _lnd(t('rel_data'), datetime.today().strftime('%d/%m/%Y %H:%M'))
        _lnd(t('rel_total_func'), str(len(itens)))
        _lnd(t('ferias_vencidas'), str(n_venc) + ' func.')
        _lnd(t('ferias_a_vencer'), str(n_atenc) + ' func.')
        _lnd(t('ferias_em_dia'), str(n_ok) + ' func.')

    def render_sit(item):
        func = item['func']
        per = item['periodos']
        an = item['an']
        sit = item['status']
        v = f" [{func.get('vinculo', '')}]" if func.get('vinculo') else ''
        ico = {'vencida': '[!] ', 'a_vencer': '[~] ', 'pendente': '[?] ', 'ok': '[✓] ', 'sem_admissao': '[–] '}.get(sit, '    ')
        _lvz()
        _ln(f"  {ico}{func['nome']}{v}")
        _ln(f"    {func['setor']}  →  {func['subsetor']}")
        _ln(_linha_periodo_atual(func, d))
        for pp in per:
            if pp['status'] == 'vencida':
                fim_s = (pp['fim_aq'] - timedelta(days=1)).strftime('%d/%m/%Y')
                _ln(f"    VENCIDA: {pp['ini_aq'].strftime('%d/%m/%Y')} – {fim_s}  ({t('vencida_em')}: {pp['fim_con'].strftime('%d/%m/%Y')})")
            elif pp['status'] == 'a_vencer':
                dr = (pp['fim_con'] - datetime.today()).days
                _ln(f"    {t('ferias_a_vencer')}: vence em {pp['fim_con'].strftime('%d/%m/%Y')}  ({dr} {t('dias_para_vencer')})")
    paginar(d, t('rel_sit_titulo'), itens, render_sit, resumo)

def rel_vencidas(d):
    itens = []
    for func in ord_funcs(d):
        if not func.get('data_admissao', ''):
            continue
        vencidas = [pp for pp in calc_periodos_aquisitivos(func) if pp['status'] == 'vencida']
        if vencidas:
            itens.append({'func': func, 'vencidas': vencidas})
    titulo = t('func_vencidas')
    if not itens:
        limpar()
        titulo_box(titulo)
        _lvz()
        _ln('  ' + t('nenhum_vencido'), 'center')
        _lvz()
        fundo()
        pausar()
        return
    n_sem = sum((1 for f in d['funcionarios'] if not f.get('data_admissao', '')))

    def resumo():
        _lnd(t('rel_data'), datetime.today().strftime('%d/%m/%Y %H:%M'))
        _lnd(t('func_vencidas'), str(len(itens)) + ' funcionário(s)')
        if n_sem:
            _lnd(t('sem_admissao'), str(n_sem) + ' sem data de admissão')

    def render_v(item):
        func = item['func']
        v = f" [{func.get('vinculo', '')}]" if func.get('vinculo') else ''
        _lvz()
        _ln(f"  [!] {func['nome']}{v}")
        _ln(f"    {func['setor']}  →  {func['subsetor']}")
        _ln(f"    {t('data_admissao')} {func.get('data_admissao', '—') or '—'}")
        for pp in item['vencidas']:
            fim_s = (pp['fim_aq'] - timedelta(days=1)).strftime('%d/%m/%Y')
            _ln(f"    VENCIDA: {pp['ini_aq'].strftime('%d/%m/%Y')} – {fim_s}")
            _ln(f"    {t('vencida_em')}: {pp['fim_con'].strftime('%d/%m/%Y')}")
    paginar(d, titulo, itens, render_v, resumo)

def _pedir_ano():
    ano_atual = datetime.today().year
    while True:
        _lvz()
        _ln(f"  {t('rel_ano_pedir')}")
        _ln(f"  (0 = {t('cancelar')})")
        _lvz()
        fundo()
        p()
        entrada = inp(f'Ano ({ano_atual}):').strip()
        if not entrada:
            return ano_atual
        if entrada == '0':
            return None
        try:
            ano = int(entrada)
            if 2000 <= ano <= ano_atual + 10:
                return ano
            flash(t('rel_ano_inv', max=ano_atual + 10), erro=True)
        except ValueError:
            flash(t('so_numero'), erro=True)
        limpar()
        titulo_box(t('rel_ano_titulo'))

def rel_por_ano_civil(d):
    limpar()
    titulo_box(t('rel_ano_titulo'))
    ano = _pedir_ano()
    if ano is None:
        return
    limpar()
    titulo_box(f"{t('rel_ano_titulo')} — {ano}")
    _lvz()
    _ln('  Filtrar por:')
    _dleve()
    _ln(f"  1. {t('rel_ano_todos')}")
    _ln(f"  2. {t('rel_ano_setor')}")
    _ln(f"  3. {t('rel_ano_sub')}")
    _ln(f"  4. {t('rel_ano_func')}")
    _dleve()
    _ln(f"  0. {t('cancelar')}")
    fundo()
    p()
    op = inp(t('opcao')).strip()
    filtro_label = ''
    funcs_base = []
    if op == '0':
        return
    elif op == '1':
        funcs_base = ord_funcs(d)
        filtro_label = t('rel_ano_todos')
    elif op == '2':
        setor = sel_setor(d)
        if not setor:
            return
        funcs_base = ord_funcs(d, [f for f in d['funcionarios'] if f['setor'] == setor])
        filtro_label = f'Setor: {setor}'
    elif op == '3':
        setor = sel_setor(d)
        if not setor:
            return
        sub = sel_sub(d, setor)
        if not sub:
            return
        funcs_base = ord_funcs(d, [f for f in d['funcionarios'] if f['setor'] == setor and f['subsetor'] == sub])
        filtro_label = f'{setor} → {sub}'
    elif op == '4':
        func = sel_func(d)
        if not func:
            return
        funcs_base = [func]
        filtro_label = func['nome']
    else:
        flash(t('invalido'), erro=True)
        return
    itens = [f for f in funcs_base if ferias_no_ano_civil(f['ferias'], ano)]
    if not itens:
        limpar()
        titulo_box(f"{t('rel_ano_titulo')} — {ano}")
        _lvz()
        _ln('  ' + t('rel_ano_vazio', ano=ano), 'center')
        _lvz()
        fundo()
        pausar()
        return
    tot_dias = sum((sum((dias_no_ano_civil(f, ano) for f in ferias_no_ano_civil(func['ferias'], ano))) for func in itens))
    hoje = datetime.today()

    def resumo():
        _lnd(t('rel_data'), hoje.strftime('%d/%m/%Y %H:%M'))
        _lnd('Ano civil', f'{ano}  (use opção 1 para análise por prd.aquisitivo)')
        _lnd('Filtro', filtro_label)
        _lnd(t('rel_encontrados'), str(len(itens)))
        _lnd(t('rel_ano_total'), f"{tot_dias} {t('pa_dias')}")

    def render_ano(func):
        ferias_ano = ferias_no_ano_civil(func['ferias'], ano)
        total_dias = sum((dias_no_ano_civil(f, ano) for f in ferias_ano))
        max_d = obter_regra(d, 'max_dias_ano', func['setor'], func['subsetor'], func.get('vinculo', ''))
        v = f" [{func.get('vinculo', '')}]" if func.get('vinculo') else ''
        _lvz()
        _ln(f"  › {func['nome']}{v}")
        _ln(f"    {func['setor']}  →  {func['subsetor']}")
        if func.get('data_admissao'):
            _ln(f"    {t('data_admissao')} {func['data_admissao']}  {t('pa_sem_admissao')}")
        if max_d and max_d > 0:
            bp = _barra_progresso(total_dias, max_d)
            if bp:
                barra, pct = bp
                _ln(f"    {total_dias}/{max_d} {t('pa_dias')}  [{barra}] {pct}%  Restam: {max(0, max_d - total_dias)}")
        else:
            _ln(f"    {total_dias} {t('pa_dias')}  ({t('pa_ilimitado')})")
        for f in sorted(ferias_ano, key=lambda x: conv_data(x['inicio']) or datetime.min):
            dias = calc_dias(f['inicio'], f['fim'])
            dias_ef = dias_no_ano_civil(f, ano)
            vd = ' ' + t('fer_venda_lbl') if f.get('venda_ferias') else ''
            cruzou = f" {t('rel_ano_cruzou')}" if conv_data(f['inicio']) and conv_data(f['fim']) and (conv_data(f['inicio']).year != conv_data(f['fim']).year) else ''
            ini = conv_data(f['inicio'])
            cat = f"[{t('rel_andamento')}]" if ini and ini <= hoje <= conv_data(f['fim']) else f"[{t('rel_futuro')}]" if ini and ini > hoje else f"[{t('rel_concluido')}]"
            _ln(f"      {cat} {f['inicio']} até {f['fim']}{cruzou}")
            if dias_ef != dias:
                _ln(f"           {dias_ef} {t('pa_dias')} em {ano}  |  {dias} {t('pa_dias')} total{vd}")
            else:
                _ln(f"           {dias_ef} {t('pa_dias')}{vd}")
    paginar(d, f"{t('rel_ano_titulo')} — {ano}  |  {filtro_label}", itens, render_ano, resumo)

# ---------------------------------------------------------------------------
# Regras e validação
# ---------------------------------------------------------------------------

def _editar_bloco(bloco, titulo_tela, parent=None):
    CR = _campos_regras()
    campos = list(CR.keys())
    while True:
        limpar()
        titulo_box(titulo_tela)
        if parent is not None:
            _ln(t('reg_herdar_nota'))
        _lvz()
        l = _larg()
        util = l - 4
        ml = max(10, util - 18)
        for i, campo in enumerate(campos, 1):
            meta = CR[campo]
            atual = bloco.get(campo)
            if parent is not None and atual is None:
                vr = parent.get(campo, meta['padrao'])
                sv = f"{t('reg_herdado')} ({fmt_val(meta['tipo'], vr)})"
            else:
                val = atual if atual is not None else meta['padrao']
                sv = fmt_val(meta['tipo'], val)
            lbl = meta['label']
            lbl = lbl[:ml - 2] + '..' if len(lbl) > ml else lbl
            _ln(f'  {i}. {lbl.ljust(ml)}: {sv}')
        _lvz()
        _dleve()
        _ln(f"  0. {t('salvar_voltar')}")
        fundo()
        p()
        try:
            op = int(inp(t('opcao')).strip())
        except ValueError:
            flash(t('so_numero'), erro=True)
            continue
        if op == 0:
            break
        if not 1 <= op <= len(campos):
            flash(t('fora_intervalo'), erro=True)
            continue
        campo = campos[op - 1]
        meta = CR[campo]
        atual = bloco.get(campo)
        limpar()
        titulo_box(t('reg_editar'))
        _lvz()
        _ln(f"  {t('reg_campo')}: {meta['label']}")
        _ln(f"  {t('reg_dica')}: {meta['dica']}")
        _lvz()
        if meta['tipo'] == 'bool':
            if parent is not None:
                vr = parent.get(campo, meta['padrao'])
                _ln(f"  {t('reg_atual')}: {('Sim' if atual else 'Não' if atual is not None else t('reg_herdado').upper())}")
                _ln(f"  {t('reg_herdar')}: {fmt_bool(vr)} ({t('reg_niv_sup')})")
                _lvz()
                fundo()
                p()
                r = inp(t('reg_s_n_h')).strip().lower()
            else:
                _ln(f"  {t('reg_atual')}: {fmt_bool(atual if atual is not None else meta['padrao'])}")
                _lvz()
                fundo()
                p()
                r = inp(t('reg_s_n_m')).strip().lower()
            if r == t('sim'):
                bloco[campo] = True
            elif r == t('nao'):
                bloco[campo] = False
            elif r == '' and parent is not None:
                bloco.pop(campo, None)
        elif meta['tipo'] == 'int':
            if parent is not None:
                vr = parent.get(campo, meta['padrao'])
                _ln(f"  {t('reg_atual')}: {(atual if atual is not None else t('reg_herdado').upper())}")
                _ln(f"  {t('reg_herdar')}: {vr} ({t('reg_niv_sup')})")
                _lvz()
                fundo()
                p()
                r = inp(t('reg_num_h')).strip()
            else:
                _ln(f"  {t('reg_atual')}: {(atual if atual is not None else meta['padrao'])}")
                _lvz()
                fundo()
                p()
                r = inp(t('reg_num_m')).strip()
            if r == '' and parent is not None:
                bloco.pop(campo, None)
            elif r.isdigit():
                bloco[campo] = int(r)
            elif r:
                flash(t('invalido'), erro=True)

def _parent_subsetor(d, setor):
    base = dict(d['regras']['global'])
    base.update(d['regras'].get('por_setor', {}).get(setor, {}))
    return base

def ver_regras(d):
    CR = _campos_regras()
    todos = []
    todos.append(('sec', t('reg_gl_s')))
    for c, m in CR.items():
        todos.append(('dado', m['label'], fmt_val(m['tipo'], d['regras']['global'].get(c, m['padrao']))))
    pv = {k: b for k, b in d['regras'].get('por_vinculo', {}).items() if b}
    todos.append(('sec', t('reg_vin_s')))
    if not pv:
        todos.append(('info', t('reg_sem_vin')))
    else:
        for vinc, bloco in pv.items():
            todos.append(('sub', f'[ {vinc} ]'))
            [todos.append(('dado', CR[c]['label'], fmt_val(CR[c]['tipo'], v))) for c, v in bloco.items()]
    ps = {k: b for k, b in d['regras'].get('por_setor', {}).items() if b}
    todos.append(('sec', t('reg_set_s')))
    if not ps:
        todos.append(('info', t('reg_sem_set')))
    else:
        for setor, bloco in ps.items():
            todos.append(('sub', f'[ {setor} ]'))
            [todos.append(('dado', CR[c]['label'], fmt_val(CR[c]['tipo'], v))) for c, v in bloco.items()]
    pb = {k: b for k, b in d['regras'].get('por_subsetor', {}).items() if b}
    todos.append(('sec', t('reg_sub_s')))
    if not pb:
        todos.append(('info', t('reg_sem_sub')))
    else:
        for ref, bloco in pb.items():
            partes = ref.split(SEP, 1)
            label = f'{partes[0]} → {partes[1]}' if len(partes) == 2 else ref
            todos.append(('sub', f'[ {label} ]'))
            [todos.append(('dado', CR[c]['label'], fmt_val(CR[c]['tipo'], v))) for c, v in bloco.items()]

    def render_r(item):
        if item[0] == 'sec':
            _lvz()
            _ln(f'  {item[1]}')
        elif item[0] == 'sub':
            _lvz()
            _ln(f'  {item[1]}')
        elif item[0] == 'dado':
            _lnd(item[1], item[2])
        elif item[0] == 'info':
            _ln(f'  {item[1]}')

    def resumo():
        _lnd(t('reg_hier'), '')
    paginar(d, t('reg_ver'), todos, render_r, resumo)

def editar_regras_global(d):
    _editar_bloco(d['regras']['global'], t('reg_global'), parent=None)
    salvar_dados(d)
    flash(t('reg_salvas'))

def editar_regras_vinculo(d):
    if not d['vinculos']:
        flash(t('nenhum_vinculo'), erro=True)
        return
    limpar()
    titulo_box(t('reg_vinculo'))
    _lvz()
    fundo()
    v = sel_vinculo(d, permitir_nenhum=False)
    if not v:
        return
    d['regras']['por_vinculo'].setdefault(v, {})
    _editar_bloco(d['regras']['por_vinculo'][v], f"{t('reg_vinculo')}: {v}", parent=d['regras']['global'])
    salvar_dados(d)
    flash(t('reg_salvas'))

def editar_regras_setor(d):
    if not d['setores']:
        flash(t('nenhum_setor'), erro=True)
        return
    limpar()
    titulo_box(t('reg_setor'))
    _lvz()
    fundo()
    setor = sel_setor(d)
    if not setor:
        return
    d['regras']['por_setor'].setdefault(setor, {})
    _editar_bloco(d['regras']['por_setor'][setor], f"{t('reg_setor')}: {setor}", parent=d['regras']['global'])
    salvar_dados(d)
    flash(t('reg_salvas'))

def editar_regras_subsetor(d):
    if not d['setores']:
        flash(t('nenhum_setor'), erro=True)
        return
    limpar()
    titulo_box(t('reg_subsetor'))
    _lvz()
    _ln('  ' + t('reg_sel_sub'))
    _lvz()
    fundo()
    setor = sel_setor(d)
    if not setor:
        return
    sub = sel_sub(d, setor)
    if not sub:
        return
    chave = _chave_sub(setor, sub)
    d['regras']['por_subsetor'].setdefault(chave, {})
    _editar_bloco(d['regras']['por_subsetor'][chave], f"{t('reg_subsetor')}: {setor} → {sub}", parent=_parent_subsetor(d, setor))
    salvar_dados(d)
    flash(t('reg_salvas'))

def menu_regras(d):
    while True:
        _render_menu(t('reg_titulo'), [(1, t('reg_ver')), (2, t('reg_global')), (3, t('reg_vinculo')), (4, t('reg_setor')), (5, t('reg_subsetor'))], info=[t('reg_hier')], rodape=[(0, t('voltar'))])
        op = inp(t('opcao')).strip()
        if op == '1':
            ver_regras(d)
        elif op == '2':
            editar_regras_global(d)
        elif op == '3':
            editar_regras_vinculo(d)
        elif op == '4':
            editar_regras_setor(d)
        elif op == '5':
            editar_regras_subsetor(d)
        elif op == '0':
            break
        else:
            flash(t('invalido'), erro=True)

def _render_pend(r):
    func = r['func']
    v = f" [{func.get('vinculo', '')}]" if func.get('vinculo') else ''
    _lvz()
    _ln(f"  {func['nome']}{v}")
    _ln(f"  {func['setor']}  →  {func['subsetor']}")
    _lvz()
    for pen in r['pendencias']:
        _ln(f"  {('[P]' if pen['tipo'] == 'periodo' else '[A]')} {pen['ref']}:")
        for i, e in enumerate(pen['erros'], 1):
            _ln(f'      {i}. {e}')

def menu_validacao(d):
    while True:
        n = contar_pends(d)
        info = ['  ' + t('val_ok')] if n == 0 else [f"  {n} {t('val_pend')}"]
        _render_menu(t('val_titulo'), [(1, t('val_ver')), (2, t('val_por_func')), (3, t('val_por_setor')), (4, t('val_revalid'))], info=info, rodape=[(0, t('voltar'))])
        op = inp(t('opcao')).strip()
        if op == '1':
            val_geral(d)
        elif op == '2':
            val_por_func(d)
        elif op == '3':
            val_por_setor(d)
        elif op == '4':
            limpar()
            titulo_box(t('val_revalid_t'))
            _lvz()
            _ln('  ' + t('val_verificando'))
            n = contar_pends(d)
            _lvz()
            if n == 0:
                _ln('  ' + t('val_ok'))
            else:
                _ln(f"  {n} {t('val_pend')} — {t('val_detalhe')}")
            _lvz()
            fundo()
            pausar()
        elif op == '0':
            break
        else:
            flash(t('invalido'), erro=True)

def val_geral(d):
    res = auditar_sistema(d)
    tot = sum((len(r['pendencias']) for r in res))

    def resumo():
        _lnd(t('val_data'), datetime.today().strftime('%d/%m/%Y %H:%M'))
        _lnd(t('val_c_pend'), str(len(res)))
        _lnd(t('val_total'), str(tot))
    if not res:
        limpar()
        titulo_box(t('val_geral_t'))
        for item in _capturar(resumo):
            _print_buf(item)
        _dleve()
        _lvz()
        _ln('  ' + t('val_conform'), 'center')
        _lvz()
        fundo()
        pausar()
        return
    paginar(d, t('val_geral_t'), res, _render_pend, resumo)

def val_por_func(d):
    limpar()
    titulo_box(t('val_func_t'))
    _lvz()
    fundo()
    func = sel_func(d)
    if not func:
        return
    pends = auditar_func(d, func)

    def resumo():
        _lnd(t('val_data'), datetime.today().strftime('%d/%m/%Y %H:%M'))
        _lnd(t('rel_nome'), func['nome'])
        _lnd(t('rel_vinculo'), func.get('vinculo', '—') or '—')
        _lnd(t('rel_setor_l'), f"{func['setor']} → {func['subsetor']}")
        _lnd(t('val_periodos'), str(len(func['ferias'])))
        _lnd(t('val_pendencias'), str(len(pends)))
    if not pends:
        limpar()
        titulo_box(f"{t('val_func_t')}: {func['nome']}")
        for item in _capturar(resumo):
            _print_buf(item)
        _dleve()
        _lvz()
        _ln('  ' + t('val_conform'), 'center')
        _lvz()
        fundo()
        pausar()
        return

    def render_p(pen):
        _lvz()
        _ln(f"  {('[P]' if pen['tipo'] == 'periodo' else '[A]')} {pen['ref']}:")
        for i, e in enumerate(pen['erros'], 1):
            _ln(f'      {i}. {e}')
    paginar(d, f"{t('val_func_t')}: {func['nome']}", pends, render_p, resumo)

def val_por_setor(d):
    limpar()
    titulo_box(t('val_setor_t'))
    _lvz()
    fundo()
    setor = sel_setor(d)
    if not setor:
        return
    fs = [f for f in d['funcionarios'] if f['setor'] == setor]
    res = [{'func': f, 'pendencias': auditar_func(d, f)} for f in fs if f['ferias'] and auditar_func(d, f)]
    tot = sum((len(r['pendencias']) for r in res))

    def resumo():
        _lnd(t('val_data'), datetime.today().strftime('%d/%m/%Y %H:%M'))
        _lnd(t('rel_setor_l'), setor)
        _lnd(t('rel_total_func'), str(len(fs)))
        _lnd(t('val_c_pend2'), str(len(res)))
        _lnd(t('val_total'), str(tot))
    if not res:
        limpar()
        titulo_box(f"{t('val_setor_t')}: {setor}")
        for item in _capturar(resumo):
            _print_buf(item)
        _dleve()
        _lvz()
        _ln('  ' + t('val_conform'), 'center')
        _lvz()
        fundo()
        pausar()
        return
    paginar(d, f"{t('val_setor_t')}: {setor}", res, _render_pend, resumo)

# ---------------------------------------------------------------------------
# Configurações e administração
# ---------------------------------------------------------------------------

def menu_configuracoes(d):
    chaves = list(CONFIG_PADRAO.keys())
    while True:
        CO = _config_opcoes()
        cfg = d.get('config', CONFIG_PADRAO)
        limpar()
        titulo_box(t('cfg_titulo'))
        _lvz()
        _ln('  ' + t('cfg_desc'))
        _lvz()
        _dleve()
        for i, chave in enumerate(chaves, 1):
            meta = CO[chave]
            val = cfg.get(chave, CONFIG_PADRAO[chave])
            desc = meta['opcoes'].get(val, val)
            lbl = meta['label'].ljust(42)
            _ln(f'  {i}. {lbl}: {desc}')
        _lvz()
        msg, erro = _get_flash()
        if msg:
            _dleve()
            _ln(_c_error('  ✗ ' + msg) if erro else _c_success('  ✓ ' + msg))
        _dleve()
        _ln(f"  0. {t('salvar_voltar')}")
        fundo()
        p()
        try:
            op = int(inp(t('opcao')).strip())
        except ValueError:
            flash(t('so_numero'), erro=True)
            continue
        if op == 0:
            salvar_dados(d)
            flash(t('cfg_salvo'))
            return
        if not 1 <= op <= len(chaves):
            flash(t('fora_intervalo'), erro=True)
            continue
        chave = chaves[op - 1]
        meta = CO[chave]
        opts = list(meta['opcoes'].items())
        limpar()
        titulo_box(f"{t('cfg_alterar')} {meta['label'].upper()}")
        _lvz()
        _ln(f"  {t('cfg_atual')} {meta['opcoes'].get(cfg.get(chave, CONFIG_PADRAO[chave]), '—')}")
        _lvz()
        _dleve()
        for j, (val, desc) in enumerate(opts, 1):
            m = ' ' + t('cfg_atual_m') if val == cfg.get(chave, CONFIG_PADRAO[chave]) else ''
            _ln(f'  {j}. {desc}{m}')
        _lvz()
        _dleve()
        _ln(f"  0. {t('cancelar')}")
        fundo()
        p()
        try:
            esc = int(inp(t('cfg_escolha')).strip())
        except ValueError:
            flash(t('so_numero'), erro=True)
            continue
        if esc == 0:
            continue
        if 1 <= esc <= len(opts):
            cfg[chave] = opts[esc - 1][0]
            d['config'] = cfg
            flash(f"'{meta['label']}': {meta['opcoes'][cfg[chave]]}")
        else:
            flash(t('fora_intervalo'), erro=True)

# ---------------------------------------------------------------------------
# Usuários e autenticação
# ---------------------------------------------------------------------------

def _users_db():
    con = _conn()
    rows = con.execute('SELECT id,login,nome,nivel FROM usuarios ORDER BY nivel,login').fetchall()
    con.close()
    return [dict(r) for r in rows]

def menu_usuarios(d):
    while True:
        _render_menu(t('usr_titulo'), [(1, t('usr_listar')), (2, t('usr_criar')), (3, t('usr_senha')), (4, t('usr_excluir'))], rodape=[(0, t('voltar'))])
        op = inp(t('opcao')).strip()
        if op == '1':
            usr_listar(d)
        elif op == '2':
            usr_criar(d)
        elif op == '3':
            usr_senha(d)
        elif op == '4':
            usr_excluir(d)
        elif op == '0':
            break
        else:
            flash(t('invalido'), erro=True)

def usr_listar(d):
    users = _users_db()
    if not users:
        limpar()
        titulo_box(t('usr_titulo'))
        _lvz()
        _ln('  ' + t('usr_nenhum'), 'center')
        _lvz()
        fundo()
        pausar()
        return

    def render_u(u):
        niv = t('nivel_admin') if u['nivel'] == 'admin' else t('nivel_usuario')
        _ln(f"  › [{u['login']}]  {u['nome']}  ({niv})")
    paginar(d, t('usr_titulo'), users, render_u)

def usr_criar(d):
    limpar()
    titulo_box(t('usr_criar'))
    _lvz()
    fundo()
    p()
    login = inp('Login:').strip()
    if not login:
        flash(t('nome_vazio'), erro=True)
        return
    con = _conn()
    ex = con.execute('SELECT id FROM usuarios WHERE login=?', (login,)).fetchone()
    con.close()
    if ex:
        flash(t('usr_ja_existe'), erro=True)
        return
    nome = inp(t('rel_nome') + ':').strip()
    if not nome:
        flash(t('nome_vazio'), erro=True)
        return
    p()
    senha = inp_s(t('usr_nova_senha'))
    conf = inp_s(t('usr_conf_senha'))
    if senha != conf:
        flash(t('usr_senha_dif'), erro=True)
        return
    if not senha:
        flash(t('nome_vazio'), erro=True)
        return
    _lvz()
    _ln(f"  1. {t('nivel_admin')}")
    _ln(f"  2. {t('nivel_usuario')}")
    _lvz()
    fundo()
    p()
    try:
        niv_op = int(inp(t('usr_nivel')).strip())
    except:
        niv_op = 2
    nivel = 'admin' if niv_op == 1 else 'usuario'
    con = _conn()
    con.execute('INSERT INTO usuarios (login,nome,senha_hash,nivel) VALUES (?,?,?,?)', (login, nome, _hash(senha), nivel))
    con.commit()
    con.close()
    flash(f'[{login}] {nome} — ' + t('usr_criado'))

def usr_senha(d):
    limpar()
    titulo_box(t('usr_senha'))
    _lvz()
    fundo()
    p()
    users = _users_db()
    if not users:
        flash(t('usr_nenhum'), erro=True)
        return
    for i, u in enumerate(users, 1):
        p(f"    {i}. [{u['login']}]  {u['nome']}")
    p(f"    0. {t('cancelar')}")
    try:
        e = int(inp(t('opcao')).strip())
    except:
        flash(t('so_numero'), erro=True)
        return
    if e == 0:
        return
    if not 1 <= e <= len(users):
        flash(t('fora_intervalo'), erro=True)
        return
    u = users[e - 1]
    p()
    senha = inp_s(t('usr_nova_senha'))
    conf = inp_s(t('usr_conf_senha'))
    if senha != conf:
        flash(t('usr_senha_dif'), erro=True)
        return
    if not senha:
        flash(t('nome_vazio'), erro=True)
        return
    con = _conn()
    con.execute('UPDATE usuarios SET senha_hash=? WHERE id=?', (_hash(senha), u['id']))
    con.commit()
    con.close()
    flash(f"[{u['login']}] — " + t('usr_senha_ok'))

def usr_excluir(d):
    limpar()
    titulo_box(t('usr_excluir'))
    _lvz()
    fundo()
    p()
    users = _users_db()
    if not users:
        flash(t('usr_nenhum'), erro=True)
        return
    for i, u in enumerate(users, 1):
        p(f"    {i}. [{u['login']}]  {u['nome']}")
    p(f"    0. {t('cancelar')}")
    try:
        e = int(inp(t('opcao')).strip())
    except:
        flash(t('so_numero'), erro=True)
        return
    if e == 0:
        return
    if not 1 <= e <= len(users):
        flash(t('fora_intervalo'), erro=True)
        return
    u = users[e - 1]
    if u['login'] == SESSAO['login']:
        flash(t('usr_proprio'), erro=True)
        return
    admins = [x for x in users if x['nivel'] == 'admin']
    if u['nivel'] == 'admin' and len(admins) == 1:
        flash(t('usr_ultimo_adm'), erro=True)
        return
    c = inp(t('confirmar_excl')).strip().lower()
    if c == t('sim'):
        con = _conn()
        con.execute('DELETE FROM usuarios WHERE id=?', (u['id'],))
        con.commit()
        con.close()
        flash(f"[{u['login']}] — " + t('usr_excluido'))
    else:
        flash(t('excluir_cancel'))

# ---------------------------------------------------------------------------
# Backup e restauração
# ---------------------------------------------------------------------------

def _fazer_backup():
    if not BANCO_DADOS.exists():
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    dst = BACKUP_DIR / f'backup_{ts}.db'
    seq = 1
    while dst.exists():
        dst = BACKUP_DIR / f'backup_{ts}_{seq:02d}.db'
        seq += 1
    tmp = dst.with_name(dst.name + '.tmp')
    origem_con = sqlite3.connect(str(BANCO_DADOS))
    destino_con = sqlite3.connect(str(tmp))
    try:
        origem_con.backup(destino_con)
    finally:
        destino_con.close()
        origem_con.close()
    os.replace(tmp, dst)
    return dst

def _listar_backups():
    if not BACKUP_DIR.exists():
        return []
    return sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith('.db')], reverse=True)

def _fmt_bkp(b):
    try:
        dt = datetime.strptime(b.replace('backup_', '').replace('.db', ''), '%Y%m%d_%H%M%S')
        return dt.strftime('%d/%m/%Y %H:%M:%S')
    except:
        return b

def _exportar_backup():
    """Exporta uma cópia consistente do banco para um caminho escolhido pelo usuário."""
    if not BANCO_DADOS.exists():
        return None, 'Banco de dados não encontrado.'
    destino = inp(t('bkp_exportar_caminho')).strip()
    if not destino:
        return None, t('bkp_exportar_cancel')
    destino = Path(destino).expanduser()
    try:
        # Se o destino já for um diretório, cria um nome automático.
        if destino.exists() and destino.is_dir():
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            destino = destino / f'gerenciador-ferias-backup_{ts}.db'
        elif str(destino).endswith(os.sep):
            destino.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            destino = destino / f'gerenciador-ferias-backup_{ts}.db'
        else:
            destino.parent.mkdir(parents=True, exist_ok=True)

        # SQLite Backup API evita copiar um arquivo em estado inconsistente.
        tmp = destino.with_name(destino.name + '.tmp')
        origem_con = sqlite3.connect(str(BANCO_DADOS))
        destino_con = sqlite3.connect(str(tmp))
        try:
            origem_con.backup(destino_con)
        finally:
            destino_con.close()
            origem_con.close()
        os.replace(tmp, destino)
        return destino, None
    except Exception as exc:
        try:
            if 'tmp' in locals() and tmp.exists():
                tmp.unlink()
        except Exception:
            pass
        return None, str(exc)

def _selecionar_backup(bkps):
    limpar(); titulo_box(t('bkp_restaurar'))
    _ln('Selecione o backup que será restaurado.', 'center'); _dleve()
    for i, nome in enumerate(bkps, 1):
        caminho = BACKUP_DIR / nome
        tamanho = caminho.stat().st_size // 1024 if caminho.exists() else 0
        _ln(f'  {_c_input(str(i).rjust(len(str(len(bkps)))))}  {_c_menu(_fmt_bkp(nome))}  {_c_muted(f"({tamanho} KB)")}')
    _dleve(); _ln(f'  {_c_input("0")}  {_c_menu(t("cancelar"))}')
    fundo()
    try:
        escolha = int(inp(t('opcao')).strip())
    except ValueError:
        flash(t('so_numero'), erro=True); return None
    if escolha == 0: return None
    if not 1 <= escolha <= len(bkps):
        flash(t('fora_intervalo'), erro=True); return None
    return bkps[escolha - 1]


def menu_backup(d):
    while True:
        itens=[(1,t('bkp_fazer')),(2,t('bkp_exportar')),(3,t('bkp_restaurar')),(4,t('bkp_listar'))]
        info=[f"{t('bkp_data_dir')}: {DATA_DIR}", f"Backups internos: {BACKUP_DIR}"]
        _render_menu(t('bkp_titulo'), itens, info=info, rodape=[(0,t('voltar'))])
        op=inp(t('opcao')).strip()
        if op == '1':
            dst=_fazer_backup()
            flash((t('bkp_ok')+' '+dst.name) if dst else 'Banco não encontrado.', erro=not dst)
        elif op == '2':
            limpar(); titulo_box(t('bkp_exportar')); _ln(t('bkp_exportar_caminho'),'center'); fundo()
            dst,err=_exportar_backup()
            flash((t('bkp_exportar_ok')+' '+str(dst)) if dst else (t('bkp_exportar_erro')+' '+str(err)), erro=not dst)
        elif op == '3':
            bkps=_listar_backups()
            if not bkps:
                flash(t('bkp_nenhum'), erro=True); continue
            nome=_selecionar_backup(bkps)
            if not nome: continue
            src=BACKUP_DIR / nome
            limpar(); titulo_box(t('bkp_restaurar'))
            _ln(f'{_fmt_bkp(nome)}', 'center'); _dleve()
            _ln('A restauração substituirá os dados atuais por esta cópia.', 'center')
            _ln('Um backup do estado atual será criado antes da operação.', 'center')
            fundo()
            if inp(t('bkp_confirma')).strip().lower() == t('sim'):
                try:
                    if not _fazer_backup():
                        raise RuntimeError('Não foi possível criar o backup de segurança.')
                    tmp=Path(str(BANCO_DADOS)+'.restore.tmp')
                    origem=sqlite3.connect(str(src)); destino=sqlite3.connect(str(tmp))
                    try: origem.backup(destino)
                    finally: destino.close(); origem.close()
                    os.replace(tmp, BANCO_DADOS)
                    d.clear(); d.update(carregar_dados())
                    flash(t('bkp_rest_ok'))
                except Exception as exc:
                    try:
                        if 'tmp' in locals() and tmp.exists(): tmp.unlink()
                    except Exception: pass
                    flash(f'{t("bkp_exportar_erro")} {exc}', erro=True)
            else:
                flash(t('bkp_cancel'))
        elif op == '4':
            bkps=_listar_backups()
            if not bkps:
                flash(t('bkp_nenhum'), erro=True); continue
            paginar(d,t('bkp_listar'),bkps,lambda b: _ln(f'{_fmt_bkp(b)}  •  {(BACKUP_DIR/b).stat().st_size//1024} KB'))
        elif op == '0': break
        else: flash(t('invalido'), erro=True)

def apagar_dados(d):
    limpar()
    titulo_box(t('apg_titulo'))
    _lvz()
    _ln(t('apg_aviso1'), 'center')
    _ln(t('apg_aviso2'), 'center')
    _lvz()
    _dleve()
    _lvz()
    _ln(f"  {t('apg_instrucao')}")
    _ln(f"  (palavra: {t('apg_palavra')})")
    _lvz()
    fundo()
    p()
    if inp('>>>').strip() == t('apg_palavra'):
        _fazer_backup()
        con = _conn()
        con.executescript('DELETE FROM ferias; DELETE FROM funcionarios; DELETE FROM subsetores; DELETE FROM setores; DELETE FROM vinculos; DELETE FROM regras; DELETE FROM configuracoes;')
        con.commit()
        con.close()
        d.clear()
        d.update(carregar_dados())
        flash(t('apg_ok'))
    else:
        flash(t('apg_cancel'))

def menu_idioma(d):
    while True:
        atual = 'Português (PT-BR)' if get_idioma() == 'pt' else 'English (EN)'
        _render_menu(t('idioma_titulo'), [(1, t('idioma_pt')), (2, t('idioma_en'))], info=[f"{t('idioma_atual')} {atual}"], rodape=[(0, t('voltar'))])
        op = inp(t('opcao')).strip()
        if op == '1':
            set_idioma('pt')
            salvar_dados(d)
            flash(t('idioma_ok') + ' → Português')
            break
        elif op == '2':
            set_idioma('en')
            salvar_dados(d)
            flash(t('idioma_ok') + ' → English')
            break
        elif op == '0':
            break
        else:
            flash(t('invalido'), erro=True)

def menu_administracao(d):
    while True:
        _render_menu(t('adm_titulo'), [(1, t('adm_usuarios')), (2, t('adm_backup')), (3, t('adm_apagar')), (4, t('adm_idioma'))], rodape=[(0, t('voltar'))])
        op = inp(t('opcao')).strip()
        if op == '1':
            menu_usuarios(d)
        elif op == '2':
            menu_backup(d)
        elif op == '3':
            apagar_dados(d)
        elif op == '4':
            menu_idioma(d)
        elif op == '0':
            break
        else:
            flash(t('invalido'), erro=True)

def _usuarios_existentes():
    con = _conn()
    try:
        return con.execute('SELECT COUNT(*) AS c FROM usuarios').fetchone()['c'] > 0
    finally:
        con.close()

def _configurar_admin_inicial():
    """Create the first administrator without shipping a default password."""
    limpar()
    titulo_box('CONFIGURAÇÃO INICIAL')
    _lvz()
    _ln('Nenhum usuário foi cadastrado. Crie o administrador inicial.', 'center')
    _lvz()
    fundo()
    p()
    login = inp('Login do administrador:').strip()
    nome = inp('Nome do administrador:').strip()
    senha = inp_s('Senha:')
    confirmacao = inp_s('Confirme a senha:')
    if not login or not nome or (not senha):
        flash('Todos os campos são obrigatórios.', erro=True)
        return False
    if senha != confirmacao:
        flash(t('usr_senha_dif'), erro=True)
        return False
    con = _conn()
    try:
        con.execute('INSERT INTO usuarios (login,nome,senha_hash,nivel) VALUES (?,?,?,?)', (login, nome, _hash(senha), 'admin'))
        con.commit()
    except sqlite3.IntegrityError:
        flash(t('usr_ja_existe'), erro=True)
        return False
    finally:
        con.close()
    flash(t('usr_criado'))
    return True

# ---------------------------------------------------------------------------
# Inicialização, login e menu principal
# ---------------------------------------------------------------------------

def tela_login():
    _migrar_banco_legado()
    _init_banco()
    if not _usuarios_existentes():
        if not _configurar_admin_inicial():
            return False
    for tentativa in range(1, 4):
        limpar()
        titulo_box(t('login_titulo'))
        _lvz()
        _ln(t('menu_titulo'), 'center')
        _lvz()
        if tentativa > 1:
            _ln(f'  ⚠  Tentativa {tentativa}/3', 'center')
            _lvz()
        fundo()
        p()
        login = inp(t('login_usuario')).strip()
        senha = inp_s(t('login_senha'))
        con = _conn()
        row = con.execute('SELECT login,nome,senha_hash,nivel FROM usuarios WHERE login=?', (login,)).fetchone()
        con.close()
        if row and _verify_password(senha, row['senha_hash']):
            if not row['senha_hash'].startswith('pbkdf2_sha256$'):
                con = _conn()
                con.execute('UPDATE usuarios SET senha_hash=? WHERE login=?', (_hash(senha), row['login']))
                con.commit()
                con.close()
            SESSAO['login'] = row['login']
            SESSAO['nome'] = row['nome']
            SESSAO['nivel'] = row['nivel']
            return True
        flash(t('login_erro'), erro=True)
        if tentativa < 3:
            limpar()
            titulo_box(t('login_titulo'))
            _lvz()
            _ln('  ' + t('login_erro'), 'center')
            _lvz()
            fundo()
            pausar()
    limpar()
    titulo_box(t('login_titulo'))
    _lvz()
    _ln('  ' + t('login_bloq'), 'center')
    _lvz()
    fundo()
    time.sleep(2)
    return False

def _render_menu_principal(titulo, itens, rodape, info_topo, painel_linhas):
    """Tela inicial compacta: menu, status e agenda em blocos distintos."""
    limpar(); topo(); _ln(_c_title(str(titulo).upper()), 'center'); _div()
    _ln(_c_muted(t('ui_menu_principal')), 'center'); _dleve()
    for numero, label in _menu_rows(itens):
        if numero is not None:
            _ln(f'  {_c_input(numero)}  {_c_menu(label)}')
    if info_topo:
        _dleve(); _ln(_c_muted(t('ui_status')), 'center'); _dleve()
        for info in info_topo:
            _ln(f'  {info}')
    if painel_linhas:
        _dleve(); _ln(_c_muted(t('ui_agenda')), 'center'); _dleve()
        for linha in painel_linhas:
            _ln(f'  {linha}')
    if rodape:
        _dleve()
        for numero, label in _menu_rows(rodape):
            if numero is not None:
                _ln(f'  {_c_input(numero)}  {_c_menu(label)}')
    msg, erro = _get_flash()
    if msg:
        _dleve(); _ln(_c_error('✗ '+msg) if erro else _c_success('✓ '+msg))
    fundo()


def menu_principal():
    """Executa o fluxo principal após a autenticação."""
    if not tela_login():
        return
    d = carregar_dados()
    eh_admin = SESSAO['nivel'] == 'admin'
    while True:
        n = contar_pends(d)
        cfg = d.get('config', CONFIG_PADRAO)
        CO = _config_opcoes()
        niv = t('nivel_admin') if eh_admin else t('nivel_usuario')
        ord_label = CO['ordem_funcionarios']['opcoes'].get(cfg.get('ordem_funcionarios', 'nome'), '—')
        dir_label = _dir_curto(cfg)
        em_ferias_n, em_30dias_n = _calcular_painel(d)
        # Menus agrupados: menos opções na tela e menor deslocamento visual.
        itens = [
            (1, t('m_cadastros')),
            (2, t('m_ferias')),
            (3, t('m_banco_horas')),
            (4, t('m_relat')),
            (5, t('m_painel')),
            (6, t('m_grafico')),
            (7, t('m_regras')),
            (8, t('m_valid')),
        ]
        if eh_admin:
            itens += [(9, t('m_config')), (10, t('m_admin'))]
        status = t('status_pend', n=n) if n > 0 else t('status_ok')
        n_venc = _contar_vencidas(d)
        info_topo = [
            f"{t('logado')} {SESSAO['nome']} ({niv})",
            status,
            f"{t('exibicao')} {ord_label} | {dir_label}",
        ]
        if n_venc > 0:
            info_topo.append(t('ferias_venc_alerta', n=n_venc))
        painel_linhas = _linhas_painel_menu(em_ferias_n, em_30dias_n, dias_alerta=7)
        _render_menu_principal(t('menu_titulo'), itens, rodape=[(0, t('sair'))], info_topo=info_topo, painel_linhas=painel_linhas)
        op = inp(t('opcao')).strip()
        if op == '1': menu_cadastros(d)
        elif op == '2': menu_ferias(d)
        elif op == '3': menu_banco_horas(d)
        elif op == '4': menu_relatorios(d)
        elif op == '5': painel_ferias(d)
        elif op == '6': grafico_evolucao_mensal(d)
        elif op == '7': menu_regras(d)
        elif op == '8': menu_validacao(d)
        elif op == '9' and eh_admin: menu_configuracoes(d)
        elif op == '10' and eh_admin: menu_administracao(d)
        elif op == '0': break
        else: flash(t('invalido'), erro=True)
    limpar(); p('Encerrando.'); p()

def main():
    """Start the interactive vacation-management application."""
    try:
        menu_principal()
    except KeyboardInterrupt:
        limpar()
        p('\nOperação interrompida pelo usuário.')
    except EOFError:
        limpar()
        p('\nEntrada encerrada.')
if __name__ == '__main__':
    main()