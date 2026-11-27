import json
import os
import re
import unicodedata
from datetime import datetime, date, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "docs" / "dados"      # lido pelo app (site)
ESTADO = RAIZ / "estado"             # memória interna do robô

FUSO_BR = timezone(timedelta(hours=-3))


def agora():
    return datetime.now(FUSO_BR)


def hoje():
    return agora().date()


def ler(caminho, padrao):
    caminho = Path(caminho)
    if not caminho.exists():
        return padrao
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return padrao


def salvar(caminho, dados):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.with_suffix(".tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False, indent=1, sort_keys=False), encoding="utf-8")
    os.replace(tmp, caminho)


def sem_acento(texto):
    texto = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in texto if not unicodedata.combining(c)).lower()


def contem_termo(texto_normalizado, termo):
    """Procura o termo como palavra inteira (texto já sem acento e minúsculo)."""
    t = re.escape(sem_acento(termo))
    return re.search(rf"(?<![a-z0-9]){t}(?![a-z0-9])", texto_normalizado) is not None


def iso(d):
    return d.isoformat() if isinstance(d, (date, datetime)) else d


def para_data(s):
    return date.fromisoformat(s[:10])


MESES_ABREV = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def mes_ano(d):
    d = para_data(d) if isinstance(d, str) else d
    return f"{MESES_ABREV[d.month - 1]}/{d.year}"


def real(valor):
    return "R$ " + f"{valor:,.0f}".replace(",", ".")


# Categorias por antecedência (dias entre hoje e a viagem)
CATEGORIAS = [
    ("relampago", "⚡ Relâmpago", 0, 30),
    ("proximos", "📅 Próximos meses", 30, 90),
    ("medio", "🗓️ Médio prazo", 90, 180),
    ("longo", "🌴 Longo prazo", 180, 10_000),
]


def categorias_do_periodo(inicio, fim, referencia=None):
    """Todas as categorias que o período de viagem [inicio, fim] cobre."""
    ref = referencia or hoje()
    a = max((inicio - ref).days, 0)
    b = max((fim - ref).days, a)
    return [cod for cod, _, lo, hi in CATEGORIAS if a < hi and b >= lo]


def rotulo_categoria(cod):
    for c, rot, *_ in CATEGORIAS:
        if c == cod:
            return rot
    return "❔ Sem data"
