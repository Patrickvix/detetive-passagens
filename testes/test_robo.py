"""Testes rápidos: python -m pytest testes (ou python testes/test_robo.py)."""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from robo import promos, voos, telegram_bot, base_dados as bd
from robo.util import categorias_do_periodo


def test_categorias():
    ref = date(2026, 11, 27)
    assert categorias_do_periodo(date(2026, 12, 10), date(2026, 12, 20), ref) == ["relampago"]
    assert categorias_do_periodo(date(2027, 2, 1), date(2027, 2, 1), ref) == ["proximos"]
    assert categorias_do_periodo(date(2027, 1, 10), date(2027, 11, 30), ref) == ["proximos", "medio", "longo"]


def test_datas_ignoram_publicacao_e_prazo_de_compra():
    texto = ("Publicado em 22/11/2026 às 10:00. Compras até 30/11/2026. "
             "Viagens de março a junho de 2027 e também em 10/09/2027.")
    d = promos.datas_de_viagem(texto, date(2026, 11, 22))
    assert date(2026, 11, 30) not in d and date(2026, 11, 22) not in d
    assert d[0] == date(2027, 3, 15) and d[-1] == date(2027, 9, 10)


def test_destinos_e_ambiguos():
    assert "NAT" not in promos.destinos_citados("Ofertas de Natal para curtir o Natal Luz em Gramado")
    assert "CXJ" in promos.destinos_citados("Ofertas de Natal para curtir o Natal Luz em Gramado")
    assert set(promos.destinos_citados("Passagens para São Luís, Jeri e Beto Carrero")) == {"SLZ", "JJD", "NVT"}
    assert "LIM" not in promos.destinos_citados("Caipirinha de lima com limão")
    assert "BYO" not in promos.destinos_citados("Um voo bonito sobre o mar")


def test_classificar_promo():
    item = dict(titulo="Voos de Vitória para Santiago a partir de R$ 1.200 ida e volta",
                link="x", resumo="", publicado="2026-11-27T10:00:00-03:00", fonte="Teste")
    p = promos.classificar(item, "Datas: de julho a agosto de 2027. Saindo de Vitória.")
    assert p["origem"] == "Sai de Vitória"
    assert p["destinos"] == ["SCL"] and p["grupos"] == ["América do Sul"]
    assert p["categorias"] == ["longo"] and not p["exige_visto"]
    assert promos.classificar(dict(titulo="Cupom de 10% no aluguel de carro", link="y", resumo="", publicado=None), "") is None


def test_visto_escondido():
    item = dict(titulo="Voe para Nova York a partir de 66 mil milhas Smiles", link="z", resumo="", publicado=None)
    # Nova York não está na tabela de destinos: sem destino identificado, não esconde
    assert promos.classificar(item, "")["tipo"] == "milhas"


def test_alerta_de_queda():
    precos = {}
    for i, valor in enumerate([1000, 980, 1010, 990]):
        novos = {"SSA": dict(janela=30, calendario=[["2027-01-01", valor]], menor=valor, ida="2027-01-01",
                             volta="2027-01-08", cia="Gol", paradas=0)}
        assert voos.registrar_e_avaliar(precos, novos, {"SSA"}, date(2026, 12, 1 + i * 4)) == []
    novos = {"SSA": dict(janela=30, calendario=[["2027-01-05", 790]], menor=790, ida="2027-01-05",
                         volta="2027-01-12", cia="Gol", paradas=0)}
    al = voos.registrar_e_avaliar(precos, novos, {"SSA"}, date(2026, 12, 20))
    assert len(al) == 1 and "abaixo do normal" in al[0]["motivo"]
    # mesmo preço no dia seguinte não repete o aviso
    assert voos.registrar_e_avaliar(precos, novos, {"SSA"}, date(2026, 12, 21)) == []


def test_rodizio_cobre_todos_os_destinos_na_semana():
    favs = [dict(iata=i) for i in bd.FAVORITOS_INICIAIS]
    vistos = set()
    for dia in range(7):
        vistos |= set(voos.rotas_do_dia(favs, date(2026, 12, 1 + dia)))
    assert vistos == {d["iata"] for d in bd.DESTINOS}
    assert max(len(voos.rotas_do_dia(favs, date(2026, 12, d))) for d in range(1, 8)) <= 40


def test_comandos_telegram():
    t = telegram_bot._interpretar
    assert t("fav:SSA") == ("favoritar", "SSA")
    assert t("/start fav_jjd") == ("favoritar", "JJD")
    assert t("/start") == ("inicio", None)
    assert t("/remover Salvador") == ("remover", "Salvador")
    assert telegram_bot.achar_iata("Salvador") == "SSA"
    assert telegram_bot.achar_iata("beto carrero") == "NVT"
    assert telegram_bot.achar_iata("Jericoacoara") == "JJD"


if __name__ == "__main__":
    for nome, f in list(globals().items()):
        if nome.startswith("test_"):
            f()
            print("ok", nome)
