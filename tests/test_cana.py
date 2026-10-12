"""Testes de regras e transações com doubles; não substituem teste Oracle real."""
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from cana import banco
from cana.arquivos import ler_json, escrever_json
from cana.dominio import validar_registro, validar_numero, validar_tabela, calcular_perdas, resumir
from cana.relatorios import gerar_relatorio

def exemplo(**campos):
    registro = {"id": "11111111-1111-4111-8111-111111111111", "talhao": "CANA-01",
                "data_colheita": "2025-08-01", "area_ha": "10", "colhida_t": "800",
                "amostra_m2": "10", "perda_kg": "4", "preco_t": "150",
                "origem": "sintetico", "observacao": "Exemplo didático"}
    registro.update(campos)
    return registro

class Regras(unittest.TestCase):
    def test_unidades_e_valor(self):
        c = calcular_perdas(exemplo())
        self.assertEqual(c["perda_t_ha"], Decimal(4))
        self.assertEqual(c["perdida_t"], Decimal(40))
        self.assertEqual(c["potencial_t"], Decimal(840))
        self.assertEqual(c["valor_estimado"], Decimal(6000))
        self.assertAlmostEqual(float(c["perda_pct"]), 4.7619047619)

    def test_zero_perda_e_perda_total(self):
        self.assertEqual(calcular_perdas(exemplo(perda_kg="0"))["perda_pct"], 0)
        self.assertEqual(calcular_perdas(exemplo(colhida_t="0"))["perda_pct"], 100)
        with self.assertRaises(ValueError):
            validar_registro(exemplo(colhida_t="0", perda_kg="0"))

    def test_media_por_massa(self):
        a = exemplo(colhida_t="10", area_ha="1", perda_kg="1")
        b = exemplo(id="22222222-2222-4222-8222-222222222222", talhao="B",
                    colhida_t="1000", area_ha="1", perda_kg="10")
        resultado = resumir([a, b])
        self.assertAlmostEqual(float(resultado["perda_pct"]), 11 / 1021 * 100)
        media_simples = (calcular_perdas(a)["perda_pct"] + calcular_perdas(b)["perda_pct"]) / 2
        self.assertNotEqual(resultado["perda_pct"], media_simples)

    def test_entradas_numericas(self):
        self.assertEqual(validar_numero("12,3456", "area_ha"), Decimal("12.3456"))
        for invalido in (True, "nan", "inf", "1e3", "1.000,50", "0", "-1", "0.00001", {}, None):
            with self.subTest(valor=invalido), self.assertRaises(ValueError):
                validar_numero(invalido, "area_ha")
        with self.assertRaises(ValueError):
            validar_numero("1.001", "preco_t")

    def test_data_texto_origem_e_area(self):
        for campos in ({"data_colheita": "31/02/2025"}, {"data_colheita": "2999-01-01"},
                       {"talhao": ""}, {"talhao": "A\nB"}, {"talhao": "A" * 61},
                       {"origem": "inventado"}, {"observacao": 4}, {"amostra_m2": "100001"},
                       {"area_ha": "0.0001", "amostra_m2": "2"}):
            with self.subTest(campos=campos), self.assertRaises(ValueError):
                validar_registro(exemplo(**campos))

    def test_duplicata_talhao_data_normalizada(self):
        with self.assertRaises(ValueError):
            validar_tabela([exemplo(), exemplo(id="22222222-2222-4222-8222-222222222222", talhao=" cana-01 ")])

    def test_relatorio_separa_origens(self):
        texto = gerar_relatorio([exemplo(), exemplo(id="22222222-2222-4222-8222-222222222222",
                                talhao="B", origem="observado", perda_kg="8")])
        self.assertIn("SINTÉTICO", texto)
        self.assertIn("OBSERVADO", texto)
        self.assertIn("ALERTA", texto)
        self.assertIn("6.000,00", texto)
        self.assertIn("Cenário hipotético", texto)

class ArquivosEDemo(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.pasta = Path(self.temp.name)
        self.base = banco.abrir_demo(self.pasta / "base.json")

    def tearDown(self):
        self.temp.cleanup()

    def test_crud_persistencia(self):
        banco.inserir_lote(self.base, [exemplo()])
        outra = banco.abrir_demo(self.pasta / "base.json")
        self.assertEqual(banco.listar(outra)[0]["talhao"], "CANA-01")
        banco.editar(self.base, exemplo(perda_kg="3"))
        self.assertEqual(banco.listar(outra)[0]["perda_kg"], "3")
        banco.excluir(self.base, exemplo()["id"])
        self.assertEqual(banco.listar(outra), [])

    def test_lote_invalido_nao_grava_parte_valida(self):
        banco.inserir_lote(self.base, [exemplo()])
        anterior = self.base["arquivo"].read_bytes()
        with self.assertRaises(ValueError):
            banco.inserir_lote(self.base, [exemplo(id="22222222-2222-4222-8222-222222222222", talhao="B"),
                                         exemplo()])
        self.assertEqual(self.base["arquivo"].read_bytes(), anterior)

    def test_json_roundtrip(self):
        caminho = self.pasta / "export.json"
        escrever_json(caminho, [exemplo(observacao="Açúcar e colheita")])
        self.assertEqual(ler_json(caminho)[0]["observacao"], "Açúcar e colheita")

    def test_json_estrutura_constantes_e_chaves(self):
        caminho = self.pasta / "erro.json"
        invalidos = ['{"versao":1,"registros":NaN}', '{"versao":true,"registros":[]}',
                     '{"versao":1,"versao":1,"registros":[]}', '{"versao":1,"registros":{}}',
                     '{"versao":1,"registros":[],"extra":1}', '{',
                     json.dumps({"versao": 1, "registros": [exemplo(area_ha=True)]})]
        for documento in invalidos:
            caminho.write_text(documento, encoding="utf-8")
            with self.subTest(documento=documento), self.assertRaises(ValueError):
                ler_json(caminho)

    def test_corrompido_preservado(self):
        self.base["arquivo"].write_text("JSON inválido", encoding="utf-8")
        with self.assertRaises(ValueError):
            banco.abrir_demo(self.base["arquivo"])
        self.assertEqual(self.base["arquivo"].read_text(encoding="utf-8"), "JSON inválido")

class ContratoOracleComDoubles(unittest.TestCase):
    def setUp(self):
        self.conexao = MagicMock()
        self.cursor = self.conexao.cursor.return_value.__enter__.return_value
        self.base = {"modo": "oracle", "conexao": self.conexao}

    @patch("cana.banco.listar", return_value=[])
    def test_bind_decimal_e_commit(self, listar_mock):
        banco.inserir_lote(self.base, [exemplo(talhao="D'ÁGUA")])
        sql, parametros = self.cursor.executemany.call_args.args
        self.assertNotIn("D'ÁGUA", sql)
        self.assertIn(":talhao", sql)
        self.assertEqual(parametros[0]["talhao"], "D'ÁGUA")
        self.assertIsInstance(parametros[0]["area_ha"], Decimal)
        self.conexao.commit.assert_called_once()
        self.conexao.rollback.assert_not_called()

    @patch("cana.banco.listar", return_value=[])
    def test_rollback_em_erro(self, listar_mock):
        self.cursor.executemany.side_effect = RuntimeError("Falha de teste")
        with self.assertRaises(RuntimeError):
            banco.inserir_lote(self.base, [exemplo()])
        self.conexao.rollback.assert_called_once()
        self.conexao.commit.assert_not_called()

    @patch("cana.banco.listar", return_value=[exemplo()])
    def test_exclusao_exige_linha_existente(self, listar_mock):
        self.cursor.rowcount = 0
        with self.assertRaises(ValueError):
            banco.excluir(self.base, exemplo()["id"])
        self.conexao.rollback.assert_called_once()
        self.conexao.commit.assert_not_called()

if __name__ == "__main__":
    unittest.main()
