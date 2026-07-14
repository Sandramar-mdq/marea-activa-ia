INTENSIDAD_ALTA = {
    "surf", "kayak", "parapente", "buceo", "pesca", "aventura",
    "rafting", "escalada", "tandem", "vuelo", "planeador",
    "cuatriciclo", "karting", "windsurf", "kitesurf", "remo",
    "extremo", "quad",
}

INTENSIDAD_MEDIA = {
    "trekking", "running", "bicicleta", "bici", "bicitando",
    "cabalgata", "footgolf", "crossfit", "funcional",
    "marcha nordica", "snorkel", "excursion",
}

INTENSIDAD_BAJA = {
    "caminata", "paseo", "recreacion", "feria", "mercado",
    "museo", "mirador", "bowling", "parque", "acuario",
    "casino", "bingo", "religioso", "ecologica", "avistaje",
    "guiado", "cultural", "artesanal",
}

CATEGORIA_ALTA = {"deportes de aventura", "pesca recreativa"}
CATEGORIA_MEDIA = {
    "alquiler de bicicletas y motos", "caminatas y actividades fisicas",
    "excursiones maritimas", "paseos aereos", "cabalgatas", "caminatas", 
    "senderismo",
}
CATEGORIA_BAJA = {
    "casinos y bingos", "recreacion para ninos", "ferias y mercados",
    "parques tematicos", "bowlings", "circuitos guiados",
    "miradores", "museos y centros culturales", "reservas ecologicas",
    "turismo religioso", "guias de turismo",
    "establecimientos para pasar el dia",
}

EDAD_INFANTIL = {
    "recreacion para ninos", "infantil", "ninos", "kids",
    "play land", "saltos", "trampoline", "chicos", "nenes", 
}
EDAD_ADULTOS = {
    "casino", "bingo", "vuelo", "buceo", "parapente",
    "cerveceria", "destileria", "planeador", "volar", 
    "bucear",
}


def _normalize(text: str) -> str:
    import unicodedata
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return text.lower().strip()


def classify_intensidad(descripcion: str, categoria: str = "") -> str:
    desc = _normalize(descripcion)
    cat = _normalize(categoria)
    for kw in INTENSIDAD_ALTA:
        if kw in desc:
            return "Alta"
    for kw in INTENSIDAD_MEDIA:
        if kw in desc:
            return "Media"
    for kw in INTENSIDAD_BAJA:
        if kw in desc:
            return "Baja"
    for kw in CATEGORIA_ALTA:
        if kw in cat:
            return "Alta"
    for kw in CATEGORIA_MEDIA:
        if kw in cat:
            return "Media"
    for kw in CATEGORIA_BAJA:
        if kw in cat:
            return "Baja"
    return "Media"


def classify_edad(descripcion: str, categoria: str = "") -> str:
    desc = _normalize(descripcion)
    cat = _normalize(categoria)
    for kw in EDAD_INFANTIL:
        if kw in desc:
            return "Infantil"
    for kw in EDAD_ADULTOS:
        if kw in desc:
            return "Adultos"
    for kw in EDAD_INFANTIL:
        if kw in cat:
            return "Infantil"
    for kw in EDAD_ADULTOS:
        if kw in cat:
            return "Adultos"
    return "Todas las edades"
