"""Ponto de entrada. Oracle é o modo padrão; --demo deve ser solicitado."""
import argparse
from decimal import Decimal, InvalidOperation
import sys
from cana.banco import abrir_demo, abrir_oracle, fechar
from cana.interface import executar_menu

def percentual(texto):
    try:
        valor = Decimal(texto.replace(",", "."))
    except InvalidOperation as erro:
        raise argparse.ArgumentTypeError("Informe um percentual numérico.") from erro
    if not valor.is_finite() or not 0 < valor <= 100:
        raise argparse.ArgumentTypeError("O limite deve ser maior que 0 e até 100%.")
    return valor

def main():
    parser = argparse.ArgumentParser(description="CanaControle: perdas visíveis de cana por amostragem.")
    parser.add_argument("--demo", action="store_true", help="Demonstração JSON, sem Oracle.")
    parser.add_argument("--limite-perda", type=percentual, default=Decimal("5"),
                        help="Percentual de alerta didático (padrão: 5).")
    args = parser.parse_args()
    base = None
    try:
        base = abrir_demo() if args.demo else abrir_oracle()
        executar_menu(base, args.limite_perda)
        return 0
    except (KeyboardInterrupt, EOFError):
        print("\nEntrada interrompida. Operações já confirmadas foram preservadas.")
        return 0
    except (ValueError, RuntimeError, OSError) as erro:
        print("Não foi possível iniciar:", erro, file=sys.stderr)
        return 1
    finally:
        if base is not None:
            fechar(base)

if __name__ == "__main__":
    sys.exit(main())
