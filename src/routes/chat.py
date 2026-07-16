from fastapi import APIRouter

from src.models.requests import ChatRequest, ChatResponse, ActivityItem, WeatherInfo, SentimentInfo
from src.services.orchestrator import recommend
from src.services.ginga_agent import generar_respuesta

router = APIRouter()


def _to_weather_info(w) -> WeatherInfo | None:
    if w is None:
        return None
    return WeatherInfo(
        temperature=w.temperature,
        condition=w.condition,
        description=w.description,
        wind_speed_kmh=w.wind_speed_kmh,
    )


def _to_activity_items(items: list[dict]) -> list[ActivityItem]:
    import pandas as pd
    result = []
    for item in items:
        sent = None
        if item.get("sentimiento"):
            sent = SentimentInfo(
                label=item["sentimiento"]["label"],
                score=item["sentimiento"]["score"],
            )
            
        # Limpiamos los NaN de Pandas convirtiéndolos en "" o strings válidos
        zona_val = item.get("zona", "")
        if pd.isna(zona_val) or not isinstance(zona_val, str):
            zona_val = ""
            
        cat_val = item.get("categoria", "")
        if pd.isna(cat_val) or not isinstance(cat_val, str):
            cat_val = ""

        result.append(
            ActivityItem(
                descripcion=item["descripcion"],
                categoria=cat_val,
                zona=zona_val,
                intensidad=item["intensidad"],
                edad=item.get("edad", "Todas las edades"),
                sentimiento=sent,
                advertence=item.get("advertencia"),
            )
        )
    return result


@router.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        data = await recommend(req.message)
        items = data.get("items", [])
        weather = data.get("weather")
        advertencias = data.get("advertencias", [])
        time_warning = data.get("time_warning")
        texto = data.get("response") or await generar_respuesta(
            mensaje=req.message,
            items=items,
            weather=_weather_dict(weather) if weather else None,
            advertencias=advertencias,
            time_warning=time_warning,
            intent=data.get("intent"),
        )
        return ChatResponse(
            response=texto,
            items=_to_activity_items(items),
            weather=_to_weather_info(weather),
            advertencias=advertencias,
        )
    except Exception as e:
        return ChatResponse(
            response="Disculpa, tuve un problema al procesar tu consulta. "
                    "Probá de nuevo o preguntame por otra actividad o zona de Mar del Plata.",
            items=[],
            weather=None,
            advertencias=[],
        )


def _weather_dict(w) -> dict:
    return {
        "temperature": w.temperature,
        "description": w.description,
        "wind_speed_kmh": w.wind_speed_kmh,
    }
