"""Apresentação legível em texto, com origem e unidades explícitas."""
from decimal import Decimal
from .dominio import calcular_perdas, resumir, validar_tabela

COLUNAS = ("Talhão", "Data", "Perda t/ha", "Perda %", "Valor estimado R$")

def numero_br(valor, casas=2):
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def gerar_relatorio(registros, limite=Decimal("5")):
    """Função com retorno; prioriza inspeção pelo valor estimado, sem inferir causas."""
    tabela = validar_tabela(registros)
    linhas = ["CANACONTROLE — PERDAS VISÍVEIS NA COLHEITA DE CANA",
              "Estimativas por amostragem; não representam prejuízo líquido comprovado.",
              f"Alerta didático configurado: perda >= {numero_br(limite)}%.",
              "Critério operacional escolhido para o projeto; não é limite agronômico universal."]
    if not tabela:
        return "\n".join(linhas + ["Nenhuma colheita cadastrada."]) + "\n"
    for origem in ("observado", "sintetico"):
        grupo = [r for r in tabela if r["origem"] == origem]
        if not grupo:
            continue
        linhas += ["", "ORIGEM: " + ("OBSERVADO — informado pelo usuário" if origem == "observado"
                                      else "SINTÉTICO — demonstração, sem medição de fazenda"),
                   "Ordem de inspeção: maior valor estimado de cana perdida primeiro.",
                   f"{COLUNAS[0]:<20} {COLUNAS[1]:<10} {COLUNAS[2]:>12} {COLUNAS[3]:>10} {COLUNAS[4]:>20}"]
        for registro in sorted(grupo, key=lambda r: calcular_perdas(r)["valor_estimado"], reverse=True):
            c = calcular_perdas(registro)
            linhas.append(f"{registro['talhao'][:20]:<20} {registro['data_colheita']:<10} "
                          f"{numero_br(c['perda_t_ha']):>12} {numero_br(c['perda_pct']):>10} "
                          f"{numero_br(c['valor_estimado']):>20}")
            if len(registro["talhao"]) > 20:
                linhas.append("  Talhão completo: " + registro["talhao"])
            if c["perda_pct"] >= limite:
                linhas.append("  ALERTA: conferir amostragem e inspecionar a operação com o responsável técnico.")
        resumo = resumir(grupo)
        linhas += [f"Colheitas: {resumo['quantidade']} | Área somada: {numero_br(resumo['area_ha'])} ha",
                   f"Perda estimada: {numero_br(resumo['perdida_t'])} t | "
                   f"Percentual agregado por massa: {numero_br(resumo['perda_pct'])}%",
                   f"Valor de cana perdida estimado: R$ {numero_br(resumo['valor_estimado'])}",
                   f"Cenário hipotético: reduzir pela metade a massa perdida corresponderia a "
                   f"R$ {numero_br(resumo['valor_estimado'] / 2)} em cana, antes dos custos."]
    linhas += ["", "LIMITAÇÕES: a extrapolação depende de amostras representativas; "
               "não mede perdas invisíveis, qualidade/ATR nem perdas de transporte.",
               "A área somada é de operações cadastradas e pode incluir o mesmo talhão em datas distintas."]
    return "\n".join(linhas) + "\n"
