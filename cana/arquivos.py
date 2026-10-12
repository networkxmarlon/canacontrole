"""Manipulação explícita de arquivos texto e JSON em UTF-8."""
import json
import os
from pathlib import Path
import tempfile
from .dominio import validar_tabela

def _rejeitar_constante(valor):
    raise ValueError(f"JSON inválido: constante {valor} não permitida.")

def _sem_chaves_repetidas(pares):
    resultado = {}
    for chave, valor in pares:
        if chave in resultado:
            raise ValueError(f"JSON inválido: chave repetida {chave}.")
        resultado[chave] = valor
    return resultado

def ler_json(caminho):
    """Lê e valida o arquivo inteiro antes de permitir importar qualquer linha."""
    caminho = Path(caminho)
    if caminho.stat().st_size > 5 * 1024 * 1024:
        raise ValueError("JSON: limite de 5 MB para este protótipo.")
    with caminho.open("r", encoding="utf-8-sig") as arquivo:
        documento = json.load(arquivo, parse_constant=_rejeitar_constante,
                              object_pairs_hook=_sem_chaves_repetidas)
    if (not isinstance(documento, dict) or set(documento) != {"versao", "registros"}
            or type(documento["versao"]) is not int or documento["versao"] != 1):
        raise ValueError("JSON: formato esperado {versao: 1, registros: [...]}.")
    return validar_tabela(documento["registros"])

def escrever_texto(caminho, conteudo):
    """Procedimento com parâmetros; substitui o arquivo somente após escrever tudo."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n",
                                         dir=caminho.parent, delete=False) as arquivo:
            temporario = Path(arquivo.name)
            arquivo.write(conteudo)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, caminho)
    finally:
        if temporario is not None and temporario.exists():
            temporario.unlink()

def escrever_json(caminho, registros):
    """Exporta uma lista de dicionários; números são strings para preservar precisão."""
    documento = {"versao": 1, "registros": validar_tabela(registros)}
    escrever_texto(caminho, json.dumps(documento, ensure_ascii=False, indent=2,
                                      allow_nan=False) + "\n")
