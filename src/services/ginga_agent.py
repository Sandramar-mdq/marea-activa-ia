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
    "REGLA TEMPORAL: Si detectas la ETIQUETA TEMPORAL: futuro en el prompt, tu respuesta DEBE comenzar "
    "con una frase personalizada que incluya el TERMINO TEMPORAL ORIGINAL que el usuario uso. "
    "Por ejemplo, si el usuario dijo 'manana', empezá con: 'Que buena idea planear para manana!'. "
    "Si dijo 'el fin de semana', empezá con: 'Que buena idea planear para el fin de semana!'. "
    "Luego de esa frase, aclará que como asistente digital no tenés acceso a la agenda exacta de apertura "
    "de cada lugar para fechas futuras, pero que le recomiendás estos lugares que suelen tener gran "
    "disponibilidad de actividades deportivas. Sugirile llamar o consultar sus redes sociales antes de ir. "
    "Luego lista las actividades recomendadas. No inventes horarios ni disponibilidad. "
    "Esta regla tiene PRIORIDAD sobre cualquier otra instruccion. "
    "REGLA DE ORO: Tu aplicacion Marea Activa es EXCLUSIVAMENTE para actividades deportivas y recreativas "
    "al aire libre en Mar del Plata. Si el usuario te pide cosas fuera de este ambito (como museos, "
    "cervecerias, gastronomia, alojamiento, politica, etc.), el sistema ya habra detectado esto y te "
    "enviara el mensaje: 'Solo estoy capacitada para recomendarte actividades deportivas y recreativas "
    "al aire libre'. Debes incluir ese mensaje exacto en tu respuesta, con calidez pero sin agregar "
    "informacion adicional ni inventar actividades. "
    "REGLA HORARIA: Si el sistema te indica que es de noche o madrugada, DEBES incluir esa advertencia "
    "dentro de tu respuesta principal. Ademas, aprovecha para mencionar con calidez que Mar del Plata "
    "y la zona tienen una gran oferta en gastronomia, espectaculos y actividades culturales, pero aclarale "
    "al usuario que vos solo estas preparada para responder sobre actividades deportivas y al aire libre. "
    "Nunca generes un mensaje separado para la advertencia horaria; integrala en el mismo texto. "
    "Respondes SIEMPRE en espanol argentino, con calidez y energia."
)


def _armar_prompt(
    mensaje: str,
    items: list[dict],
    weather: dict | None,
    advertencias: list[str],
    time_warning: str | None = None,
    intent: dict | None = None,
    IGNORAR_REGLA_HORARIA: bool = False,
) -> str:
    from datetime import datetime
    ahora = datetime.now().strftime("%H:%M")
    partes = [f"El usuario dice: '{mensaje}'.\n"]
    partes.append(f"Hora actual: {ahora}.\n")

    if intent and intent.get("temporalidad") == "futuro":
        temporal_term = intent.get("temporal_term", "manana")
        partes.append(f"ETIQUETA TEMPORAL: futuro (el usuario consulta por una fecha futura). TERMINO TEMPORAL ORIGINAL: '{temporal_term}'.\n")

    if time_warning and not IGNORAR_REGLA_HORARIA:
        partes.append(
            f"ADVERTENCIA HORARIA: {time_warning}\n"
            "INSTRUCCION: Debes incluir esta advertencia de forma natural en tu respuesta, "
            "justo antes de listar las actividades. Ejemplo: 'Hola, son las [hora]. "
            "Tene en cuenta que a esta hora muchas actividades al aire libre no estan disponibles. "
            "Aqui tienes algunas opciones para considerar:'.\n"
        )
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
        for i, act in enumerate(items[:10], 1):
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
        "entusiasmo recomendandole la lista de actividades adjunta. "
        "Presenta las opciones encontradas (pueden ser 2, 3 o mas). "
        "Si la lista es corta, no rellenes con opciones inventadas. "
        "Cierra con una despedida amable, sin invitar a seguir buscando en la misma categoria. "
        "Si la lista esta vacia, sugerile que pregunte por otro deporte o zona de la ciudad."
    )

    if intent and intent.get("temporalidad") == "futuro":
        temporal_term = intent.get("temporal_term", "manana")
        partes.append(
            f"\nIMPORTANTE: ESTA CONSULTA TIENE ETIQUETA TEMPORAL: futuro. "
            f"EL USUARIO USO EL TERMINO '{temporal_term}'. "
            "TU PRIORIDAD ABSOLUTA ES RESPONDER CON LA FRASE: "
            f"'Que buena idea planear para {temporal_term}!' y luego listar las actividades."
        )

    return "\n".join(partes)


async def generar_respuesta(
    mensaje: str,
    items: list[dict],
    weather: dict | None = None,
    advertencias: list[str] | None = None,
    time_warning: str | None = None,
    intent: dict | None = None,
) -> str:
    IGNORAR_REGLA_HORARIA = False
    if intent and intent.get("temporalidad") == "futuro":
        IGNORAR_REGLA_HORARIA = True
        time_warning = None

    if not GEMINI_API_KEY:
        return _respuesta_fallback(mensaje, items, weather, advertencias or [], time_warning, intent)

    prompt = _armar_prompt(mensaje, items, weather, advertencias or [], time_warning, intent, IGNORAR_REGLA_HORARIA)
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
        return _respuesta_fallback(mensaje, items, weather, advertencias or [], time_warning, intent)
    data = resp.json()
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return text.replace("\\n", "\n")
    except (KeyError, IndexError):
        return _respuesta_fallback(mensaje, items, weather, advertencias or [], time_warning, intent)


def _respuesta_fallback(
    mensaje: str,
    items: list[dict],
    weather: dict | None,
    advertencias: list[str],
    time_warning: str | None = None,
    intent: dict | None = None,
) -> str:
    temporal_term = intent.get("temporal_term") if intent else None

    if "milan" in mensaje.lower() or "comer" in mensaje.lower():
        return (
            "¡Hola! Se me complico la conexion, pero te cuento que por ahora solo te puedo "
            "ayudar a buscar actividades recreativas y deportes en la feliz. ¿Te gustaria "
            "consultar por surf, kayak o paseos?"
        )
    if time_warning and not items:
        return (
            f"{time_warning}\n"
            "Mar del Plata y la zona tienen una gran oferta en gastronomia, "
            "espectaculos y actividades culturales, pero yo solo estoy preparada "
            "para recomendarte actividades deportivas y al aire libre."
        )
    if not items:
        return (
            "No encontre actividades para esa busqueda. "
            "Proba preguntando por un deporte (surf, pesca, trekking...) "
            "o por una zona (Playa Grande, Puerto...)"
        )
    lines = []
    if temporal_term:
        lines.append(f"Que buena idea planear para {temporal_term}!\n")
        lines.append(
            "Como soy un asistente digital, no tengo acceso a la agenda exacta de apertura "
            "de cada lugar para fechas futuras, pero te recomiendo estos lugares que suelen "
            "tener gran disponibilidad de actividades deportivas. "
            "Te sugiero llamar o consultar sus redes sociales antes de ir!\n"
        )
    elif time_warning:
        lines.append(f"{time_warning}\n")
    else:
        lines.append("Estas son mis recomendaciones:\n")
    if weather:
        lines.append(
            f"El clima en Mar del Plata: {weather['description']}, "
            f"{weather['temperature']}C con viento de {weather['wind_speed_kmh']} km/h.\n"
        )
    for w in advertencias:
        lines.append(f"{w}\n")
    for act in items[:10]:
        line = f"  - {act['descripcion']}"
        if act.get("sentimiento", {}).get("label") == "positivo":
            line += " (muy bien valorada)"
        lines.append(line)
    lines.append(
        "\nEspero que te sirvan. ¡Saludos!"
    )
    return "\n".join(lines)
