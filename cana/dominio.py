"""Funções de validação e cálculo independentes de banco e interface."""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re
from uuid import UUID, uuid4

# Tupla: nomes e ordem dos campos são fixos. Lista de dicionários: tabela em memória.
CAMPOS = ("id", "talhao", "data_colheita", "area_ha", "colhida_t",
          "amostra_m2", "perda_kg", "preco_t", "origem", "observacao")
LIMITES = {
    "area_ha": (Decimal("0"), Decimal("100000"), 4, False),
    "colhida_t": (Decimal("0"), Decimal("100000000"), 4, True),
    "amostra_m2": (Decimal("0"), Decimal("100000"), 4, False),
    "perda_kg": (Decimal("0"), Decimal("1000000"), 4, True),
    "preco_t": (Decimal("0"), Decimal("1000000"), 2, True),
}

def validar_texto(valor, nome, tamanho, obrigatorio=True):
    """Valida texto e devolve seu conteúdo sem espaços nas extremidades."""
    if not isinstance(valor, str):
        raise ValueError(f"{nome}: informe um texto.")
    valor = valor.strip()
    if obrigatorio and not valor:
        raise ValueError(f"{nome}: não pode ficar vazio.")
    if len(valor) > tamanho or any(ord(c) < 32 or ord(c) == 127 for c in valor):
        raise ValueError(f"{nome}: máximo de {tamanho} caracteres, sem quebras de linha.")
    return valor

def validar_numero(valor, campo):
    """Aceita vírgula OU ponto decimal; rejeita booleanos, NaN e infinito."""
    minimo, maximo, casas, permite_zero = LIMITES[campo]
    if isinstance(valor, bool) or not isinstance(valor, (str, int, float, Decimal)):
        raise ValueError(f"{campo}: informe um número.")
    texto = str(valor).strip()
    if not re.fullmatch(r"[+\-]?\d+(?:[.,]\d+)?", texto):
        raise ValueError(f"{campo}: use número sem separador de milhar (ex.: 12,5).")
    try:
        numero = Decimal(texto.replace(",", "."))
    except InvalidOperation as erro:
        raise ValueError(f"{campo}: número inválido.") from erro
    if not numero.is_finite() or numero < minimo or numero > maximo:
        raise ValueError(f"{campo}: valor fora do intervalo permitido (até {maximo}).")
    if not permite_zero and numero == 0:
        raise ValueError(f"{campo}: deve ser maior que zero.")
    passo = Decimal(1).scaleb(-casas)
    if numero != numero.quantize(passo):
        raise ValueError(f"{campo}: use no máximo {casas} casas decimais.")
    return numero

def validar_data(valor):
    """Aceita DD/MM/AAAA ou AAAA-MM-DD; uma colheita registrada já deve ter ocorrido."""
    if not isinstance(valor, str):
        raise ValueError("Data: informe DD/MM/AAAA ou AAAA-MM-DD.")
    for formato in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            resultado = datetime.strptime(valor.strip(), formato).date()
            if resultado > date.today():
                raise ValueError("Data: a colheita não pode estar no futuro.")
            return resultado.isoformat()
        except ValueError:
            pass
    raise ValueError("Data: informe uma data válida, que não esteja no futuro.")

def validar_registro(dados, criar_id=False):
    """Normaliza um dicionário completo antes de qualquer gravação."""
    if not isinstance(dados, dict):
        raise ValueError("Cada registro deve ser um objeto JSON/dicionário.")
    dados = dados.copy()
    if criar_id:
        dados["id"] = str(uuid4())
    if set(dados) != set(CAMPOS):
        raise ValueError("Campos obrigatórios ausentes ou campos desconhecidos no registro.")
    try:
        identificador = str(UUID(dados["id"]))
    except (ValueError, TypeError, AttributeError) as erro:
        raise ValueError("ID: UUID inválido.") from erro
    talhao = validar_texto(dados["talhao"], "Talhão", 60).upper()
    # Alguns caracteres podem aumentar de comprimento ao converter para maiúsculas.
    talhao = validar_texto(talhao, "Talhão", 60)
    registro = {"id": identificador, "talhao": talhao,
                "data_colheita": validar_data(dados["data_colheita"])}
    for campo in LIMITES:
        registro[campo] = str(validar_numero(dados[campo], campo))
    if Decimal(registro["amostra_m2"]) > Decimal(registro["area_ha"]) * 10000:
        raise ValueError("A área amostrada não pode superar a área colhida do talhão.")
    if Decimal(registro["colhida_t"]) == 0 and Decimal(registro["perda_kg"]) == 0:
        raise ValueError("Informe massa colhida ou perda positiva para calcular o percentual.")
    if dados["origem"] not in ("observado", "sintetico"):
        raise ValueError("Origem: use observado ou sintetico.")
    registro["origem"] = dados["origem"]
    registro["observacao"] = validar_texto(dados["observacao"], "Observação", 240, False)
    return registro

def validar_tabela(registros):
    """Devolve a tabela normalizada e rejeita colheitas duplicadas."""
    if not isinstance(registros, list) or len(registros) > 1000:
        raise ValueError("A tabela deve ser uma lista com até 1000 registros.")
    tabela, ids, chaves = [], set(), set()
    for linha, registro in enumerate(registros, start=1):
        try:
            registro = validar_registro(registro)
            chave = (registro["talhao"], registro["data_colheita"])
            if registro["id"] in ids or chave in chaves:
                raise ValueError("ID ou combinação talhão/data duplicada.")
            ids.add(registro["id"])
            chaves.add(chave)
            tabela.append(registro)
        except ValueError as erro:
            raise ValueError(f"Registro {linha}: {erro}") from erro
    return tabela

def calcular_perdas(registro):
    """Estimativa didática: amostra representativa agregada da área já colhida."""
    registro = validar_registro(registro)
    area = Decimal(registro["area_ha"])
    colhida = Decimal(registro["colhida_t"])
    # (kg/m²) * (10000 m²/ha) / (1000 kg/t) = t/ha.
    perda_t_ha = Decimal(registro["perda_kg"]) / Decimal(registro["amostra_m2"]) * 10
    perdida = perda_t_ha * area
    potencial = colhida + perdida
    return {"perda_t_ha": perda_t_ha, "perdida_t": perdida,
            "potencial_t": potencial, "perda_pct": perdida / potencial * 100,
            "valor_estimado": perdida * Decimal(registro["preco_t"])}

def resumir(registros):
    """Agrega por massa; não usa média simples dos percentuais dos talhões."""
    tabela = validar_tabela(registros)
    perdida = potencial = valor = area = Decimal(0)
    for registro in tabela:
        calculo = calcular_perdas(registro)
        perdida += calculo["perdida_t"]
        potencial += calculo["potencial_t"]
        valor += calculo["valor_estimado"]
        area += Decimal(registro["area_ha"])
    return {"quantidade": len(tabela), "area_ha": area, "perdida_t": perdida,
            "potencial_t": potencial, "valor_estimado": valor,
            "perda_pct": perdida / potencial * 100 if potencial else Decimal(0)}
