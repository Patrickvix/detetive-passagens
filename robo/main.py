"""Robô do Detetive de Passagens. Roda de hora em hora no GitHub Actions.

- toda hora: lê comandos do Telegram e novas promoções dos blogs
- 1x por dia (a partir das 7h): preços das rotas, câmbio e lembrete do passaporte
- 1x por semana (segunda): explora os destinos mais baratos saindo de Vitória
"""
import os
import sys
from datetime import timedelta

from . import base_dados as bd
from . import cambio, promos, voos
from .telegram_bot import Bot, AJUDA, esc, achar_iata
from .util import sem_acento as util_sem_acento
from .util import (DADOS, ESTADO, agora, hoje, iso, ler, salvar, para_data, mes_ano, real,
                   rotulo_categoria, CATEGORIAS)

LIMITE_APIFY_USD = float(os.environ.get("LIMITE_APIFY_USD", "3.5"))
HORA_DIARIA = 7


def log(msg):
    m = str(msg)
    if m.startswith("::"):             # anotações do GitHub precisam começar a linha
        print(m, flush=True)
    elif any(t in m for t in ("falhou", "indisponível", "Sem APIFY", "Sem TELEGRAM")):
        print(f"::warning title=Atenção::{m[:300]}", flush=True)
    else:
        print(f"[{agora():%H:%M}] {msg}", flush=True)


def carregar():
    return dict(
        tg=ler(ESTADO / "telegram.json", {}),
        status=ler(DADOS / "status.json", {}),
        favoritos=ler(DADOS / "favoritos.json", None),
        promocoes=ler(DADOS / "promocoes.json", []),
        vistos=set(ler(ESTADO / "links_vistos.json", [])),
        precos=ler(DADOS / "precos.json", {}),
        descobertas=ler(DADOS / "descobertas.json", {"ultima": [], "historico": {}}),
        cambio=ler(ESTADO / "cambio.json", {}),
    )


def guardar(e):
    # o código do chat vem do segredo do GitHub e nunca é gravado no repositório público
    salvar(ESTADO / "telegram.json", {k: v for k, v in e["tg"].items() if k != "chat_id"})
    salvar(DADOS / "status.json", e["status"])
    salvar(DADOS / "favoritos.json", e["favoritos"])
    salvar(DADOS / "promocoes.json", e["promocoes"][:400])
    salvar(ESTADO / "links_vistos.json", sorted(e["vistos"])[-3000:])
    salvar(DADOS / "precos.json", e["precos"])
    salvar(DADOS / "descobertas.json", e["descobertas"])
    salvar(ESTADO / "cambio.json", e["cambio"])
    # tabelas fixas para o app
    salvar(DADOS / "destinos.json", dict(grupos=bd.GRUPOS, destinos=bd.DESTINOS, paises=bd.PAISES,
                                         verificado_em=bd.VERIFICADO_EM, etias=bd.ETIAS_NOTA,
                                         categorias=[dict(cod=c, nome=n, de=a, ate=b) for c, n, a, b in CATEGORIAS]))


def nome_destino(iata, e=None):
    d = bd.DESTINO_POR_IATA.get(iata)
    if d:
        return d["local"]
    if e:
        h = e["descobertas"]["historico"].get(iata)
        if h:
            return f'{h.get("cidade")} ({h.get("pais")})'
        f = next((f for f in e["favoritos"] if f["iata"] == iata), None)
        if f:
            return f["nome"]
    return iata


def pais_de(iata, e):
    if iata in bd.PAIS_POR_IATA:
        return bd.PAIS_POR_IATA[iata]
    h = e["descobertas"]["historico"].get(iata)
    return h.get("pais") if h else None


# ---------------- Telegram: comandos ----------------

def tratar_comandos(bot, e):
    for cmd, arg in bot.ler_comandos():
        favs = e["favoritos"]
        if cmd in ("inicio", "ajuda"):
            bot.enviar(AJUDA)
        elif cmd == "favoritar":
            iata = achar_iata(arg)
            if not iata:
                bot.enviar("Não achei esse destino. Use o código do aeroporto (ex.: /favoritar SSA) ou o nome da cidade.")
            elif any(f["iata"] == iata for f in favs):
                bot.enviar(f"⭐ {esc(nome_destino(iata, e))} já está nos favoritos.")
            else:
                favs.append(dict(iata=iata, nome=nome_destino(iata, e), desde=iso(hoje())))
                bot.enviar(f"⭐ Pronto! Vou vigiar <b>{esc(nome_destino(iata, e))}</b> todo dia a partir de amanhã.")
        elif cmd == "remover":
            iata = achar_iata(arg)
            antes = len(favs)
            e["favoritos"] = [f for f in favs if f["iata"] != iata]
            bot.enviar(f"Removido: {esc(nome_destino(iata, e))}." if len(e["favoritos"]) < antes
                       else "Esse destino não estava nos favoritos.")
        elif cmd == "favoritos":
            linhas = [f"• {esc(f['nome'])} ({f['iata']})" for f in favs]
            bot.enviar("⭐ <b>Favoritos vigiados todo dia</b>\n" + ("\n".join(linhas) or "nenhum"))
        elif cmd == "passaporte":
            try:
                validade = para_data((arg or "").strip())
                bot.salvar_passaporte(iso(validade))
                e["tg"]["passaporte_avisos"] = []
                bot.enviar(f"🛂 Anotado: passaporte válido até {validade:%d/%m/%Y}. Aviso quando faltar 1 ano, 9 meses e 6 meses.")
            except ValueError:
                bot.enviar("Mande no formato ano-mês-dia, por exemplo: /passaporte 2031-05-20")
        elif cmd == "status":
            st = e["status"]
            bot.enviar(f"📊 Apify neste mês: US$ {voos.Apify(None, st, LIMITE_APIFY_USD).gasto_mes():.3f} "
                       f"de US$ {LIMITE_APIFY_USD}\nÚltima busca de preços: {st.get('ultimo_voos', 'ainda não')}\n"
                       f"Favoritos: {len(e['favoritos'])}")


# ---------------- Promoções ----------------

def linha_entrada(paises):
    return "\n".join(f"{esc(p)}: {bd.resumo_entrada(p)}" for p in paises if p != "Brasil")


def aviso_promocao(p):
    cats = [rotulo_categoria(c) for c in p["categorias"]]
    tipo = "✈️ Milhas" if p["tipo"] == "milhas" else "✈️ Passagem"
    periodo = ""
    if p["viagem_inicio"]:
        ini, fim = mes_ano(p["viagem_inicio"]), mes_ano(p["viagem_fim"])
        periodo = f"\n🗓️ Viagem: {ini}" + (f" a {fim}" if fim != ini else "")
    destinos = ", ".join(bd.DESTINO_POR_IATA[i]["nome"] for i in p["destinos"][:6])
    preco = f"💰 {esc(p['preco'])}\n" if p.get("preco") else ""
    texto = (f"{' · '.join(cats)} | {tipo}\n<b>{esc(p['titulo'])}</b>\n{preco}"
             f"📍 {esc(p['origem'])}" + (f" → {esc(destinos)}" if destinos else "") + periodo)
    entrada = linha_entrada(p["paises"])
    if entrada:
        texto += "\n" + entrada
    texto += f"\n🔗 <a href=\"{esc(p['link'])}\">{esc(p['fonte'])}</a>"
    botoes = [(f"⭐ Favoritar {bd.DESTINO_POR_IATA[i]['nome']}", f"fav:{i}") for i in p["destinos"][:3]]
    return texto, botoes


def rodar_promocoes(bot, e):
    novas = promos.buscar_novas(e["vistos"], log=log)
    enviadas = 0
    titulos = {util_sem_acento(x["titulo"]) for x in e["promocoes"][:80]}
    for link, p in novas:
        e["vistos"].add(link)
        if not p or util_sem_acento(p["titulo"]) in titulos:
            continue          # repetida (mesma oferta em outro blog)
        titulos.add(util_sem_acento(p["titulo"]))
        e["promocoes"].insert(0, p)
        if p["exige_visto"] or not p.get("relevante"):
            continue          # visto ou não é oferta de voo (cartão, bônus, hotel): fica no app escondido, sem aviso
        texto, botoes = aviso_promocao(p)
        bot.enviar(texto, botoes)
        enviadas += 1
    log(f"Promoções: {len(novas)} novas lidas, {enviadas} avisos")


# ---------------- Preços (1x por dia) ----------------

def aviso_preco(a, e):
    ida, volta = para_data(a["ida"]), para_data(a["volta"])
    nome = nome_destino(a["iata"], e)
    fav = any(f["iata"] == a["iata"] for f in e["favoritos"])
    dias = (ida - hoje()).days
    cat = next((n for c, n, lo, hi in CATEGORIAS if lo <= dias < hi), "")
    texto = (f"{'⭐ Favorito' if fav else '📉 Preço baixo'} · {cat}\n"
             f"<b>Vitória → {esc(nome)}</b>\n💰 {real(a['menor'])} ida e volta ({esc(a['motivo'])})\n"
             f"🗓️ {ida:%d/%m/%Y} a {volta:%d/%m/%Y}" + (f" · {esc(a['cia'])}" if a.get("cia") else ""))
    p = pais_de(a["iata"], e)
    if p and p != "Brasil":
        texto += f"\n{bd.resumo_entrada(p)}"
    url = f"https://www.google.com/travel/flights?q=Flights%20from%20VIX%20to%20{a['iata']}%20on%20{a['ida']}%20through%20{a['volta']}"
    texto += f"\n🔎 <a href=\"{url}\">Ver no Google Flights</a>"
    botoes = [] if fav else [(f"⭐ Favoritar {nome[:30]}", f"fav:{a['iata']}")]
    return texto, botoes


def rodar_precos(bot, e, apify):
    favs = [f["iata"] for f in e["favoritos"]]
    rotas = voos.rotas_do_dia(e["favoritos"])
    log(f"Preços: {len(rotas)} rotas, janela +{voos.janela_do_dia()} dias")
    novos = voos.buscar_precos(apify, rotas)
    alertas = voos.registrar_e_avaliar(e["precos"], novos, set(favs))
    for a in alertas:
        if pais_de(a["iata"], e) and bd.pais_info(pais_de(a["iata"], e))["entrada"] == "visto":
            continue
        bot.enviar(*aviso_preco(a, e))
    log(f"Preços: {len(novos)} rotas com preço, {len(alertas)} quedas")


def rodar_exploracao(bot, e, apify):
    achados = voos.explorar(apify)
    if not achados:
        return
    for a in achados:
        a["entrada"] = bd.pais_info(a["pais"])["entrada"] if a.get("pais") in bd.PAISES else "conferir"
        a["destino"] = bd.AEROPORTO_PARA_DESTINO.get(a["aeroporto"], a["aeroporto"])
    e["descobertas"]["ultima"] = sorted(achados, key=lambda a: a["preco"])
    e["descobertas"]["data"] = iso(hoje())
    alertas = voos.avaliar_descobertas(e["descobertas"]["historico"], achados)
    for a in alertas:
        if a["entrada"] == "visto" or (para_data(a["ida"]) - hoje()).days < 30:
            continue
        texto = (f"🧭 Descoberta saindo de Vitória\n<b>{esc(a['cidade'])} ({esc(a['pais'])})</b>\n"
                 f"💰 {real(a['preco'])} ida e volta · {para_data(a['ida']):%d/%m} a {para_data(a['volta']):%d/%m/%Y}\n"
                 f"{bd.resumo_entrada(a['pais'])}")
        bot.enviar(texto, [(f"⭐ Favoritar {a['cidade']}", f"fav:{a['destino']}")])
    log(f"Exploração: {len(achados)} destinos, {len(alertas)} avisos")


def rodar_cambio(bot, e):
    try:
        cambio.semear_historico(e["cambio"], log=log)
        cambio.atualizar(e["cambio"], log=log)
    except Exception as ex:
        log(f"Câmbio falhou: {ex}")
    rank = cambio.ranking(e["cambio"])
    salvar(DADOS / "real_forte.json", dict(data=iso(hoje()), moedas=rank))
    return bool(rank)
    if hoje().weekday() == 0:
        fortes = [r for r in rank if r["variacao"] >= 5][:6]
        if fortes:
            linhas = []
            for r in fortes:
                p = r["paises"][0]
                linhas.append(f"• {esc(', '.join(r['paises'][:3]))} ({r['moeda']}): real {r['variacao']:+.1f}% vs média do ano · {bd.resumo_entrada(p)}")
            bot.enviar("💱 <b>Real forte esta semana</b>\n" + "\n".join(linhas))


def lembrete_passaporte(bot, e):
    validade = bot.ler_passaporte()
    if not validade:
        return
    faltam = (para_data(validade) - hoje()).days
    avisados = e["tg"].setdefault("passaporte_avisos", [])
    for marco, texto in [(365, "1 ano"), (270, "9 meses"), (180, "6 meses")]:
        if faltam <= marco and marco not in avisados:
            avisados.append(marco)
            bot.enviar(f"🛂 Seu passaporte vence em {texto} ({para_data(validade):%d/%m/%Y}).\n"
                       "Muitos países exigem 6 meses de validade na volta. Agende a renovação na Polícia Federal: "
                       "https://www.gov.br/pf/pt-br/assuntos/passaporte")
            break


def main():
    token_tg = os.environ.get("TELEGRAM_TOKEN")
    token_apify = os.environ.get("APIFY_TOKEN")
    if not token_tg:
        sys.exit("Falta o segredo TELEGRAM_TOKEN no GitHub.")
    e = carregar()
    if e["favoritos"] is None:
        e["favoritos"] = [dict(iata=i, nome=bd.DESTINO_POR_IATA[i]["local"], desde=iso(hoje())) for i in bd.FAVORITOS_INICIAIS]
    chat_env = (os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
    if chat_env:
        try:
            e["tg"]["chat_id"] = int(chat_env)
        except ValueError:
            sys.exit("O segredo TELEGRAM_CHAT_ID deve ter só o número do chat (ex.: 123456789).")
    bot = Bot(token_tg, e["tg"], log=log)
    e["status"]["bot"] = bot.nome_do_bot()
    primeira_vez = not e["vistos"]

    for antigo in e["promocoes"]:
        promos.enriquecer(antigo)
    tratar_comandos(bot, e)
    if not bot.chat:
        log("Sem TELEGRAM_CHAT_ID: mande /start ao bot para receber o código e crie o segredo no GitHub.")
        guardar(e)
        return

    if primeira_vez:
        # primeira execução: só aprende o que já existe, para não despejar dezenas de avisos antigos
        for link, p in promos.buscar_novas(set(), limite_paginas=40, log=log):
            e["vistos"].add(link)
            if p:
                e["promocoes"].append(p)
        bot.enviar("🕵️ Detetive ligado! Já li as promoções de hoje (estão no app). A partir de agora aviso as novas.\n\n" + AJUDA)
    else:
        rodar_promocoes(bot, e)

    if agora().hour >= HORA_DIARIA and e["status"].get("ultimo_voos") != iso(hoje()):
        cambio_ok = rodar_cambio(bot, e)
        lembrete_passaporte(bot, e)
        if token_apify:
            apify = voos.Apify(token_apify, e["status"], LIMITE_APIFY_USD, log=log)
            try:
                rodar_precos(bot, e, apify)
                if hoje().weekday() == 0 or not e["descobertas"]["ultima"]:
                    rodar_exploracao(bot, e, apify)
            except Exception as ex:
                log(f"Busca de preços falhou: {ex}")
        else:
            log("Sem APIFY_TOKEN: pulando preços.")
        if cambio_ok:                     # se o câmbio falhou, tenta de novo na próxima execução
            e["status"]["ultimo_voos"] = iso(hoje())

    e["status"]["ultima_execucao"] = agora().isoformat(timespec="minutes")
    guardar(e)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as erro:   # mostra o motivo no resumo da execução no GitHub
        import traceback
        traceback.print_exc()
        msg = f"{type(erro).__name__}: {erro}".replace("\n", " ")
        print(f"::error title=Erro no robô::{msg[:400]}")
        sys.exit(1)
