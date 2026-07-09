import re

POSITIVAS = {
    "excelente", "bueno", "buenisimo", "genial", "increible", "recomendable",
    "espectacular", "hermoso", "fantastico", "maravilloso", "perfecto",
    "amable", "profesional", "divertido", "comodo", "seguro", "tranquilo",
    "lindo", "agradable", "unico", "bonito", "simptico", "calido", "atento",
    "paciente", "experto", "impecable", "crack", "genio", "amoroso",
    "predispuesto", "puntual", "completo", "variado", "accesible",
    "gratis", "libre", "encant", "feliz", "alegre", "disponible",
}

NEGATIVAS = {
    "malo", "pesimo", "terrible", "desastre", "horrible", "feo", "sucio",
    "peligroso", "caro", "aburrido", "incomodo", "lento", "descortes",
    "grosero", "antipatico", "decepcion", "queja", "falta", "peor",
    "roto", "oxidado", "pinchado", "cerrado", "suspendido",
    "maleducado", "soberbio", "irresponsable", "impuntual",
    "desagradable", "basura", "estafa", "robo",
}

NEGACION = {"no", "nunca", "jamas", "tampoco", "sin", "ni"}


def _normalize(text: str) -> str:
    import unicodedata
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return text.lower().strip()


def _score_from_stars(estrellas: str) -> tuple[str, float]:
    try:
        s = float(estrellas)
    except (ValueError, TypeError):
        return "neutral", 0.5
    if s >= 4:
        return "positivo", min(s / 5, 1.0)
    if s == 3:
        return "neutral", 0.5
    return "negativo", max(1 - s / 5, 0.0)


def _extract_highlights(comentario: str) -> dict:
    tokens = _normalize(comentario).split()
    positivas_encontradas = []
    negativas_encontradas = []
    negado = False
    for token in tokens:
        token = re.sub(r"[^a-z]", "", token)
        if not token:
            continue
        if token in NEGACION:
            negado = True
            continue
        if token in POSITIVAS:
            positivas_encontradas.append(token)
        elif token in NEGATIVAS:
            negativas_encontradas.append(token)
    return {
        "positivas": positivas_encontradas,
        "negativas": negativas_encontradas,
    }


def analyze_sentiment(estrellas: str, comentario: str = "") -> dict:
    label, score = _score_from_stars(estrellas)
    highlights = _extract_highlights(comentario) if comentario else {}
    result = {
        "label": label,
        "score": round(score, 2),
    }
    if highlights:
        result["keywords"] = highlights
    return result
