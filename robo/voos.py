"""Preço de rotas saindo de Vitória, via coletor do Google Flights no Apify (kaix/google-flights-scraper)."""
import statistics
import time
from datetime import timedelta

import requests

from . import base_dados as bd
from .util import hoje, iso, para_data

ATOR = "kaix~google-flights-scraper"           # exploração (destinos mais baratos)
ATOR_PRECOS = "lergassy~google-flights-scraper"  # preço por rota (mais confiável; US$ 0,001 por rota)
TETO_PRECOS_USD = 0.10
API = "https://api.apify.com/v2"
ORIGEM = "VIX"
TETO_POR_EXECUCAO_USD = 0.03     # trava por execução do coletor
JANELAS = [30, 120, 210, 300]    # início da janela de 90 dias (dias a partir de hoje)
NOITES = 7                       # duração da viagem usada na pesquisa (ida e volta)
QUEDA_FAVORITO = 0.15            # avisa favorito 15% abaixo do normal
QUEDA_OUTROS = 0.25              # avisa demais destinos 25% abaixo do normal
MESES_EN = ["january", "february", "march", "april", "may", "june", "july", "august", "september",
            "october", "november", "december"]


class Apify:
    def __init__(self, token, status, limite_mensal_usd, log=print):
        self.token = token
        self.status = status
        self.limite = limite_mensal_usd
        self.log = log

    def gasto_mes(self):
        mes = hoje().strftime("%Y-%m")
        return self.status.setdefault("apify_gasto", {}).get(mes, 0.0)

    def _somar(self, valor):
        mes = hoje().strftime("%Y-%m")
        g = self.status.setdefault("apify_gasto", {})
        g[mes] = round(g.get(mes, 0.0) + (valor or 0.0), 5)

    def rodar(self, entrada, ator=ATOR, teto=TETO_POR_EXECUCAO_USD):
        if self.gasto_mes() + teto > self.limite:
            self.log(f"Apify: limite mensal de US$ {self.limite} atingido, pulando.")
            return None
        h = {"Authorization": f"Bearer {self.token}"}
        r = requests.post(f"{API}/acts/{ator}/runs", headers=h, json=entrada, timeout=60,
                          params={"maxTotalChargeUsd": teto, "waitForFinish": 240})
        r.raise_for_status()
        run = r.json()["data"]
        for _ in range(48):
            if run["status"] in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
                break
            time.sleep(15)
            run = requests.get(f"{API}/actor-runs/{run['id']}", headers=h, timeout=30).json()["data"]
        custo = run.get("usageTotalUsd") or teto
        self._somar(custo)
        self.log(f"Apify: execução {run['status']}, custo US$ {custo:.4f}, mês US$ {self.gasto_mes():.3f}")
        if run["status"] != "SUCCEEDED":
            return None
        itens = requests.get(f"{API}/datasets/{run['defaultDatasetId']}/items", headers=h, timeout=60,
                             params={"clean": "true", "omit": "googleResponses,legs,bookingDetails"})
        itens.raise_for_status()
        return itens.json()


def _codigo_busca(iata):
    return bd.AEROPORTOS_DA_CIDADE.get(iata, iata)


def rotas_do_dia(favoritos, referencia=None):
    """Favoritos todo dia + 1/7 dos demais destinos (rodízio semanal)."""
    ref = referencia or hoje()
    fav = [f["iata"] for f in favoritos]
    outros = [d["iata"] for d in bd.DESTINOS if d["iata"] not in fav]
    rodizio = [iata for i, iata in enumerate(outros) if i % 7 == ref.weekday()]
    return fav + rodizio


def janela_do_dia(referencia=None):
    ref = referencia or hoje()
    return JANELAS[ref.toordinal() % len(JANELAS)]


LOTE = 40            # rotas por execução do Apify
TENTATIVAS = 2       # o ator às vezes falha em algumas buscas: repete só as que faltaram


def buscar_precos(apify, iatas, referencia=None, favoritos=()):
    """Preço ida e volta (7 noites) de cada rota na janela do dia (favoritos: 2 datas; demais: 1).
    Usa a busca simples do Google Flights, porque o modo calendário do ator está instável."""
    ref = referencia or hoje()
    jan = janela_do_dia(ref)
    ida = ref + timedelta(days=jan)
    pendentes = []
    for x in iatas:
        pendentes.append((x, ida))
        if x in favoritos:
            pendentes.append((x, min(ida + timedelta(days=30), ref + timedelta(days=320))))
    coletado = {}
    for _ in range(TENTATIVAS):
        if not pendentes:
            break
        faltam = list(pendentes)
        for i in range(0, len(pendentes), LOTE):
            lote = pendentes[i:i + LOTE]
            mapa = {}
            for x, _d in lote:
                mapa[x] = x
                for cod in _codigo_busca(x).split(","):
                    mapa[cod] = x
            entrada = {
                "routes": [{"origin": ORIGEM, "destination": _codigo_busca(x).split(",")[0], "departureDate": iso(d),
                            "returnDate": iso(d + timedelta(days=NOITES))} for x, d in lote],
                "currency": "BRL", "market": "BR", "language": "pt-BR", "maxResults": 1, "sortBy": "price",
                "includePriceInsights": False, "kayakWhenGoogleEmpty": False, "includeRunSummary": False,
            }
            itens = apify.rodar(entrada, ator=ATOR_PRECOS, teto=TETO_PRECOS_USD) or []
            for it in itens:
                if it.get("type", "flight") != "flight":
                    continue
                dest = (it.get("destination") or "").split(",")[0]
                iata = mapa.get(dest)
                data, preco = it.get("departureDate"), it.get("price")
                if not iata or not data or not preco:
                    continue
                if data in coletado.get(iata, {}) and coletado[iata][data]["preco"] <= preco:
                    continue
                cia = it.get("airline") or ", ".join(it.get("airlines") or [])
                coletado.setdefault(iata, {})[data] = dict(preco=preco, cia=cia,
                                                           paradas=it.get("stops"))
                faltam = [(x, d) for x, d in faltam if not (x == iata and iso(d) == data)]
        pendentes = faltam
    resultados = {}
    for iata, por_data in coletado.items():
        cal = sorted((d, v["preco"]) for d, v in por_data.items())
        melhor = min(cal, key=lambda c: c[1])
        v = por_data[melhor[0]]
        resultados[iata] = dict(janela=jan, calendario=cal, menor=melhor[1], ida=melhor[0],
                                volta=iso(para_data(melhor[0]) + timedelta(days=NOITES)),
                                cia=v["cia"], paradas=v["paradas"])
    if pendentes:
        apify.log(f"::warning title=Preços::{len(pendentes)} consulta(s) sem resposta do Google Flights (tento de novo amanhã)")
    return resultados


def registrar_e_avaliar(precos, novos, favoritos_iatas, referencia=None):
    """Guarda o histórico e devolve a lista de quedas de preço que merecem aviso."""
    ref = iso(referencia or hoje())
    alertas = []
    for iata, r in novos.items():
        rota = precos.setdefault(iata, {"hist": [], "calendarios": {}, "recorde": None})
        anteriores = [h for h in rota["hist"] if h["janela"] == r["janela"]]
        todos = [h["min"] for h in rota["hist"]]
        rota["hist"].append(dict(d=ref, janela=r["janela"], min=r["menor"], ida=r["ida"], volta=r["volta"], cia=r["cia"]))
        rota["hist"] = rota["hist"][-400:]
        rota["calendarios"][str(r["janela"])] = dict(d=ref, pontos=r["calendario"])
        if rota["recorde"] is None or r["menor"] < rota["recorde"]["min"]:
            rota["recorde"] = dict(min=r["menor"], ida=r["ida"], volta=r["volta"], d=ref)

        limite = QUEDA_FAVORITO if iata in favoritos_iatas else QUEDA_OUTROS
        motivo = None
        if len(anteriores) >= 3:
            normal = statistics.median(h["min"] for h in anteriores[-12:])
            if r["menor"] <= normal * (1 - limite):
                motivo = f"{round((1 - r['menor'] / normal) * 100)}% abaixo do normal ({normal:,.0f})".replace(",", ".")
        if motivo is None and len(todos) >= 6 and r["menor"] < min(todos) * 0.97:
            motivo = "menor preço já visto"
        if motivo:
            ultimo = rota.get("ultimo_alerta")
            if ultimo and ultimo["min"] <= r["menor"] * 1.03 and (para_data(ref) - para_data(ultimo["d"])).days < 7:
                continue
            rota["ultimo_alerta"] = dict(d=ref, min=r["menor"])
            alertas.append(dict(iata=iata, motivo=motivo, **r))
    return alertas


def explorar(apify, referencia=None):
    """Destinos mais baratos saindo de Vitória: próximos 6 meses + 2 meses mais distantes (rodízio)."""
    ref = referencia or hoje()
    semana = ref.isocalendar()[1]
    distantes = [7 + (semana % 3) * 2, 8 + (semana % 3) * 2]   # 7-8, 9-10 ou 11-12 meses à frente
    pedidos = ["next-6-months"] + [MESES_EN[(ref.month - 1 + m) % 12] for m in distantes]
    achados = []
    for mes in pedidos:
        entrada = {"searches": [], "exploreOrigin": ORIGEM, "tripDuration": "1-week", "exploreMonth": mes,
                   "currency": "BRL", "country": "BR", "language": "pt-BR"}
        for it in apify.rodar(entrada) or []:
            if not it.get("price") or not it.get("airport"):
                continue
            achados.append(dict(aeroporto=it["airport"], cidade=it.get("city"), pais=it.get("country"),
                                ida=it.get("departureDate"), volta=it.get("returnDate"), preco=it["price"],
                                cia=it.get("airline"), paradas=it.get("stops"), pedido=mes))
    return achados


def avaliar_descobertas(historico, achados, referencia=None):
    """Guarda o menor preço por aeroporto e devolve as descobertas bem abaixo do que já foi visto."""
    ref = iso(referencia or hoje())
    alertas = []
    for a in achados:
        h = historico.setdefault(a["aeroporto"], {"precos": [], "cidade": a["cidade"], "pais": a["pais"]})
        antes = [p["preco"] for p in h["precos"]]
        h["precos"].append(dict(d=ref, preco=a["preco"], ida=a["ida"]))
        h["precos"] = h["precos"][-60:]
        if len(antes) >= 2 and a["preco"] <= statistics.median(antes) * 0.8:
            alertas.append(a)
    return alertas
