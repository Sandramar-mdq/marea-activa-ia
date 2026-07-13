import httpx

from src.config import GEMINI_API_KEY

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)

SISTEMA = (
    "Sos Ginga, una anfitriona marplatense calida, empatica e inclusiva. "
    "Hablas con entusiasmo genuino, como alguien que ama su ciudad y quiere "
    "compartirla con personas de todas las edades. Sos respetuosa, cercana sin ser informal. "
    "Usas un lenguaje claro, amable y optimista, con referencias al mar, la costa y los atardeceres. "
    "REGLA DE ORO: Tu aplicacion Marea Activa es EXCLUSIVAMENTE para deportes, paseos y actividades recreativas "
    "en Mar del Plata. Si el usuario te pide cosas fuera de este ambito (como comida/milanesas, alojamiento, "
    "politica, etc.), debes explicarle con calidez que tu especialidad son las actividades deportivas y recreativas, "
    "e invitarlo a consultar sobre eso, IGNORANDO los items de pesca o surf que el sistema te haya enviado por error "
    "si no tienen relacion con lo que el pide. "
    "REGLA HORARIA: Si el usuario pide actividades al aire libre (deportes de aventura, parapente, surf, trekking, etc.) "
    "y la hora actual es nocturna (despues de las 18:00 o antes de las 08:00), debes advertirle que no es posible "
    "por falta de luz solar y sugerirle actividades techadas o alternativas nocturnas. "
    "Respondes SIEMPRE en espanol argentino, con caliges y energia."
)


def _armar_prompt(
    mensaje: str,
    items: list[dict],
    weather: dict | None,
    advertencias: list[str],
) -> str:
    from datetime import datetime
    ahora = datetime.now().strftime("%H:%M")
    partes = [f"El usuario dice: '{mensaje}'.\n"]
    partes.append(f"Hora actual: {ahora}.\n")
    if weather:
        partes.append(
            f"Clima actual en MDP: {weather['temperature']}C, "
            f"{weather['description']}, viento {weather['wind_speed_kmh']} km/h.\n"
        )
    if advertencias:
        for w in advertencias:
            partes.append(f"Advertencia: {w}\n")
    if items:
        partes.append("Actividades recomendadas:\n")
        for i, act in enumerate(items[:15], 1):
            linea = f"  {i}. {act['descripcion']} | {act['categoria']} | Zona: {act['zona']} | Intensidad: {act['intensidad']}"
            if act.get("edad"):
                linea += f" | Edad: {act['edad']}"
            if act.get("sentimiento"):
                linea += f" | Sentimiento: {act['sentimiento']['label']}"
            if act.get("advertencia"):
                linea += f" | CUIDADO: {act['advertencia']}"
            partes.append(linea)
    else:
        partes.append("No se encontraron actividades para esa busqueda.\n")
    
    partes.append(
        "\nInstruccion final para Ginga: Evalua con atencion el mensaje del usuario. "
        "Si notas que te pide algo ajeno a las actividades deportivas o paseos (como comida), "
        "aplica la REGLA DE ORO de tu sistema. Si el mensaje es pertinente, respondele con "
        "entusiasmo recomendandole la lista de actividades adjunta. Si la lista esta vacia, "
        "sugerile que pregunte por otro deporte o zona de la ciudad."
    )
    return "\n".join(partes)


async def generar_respuesta(
    mensaje: str,
    items: list[dict],
    weather: dict | None = None,
    advertencias: list[str] | None = None,
) -> str:
    if not GEMINI_API_KEY:
        return _respuesta_fallback(mensaje, items, weather, advertencias or [])

    prompt = _armar_prompt(mensaje, items, weather, advertencias or [])
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json={
                "system_instruction": {"parts": [{"text": SISTEMA}]},
                "contents": [{"parts": [{"text": prompt}]}],
            },
            timeout=30,
        )
    if resp.status_code != 200:
        return _respuesta_fallback(mensaje, items, weather, advertencias or [])
    data = resp.json()
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return text.replace("\\n", "\n")
    except (KeyError, IndexError):
        return _respuesta_fallback(mensaje, items, weather, advertencias or [])


def _respuesta_fallback(
    mensaje: str,
    items: list[dict],
    weather: dict | None,
    advertencias: list[str],
) -> str:
    # Si el usuario pide comida y cae el fallback, no le mostramos botes de pesca
    if "milan" in mensaje.lower() or "comer" in mensaje.lower():
        return (
            "¡Hola! Se me complico la conexion, pero te cuento que por ahora solo te puedo "
            "ayudar a buscar actividades recreativas y deportes en la feliz. ¿Te gustaria "
            "consultar por surf, kayak o paseos?"
        )
    if not items:
        return (
            "No encontre actividades para esa busqueda. "
            "Proba preguntando por un deporte (surf, pesca, trekking...) "
            "o por una zona (Playa Grande, Puerto...)"
        )
    lines = [
        "Estas son mis recomendaciones:\n"
    ]
    if weather:
        lines.append(
            f"El clima en Mar del Plata: {weather['description']}, "
            f"{weather['temperature']}C con viento de {weather['wind_speed_kmh']} km/h.\n"
        )
    for w in advertencias:
        lines.append(f"{w}\n")
    for act in items[:15]:
        line = f"  - {act['descripcion']}"
        if act.get("sentimiento", {}).get("label") == "positivo":
            line += " (muy bien valorada)"
        lines.append(line)
    lines.append(
        "\nEspero que te sirvan. Decime si queres conocer mas opciones!"
    )
    return "\n".join(lines)
