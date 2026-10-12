"""Procedimentos com parâmetros para a interface de terminal."""
from decimal import Decimal
from pathlib import Path
from . import banco
from .arquivos import ler_json, escrever_json, escrever_texto
from .dominio import validar_data, validar_numero, validar_registro, validar_texto, calcular_perdas
from .relatorios import gerar_relatorio, numero_br

ROTULOS = {
    "area_ha": "Área já colhida nesta operação (ha)",
    "colhida_t": "Massa de cana efetivamente colhida nessa área (t)",
    "amostra_m2": "Soma das áreas amostradas após a colheita (m²)",
    "perda_kg": "Soma da massa de cana remanescente nessas amostras (kg)",
    "preco_t": "Preço de referência da cana (R$/t)",
}

def pedir_validado(rotulo, validador, atual=None):
    while True:
        texto = input(f"{rotulo}" + (f" [{atual}]" if atual is not None else "") + ": ")
        if not texto.strip() and atual is not None:
            return atual
        try:
            return validador(texto)
        except ValueError as erro:
            print("Entrada inválida:", erro)

def ler_formulario(atual=None):
    """Lê um dicionário; Enter conserva um campo durante a edição."""
    atual = atual or {}
    registro = {}
    registro["talhao"] = pedir_validado("Nome/código do talhão",
        lambda s: validar_texto(s, "Talhão", 60), atual.get("talhao"))
    registro["data_colheita"] = pedir_validado("Data da colheita (DD/MM/AAAA)",
        validar_data, atual.get("data_colheita"))
    for campo, rotulo in ROTULOS.items():
        registro[campo] = str(pedir_validado(rotulo,
            lambda s, c=campo: validar_numero(s, c), atual.get(campo)))
    registro["origem"] = pedir_validado("Origem (observado ou sintetico)",
        _validar_origem, atual.get("origem"))
    registro["observacao"] = pedir_validado("Observação opcional (digite - para limpar)",
        lambda s: validar_texto("" if s == "-" else s, "Observação", 240, False),
        atual.get("observacao"))
    if atual:
        registro["id"] = atual["id"]
    return validar_registro(registro, criar_id=not bool(atual))

def _validar_origem(texto):
    texto = texto.strip().lower()
    if texto not in ("observado", "sintetico"):
        raise ValueError("Digite observado para dados informados de campo ou sintetico para exemplo.")
    return texto

def confirmar(mensagem):
    return input(mensagem + " Digite SIM para confirmar: ").strip().upper() == "SIM"

def mostrar_lista(registros):
    """Procedimento que recebe a tabela de memória e mostra índices de seleção."""
    if not registros:
        print("Nenhuma colheita cadastrada.")
        return
    for indice, registro in enumerate(registros, start=1):
        print(f"{indice:>3}. {registro['talhao']} | {registro['data_colheita']} | "
              f"{registro['origem']} | {numero_br(Decimal(registro['colhida_t']))} t colhidas")

def escolher_registro(base):
    tabela = banco.listar(base)
    mostrar_lista(tabela)
    if not tabela:
        return None
    while True:
        escolha = input("Número da colheita (0 cancela): ").strip()
        if escolha == "0":
            return None
        if escolha.isascii() and escolha.isdigit() and 1 <= int(escolha) <= len(tabela):
            return tabela[int(escolha) - 1]
        print("Escolha um número exibido na lista.")

def cadastrar(base):
    registro = ler_formulario()
    calculo = calcular_perdas(registro)
    print(f"Estimativa: {numero_br(calculo['perda_t_ha'])} t/ha; "
          f"{numero_br(calculo['perda_pct'])}% de perda visível.")
    if confirmar("Gravar esta colheita?"):
        banco.inserir_lote(base, [registro])
        print("Colheita gravada.")
    else:
        print("Cadastro cancelado.")

def editar_colheita(base):
    registro = escolher_registro(base)
    if registro is None:
        return
    print("Enter mantém o valor atual. Para limpar a observação, digite -.")
    novo = ler_formulario(registro)
    if confirmar("Salvar as alterações?"):
        banco.editar(base, novo)
        print("Colheita atualizada.")
    else:
        print("Edição cancelada.")

def excluir_colheita(base):
    registro = escolher_registro(base)
    if registro and confirmar(f"Excluir {registro['talhao']} de {registro['data_colheita']}?"):
        banco.excluir(base, registro["id"])
        print("Colheita excluída.")
    else:
        print("Exclusão cancelada.")

def importar(base):
    texto = input("Caminho do JSON (Enter usa dados/exemplo_sintetico.json): ").strip().strip('"')
    caminho = Path(texto) if texto else banco.RAIZ / "dados/exemplo_sintetico.json"
    if not caminho.is_absolute():
        caminho = banco.RAIZ / caminho
    novos = ler_json(caminho)
    mostrar_lista(novos)
    print("A importação adiciona colheitas. IDs ou talhão/data repetidos cancelam TODO o lote.")
    if confirmar(f"Importar {len(novos)} colheita(s) para o modo {base['modo']}?"):
        quantidade = banco.inserir_lote(base, novos)
        print(f"{quantidade} colheita(s) importada(s).")
    else:
        print("Importação cancelada.")

def executar_menu(base, limite):
    """Loop principal; erros de uma operação não encerram o programa."""
    print("\nCANACONTROLE — controle de perdas visíveis na colheita de cana")
    print("MODO:", "DEMONSTRAÇÃO JSON — não comprova integração Oracle" if base["modo"] == "demo"
          else "ORACLE — conexão real; use opção 9 se ainda não criou a tabela")
    print("Números: vírgula OU ponto decimal; sem separador de milhar. Ctrl+C encerra.")
    while True:
        print("\n1 Cadastrar | 2 Listar | 3 Editar | 4 Excluir | 5 Relatório")
        print("6 Exportar TXT | 7 Exportar JSON | 8 Importar JSON | 9 Criar tabela Oracle | 0 Sair")
        opcao = input("Escolha: ").strip()
        if opcao == "0":
            print("Programa encerrado.")
            return
        try:
            if opcao == "1":
                cadastrar(base)
            elif opcao == "2":
                mostrar_lista(banco.listar(base))
            elif opcao == "3":
                editar_colheita(base)
            elif opcao == "4":
                excluir_colheita(base)
            elif opcao == "5":
                print(gerar_relatorio(banco.listar(base), limite))
            elif opcao == "6":
                caminho = banco.RAIZ / "resultados/relatorio_perdas.txt"
                if not caminho.exists() or confirmar("Substituir o relatório TXT existente?"):
                    escrever_texto(caminho, gerar_relatorio(banco.listar(base), limite))
                    print("TXT exportado:", caminho)
            elif opcao == "7":
                caminho = banco.RAIZ / "resultados/colheitas.json"
                if not caminho.exists() or confirmar("Substituir a exportação JSON existente?"):
                    escrever_json(caminho, banco.listar(base))
                    print("JSON exportado:", caminho)
            elif opcao == "8":
                importar(base)
            elif opcao == "9":
                if base["modo"] == "demo":
                    print("Esta opção exige o modo Oracle. Saia e execute python main.py.")
                elif confirmar("Criar a tabela ftc_colheitas no seu usuário Oracle?"):
                    banco.criar_tabelas(base)
                    print("Tabela Oracle criada. Agora cadastre ou importe colheitas.")
            else:
                print("Opção inválida. Digite um número de 0 a 9.")
        except (ValueError, OSError) as erro:
            print("Operação cancelada:", erro)
        except Exception as erro:
            # O driver Oracle só é importado no modo Oracle; nenhum fallback silencioso.
            if base["modo"] == "oracle":
                import oracledb
                if isinstance(erro, oracledb.Error):
                    codigo = getattr(erro.args[0], "full_code", "erro Oracle")
                    if codigo == "ORA-00942":
                        print("Tabela ausente ou sem permissão. Use opção 9 ou consulte o acesso Oracle.")
                    elif codigo == "ORA-00955":
                        print("Já existe um objeto com esse nome. Confira a tabela; nenhum dado foi apagado.")
                    elif codigo == "ORA-00001":
                        print("Colheita duplicada. Nenhuma alteração do lote foi confirmada.")
                    else:
                        print(f"Operação Oracle falhou ({codigo}); confira a conexão e a tabela.")
                    continue
            raise
