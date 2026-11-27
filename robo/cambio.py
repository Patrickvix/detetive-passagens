"""Real forte: compara quanto 1 real compra hoje de cada moeda com a média dos últimos 12 meses."""
import statistics

import requests

from . import base_dados as bd
from .util import hoje, iso, para_data

URL_HOJE = "https://open.er-api.com/v6/latest/BRL"          # grátis, sem chave, todas as moedas
URL_HIST = "https://economia.awesomeapi.com.br/json/daily/{m}-BRL/365"  # histórico para começar
INFLACAO = {"ARS", "VES", "TRY", "CUP"}   # inflação alta / câmbio oficial irreal: a comparação com o ano engana
URL_DIA = ["https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{d}/v1/currencies/brl.json",
           "https://{d}.currency-api.pages.dev/v1/currencies/brl.json"]   # grátis, todas as moedas, por data


def moedas_monitoradas():
    return sorted({p["moeda"] for p in bd.PAISES.values() if p.get("moeda")} - {"BRL"})


def _cotacoes_do_dia(d):
    for url in URL_DIA:
        try:
            r = requests.get(url.format(d=d), timeout=30)
            if r.ok:
                return {k.upper(): v for k, v in (r.json().get("brl") or {}).items()}
        except Exception:
            pass
    return {}


def _semear_mensal(cambio, log):
    """1 cotação por mês nos últimos 12 meses, para todas as moedas (fonte com histórico por data)."""
    from datetime import timedelta
    ref = hoje()
    ok = 0
    for meses in range(1, 13):
        d = iso(ref - timedelta(days=30 * meses))
        taxas = _cotacoes_do_dia(d)
        if taxas:
            ok += 1
        for m in moedas_monitoradas():
            if taxas.get(m):
                cambio.setdefault(m, {}).setdefault(d, round(float(taxas[m]), 6))
    if not ok:
        log("Histórico mensal de câmbio indisponível")


URL_HIST2 = "https://api.frankfurter.dev/v1/{ini}..{fim}"     # BCE: ~30 moedas principais, grátis


def _semear_frankfurter(cambio, faltando, log):
    """2ª fonte do histórico (moedas do BCE: EUR, USD, GBP, CAD, AUD, MXN, etc.)."""
    from datetime import timedelta
    fim = hoje()
    try:
        r = requests.get(URL_HIST2.format(ini=iso(fim - timedelta(days=365)), fim=iso(fim)),
                         params={"base": "BRL", "symbols": ",".join(sorted(faltando))}, timeout=60)
        r.raise_for_status()
        for dia, taxas in (r.json().get("rates") or {}).items():
            for m, v in taxas.items():
                if v and m in faltando:
                    cambio.setdefault(m, {}).setdefault(dia, round(float(v), 6))
    except Exception as e:
        log(f"Histórico (Frankfurter) indisponível: {e}")


def semear_historico(cambio, log=print):
    """Na primeira vez, busca 1 ano de histórico (quando a fonte tem a moeda)."""
    falhas = 0
    for m in moedas_monitoradas():
        h = cambio.setdefault(m, {})
        if len(h) >= 30 or m in INFLACAO:
            continue
        if falhas >= 1:                  # fonte fora do ar: não insiste moeda por moeda
            break
        try:
            resp = requests.get(URL_HIST.format(m=m), timeout=30)
            dados = resp.json()
            if not isinstance(dados, list):
                falhas += 1
                log(f"Histórico de {m} indisponível: resposta inesperada ({str(dados)[:120]})")
            for linha in dados if isinstance(dados, list) else []:
                from datetime import datetime
                dia = datetime.fromtimestamp(int(linha["timestamp"])).date().isoformat()
                bid = float(linha["bid"])          # reais por 1 unidade da moeda
                if bid > 0:
                    h.setdefault(dia, round(1 / bid, 6))
        except Exception as e:
            falhas += 1
            log(f"Histórico de {m} indisponível: {e}")
    faltando = {m for m in moedas_monitoradas() if len(cambio.get(m, {})) < 30}
    if faltando:
        _semear_frankfurter(cambio, faltando, log)
    if any(len(cambio.get(m, {})) < 8 for m in moedas_monitoradas()):
        _semear_mensal(cambio, log)


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
    """Por moeda: quanto R$ 100 compram hoje e quanto o real está mais forte (+) ou fraco (−) que a média do ano."""
    lista = []
    ref = hoje()
    for m in moedas_monitoradas():
        h = cambio.get(m) or {}
        if not h:
            continue
        ultimo = max(h)
        atual = h[ultimo]
        ano = [v for d, v in h.items() if (ref - para_data(d)).days <= 365 and d != ultimo]
        variacao = None
        if m not in INFLACAO and len(ano) >= 6:
            v = (atual / statistics.mean(ano) - 1) * 100
            if abs(v) <= 60:            # dado quebrado ou unidade diferente: melhor não mostrar
                variacao = round(v, 1)
        paises = sorted(n for n, p in bd.PAISES.items() if p.get("moeda") == m and p.get("entrada") != "visto")
        if not paises:
            continue
        lista.append(dict(moeda=m, nome=bd.NOME_MOEDA.get(m, m), por_100=round(atual * 100, 2), variacao=variacao,
                          inflacao=m in INFLACAO, data=ultimo, paises=paises,
                          dolar={p: bd.DOLAR[p] for p in paises if p in bd.DOLAR}))
    lista.sort(key=lambda x: -(x["variacao"] if x["variacao"] is not None else -999))
    return lista
