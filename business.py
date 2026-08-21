"""Módulo refatorado do Gerenciador de Férias v3.9.1."""
import runtime
globals().update({k: v for k, v in vars(runtime).items() if not k.startswith("__")})

def conv_data(s):
    try:    return datetime.strptime(s.strip(),"%d/%m/%Y")
    except: return None
def calc_dias(i,f):
    a,b=conv_data(i),conv_data(f); return (b-a).days+1 if a and b else 0
def sobrepoem(i1,f1,i2,f2): return i1<=f2 and f1>=i2
def fmt_bool(v):
    if v is None: return "—"
    return {"pt":"Sim","en":"Yes"}[get_idioma()] if v else {"pt":"Não","en":"No"}[get_idioma()]
def fmt_val(tipo,v): return fmt_bool(v) if tipo=="bool" else ("—" if v is None else str(v))
def _chave_sub(s,sub): return f"{s}{SEP}{sub}"
def add_meses(data,n):
    """Adiciona meses preservando o último dia válido do mês de destino."""
    m=data.month+n; a=data.year+(m-1)//12; m=((m-1)%12)+1
    dia=min(data.day, calendar.monthrange(a,m)[1])
    return datetime(a,m,dia)
def _rev(d): return d.get("config",CONFIG_PADRAO).get("direcao","asc")=="desc"
def ord_setores(d):
    ns=list(d["setores"].keys()); rev=_rev(d)
    return sorted(ns,key=lambda x:x.lower(),reverse=rev) if d.get("config",CONFIG_PADRAO).get("ordem_setores","nome")=="nome" else (list(reversed(ns)) if rev else ns)
def ord_subs(d,setor):
    subs=list(d["setores"].get(setor,{}).get("subsetores",[])); rev=_rev(d)
    return sorted(subs,key=lambda x:x.lower(),reverse=rev) if d.get("config",CONFIG_PADRAO).get("ordem_subsetores","nome")=="nome" else (list(reversed(subs)) if rev else subs)
def ord_vinculos(d):
    vs=list(d.get("vinculos",[])); rev=_rev(d)
    return sorted(vs,key=lambda x:x.lower(),reverse=rev) if d.get("config",CONFIG_PADRAO).get("ordem_vinculos","nome")=="nome" else (list(reversed(vs)) if rev else vs)
def ord_funcs(d,lista=None):
    cfg=d.get("config",CONFIG_PADRAO); rev=_rev(d)
    funcs=list(lista if lista is not None else d["funcionarios"])
    chaves={"nome":lambda f:f["nome"].lower(),"setor":lambda f:(f["setor"].lower(),f["subsetor"].lower(),f["nome"].lower()),"subsetor":lambda f:(f["subsetor"].lower(),f["nome"].lower()),"vinculo":lambda f:(f.get("vinculo","").lower(),f["nome"].lower()),"cadastro":lambda f:f.get("_id",0)}
    return sorted(funcs,key=chaves.get(cfg.get("ordem_funcionarios","nome"),chaves["nome"]),reverse=rev)
def ord_ferias(d,ferias):
    cfg=d.get("config",CONFIG_PADRAO); rev=_rev(d)
    def _dt(s):
        try: pp=s.split("/"); return (int(pp[2]),int(pp[1]),int(pp[0]))
        except: return (0,0,0)
    for i,f in enumerate(ferias): f["_idx"]=i
    chaves={"inicio":lambda f:_dt(f.get("inicio","")),"fim":lambda f:_dt(f.get("fim","")),"dias":lambda f:calc_dias(f.get("inicio",""),f.get("fim","")),"cadastro":lambda f:f.get("_idx",0)}
    return sorted(ferias,key=chaves.get(cfg.get("ordem_ferias","inicio"),chaves["inicio"]),reverse=rev)
def sel_setor(d):
    ns=ord_setores(d)
    if not ns: p("  "+t("nenhum_setor")); return None
    p(); p("  "+t("set_disponiveis"))
    for i,n in enumerate(ns,1): p(f"    {i}. {n}")
    p(f"    0. {t('cancelar')}")
    try:
        e=int(inp(t("opcao")).strip())
        if e==0: return None
        if 1<=e<=len(ns): return ns[e-1]
        p("  "+t("fora_intervalo"))
    except ValueError: p("  "+t("so_numero"))
    return None
def sel_sub(d,setor):
    subs=ord_subs(d,setor)
    if not subs: p(f"  '{setor}': {t('nenhum_sub')}"); return None
    p(); p(f"  {t('sub_disponiveis')} '{setor}':")
    for i,s in enumerate(subs,1): p(f"    {i}. {s}")
    p(f"    0. {t('cancelar')}")
    try:
        e=int(inp(t("opcao")).strip())
        if e==0: return None
        if 1<=e<=len(subs): return subs[e-1]
        p("  "+t("fora_intervalo"))
    except ValueError: p("  "+t("so_numero"))
    return None
def sel_func(d,msg=None):
    if msg is None: msg=t("opcao")
    funcs=ord_funcs(d)
    if not funcs: p("  "+t("nenhum_func")); return None
    p(); p("  "+t("fun_lista"))
    for i,f in enumerate(funcs,1):
        v=f" [{f.get('vinculo','')}]" if f.get("vinculo") else ""
        p(f"    {i}. {f['nome']}{v}  ({f['setor']} → {f['subsetor']})")
    p(f"    0. {t('cancelar')}")
    try:
        e=int(inp(msg).strip())
        if e==0: return None
        if 1<=e<=len(funcs): return funcs[e-1]
        p("  "+t("fora_intervalo"))
    except ValueError: p("  "+t("so_numero"))
    return None
def sel_vinculo(d,permitir_nenhum=True):
    vs=ord_vinculos(d)
    if not vs: p("  "+t("nenhum_vinculo")); return None
    p(); p("  "+t("vin_disponiveis"))
    for i,v in enumerate(vs,1): p(f"    {i}. {v}")
    p("    "+(t("vin_sem") if permitir_nenhum else f"0. {t('cancelar')}"))
    try:
        e=int(inp(t("opcao")).strip())
        if e==0: return None
        if 1<=e<=len(vs): return vs[e-1]
        p("  "+t("fora_intervalo"))
    except ValueError: p("  "+t("so_numero"))
    return None

# ── Análise por período aquisitivo ────────────────────
def periodo_aquisitivo_atual(func):
    adm=conv_data(func.get("data_admissao",""))
    if not adm: return None, None, None
    hoje=datetime.today(); ini=adm; n=0
    while True:
        fim=add_meses(ini,12); n+=1
        if ini<=hoje<fim: return ini, fim, n
        if fim>hoje:      return ini, fim, n
        ini=fim
def todos_periodos_aquisitivos(func):
    adm=conv_data(func.get("data_admissao",""))
    if not adm: return []
    hoje=datetime.today(); periodos=[]; ini=adm; n=0
    while True:
        fim=add_meses(ini,12); n+=1
        periodos.append({"ini":ini,"fim":fim,"numero":n})
        if ini<=hoje<fim: break
        if fim>hoje:      break
        ini=fim
    return periodos
def dias_no_periodo(f, ini_p, fim_p):
    try:
        fi=datetime.strptime(f["inicio"].strip(),"%d/%m/%Y"); ff=datetime.strptime(f["fim"].strip(),"%d/%m/%Y")
        fim_inc=fim_p-timedelta(days=1); ie=max(fi,ini_p); fe=min(ff,fim_inc)
        return max(0,(fe-ie).days+1)
    except: return 0
def ferias_no_periodo(ferias, ini_p, fim_p):
    fim_inc=fim_p-timedelta(days=1)
    return [f for f in ferias if conv_data(f["inicio"]) and conv_data(f["fim"]) and conv_data(f["inicio"])<=fim_inc and conv_data(f["fim"])>=ini_p]
def ferias_no_ano_civil(ferias,ano):
    res=[]
    for f in ferias:
        try:
            fi=datetime.strptime(f["inicio"].strip(),"%d/%m/%Y"); ff=datetime.strptime(f["fim"].strip(),"%d/%m/%Y")
            if fi.year<=ano<=ff.year: res.append(f)
        except: pass
    return res
def dias_no_ano_civil(f,ano):
    try:
        fi=datetime.strptime(f["inicio"].strip(),"%d/%m/%Y"); ff=datetime.strptime(f["fim"].strip(),"%d/%m/%Y")
        ie=max(fi,datetime(ano,1,1)); fe=min(ff,datetime(ano,12,31)); return max(0,(fe-ie).days+1)
    except: return 0
def analise_periodo_atual(d, func):
    ini,fim,n=periodo_aquisitivo_atual(func)
    setor=func["setor"]; subsetor=func["subsetor"]; vinculo=func.get("vinculo","")
    max_d=obter_regra(d,"max_dias_ano",setor,subsetor,vinculo)
    if ini is None:
        ano=datetime.today().year
        tirados=sum(dias_no_ano_civil(f,ano) for f in ferias_no_ano_civil(func["ferias"],ano))
        restantes=max(0,max_d-tirados) if max_d and max_d>0 else None
        return {"ini":None,"fim":None,"numero":None,"tirados":tirados,"max_dias":max_d,"restantes":restantes,"tipo":"civil","ano_civil":ano}
    tirados=sum(dias_no_periodo(f,ini,fim) for f in ferias_no_periodo(func["ferias"],ini,fim))
    restantes=max(0,max_d-tirados) if max_d and max_d>0 else None
    return {"ini":ini,"fim":fim,"numero":n,"tirados":tirados,"max_dias":max_d,"restantes":restantes,"tipo":"aquisitivo"}
def classificar_ferias(func):
    hoje=datetime.today(); pas,atu,fut=[],[],[]
    for f in func["ferias"]:
        ini=conv_data(f["inicio"]); fim=conv_data(f["fim"])
        if not ini or not fim: continue
        if fim<hoje:           pas.append(f)
        elif ini<=hoje<=fim:   atu.append(f)
        else:                  fut.append(f)
    return pas,atu,fut
def calc_periodos_aquisitivos(func):
    adm=conv_data(func.get("data_admissao",""))
    if not adm: return []
    hoje=datetime.today(); periodos=[]; ini=adm
    for _ in range(40):
        fim=add_meses(ini,12)
        if fim>hoje: break
        fim_con=add_meses(fim,12)
        ferias_p=ferias_no_periodo(func["ferias"],ini,fim)
        dias_t=sum(dias_no_periodo(f,ini,fim) for f in ferias_p)
        if dias_t>0: status="ok"
        elif fim_con<hoje: status="vencida"
        elif (fim_con-hoje).days<=60: status="a_vencer"
        else: status="pendente"
        periodos.append({"ini_aq":ini,"fim_aq":fim,"fim_con":fim_con,"dias_tirados":dias_t,"status":status,"ferias_periodo":ferias_p})
        ini=fim
    return periodos
def situacao_geral_func(func):
    try:
        per=calc_periodos_aquisitivos(func)
        if not per: return "sem_admissao"
        pri={"vencida":4,"a_vencer":3,"pendente":2,"ok":1}
        return max(per,key=lambda x:pri.get(x["status"],0))["status"]
    except: return "sem_admissao"
def _contar_vencidas(d):
    try: return sum(1 for f in d["funcionarios"] if f.get("data_admissao","") and situacao_geral_func(f)=="vencida")
    except: return 0
def _barra_progresso(tirados, max_d, largura=18):
    if not max_d or max_d<=0: return None
    fill=round(min(tirados,max_d)/max_d*largura); barra="█"*fill+"░"*(largura-fill)
    pct=round(min(tirados,max_d)/max_d*100); return barra, pct
def _linha_periodo_atual(func, d):
    an=analise_periodo_atual(d,func)
    if an["tipo"]=="civil": prefixo=f"Ano {an['ano_civil']}"
    else:
        ini_s=an["ini"].strftime("%d/%m/%Y"); fim_s=(an["fim"]-timedelta(days=1)).strftime("%d/%m/%Y")
        prefixo=f"Prd.{an['numero']} ({ini_s}–{fim_s})"
    if an["max_dias"] and an["max_dias"]>0:
        bp=_barra_progresso(an["tirados"],an["max_dias"],14)
        if bp: barra,pct=bp; return f"    {prefixo}: {an['tirados']}/{an['max_dias']} dias  [{barra}] {pct}%  Restam: {an['restantes']}"
    return f"    {prefixo}: {an['tirados']} dias  {t('pa_ilimitado')}"

# ── Motor de regras ───────────────────────────────────
def obter_regra(d,campo,setor=None,subsetor=None,vinculo=None):
    CR=_campos_regras(); r=d["regras"]
    if setor and subsetor:
        bloco=r.get("por_subsetor",{}).get(_chave_sub(setor,subsetor),{})
        if campo in bloco: return bloco[campo]
    if setor:
        bloco=r.get("por_setor",{}).get(setor,{})
        if campo in bloco: return bloco[campo]
    if vinculo:
        bloco=r.get("por_vinculo",{}).get(vinculo,{})
        if campo in bloco: return bloco[campo]
    return r["global"].get(campo,CR[campo]["padrao"])

def validar_agendamento(d,func,inicio,fim):
    setor=func["setor"]; subsetor=func["subsetor"]; vinculo=func.get("vinculo","")
    dias_p=(fim-inicio).days+1; erros=[]
    av=obter_regra(d,"aviso_previo_dias",setor,subsetor,vinculo)
    if av and av>0:
        diff=(inicio-datetime.today()).days
        if diff<av: erros.append(f"Antecedência mínima de {av} dia(s) não cumprida ({max(0,diff)} disponíveis).")
    mn=obter_regra(d,"min_dias_periodo",setor,subsetor,vinculo)
    if mn and mn>0 and dias_p<mn: erros.append(f"Período mínimo de {mn} dia(s) (informado: {dias_p}).")
    ini_aq,fim_aq,n_aq=periodo_aquisitivo_atual(func)
    if ini_aq:
        ini_ref,fim_ref=ini_aq,fim_aq
        if inicio>=fim_aq: ini_ref=fim_aq; fim_ref=add_meses(fim_aq,12)
        mx=obter_regra(d,"max_dias_ano",setor,subsetor,vinculo)
        if mx and mx>0:
            usados=sum(dias_no_periodo(f,ini_ref,fim_ref) for f in ferias_no_periodo(func["ferias"],ini_ref,fim_ref))
            dias_ef=dias_no_periodo({"inicio":inicio.strftime("%d/%m/%Y"),"fim":fim.strftime("%d/%m/%Y")},ini_ref,fim_ref)
            if usados+dias_ef>mx:
                label=f"{ini_ref.strftime('%d/%m/%Y')} – {fim_ref.strftime('%d/%m/%Y')}"
                erros.append(f"Limite de {mx} dias no período aquisitivo excedido (já: {usados} + novo: {dias_ef} = {usados+dias_ef}). Período: {label}.")
        mp=obter_regra(d,"max_periodos_ano",setor,subsetor,vinculo)
        if mp and mp>0:
            qtd=len(ferias_no_periodo(func["ferias"],ini_ref,fim_ref))
            if qtd>=mp: erros.append(f"Limite de {mp} período(s) no período aquisitivo atingido ({qtd} cadastrado(s)).")
    else:
        ano=inicio.year
        mx=obter_regra(d,"max_dias_ano",setor,subsetor,vinculo)
        if mx and mx>0:
            usados=sum(dias_no_ano_civil(f,ano) for f in ferias_no_ano_civil(func["ferias"],ano))
            if usados+dias_p>mx: erros.append(f"Limite anual de {mx} dias excedido (já: {usados} + novo: {dias_p}).")
        mp=obter_regra(d,"max_periodos_ano",setor,subsetor,vinculo)
        if mp and mp>0:
            qtd=len(ferias_no_ano_civil(func["ferias"],ano))
            if qtd>=mp: erros.append(f"Limite de {mp} período(s)/ano atingido ({qtd} cadastrado(s)).")
    pc=obter_regra(d,"permite_concomitantes",setor,subsetor,vinculo)
    mc=obter_regra(d,"max_concomitantes",setor,subsetor,vinculo)
    cnt,nomes=[],[]
    for o in d["funcionarios"]:
        if o["nome"].lower()==func["nome"].lower(): continue
        if o["setor"]!=setor or o["subsetor"]!=subsetor: continue
        for f in o["ferias"]:
            io,fo=conv_data(f["inicio"]),conv_data(f["fim"])
            if io and fo and sobrepoem(inicio,fim,io,fo): cnt.append(o); nomes.append(o["nome"]); break
    if not pc and cnt: erros.append(f"Férias simultâneas não permitidas no subsetor '{subsetor}'. Conflito: {', '.join(nomes)}.")
    elif pc and mc and mc>0 and len(cnt)>=mc: erros.append(f"Máximo de {mc} simultâneo(s) atingido. Conflito: {', '.join(nomes)}.")
    return erros

# ── Validação automática ──────────────────────────────
def auditar_func(d,func):
    pends=[]; setor=func["setor"]; subsetor=func["subsetor"]; vinculo=func.get("vinculo","")
    ini_aq,fim_aq,_=periodo_aquisitivo_atual(func)
    for f in func["ferias"]:
        ep=[]; ini,fim=conv_data(f["inicio"]),conv_data(f["fim"])
        if not ini or not fim: pends.append({"tipo":"periodo","ref":f"{f.get('inicio','?')} - {f.get('fim','?')}","erros":["Datas inválidas."]}); continue
        dias=(fim-ini).days+1
        mn=obter_regra(d,"min_dias_periodo",setor,subsetor,vinculo)
        if mn and mn>0 and dias<mn: ep.append(f"Abaixo do mínimo de {mn} dia(s) ({dias} registrado(s)).")
        if f.get("venda_ferias") and not obter_regra(d,"permite_venda_ferias",setor,subsetor,vinculo):
            ep.append("Venda de férias marcada, mas a regra não permite.")
        pc=obter_regra(d,"permite_concomitantes",setor,subsetor,vinculo); mc=obter_regra(d,"max_concomitantes",setor,subsetor,vinculo)
        cnt,nomes=0,[]
        for o in d["funcionarios"]:
            if o["nome"].lower()==func["nome"].lower(): continue
            if o["setor"]!=setor or o["subsetor"]!=subsetor: continue
            for of in o["ferias"]:
                io,fo=conv_data(of["inicio"]),conv_data(of["fim"])
                if io and fo and sobrepoem(ini,fim,io,fo): cnt+=1; nomes.append(o["nome"]); break
        if not pc and cnt>0: ep.append(f"Simultânea com {', '.join(nomes)} (não permitido).")
        elif pc and mc and mc>0 and cnt>=mc: ep.append(f"Excede o máximo de {mc} simultâneo(s). Conflito: {', '.join(nomes)}.")
        if ep: pends.append({"tipo":"periodo","ref":f"{f['inicio']} – {f['fim']} ({dias} dias)","erros":ep})
    todos=todos_periodos_aquisitivos(func) if ini_aq else []
    for prd in todos:
        ea=[]; ip=prd["ini"]; fp=prd["fim"]
        mp=obter_regra(d,"max_periodos_ano",setor,subsetor,vinculo)
        qtd=len(ferias_no_periodo(func["ferias"],ip,fp))
        if mp and mp>0 and qtd>mp: ea.append(f"{qtd} período(s) no prd.aquisitivo {ip.strftime('%d/%m/%Y')}–{fp.strftime('%d/%m/%Y')}, máximo: {mp}.")
        mx=obter_regra(d,"max_dias_ano",setor,subsetor,vinculo)
        if mx and mx>0:
            tot=sum(dias_no_periodo(f,ip,fp) for f in ferias_no_periodo(func["ferias"],ip,fp))
            if tot>mx: ea.append(f"{tot} dia(s) no prd.aquisitivo, máximo: {mx}.")
        if ea: pends.append({"tipo":"aquisitivo","ref":f"Prd.{prd['numero']} ({ip.strftime('%d/%m/%Y')}–{fp.strftime('%d/%m/%Y')})","erros":ea})
    if not ini_aq:
        anos=set()
        for f in func["ferias"]:
            fi=conv_data(f["inicio"])
            if fi: anos.add(fi.year)
        for ano in sorted(anos):
            ea=[]
            mp=obter_regra(d,"max_periodos_ano",setor,subsetor,vinculo)
            qtd=len(ferias_no_ano_civil(func["ferias"],ano))
            if mp and mp>0 and qtd>mp: ea.append(f"{qtd} período(s) em {ano}, máximo: {mp}.")
            mx=obter_regra(d,"max_dias_ano",setor,subsetor,vinculo)
            if mx and mx>0:
                tot=sum(dias_no_ano_civil(f,ano) for f in ferias_no_ano_civil(func["ferias"],ano))
                if tot>mx: ea.append(f"{tot} dia(s) em {ano}, máximo: {mx}.")
            if ea: pends.append({"tipo":"ano","ref":str(ano),"erros":ea})
    return pends
def auditar_sistema(d): return [{"func":f,"pendencias":auditar_func(d,f)} for f in d["funcionarios"] if f["ferias"] and auditar_func(d,f)]
def contar_pends(d): return sum(len(auditar_func(d,f)) for f in d["funcionarios"] if f["ferias"])

# ── Render helpers ────────────────────────────────────
