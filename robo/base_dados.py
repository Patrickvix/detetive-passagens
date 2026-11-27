"""Tabelas fixas do Detetive de Passagens: destinos, países, regras de entrada e vacinas.

As regras de entrada e de vacina mudam. Cada país tem a data em que a regra foi conferida
e o link oficial para confirmar antes de comprar.
"""

VERIFICADO_EM = "2026-11-27"

LINK_CIVP = "https://www.gov.br/pt-br/servicos/obter-o-certificado-internacional-de-vacinacao-e-profilaxia"
LINK_ITAMARATY = "https://www.gov.br/mre/pt-br/assuntos/portal-consular"

# entrada: "livre" (sem visto), "online" (autorização eletrônica feita pela internet), "visto" (visto consular)
# documento: "RG" (RG com menos de 10 anos ou passaporte) ou "passaporte"
# vacina_fa (febre amarela / CIVP): "exige", "nao", "depende", "conferir"
PAISES = {
    "Brasil": dict(continente="Brasil", documento="RG", entrada="livre", vacina_fa="nao", moeda="BRL"),
    # --- América do Sul (Mercosul e associados: RG serve) ---
    "Argentina": dict(continente="América do Sul", documento="RG", entrada="livre", vacina_fa="nao", moeda="ARS",
                      nota_moeda="Inflação alta: a comparação do câmbio com a média do ano engana, por isso fica fora do Real forte."),
    "Uruguai": dict(continente="América do Sul", documento="RG", entrada="livre", vacina_fa="nao", moeda="UYU"),
    "Paraguai": dict(continente="América do Sul", documento="RG", entrada="livre", vacina_fa="conferir", moeda="PYG",
                     nota_vacina="Já exigiu o certificado para voos a Assunção. Confira antes."),
    "Chile": dict(continente="América do Sul", documento="RG", entrada="livre", vacina_fa="nao", moeda="CLP"),
    "Bolívia": dict(continente="América do Sul", documento="RG", entrada="livre", vacina_fa="depende", moeda="BOB",
                    nota_vacina="Pedido principalmente em roteiros por Santa Cruz, Amazônia boliviana e áreas tropicais."),
    "Peru": dict(continente="América do Sul", documento="RG", entrada="livre", vacina_fa="nao", moeda="PEN",
                 nota_vacina="Não exige hoje, mas recomenda a vacina para a Amazônia peruana."),
    "Equador": dict(continente="América do Sul", documento="RG", entrada="livre", vacina_fa="nao", moeda="USD",
                    nota_vacina="A exigência foi retirada em agosto de 2025; a vacina segue recomendada."),
    "Colômbia": dict(continente="América do Sul", documento="RG", entrada="livre", vacina_fa="conferir", moeda="COP",
                     nota_vacina="Teve casos de febre amarela em 2026 e costuma pedir o certificado. Confira antes."),
    "Venezuela": dict(continente="América do Sul", documento="RG", entrada="livre", vacina_fa="conferir", moeda="VES",
                      nota_moeda="Inflação alta: fica fora do Real forte."),
    # --- Europa ---
    "Portugal": dict(continente="Europa", schengen=True, moeda="EUR"),
    "Espanha": dict(continente="Europa", schengen=True, moeda="EUR"),
    "França": dict(continente="Europa", schengen=True, moeda="EUR"),
    "Itália": dict(continente="Europa", schengen=True, moeda="EUR"),
    "Alemanha": dict(continente="Europa", schengen=True, moeda="EUR"),
    "Países Baixos": dict(continente="Europa", schengen=True, moeda="EUR"),
    "Bélgica": dict(continente="Europa", schengen=True, moeda="EUR"),
    "Luxemburgo": dict(continente="Europa", schengen=True, moeda="EUR"),
    "Suíça": dict(continente="Europa", schengen=True, moeda="CHF"),
    "Áustria": dict(continente="Europa", schengen=True, moeda="EUR"),
    "Tchéquia": dict(continente="Europa", schengen=True, moeda="CZK"),
    "Hungria": dict(continente="Europa", schengen=True, moeda="HUF"),
    "Polônia": dict(continente="Europa", schengen=True, moeda="PLN"),
    "Eslováquia": dict(continente="Europa", schengen=True, moeda="EUR"),
    "Eslovênia": dict(continente="Europa", schengen=True, moeda="EUR"),
    "Croácia": dict(continente="Europa", schengen=True, moeda="EUR"),
    "Grécia": dict(continente="Europa", schengen=True, moeda="EUR"),
    "Malta": dict(continente="Europa", schengen=True, moeda="EUR"),
    "Dinamarca": dict(continente="Europa", schengen=True, moeda="DKK"),
    "Suécia": dict(continente="Europa", schengen=True, moeda="SEK"),
    "Noruega": dict(continente="Europa", schengen=True, moeda="NOK"),
    "Finlândia": dict(continente="Europa", schengen=True, moeda="EUR"),
    "Islândia": dict(continente="Europa", schengen=True, moeda="ISK"),
    "Estônia": dict(continente="Europa", schengen=True, moeda="EUR"),
    "Letônia": dict(continente="Europa", schengen=True, moeda="EUR"),
    "Lituânia": dict(continente="Europa", schengen=True, moeda="EUR"),
    "Romênia": dict(continente="Europa", schengen=True, moeda="RON"),
    "Bulgária": dict(continente="Europa", schengen=True, moeda="EUR"),
    "Chipre": dict(continente="Europa", moeda="EUR", nota_entrada="Fora do Schengen, mas da União Europeia: entra no ETIAS quando começar."),
    "Irlanda": dict(continente="Europa", moeda="EUR", nota_entrada="Fora do Schengen e do ETIAS. Entrada sem visto para turismo."),
    "Reino Unido": dict(continente="Europa", entrada="online", moeda="GBP",
                        nota_entrada="Precisa da ETA (autorização eletrônica, £16, vale 2 anos). Pedido pelo app ou site oficial do governo britânico."),
    "Turquia": dict(continente="Europa", moeda="TRY", nota_entrada="Sem visto para turismo curto.",
                    nota_moeda="Inflação alta: fica fora do Real forte."),
    "Sérvia": dict(continente="Europa", moeda="RSD"),
    "Montenegro": dict(continente="Europa", moeda="EUR"),
    "Albânia": dict(continente="Europa", moeda="ALL"),
    "Bósnia e Herzegovina": dict(continente="Europa", moeda="BAM"),
    "Macedônia do Norte": dict(continente="Europa", moeda="MKD"),
    # --- Outros (aparecem no modo "explorar") ---
    "México": dict(continente="América do Norte e Caribe", entrada="online", vacina_fa="nao", moeda="MXN",
                   nota_entrada="Visto eletrônico pela internet desde fev/2026 (cerca de R$ 55). Quem tem visto americano válido não precisa."),
    "Estados Unidos": dict(continente="América do Norte e Caribe", entrada="visto", vacina_fa="nao", moeda="USD"),
    "Canadá": dict(continente="América do Norte e Caribe", entrada="visto", vacina_fa="nao", moeda="CAD",
                   nota_entrada="Quem tem visto americano válido ou teve visto canadense nos últimos 10 anos pode pedir só a eTA (online) para ir de avião. Confira no site oficial."),
    "Panamá": dict(continente="América do Norte e Caribe", vacina_fa="conferir", moeda="USD"),
    "Costa Rica": dict(continente="América do Norte e Caribe", vacina_fa="conferir", moeda="CRC"),
    "Cuba": dict(continente="América do Norte e Caribe", entrada="online", vacina_fa="exige", moeda="CUP",
                 nota_entrada="Pede cartão de turista (comprado com a companhia aérea ou agência)."),
    "Aruba": dict(continente="América do Norte e Caribe", vacina_fa="exige", moeda="AWG"),
    "Curaçao": dict(continente="América do Norte e Caribe", vacina_fa="exige", moeda="ANG"),
    "República Dominicana": dict(continente="América do Norte e Caribe", vacina_fa="conferir", moeda="DOP"),
    "África do Sul": dict(continente="Outros", vacina_fa="exige", moeda="ZAR"),
    "Austrália": dict(continente="Outros", entrada="visto", vacina_fa="exige", moeda="AUD"),
    "China": dict(continente="Outros", entrada="conferir", vacina_fa="exige", moeda="CNY"),
    "Japão": dict(continente="Outros", moeda="JPY", nota_entrada="Sem visto para turismo curto desde 2023."),
    "Emirados Árabes Unidos": dict(continente="Outros", moeda="AED", vacina_fa="conferir"),
}

ETIAS_NOTA = ("ETIAS (autorização eletrônica da Europa, €20): ainda NÃO está valendo e não tem data oficial. "
              "Quando começar, será pedido pela internet antes da viagem.")

for _nome, _p in PAISES.items():
    _p.setdefault("documento", "passaporte")
    _p.setdefault("entrada", "livre")
    _p.setdefault("vacina_fa", "nao" if _p["continente"] == "Europa" else "conferir")
    if _p.get("schengen"):
        _p.setdefault("nota_entrada", "Sem visto (até 90 dias). " + ETIAS_NOTA)

# Destinos monitorados. grupo = categoria que aparece no app.
# termos = palavras usadas para reconhecer o destino no texto das promoções.
def _d(iata, nome, local, pais, grupo, termos=(), uf=None, sem_nome=False):
    """sem_nome=True quando o nome é palavra comum (Natal, Bonito, Lima...) e daria falso positivo."""
    base = set() if sem_nome else {nome.lower()}
    return dict(iata=iata, nome=nome, local=local, pais=pais, grupo=grupo, uf=uf,
                termos=sorted(base | {t.lower() for t in termos}))

DESTINOS = [
    # Norte
    _d("BEL", "Belém", "Belém (PA)", "Brasil", "Norte", ["belem"], "PA"),
    _d("MAO", "Manaus", "Manaus (AM)", "Brasil", "Norte", [], "AM"),
    _d("STM", "Santarém", "Santarém e Alter do Chão (PA)", "Brasil", "Norte", ["alter do chão", "santarem"], "PA"),
    _d("PMW", "Palmas", "Palmas e Jalapão (TO)", "Brasil", "Norte", ["jalapão", "palmas (to)", "para palmas", "em palmas"], "TO", sem_nome=True),
    _d("MCP", "Macapá", "Macapá (AP)", "Brasil", "Norte", [], "AP"),
    _d("BVB", "Boa Vista", "Boa Vista (RR)", "Brasil", "Norte", [], "RR"),
    _d("PVH", "Porto Velho", "Porto Velho (RO)", "Brasil", "Norte", [], "RO"),
    _d("RBR", "Rio Branco", "Rio Branco (AC)", "Brasil", "Norte", [], "AC"),
    # Nordeste
    _d("SLZ", "São Luís", "São Luís e Lençóis Maranhenses (MA)", "Brasil", "Nordeste", ["lençóis maranhenses", "maranhão", "barreirinhas", "sao luis"], "MA"),
    _d("JJD", "Jericoacoara", "Jericoacoara (CE)", "Brasil", "Nordeste", ["jeri", "jericoacoara"], "CE"),
    _d("FOR", "Fortaleza", "Fortaleza (CE)", "Brasil", "Nordeste", [], "CE"),
    _d("SSA", "Salvador", "Salvador (BA)", "Brasil", "Nordeste", [], "BA"),
    _d("BPS", "Porto Seguro", "Porto Seguro e Trancoso (BA)", "Brasil", "Nordeste", ["trancoso", "arraial d'ajuda"], "BA"),
    _d("IOS", "Ilhéus", "Ilhéus e Itacaré (BA)", "Brasil", "Nordeste", ["itacaré", "ilheus"], "BA"),
    _d("REC", "Recife", "Recife e Porto de Galinhas (PE)", "Brasil", "Nordeste", ["porto de galinhas"], "PE"),
    _d("FEN", "Fernando de Noronha", "Fernando de Noronha (PE)", "Brasil", "Nordeste", ["noronha"], "PE"),
    _d("NAT", "Natal", "Natal e Pipa (RN)", "Brasil", "Nordeste", ["praia da pipa", "natal (rn)", "natal/rn", "para natal", "em natal", "de natal e"], "RN", sem_nome=True),
    _d("JPA", "João Pessoa", "João Pessoa (PB)", "Brasil", "Nordeste", ["joao pessoa"], "PB"),
    _d("MCZ", "Maceió", "Maceió e Maragogi (AL)", "Brasil", "Nordeste", ["maragogi", "maceio"], "AL"),
    _d("AJU", "Aracaju", "Aracaju (SE)", "Brasil", "Nordeste", [], "SE"),
    _d("THE", "Teresina", "Teresina (PI)", "Brasil", "Nordeste", [], "PI"),
    _d("PHB", "Parnaíba", "Parnaíba e Delta do Parnaíba (PI)", "Brasil", "Nordeste", ["delta do parnaíba"], "PI"),
    # Centro-Oeste
    _d("BSB", "Brasília", "Brasília e Chapada dos Veadeiros (DF/GO)", "Brasil", "Centro-Oeste", ["chapada dos veadeiros", "brasilia"], "DF"),
    _d("CGB", "Cuiabá", "Cuiabá, Chapada e Pantanal (MT)", "Brasil", "Centro-Oeste", ["chapada dos guimarães", "pantanal", "cuiaba"], "MT"),
    _d("CGR", "Campo Grande", "Campo Grande (MS)", "Brasil", "Centro-Oeste", [], "MS"),
    _d("BYO", "Bonito", "Bonito (MS)", "Brasil", "Centro-Oeste", ["bonito (ms)", "bonito/ms", "para bonito", "em bonito"], "MS", sem_nome=True),
    _d("GYN", "Goiânia", "Goiânia (GO)", "Brasil", "Centro-Oeste", ["goiania"], "GO"),
    # Sudeste
    _d("SAO", "São Paulo", "São Paulo (SP)", "Brasil", "Sudeste", ["guarulhos", "congonhas", "sao paulo"], "SP"),
    _d("RIO", "Rio de Janeiro", "Rio de Janeiro (RJ)", "Brasil", "Sudeste", ["galeão", "santos dumont"], "RJ"),
    _d("CNF", "Belo Horizonte", "Belo Horizonte (MG)", "Brasil", "Sudeste", ["confins"], "MG"),
    # Sul
    _d("NVT", "Navegantes", "Beto Carrero World e Balneário Camboriú (SC)", "Brasil", "Sul", ["beto carrero", "balneário camboriú"], "SC"),
    _d("FLN", "Florianópolis", "Florianópolis (SC)", "Brasil", "Sul", ["floripa", "florianopolis"], "SC"),
    _d("JOI", "Joinville", "Joinville (SC)", "Brasil", "Sul", [], "SC"),
    _d("POA", "Porto Alegre", "Porto Alegre (RS)", "Brasil", "Sul", [], "RS"),
    _d("CXJ", "Caxias do Sul", "Serra Gaúcha: Gramado e Canela (RS)", "Brasil", "Sul", ["gramado", "serra gaúcha", "bento gonçalves"], "RS"),
    _d("CWB", "Curitiba", "Curitiba (PR)", "Brasil", "Sul", [], "PR"),
    _d("IGU", "Foz do Iguaçu", "Foz do Iguaçu (PR)", "Brasil", "Sul", ["cataratas", "foz do iguacu"], "PR"),
    # América do Sul
    _d("BUE", "Buenos Aires", "Buenos Aires", "Argentina", "América do Sul", ["aeroparque", "ezeiza"]),
    _d("BRC", "Bariloche", "Bariloche", "Argentina", "América do Sul", []),
    _d("MDZ", "Mendoza", "Mendoza", "Argentina", "América do Sul", []),
    _d("USH", "Ushuaia", "Ushuaia", "Argentina", "América do Sul", []),
    _d("FTE", "El Calafate", "El Calafate", "Argentina", "América do Sul", []),
    _d("SCL", "Santiago", "Santiago", "Chile", "América do Sul", ["santiago do chile"]),
    _d("CJC", "Atacama", "Deserto do Atacama (Calama)", "Chile", "América do Sul", ["san pedro de atacama", "calama"]),
    _d("MVD", "Montevidéu", "Montevidéu", "Uruguai", "América do Sul", ["montevideo"]),
    _d("PDP", "Punta del Este", "Punta del Este", "Uruguai", "América do Sul", []),
    _d("ASU", "Assunção", "Assunção", "Paraguai", "América do Sul", ["asunción", "para assunção", "assunção (paraguai)"], sem_nome=True),
    _d("LIM", "Lima", "Lima", "Peru", "América do Sul", ["para lima", "em lima", "lima (peru)", "lima, no peru"], sem_nome=True),
    _d("CUZ", "Cusco", "Cusco e Machu Picchu", "Peru", "América do Sul", ["machu picchu", "cuzco"]),
    _d("BOG", "Bogotá", "Bogotá", "Colômbia", "América do Sul", []),
    _d("CTG", "Cartagena", "Cartagena", "Colômbia", "América do Sul", []),
    _d("ADZ", "San Andrés", "San Andrés", "Colômbia", "América do Sul", ["san andres"]),
    _d("UIO", "Quito", "Quito", "Equador", "América do Sul", []),
    _d("GPS", "Galápagos", "Ilhas Galápagos", "Equador", "América do Sul", ["galapagos"]),
    _d("VVI", "Santa Cruz de la Sierra", "Santa Cruz de la Sierra", "Bolívia", "América do Sul", []),
    _d("LPB", "La Paz", "La Paz e Uyuni", "Bolívia", "América do Sul", ["uyuni"]),
    # Europa
    _d("LIS", "Lisboa", "Lisboa", "Portugal", "Europa", ["lisbon"]),
    _d("OPO", "Porto", "Porto (Portugal)", "Portugal", "Europa", ["cidade do porto", "porto, em portugal", "porto (portugal)", "lisboa e porto", "porto e lisboa"], sem_nome=True),
    _d("FNC", "Madeira", "Ilha da Madeira (Funchal)", "Portugal", "Europa", ["funchal", "ilha da madeira"], sem_nome=True),
    _d("MAD", "Madri", "Madri", "Espanha", "Europa", ["madrid"]),
    _d("BCN", "Barcelona", "Barcelona", "Espanha", "Europa", []),
    _d("PAR", "Paris", "Paris", "França", "Europa", []),
    _d("NCE", "Nice", "Nice e Riviera Francesa", "França", "Europa", []),
    _d("ROM", "Roma", "Roma", "Itália", "Europa", ["rome"]),
    _d("MIL", "Milão", "Milão", "Itália", "Europa", ["milan"]),
    _d("VCE", "Veneza", "Veneza", "Itália", "Europa", []),
    _d("FLR", "Florença", "Florença", "Itália", "Europa", []),
    _d("BER", "Berlim", "Berlim", "Alemanha", "Europa", []),
    _d("FRA", "Frankfurt", "Frankfurt", "Alemanha", "Europa", []),
    _d("MUC", "Munique", "Munique", "Alemanha", "Europa", []),
    _d("AMS", "Amsterdã", "Amsterdã", "Países Baixos", "Europa", ["amsterdam", "holanda"]),
    _d("BRU", "Bruxelas", "Bruxelas", "Bélgica", "Europa", []),
    _d("LUX", "Luxemburgo", "Luxemburgo", "Luxemburgo", "Europa", []),
    _d("ZRH", "Zurique", "Zurique", "Suíça", "Europa", ["suíça"]),
    _d("VIE", "Viena", "Viena", "Áustria", "Europa", []),
    _d("PRG", "Praga", "Praga", "Tchéquia", "Europa", []),
    _d("BUD", "Budapeste", "Budapeste", "Hungria", "Europa", []),
    _d("WAW", "Varsóvia", "Varsóvia", "Polônia", "Europa", ["cracóvia"]),
    _d("BTS", "Bratislava", "Bratislava", "Eslováquia", "Europa", []),
    _d("LJU", "Liubliana", "Liubliana", "Eslovênia", "Europa", []),
    _d("ZAG", "Zagreb", "Zagreb e Dubrovnik", "Croácia", "Europa", ["dubrovnik", "split", "croácia"]),
    _d("ATH", "Atenas", "Atenas e ilhas gregas", "Grécia", "Europa", ["santorini", "mykonos", "grécia"]),
    _d("MLA", "Malta", "Malta", "Malta", "Europa", ["para malta", "ilha de malta", "em malta"], sem_nome=True),
    _d("CPH", "Copenhague", "Copenhague", "Dinamarca", "Europa", []),
    _d("STO", "Estocolmo", "Estocolmo", "Suécia", "Europa", []),
    _d("OSL", "Oslo", "Oslo", "Noruega", "Europa", ["noruega"]),
    _d("HEL", "Helsinque", "Helsinque", "Finlândia", "Europa", ["lapônia"]),
    _d("REK", "Reykjavík", "Reykjavík", "Islândia", "Europa", ["islândia"]),
    _d("TLL", "Tallinn", "Tallinn", "Estônia", "Europa", []),
    _d("RIX", "Riga", "Riga", "Letônia", "Europa", []),
    _d("VNO", "Vilnius", "Vilnius", "Lituânia", "Europa", []),
    _d("OTP", "Bucareste", "Bucareste", "Romênia", "Europa", []),
    _d("SOF", "Sófia", "Sófia", "Bulgária", "Europa", []),
    _d("LCA", "Chipre", "Chipre (Larnaca)", "Chipre", "Europa", ["larnaca"]),
    _d("DUB", "Dublin", "Dublin", "Irlanda", "Europa", ["irlanda"]),
    _d("LON", "Londres", "Londres", "Reino Unido", "Europa", ["london", "edimburgo"]),
    _d("IST", "Istambul", "Istambul", "Turquia", "Europa", ["capadócia"]),
    _d("BEG", "Belgrado", "Belgrado", "Sérvia", "Europa", []),
    _d("TGD", "Podgorica", "Montenegro", "Montenegro", "Europa", []),
    _d("TIA", "Tirana", "Tirana", "Albânia", "Europa", []),
    _d("SJJ", "Sarajevo", "Sarajevo", "Bósnia e Herzegovina", "Europa", []),
    _d("SKP", "Escópia", "Escópia", "Macedônia do Norte", "Europa", []),
]

GRUPOS = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul", "América do Sul", "Europa",
          "América do Norte e Caribe", "Outros"]

FAVORITOS_INICIAIS = ["SLZ", "JJD", "NVT", "SSA", "REC", "FOR", "NAT", "JPA", "MCZ", "AJU", "THE"]

# Aeroportos reconhecidos no modo "explorar" que equivalem a um destino da tabela.
AEROPORTO_PARA_DESTINO = {
    "GRU": "SAO", "CGH": "SAO", "VCP": "SAO", "GIG": "RIO", "SDU": "RIO",
    "EZE": "BUE", "AEP": "BUE", "CDG": "PAR", "ORY": "PAR", "FCO": "ROM", "CIA": "ROM",
    "MXP": "MIL", "LIN": "MIL", "LHR": "LON", "LGW": "LON", "STN": "LON", "ARN": "STO",
    "KEF": "REK", "SAW": "IST", "DBV": "ZAG", "SPU": "ZAG", "JTR": "ATH", "JMK": "ATH",
    "EDI": "LON", "KRK": "WAW",
}

PAIS_POR_IATA = {d["iata"]: d["pais"] for d in DESTINOS}


def pais_info(pais):
    return PAISES.get(pais) or dict(continente="Outros", documento="passaporte", entrada="conferir",
                                    vacina_fa="conferir", moeda=None)


def resumo_entrada(pais):
    """Texto curto para os avisos: documento, entrada e vacina."""
    p = pais_info(pais)
    partes = []
    if pais == "Brasil":
        return ""
    partes.append("🪪 Só RG" if p["documento"] == "RG" else "🛂 Passaporte")
    partes.append({"livre": "sem visto", "online": "autorização online", "visto": "⛔ precisa de visto",
                   "conferir": "⚠️ conferir regra"}[p["entrada"]])
    if p["vacina_fa"] == "exige":
        partes.append("💉 febre amarela obrigatória")
    elif p["vacina_fa"] in ("depende", "conferir"):
        partes.append("💉 conferir vacina")
    return " · ".join(partes)

GRUPO_POR_IATA = {d["iata"]: d["grupo"] for d in DESTINOS}
DESTINO_POR_IATA = {d["iata"]: d for d in DESTINOS}

# Códigos de cidade com mais de um aeroporto (o coletor de voos recebe a lista)
AEROPORTOS_DA_CIDADE = {
    "SAO": "GRU,CGH,VCP", "RIO": "GIG,SDU", "BUE": "EZE,AEP", "PAR": "CDG,ORY", "ROM": "FCO",
    "MIL": "MXP,LIN", "LON": "LHR,LGW", "STO": "ARN", "REK": "KEF",
}
