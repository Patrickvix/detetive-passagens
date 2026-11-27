"""Radar de promoções: lê os blogs de passagens e milhas e classifica cada oferta."""
import re
import xml.etree.ElementTree as ET
from datetime import date
from email.utils import parsedate_to_datetime

import requests
from bs4 import BeautifulSoup

from . import base_dados as bd
from .util import sem_acento, contem_termo, categorias_do_periodo, hoje, FUSO_BR

FEEDS = [
    ("Melhores Destinos", "https://www.melhoresdestinos.com.br/feed"),
    ("Passageiro de Primeira", "https://passageirodeprimeira.com/feed/"),
    ("Pontos pra Voar", "https://pontospravoar.com/feed/"),
]

CABECALHO = {"User-Agent": "Mozilla/5.0 (DetetiveDePassagens; uso pessoal)"}

PALAVRAS_PASSAGEM = ["passagem", "passagens", "voo", "voos", "aerea", "aereas", "ida e volta", "trecho",
                     "companhia aerea", "latam", "gol", "azul", "tap", "iberia", "air france", "klm"]
PALAVRAS_MILHAS = ["milhas", "pontos", "smiles", "latam pass", "azul fidelidade", "tudoazul", "livelo",
                   "esfera", "avios", "bonus de transferencia", "transferencia bonificada", "clube smiles"]
SO_OUTROS = ["aluguel de carro", "hotel", "hoteis", "hospedagem", "cruzeiro", "seguro viagem", "ingresso",
             "pacote", "chip", "cartao de credito"]
ORIGEM_VIX = ["de vitoria", "vitoria (vix)", "vitoria/es", "vitoria-es", "vitoria (es)", "saindo de vitoria",
              "partindo de vitoria", "vix"]
MUITAS_ORIGENS = ["varias cidades", "diversas cidades", "mais de 50 cidades", "saindo de varias", "varias origens",
                  "todo o brasil"]

MESES = {"janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4, "maio": 5, "junho": 6, "julho": 7,
         "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12}


def ler_feed(url):
    r = requests.get(url, headers=CABECALHO, timeout=30)
    r.raise_for_status()
    raiz = ET.fromstring(r.content)
    itens = []
    for item in raiz.iter("item"):
        titulo = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        resumo = BeautifulSoup(item.findtext("description") or "", "html.parser").get_text(" ", strip=True)
        try:
            pub = parsedate_to_datetime(item.findtext("pubDate")).astimezone(FUSO_BR)
        except (TypeError, ValueError):
            pub = None
        if link:
            itens.append(dict(titulo=titulo, link=link, resumo=resumo, publicado=pub.isoformat() if pub else None))
    return itens


def texto_da_pagina(url):
    r = requests.get(url, headers=CABECALHO, timeout=30)
    r.raise_for_status()
    sopa = BeautifulSoup(r.text, "html.parser")
    for lixo in sopa(["script", "style", "nav", "footer", "header", "aside", "form"]):
        lixo.decompose()
    corpo = sopa.find("article") or sopa.find("main") or sopa.body or sopa
    return corpo.get_text(" ", strip=True)[:20000]


def _ano_provavel(mes, referencia):
    """Mês sem ano: assume a próxima vez que esse mês acontece."""
    return referencia.year if mes >= referencia.month else referencia.year + 1


def datas_de_viagem(texto, publicado):
    """Extrai as datas de viagem citadas no texto (ignora datas de publicação e prazos de compra)."""
    t = sem_acento(texto)
    ref = publicado or hoje()
    datas = []

    def contexto_ruim(ini):
        antes = t[max(0, ini - 45):ini]
        antes = re.split(r"[.;!?]\s", antes)[-1]      # só a frase atual
        return any(p in antes for p in ["compra", "emiti", "valid", "publicad", "atualizad", "ate as", "vende", "resgat"])

    # 10/03/2027, 10/03/27
    for m in re.finditer(r"(?<!\d)(\d{1,2})/(\d{1,2})/(\d{2,4})(?!\d)", t):
        if t[m.end():m.end() + 4].strip().startswith("as") or contexto_ruim(m.start()):
            continue
        d, mo, a = int(m[1]), int(m[2]), int(m[3])
        a = a + 2000 if a < 100 else a
        try:
            datas.append(date(a, mo, d))
        except ValueError:
            pass
    # "março de 2027", "março/2027", "de março a junho de 2027"
    nomes = "|".join(MESES)
    for m in re.finditer(rf"(?<![a-z])({nomes})(?:\s*(?:de|/)\s*(20\d\d))?", t):
        if contexto_ruim(m.start()):
            continue
        mes = MESES[m[1]]
        ano = int(m[2]) if m[2] else None
        if ano is None:
            seguinte = re.search(r"20\d\d", t[m.end():m.end() + 40])
            ano = int(seguinte.group()) if seguinte else _ano_provavel(mes, ref)
        try:
            datas.append(date(ano, mes, 15))
        except ValueError:
            pass
    datas = sorted({d for d in datas if ref <= d <= date(ref.year + 2, 12, 31)})
    return datas


def destinos_citados(texto):
    t = sem_acento(texto)
    achados = []
    for d in bd.DESTINOS:
        if any(contem_termo(t, termo) for termo in d["termos"]):
            achados.append(d["iata"])
    return achados


def classificar(item, texto_completo):
    titulo_n = sem_acento(item["titulo"])
    tudo = f'{item["titulo"]} . {item["resumo"]} . {texto_completo}'
    tudo_n = sem_acento(tudo)

    e_milhas = any(contem_termo(titulo_n, p) for p in PALAVRAS_MILHAS)
    e_passagem = any(contem_termo(titulo_n, p) for p in PALAVRAS_PASSAGEM)
    if not (e_milhas or e_passagem):
        if any(p in titulo_n for p in SO_OUTROS):
            return None
        if not any(contem_termo(tudo_n, p) for p in ["passagem", "passagens", "milhas"]):
            return None

    publicado = None
    if item.get("publicado"):
        publicado = date.fromisoformat(item["publicado"][:10])

    iatas = destinos_citados(tudo)
    datas = datas_de_viagem(tudo, publicado)
    if datas:
        inicio, fim = datas[0], datas[-1]
        cats = categorias_do_periodo(inicio, fim)
    else:
        inicio = fim = None
        cats = ["sem_data"]

    grupos = sorted({bd.GRUPO_POR_IATA[i] for i in iatas}) if iatas else []
    paises = sorted({bd.PAIS_POR_IATA[i] for i in iatas})
    exige_visto = bool(paises) and all(bd.pais_info(p)["entrada"] == "visto" for p in paises)

    if any(p in tudo_n for p in ORIGEM_VIX):
        origem = "Sai de Vitória"
    elif any(p in tudo_n for p in MUITAS_ORIGENS):
        origem = "Várias cidades"
    else:
        origem = "Origem não informada"

    return dict(
        titulo=item["titulo"], link=item["link"], fonte=item.get("fonte"), publicado=item.get("publicado"),
        resumo=item["resumo"][:300], tipo="milhas" if e_milhas else "passagem",
        destinos=iatas, grupos=grupos, paises=paises, origem=origem,
        viagem_inicio=inicio.isoformat() if inicio else None, viagem_fim=fim.isoformat() if fim else None,
        categorias=cats, exige_visto=exige_visto,
    )


def buscar_novas(vistos, limite_paginas=25, log=print):
    """Devolve as promoções novas (que ainda não estão em `vistos`)."""
    novas = []
    for fonte, url in FEEDS:
        try:
            itens = ler_feed(url)
        except Exception as e:  # um blog fora do ar não pode parar o robô
            log(f"Feed {fonte} falhou: {e}")
            continue
        for it in itens:
            if it["link"] in vistos:
                continue
            it["fonte"] = fonte
            novas.append(it)
    resultado = []
    for it in novas[:limite_paginas]:
        try:
            texto = texto_da_pagina(it["link"])
        except Exception as e:
            log(f"Página falhou ({it['link']}): {e}")
            texto = ""
        promo = classificar(it, texto)
        resultado.append((it["link"], promo))
    return resultado
