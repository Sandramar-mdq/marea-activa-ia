import unicodedata
import re
from datetime import datetime

import pandas as pd

from src.services.data_loader import load_merged_data, load_all_dataframes
from src.services.classifier import classify_intensidad, classify_edad
from src.services.sentiment import analyze_sentiment
from src.services.weather import fetch_weather, WeatherData

ACTIVIDADES_KEYWORDS = {
    "surf", "surfing", "surfear", "surferos", "surferas", "surfero", 
    "surfera", "pesca", "pescador", "pescadores", "pescar", "kayak", 
    "kayakismo", "kayaks", "kayakista", "kayakistas", "vuelos con planeadores",
    "parapente", "parapentes", "buceo", "bucear", "buceador", "buceadores", 
    "buceadoras", "trekking","running", "bicicleta", "bici", "ciclismo", "senderiemo",
    "ciclista", "ciclistas", "cabalgata", "cabalgar", "equitacion", "footgolf",
    "stand up paddle", "sup", "navegacion", "navegar", "paseo", "paseos", "pasear", 
    "caminata", "caminatas", "caminar", "bowling", "boliche", "vuelo", 
    "vuelos", "volar", "acuario", "parque", "casino", "bingo", "juegos", "jugar", 
    "museo", "feria", "mercado", "aventura", "remo", "remar", "remar", "remos", 
    "vuelo de bautismo", "vuelos de bautismo", "volar en parapente", "volar con parapente", 
    "vuelo con planeador","volar en planeador", "volar en planeadores", "planeadores","planeador",
    "ninos", "nino","ninas", "nina", "nene", "nenes", "chicos", "chica", "chico", "chica", "abuelo",
    "abuela", "abuelos", "adulto mayor", "adultos mayores", "jubilados", "jubiladas", "jubilado", "jubilada",

}

ZONAS_KEYWORDS = {
    "playa grande", "puerto", "centro", "varese", "punta mogotes",
    "la perla", "playas del centro", "playas del sur", "playas alfar",
    "punta cantera", "camet", "chapadmalal", "sierra de los padres",
    "serrana", "batan", "microcentro", "perla norte",
    "los troncos", "plaza rocha", "caballito",
    "zona norte", "norte", "zona sur", "sur", "zona este", "este",
    "zona oeste", "oeste", "costa", "costero", "costera",
}

NAUTICAS_KEYWORDS = {
    "pesca", "kayak", "surf", "navegacion", "vela", "remo",
    "canoa", "paseo", "maritimo", "buceo", "stand up paddle",
    "sup", "wind", "kite", "pescar", "surfear", "navegar", 
    "remar", "pasear", "bucear", "planeador",
}

OUTDOOR_KEYWORDS = {
    "parapente", "vuelo", "volar", "planeador", "surf", "kayak", "buceo",
    "trekking", "escalada", "cabalgata", "remo", "navegacion", "navegar",
    "aventura", "rafting", "kitesurf", "windsurf", "excursion", "pesca",
    "caminata", "bicicleta", "bici", "running", "karting", "cuatriciclo",
}

INDOOR_KEYWORDS = {
    "museo", "casino", "bingo", "bowling", "acuario", "feria",
    "mercado", "teatro", "cine", "religioso", "cultural",
    "artesanal", "recreacion para ninos",
}

PLAYA_KEYWORDS = {
    "playa", "playas", "costa", "costero", "costera",
    "maritimo", "maritima", "acuatico", "acuatica", "acuaticas",
    "nautico", "nautica", "nauticas", "orilla", "arena", "olas",
}

FAMILIA_KEYWORDS = {
    "abuelo", "abuela", "abuelos", "abuelas", "adulto mayor", "adultos mayores",
    "jubilado", "jubilada", "jubilados", "jubiladas", "nino", "nina", "ninos",
    "ninas", "nene", "nenes", "chico", "chica", "chicos", "chicas", "familia",
    "familias", "trankilo", "tranquilo", "tranquila", "relajado", "relajada",
}

CATEGORIAS_PLAYA_PERMITIDAS = {
    "deportes de aventura", "excursiones maritimas",
    "alquiler de bicicletas y motos", "circuitos guiados",
    "pesca recreativa", "paseos aereos",
}

CATEGORIAS_PLAYA_EXCLUIR = {
    "cultural", "religioso", "museos", "reservas ecologicas",
    "ferias y mercados", "bingo", "casinos",
}

CATEGORIAS_EXCLUIR_FAMILIA = {
    "turismo religioso",
}


def _es_categoria_playa_valida(cat_norm: str) -> bool:
    """Inclusivo: solo permite categorías que matcheen las permitidas."""
    if cat_norm in CATEGORIAS_PLAYA_PERMITIDAS:
        return True
    for excl in CATEGORIAS_PLAYA_EXCLUIR:
        if excl in cat_norm:
            return False
    return False

PLAYA_ZONAS_COSTERAS = {
    "playa grande", "playas del centro", "playas alfar",
    "la perla", "punta mogotes", "camet", "chapadmalal",
    "varese", "sur",
}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return text.lower().strip()


def _kw_in_text(kw: str, text: str) -> bool:
    if " " in kw:
        return kw in text
    return bool(re.search(r'\b' + re.escape(kw) + r'\b', text))


def _detect_intent(message: str) -> dict:
    msg = _normalize(message)
    result = {
        "tipo": "general",
        "keyword": "",
        "actividad": None,
        "zona": None,
    }

    for kw in ZONAS_KEYWORDS:
        if _kw_in_text(kw, msg):
            result["zona"] = kw
            break

    if any(_kw_in_text(kw, msg) for kw in PLAYA_KEYWORDS):
        result["tipo"] = "playa"
        result["actividad"] = "playa"
    elif any(_kw_in_text(kw, msg) for kw in FAMILIA_KEYWORDS):
        result["tipo"] = "familia"
        result["actividad"] = "familia"
    else:
        for kw in ACTIVIDADES_KEYWORDS:
            if _kw_in_text(kw, msg):
                result["tipo"] = "actividad"
                result["actividad"] = kw
                break

    if result["tipo"] == "general" and result["zona"]:
        result["tipo"] = "zona"

    if result["tipo"] == "general" and any(_kw_in_text(p, msg) for p in ["aventura", "intenso", "extremo", "fuerte"]):
        result["tipo"] = "intensidad"
        result["keyword"] = "Alta"

    return result


def _match_zone(df: pd.DataFrame, zona: str) -> pd.DataFrame:
    z = _normalize(zona)
    mask = df["Zona"].fillna("").apply(lambda v: z in _normalize(v))
    return df[mask].copy()


def _search_columns(df: pd.DataFrame, terms: list[str]) -> pd.DataFrame:
    def _row_matches(row):
        textos = [
            str(row.get("descripcion", "")),
            str(row.get("observacion", "")),
            str(row.get("Categoria", "")),
        ]
        combined = " ".join(textos)
        normalized = _normalize(combined)
        return any(term in normalized for term in terms)

    mask = df.apply(_row_matches, axis=1)
    return df[mask].copy()


def _excluir_categorias_irrelevantes(df: pd.DataFrame, intent: dict) -> pd.DataFrame:
    if intent["tipo"] == "playa":
        mask = df["Categoria"].fillna("").apply(
            lambda v: _es_categoria_playa_valida(_normalize(v))
        )
        return df[mask].copy()
    if intent["tipo"] == "familia":
        mask = ~df["Categoria"].fillna("").apply(
            lambda v: _normalize(v) in CATEGORIAS_EXCLUIR_FAMILIA
        )
        return df[mask].copy()
    return df


def _priorizar_por_relevancia(df: pd.DataFrame, intent: dict) -> pd.DataFrame:
    if intent["tipo"] != "playa" or df.empty:
        return df

    def _score(row):
        s = 0
        cat_raw = row.get("Categoria", "")
        zona_raw = row.get("Zona", "")
        cat = _normalize(str(cat_raw) if pd.notna(cat_raw) else "")
        zona = _normalize(str(zona_raw) if pd.notna(zona_raw) else "")
        if cat in CATEGORIAS_PLAYA_PERMITIDAS:
            s += 2
        if zona in PLAYA_ZONAS_COSTERAS:
            s += 1
        return s

    df["_score"] = df.apply(_score, axis=1)
    df = df.sort_values("_score", ascending=False).drop(columns=["_score"])
    return df


def _check_time_restriction(message: str, intent: dict) -> str | None:
    hora = datetime.now().hour
    if hora < 8 or hora >= 18:
        if intent["tipo"] == "actividad" and intent.get("actividad"):
            act = _normalize(intent["actividad"])
            if act in INDOOR_KEYWORDS:
                return None
        if intent["tipo"] == "playa":
            return None
        ahora = datetime.now().strftime("%H:%M")
        if hora >= 18:
            return (
                f"Hola, son las {ahora}. "
                "Ten en cuenta que a esta hora muchas actividades al aire libre "
                "no estan disponibles por falta de luz solar. "
                "Aqui tenes algunas opciones para considerar:"
            )
        else:
            return (
                f"Hola, son las {ahora} (madrugada). "
                "A esta hora no hay luz solar para actividades al aire libre. "
                "Aqui tenes algunas opciones para considerar:"
            )
    return None


def _apply_weather_warnings(result: dict, weather: WeatherData | None) -> list[str]:
    warnings = []
    if weather is None:
        return warnings
    if weather.condition in ("Rain", "Thunderstorm", "Drizzle", "Squall"):
        warnings.append("Lluvia activa: algunas actividades al aire libre pueden verse afectadas.")
        result["_lluvia"] = True
    if weather.wind_speed_kmh > 25:
        warnings.append(f"Viento fuerte ({weather.wind_speed_kmh} km/h): precaucion en actividades nauticas.")
        result["_viento_fuerte"] = True
    return warnings


def _build_advertencia(item: dict, weather: WeatherData | None) -> str | None:
    if weather is None:
        return None
    if item.get("_lluvia") and _normalize(item["categoria"]) not in (
        "casinos y bingos", "museos y centros culturales", "bowlings",
    ):
        return "Actividad al aire libre - verificar condiciones climaticas"
    if item.get("_viento_fuerte"):
        desc = _normalize(item["descripcion"])
        for kw in NAUTICAS_KEYWORDS:
            if kw in desc:
                return f"Viento fuerte ({weather.wind_speed_kmh} km/h) - precaucion"
    return None


async def recommend(message: str) -> dict:
    merged, recreacion, opiniones = load_merged_data()
    weather = await fetch_weather()

    intent = _detect_intent(message)
    time_warning = _check_time_restriction(message, intent)
    if time_warning:
        return {
            "items": [],
            "weather": None,
            "advertencias": [],
            "intent": intent,
            "response": "",
            "time_warning": time_warning,
        }
    result = {"intent": intent, "weather": weather, "_lluvia": False, "_viento_fuerte": False}
    warnings = _apply_weather_warnings(result, weather)

    result["advertencias"] = warnings

    filtered = merged.copy()

    if intent["zona"]:
        filtered = _match_zone(filtered, intent["zona"])

    if intent["tipo"] == "playa":
        search_terms = [
            "playa", "costa", "costero", "costera", "mar", "maritimo", "maritima",
            "olas", "arena", "surf", "kayak", "navegacion", "navegar", "paseo",
            "excursion", "nautico", "nautica", "acuatico", "acuatica",
            "stand up paddle", "sup", "buceo", "vela", "remo",
        ]
        filtered = _search_columns(filtered, search_terms)
        filtered = _excluir_categorias_irrelevantes(filtered, intent)
        filtered = _priorizar_por_relevancia(filtered, intent)

    elif intent["tipo"] == "familia":
        search_terms = [
            "familia", "familias", "nino", "nina", "ninos", "ninas", "chicos",
            "chicas", "abuelo", "abuela", "abuelos", "adulto mayor",
            "adultos mayores", "jubilado", "jubilada", "tranquilo", "tranquila",
            "paseo", "caminata", "guiado", "recreacion", "infantil",
        ]
        filtered = _search_columns(filtered, search_terms)
        filtered = _excluir_categorias_irrelevantes(filtered, intent)

    elif intent["tipo"] == "actividad":
        kw = intent["actividad"]
        search_terms = [kw]

        if kw in ["vuelo", "vuelos", "volar", "parapente", "parapentes", "planeador", "planeadores", "aeroclub"]:
            search_terms = ["vuelo", "vuelos", "volar", "parapente", "parapentes", "planeador", "planeadores", "aeroclub"]
        elif kw in ["surf", "surfing", "surfear"]:
            search_terms = ["surf", "surfing", "surfear"]

        filtered = _search_columns(filtered, search_terms)

    if filtered.empty:
        result["items"] = []
        return result

    seen = set()
    items = []
    for _, row in filtered.iterrows():
        key = row.get("cod_lugar", row.get("descripcion", ""))
        if key in seen:
            continue
        seen.add(key)

        zona_val = row.get("Zona", "")
        if pd.isna(zona_val):
            zona_val = ""
        cat_val = row.get("Categoria", "")
        if pd.isna(cat_val):
            cat_val = ""

        item = {
            "descripcion": row["descripcion"],
            "categoria": cat_val,
            "zona": zona_val,
            "intensidad": classify_intensidad(row["descripcion"], cat_val),
            "edad": classify_edad(row["descripcion"], cat_val),
        }

        if pd.notna(row.get("estrellas")):
            sent = analyze_sentiment(row["estrellas"], row.get("comentario", ""))
            item["sentimiento"] = sent

        warning = _build_advertencia(item, weather)
        if warning:
            item["advertencia"] = warning

        items.append(item)

    result["items"] = items
    return result
