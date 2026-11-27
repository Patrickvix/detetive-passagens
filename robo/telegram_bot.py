"""Conversa com o bot do Telegram: envia avisos e lê comandos (favoritar, remover, passaporte)."""
import html
import re

import requests

from . import base_dados as bd


class Bot:
    def __init__(self, token, estado, log=print):
        self.url = f"https://api.telegram.org/bot{token}"
        self.estado = estado          # dict salvo em estado/telegram.json
        self.log = log

    def _api(self, metodo, **dados):
        r = requests.post(f"{self.url}/{metodo}", json=dados, timeout=30)
        resposta = r.json()
        if not resposta.get("ok"):
            self.log(f"Telegram {metodo} falhou: {resposta.get('description')}")
        return resposta

    @property
    def chat(self):
        return self.estado.get("chat_id")

    def nome_do_bot(self):
        if not self.estado.get("bot_username"):
            r = self._api("getMe")
            if r.get("ok"):
                self.estado["bot_username"] = r["result"]["username"]
        return self.estado.get("bot_username")

    def enviar(self, texto, botoes=None):
        if not self.chat:
            return
        dados = dict(chat_id=self.chat, text=texto[:4000], parse_mode="HTML", disable_web_page_preview=True)
        if botoes:
            dados["reply_markup"] = {"inline_keyboard": [[{"text": t, "callback_data": c}] for t, c in botoes[:4]]}
        self._api("sendMessage", **dados)

    # A validade do passaporte fica só na mensagem fixada do seu chat (não vai para o repositório público).
    def salvar_passaporte(self, validade_iso):
        r = self._api("sendMessage", chat_id=self.chat, text=f"🛂 Validade do passaporte: {validade_iso}")
        if r.get("ok"):
            self._api("pinChatMessage", chat_id=self.chat, message_id=r["result"]["message_id"],
                      disable_notification=True)

    def ler_passaporte(self):
        if not self.chat:
            return None
        r = self._api("getChat", chat_id=self.chat)
        texto = ((r.get("result") or {}).get("pinned_message") or {}).get("text", "")
        m = re.search(r"Validade do passaporte: (\d{4}-\d{2}-\d{2})", texto)
        return m[1] if m else None

    def ler_comandos(self):
        """Devolve a lista de comandos recebidos desde a última execução: [(comando, argumento)]."""
        r = self._api("getUpdates", offset=self.estado.get("offset", 0), timeout=0,
                      allowed_updates=["message", "callback_query"])
        comandos = []
        for up in r.get("result", []):
            self.estado["offset"] = up["update_id"] + 1
            if "callback_query" in up:
                cq = up["callback_query"]
                origem = cq["message"]["chat"]["id"]
                texto = cq.get("data", "")
                self._api("answerCallbackQuery", callback_query_id=cq["id"], text="Anotado! Confirmo em seguida.")
            elif "message" in up:
                origem = up["message"]["chat"]["id"]
                texto = up["message"].get("text", "")
            else:
                continue
            if self.chat is None:
                # sem dono configurado: só ensina como configurar e não guarda nada
                if texto.startswith("/start"):
                    self._api("sendMessage", chat_id=origem,
                              text=f"Seu código de chat é {origem}. No GitHub, crie o segredo TELEGRAM_CHAT_ID com esse número.")
                continue
            if origem != self.chat:
                continue                                    # ignora qualquer outra pessoa
            comandos.append(_interpretar(texto))
        return [c for c in comandos if c]


def _interpretar(texto):
    texto = (texto or "").strip()
    m = re.match(r"^fav:([A-Z]{3})$", texto)
    if m:
        return ("favoritar", m[1])
    m = re.match(r"^/start(?:\s+(fav|rem)_([A-Za-z]{3}))?", texto)
    if m:
        if m[1] == "fav":
            return ("favoritar", m[2].upper())
        if m[1] == "rem":
            return ("remover", m[2].upper())
        return ("inicio", None)
    partes = texto.split(maxsplit=1)
    cmd = partes[0].lower().split("@")[0] if partes else ""
    arg = partes[1].strip() if len(partes) > 1 else None
    mapa = {"/favoritar": "favoritar", "/remover": "remover", "/favoritos": "favoritos",
            "/passaporte": "passaporte", "/status": "status", "/ajuda": "ajuda", "/help": "ajuda"}
    if cmd in mapa:
        return (mapa[cmd], arg)
    return None


AJUDA = (
    "🕵️ <b>Detetive de Passagens</b>\n\n"
    "Eu vigio promoções e preços saindo de Vitória e te aviso aqui.\n\n"
    "<b>Comandos</b>\n"
    "/favoritos – lista os destinos vigiados todo dia\n"
    "/favoritar SSA – vigia um destino (código do aeroporto ou nome)\n"
    "/remover SSA – para de vigiar\n"
    "/passaporte 2031-05-20 – data de validade, para eu te lembrar antes de vencer\n"
    "/status – gasto do Apify no mês e última busca\n\n"
    "Toque em ⭐ nos avisos para favoritar. Eu leio os comandos a cada hora."
)


def esc(t):
    return html.escape(str(t or ""))


def achar_iata(arg):
    """Aceita código (SSA) ou nome (Salvador, Jericoacoara)."""
    if not arg:
        return None
    a = arg.strip()
    if re.fullmatch(r"[A-Za-z]{3}", a):
        return a.upper()
    from .util import sem_acento
    alvo = sem_acento(a)
    for d in bd.DESTINOS:
        if alvo in (sem_acento(d["nome"]), sem_acento(d["local"])) or alvo in [sem_acento(t) for t in d["termos"]]:
            return d["iata"]
    for d in bd.DESTINOS:
        if alvo in sem_acento(d["local"]):
            return d["iata"]
    return None
