"""Ponto de composição da aplicação."""
import runtime, database, business, dashboard, menus

for _module in (runtime, database, business, dashboard, menus):
    globals().update({k: v for k, v in vars(_module).items() if not k.startswith("__")})


def main():
    """Inicializa o banco e inicia a interface CLI."""
    runtime.verificar_ambiente()
    runtime.preparar_ambiente()
    database._init_banco()
    database._criar_admin_inicial()
    menus.menu_principal()
