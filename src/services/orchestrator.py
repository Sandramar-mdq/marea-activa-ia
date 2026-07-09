import unicodedata
import re

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

}

ZONAS_KEYWORDS = {
    "playa grande", "puerto", "centro", "varese", "punta mogotes",
    "la perla", "playas del centro", "playas del sur", "playas alfar",
    "punta cantera", "camet", "chapadmalal", "sierra de los padres",
    "serrana", "batan", "sur", "microcentro", "perla norte",
    "los troncos", "plaza rocha", "caballito",
}

NAUTICAS_KEYWORDS = {
    "pesca", "kayak", "surf", "navegacion", "vela", "remo",
    "canoa", "paseo", "maritimo", "buceo", "stand up paddle",
    "sup", "wind", "kite", "pescar", "surfear", "navegar", 
    "remar", "pasear", "bucear", "planeador",
}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return text.lower().strip()


def _detect_intent(message: str) -> dict:
    msg = _normalize(message)
    for kw in ACTIVIDADES_KEYWORDS:
        if kw in msg:
            return {"tipo": "actividad", "keyword": kw}
    for kw in ZONAS_KEYWORDS:
        if kw in msg:
            return {"tipo": "zona", "keyword": kw}
    if any(p in msg for p in ["aventura", "intenso", "extremo", "fuerte"]):
        return {"tipo": "intensidad", "keyword": "Alta"}
    if any(p in msg for p in ["tranquilo", "relajado", "familia", "nino"]):
        return {"tipo": "intensidad", "keyword": "Baja"}
    return {"tipo": "general", "keyword": ""}


def _match_zone(df: pd.DataFrame, zona: str) -> pd.DataFrame:
    z = _normalize(zona)
    mask = df["Zona"].fillna("").apply(lambda v: z in _normalize(v))
    return df[mask].copy()


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
    result = {"intent": intent, "weather": weather, "_lluvia": False, "_viento_fuerte": False}
    warnings = _apply_weather_warnings(result, weather)
    result["advertencias"] = warnings

    if intent["tipo"] == "actividad":
        kw = intent["keyword"]
        
        # Mapeamos sinónimos para que busque varias palabras juntas en el CSV
        search_terms = [kw]
        
        # Grupo Aéreo: Si detecta cualquiera de estos, busca todas las variantes aéreas en el CSV
        if kw in ["vuelo", "vuelos", "volar", "parapente", "parapentes", "planeador", "planeadores", "aeroclub"]:
            search_terms = ["vuelo", "vuelos", "volar", "parapente", "parapentes", "planeador", "planeadores", "aeroclub"]
            
        # Grupo Surf (Opcional, por si te pasa lo mismo con las olas)
        elif kw in ["surf", "surfing", "surfear"]:
            search_terms = ["surf", "surfing", "surfear", "school", "club"]

        # Filtramos la descripción si contiene CUALQUIERA de los términos de la lista
        mask = merged["descripcion"].fillna("").apply(
            lambda v: any(term in _normalize(v) for term in search_terms)
        )
        filtered = merged[mask].copy()
    elif intent["tipo"] == "zona":
        filtered = _match_zone(merged, intent["keyword"])
    else:
        filtered = merged.copy()

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

        item = {
            "descripcion": row["descripcion"],
            "categoria": row.get("Categoria", ""),
            "zona": row.get("Zona", ""),
            "intensidad": classify_intensidad(row["descripcion"], row.get("Categoria", "")),
            "edad": classify_edad(row["descripcion"], row.get("Categoria", "")),
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
