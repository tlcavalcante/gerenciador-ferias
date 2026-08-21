"""Persistência SQLite do Gerenciador de Férias."""
from pathlib import Path
import runtime
globals().update({k: v for k, v in vars(runtime).items() if not k.startswith("__")})

def _conn():
    con=sqlite3.connect(BANCO_DADOS); con.execute("PRAGMA foreign_keys = ON")
    con.row_factory=sqlite3.Row; return con

_PASSWORD_ITERATIONS = 600_000

def _hash(senha):
    """Gera hash PBKDF2-HMAC-SHA256 versionado."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, _PASSWORD_ITERATIONS)
    return f"pbkdf2_sha256${_PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"

def _verificar_senha(senha, armazenada):
    """Verifica hashes atuais e SHA-256 legados para migração automática."""
    if not armazenada:
        return False, False
    if armazenada.startswith("pbkdf2_sha256$"):
        try:
            _, iteracoes, salt_hex, digest_hex = armazenada.split("$", 3)
            atual = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), bytes.fromhex(salt_hex), int(iteracoes))
            return hmac.compare_digest(atual, bytes.fromhex(digest_hex)), False
        except (ValueError, TypeError):
            return False, False
    legado = hashlib.sha256(senha.encode("utf-8")).hexdigest()
    return hmac.compare_digest(armazenada, legado), True

def _init_banco():
    con=_conn()
    con.executescript("""
        CREATE TABLE IF NOT EXISTS setores (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE);
        CREATE TABLE IF NOT EXISTS subsetores (id INTEGER PRIMARY KEY AUTOINCREMENT, setor TEXT NOT NULL, nome TEXT NOT NULL, UNIQUE(setor,nome));
        CREATE TABLE IF NOT EXISTS vinculos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE);
        CREATE TABLE IF NOT EXISTS funcionarios (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, setor TEXT NOT NULL, subsetor TEXT NOT NULL, vinculo TEXT NOT NULL DEFAULT '', data_admissao TEXT NOT NULL DEFAULT '');
        CREATE TABLE IF NOT EXISTS ferias (id INTEGER PRIMARY KEY AUTOINCREMENT, funcionario_id INTEGER NOT NULL, inicio TEXT NOT NULL, fim TEXT NOT NULL, venda_ferias INTEGER NOT NULL DEFAULT 0, FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS regras (id INTEGER PRIMARY KEY AUTOINCREMENT, nivel TEXT NOT NULL, referencia TEXT NOT NULL DEFAULT '', campo TEXT NOT NULL, valor TEXT NOT NULL, UNIQUE(nivel, referencia, campo));
        CREATE TABLE IF NOT EXISTS configuracoes (chave TEXT PRIMARY KEY, valor TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, login TEXT NOT NULL UNIQUE, nome TEXT NOT NULL, senha_hash TEXT NOT NULL, nivel TEXT NOT NULL DEFAULT 'usuario', failed_attempts INTEGER NOT NULL DEFAULT 0, locked_until TEXT NOT NULL DEFAULT '', last_login TEXT NOT NULL DEFAULT '');
    """)
    for table, column, definition in [
        ("funcionarios", "data_admissao", "TEXT NOT NULL DEFAULT ''"),
        ("usuarios", "failed_attempts", "INTEGER NOT NULL DEFAULT 0"),
        ("usuarios", "locked_until", "TEXT NOT NULL DEFAULT ''"),
        ("usuarios", "last_login", "TEXT NOT NULL DEFAULT ''"),
    ]:
        try:
            con.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        except sqlite3.OperationalError as exc:
            if "duplicate column name" not in str(exc).lower():
                con.close(); raise
    con.commit(); con.close()
    try:
        Path(BANCO_DADOS).chmod(0o600)
    except OSError:
        pass

def _criar_admin_inicial():
    """Solicita o primeiro administrador, sem credencial padrão."""
    _init_banco()
    con=_conn(); existe=con.execute("SELECT 1 FROM usuarios LIMIT 1").fetchone(); con.close()
    if existe: return True
    while True:
        limpar(); titulo_box("CONFIGURAÇÃO INICIAL"); _lvz()
        _ln("  Nenhum usuário cadastrado.","center")
        _ln("  Crie o primeiro administrador do sistema.","center"); _lvz(); fundo(); p()
        login=inp("Login do administrador:").strip(); nome=inp("Nome do administrador:").strip()
        senha=inp_s("Senha:"); confirmacao=inp_s("Confirme a senha:")
        if not login or not nome or not senha: flash("Todos os campos são obrigatórios.",erro=True); continue
        if senha!=confirmacao: flash("As senhas não conferem.",erro=True); continue
        con=_conn()
        try:
            con.execute("INSERT INTO usuarios (login,nome,senha_hash,nivel) VALUES (?,?,?,?)",(login,nome,_hash(senha),"admin")); con.commit(); con.close(); return True
        except sqlite3.IntegrityError:
            con.close(); flash("Esse login já existe.",erro=True)

def _regras_padrao():
    CR=_campos_regras()
    return {"global":{c:m["padrao"] for c,m in CR.items()},"por_vinculo":{},"por_setor":{},"por_subsetor":{}}
def _v2s(v): return "true" if v is True else "false" if v is False else str(v)
def _s2v(tipo,s):
    if tipo=="bool": return s=="true"
    try: return int(s)
    except: return 0
def _migrar_json():
    JF = runtime._LEGACY_JSON
    if not JF.exists():
        JF = BANCO_DADOS.parent / "dados_ferias.json"
    if not JF.exists(): return
    try:
        con=_conn()
        if con.execute("SELECT COUNT(*) as c FROM setores").fetchone()["c"]>0:
            con.close(); os.rename(JF,JF+".bak"); return
        con.close()
        with open(JF,"r",encoding="utf-8") as f: ant=json.load(f)
        d={"setores":ant.get("setores",{}),"funcionarios":ant.get("funcionarios",[]),
           "vinculos":ant.get("vinculos",["CLT","PJ","Estatutário"]),
           "regras":ant.get("regras",_regras_padrao()),"config":CONFIG_PADRAO}
        d["regras"].setdefault("por_subsetor",{}); salvar_dados(d); os.replace(JF, Path(str(JF) + ".bak"))
    except (OSError, ValueError, json.JSONDecodeError):
        return
def carregar_dados():
    _init_banco(); _migrar_json()
    con=_conn(); c=con.cursor(); c2=con.cursor()
    setores={}
    for r in c.execute("SELECT nome FROM setores ORDER BY id").fetchall(): setores[r["nome"]]={"subsetores":[]}
    for r in c.execute("SELECT setor,nome FROM subsetores ORDER BY id").fetchall():
        if r["setor"] in setores: setores[r["setor"]]["subsetores"].append(r["nome"])
    vinculos=[r["nome"] for r in c.execute("SELECT nome FROM vinculos ORDER BY id")]
    if not vinculos:
        vinculos=["CLT","PJ","Estatutário"]
        for v in vinculos: c.execute("INSERT OR IGNORE INTO vinculos (nome) VALUES (?)",(v,))
        con.commit()
    funcs=[]
    for fr in c.execute("SELECT id,nome,setor,subsetor,vinculo,data_admissao FROM funcionarios ORDER BY id").fetchall():
        ferias=[]
        for pr in c2.execute("SELECT inicio,fim,venda_ferias FROM ferias WHERE funcionario_id=? ORDER BY id",(fr["id"],)):
            ferias.append({"inicio":pr["inicio"],"fim":pr["fim"],"venda_ferias":bool(pr["venda_ferias"])})
        funcs.append({"_id":fr["id"],"nome":fr["nome"],"setor":fr["setor"],"subsetor":fr["subsetor"],"vinculo":fr["vinculo"],"data_admissao":fr["data_admissao"] or "","ferias":ferias})
    CR=_campos_regras(); regras=_regras_padrao()
    for rr in c.execute("SELECT nivel,referencia,campo,valor FROM regras"):
        m=CR.get(rr["campo"])
        if not m: continue
        v=_s2v(m["tipo"],rr["valor"])
        if   rr["nivel"]=="global":   regras["global"][rr["campo"]]=v
        elif rr["nivel"]=="vinculo":  regras["por_vinculo"].setdefault(rr["referencia"],{})[rr["campo"]]=v
        elif rr["nivel"]=="setor":    regras["por_setor"].setdefault(rr["referencia"],{})[rr["campo"]]=v
        elif rr["nivel"]=="subsetor": regras["por_subsetor"].setdefault(rr["referencia"],{})[rr["campo"]]=v
    config=dict(CONFIG_PADRAO)
    for cr in c.execute("SELECT chave,valor FROM configuracoes"):
        if cr["chave"] in CONFIG_PADRAO: config[cr["chave"]]=cr["valor"]
        elif cr["chave"]=="idioma": set_idioma(cr["valor"])
    con.close()
    return {"setores":setores,"funcionarios":funcs,"vinculos":vinculos,"regras":regras,"config":config}
def salvar_dados(d):
    con=_conn(); c=con.cursor()
    ns=list(d["setores"].keys())
    c.execute(f"DELETE FROM setores WHERE nome NOT IN ({','.join('?'*len(ns))})" if ns else "DELETE FROM setores",ns)
    for setor,info in d["setores"].items():
        c.execute("INSERT OR IGNORE INTO setores (nome) VALUES (?)",(setor,))
        subs=info.get("subsetores",[])
        c.execute(f"DELETE FROM subsetores WHERE setor=? AND nome NOT IN ({','.join('?'*len(subs))})" if subs else "DELETE FROM subsetores WHERE setor=?",[setor]+subs if subs else [setor])
        for sub in subs: c.execute("INSERT OR IGNORE INTO subsetores (setor,nome) VALUES (?,?)",(setor,sub))
    nv=list(d.get("vinculos",[]))
    c.execute(f"DELETE FROM vinculos WHERE nome NOT IN ({','.join('?'*len(nv))})" if nv else "DELETE FROM vinculos",nv)
    for v in nv: c.execute("INSERT OR IGNORE INTO vinculos (nome) VALUES (?)",(v,))
    ids_ok=set()
    for func in d["funcionarios"]:
        fid=func.get("_id"); adm=func.get("data_admissao","") or ""
        if fid:
            c.execute("UPDATE funcionarios SET nome=?,setor=?,subsetor=?,vinculo=?,data_admissao=? WHERE id=?",
                      (func["nome"],func["setor"],func["subsetor"],func.get("vinculo",""),adm,fid))
        else:
            c.execute("INSERT INTO funcionarios (nome,setor,subsetor,vinculo,data_admissao) VALUES (?,?,?,?,?)",
                      (func["nome"],func["setor"],func["subsetor"],func.get("vinculo",""),adm))
            fid=c.lastrowid; func["_id"]=fid
        ids_ok.add(fid)
        c.execute("DELETE FROM ferias WHERE funcionario_id=?",(fid,))
        for f in func.get("ferias",[]):
            c.execute("INSERT INTO ferias (funcionario_id,inicio,fim,venda_ferias) VALUES (?,?,?,?)",
                      (fid,f["inicio"],f["fim"],1 if f.get("venda_ferias") else 0))
    if ids_ok: c.execute(f"DELETE FROM funcionarios WHERE id NOT IN ({','.join('?'*len(ids_ok))})",list(ids_ok))
    else: c.execute("DELETE FROM funcionarios")
    c.execute("DELETE FROM regras"); r=d["regras"]
    for campo,val in r["global"].items():
        c.execute("INSERT INTO regras (nivel,referencia,campo,valor) VALUES (?,?,?,?)",("global","",campo,_v2s(val)))
    for vinc,bloco in r.get("por_vinculo",{}).items():
        for campo,val in bloco.items():
            c.execute("INSERT INTO regras (nivel,referencia,campo,valor) VALUES (?,?,?,?)",("vinculo",vinc,campo,_v2s(val)))
    for setor,bloco in r.get("por_setor",{}).items():
        for campo,val in bloco.items():
            c.execute("INSERT INTO regras (nivel,referencia,campo,valor) VALUES (?,?,?,?)",("setor",setor,campo,_v2s(val)))
    for ref,bloco in r.get("por_subsetor",{}).items():
        for campo,val in bloco.items():
            c.execute("INSERT INTO regras (nivel,referencia,campo,valor) VALUES (?,?,?,?)",("subsetor",ref,campo,_v2s(val)))
    c.execute("DELETE FROM configuracoes")
    for chave,val in d.get("config",CONFIG_PADRAO).items():
        c.execute("INSERT INTO configuracoes (chave,valor) VALUES (?,?)",(chave,str(val)))
    c.execute("INSERT OR REPLACE INTO configuracoes (chave,valor) VALUES (?,?)",("idioma",get_idioma()))
    con.commit(); con.close()

# ── Utilitários ───────────────────────────────────────
