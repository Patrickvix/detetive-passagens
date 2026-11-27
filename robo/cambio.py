"""Real forte: compara quanto 1 real compra hoje de cada moeda com a média dos últimos 12 meses."""
import statistics

import requests

from . import base_dados as bd
from .util import hoje, iso, para_data

URL_HOJE = "https://open.er-api.com/v6/latest/BRL"          # grátis, sem chave, todas as moedas
URL_HIST = "https://economia.awesomeapi.com.br/json/daily/{m}-BRL/365"  # histórico para começar
FORA = {"ARS", "VES", "TRY", "BRL"}   # inflação alta (comparação engana) ou a própria moeda


def moedas_monitoradas():
    return sorted({p["moeda"] for p in bd.PAISES.values() if p.get("moeda")} - FORA)


def semear_historico(cambio, log=print):
    """Na primeira vez, busca 1 ano de histórico (quando a fonte tem a moeda)."""
    for m in moedas_monitoradas():
        h = cambio.setdefault(m, {})
        if len(h) >= 30:
            continue
        try:
            dados = requests.get(URL_HIST.format(m=m), timeout=30).json()
            for linha in dados if isinstance(dados, list) else []:
                from datetime import datetime
                dia = datetime.fromtimestamp(int(linha["timestamp"])).date().isoformat()
                bid = float(linha["bid"])          # reais por 1 unidade da moeda
                if bid > 0:
                    h.setdefault(dia, round(1 / bid, 6))
        except Exception as e:
            log(f"Histórico de {m} indisponível: {e}")


def atualizar(cambio, log=print):
    r = requests.get(URL_HOJE, timeout=30)
    r.raise_for_status()
    taxas = r.json().get("rates", {})
    dia = iso(hoje())
    for m in moedas_monitoradas():
        if m in taxas:
            cambio.setdefault(m, {})[dia] = round(float(taxas[m]), 6)
    # guarda só 400 dias
    for m, h in cambio.items():
        for d in sorted(h)[:-400]:
            del h[d]


def ranking(cambio):
    """Lista de moedas com quanto o real está mais forte (+) ou mais fraco (−) que a média do ano."""
    lista = []
    ref = hoje()
    for m in moedas_monitoradas():
        h = cambio.get(m) or {}
        if not h:
            continue
        ultimo = max(h)
        ano = [v for d, v in h.items() if (ref - para_data(d)).days <= 365]
        if len(ano) < 20:
            continue
        media = statistics.mean(ano)
        atual = h[ultimo]
        variacao = (atual / media - 1) * 100
        if abs(variacao) > 60:      # fontes com unidades diferentes ou dado quebrado: melhor não mostrar
            continue
        paises = sorted(n for n, p in bd.PAISES.items() if p.get("moeda") == m)
        lista.append(dict(moeda=m, por_real=atual, media_ano=round(media, 6), variacao=round(variacao, 1),
                          data=ultimo, paises=paises))
    lista.sort(key=lambda x: -x["variacao"])
    return lista
