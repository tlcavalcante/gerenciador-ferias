"""Módulo refatorado do Gerenciador de Férias v3.9.1."""
import runtime
import business
globals().update({k: v for k, v in vars(runtime).items() if not k.startswith("__")})
globals().update({k: v for k, v in vars(business).items() if not k.startswith("__")})

def _status_ferias(func):
    hoje,tot,fut,em=datetime.today(),0,0,0
    for f in func["ferias"]:
        tot+=calc_dias(f["inicio"],f["fim"]); ini=conv_data(f["inicio"]); fim=conv_data(f["fim"])
        if ini and fim:
            if ini<=hoje<=fim: em+=1
            elif ini>hoje:     fut+=1
    return tot,fut,em

def _render_func_simples(func, d):
    an=analise_periodo_atual(d,func); pas,atu,fut=classificar_ferias(func)
    v=f" [{func.get('vinculo','')}]" if func.get("vinculo") else ""
    _lvz(); _ln(f"  › {func['nome']}{v}")
    _ln(f"    {func['setor']}  →  {func['subsetor']}")
    _ln(_linha_periodo_atual(func,d))
    if atu: _ln(f"    Em férias: {atu[0]['inicio']} até {atu[0]['fim']}")
    elif fut: _ln(f"    Próximo: {fut[0]['inicio']} até {fut[0]['fim']}")
    if not func["ferias"]: _ln("    "+t("sem_ferias"))

def _render_func_individual(func, d):
    an=analise_periodo_atual(d,func); pas,atu,fut=classificar_ferias(func)
    per=calc_periodos_aquisitivos(func); sit=situacao_geral_func(func)
    v=f" [{func.get('vinculo','')}]" if func.get("vinculo") else ""
    sit_txt={"vencida":f"[!] {t('ferias_vencidas')}","a_vencer":f"[~] {t('ferias_a_vencer')}","pendente":f"[?] {t('ferias_pendentes')}","ok":f"[✓] {t('ferias_em_dia')}","sem_admissao":f"[–] {t('sem_admissao')}"}.get(sit,"")
    _dleve(); _ln(f"  {func['nome']}{v}","center"); _dleve()
    _ln(f"  {t('rel_setor_l')}: {func['setor']}  |  {t('rel_sub_l')}: {func['subsetor']}")
    if func.get("vinculo"):       _ln(f"  {t('rel_vinculo')}: {func['vinculo']}")
    if func.get("data_admissao"): _ln(f"  {t('data_admissao')} {func['data_admissao']}")
    if sit_txt:                   _ln(f"  {t('situacao_label')}: {sit_txt}")
    _lvz()
    if an["tipo"]=="aquisitivo":
        ini_s=an["ini"].strftime("%d/%m/%Y"); fim_s=(an["fim"]-timedelta(days=1)).strftime("%d/%m/%Y")
        _ln(f"  [{t('pa_atual')} #{an['numero']}:  {ini_s} → {fim_s}]")
    else:
        _ln(f"  [Ano civil {an['ano_civil']}  {t('pa_sem_admissao')}]")
    if an["max_dias"] and an["max_dias"]>0:
        bp=_barra_progresso(an["tirados"],an["max_dias"])
        if bp: barra,pct=bp; _ln(f"    {t('pa_tirados')}  : {an['tirados']:>3} / {an['max_dias']} {t('pa_dias')}"); _ln(f"    {t('pa_restantes')}: {an['restantes']:>3} {t('pa_dias')}"); _ln(f"    {t('pa_progresso')}: [{barra}] {pct}%")
    else: _ln(f"    {t('pa_tirados')}: {an['tirados']} {t('pa_dias')}  ({t('pa_ilimitado')})")
    if atu:
        _lvz(); _ln(f"  [{t('rel_andamento')}]")
        for f in atu:
            dias=calc_dias(f["inicio"],f["fim"]); vd=" "+t("fer_venda_lbl") if f.get("venda_ferias") else ""
            _ln(f"    • {f['inicio']} até {f['fim']}  ({dias} {t('pa_dias')}){vd}")
    if fut:
        _lvz(); _ln(f"  [{t('periodos_futuros')}: {len(fut)}]")
        for f in sorted(fut,key=lambda x:conv_data(x["inicio"]) or datetime.min):
            dias=calc_dias(f["inicio"],f["fim"]); vd=" "+t("fer_venda_lbl") if f.get("venda_ferias") else ""
            _ln(f"    • {f['inicio']} até {f['fim']}  ({dias} {t('pa_dias')}){vd}")
    if pas:
        _lvz(); _ln(f"  [{t('periodos_passados')}: {len(pas)}]")
        for f in sorted(pas,key=lambda x:conv_data(x["inicio"]) or datetime.min,reverse=True):
            dias=calc_dias(f["inicio"],f["fim"]); vd=" "+t("fer_venda_lbl") if f.get("venda_ferias") else ""
            _ln(f"    • {f['inicio']} até {f['fim']}  ({dias} {t('pa_dias')}){vd}")
    if not func["ferias"]: _lvz(); _ln("    "+t("sem_ferias"))
    if per:
        _lvz(); _ln(f"  [{t('periodo_aquisitivo')} — histórico]")
        for i,pp in enumerate(per,1):
            s_txt={"ok":t("ferias_em_dia"),"vencida":t("ferias_vencidas"),"a_vencer":t("ferias_a_vencer"),"pendente":t("ferias_pendentes")}.get(pp["status"],pp["status"])
            fim_s=(pp["fim_aq"]-timedelta(days=1)).strftime("%d/%m/%Y")
            _ln(f"    Prd.{i}: {pp['ini_aq'].strftime('%d/%m/%Y')} – {fim_s}  |  {pp['dias_tirados']} dias  |  {s_txt}")
            if pp["status"]=="a_vencer": _ln(f"      ⚠ Concessivo vence em {(pp['fim_con']-datetime.today()).days} {t('dias_para_vencer')}")
            elif pp["status"]=="vencida": _ln(f"      ✗ {t('vencida_em')}: {pp['fim_con'].strftime('%d/%m/%Y')}")
    _lvz()

# ══════════════════════════════════════════════════════
#  GRÁFICO DE EVOLUÇÃO MENSAL
# ══════════════════════════════════════════════════════

MESES_LABEL = {
    "pt": ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"],
    "en": ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
}

def _mes_label(ano, mes):
    return f"{MESES_LABEL.get(get_idioma(),MESES_LABEL['pt'])[mes-1]}/{str(ano)[2:]}"

def _dias_no_mes(f, ano, mes):
    try:
        fi=datetime.strptime(f["inicio"].strip(),"%d/%m/%Y"); ff=datetime.strptime(f["fim"].strip(),"%d/%m/%Y")
        ini_m=datetime(ano,mes,1); fim_m=(datetime(ano+1,1,1) if mes==12 else datetime(ano,mes+1,1))-timedelta(days=1)
        ie=max(fi,ini_m); fe=min(ff,fim_m); return max(0,(fe-ie).days+1)
    except: return 0

def _pico_mes(funcionarios, ano, mes):
    ini_m=datetime(ano,mes,1); fim_m=datetime(ano+1,1,1) if mes==12 else datetime(ano,mes+1,1)
    pico=0; dia=ini_m
    while dia<fim_m:
        em=0
        for func in funcionarios:
            for f in func.get("ferias",[]):
                fi=conv_data(f["inicio"]); ff=conv_data(f["fim"])
                if fi and ff and fi<=dia<=ff: em+=1; break
        pico=max(pico,em); dia+=timedelta(days=1)
    return pico

def _evolucao_empresa(funcionarios, n_meses=12):
    hoje=datetime.today(); cur=add_meses(datetime(hoje.year,hoje.month,1),-(n_meses-1)); fim=datetime(hoje.year,hoje.month,1); resultado=[]
    while cur<=fim:
        ano,mes=cur.year,cur.month
        por_func={func["nome"]:d for func in funcionarios if (d:=sum(_dias_no_mes(f,ano,mes) for f in func.get("ferias",[])))>0}
        total=sum(por_func.values()); pico=_pico_mes(funcionarios,ano,mes) if por_func else 0
        resultado.append({"ano":ano,"mes":mes,"total_dias":total,"n_func":len(por_func),"pico":pico,"por_func":por_func})
        cur=add_meses(cur,1)
    return resultado

def _evolucao_func(func, n_meses=12):
    hoje=datetime.today(); cur=add_meses(datetime(hoje.year,hoje.month,1),-(n_meses-1)); fim=datetime(hoje.year,hoje.month,1); resultado=[]; acum=0
    while cur<=fim:
        ano,mes=cur.year,cur.month; d=sum(_dias_no_mes(f,ano,mes) for f in func.get("ferias",[])); acum+=d
        resultado.append({"ano":ano,"mes":mes,"dias":d,"acumulado":acum}); cur=add_meses(cur,1)
    return resultado

def _barra_grafico(valor, max_val, largura=None):
    if largura is None: largura=max(10,(_larg()-4)*38//100)
    if max_val<=0: return "░"*largura
    fill=round(min(valor,max_val)/max_val*largura); return "█"*fill+"░"*(largura-fill)

def _pedir_n_meses():
    limpar(); titulo_box(t("graf_titulo")); _lvz()
    _ln("  Período do gráfico:")
    _dleve()
    _ln(f"  1. {t('graf_3m')}"); _ln(f"  2. {t('graf_6m')}")
    _ln(f"  3. {t('graf_12m')}"); _ln(f"  4. {t('graf_24m')}")
    _dleve(); _ln(f"  0. {t('cancelar')}"); fundo(); p()
    op=inp(t("opcao")).strip()
    return {"1":3,"2":6,"3":12,"4":24,"":12,"0":None}.get(op,12)

def grafico_evolucao_mensal(d):
    """Gráfico de barras horizontais de evolução mensal de férias."""
    limpar(); titulo_box(t("graf_titulo")); _lvz()
    _ln(f"  {t('graf_escolha_tipo')}")
    _dleve()
    _ln(f"  1. {t('graf_empresa')}"); _ln(f"  2. {t('graf_setor')}")
    _ln(f"  3. {t('graf_subsetor')}"); _ln(f"  4. {t('graf_funcionario')}")
    _dleve(); _ln(f"  0. {t('cancelar')}"); fundo(); p()
    op=inp(t("opcao")).strip()
    if op=="0": return
    n_meses=_pedir_n_meses()
    if n_meses is None: return
    hoje=datetime.today()

    if op=="1":
        ev=_evolucao_empresa(d["funcionarios"],n_meses)
        tot=sum(m["total_dias"] for m in ev); n_c=sum(1 for m in ev if m["total_dias"]>0)
        max_d=max((m["total_dias"] for m in ev),default=1) or 1; bw=max(12,(_larg()-4)*38//100)
        limpar(); titulo_box(f"{t('graf_titulo')} — {t('graf_empresa')}")
        def resumo_emp():
            _lnd(t("rel_data"),         hoje.strftime("%d/%m/%Y %H:%M"))
            _lnd(t("graf_periodo"),     f"{n_meses} meses")
            _lnd(t("rel_total_func"),   str(len(d["funcionarios"])))
            _lnd(t("graf_total_periodo"),f"{tot} {t('pa_dias')}")
            _lnd(t("graf_meses_ativos"),f"{n_c} mês(es)")
            _lnd("Legenda","█=Dias de férias  ◄=Mês atual")
        for item in _capturar(resumo_emp): _print_buf(item)
        _dleve()
        _ln(f"  {'Mês':7}  {'Dias de férias'.ljust(bw)}  {'Dias':5}  {'Func':5}  {'Pico':5}")
        _dleve()
        for m in ev:
            label=_mes_label(m["ano"],m["mes"]); barra=_barra_grafico(m["total_dias"],max_d,bw)
            flag="◄" if m["ano"]==hoje.year and m["mes"]==hoje.month else " "
            _ln(f"  {label}{flag} [{barra}]  {m['total_dias']:4}d  {m['n_func']:4}   {m['pico']:4}")
        _dleve()
        _ln(f"  {t('graf_total_periodo')}: {tot} {t('pa_dias')}  |  {t('graf_meses_ativos')}: {n_c}")
        _ln(f"  {t('graf_detalhe')}")
        _dleve(); fundo(); p()
        op2=inp(t("pag_cmd")).strip().lower()
        if op2=="p":
            meses_com=[ m for m in ev if m["total_dias"]>0]
            if not meses_com: flash(t("graf_sem_dados"),erro=True); return
            def render_mes(m):
                barra=_barra_grafico(m["total_dias"],max_d,bw)
                flag="◄" if m["ano"]==hoje.year and m["mes"]==hoje.month else " "
                _lvz(); _ln(f"  {_mes_label(m['ano'],m['mes'])}{flag}  [{barra}]  {m['total_dias']}d  {m['n_func']}func  pico:{m['pico']}")
                if m["por_func"]:
                    max_f=max(m["por_func"].values(),default=1); bw2=max(8,(_larg()-4)*22//100)
                    for nome,dias in sorted(m["por_func"].items(),key=lambda x:-x[1]):
                        b2=_barra_grafico(dias,max_f,bw2); _ln(f"    [{b2}] {nome}: {dias}d")
            paginar(d,f"{t('graf_titulo')} — detalhado",meses_com,render_mes,resumo_emp)

    elif op=="2":
        setores=ord_setores(d)
        if not setores: flash(t("nenhum_setor"),erro=True); return
        ev_map={s:_evolucao_empresa([f for f in d["funcionarios"] if f["setor"]==s],n_meses) for s in setores}
        bw=max(10,(_larg()-4)*32//100); max_glob=max((m["total_dias"] for ev in ev_map.values() for m in ev),default=1) or 1
        def resumo_set():
            _lnd(t("rel_data"),hoje.strftime("%d/%m/%Y %H:%M")); _lnd(t("graf_periodo"),f"{n_meses} meses")
            _lnd(t("rel_set_cad"),str(len(setores))); _lnd("Legenda","█=Dias  ◄=Mês atual  (escala global)")
        def render_set(setor):
            ev=ev_map[setor]; _lvz(); _ln(f"  ══ {setor} ══"); _dleve()
            for m in ev:
                if m["total_dias"]==0 and m["n_func"]==0: continue
                label=_mes_label(m["ano"],m["mes"]); barra=_barra_grafico(m["total_dias"],max_glob,bw)
                flag="◄" if m["ano"]==hoje.year and m["mes"]==hoje.month else " "
                _ln(f"  {label}{flag} [{barra}]  {m['total_dias']:3}d  {m['n_func']}func")
        paginar(d,f"{t('graf_titulo')} — {t('graf_setor')}",setores,render_set,resumo_set)

    elif op=="3":
        setor=sel_setor(d)
        if not setor: return
        subs=ord_subs(d,setor)
        if not subs: flash(t("nenhum_sub"),erro=True); return
        ev_map={s:_evolucao_empresa([f for f in d["funcionarios"] if f["setor"]==setor and f["subsetor"]==s],n_meses) for s in subs}
        bw=max(10,(_larg()-4)*32//100); max_glob=max((m["total_dias"] for ev in ev_map.values() for m in ev),default=1) or 1
        def resumo_sub():
            _lnd(t("rel_data"),hoje.strftime("%d/%m/%Y %H:%M")); _lnd(t("rel_setor_l"),setor); _lnd(t("graf_periodo"),f"{n_meses} meses")
        def render_sub(sub):
            ev=ev_map[sub]; _lvz(); _ln(f"  ══ {sub} ══"); _dleve()
            for m in ev:
                if m["total_dias"]==0 and m["n_func"]==0: continue
                label=_mes_label(m["ano"],m["mes"]); barra=_barra_grafico(m["total_dias"],max_glob,bw)
                flag="◄" if m["ano"]==hoje.year and m["mes"]==hoje.month else " "
                _ln(f"  {label}{flag} [{barra}]  {m['total_dias']:3}d  {m['n_func']}func")
        paginar(d,f"{t('graf_titulo')} — {setor}",subs,render_sub,resumo_sub)

    elif op=="4":
        func=sel_func(d)
        if not func: return
        ev=_evolucao_func(func,n_meses); an=analise_periodo_atual(d,func)
        max_mes=max((m["dias"] for m in ev),default=1) or 1; max_acum=max((m["acumulado"] for m in ev),default=1) or 1
        bw=max(10,(_larg()-4)*30//100)
        def resumo_func():
            _lnd(t("rel_data"),hoje.strftime("%d/%m/%Y %H:%M")); _lnd(t("rel_nome"),func["nome"])
            _lnd(t("rel_setor_l"),f"{func['setor']} → {func['subsetor']}"); _lnd(t("graf_periodo"),f"{n_meses} meses")
            if func.get("data_admissao"): _lnd(t("data_admissao"),func["data_admissao"])
            if an["tipo"]=="aquisitivo":
                ini_s=an["ini"].strftime("%d/%m/%Y"); fim_s=(an["fim"]-timedelta(days=1)).strftime("%d/%m/%Y")
                _lnd(t("pa_atual")+f" #{an['numero']}",f"{ini_s} → {fim_s}")
                if an["max_dias"] and an["max_dias"]>0:
                    bp=_barra_progresso(an["tirados"],an["max_dias"])
                    if bp: barra,pct=bp; _lnd(t("pa_tirados"),f"{an['tirados']}/{an['max_dias']} {t('pa_dias')}  [{barra}] {pct}%  Restam: {an['restantes']}")
            _lnd("Legenda","Mês=barras mensais  Acumulado=total  ◄=Mês atual")
        def render_func_mes(m):
            label=_mes_label(m["ano"],m["mes"]); b_mes=_barra_grafico(m["dias"],max_mes,bw); b_acum=_barra_grafico(m["acumulado"],max_acum,bw)
            flag="◄" if m["ano"]==hoje.year and m["mes"]==hoje.month else " "
            _lvz()
            _ln(f"  {label}{flag}  Mês      : [{b_mes}]  {m['dias']:3} {t('pa_dias')}")
            _ln(f"  {' '*6}{' '}  Acumulado: [{b_acum}]  {m['acumulado']:3} {t('pa_dias')}")
        paginar(d,f"{t('graf_titulo')} — {func['nome']}",ev,render_func_mes,resumo_func)
    else: flash(t("invalido"),erro=True)

# ══════════════════════════════════════════════════════
#  PAINEL DE FÉRIAS
# ══════════════════════════════════════════════════════
def _calcular_painel(d):
    hoje=datetime.today(); lim30=datetime(hoje.year,hoje.month,hoje.day)+timedelta(days=30); hoje_d=datetime(hoje.year,hoje.month,hoje.day)
    em_ferias=[]; em_30dias=[]
    for func in ord_funcs(d):
        v=f" [{func.get('vinculo','')}]" if func.get("vinculo") else ""
        for f in func["ferias"]:
            ini=conv_data(f["inicio"]); fim=conv_data(f["fim"])
            if not ini or not fim: continue
            if ini<=hoje<=fim:
                em_ferias.append({"nome":func["nome"]+v,"setor":func["setor"],"subsetor":func["subsetor"],"inicio":f["inicio"],"fim":f["fim"],"dias_rest":(fim-hoje_d).days+1,"venda":f.get("venda_ferias",False)}); break
            if hoje_d<ini<=lim30:
                em_30dias.append({"nome":func["nome"]+v,"setor":func["setor"],"subsetor":func["subsetor"],"inicio":f["inicio"],"fim":f["fim"],"dias_ini":(ini-hoje_d).days,"venda":f.get("venda_ferias",False)}); break
    em_ferias.sort(key=lambda x:x["dias_rest"]); em_30dias.sort(key=lambda x:x["dias_ini"])
    return em_ferias, em_30dias

def _linhas_painel_menu(em_ferias, em_30dias, dias_alerta=7):
    linhas=[]; MAX=3
    linhas.append(f"[{t('painel_agora')}]")
    if em_ferias:
        for r in em_ferias[:MAX]: linhas.append(f"  › {r['nome']}  —  até {r['fim']}  ({r['dias_rest']} {t('painel_dias_rest')})")
        if len(em_ferias)>MAX: linhas.append(f"  ... e mais {len(em_ferias)-MAX} funcionário(s)")
    else: linhas.append(f"  {t('menu_nenhum_agora')}")
    linhas.append(f"[{t('menu_inicio_label',n=dias_alerta)}]")
    proximos=[r for r in em_30dias if r["dias_ini"]<=dias_alerta]
    if proximos:
        for r in proximos[:MAX]: linhas.append(f"  › {r['nome']}  —  {r['inicio']}  (em {r['dias_ini']} {t('painel_dias_ini')})")
        if len(proximos)>MAX: linhas.append(f"  ... e mais {len(proximos)-MAX} funcionário(s)")
    else: linhas.append(f"  {t('menu_nenhum_prox',n=dias_alerta)}")
    return linhas

def painel_ferias(d):
    em_ferias,em_30dias=_calcular_painel(d); hoje_str=datetime.today().strftime("%d/%m/%Y  %H:%M")
    itens=[]
    itens.append({"tipo":"secao","txt":t("painel_agora")})
    if em_ferias:
        for r in em_ferias: itens.append({"tipo":"agora",**r})
    else: itens.append({"tipo":"vazio_ag"})
    itens.append({"tipo":"secao","txt":t("painel_30dias")})
    if em_30dias:
        for r in em_30dias: itens.append({"tipo":"em30",**r})
    else: itens.append({"tipo":"vazio_30"})
    def resumo():
        _lnd(t("rel_data"),        hoje_str)
        _lnd(t("painel_em_ferias"),str(len(em_ferias))+" funcionário(s)")
        _lnd(t("painel_em_30d"),   str(len(em_30dias))+" funcionário(s)")
    def render_item(item):
        tipo=item["tipo"]
        if tipo=="secao": _dleve(); _ln(f"  {item['txt']}","center"); _dleve()
        elif tipo=="vazio_ag": _lvz(); _ln(f"  {t('painel_nenhum_ag')}"); _lvz()
        elif tipo=="vazio_30": _lvz(); _ln(f"  {t('painel_nenhum_30')}"); _lvz()
        elif tipo=="agora":
            vd=f"  {t('fer_venda_lbl')}" if item["venda"] else ""
            _lvz(); _ln(f"  › {item['nome']}")
            _ln(f"    {item['setor']}  →  {item['subsetor']}")
            _ln(f"    {item['inicio']}  até  {item['fim']}{vd}")
            _ln(f"    {t('painel_termina')}: {item['dias_rest']} {t('painel_dias_rest')}")
        elif tipo=="em30":
            vd=f"  {t('fer_venda_lbl')}" if item["venda"] else ""
            _lvz(); _ln(f"  › {item['nome']}")
            _ln(f"    {item['setor']}  →  {item['subsetor']}")
            _ln(f"    {item['inicio']}  até  {item['fim']}{vd}")
            _ln(f"    {t('painel_inicia')}: {item['dias_ini']} {t('painel_dias_ini')}")
    paginar(d, t("painel_titulo"), itens, render_item, resumo)

# ══════════════════════════════════════════════════════
#  SETORES E SUBSETORES
# ══════════════════════════════════════════════════════
