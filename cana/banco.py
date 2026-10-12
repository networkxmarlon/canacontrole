"""Persistência Oracle real e modo de demonstração JSON escolhido explicitamente."""
from datetime import datetime
from decimal import Decimal
import getpass
import json
import os
from pathlib import Path
from .arquivos import ler_json, escrever_json
from .dominio import CAMPOS, LIMITES, validar_registro, validar_tabela

RAIZ = Path(__file__).resolve().parents[1]
SQL_LISTAR = """SELECT id, talhao, data_colheita, area_ha, colhida_t,
    amostra_m2, perda_kg, preco_t, origem, observacao FROM ftc_colheitas
    ORDER BY data_colheita, talhao"""
SQL_INSERIR = """INSERT INTO ftc_colheitas
    (id, talhao, data_colheita, area_ha, colhida_t, amostra_m2,
     perda_kg, preco_t, origem, observacao)
    VALUES (:id, :talhao, :data_colheita, :area_ha, :colhida_t,
            :amostra_m2, :perda_kg, :preco_t, :origem, :observacao)"""
SQL_EDITAR = """UPDATE ftc_colheitas SET talhao=:talhao,
    data_colheita=:data_colheita, area_ha=:area_ha, colhida_t=:colhida_t,
    amostra_m2=:amostra_m2, perda_kg=:perda_kg, preco_t=:preco_t,
    origem=:origem, observacao=:observacao WHERE id=:id"""

def abrir_demo(caminho=None):
    caminho = Path(caminho) if caminho else RAIZ / "dados/demo_local.json"
    if not caminho.exists():
        escrever_json(caminho, [])
    ler_json(caminho)  # Arquivo inválido não é apagado nem substituído por uma tabela vazia.
    return {"modo": "demo", "arquivo": caminho}

def abrir_oracle():
    """Conexão Thin: senha digitada localmente ou obtida de variável de ambiente."""
    try:
        import oracledb
    except ImportError as erro:
        raise RuntimeError("Instale a dependência: python -m pip install -r requirements.txt") from erro
    configuracao = {}
    caminho = RAIZ / "config/oracle.json"
    if caminho.exists():
        with caminho.open(encoding="utf-8-sig") as arquivo:
            configuracao = json.load(arquivo)
        if (not isinstance(configuracao, dict)
                or set(configuracao) != {"usuario", "dsn"}):
            raise ValueError("config/oracle.json deve conter somente usuario e dsn.")
    usuario = os.environ.get("CANA_ORACLE_USER") or configuracao.get("usuario")
    dsn = os.environ.get("CANA_ORACLE_DSN") or configuracao.get("dsn")
    if (not isinstance(usuario, str) or not usuario.strip()
            or not isinstance(dsn, str) or not dsn.strip()
            or "SEU_USUARIO" in usuario or "HOST_ORACLE" in dsn):
        raise ValueError("Configure usuario e dsn em config/oracle.json. Veja PASSO_A_PASSO.md.")
    senha = os.environ.get("CANA_ORACLE_PASSWORD") or getpass.getpass("Senha Oracle (não aparece): ")
    if not senha:
        raise ValueError("A senha Oracle não pode ficar vazia.")
    try:
        conexao = oracledb.connect(user=usuario.strip(), password=senha, dsn=dsn.strip(),
                                  tcp_connect_timeout=10, retry_count=0)
    except oracledb.Error as erro:
        codigo = getattr(erro.args[0], "full_code", "erro de conexão")
        raise RuntimeError(f"Oracle indisponível ({codigo}). Confira host, serviço, acesso e senha.") from erro
    conexao.call_timeout = 15000
    return {"modo": "oracle", "conexao": conexao}

def criar_tabelas(base):
    """DDL opcional, executado uma vez. Não contém DROP nem limpeza automática."""
    if base["modo"] != "oracle":
        raise ValueError("A criação da tabela exige conexão Oracle.")
    sql = (RAIZ / "sql/criar_tabelas.sql").read_text(encoding="utf-8").strip().rstrip(";")
    with base["conexao"].cursor() as cursor:
        cursor.execute(sql)

def listar(base):
    """Carrega uma lista de dicionários (tabela de memória)."""
    if base["modo"] == "demo":
        return sorted(ler_json(base["arquivo"]), key=lambda r: (r["data_colheita"], r["talhao"]))
    with base["conexao"].cursor() as cursor:
        # O driver entrega NUMBER como Decimal, evitando conversões intermediárias para float.
        def numeros_decimais(cur, metadata):
            import oracledb
            if metadata.type_code == oracledb.DB_TYPE_NUMBER:
                return cur.var(Decimal, arraysize=cur.arraysize)
        cursor.outputtypehandler = numeros_decimais
        cursor.execute(SQL_LISTAR)
        linhas = cursor.fetchmany(1001)
    registros = []
    for linha in linhas:
        registro = dict(zip(CAMPOS, linha))
        registro["data_colheita"] = registro["data_colheita"].date().isoformat()
        registro["observacao"] = registro["observacao"] or ""
        for campo in LIMITES:
            registro[campo] = str(registro[campo])
        registros.append(registro)
    return validar_tabela(registros)

def _parametros(registro):
    resultado = validar_registro(registro)
    resultado["data_colheita"] = datetime.strptime(resultado["data_colheita"], "%Y-%m-%d")
    for campo in LIMITES:
        resultado[campo] = Decimal(resultado[campo])
    return resultado

def inserir_lote(base, novos):
    """Importação atômica: valida tudo e então grava tudo ou nada."""
    novos = validar_tabela(novos)
    existentes = listar(base)
    tabela = validar_tabela(existentes + novos)
    if not novos:
        return 0
    if base["modo"] == "demo":
        escrever_json(base["arquivo"], tabela)
    else:
        conexao = base["conexao"]
        try:
            with conexao.cursor() as cursor:
                cursor.executemany(SQL_INSERIR, [_parametros(r) for r in novos])
            conexao.commit()
        except Exception:
            conexao.rollback()
            raise
    return len(novos)

def editar(base, registro):
    registro = validar_registro(registro)
    existentes = listar(base)
    if not any(r["id"] == registro["id"] for r in existentes):
        raise ValueError("Registro não encontrado.")
    tabela = validar_tabela([registro if r["id"] == registro["id"] else r for r in existentes])
    if base["modo"] == "demo":
        escrever_json(base["arquivo"], tabela)
    else:
        conexao = base["conexao"]
        try:
            with conexao.cursor() as cursor:
                cursor.execute(SQL_EDITAR, _parametros(registro))
                if cursor.rowcount != 1:
                    raise ValueError("Registro alterado por outra sessão; consulte novamente.")
            conexao.commit()
        except Exception:
            conexao.rollback()
            raise

def excluir(base, identificador):
    existentes = listar(base)
    if not any(r["id"] == identificador for r in existentes):
        raise ValueError("Registro não encontrado.")
    if base["modo"] == "demo":
        escrever_json(base["arquivo"], [r for r in existentes if r["id"] != identificador])
    else:
        conexao = base["conexao"]
        try:
            with conexao.cursor() as cursor:
                cursor.execute("DELETE FROM ftc_colheitas WHERE id=:id", {"id": identificador})
                if cursor.rowcount != 1:
                    raise ValueError("Registro alterado por outra sessão; consulte novamente.")
            conexao.commit()
        except Exception:
            conexao.rollback()
            raise

def fechar(base):
    if base["modo"] == "oracle":
        base["conexao"].close()
