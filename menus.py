"""Módulo refatorado do Gerenciador de Férias v3.9.1."""
import runtime
import database
import business
import dashboard
globals().update({k: v for k, v in vars(runtime).items() if not k.startswith("__")})
globals().update({k: v for k, v in vars(database).items() if not k.startswith("__")})
globals().update({k: v for k, v in vars(business).items() if not k.startswith("__")})
globals().update({k: v for k, v in vars(dashboard).items() if not k.startswith("__")})

def menu_setores(d):
    while True:
        _render_menu(t("set_titulo"),[(1,t("set_listar")),(2,t("set_novo")),(3,t("set_excluir")),(4,t("set_novo_sub")),(5,t("set_excluir_sub"))],rodape=[(0,t("voltar"))])
        op=inp(t("opcao")).strip()
        if   op=="1": listar_setores(d)
        elif op=="2": criar_setor(d)
        elif op=="3": excluir_setor(d)
        elif op=="4": criar_subsetor(d)
        elif op=="5": excluir_subsetor(d)
        elif op=="0": break
        else: flash(t("invalido"),erro=True)
def listar_setores(d):
    setores_ord=ord_setores(d)
    if not setores_ord:
        limpar(); titulo_box(t("set_titulo")); _lvz(); _ln("  "+t("nenhum_setor"),"center"); _lvz(); fundo(); pausar(); return
    def render(s):
        _lvz(); _ln(f"  {s}"); fs=[f for f in d["funcionarios"] if f["setor"]==s]; _ln(f"    {t('rel_total_func')}: {len(fs)}")
        subs=ord_subs(d,s)
        if subs:
            for j,sub in enumerate(subs,1): _ln(f"    {j}. {sub}")
        else: _ln("    "+t("sem_sub"))
    def resumo():
        _lnd(t("rel_set_cad"),str(len(setores_ord))); _lnd(t("rel_subs"),str(sum(len(d["setores"][s]["subsetores"]) for s in setores_ord)))
        _lnd(t("rel_total_func"),str(len(d["funcionarios"])))
    paginar(d, t("set_titulo"), setores_ord, render, resumo)
def criar_setor(d):
    limpar(); titulo_box(t("set_novo")); _lvz(); fundo(); p()
    nome=inp(t("set_nome")).strip()
    if not nome: flash(t("nome_vazio"),erro=True); return
    if nome in d["setores"]: flash(t("set_ja_existe"),erro=True); return
    d["setores"][nome]={"subsetores":[]}; salvar_dados(d); flash(f"'{nome}' — "+t("set_criado"))
def excluir_setor(d):
    limpar(); titulo_box(t("set_excluir")); _lvz(); fundo()
    if not d["setores"]: flash(t("nenhum_setor"),erro=True); return
    setor=sel_setor(d)
    if not setor: return
    vinc=[f for f in d["funcionarios"] if f["setor"]==setor]
    if vinc: flash(t("set_vinculados",n=len(vinc)),erro=True); return
    c=inp(t("confirmar_excl")).strip().lower()
    if c==t("sim"):
        del d["setores"][setor]; d["regras"]["por_setor"].pop(setor,None)
        for k in [k for k in d["regras"]["por_subsetor"] if k.startswith(setor+SEP)]: d["regras"]["por_subsetor"].pop(k,None)
        salvar_dados(d); flash(f"'{setor}' — "+t("set_excluido"))
    else: flash(t("excluir_cancel"))
def criar_subsetor(d):
    limpar(); titulo_box(t("set_novo_sub")); _lvz(); fundo()
    if not d["setores"]: flash(t("nenhum_setor"),erro=True); return
    setor=sel_setor(d)
    if not setor: return
    p(); nome=inp(f"{t('sub_nome')} ({setor}):").strip()
    if not nome: flash(t("nome_vazio"),erro=True); return
    if nome in d["setores"][setor]["subsetores"]: flash(t("sub_ja_existe"),erro=True); return
    d["setores"][setor]["subsetores"].append(nome); salvar_dados(d); flash(f"'{nome}' — "+t("sub_criado"))
def excluir_subsetor(d):
    limpar(); titulo_box(t("set_excluir_sub")); _lvz(); fundo()
    if not d["setores"]: flash(t("nenhum_setor"),erro=True); return
    setor=sel_setor(d)
    if not setor: return
    sub=sel_sub(d,setor)
    if not sub: return
    vinc=[f for f in d["funcionarios"] if f["setor"]==setor and f["subsetor"]==sub]
    if vinc: flash(t("set_vinculados",n=len(vinc)),erro=True); return
    c=inp(t("confirmar_excl")).strip().lower()
    if c==t("sim"):
        d["setores"][setor]["subsetores"].remove(sub); d["regras"]["por_subsetor"].pop(_chave_sub(setor,sub),None)
        salvar_dados(d); flash(f"'{sub}' — "+t("sub_excluido"))
    else: flash(t("excluir_cancel"))

# ── Vínculos ──────────────────────────────────────────
def menu_vinculos(d):
    while True:
        _render_menu(t("vin_titulo"),[(1,t("vin_listar")),(2,t("vin_novo")),(3,t("vin_excluir"))],rodape=[(0,t("voltar"))])
        op=inp(t("opcao")).strip()
        if   op=="1": listar_vinculos(d)
        elif op=="2": criar_vinculo(d)
        elif op=="3": excluir_vinculo(d)
        elif op=="0": break
        else: flash(t("invalido"),erro=True)
def listar_vinculos(d):
    vs=ord_vinculos(d)
    if not vs:
        limpar(); titulo_box(t("vin_titulo")); _lvz(); _ln("  "+t("nenhum_vinculo"),"center"); _lvz(); fundo(); pausar(); return
    paginar(d, t("vin_titulo"), vs, lambda v: _ln(f"  › {v}"))
def criar_vinculo(d):
    limpar(); titulo_box(t("vin_novo")); _lvz(); fundo(); p()
    nome=inp(t("vin_nome")).strip()
    if not nome: flash(t("nome_vazio"),erro=True); return
    if nome in d["vinculos"]: flash(t("vin_ja_existe"),erro=True); return
    d["vinculos"].append(nome); salvar_dados(d); flash(f"'{nome}' — "+t("vin_criado"))
def excluir_vinculo(d):
    limpar(); titulo_box(t("vin_excluir")); _lvz(); fundo()
    if not d["vinculos"]: flash(t("nenhum_vinculo"),erro=True); return
    v=sel_vinculo(d,permitir_nenhum=False)
    if not v: return
    em=[f for f in d["funcionarios"] if f.get("vinculo")==v]
    if em: flash(t("vin_em_uso",n=len(em)),erro=True); return
    c=inp(t("confirmar_excl")).strip().lower()
    if c==t("sim"):
        d["vinculos"].remove(v); d["regras"]["por_vinculo"].pop(v,None)
        salvar_dados(d); flash(f"'{v}' — "+t("vin_excluido"))
    else: flash(t("excluir_cancel"))

# ── Funcionários ──────────────────────────────────────
def menu_funcionarios(d):
    while True:
        _render_menu(t("fun_titulo"),[(1,t("fun_listar")),(2,t("fun_por_setor")),(3,t("fun_novo")),(4,t("fun_excluir")),(5,t("fun_vinculos"))],rodape=[(0,t("voltar"))])
        op=inp(t("opcao")).strip()
        if   op=="1": listar_funcionarios(d)
        elif op=="2": listar_funcionarios_por_setor(d)
        elif op=="3": cadastrar_funcionario(d)
        elif op=="4": excluir_funcionario(d)
        elif op=="5": menu_vinculos(d)
        elif op=="0": break
        else: flash(t("invalido"),erro=True)
def listar_funcionarios(d):
    funcs=ord_funcs(d)
    if not funcs:
        limpar(); titulo_box(t("fun_titulo")); _lvz(); _ln("  "+t("nenhum_func"),"center"); _lvz(); fundo(); pausar(); return
    cf=sum(1 for f in funcs if f["ferias"])
    def resumo(): _lnd(t("rel_total_func"),str(len(funcs))); _lnd(t("rel_com_ferias"),str(cf)); _lnd(t("rel_sem_ferias"),str(len(funcs)-cf))
    paginar(d, t("fun_titulo"), funcs, lambda func: _render_func_simples(func,d), resumo)
def listar_funcionarios_por_setor(d):
    setores_ord=ord_setores(d)
    if not setores_ord:
        limpar(); titulo_box(t("fun_por_setor")); _lvz(); _ln("  "+t("nenhum_setor"),"center"); _lvz(); fundo(); pausar(); return
    blocos=[{"setor":s,"subs":[{"sub":sub,"funcs":ord_funcs(d,[f for f in d["funcionarios"] if f["setor"]==s and f["subsetor"]==sub])} for sub in ord_subs(d,s)],"total":sum(1 for f in d["funcionarios"] if f["setor"]==s)} for s in setores_ord]
    tf=len(d["funcionarios"]); cf=sum(1 for f in d["funcionarios"] if f["ferias"])
    def resumo(): _lnd(t("rel_total_func"),str(tf)); _lnd(t("rel_com_ferias"),str(cf)); _lnd(t("rel_set_cad"),str(len(setores_ord)))
    def render_b(bloco):
        _lvz(); _ln(f"  ══  {bloco['setor']}  ({bloco['total']} func.)  ══")
        for sb in bloco["subs"]:
            fs_sub=sb["funcs"]; c_fer=sum(1 for f in fs_sub if f["ferias"])
            _lvz(); _ln(f"  +── {sb['sub']}"); _ln(f"      Func: {len(fs_sub)}  |  {t('rel_com_ferias')}: {c_fer}  |  {t('rel_sem_ferias')}: {len(fs_sub)-c_fer}")
            _dleve()
            if not fs_sub: _ln("      "+t("sem_func"))
            else:
                for func in fs_sub:
                    v=f" [{func.get('vinculo','')}]" if func.get("vinculo") else ""
                    _ln(f"      › {func['nome']}{v}"); _ln(_linha_periodo_atual(func,d))
                    pas,atu,fut=classificar_ferias(func)
                    if atu: _ln(f"        Em férias: {atu[0]['inicio']} até {atu[0]['fim']}")
                    elif fut: _ln(f"        Próximo: {fut[0]['inicio']} até {fut[0]['fim']}")
    paginar(d, t("fun_por_setor"), blocos, render_b, resumo)
def cadastrar_funcionario(d):
    limpar(); titulo_box(t("fun_novo")); _lvz(); fundo()
    if not d["setores"]: flash(t("nenhum_setor"),erro=True); return
    setor=sel_setor(d)
    if not setor: return
    sub=sel_sub(d,setor)
    if not sub: return
    p(); p("  "+t("fun_vinculo_sel"))
    vinculo=sel_vinculo(d,permitir_nenhum=True)
    p(); nome=inp(t("fun_nome")).strip()
    if not nome: flash(t("nome_vazio"),erro=True); return
    if any(f["nome"].lower()==nome.lower() and f["setor"]==setor and f["subsetor"]==sub for f in d["funcionarios"]):
        flash(t("fun_ja_existe"),erro=True); return
    adm=inp(f"{t('data_admissao')} (DD/MM/AAAA ou ENTER para pular):").strip()
    if adm and not conv_data(adm): flash(t("admissao_inv"),erro=True); return
    d["funcionarios"].append({"nome":nome,"setor":setor,"subsetor":sub,"vinculo":vinculo or "","data_admissao":adm,"ferias":[]})
    salvar_dados(d); flash(f"'{nome}' — "+t("fun_criado"))
def excluir_funcionario(d):
    limpar(); titulo_box(t("fun_excluir")); _lvz(); fundo()
    func=sel_func(d)
    if not func: return
    p(); p(f"  {func['nome']} ({func['setor']} → {func['subsetor']})")
    c=inp(t("confirmar_excl")).strip().lower()
    if c==t("sim"):
        d["funcionarios"].remove(func); salvar_dados(d); flash(f"'{func['nome']}' — "+t("fun_excluido"))
    else: flash(t("excluir_cancel"))

# ── Férias ────────────────────────────────────────────
def menu_ferias(d):
    while True:
        _render_menu(t("fer_titulo"),[(1,t("fer_agendar")),(2,t("fer_cancelar")),(3,t("fer_calendario"))],rodape=[(0,t("voltar"))])
        op=inp(t("opcao")).strip()
        if   op=="1": agendar_ferias(d)
        elif op=="2": cancelar_ferias(d)
        elif op=="3": ver_calendario(d)
        elif op=="0": break
        else: flash(t("invalido"),erro=True)
def agendar_ferias(d):
    limpar(); titulo_box(t("fer_agendar")); _lvz(); fundo()
    func=sel_func(d)
    if not func: return
    v=f" [{func.get('vinculo','')}]" if func.get("vinculo") else ""
    p(); p(f"  {func['nome']}{v}  ({func['setor']} → {func['subsetor']})"); p()
    ini_s=inp(t("fer_inicio")).strip(); fim_s=inp(t("fer_fim")).strip()
    ini=conv_data(ini_s); fim=conv_data(fim_s)
    if not ini or not fim: flash(t("fer_data_inv"),erro=True); return
    if ini>fim: flash(t("fer_data_ord"),erro=True); return
    erros=validar_agendamento(d,func,ini,fim)
    if erros:
        limpar(); titulo_box(t("fer_bloqueado")); _lvz()
        for i,e in enumerate(erros,1): _ln(f"  {i}. {e}")
        _lvz(); fundo(); pausar(); return
    venda=False
    if obter_regra(d,"permite_venda_ferias",func["setor"],func["subsetor"],func.get("vinculo","")):
        p(); p("  "+t("fer_venda_info"))
        venda=inp(t("fer_venda_marcar")).strip().lower()==t("sim")
    func["ferias"].append({"inicio":ini_s,"fim":fim_s,"venda_ferias":venda})
    salvar_dados(d)
    an=analise_periodo_atual(d,func)
    if an["tipo"]=="aquisitivo": label=f"Prd.{an['numero']}: {an['tirados']} {t('pa_dias')} tirados"
    else:                        label=f"Ano {an['ano_civil']}: {an['tirados']} {t('pa_dias')} tirados"
    flash(f"{func['nome']}: {ini_s} → {fim_s}  |  {label} — "+t("fer_ok"))
def cancelar_ferias(d):
    limpar(); titulo_box(t("fer_cancelar")); _lvz(); fundo()
    func=sel_func(d)
    if not func: return
    if not func["ferias"]: flash(f"{func['nome']} {t('fer_sem')}",erro=True); return
    pas,atu,fut=classificar_ferias(func); ferias_ord=ord_ferias(d,list(func["ferias"]))
    def render_f(f):
        dias=calc_dias(f["inicio"],f["fim"]); vd=" "+t("fer_venda_lbl") if f.get("venda_ferias") else ""
        ini=conv_data(f["inicio"]); hoje=datetime.today()
        cat=f"[{t('rel_andamento')}]" if ini and ini<=hoje<=conv_data(f["fim"]) else (f"[{t('rel_futuro')}]" if ini and ini>hoje else f"[{t('rel_concluido')}]")
        _ln(f"  {f['inicio']}  até  {f['fim']}  ({dias} {t('pa_dias')}){vd}  {cat}")
    def resumo():
        _lnd(t("fun_lista")[:-1], func["nome"])
        _lnd(t("rel_andamento"),  str(len(atu))+" período(s)" if atu else "—")
        _lnd(t("periodos_futuros"),str(len(fut))+" período(s)" if fut else "—")
        _lnd(t("periodos_passados"),str(len(pas))+" período(s)" if pas else "—")
    paginar(d, t("fer_cancelar"), ferias_ord, render_f, resumo)
    p(); p("  Informe o número do período a cancelar:")
    for i,f in enumerate(ferias_ord,1): p(f"    {i}. {f['inicio']} até {f['fim']}  ({calc_dias(f['inicio'],f['fim'])} {t('pa_dias')})")
    p(f"    0. {t('voltar')}")
    try:
        e=int(inp(t("fer_remover_num")))
        if e==0: return
        idx=e-1
        if 0<=idx<len(ferias_ord):
            rm=ferias_ord[idx]
            func["ferias"]=[f for f in func["ferias"] if not (f["inicio"]==rm["inicio"] and f["fim"]==rm["fim"])]
            salvar_dados(d); flash(f"{rm['inicio']} → {rm['fim']} — "+t("fer_removida"))
        else: flash(t("fora_intervalo"),erro=True)
    except ValueError: flash(t("so_numero"),erro=True)
def ver_calendario(d):
    setores_ord=ord_setores(d)
    if not setores_ord:
        limpar(); titulo_box(t("fer_cal_titulo")); _lvz(); _ln("  "+t("nenhum_setor"),"center"); _lvz(); fundo(); pausar(); return
    blocos=[{"setor":s,"subs":[{"sub":sub,"funcs":ord_funcs(d,[f for f in d["funcionarios"] if f["setor"]==s and f["subsetor"]==sub])} for sub in ord_subs(d,s)]} for s in setores_ord]
    def render_cal(bloco):
        _lvz(); _ln(f"  {bloco['setor']}")
        for sb in bloco["subs"]:
            _ln(f"  +── {sb['sub']}")
            if not sb["funcs"]: _ln("       "+t("sem_func"))
            else:
                for func in sb["funcs"]:
                    pas,atu,fut=classificar_ferias(func); v=f" [{func.get('vinculo','')}]" if func.get("vinculo") else ""
                    if atu: f0=atu[0]; vd=" "+t("fer_venda_lbl") if f0.get("venda_ferias") else ""; _ln(f"       [ANDAMENTO] {func['nome']}{v}: {f0['inicio']} até {f0['fim']}{vd}")
                    elif fut: f0=fut[0]; vd=" "+t("fer_venda_lbl") if f0.get("venda_ferias") else ""; _ln(f"       [FUTURO] {func['nome']}{v}: {f0['inicio']} até {f0['fim']}{vd}")
                    elif pas: _ln(f"       [CONCLUÍDO] {func['nome']}{v}: último {pas[-1]['inicio']} até {pas[-1]['fim']}")
                    else: _ln(f"       {func['nome']}{v}: {t('sem_ferias')}")
    paginar(d, t("fer_cal_titulo"), blocos, render_cal)

# ══════════════════════════════════════════════════════
#  RELATÓRIOS
# ══════════════════════════════════════════════════════
def menu_relatorios(d):
    while True:
        _render_menu(t("rel_titulo"),[
            (1,  t("rel_pa_menu")),
            (2,  t("rel_saldo")),
            (3,  t("rel_individual")),
            (4,  t("rel_multi")),
            (5,  t("rel_periodo")),
            (6,  t("rel_geral")),
            (7,  t("rel_setor")),
            (8,  t("rel_sub")),
            (9,  t("rel_situacao")),
            (10, t("rel_vencidas")),
            (11, t("rel_ano")),
        ], rodape=[(0, t("voltar"))])
        op=inp(t("opcao")).strip()
        if   op=="1":  rel_por_periodo_aquisitivo(d)
        elif op=="2":  rel_saldo_dias(d)
        elif op=="3":  rel_individual(d)
        elif op=="4":  rel_multiplos_funcionarios(d)
        elif op=="5":  rel_periodo(d)
        elif op=="6":  rel_geral(d)
        elif op=="7":  rel_setor(d)
        elif op=="8":  rel_sub(d)
        elif op=="9":  rel_situacao(d)
        elif op=="10": rel_vencidas(d)
        elif op=="11": rel_por_ano_civil(d)
        elif op=="0":  break
        else: flash(t("invalido"),erro=True)

def rel_por_periodo_aquisitivo(d):
    limpar(); titulo_box(t("rel_pa_titulo")); _lvz()
    _ln(f"  {t('rel_pa_filtro')}")
    _dleve()
    _ln(f"  1. {t('rel_pa_todos')}"); _ln(f"  2. {t('rel_pa_setor')}")
    _ln(f"  3. {t('rel_pa_sub')}");  _ln(f"  4. {t('rel_pa_func')}")
    _dleve(); _ln(f"  0. {t('cancelar')}"); fundo(); p()
    op=inp(t("opcao")).strip(); filtro_label=""; funcs_base=[]
    if op=="0": return
    elif op=="1": funcs_base=ord_funcs(d); filtro_label=t("rel_pa_todos")
    elif op=="2":
        setor=sel_setor(d)
        if not setor: return
        funcs_base=ord_funcs(d,[f for f in d["funcionarios"] if f["setor"]==setor]); filtro_label=f"{t('rel_pa_setor')}: {setor}"
    elif op=="3":
        setor=sel_setor(d)
        if not setor: return
        sub=sel_sub(d,setor)
        if not sub: return
        funcs_base=ord_funcs(d,[f for f in d["funcionarios"] if f["setor"]==setor and f["subsetor"]==sub]); filtro_label=f"{setor} → {sub}"
    elif op=="4":
        func=sel_func(d)
        if not func: return
        funcs_base=[func]; filtro_label=func["nome"]
    else: flash(t("invalido"),erro=True); return
    if not funcs_base: flash(t("nenhum_func"),erro=True); return
    hoje=datetime.today()
    def resumo():
        _lnd(t("rel_data"),           hoje.strftime("%d/%m/%Y %H:%M"))
        _lnd(t("rel_pa_filtro")[:-1], filtro_label)
        _lnd(t("rel_total_func"),     str(len(funcs_base)))
        n_adm=sum(1 for f in funcs_base if f.get("data_admissao",""))
        _lnd(t("pa_atual"),           f"{n_adm} com data de admissão  |  {len(funcs_base)-n_adm} sem")
    def render_pa(func):
        an=analise_periodo_atual(d,func); pas,atu,fut=classificar_ferias(func)
        v=f" [{func.get('vinculo','')}]" if func.get("vinculo") else ""
        _dleve(); _ln(f"  {func['nome']}{v}","center"); _dleve()
        _ln(f"  {t('rel_setor_l')}: {func['setor']}  |  {t('rel_sub_l')}: {func['subsetor']}")
        if func.get("data_admissao"): _ln(f"  {t('data_admissao')} {func['data_admissao']}")
        _lvz()
        if an["tipo"]=="aquisitivo":
            ini_s=an["ini"].strftime("%d/%m/%Y"); fim_s=(an["fim"]-timedelta(days=1)).strftime("%d/%m/%Y")
            _ln(f"  [{t('pa_atual')} #{an['numero']}]  {ini_s} → {fim_s}")
        else: _ln(f"  [Ano civil {an['ano_civil']}  {t('pa_sem_admissao')}]")
        if an["max_dias"] and an["max_dias"]>0:
            bp=_barra_progresso(an["tirados"],an["max_dias"])
            if bp: barra,pct=bp; _ln(f"    {t('pa_tirados')}  : {an['tirados']:>3} / {an['max_dias']} {t('pa_dias')}"); _ln(f"    {t('pa_restantes')}: {an['restantes']:>3} {t('pa_dias')}"); _ln(f"    {t('pa_progresso')}: [{barra}] {pct}%")
        else: _ln(f"    {t('pa_tirados')}: {an['tirados']} {t('pa_dias')}  ({t('pa_ilimitado')})")
        if an["tipo"]=="aquisitivo": ferias_prd=ferias_no_periodo(func["ferias"],an["ini"],an["fim"])
        else: ferias_prd=ferias_no_ano_civil(func["ferias"],an.get("ano_civil",datetime.today().year))
        if ferias_prd:
            _lvz(); _ln(f"  [Férias no período ({len(ferias_prd)} registro(s))]")
            for f in sorted(ferias_prd,key=lambda x:conv_data(x["inicio"]) or datetime.min):
                dias=calc_dias(f["inicio"],f["fim"]); vd=" "+t("fer_venda_lbl") if f.get("venda_ferias") else ""
                ini=conv_data(f["inicio"])
                if ini and ini<=hoje<=conv_data(f["fim"]): cat=f"[{t('rel_andamento')}]"
                elif ini and ini>hoje:                      cat=f"[{t('rel_futuro')}]"
                else:                                       cat=f"[{t('rel_concluido')}]"
                _ln(f"    {cat} {f['inicio']} até {f['fim']}  ({dias} {t('pa_dias')}){vd}")
        elif not func["ferias"]: _lvz(); _ln("    "+t("sem_ferias"))
        else: _lvz(); _ln(f"    (sem férias no período aquisitivo atual)")
        if fut:
            fut_fora=[f for f in fut if an["tipo"]!="aquisitivo" or conv_data(f["inicio"])>=an["fim"]]
            if fut_fora:
                _lvz(); _ln(f"  [{t('periodos_futuros')} fora do prd. atual: {len(fut_fora)}]")
                for f in fut_fora[:3]:
                    dias=calc_dias(f["inicio"],f["fim"]); _ln(f"    • {f['inicio']} até {f['fim']}  ({dias} {t('pa_dias')})")
        _lvz()
    paginar(d, f"{t('rel_pa_titulo')}  |  {filtro_label}", funcs_base, render_pa, resumo)

def rel_saldo_dias(d):
    limpar(); titulo_box(t("rel_saldo_titulo")); _lvz()
    _ln("  Filtrar por:")
    _dleve()
    _ln(f"  1. {t('rel_saldo_todos')}"); _ln(f"  2. {t('rel_saldo_setor')}"); _ln(f"  3. {t('rel_saldo_sub')}")
    _dleve(); _ln(f"  0. {t('cancelar')}"); fundo(); p()
    op=inp(t("opcao")).strip(); filtro_label=""; funcs_base=[]
    if op=="0": return
    elif op=="1": funcs_base=ord_funcs(d); filtro_label=t("rel_saldo_todos")
    elif op=="2":
        setor=sel_setor(d)
        if not setor: return
        funcs_base=ord_funcs(d,[f for f in d["funcionarios"] if f["setor"]==setor]); filtro_label=f"Setor: {setor}"
    elif op=="3":
        setor=sel_setor(d)
        if not setor: return
        sub=sel_sub(d,setor)
        if not sub: return
        funcs_base=ord_funcs(d,[f for f in d["funcionarios"] if f["setor"]==setor and f["subsetor"]==sub]); filtro_label=f"{setor} → {sub}"
    else: flash(t("invalido"),erro=True); return
    if not funcs_base: flash(t("nenhum_func"),erro=True); return
    registros=[]
    for func in funcs_base:
        an=analise_periodo_atual(d,func); tirados=an["tirados"]; max_d=an["max_dias"]; restantes=an["restantes"]
        excedido=(max_d and max_d>0 and tirados>max_d)
        registros.append({"func":func,"an":an,"tirados":tirados,"max_d":max_d,"restantes":restantes,"excedido":excedido})
    def _sk(r):
        if r["excedido"]: return (0,r["tirados"])
        if r["restantes"] is not None: return (1,r["restantes"])
        return (2,0)
    registros.sort(key=_sk)
    n_exc=sum(1 for r in registros if r["excedido"]); n_ok=sum(1 for r in registros if not r["excedido"] and r["restantes"] is not None)
    tot=sum(r["tirados"] for r in registros)
    def resumo():
        _lnd(t("rel_data"),             datetime.today().strftime("%d/%m/%Y %H:%M"))
        _lnd("Filtro",                  filtro_label)
        _lnd(t("rel_saldo_tot_func"),   str(len(registros)))
        _lnd(t("rel_saldo_excedidos"),  str(n_exc)+" funcionário(s)")
        _lnd(t("rel_saldo_sem_saldo"),  str(n_ok)+" funcionário(s)")
        _lnd(t("rel_saldo_total_dias"), f"{tot} {t('pa_dias')}")
    def render_saldo(reg):
        func=reg["func"]; an=reg["an"]; tirados=reg["tirados"]; max_d=reg["max_d"]; restantes=reg["restantes"]; excedido=reg["excedido"]
        v=f" [{func.get('vinculo','')}]" if func.get("vinculo") else ""
        if excedido:                                             icone="[✗]"
        elif restantes is not None and restantes==0:             icone="[=]"
        elif restantes is not None and restantes<=5:             icone="[!]"
        else:                                                    icone="[✓]"
        _lvz(); _ln(f"  {icone} {func['nome']}{v}")
        _ln(f"       {func['setor']}  →  {func['subsetor']}")
        if an["tipo"]=="aquisitivo":
            ini_s=an["ini"].strftime("%d/%m/%Y"); fim_s=(an["fim"]-timedelta(days=1)).strftime("%d/%m/%Y")
            _ln(f"       Prd.{an['numero']}: {ini_s} → {fim_s}")
        else: _ln(f"       Ano civil {an['ano_civil']}  ({t('rel_saldo_usando')})")
        if max_d and max_d>0:
            saldo_str=f"-{tirados-max_d}" if excedido else str(restantes)
            status_str=t("rel_saldo_neg") if excedido else t("rel_saldo_ok")
            bp=_barra_progresso(tirados,max_d,20)
            if bp: barra,pct=bp; _ln(f"       Tirados: {tirados:>3}  |  Limite: {max_d}  |  Saldo: {saldo_str}  |  {status_str}"); _ln(f"       [{barra}] {pct}%")
        else: _ln(f"       Tirados: {tirados}  |  Limite: {t('rel_saldo_sem_lim')}")
    paginar(d, f"{t('rel_saldo_titulo')}  |  {filtro_label}", registros, render_saldo, resumo)

def rel_individual(d):
    if not d["funcionarios"]: flash(t("nenhum_func"),erro=True); return
    limpar(); titulo_box(t("rel_individual_t")); _lvz(); fundo()
    func=sel_func(d)
    if not func: return
    an=analise_periodo_atual(d,func); tot,_,__=_status_ferias(func); per=calc_periodos_aquisitivos(func)
    def resumo():
        _lnd(t("rel_data"),    datetime.today().strftime("%d/%m/%Y %H:%M"))
        _lnd(t("rel_nome"),    func["nome"]); _lnd(t("rel_vinculo"),func.get("vinculo","—") or "—")
        _lnd(t("rel_setor_l"), func["setor"]); _lnd(t("rel_sub_l"),func["subsetor"])
        if func.get("data_admissao"): _lnd(t("data_admissao"),func["data_admissao"])
        _lnd(t("rel_periodos"),str(len(func["ferias"]))); _lnd(t("rel_tot_dias"),f"{tot} {t('pa_dias')} (histórico total)")
        if an["tipo"]=="aquisitivo":
            ini_s=an["ini"].strftime("%d/%m/%Y"); fim_s=(an["fim"]-timedelta(days=1)).strftime("%d/%m/%Y")
            _lnd(t("pa_atual")+f" #{an['numero']}", f"{ini_s} → {fim_s}")
            if an["max_dias"] and an["max_dias"]>0:
                bp=_barra_progresso(an["tirados"],an["max_dias"])
                if bp: barra,pct=bp; _lnd(t("pa_tirados"),f"{an['tirados']}/{an['max_dias']} {t('pa_dias')}  [{barra}] {pct}%  Restam: {an['restantes']}")
            else: _lnd(t("pa_tirados"),f"{an['tirados']} {t('pa_dias')}  ({t('pa_ilimitado')})")
        else: _lnd(f"Ano civil {an['ano_civil']}", f"{an['tirados']} {t('pa_dias')}  {t('pa_sem_admissao')}")
    itens=[]
    for pp in per: itens.append({"tipo":"aq","pp":pp})
    hoje=datetime.today()
    for i,f in enumerate(ord_ferias(d,list(func["ferias"])),1): itens.append({"tipo":"fer","f":f,"idx":i})
    if not itens:
        limpar(); titulo_box(f"{t('rel_individual_t')}: {func['nome']}")
        for item in _capturar(resumo): _print_buf(item)
        _dleve(); _lvz(); _ln("  "+t("sem_ferias"),"center"); _lvz(); fundo(); pausar(); return
    def render_item(item):
        if item["tipo"]=="aq":
            pp=item["pp"]; s_txt={"ok":t("ferias_em_dia"),"vencida":t("ferias_vencidas"),"a_vencer":t("ferias_a_vencer"),"pendente":t("ferias_pendentes")}.get(pp["status"],pp["status"])
            fim_s=(pp["fim_aq"]-timedelta(days=1)).strftime("%d/%m/%Y")
            _lvz(); _ln(f"  [Prd.Aquisitivo] {pp['ini_aq'].strftime('%d/%m/%Y')} – {fim_s}")
            _ln(f"    Concessivo até: {pp['fim_con'].strftime('%d/%m/%Y')}  |  Status: {s_txt}")
            _ln(f"    Dias tirados no período: {pp['dias_tirados']}")
            if pp["status"]=="a_vencer": _ln(f"    ⚠ Vence em {(pp['fim_con']-hoje).days} {t('dias_para_vencer')}")
            elif pp["status"]=="vencida": _ln(f"    ✗ {t('vencida_em')}: {pp['fim_con'].strftime('%d/%m/%Y')}")
        else:
            f=item["f"]; dias=calc_dias(f["inicio"],f["fim"]); ini=conv_data(f["inicio"]); fim=conv_data(f["fim"])
            if ini and ini<=hoje<=fim: est=t("rel_andamento")
            elif ini and ini>hoje:     est=t("rel_futuro")
            else:                      est=t("rel_concluido")
            vd=" "+t("fer_venda_lbl") if f.get("venda_ferias") else ""
            _lvz(); _ln(f"  {t('rel_periodos')} {item['idx']}:  [{est}]")
            _ln(f"    {t('rel_inicio')}: {f['inicio']}  |  {t('rel_termino')}: {f['fim']}")
            _ln(f"    {t('rel_dias')}: {dias} {t('pa_dias')}{vd}")
    paginar(d, f"{t('rel_individual_t')}: {func['nome']}", itens, render_item, resumo)

def _tela_selecao_funcionarios(d):
    selecionados=[]
    while True:
        limpar(); titulo_box(t("rel_multi_titulo")); _lvz()
        _ln(f"  {t('rel_multi_lista')}  ({len(selecionados)} {t('rel_selecionados')})")
        _dleve()
        if not selecionados: _ln(f"  — {t('rel_multi_vazio')} —","center")
        else:
            for i,func in enumerate(selecionados,1):
                v=f" [{func.get('vinculo','')}]" if func.get("vinculo") else ""
                _ln(f"  {i}. {func['nome']}{v}  ({func['setor']} → {func['subsetor']})")
                _ln(_linha_periodo_atual(func,d))
        _lvz(); _dleve(); _ln(f"  {t('rel_multi_gerenciar')}"); fundo()
        msg,erro=_get_flash()
        if msg: p(("  ✗ " if erro else "  ✓ ")+msg)
        p(); cmd=inp(t("opcao")).strip().lower()
        if cmd=="a":
            todos=ord_funcs(d); ids_sel={f.get("_id") for f in selecionados}
            limpar(); titulo_box(t("rel_multi_titulo")); _lvz()
            for i,func in enumerate(todos,1):
                v=f" [{func.get('vinculo','')}]" if func.get("vinculo") else ""; mrk=" ✓" if func.get("_id") in ids_sel else ""
                _ln(f"  {i}. {func['nome']}{v}  ({func['setor']} → {func['subsetor']}){mrk}")
            _lvz(); _dleve(); _ln(f"  0. {t('voltar')}  |  * = selecionar todos"); fundo(); p()
            entrada=inp(t("opcao")).strip().lower()
            if entrada=="0": continue
            elif entrada=="*":
                ads=0
                for func in todos:
                    if func.get("_id") not in ids_sel: selecionados.append(func); ads+=1
                flash(f"{ads} adicionado(s).")
            else:
                try:
                    nums=[int(x.strip()) for x in entrada.replace(","," ").split() if x.strip()]; ads=0
                    for num in nums:
                        if 1<=num<=len(todos):
                            func=todos[num-1]
                            if func.get("_id") in {f.get("_id") for f in selecionados}: flash(t("rel_multi_dup"),erro=True)
                            else: selecionados.append(func); ads+=1
                        else: flash(t("fora_intervalo"),erro=True)
                    if ads: flash(f"{ads} adicionado(s).")
                except ValueError: flash(t("so_numero"),erro=True)
        elif cmd=="r":
            if not selecionados: flash(t("rel_multi_vazio"),erro=True); continue
            limpar(); titulo_box(t("rel_multi_titulo")); _lvz()
            for i,func in enumerate(selecionados,1):
                v=f" [{func.get('vinculo','')}]" if func.get("vinculo") else ""; _ln(f"  {i}. {func['nome']}{v}")
            _lvz(); _dleve(); _ln(f"  0. {t('cancelar')}  |  * = limpar tudo"); fundo(); p()
            entrada=inp(t("opcao")).strip().lower()
            if entrada=="0": continue
            elif entrada=="*": selecionados.clear(); flash("Seleção limpa.")
            else:
                try:
                    nums=sorted(set(int(x.strip()) for x in entrada.replace(","," ").split() if x.strip()),reverse=True); rm=0
                    for num in nums:
                        if 1<=num<=len(selecionados): selecionados.pop(num-1); rm+=1
                    flash(f"{rm} removido(s).")
                except ValueError: flash(t("so_numero"),erro=True)
        elif cmd=="g":
            if not selecionados: flash(t("rel_multi_vazio"),erro=True); continue
            return selecionados
        elif cmd in ("0",""): return []
        else: flash(t("invalido"),erro=True)

def rel_multiplos_funcionarios(d):
    if not d["funcionarios"]: flash(t("nenhum_func"),erro=True); return
    selecionados=_tela_selecao_funcionarios(d)
    if not selecionados: flash(t("rel_multi_vazio")); return
    n=len(selecionados); n_venc=sum(1 for f in selecionados if situacao_geral_func(f)=="vencida")
    n_atu=sum(1 for f in selecionados if classificar_ferias(f)[1]); n_fut=sum(1 for f in selecionados if classificar_ferias(f)[2])
    tot=sum(analise_periodo_atual(d,f)["tirados"] for f in selecionados)
    def resumo():
        _lnd(t("rel_data"),       datetime.today().strftime("%d/%m/%Y %H:%M"))
        _lnd(t("rel_total_func"), str(n)); _lnd(t("pa_tirados")+" (prd.atual total)",f"{tot} {t('pa_dias')}")
        _lnd(t("rel_andamento"),  str(n_atu)+" em férias agora"); _lnd(t("periodos_futuros"),str(n_fut)+" com férias agendadas")
        if n_venc: _lnd(t("ferias_vencidas"),str(n_venc)+" funcionário(s) com férias vencidas")
    paginar(d, f"{t('rel_multi_titulo')}  ({n} {t('rel_selecionados')})", selecionados, lambda func: _render_func_individual(func,d), resumo)

def rel_geral(d):
    setores_ord=ord_setores(d); tf=len(d["funcionarios"]); tc=sum(1 for f in d["funcionarios"] if f["ferias"])
    def resumo():
        _lnd(t("rel_data"),      datetime.today().strftime("%d/%m/%Y %H:%M"))
        _lnd(t("rel_set_cad"),   str(len(setores_ord))); _lnd(t("rel_subs"),str(sum(len(v["subsetores"]) for v in d["setores"].values())))
        _lnd(t("rel_total_func"),str(tf)); _lnd(t("rel_com_ferias"),str(tc)); _lnd(t("rel_sem_ferias"),str(tf-tc))
    def render_s(setor):
        fs=ord_funcs(d,[f for f in d["funcionarios"] if f["setor"]==setor])
        _lvz(); _ln(f"  ══  {setor}  ══"); _ln(f"  Func: {len(fs)}  |  Dias: {sum(_status_ferias(f)[0] for f in fs)} {t('pa_dias')} (histórico)")
        for sub in ord_subs(d,setor):
            fsub=ord_funcs(d,[f for f in fs if f["subsetor"]==sub])
            _lvz(); _ln(f"  +── {sub}  ({len(fsub)} func.)"); _dleve()
            if not fsub: _ln("      "+t("sem_func"))
            else:
                for func in fsub: _render_func_individual(func,d)
    paginar(d, t("rel_geral"), setores_ord, render_s, resumo)

def rel_setor(d):
    limpar(); titulo_box(t("rel_setor")); _lvz(); fundo()
    setor=sel_setor(d)
    if not setor: return
    fs=ord_funcs(d,[f for f in d["funcionarios"] if f["setor"]==setor]); info=d["setores"][setor]
    def resumo():
        _lnd(t("rel_data"),      datetime.today().strftime("%d/%m/%Y %H:%M"))
        _lnd(t("rel_setor_l"),   setor); _lnd(t("rel_subs"),str(len(info["subsetores"])))
        _lnd(t("rel_total_func"),str(len(fs))); _lnd(t("rel_tot_dias"),str(sum(_status_ferias(f)[0] for f in fs))+" "+t("pa_dias")+" (histórico)")
    def render_sub(sub):
        fsub=ord_funcs(d,[f for f in fs if f["subsetor"]==sub])
        _lvz(); _ln(f"  +── {sub}  ({len(fsub)} func.)"); _dleve()
        if not fsub: _ln("      "+t("sem_func"))
        else:
            for func in fsub: _render_func_individual(func,d)
    paginar(d, f"{t('rel_setor')}: {setor}", ord_subs(d,setor), render_sub, resumo)

def rel_sub(d):
    limpar(); titulo_box(t("rel_sub")); _lvz(); fundo()
    setor=sel_setor(d)
    if not setor: return
    sub=sel_sub(d,setor)
    if not sub: return
    fsub=ord_funcs(d,[f for f in d["funcionarios"] if f["setor"]==setor and f["subsetor"]==sub])
    c=sum(1 for f in fsub if f["ferias"])
    def resumo():
        _lnd(t("rel_data"),      datetime.today().strftime("%d/%m/%Y %H:%M"))
        _lnd(t("rel_setor_l"),   setor); _lnd(t("rel_sub_l"),sub)
        _lnd(t("rel_total_func"),str(len(fsub))); _lnd(t("rel_com_ferias"),str(c)); _lnd(t("rel_sem_ferias"),str(len(fsub)-c))
        _lnd(t("rel_tot_dias"),  str(sum(_status_ferias(f)[0] for f in fsub))+" "+t("pa_dias")+" (histórico)")
    paginar(d, f"{t('rel_sub')}: {sub}", fsub, lambda func: _render_func_individual(func,d), resumo)

def rel_periodo(d):
    limpar(); titulo_box(t("rel_periodo")); _lvz(); _ln("  "+t("rel_interv")); _lvz(); fundo(); p()
    ini_s=inp(t("fer_inicio")).strip(); fim_s=inp(t("fer_fim")).strip()
    ini=conv_data(ini_s); fim=conv_data(fim_s)
    if not ini or not fim: flash(t("fer_data_inv"),erro=True); return
    if ini>fim: flash(t("fer_data_ord"),erro=True); return
    resultado=[]
    for func in d["funcionarios"]:
        pok=[f for f in func["ferias"] if conv_data(f["inicio"]) and conv_data(f["fim"]) and sobrepoem(ini,fim,conv_data(f["inicio"]),conv_data(f["fim"]))]
        if pok: resultado.append({"func":func,"periodos":pok})
    if not resultado:
        limpar(); titulo_box(t("rel_periodo")); _lvz()
        _lnd(t("rel_periodo_c"),f"{ini_s}  até  {fim_s}"); _lnd(t("rel_encontrados"),"0"); _dleve()
        _lvz(); _ln("  "+t("rel_nenhum_p"),"center"); _lvz(); fundo(); pausar(); return
    tot_g=sum(calc_dias(f["inicio"],f["fim"]) for r in resultado for f in r["periodos"])
    def resumo():
        _lnd(t("rel_data"),       datetime.today().strftime("%d/%m/%Y %H:%M"))
        _lnd(t("rel_periodo_c"),  f"{ini_s}  até  {fim_s}")
        _lnd(t("rel_encontrados"),str(len(resultado))); _lnd(t("rel_tot_per"),f"{tot_g} {t('pa_dias')}")
    def render_r(r):
        func=r["func"]; v=f" [{func.get('vinculo','')}]" if func.get("vinculo") else ""
        _lvz(); _ln(f"  › {func['nome']}{v}  ({func['setor']} → {func['subsetor']})")
        for i,f in enumerate(ord_ferias(d,list(r["periodos"])),1):
            dias=calc_dias(f["inicio"],f["fim"]); ie=max(ini,conv_data(f["inicio"])); fe=min(fim,conv_data(f["fim"]))
            deff=(fe-ie).days+1; vd=" "+t("fer_venda_lbl") if f.get("venda_ferias") else ""
            _ln(f"    {i}. {f['inicio']} até {f['fim']}  ({dias} {t('pa_dias')} | {deff} {t('rel_dias_per')}){vd}")
    paginar(d, t("rel_periodo"), resultado, render_r, resumo)

def rel_situacao(d):
    funcs=ord_funcs(d)
    if not funcs:
        limpar(); titulo_box(t("rel_sit_titulo")); _lvz(); _ln("  "+t("nenhum_func"),"center"); _lvz(); fundo(); pausar(); return
    itens=[{"func":f,"periodos":calc_periodos_aquisitivos(f),"status":situacao_geral_func(f),"an":analise_periodo_atual(d,f)} for f in funcs]
    pri={"vencida":4,"a_vencer":3,"pendente":2,"sem_admissao":1,"ok":0}
    itens.sort(key=lambda x:pri.get(x["status"],0),reverse=True)
    n_venc=sum(1 for i in itens if i["status"]=="vencida"); n_atenc=sum(1 for i in itens if i["status"]=="a_vencer"); n_ok=sum(1 for i in itens if i["status"]=="ok")
    def resumo():
        _lnd(t("rel_data"),       datetime.today().strftime("%d/%m/%Y %H:%M"))
        _lnd(t("rel_total_func"), str(len(itens))); _lnd(t("ferias_vencidas"),str(n_venc)+" func.")
        _lnd(t("ferias_a_vencer"),str(n_atenc)+" func."); _lnd(t("ferias_em_dia"),str(n_ok)+" func.")
    def render_sit(item):
        func=item["func"]; per=item["periodos"]; an=item["an"]; sit=item["status"]
        v=f" [{func.get('vinculo','')}]" if func.get("vinculo") else ""
        ico={"vencida":"[!] ","a_vencer":"[~] ","pendente":"[?] ","ok":"[✓] ","sem_admissao":"[–] "}.get(sit,"    ")
        _lvz(); _ln(f"  {ico}{func['nome']}{v}"); _ln(f"    {func['setor']}  →  {func['subsetor']}")
        _ln(_linha_periodo_atual(func,d))
        for pp in per:
            if pp["status"]=="vencida":
                fim_s=(pp["fim_aq"]-timedelta(days=1)).strftime("%d/%m/%Y")
                _ln(f"    VENCIDA: {pp['ini_aq'].strftime('%d/%m/%Y')} – {fim_s}  ({t('vencida_em')}: {pp['fim_con'].strftime('%d/%m/%Y')})")
            elif pp["status"]=="a_vencer":
                dr=(pp["fim_con"]-datetime.today()).days
                _ln(f"    {t('ferias_a_vencer')}: vence em {pp['fim_con'].strftime('%d/%m/%Y')}  ({dr} {t('dias_para_vencer')})")
    paginar(d, t("rel_sit_titulo"), itens, render_sit, resumo)

def rel_vencidas(d):
    itens=[]
    for func in ord_funcs(d):
        if not func.get("data_admissao",""): continue
        vencidas=[pp for pp in calc_periodos_aquisitivos(func) if pp["status"]=="vencida"]
        if vencidas: itens.append({"func":func,"vencidas":vencidas})
    titulo=t("func_vencidas")
    if not itens:
        limpar(); titulo_box(titulo); _lvz(); _ln("  "+t("nenhum_vencido"),"center"); _lvz(); fundo(); pausar(); return
    n_sem=sum(1 for f in d["funcionarios"] if not f.get("data_admissao",""))
    def resumo():
        _lnd(t("rel_data"),      datetime.today().strftime("%d/%m/%Y %H:%M"))
        _lnd(t("func_vencidas"), str(len(itens))+" funcionário(s)")
        if n_sem: _lnd(t("sem_admissao"), str(n_sem)+" sem data de admissão")
    def render_v(item):
        func=item["func"]; v=f" [{func.get('vinculo','')}]" if func.get("vinculo") else ""
        _lvz(); _ln(f"  [!] {func['nome']}{v}"); _ln(f"    {func['setor']}  →  {func['subsetor']}")
        _ln(f"    {t('data_admissao')} {func.get('data_admissao','—') or '—'}")
        for pp in item["vencidas"]:
            fim_s=(pp["fim_aq"]-timedelta(days=1)).strftime("%d/%m/%Y")
            _ln(f"    VENCIDA: {pp['ini_aq'].strftime('%d/%m/%Y')} – {fim_s}")
            _ln(f"    {t('vencida_em')}: {pp['fim_con'].strftime('%d/%m/%Y')}")
    paginar(d, titulo, itens, render_v, resumo)

def _pedir_ano():
    ano_atual=datetime.today().year
    while True:
        _lvz(); _ln(f"  {t('rel_ano_pedir')}"); _ln(f"  (0 = {t('cancelar')})"); _lvz(); fundo(); p()
        entrada=inp(f"Ano ({ano_atual}):").strip()
        if not entrada: return ano_atual
        if entrada=="0": return None
        try:
            ano=int(entrada)
            if 2000<=ano<=ano_atual+10: return ano
            flash(t("rel_ano_inv",max=ano_atual+10),erro=True)
        except ValueError: flash(t("so_numero"),erro=True)
        limpar(); titulo_box(t("rel_ano_titulo"))

def rel_por_ano_civil(d):
    limpar(); titulo_box(t("rel_ano_titulo")); ano=_pedir_ano()
    if ano is None: return
    limpar(); titulo_box(f"{t('rel_ano_titulo')} — {ano}"); _lvz()
    _ln("  Filtrar por:")
    _dleve()
    _ln(f"  1. {t('rel_ano_todos')}"); _ln(f"  2. {t('rel_ano_setor')}")
    _ln(f"  3. {t('rel_ano_sub')}");  _ln(f"  4. {t('rel_ano_func')}")
    _dleve(); _ln(f"  0. {t('cancelar')}"); fundo(); p()
    op=inp(t("opcao")).strip(); filtro_label=""; funcs_base=[]
    if op=="0": return
    elif op=="1": funcs_base=ord_funcs(d); filtro_label=t("rel_ano_todos")
    elif op=="2":
        setor=sel_setor(d)
        if not setor: return
        funcs_base=ord_funcs(d,[f for f in d["funcionarios"] if f["setor"]==setor]); filtro_label=f"Setor: {setor}"
    elif op=="3":
        setor=sel_setor(d)
        if not setor: return
        sub=sel_sub(d,setor)
        if not sub: return
        funcs_base=ord_funcs(d,[f for f in d["funcionarios"] if f["setor"]==setor and f["subsetor"]==sub]); filtro_label=f"{setor} → {sub}"
    elif op=="4":
        func=sel_func(d)
        if not func: return
        funcs_base=[func]; filtro_label=func["nome"]
    else: flash(t("invalido"),erro=True); return
    itens=[f for f in funcs_base if ferias_no_ano_civil(f["ferias"],ano)]
    if not itens:
        limpar(); titulo_box(f"{t('rel_ano_titulo')} — {ano}"); _lvz(); _ln("  "+t("rel_ano_vazio",ano=ano),"center"); _lvz(); fundo(); pausar(); return
    tot_dias=sum(sum(dias_no_ano_civil(f,ano) for f in ferias_no_ano_civil(func["ferias"],ano)) for func in itens)
    hoje=datetime.today()
    def resumo():
        _lnd(t("rel_data"),     hoje.strftime("%d/%m/%Y %H:%M"))
        _lnd("Ano civil",       f"{ano}  (use opção 1 para análise por prd.aquisitivo)")
        _lnd("Filtro",          filtro_label)
        _lnd(t("rel_encontrados"),str(len(itens)))
        _lnd(t("rel_ano_total"),f"{tot_dias} {t('pa_dias')}")
    def render_ano(func):
        ferias_ano=ferias_no_ano_civil(func["ferias"],ano); total_dias=sum(dias_no_ano_civil(f,ano) for f in ferias_ano)
        max_d=obter_regra(d,"max_dias_ano",func["setor"],func["subsetor"],func.get("vinculo",""))
        v=f" [{func.get('vinculo','')}]" if func.get("vinculo") else ""
        _lvz(); _ln(f"  › {func['nome']}{v}"); _ln(f"    {func['setor']}  →  {func['subsetor']}")
        if func.get("data_admissao"): _ln(f"    {t('data_admissao')} {func['data_admissao']}  {t('pa_sem_admissao')}")
        if max_d and max_d>0:
            bp=_barra_progresso(total_dias,max_d)
            if bp: barra,pct=bp; _ln(f"    {total_dias}/{max_d} {t('pa_dias')}  [{barra}] {pct}%  Restam: {max(0,max_d-total_dias)}")
        else: _ln(f"    {total_dias} {t('pa_dias')}  ({t('pa_ilimitado')})")
        for f in sorted(ferias_ano,key=lambda x:conv_data(x["inicio"]) or datetime.min):
            dias=calc_dias(f["inicio"],f["fim"]); dias_ef=dias_no_ano_civil(f,ano)
            vd=" "+t("fer_venda_lbl") if f.get("venda_ferias") else ""
            cruzou=f" {t('rel_ano_cruzou')}" if conv_data(f["inicio"]) and conv_data(f["fim"]) and conv_data(f["inicio"]).year!=conv_data(f["fim"]).year else ""
            ini=conv_data(f["inicio"])
            cat=f"[{t('rel_andamento')}]" if ini and ini<=hoje<=conv_data(f["fim"]) else (f"[{t('rel_futuro')}]" if ini and ini>hoje else f"[{t('rel_concluido')}]")
            _ln(f"      {cat} {f['inicio']} até {f['fim']}{cruzou}")
            if dias_ef!=dias: _ln(f"           {dias_ef} {t('pa_dias')} em {ano}  |  {dias} {t('pa_dias')} total{vd}")
            else: _ln(f"           {dias_ef} {t('pa_dias')}{vd}")
    paginar(d, f"{t('rel_ano_titulo')} — {ano}  |  {filtro_label}", itens, render_ano, resumo)

# ── Regras ────────────────────────────────────────────
def _editar_bloco(bloco, titulo_tela, parent=None):
    CR=_campos_regras(); campos=list(CR.keys())
    while True:
        limpar(); titulo_box(titulo_tela)
        if parent is not None: _ln(t("reg_herdar_nota"))
        _lvz(); l=_larg(); util=l-4; ml=max(10,util-18)
        for i,campo in enumerate(campos,1):
            meta=CR[campo]; atual=bloco.get(campo)
            if parent is not None and atual is None:
                vr=parent.get(campo,meta["padrao"]); sv=f"{t('reg_herdado')} ({fmt_val(meta['tipo'],vr)})"
            else:
                val=atual if atual is not None else meta["padrao"]; sv=fmt_val(meta["tipo"],val)
            lbl=meta["label"]; lbl=(lbl[:ml-2]+"..") if len(lbl)>ml else lbl
            _ln(f"  {i}. {lbl.ljust(ml)}: {sv}")
        _lvz(); _dleve(); _ln(f"  0. {t('salvar_voltar')}"); fundo(); p()
        try: op=int(inp(t("opcao")).strip())
        except ValueError: flash(t("so_numero"),erro=True); continue
        if op==0: break
        if not (1<=op<=len(campos)): flash(t("fora_intervalo"),erro=True); continue
        campo=campos[op-1]; meta=CR[campo]; atual=bloco.get(campo)
        limpar(); titulo_box(t("reg_editar")); _lvz()
        _ln(f"  {t('reg_campo')}: {meta['label']}"); _ln(f"  {t('reg_dica')}: {meta['dica']}"); _lvz()
        if meta["tipo"]=="bool":
            if parent is not None:
                vr=parent.get(campo,meta["padrao"])
                _ln(f"  {t('reg_atual')}: {'Sim' if atual else 'Não' if atual is not None else t('reg_herdado').upper()}")
                _ln(f"  {t('reg_herdar')}: {fmt_bool(vr)} ({t('reg_niv_sup')})"); _lvz(); fundo(); p()
                r=inp(t("reg_s_n_h")).strip().lower()
            else:
                _ln(f"  {t('reg_atual')}: {fmt_bool(atual if atual is not None else meta['padrao'])}"); _lvz(); fundo(); p()
                r=inp(t("reg_s_n_m")).strip().lower()
            if r==t("sim"): bloco[campo]=True
            elif r==t("nao"): bloco[campo]=False
            elif r=="" and parent is not None: bloco.pop(campo,None)
        elif meta["tipo"]=="int":
            if parent is not None:
                vr=parent.get(campo,meta["padrao"])
                _ln(f"  {t('reg_atual')}: {atual if atual is not None else t('reg_herdado').upper()}")
                _ln(f"  {t('reg_herdar')}: {vr} ({t('reg_niv_sup')})"); _lvz(); fundo(); p()
                r=inp(t("reg_num_h")).strip()
            else:
                _ln(f"  {t('reg_atual')}: {atual if atual is not None else meta['padrao']}"); _lvz(); fundo(); p()
                r=inp(t("reg_num_m")).strip()
            if r=="" and parent is not None: bloco.pop(campo,None)
            elif r.isdigit(): bloco[campo]=int(r)
            elif r: flash(t("invalido"),erro=True)

def _parent_subsetor(d,setor):
    base=dict(d["regras"]["global"]); base.update(d["regras"].get("por_setor",{}).get(setor,{})); return base

def ver_regras(d):
    CR=_campos_regras(); todos=[]
    todos.append(("sec",t("reg_gl_s")))
    for c,m in CR.items(): todos.append(("dado",m["label"],fmt_val(m["tipo"],d["regras"]["global"].get(c,m["padrao"]))))
    pv={k:b for k,b in d["regras"].get("por_vinculo",{}).items() if b}
    todos.append(("sec",t("reg_vin_s")))
    if not pv: todos.append(("info",t("reg_sem_vin")))
    else:
        for vinc,bloco in pv.items(): todos.append(("sub",f"[ {vinc} ]")); [todos.append(("dado",CR[c]["label"],fmt_val(CR[c]["tipo"],v))) for c,v in bloco.items()]
    ps={k:b for k,b in d["regras"].get("por_setor",{}).items() if b}
    todos.append(("sec",t("reg_set_s")))
    if not ps: todos.append(("info",t("reg_sem_set")))
    else:
        for setor,bloco in ps.items(): todos.append(("sub",f"[ {setor} ]")); [todos.append(("dado",CR[c]["label"],fmt_val(CR[c]["tipo"],v))) for c,v in bloco.items()]
    pb={k:b for k,b in d["regras"].get("por_subsetor",{}).items() if b}
    todos.append(("sec",t("reg_sub_s")))
    if not pb: todos.append(("info",t("reg_sem_sub")))
    else:
        for ref,bloco in pb.items():
            partes=ref.split(SEP,1); label=f"{partes[0]} → {partes[1]}" if len(partes)==2 else ref
            todos.append(("sub",f"[ {label} ]")); [todos.append(("dado",CR[c]["label"],fmt_val(CR[c]["tipo"],v))) for c,v in bloco.items()]
    def render_r(item):
        if   item[0]=="sec": _lvz(); _ln(f"  {item[1]}")
        elif item[0]=="sub": _lvz(); _ln(f"  {item[1]}")
        elif item[0]=="dado": _lnd(item[1],item[2])
        elif item[0]=="info": _ln(f"  {item[1]}")
    def resumo(): _lnd(t("reg_hier"),"")
    paginar(d, t("reg_ver"), todos, render_r, resumo)

def editar_regras_global(d):
    _editar_bloco(d["regras"]["global"],t("reg_global"),parent=None); salvar_dados(d); flash(t("reg_salvas"))
def editar_regras_vinculo(d):
    if not d["vinculos"]: flash(t("nenhum_vinculo"),erro=True); return
    limpar(); titulo_box(t("reg_vinculo")); _lvz(); fundo()
    v=sel_vinculo(d,permitir_nenhum=False)
    if not v: return
    d["regras"]["por_vinculo"].setdefault(v,{})
    _editar_bloco(d["regras"]["por_vinculo"][v],f"{t('reg_vinculo')}: {v}",parent=d["regras"]["global"])
    salvar_dados(d); flash(t("reg_salvas"))
def editar_regras_setor(d):
    if not d["setores"]: flash(t("nenhum_setor"),erro=True); return
    limpar(); titulo_box(t("reg_setor")); _lvz(); fundo()
    setor=sel_setor(d)
    if not setor: return
    d["regras"]["por_setor"].setdefault(setor,{})
    _editar_bloco(d["regras"]["por_setor"][setor],f"{t('reg_setor')}: {setor}",parent=d["regras"]["global"])
    salvar_dados(d); flash(t("reg_salvas"))
def editar_regras_subsetor(d):
    if not d["setores"]: flash(t("nenhum_setor"),erro=True); return
    limpar(); titulo_box(t("reg_subsetor")); _lvz(); _ln("  "+t("reg_sel_sub")); _lvz(); fundo()
    setor=sel_setor(d)
    if not setor: return
    sub=sel_sub(d,setor)
    if not sub: return
    chave=_chave_sub(setor,sub); d["regras"]["por_subsetor"].setdefault(chave,{})
    _editar_bloco(d["regras"]["por_subsetor"][chave],f"{t('reg_subsetor')}: {setor} → {sub}",parent=_parent_subsetor(d,setor))
    salvar_dados(d); flash(t("reg_salvas"))

def menu_regras(d):
    while True:
        _render_menu(t("reg_titulo"),[(1,t("reg_ver")),(2,t("reg_global")),(3,t("reg_vinculo")),(4,t("reg_setor")),(5,t("reg_subsetor"))],info=[t("reg_hier")],rodape=[(0,t("voltar"))])
        op=inp(t("opcao")).strip()
        if   op=="1": ver_regras(d)
        elif op=="2": editar_regras_global(d)
        elif op=="3": editar_regras_vinculo(d)
        elif op=="4": editar_regras_setor(d)
        elif op=="5": editar_regras_subsetor(d)
        elif op=="0": break
        else: flash(t("invalido"),erro=True)

# ── Validação ─────────────────────────────────────────
def _render_pend(r):
    func=r["func"]; v=f" [{func.get('vinculo','')}]" if func.get("vinculo") else ""
    _lvz(); _ln(f"  {func['nome']}{v}"); _ln(f"  {func['setor']}  →  {func['subsetor']}"); _lvz()
    for pen in r["pendencias"]:
        _ln(f"  {'[P]' if pen['tipo']=='periodo' else '[A]'} {pen['ref']}:")
        for i,e in enumerate(pen["erros"],1): _ln(f"      {i}. {e}")

def menu_validacao(d):
    while True:
        n=contar_pends(d); info=["  "+t("val_ok")] if n==0 else [f"  {n} {t('val_pend')}"]
        _render_menu(t("val_titulo"),[(1,t("val_ver")),(2,t("val_por_func")),(3,t("val_por_setor")),(4,t("val_revalid"))],info=info,rodape=[(0,t("voltar"))])
        op=inp(t("opcao")).strip()
        if   op=="1": val_geral(d)
        elif op=="2": val_por_func(d)
        elif op=="3": val_por_setor(d)
        elif op=="4":
            limpar(); titulo_box(t("val_revalid_t")); _lvz()
            _ln("  "+t("val_verificando")); n=contar_pends(d); _lvz()
            if n==0: _ln("  "+t("val_ok"))
            else:    _ln(f"  {n} {t('val_pend')} — {t('val_detalhe')}")
            _lvz(); fundo(); pausar()
        elif op=="0": break
        else: flash(t("invalido"),erro=True)

def val_geral(d):
    res=auditar_sistema(d); tot=sum(len(r["pendencias"]) for r in res)
    def resumo(): _lnd(t("val_data"),datetime.today().strftime("%d/%m/%Y %H:%M")); _lnd(t("val_c_pend"),str(len(res))); _lnd(t("val_total"),str(tot))
    if not res:
        limpar(); titulo_box(t("val_geral_t"))
        for item in _capturar(resumo): _print_buf(item)
        _dleve(); _lvz(); _ln("  "+t("val_conform"),"center"); _lvz(); fundo(); pausar(); return
    paginar(d, t("val_geral_t"), res, _render_pend, resumo)

def val_por_func(d):
    limpar(); titulo_box(t("val_func_t")); _lvz(); fundo()
    func=sel_func(d)
    if not func: return
    pends=auditar_func(d,func)
    def resumo():
        _lnd(t("val_data"),    datetime.today().strftime("%d/%m/%Y %H:%M"))
        _lnd(t("rel_nome"),    func["nome"]); _lnd(t("rel_vinculo"),func.get("vinculo","—") or "—")
        _lnd(t("rel_setor_l"), f"{func['setor']} → {func['subsetor']}")
        _lnd(t("val_periodos"),str(len(func["ferias"]))); _lnd(t("val_pendencias"),str(len(pends)))
    if not pends:
        limpar(); titulo_box(f"{t('val_func_t')}: {func['nome']}")
        for item in _capturar(resumo): _print_buf(item)
        _dleve(); _lvz(); _ln("  "+t("val_conform"),"center"); _lvz(); fundo(); pausar(); return
    def render_p(pen):
        _lvz(); _ln(f"  {'[P]' if pen['tipo']=='periodo' else '[A]'} {pen['ref']}:")
        for i,e in enumerate(pen["erros"],1): _ln(f"      {i}. {e}")
    paginar(d, f"{t('val_func_t')}: {func['nome']}", pends, render_p, resumo)

def val_por_setor(d):
    limpar(); titulo_box(t("val_setor_t")); _lvz(); fundo()
    setor=sel_setor(d)
    if not setor: return
    fs=[f for f in d["funcionarios"] if f["setor"]==setor]
    res=[{"func":f,"pendencias":auditar_func(d,f)} for f in fs if f["ferias"] and auditar_func(d,f)]
    tot=sum(len(r["pendencias"]) for r in res)
    def resumo():
        _lnd(t("val_data"),    datetime.today().strftime("%d/%m/%Y %H:%M"))
        _lnd(t("rel_setor_l"), setor); _lnd(t("rel_total_func"),str(len(fs)))
        _lnd(t("val_c_pend2"), str(len(res))); _lnd(t("val_total"),str(tot))
    if not res:
        limpar(); titulo_box(f"{t('val_setor_t')}: {setor}")
        for item in _capturar(resumo): _print_buf(item)
        _dleve(); _lvz(); _ln("  "+t("val_conform"),"center"); _lvz(); fundo(); pausar(); return
    paginar(d, f"{t('val_setor_t')}: {setor}", res, _render_pend, resumo)

# ── Configurações ─────────────────────────────────────
def menu_configuracoes(d):
    chaves=list(CONFIG_PADRAO.keys())
    while True:
        CO=_config_opcoes(); cfg=d.get("config",CONFIG_PADRAO)
        limpar(); titulo_box(t("cfg_titulo")); _lvz(); _ln("  "+t("cfg_desc")); _lvz(); _dleve()
        for i,chave in enumerate(chaves,1):
            meta=CO[chave]; val=cfg.get(chave,CONFIG_PADRAO[chave])
            desc=meta["opcoes"].get(val,val); lbl=meta["label"].ljust(42)
            _ln(f"  {i}. {lbl}: {desc}")
        _lvz()
        msg,erro=_get_flash()
        if msg: _dleve(); _ln(("  ✗ " if erro else "  ✓ ")+msg)
        _dleve(); _ln(f"  0. {t('salvar_voltar')}"); fundo(); p()
        try: op=int(inp(t("opcao")).strip())
        except ValueError: flash(t("so_numero"),erro=True); continue
        if op==0: salvar_dados(d); flash(t("cfg_salvo")); return
        if not (1<=op<=len(chaves)): flash(t("fora_intervalo"),erro=True); continue
        chave=chaves[op-1]; meta=CO[chave]; opts=list(meta["opcoes"].items())
        limpar(); titulo_box(f"{t('cfg_alterar')} {meta['label'].upper()}")
        _lvz(); _ln(f"  {t('cfg_atual')} {meta['opcoes'].get(cfg.get(chave,CONFIG_PADRAO[chave]),'—')}"); _lvz(); _dleve()
        for j,(val,desc) in enumerate(opts,1):
            m=" "+t("cfg_atual_m") if val==cfg.get(chave,CONFIG_PADRAO[chave]) else ""
            _ln(f"  {j}. {desc}{m}")
        _lvz(); _dleve(); _ln(f"  0. {t('cancelar')}"); fundo(); p()
        try: esc=int(inp(t("cfg_escolha")).strip())
        except ValueError: flash(t("so_numero"),erro=True); continue
        if esc==0: continue
        if 1<=esc<=len(opts): cfg[chave]=opts[esc-1][0]; d["config"]=cfg; flash(f"'{meta['label']}': {meta['opcoes'][cfg[chave]]}")
        else: flash(t("fora_intervalo"),erro=True)

# ── Administração ─────────────────────────────────────
def _users_db():
    con=_conn(); rows=con.execute("SELECT id,login,nome,nivel FROM usuarios ORDER BY nivel,login").fetchall(); con.close()
    return [dict(r) for r in rows]
def menu_usuarios(d):
    while True:
        _render_menu(t("usr_titulo"),[(1,t("usr_listar")),(2,t("usr_criar")),(3,t("usr_senha")),(4,t("usr_excluir"))],rodape=[(0,t("voltar"))])
        op=inp(t("opcao")).strip()
        if   op=="1": usr_listar(d)
        elif op=="2": usr_criar(d)
        elif op=="3": usr_senha(d)
        elif op=="4": usr_excluir(d)
        elif op=="0": break
        else: flash(t("invalido"),erro=True)
def usr_listar(d):
    users=_users_db()
    if not users:
        limpar(); titulo_box(t("usr_titulo")); _lvz(); _ln("  "+t("usr_nenhum"),"center"); _lvz(); fundo(); pausar(); return
    def render_u(u): niv=t("nivel_admin") if u["nivel"]=="admin" else t("nivel_usuario"); _ln(f"  › [{u['login']}]  {u['nome']}  ({niv})")
    paginar(d, t("usr_titulo"), users, render_u)
def usr_criar(d):
    limpar(); titulo_box(t("usr_criar")); _lvz(); fundo(); p()
    login=inp("Login:").strip()
    if not login: flash(t("nome_vazio"),erro=True); return
    con=_conn(); ex=con.execute("SELECT id FROM usuarios WHERE login=?",(login,)).fetchone(); con.close()
    if ex: flash(t("usr_ja_existe"),erro=True); return
    nome=inp(t("rel_nome")+":").strip()
    if not nome: flash(t("nome_vazio"),erro=True); return
    p(); senha=inp_s(t("usr_nova_senha")); conf=inp_s(t("usr_conf_senha"))
    if senha!=conf: flash(t("usr_senha_dif"),erro=True); return
    if not senha: flash(t("nome_vazio"),erro=True); return
    _lvz(); _ln(f"  1. {t('nivel_admin')}"); _ln(f"  2. {t('nivel_usuario')}"); _lvz(); fundo(); p()
    try: niv_op=int(inp(t("usr_nivel")).strip())
    except: niv_op=2
    nivel="admin" if niv_op==1 else "usuario"
    con=_conn(); con.execute("INSERT INTO usuarios (login,nome,senha_hash,nivel) VALUES (?,?,?,?)",(login,nome,_hash(senha),nivel)); con.commit(); con.close()
    flash(f"[{login}] {nome} — "+t("usr_criado"))
def usr_senha(d):
    limpar(); titulo_box(t("usr_senha")); _lvz(); fundo(); p()
    users=_users_db()
    if not users: flash(t("usr_nenhum"),erro=True); return
    for i,u in enumerate(users,1): p(f"    {i}. [{u['login']}]  {u['nome']}")
    p(f"    0. {t('cancelar')}")
    try: e=int(inp(t("opcao")).strip())
    except: flash(t("so_numero"),erro=True); return
    if e==0: return
    if not (1<=e<=len(users)): flash(t("fora_intervalo"),erro=True); return
    u=users[e-1]; p(); senha=inp_s(t("usr_nova_senha")); conf=inp_s(t("usr_conf_senha"))
    if senha!=conf: flash(t("usr_senha_dif"),erro=True); return
    if not senha: flash(t("nome_vazio"),erro=True); return
    con=_conn(); con.execute("UPDATE usuarios SET senha_hash=? WHERE id=?",(_hash(senha),u["id"])); con.commit(); con.close()
    flash(f"[{u['login']}] — "+t("usr_senha_ok"))
def usr_excluir(d):
    limpar(); titulo_box(t("usr_excluir")); _lvz(); fundo(); p()
    users=_users_db()
    if not users: flash(t("usr_nenhum"),erro=True); return
    for i,u in enumerate(users,1): p(f"    {i}. [{u['login']}]  {u['nome']}")
    p(f"    0. {t('cancelar')}")
    try: e=int(inp(t("opcao")).strip())
    except: flash(t("so_numero"),erro=True); return
    if e==0: return
    if not (1<=e<=len(users)): flash(t("fora_intervalo"),erro=True); return
    u=users[e-1]
    if u["login"]==SESSAO["login"]: flash(t("usr_proprio"),erro=True); return
    admins=[x for x in users if x["nivel"]=="admin"]
    if u["nivel"]=="admin" and len(admins)==1: flash(t("usr_ultimo_adm"),erro=True); return
    c=inp(t("confirmar_excl")).strip().lower()
    if c==t("sim"):
        con=_conn(); con.execute("DELETE FROM usuarios WHERE id=?",(u["id"],)); con.commit(); con.close()
        flash(f"[{u['login']}] — "+t("usr_excluido"))
    else: flash(t("excluir_cancel"))
def _fazer_backup():
    """Cria backup consistente usando a API nativa do SQLite."""
    if not os.path.exists(BANCO_DADOS): return None
    os.makedirs(BACKUP_DIR,mode=0o700,exist_ok=True)
    ts=datetime.now().strftime("%Y%m%d_%H%M%S_%f"); dst=os.path.join(BACKUP_DIR,f"backup_{ts}.db")
    src_con=_conn(); dst_con=sqlite3.connect(dst)
    try: src_con.backup(dst_con)
    finally: dst_con.close(); src_con.close()
    try: os.chmod(dst, 0o600)
    except OSError: pass
    return dst
def _listar_backups():
    if not os.path.exists(BACKUP_DIR): return []
    return sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith("backup_") and f.endswith(".db")],reverse=True)
def _fmt_bkp(b):
    try:    dt=datetime.strptime(b.replace("backup_","").replace(".db",""),"%Y%m%d_%H%M%S"); return dt.strftime("%d/%m/%Y %H:%M:%S")
    except: return b
def menu_backup(d):
    while True:
        _render_menu(t("bkp_titulo"),[(1,t("bkp_fazer")),(2,t("bkp_restaurar")),(3,t("bkp_listar"))],rodape=[(0,t("voltar"))])
        op=inp(t("opcao")).strip()
        if op=="1":
            dst=_fazer_backup(); flash((t("bkp_ok")+os.path.basename(dst)) if dst else "Banco não encontrado.",erro=not dst)
        elif op=="2":
            bkps=_listar_backups()
            if not bkps: flash(t("bkp_nenhum"),erro=True); continue
            paginar(d, t("bkp_restaurar"), bkps, lambda b: _ln(f"  › {_fmt_bkp(b)}  ({os.path.getsize(os.path.join(BACKUP_DIR,b))//1024+1} KB)"))
            p(); p("  Número do backup a restaurar:")
            for i,b in enumerate(bkps,1): p(f"    {i}. {_fmt_bkp(b)}")
            p(f"    0. {t('cancelar')}")
            try: e=int(inp(t("opcao")).strip())
            except: flash(t("so_numero"),erro=True); continue
            if e==0: continue
            if not (1<=e<=len(bkps)): flash(t("fora_intervalo"),erro=True); continue
            src=os.path.join(BACKUP_DIR,bkps[e-1]); p()
            c=inp(t("bkp_confirma")).strip().lower()
            if c==t("sim"):
                _fazer_backup()
                src_con=sqlite3.connect(src); dst_con=sqlite3.connect(BANCO_DADOS)
                try: src_con.backup(dst_con)
                finally: dst_con.close(); src_con.close()
                d.clear(); d.update(carregar_dados()); flash(t("bkp_rest_ok"))
            else: flash(t("bkp_cancel"))
        elif op=="3":
            bkps=_listar_backups()
            if not bkps: flash(t("bkp_nenhum"),erro=True); continue
            paginar(d, t("bkp_listar"), bkps, lambda b: _ln(f"  › {_fmt_bkp(b)}  —  {os.path.getsize(os.path.join(BACKUP_DIR,b))//1024+1} KB"))
        elif op=="0": break
        else: flash(t("invalido"),erro=True)
def apagar_dados(d):
    limpar(); titulo_box(t("apg_titulo")); _lvz(); _ln(t("apg_aviso1"),"center"); _ln(t("apg_aviso2"),"center")
    _lvz(); _dleve(); _lvz(); _ln(f"  {t('apg_instrucao')}"); _ln(f"  (palavra: {t('apg_palavra')})"); _lvz(); fundo(); p()
    if inp(">>>").strip()==t("apg_palavra"):
        _fazer_backup()
        con=_conn(); con.executescript("DELETE FROM ferias; DELETE FROM funcionarios; DELETE FROM subsetores; DELETE FROM setores; DELETE FROM vinculos; DELETE FROM regras; DELETE FROM configuracoes;"); con.commit(); con.close()
        d.clear(); d.update(carregar_dados()); flash(t("apg_ok"))
    else: flash(t("apg_cancel"))
def menu_idioma(d):
    while True:
        atual="Português (PT-BR)" if get_idioma()=="pt" else "English (EN)"
        _render_menu(t("idioma_titulo"),[(1,t("idioma_pt")),(2,t("idioma_en"))],info=[f"{t('idioma_atual')} {atual}"],rodape=[(0,t("voltar"))])
        op=inp(t("opcao")).strip()
        if op=="1": set_idioma("pt"); salvar_dados(d); flash(t("idioma_ok")+" → Português"); break
        elif op=="2": set_idioma("en"); salvar_dados(d); flash(t("idioma_ok")+" → English"); break
        elif op=="0": break
        else: flash(t("invalido"),erro=True)
def menu_administracao(d):
    while True:
        _render_menu(t("adm_titulo"),[(1,t("adm_usuarios")),(2,t("adm_backup")),(3,t("adm_apagar")),(4,t("adm_idioma"))],rodape=[(0,t("voltar"))])
        op=inp(t("opcao")).strip()
        if   op=="1": menu_usuarios(d)
        elif op=="2": menu_backup(d)
        elif op=="3": apagar_dados(d)
        elif op=="4": menu_idioma(d)
        elif op=="0": break
        else: flash(t("invalido"),erro=True)

# ══════════════════════════════════════════════════════
#  LOGIN
# ══════════════════════════════════════════════════════
def tela_login():
    _criar_admin_inicial()
    for tentativa in range(1,4):
        limpar(); titulo_box(t("login_titulo")); _lvz(); _ln(t("menu_titulo"),"center"); _lvz()
        if tentativa>1: _ln(f"  ⚠  Tentativa {tentativa}/3","center"); _lvz()
        fundo(); p()
        login=inp(t("login_usuario")).strip(); senha=inp_s(t("login_senha"))
        con=_conn(); row=con.execute("SELECT id,login,nome,senha_hash,nivel,failed_attempts,locked_until FROM usuarios WHERE login=?",(login,)).fetchone()
        if not row:
            con.close(); flash(t("login_erro"),erro=True); continue
        bloqueado=row["locked_until"] or ""
        if bloqueado:
            try:
                if datetime.fromisoformat(bloqueado)>datetime.now():
                    con.close(); flash("Usuário temporariamente bloqueado.",erro=True); continue
                con.execute("UPDATE usuarios SET failed_attempts=0,locked_until='' WHERE id=?",(row["id"],)); con.commit()
            except ValueError:
                con.execute("UPDATE usuarios SET failed_attempts=0,locked_until='' WHERE id=?",(row["id"],)); con.commit()
        valido,legado=_verificar_senha(senha,row["senha_hash"])
        if valido:
            if legado: con.execute("UPDATE usuarios SET senha_hash=? WHERE id=?",(_hash(senha),row["id"]))
            con.execute("UPDATE usuarios SET failed_attempts=0,locked_until='',last_login=? WHERE id=?",(datetime.now().isoformat(timespec="seconds"),row["id"]))
            con.commit(); con.close()
            SESSAO["login"]=row["login"]; SESSAO["nome"]=row["nome"]; SESSAO["nivel"]=row["nivel"]; return True
        falhas=int(row["failed_attempts"] or 0)+1
        if falhas>=3:
            bloqueio=(datetime.now()+timedelta(minutes=5)).isoformat(timespec="seconds")
            con.execute("UPDATE usuarios SET failed_attempts=?,locked_until=? WHERE id=?",(falhas,bloqueio,row["id"]))
        else: con.execute("UPDATE usuarios SET failed_attempts=? WHERE id=?",(falhas,row["id"]))
        con.commit(); con.close(); flash(t("login_erro"),erro=True)
        if tentativa<3:
            limpar(); titulo_box(t("login_titulo")); _lvz(); _ln("  "+t("login_erro"),"center"); _lvz(); fundo(); pausar()
    limpar(); titulo_box(t("login_titulo")); _lvz(); _ln("  "+t("login_bloq"),"center"); _lvz(); fundo(); time.sleep(2); return False

# ══════════════════════════════════════════════════════
#  MENU PRINCIPAL — com painel inline
# ══════════════════════════════════════════════════════
def _render_menu_principal(titulo, itens, rodape, info_topo, painel_linhas):
    limpar(); titulo_box(titulo); _lvz()
    for item in itens:
        if item is None: _dleve()
        else:            _ln(f"  {item[0]}. {item[1]}")
    _dleve()
    for i in info_topo: _ln(f"  {i}")
    if painel_linhas:
        _dleve()
        for linha in painel_linhas: _ln(f"  {linha}")
    _dleve()
    for item in rodape: _ln(f"  {item[0]}. {item[1]}")
    msg,erro=_get_flash()
    if msg: _dleve(); _ln(("  ✗ " if erro else "  ✓ ")+msg)
    fundo(); p()

def menu_principal():
    if not tela_login(): return
    d=carregar_dados(); eh_admin=(SESSAO["nivel"]=="admin")
    while True:
        n=contar_pends(d); cfg=d.get("config",CONFIG_PADRAO)
        CO=_config_opcoes(); niv=t("nivel_admin") if eh_admin else t("nivel_usuario")
        ord_label=CO["ordem_funcionarios"]["opcoes"].get(cfg.get("ordem_funcionarios","nome"),"—")
        dir_label=_dir_curto(cfg)
        em_ferias_n,em_30dias_n=_calcular_painel(d)
        # ── Menu de gráfico ─────────────────────────────────────
        # "m_grafico" = "Gráfico de evolução mensal" (minúsculas, adequado para lista de menu)
        # "graf_titulo" = "GRÁFICO DE EVOLUÇÃO MENSAL" (maiúsculas, para cabeçalho de tela)
        itens_admin=[
            (1,  t("m_setores")),   (2,  t("m_funcs")),   (3,  t("m_ferias")),
            (4,  t("m_relat")),     (5,  t("m_regras")),   (6,  t("m_valid")),
            (7,  t("m_config")),    (8,  t("m_admin")),    (9,  t("m_painel")),
            (10, t("m_grafico")),   # texto curto para o menu
        ]
        itens_user=[
            (1, t("m_funcs")),  (2, t("m_ferias")),
            (3, t("m_relat")),  (4, t("m_painel")),
            (5, t("m_grafico")),  # texto curto para o menu
        ]
        status=t("status_pend",n=n) if n>0 else t("status_ok")
        n_venc=_contar_vencidas(d)
        info_topo=[f"{t('logado')} {SESSAO['nome']} ({niv})",status,f"{t('exibicao')} {ord_label}  |  {dir_label}"]
        if n_venc>0: info_topo.append(t("ferias_venc_alerta",n=n_venc))
        painel_linhas=_linhas_painel_menu(em_ferias_n, em_30dias_n, dias_alerta=7)
        _render_menu_principal(t("menu_titulo"), itens_admin if eh_admin else itens_user,
                               rodape=[(0,t("sair"))], info_topo=info_topo, painel_linhas=painel_linhas)
        op=inp(t("opcao")).strip()
        if eh_admin:
            if   op=="1":  menu_setores(d)
            elif op=="2":  menu_funcionarios(d)
            elif op=="3":  menu_ferias(d)
            elif op=="4":  menu_relatorios(d)
            elif op=="5":  menu_regras(d)
            elif op=="6":  menu_validacao(d)
            elif op=="7":  menu_configuracoes(d)
            elif op=="8":  menu_administracao(d)
            elif op=="9":  painel_ferias(d)
            elif op=="10": grafico_evolucao_mensal(d)
            elif op=="0":  break
            else: flash(t("invalido"),erro=True)
        else:
            if   op=="1": menu_funcionarios(d)
            elif op=="2": menu_ferias(d)
            elif op=="3": menu_relatorios(d)
            elif op=="4": painel_ferias(d)
            elif op=="5": grafico_evolucao_mensal(d)
            elif op=="0": break
            else: flash(t("invalido"),erro=True)
    limpar(); p(); p("  "+("Encerrando. Até logo!" if get_idioma()=="pt" else "Closing. Goodbye!")); p()


if __name__ == "__main__":
    menu_principal()
