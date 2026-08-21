# Compatibilidade Linux

## Princípio

O Gerenciador de Férias é distribuído como uma pasta autocontida. O programa não depende do diretório de trabalho atual para localizar o banco.

A localização é determinada pelo diretório do próprio arquivo `core.py`, por meio de `Path(__file__).resolve().parent`.

Isso permite:

```bash
cd /tmp
python3 /opt/gerenciador-ferias/gerenciador_ferias.py
```

sem criar `dados_ferias.db` em `/tmp`.

## Dados persistentes

Os arquivos de runtime ficam juntos:

```text
gerenciador-ferias/
├── gerenciador_ferias.py
├── app.py
├── business.py
├── core.py
├── dashboard.py
├── database.py
├── menus.py
├── runtime.py
├── dados_ferias.db
└── backup_*.db
```

Não são utilizados `XDG_DATA_HOME` ou `GERENCIADOR_FERIAS_DATA_DIR`.

## Sistemas-alvo

A matriz de CI utiliza Python 3.10 a 3.14. O objetivo é compatibilidade com distribuições Linux que forneçam uma dessas versões, incluindo famílias Ubuntu, Debian e RHEL-like.

A compatibilidade efetiva de uma distribuição depende da versão do Python disponível nela.

## Requisitos do sistema

Não há pacotes Python de runtime externos. O aplicativo utiliza a biblioteca padrão, incluindo `sqlite3`.

Para uma instalação institucional, recomenda-se criar uma pasta com permissões adequadas e executar o programa com um usuário que tenha permissão de leitura/escrita nela, pois o banco fica ao lado do programa.

## Verificação

```bash
bash scripts/verify-linux.sh
```

O teste também verifica que alterar o `cwd` não altera a localização do banco.
