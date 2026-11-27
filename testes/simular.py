"""Simula execuções completas do robô sem internet (respostas falsas). Uso: python testes/simular.py"""
import json
import shutil
import sys
import tempfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import robo.util as util

TMP = Path(tempfile.mkdtemp())
util.DADOS = TMP / "docs" / "dados"
util.ESTADO = TMP / "estado"
import robo.main as main  # noqa: E402
main.DADOS, main.ESTADO = util.DADOS, util.ESTADO

ENVIADAS = []
RSS = """<?xml version="1.0"?><rss version="2.0"><channel><title>x</title>
<item><title>Passagens de Vitória para Salvador e Recife a partir de R$ 499 ida e volta</title>
<link>https://blog/{n}a</link><description>Oferta</description><pubDate>Fri, 27 Nov 2026 10:00:00 +0000</pubDate></item>
<item><title>Lisboa a partir de 45 mil milhas Smiles</title>
<link>https://blog/{n}b</link><description>milhas</description><pubDate>Fri, 27 Nov 2026 09:00:00 +0000</pubDate></item>
<item><title>Cupom no aluguel de carro</title>
<link>https://blog/{n}c</link><description>carro</description><pubDate>Fri, 27 Nov 2026 08:00:00 +0000</pubDate></item>
</channel></rss>"""
RODADA = {"n": 1, "updates": []}


class R:
    def __init__(self, dados=None, texto="", conteudo=b""):
        self._d, self.text, self.content, self.status_code = dados, texto, conteudo, 200

    def json(self):
        return self._d

    def raise_for_status(self):
        pass


def falso_get(url, **kw):
    if "feed" in url:
        return R(conteudo=RSS.format(n=RODADA["n"]).encode())
    if url.startswith("https://blog/"):
        return R(texto="<article>Viagens de março a junho de 2027. Saindo de Vitória.</article>")
    if "actor-runs" in url:
        return R({"data": {"id": "r", "status": "SUCCEEDED", "usageTotalUsd": 0.002, "defaultDatasetId": "d"}})
    if "datasets" in url:
        if kw.get("params") and "exploreOrigin" in str(kw):
            pass
        return R(ITENS_APIFY["atual"])
    if "open.er-api" in url:
        return R({"rates": {"EUR": 0.17, "CLP": 170.0, "USD": 0.19, "UYU": 7.9}})
    if "awesomeapi" in url:
        import time
        base = 6.0 if "EUR" in url else 0.0055 if "CLP" in url else 5.3
        return R([{"timestamp": str(int(time.time()) - i * 86400), "bid": str(base)} for i in range(200)])
    raise AssertionError(url)


ITENS_APIFY = {"atual": []}


def falso_post(url, json=None, **kw):
    if "api.telegram.org" in url:
        metodo = url.rsplit("/", 1)[-1]
        if metodo == "getMe":
            return R({"ok": True, "result": {"username": "detetive_teste_bot"}})
        if metodo == "getUpdates":
            ups, RODADA["updates"] = RODADA["updates"], []
            return R({"ok": True, "result": ups})
        if metodo == "sendMessage":
            ENVIADAS.append(json["text"])
        return R({"ok": True})
    if "api.apify.com" in url:
        if json.get("exploreOrigin"):
            ITENS_APIFY["atual"] = [{"airport": "SCL", "city": "Santiago", "country": "Chile", "departureDate": "2027-06-10",
                                     "returnDate": "2027-06-17", "price": 1500, "airline": "LATAM", "stops": 0}]
        else:
            ITENS_APIFY["atual"] = [{"destination": s["destination"], "price": 900, "airlines": ["Gol"], "stops": 1,
                                     "departureDate": s["departureDate"],
                                     "calendarPrices": [{"date": s["departureDate"], "price": 900}]} for s in json["searches"]]
        return R({"data": {"id": "r", "status": "SUCCEEDED", "usageTotalUsd": 0.002, "defaultDatasetId": "d"}})
    raise AssertionError(url)


def rodar(desc):
    with mock.patch("requests.get", falso_get), mock.patch("requests.post", falso_post), \
            mock.patch.dict("os.environ", {"TELEGRAM_TOKEN": "t", "APIFY_TOKEN": "a"}):
        antes = len(ENVIADAS)
        main.main()
        print(f"\n=== {desc}: {len(ENVIADAS) - antes} mensagens")
        for m in ENVIADAS[antes:]:
            print("---\n" + m[:400])


msg = lambda txt, uid: {"update_id": uid, "message": {"chat": {"id": 42}, "text": txt}}
RODADA["updates"] = [msg("/start", 1)]
rodar("1ª execução (dono manda /start)")
RODADA["n"] = 2
RODADA["updates"] = [msg("/favoritar Gramado", 2), msg("/passaporte 2027-06-01", 3),
                     {"update_id": 4, "callback_query": {"id": "c", "data": "fav:LIS", "message": {"chat": {"id": 99}}}}]
main.agora = lambda: util.datetime(2026, 11, 27, 6, 0, tzinfo=util.FUSO_BR)   # antes das 7h: sem preços
rodar("2ª execução (promoções novas + comandos; callback de estranho ignorado)")
main.agora = lambda: util.datetime(2026, 11, 27, 8, 0, tzinfo=util.FUSO_BR)
rodar("3ª execução (diária: preços, câmbio, exploração)")

d = util.DADOS
favs = json.loads((d / "favoritos.json").read_text())
print("\nFavoritos:", [f["iata"] for f in favs])
assert "CXJ" in favs[-1]["iata"] and "LIS" not in [f["iata"] for f in favs]
print("Promoções guardadas:", len(json.loads((d / "promocoes.json").read_text())))
print("Rotas com preço:", len(json.loads((d / "precos.json").read_text())))
print("Real forte:", json.loads((d / "real_forte.json").read_text())["moedas"][:2])
print("Status:", json.loads((d / "status.json").read_text()))
shutil.rmtree(TMP)
