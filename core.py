"""Núcleo compartilhado da aplicação e configuração de runtime."""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
══════════════════════════════════════════════════════════
  SISTEMA DE GERENCIAMENTO DE FÉRIAS  v3.9.1
  Segurança: autenticação com PBKDF2 e criação inicial do administrador
  Correção: texto do menu de gráfico em minúsculas
  Gráfico de Evolução Mensal | Saldo de Dias | Painel Inline
  Análise por Período Aquisitivo | Paginação dinâmica | SQLite
══════════════════════════════════════════════════════════
"""

import getpass, hashlib, hmac, json, locale, os, shutil, secrets, calendar
import sqlite3, sys, unicodedata, time, math
from datetime import datetime, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
try:
    locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, "pt_BR")
    except locale.Error:
        pass

# O aplicativo é autocontido: banco, backups e arquivos de dados ficam
# no mesmo diretório dos arquivos do programa.
# Isso permite executar o sistema a partir de qualquer diretório do sistema,
# sem depender do diretório de trabalho atual, XDG ou variáveis de ambiente.
APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR
BANCO_DADOS = APP_DIR / "dados_ferias.db"
BACKUP_DIR = APP_DIR
_LEGACY_DB = APP_DIR / "dados_ferias.db"
_LEGACY_JSON = APP_DIR / "dados_ferias.json"

LARGURA_MIN = 62
LARGURA_MAX = 110
SEP         = "::"
SESSAO      = {"login": None, "nome": None, "nivel": None}
_FLASH      = {"msg": None, "erro": False}
_IDIOMA     = ["pt"]
_BUF        = None


def verificar_ambiente() -> None:
    """Valida os requisitos mínimos de execução suportados pelo projeto."""
    if sys.version_info < (3, 10):
        atual = ".".join(map(str, sys.version_info[:3]))
        raise RuntimeError(
            f"Python 3.10 ou superior é necessário; versão detectada: {atual}."
        )
    if os.name != "posix":
        raise RuntimeError("Esta versão do Gerenciador de Férias suporta sistemas Linux/Unix (POSIX).")


def preparar_ambiente() -> None:
    """Prepara o diretório da aplicação.

    O diretório da aplicação é a única referência para os dados persistentes.
    Não são criados diretórios auxiliares e o diretório de trabalho atual
    (``cwd``) não influencia a localização do banco ou dos backups.
    """
    APP_DIR.mkdir(parents=True, exist_ok=True)
def flash(msg, erro=False): _FLASH["msg"] = msg; _FLASH["erro"] = erro
def _get_flash():
    msg = _FLASH["msg"]; _FLASH["msg"] = None; return msg, _FLASH["erro"]

T = {
    "sim":               {"pt":"s","en":"y"},
    "nao":               {"pt":"n","en":"n"},
    "cancelar":          {"pt":"Cancelar","en":"Cancel"},
    "voltar":            {"pt":"Voltar","en":"Back"},
    "sair":              {"pt":"Sair","en":"Exit"},
    "salvar_voltar":     {"pt":"Salvar e Voltar","en":"Save and Back"},
    "opcao":             {"pt":"Opção:","en":"Option:"},
    "enter":             {"pt":"[ENTER para continuar...]","en":"[ENTER to continue...]"},
    "invalido":          {"pt":"Opção inválida.","en":"Invalid option."},
    "so_numero":         {"pt":"Digite apenas um número.","en":"Numbers only."},
    "fora_intervalo":    {"pt":"Número fora do intervalo.","en":"Number out of range."},
    "nome_vazio":        {"pt":"O nome não pode ser vazio.","en":"Name cannot be empty."},
    "sem_ferias":        {"pt":"Sem férias agendadas.","en":"No vacations scheduled."},
    "nenhum_setor":      {"pt":"Nenhum setor cadastrado.","en":"No department registered."},
    "nenhum_sub":        {"pt":"Nenhum subsetor cadastrado.","en":"No sub-dept registered."},
    "nenhum_func":       {"pt":"Nenhum funcionário cadastrado.","en":"No employee registered."},
    "nenhum_vinculo":    {"pt":"Nenhum vínculo cadastrado.","en":"No contract type registered."},
    "sem_sub":           {"pt":"(sem subsetores)","en":"(no sub-departments)"},
    "sem_func":          {"pt":"(sem funcionários)","en":"(no employees)"},
    "excluir_cancel":    {"pt":"Exclusão cancelada.","en":"Deletion cancelled."},
    "confirmar_excl":    {"pt":"Confirmar exclusão? (s/n):","en":"Confirm deletion? (y/n):"},
    "pag_pag":           {"pt":"Página","en":"Page"},
    "pag_de":            {"pt":"de","en":"of"},
    "pag_itens":         {"pt":"itens","en":"items"},
    "pag_nav_ambas":     {"pt":"[A]=Anterior  [P]=Próxima  [N]=Ir para  [0]=Sair","en":"[A]=Prev  [P]=Next  [N]=Go  [0]=Exit"},
    "pag_nav_prox":      {"pt":"[P]=Próxima  [N]=Ir para  [0]=Sair","en":"[P]=Next  [N]=Go  [0]=Exit"},
    "pag_nav_ant":       {"pt":"[A]=Anterior  [N]=Ir para  [0]=Sair","en":"[A]=Prev  [N]=Go  [0]=Exit"},
    "pag_nav_unica":     {"pt":"[0]=Sair","en":"[0]=Exit"},
    "pag_cmd":           {"pt":"Navegar:","en":"Navigate:"},
    "pag_ir_para":       {"pt":"Ir para (1–{n}):","en":"Go to (1–{n}):"},
    # ── Gráfico ─────────────────────────────────────────
    # Compatibilidade: o texto do menu de gráfico é mantido em minúsculas.
    # "graf_titulo" mantém MAIÚSCULAS (para o cabeçalho da tela)
    "graf_titulo":       {"pt":"GRÁFICO DE EVOLUÇÃO MENSAL","en":"MONTHLY EVOLUTION CHART"},
    "m_grafico":         {"pt":"Gráfico de evolução mensal","en":"Monthly evolution chart"},
    "graf_escolha_tipo": {"pt":"Tipo de gráfico:","en":"Chart type:"},
    "graf_empresa":      {"pt":"Empresa completa","en":"Whole company"},
    "graf_setor":        {"pt":"Por setor","en":"By department"},
    "graf_subsetor":     {"pt":"Por subsetor","en":"By sub-department"},
    "graf_funcionario":  {"pt":"Por funcionário","en":"By employee"},
    "graf_periodo":      {"pt":"Período","en":"Period"},
    "graf_total_periodo":{"pt":"Total no período","en":"Total in period"},
    "graf_meses_ativos": {"pt":"Meses com férias","en":"Months with vacations"},
    "graf_sem_dados":    {"pt":"Sem dados para o período selecionado.","en":"No data for selected period."},
    "graf_3m":           {"pt":"Últimos  3 meses","en":"Last  3 months"},
    "graf_6m":           {"pt":"Últimos  6 meses","en":"Last  6 months"},
    "graf_12m":          {"pt":"Últimos 12 meses  [padrão]","en":"Last 12 months  [default]"},
    "graf_24m":          {"pt":"Últimos 24 meses","en":"Last 24 months"},
    "graf_detalhe":      {"pt":"[P]=Detalhado por funcionário","en":"[P]=Detailed by employee"},
    # ── Painel inline ────────────────────────────────────
    "menu_nenhum_agora": {"pt":"Ninguém em férias agora","en":"Nobody on vacation now"},
    "menu_inicio_label": {"pt":"Próximos {n} dias","en":"Next {n} days"},
    "menu_nenhum_prox":  {"pt":"Nenhuma entrada nos próximos {n} dias","en":"No starts in the next {n} days"},
    # ── Saldo de dias ────────────────────────────────────
    "rel_saldo":         {"pt":"Saldo de dias de férias","en":"Vacation days balance"},
    "rel_saldo_titulo":  {"pt":"SALDO DE DIAS DE FÉRIAS","en":"VACATION DAYS BALANCE"},
    "rel_saldo_todos":   {"pt":"Todos os funcionários","en":"All employees"},
    "rel_saldo_setor":   {"pt":"Por setor","en":"By department"},
    "rel_saldo_sub":     {"pt":"Por subsetor","en":"By sub-department"},
    "rel_saldo_ok":      {"pt":"Regular","en":"Regular"},
    "rel_saldo_neg":     {"pt":"EXCEDIDO","en":"EXCEEDED"},
    "rel_saldo_sem_lim": {"pt":"Ilimitado","en":"Unlimited"},
    "rel_saldo_usando":  {"pt":"usando ano civil","en":"using calendar year"},
    "rel_saldo_tot_func":{"pt":"Total de funcionários","en":"Total employees"},
    "rel_saldo_excedidos":{"pt":"Com saldo excedido","en":"Exceeded balance"},
    "rel_saldo_sem_saldo":{"pt":"Com saldo disponível","en":"Available balance"},
    "rel_saldo_total_dias":{"pt":"Total de dias tirados","en":"Total days taken"},
    # ── Período aquisitivo ───────────────────────────────
    "pa_atual":          {"pt":"Período aquisitivo atual","en":"Current acquisition period"},
    "pa_tirados":        {"pt":"Tirados","en":"Taken"},
    "pa_restantes":      {"pt":"Restantes","en":"Remaining"},
    "pa_progresso":      {"pt":"Progresso","en":"Progress"},
    "pa_ilimitado":      {"pt":"(sem limite definido)","en":"(no limit defined)"},
    "pa_dias":           {"pt":"dias","en":"days"},
    "pa_sem_admissao":   {"pt":"(sem data de admissão — usando ano civil)","en":"(no hire date — using calendar year)"},
    # ── Relatórios ───────────────────────────────────────
    "rel_titulo":        {"pt":"RELATÓRIOS","en":"REPORTS"},
    "rel_pa_menu":       {"pt":"Por período aquisitivo","en":"By acquisition period"},
    "rel_pa_titulo":     {"pt":"RELATÓRIO POR PERÍODO AQUISITIVO","en":"REPORT BY ACQUISITION PERIOD"},
    "rel_pa_todos":      {"pt":"Todos os funcionários","en":"All employees"},
    "rel_pa_setor":      {"pt":"Por setor","en":"By department"},
    "rel_pa_sub":        {"pt":"Por subsetor","en":"By sub-department"},
    "rel_pa_func":       {"pt":"Por funcionário","en":"By employee"},
    "rel_pa_filtro":     {"pt":"Filtrar por:","en":"Filter by:"},
    "rel_individual":    {"pt":"Relatório individual","en":"Individual report"},
    "rel_individual_t":  {"pt":"RELATÓRIO INDIVIDUAL DE FUNCIONÁRIO","en":"INDIVIDUAL EMPLOYEE REPORT"},
    "rel_multi":         {"pt":"Múltiplos funcionários","en":"Multiple employees"},
    "rel_multi_titulo":  {"pt":"RELATÓRIO — FUNCIONÁRIOS SELECIONADOS","en":"REPORT — SELECTED EMPLOYEES"},
    "rel_multi_lista":   {"pt":"Funcionários selecionados:","en":"Selected employees:"},
    "rel_multi_vazio":   {"pt":"Nenhum funcionário selecionado.","en":"No employees selected."},
    "rel_multi_dup":     {"pt":"Funcionário já adicionado à seleção.","en":"Employee already in selection."},
    "rel_multi_gerenciar":{"pt":"[A]=Adicionar  [R]=Remover  [G]=Gerar  [0]=Cancelar","en":"[A]=Add  [R]=Remove  [G]=Generate  [0]=Cancel"},
    "rel_selecionados":  {"pt":"selecionado(s)","en":"selected"},
    "rel_geral":         {"pt":"Geral — toda a empresa","en":"General — whole company"},
    "rel_setor":         {"pt":"Por setor","en":"By department"},
    "rel_sub":           {"pt":"Por subsetor","en":"By sub-department"},
    "rel_periodo":       {"pt":"Por período de datas","en":"By date range"},
    "rel_situacao":      {"pt":"Situação de férias","en":"Vacation status"},
    "rel_vencidas":      {"pt":"Férias vencidas","en":"Overdue vacations"},
    "rel_ano":           {"pt":"Por ano civil (complemento)","en":"By calendar year"},
    "rel_ano_titulo":    {"pt":"RELATÓRIO POR ANO CIVIL","en":"VACATION REPORT BY CALENDAR YEAR"},
    "rel_ano_pedir":     {"pt":"Ano (ex: 2026) ou ENTER para o ano atual:","en":"Year (e.g. 2026) or ENTER for current year:"},
    "rel_ano_inv":       {"pt":"Ano inválido. Use entre 2000 e {max}.","en":"Invalid year. Use between 2000 and {max}."},
    "rel_ano_todos":     {"pt":"Todos os funcionários","en":"All employees"},
    "rel_ano_setor":     {"pt":"Por setor","en":"By department"},
    "rel_ano_sub":       {"pt":"Por subsetor","en":"By sub-department"},
    "rel_ano_func":      {"pt":"Por funcionário","en":"By employee"},
    "rel_ano_vazio":     {"pt":"Nenhuma férias encontrada para {ano}.","en":"No vacations found for {ano}."},
    "rel_ano_label":     {"pt":"Ano consultado","en":"Queried year"},
    "rel_ano_total":     {"pt":"Total de dias no ano civil","en":"Total days in calendar year"},
    "rel_ano_cruzou":    {"pt":"(cruza ano)","en":"(crosses year)"},
    "rel_data":          {"pt":"Data do relatório","en":"Report date"},
    "rel_periodo_c":     {"pt":"Período consultado","en":"Queried period"},
    "rel_encontrados":   {"pt":"Funcionários encontrados","en":"Employees found"},
    "rel_nenhum_p":      {"pt":"Nenhum funcionário com férias neste período.","en":"No employees with vacations in this period."},
    "rel_set_cad":       {"pt":"Setores cadastrados","en":"Departments"},
    "rel_subs":          {"pt":"Subsetores","en":"Sub-departments"},
    "rel_total_func":    {"pt":"Total de funcionários","en":"Total employees"},
    "rel_com_ferias":    {"pt":"Com férias","en":"With vacations"},
    "rel_sem_ferias":    {"pt":"Sem férias","en":"Without vacations"},
    "rel_tot_dias":      {"pt":"Total de dias de férias","en":"Total vacation days"},
    "rel_dias_per":      {"pt":"dias no período","en":"days in period"},
    "rel_tot_per":       {"pt":"Total de dias no período","en":"Total days in period"},
    "rel_periodos":      {"pt":"Períodos agendados","en":"Scheduled periods"},
    "rel_total_label":   {"pt":"Total","en":"Total"},
    "rel_dias_unit":     {"pt":"dias","en":"days"},
    "rel_vinculo":       {"pt":"Vínculo","en":"Contract"},
    "rel_nome":          {"pt":"Nome","en":"Name"},
    "rel_setor_l":       {"pt":"Setor","en":"Department"},
    "rel_sub_l":         {"pt":"Subsetor","en":"Sub-dept"},
    "rel_inicio":        {"pt":"Início","en":"Start"},
    "rel_termino":       {"pt":"Término","en":"End"},
    "rel_dias":          {"pt":"Dias","en":"Days"},
    "rel_status":        {"pt":"Status","en":"Status"},
    "rel_venda":         {"pt":"Venda férias","en":"Vacation sale"},
    "rel_andamento":     {"pt":"EM ANDAMENTO","en":"IN PROGRESS"},
    "rel_futuro":        {"pt":"FUTURO","en":"UPCOMING"},
    "rel_concluido":     {"pt":"CONCLUÍDO","en":"COMPLETED"},
    "rel_interv":        {"pt":"Informe o intervalo de datas:","en":"Enter the date range:"},
    "rel_agendamentos":  {"pt":"Agendamentos:","en":"Schedules:"},
    "rel_funclist":      {"pt":"Funcionários:","en":"Employees:"},
    # ── Análise de férias ────────────────────────────────
    "dias_restantes":    {"pt":"Restantes","en":"Remaining"},
    "dias_ilimitado":    {"pt":"(sem limite anual)","en":"(no annual limit)"},
    "periodos_passados": {"pt":"Períodos concluídos","en":"Completed periods"},
    "periodos_futuros":  {"pt":"Períodos futuros","en":"Upcoming periods"},
    "ferias_em_dia":     {"pt":"Em dia","en":"Up to date"},
    "ferias_vencidas":   {"pt":"FÉRIAS VENCIDAS","en":"OVERDUE VACATION"},
    "ferias_a_vencer":   {"pt":"A vencer","en":"Expiring soon"},
    "ferias_pendentes":  {"pt":"Pendente","en":"Pending"},
    "sem_admissao":      {"pt":"(sem data de admissão)","en":"(no hire date)"},
    "data_admissao":     {"pt":"Data de admissão:","en":"Hire date:"},
    "periodo_aquisitivo":{"pt":"Período aquisitivo","en":"Acquisition period"},
    "periodo_concessivo":{"pt":"Período concessivo até","en":"Concession deadline"},
    "nenhum_vencido":    {"pt":"Nenhum funcionário com férias vencidas.","en":"No employees with overdue vacations."},
    "vencida_em":        {"pt":"Venceu em","en":"Expired on"},
    "dias_para_vencer":  {"pt":"dias para vencer","en":"days to expire"},
    "admissao_inv":      {"pt":"Data de admissão inválida. Use DD/MM/AAAA.","en":"Invalid hire date. Use DD/MM/YYYY."},
    "situacao_label":    {"pt":"Situação","en":"Status"},
    "rel_sit_titulo":    {"pt":"SITUAÇÃO DE FÉRIAS — TODOS","en":"VACATION STATUS — ALL"},
    "func_vencidas":     {"pt":"Funcionários com Férias Vencidas","en":"Employees with Overdue Vacations"},
    "dir_asc_curto":     {"pt":"A→Z","en":"A→Z"},
    "dir_desc_curto":    {"pt":"Z→A","en":"Z→A"},
    # ── Login ────────────────────────────────────────────
    "login_titulo":      {"pt":"LOGIN DO SISTEMA","en":"SYSTEM LOGIN"},
    "login_usuario":     {"pt":"Usuário:","en":"Username:"},
    "login_senha":       {"pt":"Senha:","en":"Password:"},
    "login_erro":        {"pt":"Usuário ou senha incorretos. Tente novamente.","en":"Incorrect credentials. Try again."},
    "login_bloq":        {"pt":"Conta bloqueada após 3 tentativas.","en":"Account locked after 3 attempts."},
    "nivel_admin":       {"pt":"Administrador","en":"Administrator"},
    "nivel_usuario":     {"pt":"Usuário","en":"User"},
    "acesso_negado":     {"pt":"Acesso restrito ao Administrador.","en":"Administrator access only."},
    # ── Menu principal ───────────────────────────────────
    "menu_titulo":       {"pt":"GERENCIAMENTO DE FÉRIAS  v3.9.1","en":"VACATION MANAGEMENT SYSTEM  v3.9.1"},
    "m_setores":         {"pt":"Setores e subsetores","en":"Departments"},
    "m_funcs":           {"pt":"Funcionários e vínculos","en":"Employees & contracts"},
    "m_ferias":          {"pt":"Férias","en":"Vacations"},
    "m_relat":           {"pt":"Relatórios","en":"Reports"},
    "m_regras":          {"pt":"Regras de férias","en":"Vacation rules"},
    "m_valid":           {"pt":"Validação automática","en":"Auto validation"},
    "m_config":          {"pt":"Configurações de exibição","en":"Display settings"},
    "m_admin":           {"pt":"Administração do sistema","en":"System administration"},
    "m_painel":          {"pt":"Painel de férias","en":"Vacation panel"},
    "status_ok":         {"pt":"Sistema sem pendências.","en":"No issues found."},
    "status_pend":       {"pt":"ATENÇÃO: {n} pendência(s) detectada(s)","en":"WARNING: {n} issue(s) detected"},
    "logado":            {"pt":"Logado como:","en":"Logged in as:"},
    "exibicao":          {"pt":"Exibição:","en":"Display:"},
    "ferias_venc_alerta":{"pt":"FÉRIAS VENCIDAS: {n} funcionário(s)","en":"OVERDUE: {n} employee(s)"},
    # ── Painel rápido ────────────────────────────────────
    "painel_titulo":     {"pt":"PAINEL DE FÉRIAS","en":"VACATION PANEL"},
    "painel_agora":      {"pt":"EM FÉRIAS AGORA","en":"ON VACATION NOW"},
    "painel_30dias":     {"pt":"PRÓXIMOS 30 DIAS","en":"STARTING WITHIN 30 DAYS"},
    "painel_nenhum_ag":  {"pt":"Nenhum funcionário em férias no momento.","en":"No employees on vacation right now."},
    "painel_nenhum_30":  {"pt":"Nenhum funcionário entra de férias nos próximos 30 dias.","en":"No employees starting vacation in the next 30 days."},
    "painel_termina":    {"pt":"Termina em","en":"Ends in"},
    "painel_inicia":     {"pt":"Inicia em","en":"Starts in"},
    "painel_dias_rest":  {"pt":"dia(s) restante(s)","en":"day(s) remaining"},
    "painel_dias_ini":   {"pt":"dia(s) para iniciar","en":"day(s) to start"},
    "painel_em_ferias":  {"pt":"Em férias agora","en":"On vacation now"},
    "painel_em_30d":     {"pt":"Iniciam em até 30 dias","en":"Starting within 30 days"},
    "painel_alerta":     {"pt":"Em férias: {agora}  |  Próximos 30 dias: {em30}","en":"On vacation: {agora}  |  Next 30 days: {em30}"},
    # ── Administração ────────────────────────────────────
    "adm_titulo":        {"pt":"ADMINISTRAÇÃO DO SISTEMA","en":"SYSTEM ADMINISTRATION"},
    "adm_usuarios":      {"pt":"Usuários do sistema","en":"System users"},
    "adm_backup":        {"pt":"Backup e restauração","en":"Backup & restore"},
    "adm_apagar":        {"pt":"Apagar todos os dados","en":"Delete all data"},
    "adm_idioma":        {"pt":"Idioma / Language","en":"Idioma / Language"},
    "usr_titulo":        {"pt":"USUÁRIOS DO SISTEMA","en":"SYSTEM USERS"},
    "usr_listar":        {"pt":"Listar usuários","en":"List users"},
    "usr_criar":         {"pt":"Criar usuário","en":"Create user"},
    "usr_senha":         {"pt":"Alterar senha","en":"Change password"},
    "usr_excluir":       {"pt":"Excluir usuário","en":"Delete user"},
    "usr_nova_senha":    {"pt":"Nova senha:","en":"New password:"},
    "usr_conf_senha":    {"pt":"Confirme a senha:","en":"Confirm password:"},
    "usr_nivel":         {"pt":"Nível (1=Admin / 2=Usuário):","en":"Level (1=Admin / 2=User):"},
    "usr_senha_dif":     {"pt":"As senhas não conferem.","en":"Passwords do not match."},
    "usr_ja_existe":     {"pt":"Login já cadastrado.","en":"Login already exists."},
    "usr_ultimo_adm":    {"pt":"Não é possível excluir o único administrador.","en":"Cannot delete the only administrator."},
    "usr_proprio":       {"pt":"Não é possível excluir seu próprio usuário.","en":"Cannot delete your own account."},
    "usr_nenhum":        {"pt":"Nenhum usuário cadastrado.","en":"No users registered."},
    "usr_criado":        {"pt":"Usuário criado com sucesso!","en":"User created successfully!"},
    "usr_excluido":      {"pt":"Usuário excluído com sucesso!","en":"User deleted successfully!"},
    "usr_senha_ok":      {"pt":"Senha alterada com sucesso!","en":"Password changed successfully!"},
    "bkp_titulo":        {"pt":"BACKUP E RESTAURAÇÃO","en":"BACKUP & RESTORE"},
    "bkp_fazer":         {"pt":"Fazer backup agora","en":"Create backup now"},
    "bkp_restaurar":     {"pt":"Restaurar backup","en":"Restore backup"},
    "bkp_listar":        {"pt":"Listar backups","en":"List backups"},
    "bkp_ok":            {"pt":"Backup criado: ","en":"Backup created: "},
    "bkp_rest_ok":       {"pt":"Backup restaurado com sucesso!","en":"Backup restored successfully!"},
    "bkp_nenhum":        {"pt":"Nenhum backup encontrado.","en":"No backups found."},
    "bkp_confirma":      {"pt":"Restaurar substituirá os dados atuais. Confirmar? (s/n):","en":"Restore will replace current data. Confirm? (y/n):"},
    "bkp_cancel":        {"pt":"Restauração cancelada.","en":"Restore cancelled."},
    "apg_titulo":        {"pt":"APAGAR TODOS OS DADOS","en":"DELETE ALL DATA"},
    "apg_aviso1":        {"pt":"ATENÇÃO: Esta ação é IRREVERSÍVEL!","en":"WARNING: This action is IRREVERSIBLE!"},
    "apg_aviso2":        {"pt":"Todos os dados serão apagados permanentemente.","en":"All data will be permanently deleted."},
    "apg_instrucao":     {"pt":"Digite CONFIRMAR para prosseguir:","en":"Type CONFIRM to proceed:"},
    "apg_palavra":       {"pt":"CONFIRMAR","en":"CONFIRM"},
    "apg_ok":            {"pt":"Todos os dados foram apagados.","en":"All data has been deleted."},
    "apg_cancel":        {"pt":"Operação cancelada.","en":"Operation cancelled."},
    "idioma_titulo":     {"pt":"IDIOMA / LANGUAGE","en":"IDIOMA / LANGUAGE"},
    "idioma_atual":      {"pt":"Idioma atual:","en":"Current language:"},
    "idioma_pt":         {"pt":"Português (PT-BR)","en":"Portuguese (PT-BR)"},
    "idioma_en":         {"pt":"English (EN)","en":"English (EN)"},
    "idioma_ok":         {"pt":"Idioma alterado!","en":"Language changed!"},
    # ── Setores ─────────────────────────────────────────
    "set_titulo":        {"pt":"SETORES E SUBSETORES","en":"DEPARTMENTS"},
    "set_listar":        {"pt":"Listar setores","en":"List departments"},
    "set_novo":          {"pt":"Novo setor","en":"New department"},
    "set_excluir":       {"pt":"Excluir setor","en":"Delete department"},
    "set_novo_sub":      {"pt":"Novo subsetor","en":"New sub-department"},
    "set_excluir_sub":   {"pt":"Excluir subsetor","en":"Delete sub-department"},
    "set_nome":          {"pt":"Nome do setor:","en":"Department name:"},
    "sub_nome":          {"pt":"Nome do subsetor:","en":"Sub-dept name:"},
    "set_ja_existe":     {"pt":"Setor já cadastrado.","en":"Department already exists."},
    "sub_ja_existe":     {"pt":"Subsetor já cadastrado.","en":"Sub-dept already exists."},
    "set_criado":        {"pt":"Setor criado com sucesso!","en":"Department created!"},
    "sub_criado":        {"pt":"Subsetor criado com sucesso!","en":"Sub-dept created!"},
    "set_excluido":      {"pt":"Setor excluído com sucesso!","en":"Department deleted!"},
    "sub_excluido":      {"pt":"Subsetor excluído com sucesso!","en":"Sub-dept deleted!"},
    "set_vinculados":    {"pt":"Não é possível excluir: {n} funcionário(s) vinculado(s).","en":"Cannot delete: {n} linked employee(s)."},
    "set_disponiveis":   {"pt":"Setores disponíveis:","en":"Available departments:"},
    "sub_disponiveis":   {"pt":"Subsetores de","en":"Sub-departments of"},
    # ── Vínculos ─────────────────────────────────────────
    "vin_titulo":        {"pt":"VÍNCULOS","en":"CONTRACT TYPES"},
    "vin_listar":        {"pt":"Listar vínculos","en":"List contract types"},
    "vin_novo":          {"pt":"Novo vínculo","en":"New contract type"},
    "vin_excluir":       {"pt":"Excluir vínculo","en":"Delete contract type"},
    "vin_nome":          {"pt":"Nome do vínculo (ex: CLT, PJ):","en":"Contract type:"},
    "vin_ja_existe":     {"pt":"Vínculo já cadastrado.","en":"Contract type already exists."},
    "vin_criado":        {"pt":"Vínculo criado com sucesso!","en":"Contract type created!"},
    "vin_excluido":      {"pt":"Vínculo excluído com sucesso!","en":"Contract type deleted!"},
    "vin_em_uso":        {"pt":"Não é possível excluir: {n} funcionário(s) com este vínculo.","en":"Cannot delete: {n} employee(s) with this contract."},
    "vin_disponiveis":   {"pt":"Vínculos disponíveis:","en":"Available contracts:"},
    "vin_sem":           {"pt":"0. Sem vínculo","en":"0. No contract type"},
    # ── Funcionários ─────────────────────────────────────
    "fun_titulo":        {"pt":"FUNCIONÁRIOS","en":"EMPLOYEES"},
    "fun_listar":        {"pt":"Listar funcionários","en":"List employees"},
    "fun_por_setor":     {"pt":"Listar por setor e subsetor","en":"List by department & sub-dept"},
    "fun_novo":          {"pt":"Novo funcionário","en":"New employee"},
    "fun_excluir":       {"pt":"Excluir funcionário","en":"Delete employee"},
    "fun_vinculos":      {"pt":"Gerenciar vínculos","en":"Manage contracts"},
    "fun_nome":          {"pt":"Nome do funcionário:","en":"Employee name:"},
    "fun_vinculo_sel":   {"pt":"Vínculo do funcionário:","en":"Employee contract:"},
    "fun_ja_existe":     {"pt":"Funcionário já cadastrado neste subsetor.","en":"Employee already registered in this sub-dept."},
    "fun_criado":        {"pt":"Funcionário cadastrado com sucesso!","en":"Employee registered!"},
    "fun_excluido":      {"pt":"Funcionário excluído com sucesso!","en":"Employee deleted!"},
    "fun_lista":         {"pt":"Funcionários:","en":"Employees:"},
    # ── Férias ───────────────────────────────────────────
    "fer_titulo":        {"pt":"FÉRIAS","en":"VACATIONS"},
    "fer_agendar":       {"pt":"Agendar férias","en":"Schedule vacation"},
    "fer_cancelar":      {"pt":"Cancelar férias","en":"Cancel vacation"},
    "fer_calendario":    {"pt":"Calendário por subsetor","en":"Calendar by sub-dept"},
    "fer_inicio":        {"pt":"Data de início   (DD/MM/AAAA):","en":"Start date (DD/MM/YYYY):"},
    "fer_fim":           {"pt":"Data de término  (DD/MM/AAAA):","en":"End date   (DD/MM/YYYY):"},
    "fer_data_inv":      {"pt":"Data inválida! Use DD/MM/AAAA.","en":"Invalid date! Use DD/MM/YYYY."},
    "fer_data_ord":      {"pt":"Início posterior ao término.","en":"Start date is after end date."},
    "fer_bloqueado":     {"pt":"AGENDAMENTO BLOQUEADO — regras violadas:","en":"SCHEDULING BLOCKED — rules violated:"},
    "fer_venda_info":    {"pt":"Venda de férias (abono pecuniário) permitida.","en":"Vacation sale (cash allowance) permitted."},
    "fer_venda_marcar":  {"pt":"Marcar venda de 1/3? (s/n):","en":"Mark 1/3 vacation sale? (y/n):"},
    "fer_ok":            {"pt":"Férias agendadas com sucesso!","en":"Vacation scheduled!"},
    "fer_removida":      {"pt":"Férias removidas com sucesso!","en":"Vacation removed!"},
    "fer_sem":           {"pt":"não possui férias agendadas.","en":"has no vacations scheduled."},
    "fer_remover_num":   {"pt":"Número a remover:","en":"Number to remove:"},
    "fer_cal_titulo":    {"pt":"CALENDÁRIO DE FÉRIAS","en":"VACATION CALENDAR"},
    "fer_com_venda":     {"pt":"[com venda]","en":"[with sale]"},
    "fer_venda_lbl":     {"pt":"[venda]","en":"[sale]"},
    # ── Regras ───────────────────────────────────────────
    "reg_titulo":        {"pt":"REGRAS DE FÉRIAS","en":"VACATION RULES"},
    "reg_ver":           {"pt":"Ver todas as regras","en":"View all rules"},
    "reg_global":        {"pt":"Regras globais","en":"Global rules"},
    "reg_vinculo":       {"pt":"Regras por vínculo","en":"Rules by contract"},
    "reg_setor":         {"pt":"Regras por setor","en":"Rules by department"},
    "reg_subsetor":      {"pt":"Regras por subsetor","en":"Rules by sub-department"},
    "reg_hier":          {"pt":"Hierarquia: Subsetor > Setor > Vínculo > Global","en":"Hierarchy: Sub-dept > Dept > Contract > Global"},
    "reg_editar":        {"pt":"EDITAR REGRA","en":"EDIT RULE"},
    "reg_campo":         {"pt":"Campo","en":"Field"},
    "reg_dica":          {"pt":"Dica","en":"Tip"},
    "reg_atual":         {"pt":"Atual","en":"Current"},
    "reg_herdar":        {"pt":"Herdar","en":"Inherit"},
    "reg_herdado":       {"pt":"Herdado","en":"Inherited"},
    "reg_niv_sup":       {"pt":"nível superior","en":"upper level"},
    "reg_s_n_h":         {"pt":"s=Sim / n=Não / ENTER=herdar:","en":"y=Yes / n=No / ENTER=inherit:"},
    "reg_s_n_m":         {"pt":"s=Sim / n=Não / ENTER=manter:","en":"y=Yes / n=No / ENTER=keep:"},
    "reg_num_h":         {"pt":"Número / ENTER=herdar:","en":"Number / ENTER=inherit:"},
    "reg_num_m":         {"pt":"Número / ENTER=manter:","en":"Number / ENTER=keep:"},
    "reg_herdar_nota":   {"pt":"  * ENTER = herdar do nível superior","en":"  * ENTER = inherit from upper level"},
    "reg_salvas":        {"pt":"Regras salvas com sucesso!","en":"Rules saved!"},
    "reg_gl_s":          {"pt":"▸ GLOBAIS","en":"▸ GLOBAL"},
    "reg_vin_s":         {"pt":"▸ POR VÍNCULO","en":"▸ BY CONTRACT"},
    "reg_set_s":         {"pt":"▸ POR SETOR","en":"▸ BY DEPARTMENT"},
    "reg_sub_s":         {"pt":"▸ POR SUBSETOR","en":"▸ BY SUB-DEPARTMENT"},
    "reg_sem_vin":       {"pt":"(nenhuma regra específica por vínculo)","en":"(no specific rules per contract)"},
    "reg_sem_set":       {"pt":"(nenhuma regra específica por setor)","en":"(no specific rules per department)"},
    "reg_sem_sub":       {"pt":"(nenhuma regra específica por subsetor)","en":"(no specific rules per sub-department)"},
    "reg_sel_sub":       {"pt":"Selecione o subsetor para configurar as regras:","en":"Select the sub-department to configure rules:"},
    # ── Validação ────────────────────────────────────────
    "val_titulo":        {"pt":"VALIDAÇÃO AUTOMÁTICA","en":"AUTO VALIDATION"},
    "val_ok":            {"pt":"Nenhuma pendência encontrada!","en":"No issues found!"},
    "val_pend":          {"pt":"pendência(s) encontrada(s)","en":"issue(s) found"},
    "val_ver":           {"pt":"Ver todas as pendências","en":"View all issues"},
    "val_por_func":      {"pt":"Validar por funcionário","en":"Validate by employee"},
    "val_por_setor":     {"pt":"Validar por setor","en":"Validate by department"},
    "val_revalid":       {"pt":"Revalidar sistema","en":"Revalidate system"},
    "val_geral_t":       {"pt":"PENDÊNCIAS — SISTEMA COMPLETO","en":"ISSUES — FULL SYSTEM"},
    "val_func_t":        {"pt":"VALIDAÇÃO POR FUNCIONÁRIO","en":"VALIDATE BY EMPLOYEE"},
    "val_setor_t":       {"pt":"VALIDAÇÃO POR SETOR","en":"VALIDATE BY DEPARTMENT"},
    "val_data":          {"pt":"Data da verificação","en":"Verification date"},
    "val_c_pend":        {"pt":"Funcionários com pendências","en":"Employees with issues"},
    "val_total":         {"pt":"Total de pendências","en":"Total issues"},
    "val_conform":       {"pt":"Todos os agendamentos estão em conformidade!","en":"All schedules are compliant!"},
    "val_periodos":      {"pt":"Períodos de férias","en":"Vacation periods"},
    "val_pendencias":    {"pt":"Pendências","en":"Issues"},
    "val_c_pend2":       {"pt":"Com pendências","en":"With issues"},
    "val_revalid_t":     {"pt":"REVALIDANDO SISTEMA...","en":"REVALIDATING..."},
    "val_verificando":   {"pt":"Verificando todos os funcionários e períodos...","en":"Checking all employees and periods..."},
    "val_detalhe":       {"pt":"Veja 'Ver Todas as Pendências'.","en":"See 'View All Issues'."},
    # ── Configurações ────────────────────────────────────
    "cfg_titulo":        {"pt":"CONFIGURAÇÕES DE EXIBIÇÃO","en":"DISPLAY SETTINGS"},
    "cfg_desc":          {"pt":"Ordenação aplicada em todas as telas e relatórios.","en":"Sorting applied across all screens."},
    "cfg_atual":         {"pt":"Configuração atual:","en":"Current setting:"},
    "cfg_atual_m":       {"pt":"[atual]","en":"[current]"},
    "cfg_alterar":       {"pt":"ALTERAR:","en":"CHANGE:"},
    "cfg_escolha":       {"pt":"Opção:","en":"Option:"},
    "cfg_salvo":         {"pt":"Configurações salvas!","en":"Settings saved!"},
}

def set_idioma(lang): _IDIOMA[0] = lang if lang in ("pt","en") else "pt"
def get_idioma():     return _IDIOMA[0]
def t(chave, **kw):
    lang = get_idioma()
    txt  = T.get(chave,{}).get(lang, T.get(chave,{}).get("pt", chave))
    return txt.format(**kw) if kw else txt
def _dir_curto(cfg):
    return t("dir_asc_curto") if cfg.get("direcao","asc")=="asc" else t("dir_desc_curto")

def _campos_regras():
    lg = get_idioma()
    return {
        "permite_venda_ferias":  {"label":{"pt":"Permite venda de férias (abono)","en":"Allow vacation sale"}[lg],"tipo":"bool","padrao":False,"dica":{"pt":"Vender até 1/3 das férias em dinheiro","en":"Sell up to 1/3 as cash"}[lg]},
        "max_periodos_ano":      {"label":{"pt":"Máximo de períodos por prd.aquisitivo","en":"Max periods per acquisition period"}[lg],"tipo":"int","padrao":3,"dica":{"pt":"Limite por período aquisitivo (0=ilimitado)","en":"Limit per acquisition period (0=unlimited)"}[lg]},
        "min_dias_periodo":      {"label":{"pt":"Mínimo de dias por período","en":"Min days per period"}[lg],"tipo":"int","padrao":5,"dica":{"pt":"Mínimo de dias corridos (0=sem restrição)","en":"Min calendar days (0=none)"}[lg]},
        "max_dias_ano":          {"label":{"pt":"Máximo de dias (por período aquisitivo)","en":"Max days (per acquisition period)"}[lg],"tipo":"int","padrao":30,"dica":{"pt":"Total de dias por período de 12 meses (0=ilimitado)","en":"Total days per 12-month period (0=unlimited)"}[lg]},
        "permite_concomitantes": {"label":{"pt":"Permite férias simultâneas no subsetor","en":"Allow concurrent vacations"}[lg],"tipo":"bool","padrao":False,"dica":{"pt":"Se Não, bloqueia sobreposição no subsetor","en":"If No, blocks sub-dept overlap"}[lg]},
        "max_concomitantes":     {"label":{"pt":"Máx. funcionários simultâneos","en":"Max concurrent employees"}[lg],"tipo":"int","padrao":1,"dica":{"pt":"Aplica se simultâneas forem permitidas (0=ilimitado)","en":"Applies if concurrent allowed (0=unlimited)"}[lg]},
        "aviso_previo_dias":     {"label":{"pt":"Antecedência mínima (dias)","en":"Min advance notice (days)"}[lg],"tipo":"int","padrao":0,"dica":{"pt":"Dias de antecedência exigidos (0=sem restrição)","en":"Required advance days (0=none)"}[lg]},
    }

CONFIG_PADRAO = {
    "ordem_setores":"nome","ordem_subsetores":"nome","ordem_vinculos":"nome",
    "ordem_funcionarios":"nome","ordem_ferias":"inicio","direcao":"asc",
}

def _config_opcoes():
    lg = get_idioma()
    return {
        "ordem_setores":      {"label":{"pt":"Ordenação de setores","en":"Department sorting"}[lg],"opcoes":{"nome":{"pt":"Alfabética","en":"Alphabetical"}[lg],"cadastro":{"pt":"Por cadastro","en":"By registration"}[lg]}},
        "ordem_subsetores":   {"label":{"pt":"Ordenação de subsetores","en":"Sub-dept sorting"}[lg],"opcoes":{"nome":{"pt":"Alfabética","en":"Alphabetical"}[lg],"cadastro":{"pt":"Por cadastro","en":"By registration"}[lg]}},
        "ordem_vinculos":     {"label":{"pt":"Ordenação de vínculos","en":"Contract sorting"}[lg],"opcoes":{"nome":{"pt":"Alfabética","en":"Alphabetical"}[lg],"cadastro":{"pt":"Por cadastro","en":"By registration"}[lg]}},
        "ordem_funcionarios": {"label":{"pt":"Ordenação de funcionários","en":"Employee sorting"}[lg],"opcoes":{"nome":{"pt":"Por nome","en":"By name"}[lg],"setor":{"pt":"Por setor","en":"By department"}[lg],"subsetor":{"pt":"Por subsetor","en":"By sub-dept"}[lg],"vinculo":{"pt":"Por vínculo","en":"By contract"}[lg],"cadastro":{"pt":"Por cadastro","en":"By registration"}[lg]}},
        "ordem_ferias":       {"label":{"pt":"Ordenação de férias","en":"Vacation sorting"}[lg],"opcoes":{"inicio":{"pt":"Por data de início","en":"By start date"}[lg],"fim":{"pt":"Por data de término","en":"By end date"}[lg],"dias":{"pt":"Por duração (dias)","en":"By duration"}[lg],"cadastro":{"pt":"Por cadastro","en":"By registration"}[lg]}},
        "direcao":            {"label":{"pt":"Direção da ordenação","en":"Sort direction"}[lg],"opcoes":{"asc":{"pt":"Crescente  (A → Z)","en":"Ascending  (A → Z)"}[lg],"desc":{"pt":"Decrescente (Z → A)","en":"Descending (Z → A)"}[lg]}},
    }

# ── Layout ────────────────────────────────────────────
def _cols():  return shutil.get_terminal_size((80,24)).columns
def _rows():  return shutil.get_terminal_size((80,24)).lines
def _larg():  return max(LARGURA_MIN, min(LARGURA_MAX, _cols()-4))
def _recuo(): return " " * max(0, (_cols()-_larg())//2)
def _vis(s):
    return sum(2 if unicodedata.east_asian_width(c) in ("W","F") else 1 for c in str(s))
def _pl(s,n): return s + " "*max(0, n-_vis(s))
def _pc(s,n):
    e=max(0,n-_vis(s)); el=e//2; return " "*el+s+" "*(e-el)
def _wrap(txt, util):
    ind=len(txt)-len(txt.lstrip()); pref=" "*ind; words=txt.strip().split()
    if not words: return [""]
    lines,cur=[],pref
    for w in words:
        cand=(cur+" "+w) if cur.strip() else pref+w
        if _vis(cand)<=util: cur=cand
        else:
            if cur.strip(): lines.append(cur)
            cur=pref+w
    if cur.strip(): lines.append(cur)
    return lines or [""]

def _ln(txt="", align="left"):
    global _BUF; l=_larg(); util=l-4
    partes=_wrap(txt,util) if _vis(txt)>util else [txt]
    for pp in partes:
        c=_pc(pp,util) if align=="center" else _pl(pp,util)
        if _BUF is not None: _BUF.append(("L",c))
        else: print(_recuo()+"║ "+c+" ║")
def _lvz():
    global _BUF
    if _BUF is not None: _BUF.append(("V",))
    else: l=_larg(); print(_recuo()+"║"+" "*(l-2)+"║")
def _dleve():
    global _BUF
    if _BUF is not None: _BUF.append(("D",))
    else: l=_larg(); print(_recuo()+"║"+"─"*(l-2)+"║")
def _print_buf(item):
    l=_larg(); r=_recuo()
    if   item[0]=="L": print(r+"║ "+item[1]+" ║")
    elif item[0]=="V": print(r+"║"+" "*(l-2)+"║")
    elif item[0]=="D": print(r+"║"+"─"*(l-2)+"║")
def _capturar(fn, *args, **kwargs):
    global _BUF; _BUF=[]
    fn(*args,**kwargs); result=list(_BUF); _BUF=None; return result
def topo():  l=_larg(); print(_recuo()+"╔"+"═"*(l-2)+"╗")
def fundo(): l=_larg(); print(_recuo()+"╚"+"═"*(l-2)+"╝")
def _div():  l=_larg(); print(_recuo()+"╠"+"═"*(l-2)+"╣")
def titulo_box(txt): topo(); _ln(txt,"center"); _div()
def _lnd(chave, valor):
    l=_larg(); util=l-4; txt=f"  {chave}: {valor}"
    if _vis(txt)<=util: _ln(txt)
    else:
        pref=f"  {chave}: "; pp=" "*_vis(pref); mv=util-_vis(pref)
        partes=_wrap(valor,mv) if mv>4 else [valor[:mv]]
        _ln(pref+partes[0])
        for pt in partes[1:]: _ln(pp+pt)
def p(txt=""):
    r=_recuo(); util=_larg()-2
    if not txt: print(); return
    if _vis(txt)<=util: print(r+txt)
    else:
        for ln in _wrap(txt,util): print(r+ln)
def inp(prompt):  return input(_recuo()+"  "+prompt+" ")
def inp_s(prompt):
    try:    return getpass.getpass(_recuo()+"  "+prompt+" ")
    except: return inp(prompt)
def pausar(): print(); input(_recuo()+"  "+t("enter")+" ")
def limpar():
    """Limpa o terminal sem depender do comando externo ``clear``."""
    if sys.stdout.isatty():
        print("\033[2J\033[H", end="")
    else:
        print()

def _render_menu(titulo, itens, rodape=None, info=None):
    limpar(); titulo_box(titulo); _lvz()
    for item in itens:
        if item is None: _dleve()
        else:            _ln(f"  {item[0]}. {item[1]}")
    if rodape: _dleve()
    if rodape:
        for item in rodape: _ln(f"  {item[0]}. {item[1]}")
    if info: _dleve()
    if info:
        for i in info: _ln(f"  {i}")
    msg,erro=_get_flash()
    if msg: _dleve(); _ln(("  ✗ " if erro else "  ✓ ")+msg)
    fundo(); p()

# ── Paginação ─────────────────────────────────────────
def _available_rows(n_resumo=0):
    total=_rows(); fixo=4+1+1+1+2; resumo=(n_resumo+1) if n_resumo>0 else 0
    return max(3, total-fixo-resumo)
def _build_pages(renders, available):
    pages=[]; pag=[]; usado=0
    for r in renders:
        n=len(r)
        if pag and usado+n>available: pages.append(pag); pag=list(r); usado=n
        else: pag.extend(r); usado+=n
    if pag: pages.append(pag)
    return pages or [[]]
def paginar(d, titulo, itens, render_item_fn, resumo_fn=None):
    if not itens:
        limpar(); titulo_box(titulo); _lvz(); _ln("  — Nenhum item para exibir —","center"); _lvz(); fundo(); pausar(); return
    renders=   [_capturar(render_item_fn, item) for item in itens]
    resumo_buf=_capturar(resumo_fn) if resumo_fn else []
    pag_idx=0
    while True:
        available=_available_rows(len(resumo_buf)); pages=_build_pages(renders, available)
        total_pags=len(pages); pag_idx=min(pag_idx, total_pags-1)
        limpar(); topo(); _ln(titulo,"center")
        _ln(f"  {t('pag_pag')} {pag_idx+1} {t('pag_de')} {total_pags}  —  {len(itens)} {t('pag_itens')}"); _div()
        if resumo_buf:
            for item in resumo_buf: _print_buf(item)
            if not (pages[pag_idx] and pages[pag_idx][0][0]=="D"): _dleve()
        for item in pages[pag_idx]: _print_buf(item)
        if not (pages[pag_idx] and pages[pag_idx][-1][0]=="D"): _dleve()
        if   total_pags==1:             nav=t("pag_nav_unica")
        elif pag_idx==0:                nav=t("pag_nav_prox")
        elif pag_idx==total_pags-1:     nav=t("pag_nav_ant")
        else:                           nav=t("pag_nav_ambas")
        _ln(f"  {nav}"); fundo(); p()
        msg,erro=_get_flash()
        if msg: p(("  ✗ " if erro else "  ✓ ")+msg)
        cmd=inp(t("pag_cmd")).strip().lower()
        if   cmd in ("0",""): break
        elif cmd in ("p","d"):
            if pag_idx<total_pags-1: pag_idx+=1
            else: flash("Última página.")
        elif cmd in ("a","q"):
            if pag_idx>0: pag_idx-=1
            else: flash("Primeira página.")
        elif cmd=="n":
            try:
                num=int(inp(t("pag_ir_para",n=total_pags)).strip())
                if 1<=num<=total_pags: pag_idx=num-1
                else: flash(t("fora_intervalo"),erro=True)
            except ValueError: flash(t("so_numero"),erro=True)
        else: flash(t("invalido"),erro=True)

# ── Banco de dados ────────────────────────────────────
