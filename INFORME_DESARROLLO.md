# INFORME DE DESARROLLO - MareaActiva

**Proyecto:** MareaActiva - Asistente de Turismo Deportivo y Recreativo
**Tecnologias:** FastAPI, Pandas, Google Gemini 2.0 Flash, HTML/CSS/JS
**Fecha de cierre:** 17 de julio de 2026
**Autores:** Equipo de desarrollo - TP Integrador Desarrollo Sistemas IA

---

## 1. Resumen Ejecutivo

MareaActiva es un chatbot basado en LLM que recomienda actividades deportivas y recreativas al aire libre exclusivamente en Mar del Plata, Argentina. El sistema combina procesamiento local de datos (Pandas) con la API de Google Gemini para generar respuestas conversacionales con personalidad, a traves de una agente de IA llamada "Ginga".

El orquestador analiza el mensaje del usuario, detecta la intencion, filtra datos de CSVs, aplica restricciones temporales, climaticas y de dominio, y pasa los resultados estructurados a Ginga para que genere una respuesta empatica y contextualizada.

---

## 2. Arquitectura del Sistema

```
Browser (app.js)
    |
    +-- POST /api/chat { message: "..." }
    |
FastAPI Router (routes/chat.py)
    |
    +-- orchestrator.recommend(message)
    |       |
    |       +-- data_loader.load_merged_data()     --> Pandas lee CSVs
    |       +-- weather.fetch_weather()             --> OpenWeatherMap API
    |       +-- _detect_intent(message)             --> Keyword matching
    |       +-- _es_fuera_de_dominio(message)       --> Dominio check
    |       +-- _es_otra_ciudad(message)            --> Geografia check
    |       +-- _filtrar_compuesto(df, ...)         --> Filtrado AND
    |       +-- classifier.classify_intensidad()    --> Etiquetas
    |       +-- classifier.classify_edad()          --> Etiquetas
    |       +-- sentiment.analyze_sentiment()       --> Sentimiento
    |       |
    |       +-- Retorna { items, weather, advertencias, intent, response }
    |
    +-- ginga_agent.generar_respuesta(...)
            |
            +-- _armar_prompt(...)                  --> Prompt dinamico
            +-- Gemini API (gemini-2.0-flash)       --> Respuesta IA
            +-- (fallback si no hay API key)
    |
    +-- Retorna ChatResponse
```

### Stack Tecnologico

| Componente | Tecnologia | Version |
|---|---|---|
| Backend | FastAPI | 0.115.6 |
| Servidor | Uvicorn | 0.34.0 |
| Datos | Pandas | 2.2.3 |
| HTTP Client | httpx | 0.28.1 |
| LLM | Google Gemini | 2.0 Flash |
| Clima | OpenWeatherMap | API REST |
| Frontend | HTML/CSS/JS | Vanilla |
| Testing | pytest | 8.3.4 |
| Python | CPython | 3.10+ |

---

## 3. Estructura del Proyecto

```
marea_activa/
  .env                         # API keys (GEMINI, OPENWEATHER)
  .env.example                 # Template de variables de entorno
  requirements.txt             # Dependencias Python
  iniciar_servidor.bat         # Script de inicio Windows
  AGENTS.md                    # Reglas para agentes de IA
  INFORME_DESARROLLO.md        # Este documento
  src/
    main.py                    # FastAPI app, CORS, rutas estaticas
    config.py                  # Configuracion: rutas, encoding, API keys
    models/
      requests.py              # Modelos Pydantic (ChatRequest, ChatResponse)
    routes/
      chat.py                  # POST /api/chat - endpoint unico
    services/
      orchestrator.py          # ORQUESTADOR: deteccion de intencion, filtrado
      ginga_agent.py           # AGENTE IA: prompt SISTEMA, llamada Gemini
      classifier.py            # Clasificacion de intensidad y edad
      data_loader.py           # Carga y merge de CSVs con Pandas
      sentiment.py             # Analisis de sentimiento basado en estrellas
      weather.py               # API OpenWeatherMap
  datasets/
    recreacion_0.csv           # 141 actividades (separator: ;, encoding: latin1)
    opiniones_google.csv       # 103 opiniones de usuarios
    balnearios_0.csv           # 103 balnearios (cargado, no usado aun)
  static/
    css/styles.css             # UI del chat (305 lineas, responsive)
    js/app.js                  # Frontend vanilla JS (117 lineas)
  templates/
    index.html                 # Template principal del chat
  tests/
    test_weather_functions.py  # 19 tests unitarios de clima
```

---

## 4. Cronologia de Desarrollo - Hitos Clave

### Hito 1: Setup Inicial del Proyecto

**Commit:** `b189d3b` - "chore: initial project setup - MareaActiva backend"

Se configuro la estructura base del proyecto con:
- FastAPI como framework backend
- Uvicorn como servidor ASGI
- Pandas para procesamiento local de datos
- Estructura de directorios modular (`src/routes/`, `src/services/`, `src/models/`)

**Decision tecnica:** Se opto por una arquitectura fragmentada donde el orquestador (orchestrator.py) maneja toda la logica de negocio y el agente de IA (ginga_agent.py) solo genera la respuesta conversacional. Esta separacion permite testear la logica de filtrado sin depender de la API de Gemini.

**Dataset:** Se cargaron 3 CSVs separados por punto y coma (`;`) con encoding `latin1`:
- `recreacion_0.csv`: 141 actividades deportivas y recreativas
- `opiniones_google.csv`: 103 opiniones de usuarios con calificacion en estrellas
- `balnearios_0.csv`: 103 registros de balnearios (cargado pero no integrado)

**Problema resuelto:** Los CSVs usan `latin1` encoding y separador `;`, no el estandar UTF-8 con coma. Se configuro en `config.py`:

```python
CSV_ENCODINGS = {
    "recreacion": "latin1",
    "balnearios": "latin1",
    "opiniones": "latin1",
}
CSV_SEPARATOR = ";"
```

---

### Hito 2: Tests de Clima y Limpieza de Salida

**Commit:** `94f07cd` - "feat: limpiar \\n en generar_respuesta y agregar tests de clima"

**Problema detectado:** La respuesta de Gemini contenía secuencias de escape `\\n` en lugar de saltos de linea reales, arruinando la visualizacion en el frontend.

**Solucion:** En `ginga_agent.py:141`:

```python
text = data["candidates"][0]["content"]["parts"][0]["text"]
return text.replace("\\n", "\n")
```

**Testing:** Se crearon los primeros tests unitarios para las funciones de advertencias climaticas:
- `_apply_weather_warnings()`: Verifica que lluvia, tormenta, llovizna y chubasco activen la flag `_lluvia`. Verifica que viento > 25 km/h active `_viento_fuerte`. Verifica que viento exacto de 25 km/h NO active la alerta (limite estricto).
- `_build_advertencia()`: Verifica que actividades techadas (museos, casinos, bowlings) NO reciban advertencia de lluvia. Verifica que actividades nauticas SI reciban advertencia de viento fuerte.

---

### Hito 3: Filtrado Semantico Estricto

**Commit:** `ec4d7e8` - "feat: filtrado semantico estricto con deteccion combinada de actividad+zona"

**Problema detectado:** El sistema original buscaba actividades o zonas por separado. Si el usuario decia "surf en Playa Grande", el orquestador detectaba "surf" como actividad pero podia ignorar "Playa Grande" como zona, devolviendo surf de todas las zonas.

**Solucion:** Se implemento el filtrado compuesto AND en `_filtrar_compuesto()`:

```python
def _filtrar_compuesto(df, activity_terms, zona):
    filtered = df.copy()
    if zona:
        z = _normalize(zona)
        filtered["_match_zona"] = filtered["Zona"].fillna("").apply(
            lambda v: z in _normalize(v)
        )
        filtered = filtered.query("_match_zona == True")
        filtered = filtered.drop(columns=["_match_zona"])
    if activity_terms:
        filtered = _search_columns(filtered, activity_terms)
    return filtered
```

**Logica:** Primero filtra por zona (substring match en la columna `Zona`), luego busca keywords de actividad en las columnas `descripcion`, `observacion` y `Categoria`. Ambos filtros se aplican con logica AND.

**Busqueda en multiples columnas:**

```python
def _search_columns(df, terms):
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
```

---

### Hito 4: Mejoras en Filtrado, Respuesta y Frontend

**Commit:** `a223bf2` - "feat: mejoras en filtrado, respuesta y frontend del chat"

Se realizaron multiples mejoras simultaneas:

**A) Normalizacion de texto:** Se implemento `_normalize()` que elimina acentos, convierte a minuscula y elimina espacios:

```python
def _normalize(text):
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return text.lower().strip()
```

**B) Matching de keywords con word boundaries:** Se implemento `_kw_in_text()` para evitar falsos positivos:

```python
def _kw_in_text(kw, text):
    if " " in kw:
        return kw in text  # Substring para keywords compuestas
    return bool(re.search(r'\b' + re.escape(kw) + r'\b', text))  # Word boundary para una palabra
```

Esto evita que "sur" matchee "estructura" o que "pesca" matchee "pescaito".

**C) Deteccion de zonas de MDP:** Se creo el diccionario `ZONAS_KEYWORDS` con las 23 zonas conocidas de Mar del Plata:

```python
ZONAS_KEYWORDS = {
    "playa grande", "puerto", "centro", "varese", "punta mogotes",
    "la perla", "playas del centro", "playas del sur", "playas alfar",
    "punta cantera", "camet", "chapadmalal", "sierra de los padres",
    "serrana", "batan", "microcentro", "perla norte",
    "los troncos", "plaza rocha", "caballito",
    "zona norte", "norte", "zona sur", "sur", "zona este", "este",
    "zona oeste", "oeste", "costa", "costero", "costera",
}
```

**D) Deteccion de intencion:** Se implemento `_detect_intent()` con prioridad jerarquica:
1. Listar zonas (si dice "listar" + "zona")
2. Mejor valoradas (si dice "mejor valorada", "top", etc.)
3. Playa (si dice palabras clave de playa)
4. Familia (si dice palabras clave familiares)
5. Actividad especifica (si dice un deporte)
6. Solo zona (si no matcheo actividad pero si zona)
7. Intensidad (si dice "aventura", "extremo", etc.)
8. Temporalidad (si dice "manana", "fin de semana", etc.)

**E) Frontend:** Se implemento la interfaz de chat con:
- Burbujas de mensaje (usuario azul, bot gris con borde celeste)
- Indicador de "escribiendo..." con animacion de puntos
- Botones de acciones rapidas (actividades familiares, playa, mejor valoradas, listar por zona)
- Adaptada a movil (max-width: 480px) y desktop (max-width: 720px)

---

### Hito 5: Filtrado Compuesto AND y Respuesta Temporal

**Commit:** `5db67fe` - "feat: filtrado compuesto AND, respuesta temporal empatica y documentacion README"

**A) Intenciones compuestas:** Se mejoro la deteccion para que "surf en Playa Grande" genere un intent con `tipo="actividad"`, `actividad="surf"` y `zona="playa grande"`. El orquestador luego aplica ambos filtros.

**B) Respuesta temporal empatica:** Cuando el usuario pregunta por una fecha futura ("manana", "fin de semana"), el sistema:
1. Detecta la temporalidad y guarda el termino original
2. Limpia el mensaje de palabras temporales antes de buscar
3. Envia una etiqueta `ETIQUETA TEMPORAL: futuro` al prompt de Gemini
4. Ginga DEBE empezar con una frase como "Que buena idea planear para manana!"
5. Se repite la instruccion al final del prompt con la maxima prioridad

**Prompt temporal (lineas 15-23 de ginga_agent.py):**

```
REGLA TEMPORAL: Si detectas la ETIQUETA TEMPORAL: futuro en el prompt, tu respuesta DEBE comenzar
con una frase personalizada que incluya el TERMINO TEMPORAL ORIGINAL que el usuario uso.
Por ejemplo, si el usuario dijo 'manana', empezá con: 'Que buena idea planear para manana!'.
Si dijo 'el fin de semana', empezá con: 'Que buena idea planear para el fin de semana!'.
Luego de esa frase, aclará que como asistente digital no tenés acceso a la agenda exacta de apertura
de cada lugar para fechas futuras, pero que le recomiendás estos lugares que suelen tener gran
disponibilidad de actividades deportivas. Sugirile llamar o consultar sus redes sociales antes de ir.
Luego lista las actividades recomendadas. No inventes horarios ni disponibilidad.
Esta regla tiene PRIORIDAD sobre cualquier otra instruccion.
```

**C) Resolucion de conflictos temporales vs horarios:** Cuando hay consulta futura + hora nocturna, la temporalidad tiene prioridad y se suprime la advertencia horaria:

```python
IGNORAR_REGLA_HORARIA = False
if intent and intent.get("temporalidad") == "futuro":
    IGNORAR_REGLA_HORARIA = True
    time_warning = None
```

Esto evita que Ginga diga "son las 22hs, no hay actividades" cuando el usuario pregunto por "manana".

---

### Hito 6: Estabilidad del Servidor

**Commit:** `b8ec9d4` - "fix: estabilidad del servidor - try/except en recommend() y chat, uvicorn solo monitorea src/"

**Problema detectado:** El servidor crasheaba con excepciones no capturadas (NaN en Pandas, columnas faltantes, etc.).

**Soluciones:**

A) `try/except` en `recommend()` (orchestrator.py:524-533):

```python
except Exception as e:
    return {
        "items": [],
        "weather": None,
        "advertencias": [],
        "intent": {"tipo": "general", "keyword": "", "actividad": None, "zona": None},
        "response": "",
        "time_warning": None,
        "error": str(e),
    }
```

B) `try/except` en el endpoint `chat()` (routes/chat.py:68-76):

```python
except Exception as e:
    return ChatResponse(
        response="Disculpa, tuve un problema al procesar tu consulta. "
                "Probá de nuevo o preguntame por otra actividad o zona de Mar del Plata.",
        items=[],
        weather=None,
        advertencias=[],
    )
```

C) Proteccion contra NaN de Pandas en `_filtrar_por_tipo_actividad()`:

```python
col = "tipo_actividad "
if col not in df.columns:
    col = "tipo_actividad"
```

Nota: El CSV tiene un espacio al final del nombre de columna `"tipo_actividad "`. Se verifican ambas variantes.

D) Limpieza de NaN en la capa de presentacion (`routes/chat.py:33-38`):

```python
zona_val = item.get("zona", "")
if pd.isna(zona_val) or not isinstance(zona_val, str):
    zona_val = ""
```

---

### Hito 7: Eximir Actividades Indoor de Advertencia Nocturna

**Commit:** `03069d4` - "fix: eximir actividades indoor de la advertencia horaria nocturna"

**Problema detectado:** A las 22hs, si el usuario preguntaba por "museo" o "bowling", el sistema devolvia una advertencia de "no hay luz solar" y no mostraba actividades, pese a que estos places funcionan de noche.

**Solucion:** En `_check_time_restriction()`, se verifica si la actividad es indoor antes de retornar la advertencia:

```python
def _check_time_restriction(message, intent):
    hora = datetime.now().hour
    if hora < 8 or hora >= 18:
        if intent["tipo"] == "actividad" and intent.get("actividad"):
            act = _normalize(intent["actividad"])
            if act in INDOOR_KEYWORDS:
                return None  # No hay restriccion para actividades techadas
        ...
```

Se definio `INDOOR_KEYWORDS`:

```python
INDOOR_KEYWORDS = {
    "museo", "casino", "bingo", "bowling", "acuario", "feria",
    "mercado", "teatro", "cine", "religioso", "cultural",
    "artesanal", "recreacion para ninos",
}
```

---

### Hito 8: Restriccion de Dominio (Fuera de Ambito)

**Fecha:** Sesion de desarrollo actual

**Problema detectado:** El usuario podia preguntar por temas ajenos al turismo deportivo (gastronomia, alojamiento, museos, politica, etc.) y Ginga intentaba responder con informacion inventada.

**Solucion:** Se implemento la REGLA DE ORO en el prompt del sistema y la deteccion `_es_fuera_de_dominio()`:

```python
FUERA_DE_DOMINIO_KEYWORDS = {
    "museo", "museos", "cerveceria", "cervecerias", "bodega", "bodegas",
    "destileria", "feria", "ferias", "mercado", "mercados",
    "casino", "casinos", "bingo", "bingos", "iglesia", "iglesias",
    "capilla", "capillas", "parroquia", "parroquias",
    "turismo religioso", "gastronomia", "comida", "restaurante",
    "restaurantes", "milanesa", "milanesas", "helado", "helados",
    "teatro", "teatros", "cine", "cines", "alojamiento", "hotel",
    "hoteles", "departamento", "hostel", "propiedad", "inmobiliaria",
}
```

Cuando se detecta, se retorna un mensaje fijo SIN llamar a Gemini:

```python
MENSAJE_FUERA_DE_DOMINIO = (
    "Solo estoy capacitado para recomendarte actividades deportivas y recreativas al aire libre."
)
```

**Prompt de soporte (REGLA DE ORO en SISTEMA):**

```
REGLA DE ORO: Tu aplicacion Marea Activa es EXCLUSIVAMENTE para actividades deportivas y recreativas
al aire libre en Mar del Plata. Si el usuario te pide cosas fuera de este ambito (como museos,
cervecerias, gastronomia, alojamiento, politica, etc.), el sistema ya habra detectado esto y te
enviara el mensaje: 'Solo estoy capacitada para recomendarte actividades deportivas y recreativas
al aire libre'. Debes incluir ese mensaje exacto en tu respuesta, con calidez pero sin agregar
informacion adicional ni inventar actividades.
```

---

### Hito 9: Restriccion Geografica (Otra Ciudad)

**Fecha:** Sesion de desarrollo actual

**Problema detectado:** El usuario podia preguntar por actividades en otras ciudades (Necochea, Miramar, Villa Gesell, Tandil, etc.) y el sistema respondia con actividades de Mar del Plata como si fueran de la ciudad consultada, generando informacion engañosa.

**Solucion:** Se implemento la deteccion geografica con dos componentes:

A) Diccionario de ciudades exteriores:

```python
CIUDADES_EXTERIOR_KEYWORDS = {
    # Costa bonaerense
    "necochea", "miramar", "villa gesell", "pinamar", "carilo",
    "san clemente", "la lucila del mar", "mar de ajo",
    "san bernardo", "costa chica", "costa azul", "mar del tuyu",
    "santa teresita", "partido de la costa",
    # Interior turistico
    "tandil", "balcarce", "loberia", "chascomus", "dolores",
    "ayacucho", "rauch",
    # Ciudades principales
    "buenos aires", "la plata", "rosario", "cordoba",
    "bariloche", "mendoza", "salta", "neuquen",
    "san juan", "san luis", "santa fe", "ushuaia",
    "el calafate", "rio gallegos", "concepcion del uruguay",
}
```

B) Funcion de deteccion con excepcion para MDP:

```python
def _es_otra_ciudad(message):
    msg = _normalize(message)
    menciona_mdp = (
        "mar del plata" in msg
        or bool(re.search(r'\bmdp\b', msg))
        or any(_kw_in_text(kw, msg) for kw in ZONAS_KEYWORDS)
    )
    if menciona_mdp:
        return False  # Si menciona MDP o sus zonas, no rechazar
    return any(_kw_in_text(kw, msg) for kw in CIUDADES_EXTERIOR_KEYWORDS)
```

**Logica clave:** La funcion solo rechaza si el usuario menciona una ciudad exterior Y NO menciona "mar del plata", "mdp" ni ninguna zona de MDP. Esto resuelve el edge case "soy de Buenos Aires, que hay en Mar del Plata?" -> se acepta porque menciona MDP.

**Mensaje de rechazo:**

```python
MENSAJE_OTRA_CIUDAD = (
    "Soy Ginga, tu asistente de turismo deportivo en Mar del Plata. "
    "Por el momento solo estoy preparada para recomendarte actividades "
    "deportivas y recreativas en la ciudad de Mar del Plata. "
    "¿Te gustaria que te recomiende algo para hacer en la Feliz?"
)
```

C) Prompt de soporte (REGLA GEOGRAFICA en SISTEMA):

```
REGLA GEOGRAFICA: Tu asistencia es EXCLUSIVAMENTE para la ciudad de
Mar del Plata y sus zonas. Si el usuario te menciona otra ciudad,
playa o localidad (como Necochea, Miramar, Villa Gesell, Tandil, etc.),
el sistema ya habra detectado esto y te enviara un mensaje indicando
que solo estas preparada para responder sobre Mar del Plata.
Incluye ese mensaje con calidez, sin inventar informacion sobre otras ciudades.
```

---

## 5. Modulos del Sistema - Detalle Tecnico

### 5.1 Orquestador (`orchestrator.py` - 575 lineas)

El orquestador es el nucleo del sistema. Su funcion principal `recommend()` orquesta todo el pipeline:

1. **Carga de datos:** `load_merged_data()` carga los CSVs y hace un LEFT JOIN entre recreacion y opiniones por la columna `descripcion` normalizada.
2. **Clima:** `fetch_weather()` obtiene el clima actual de MDP via OpenWeatherMap.
3. **Deteccion de intencion:** `_detect_intent()` analiza el mensaje con 8 categorias de prioridad.
4. **Filtros de dominio:** `_es_fuera_de_dominio()` y `_es_otra_ciudad()` rechazan consultas fuera de alcance.
5. **Filtrado de datos:** `_filtrar_por_tipo_actividad()` excluye actividades que no son "deportiva" o "recreacion activa".
6. **Restriccion horaria:** `_check_time_restriction()` advierte sobre falta de luz solar (excepto actividades indoor).
7. **Filtrado compuesto:** `_filtrar_compuesto()` aplica filtros AND (zona + actividad).
8. **Clasificacion:** `classify_intensidad()` y `classify_edad()` etiquetan cada resultado.
9. **Sentimiento:** `analyze_sentiment()` analiza estrellas y keywords de opiniones.
10. **Advertencias climaticas:** `_apply_weather_warnings()` y `_build_advertencia()` generan alertas contextuales.

**Diccionarios de keywords:**

| Diccionario | Cantidad | Proposito |
|---|---|---|
| `ACTIVIDADES_KEYWORDS` | ~60 | Deteccion de deportes/actividades |
| `ZONAS_KEYWORDS` | ~28 | Zonas de Mar del Plata |
| `PLAYA_KEYWORDS` | ~14 | Actividades de playa/costa |
| `FAMILIA_KEYWORDS` | ~20 | Actividades familiares |
| `FUERA_DE_DOMINIO_KEYWORDS` | ~30 | Temas ajenos al dominio |
| `CIUDADES_EXTERIOR_KEYWORDS` | ~30 | Ciudades fuera de MDP |
| `TEMPORAL_KEYWORDS` | ~8 | Consultas a futuro |

### 5.2 Agente de IA (`ginga_agent.py` - 209 lineas)

Ginga es la personalidad del chatbot. Su prompt `SISTEMA` define:
- Personalidad: anfitriona marplatense, calida, empatica, inclusiva
- Regla temporal: RESPUESTA EMPATICA para consultas futuras
- Regla de oro: Solo actividades deportivas al aire libre
- Regla geografica: Solo Mar del Plata
- Regla horaria: Advertencia integrada en la respuesta
- Idioma: Espanol argentino

**Construccion dinamica del prompt (`_armar_prompt`):**

El prompt se ensambla con secciones condicionales:
1. Mensaje del usuario
2. Hora actual
3. Etiqueta temporal (si aplica)
4. Advertencia horaria (si aplica y no hay temporalidad futura)
5. Datos del clima
6. Advertencias climaticas
7. Lista de actividades (hasta 10)
8. Instruccion final
9. Refuerzo de temporalidad (si aplica)

**Fallback sin API key:** Si no hay `GEMINI_API_KEY` configurada, el sistema genera una respuesta basada en templates sin llamar a Gemini. Esto permite desarrollar y testear sin costo de API.

### 5.3 Clasificador (`classifier.py` - 92 lineas)

Clasifica cada actividad en:
- **Intensidad:** Alta (surf, kayak, parapente), Media (trekking, running), Baja (caminata, paseo)
- **Edad:** Infantil (play ground, ninos), Adultos (casino, buceo), Todas las edades

La clasificacion se basa en keywords de la descripcion y la categoria de cada actividad.

### 5.4 Analisis de Sentimiento (`sentiment.py` - 75 lineas)

Combina dos senales:
1. **Estrellas (1-5):** >=4 positivo, ==3 neutral, <3 negativo
2. **Keywords del comentario:** Busca palabras positivas ("excelente", "genial") y negativas ("malo", "pesimo") en el texto de la opinion

Nota: Actualmente el flag `negado` se detecta pero no se usa para invertir el sentimiento. Es una mejora pendiente.

### 5.5 Carga de Datos (`data_loader.py` - 33 lineas)

- `load_all_dataframes()`: Carga los 3 CSVs crudos
- `load_merged_data()`: Hace LEFT JOIN entre recreacion y opiniones, retorna (merged, recreacion, opiniones)

El merge usa la columna `descripcion` normalizada (lowercase + strip) como join key.

### 5.6 Clima (`weather.py` - 42 lineas)

Coordenadas hardcodeadas de Mar del Plata:
```python
MDP_LAT = -38.0023
MDP_LON = -57.5575
```

La funcion `fetch_weather()` retorna un dataclass `WeatherData` con temperatura, condicion, descripcion y velocidad del viento en km/h.

---

## 6. Edge Cases y Problemas Resueltos

### 6.1 Columna con espacio: `"tipo_actividad "`
El CSV tiene un espacio al final del nombre de columna. Se verifican ambas variantes:
```python
col = "tipo_actividad "
if col not in df.columns:
    col = "tipo_actividad"
```

### 6.2 NaN de Pandas
Los valores faltantes en columnas como `Zona` y `Categoria` se convierten a string vacio antes de usar:
```python
zona_val = row.get("Zona", "")
if pd.isna(zona_val):
    zona_val = ""
```

### 6.3 Word boundaries en keywords
Evita falsos positivos como "sur" matcheando "estructura":
```python
def _kw_in_text(kw, text):
    if " " in kw:
        return kw in text
    return bool(re.search(r'\b' + re.escape(kw) + r'\b', text))
```

### 6.4 Conflicto temporal vs horario
Consulta futura ("manana") + hora nocturna (22:00) -> la temporalidad tiene prioridad, se suprime la advertencia horaria.

### 6.5 Actividades indoor de noche
Museos, casinos y bowling se eximen de la restriccion horaria nocturna.

### 6.6 "Soy de Buenos Aires, que hay en Mar del Plata"
La deteccion geografica verifica si se menciona MDP antes de rechazar. Si se menciona, se acepta.

### 6.7 Mensaje vacio o sin intencion
Si no se detecta ninguna intencion especifica, el tipo queda como "general" y Ginga responde con la lista completa de actividades.

---

## 7. Flujo Completo de una Consulta

**Ejemplo:** Usuario envia "quiero surfear en Playa Grande manana"

1. **Orquestador recibe:** `"quiero surfear en Playa Grande manana"`
2. **Normalizacion:** `"quiero surfear en playa grande manana"`
3. **Deteccion de intencion:**
   - No es "listar zonas"
   - No es "mejor valoradas"
   - Matchea zona: `"playa grande"`
   - No matchea playa (porque "surf" esta en ACTIVIDADES_KEYWORDS primero)
   - Matchea actividad: `"surf"` -> `tipo="actividad"`
   - Matchea temporal: `"manana"` -> `temporalidad="futuro"`
4. **Filtro dominio:** No es fuera de dominio, no es otra ciudad
5. **Carga de datos:** Pandas carga CSVs, hace merge
6. **Filtrado por tipo:** Solo actividades "deportiva" o "recreacion activa"
7. **Temporalidad futura:** Se salta la restriccion horaria
8. **Limpieza temporal:** Se elimina "manana" del mensaje para buscar
9. **Filtrado compuesto:** Busca "surf" en descripciones/categorias AND zona="playa grande"
10. **Clasificacion:** Cada resultado recibe intensidad, edad, sentimiento
11. **Prompt:** Se arma el prompt con etiqueta temporal, clima, actividades
12. **Gemini:** Genera respuesta empatica que empieza con "Que buena idea planear para manana!"
13. **Respuesta:** Se retorna al frontend

---

## 8. Testing

### 8.1 Suite de Tests (`test_weather_functions.py`)

19 tests unitarios cubriendo:

| Clase | Tests | Cubre |
|---|---|---|
| `TestApplyWeatherWarnings` | 9 | Lluvia (Rain, Thunderstorm, Drizzle, Squall), viento fuerte, caso combinado |
| `TestBuildAdvertencia` | 10 | Aire libre vs techado, viento en nauticas, sin flags |

### 8.2 Ejecucion

```bash
python -m pytest tests/ -v
```

Resultado: 19/19 tests pasan.

### 8.3 Testing Manual (Edge Cases)

| Mensaje | Resultado Esperado |
|---|---|
| "quiero surfear en Necochea" | Rechazo geografico |
| "actividades en Miramar" | Rechazo geografico |
| "que hay para hacer en Villa Gesell" | Rechazo geografico |
| "soy de Buenos Aires, que hay en Mar del Plata?" | Acepta (menciona MDP) |
| "quiero surfear" | Busqueda normal |
| "playa en Pinamar" | Rechazo geografico |
| "que hay en el norte?" | Acepta (zona norte de MDP) |
| "museo" a las 22hs | Muestra museos sin advertencia |
| "surf" a las 22hs | Advertencia nocturna |
| "que actividades hay manana?" | Respuesta temporal empatica |
| "quiero milanesas" | Rechazo fuera de dominio |

---

## 9. Decisiones de Diseno

### 9.1 Por que no se usa la API de Gemini para todo?
Se decidio que el orquestador haga el trabajo pesado de filtrado localmente con Pandas por:
- **Costo:** Cada llamada a Gemini tiene un costo monetario
- **Velocidad:** El filtrado local es instantaneo
- **Control:** Se puede garantizar que solo se recomienden actividades reales del dataset
- **Testing:** La logica de negocio se puede testear sin dependencia externa

### 9.2 Por que un solo endpoint?
Se uso unico endpoint `POST /api/chat` para:
- Simplicidad del frontend
- Un solo flujo de datos para todos los tipos de consulta
- El orquestador internamente maneja las diferencias

### 9.3 Por que keyword matching y no NLP avanzado?
- El dataset es pequeno (141 actividades)
- Los dominios son estrechos (deportes en una ciudad)
- No se requiere entrenamiento de modelos
- Es transparente y mantenible
- Se puede extender agregando keywords

### 9.4 Separacion Orquestador / Agente
Esta separacion permite:
- Cambiar el LLM (Gemini -> otro) sin tocar la logica de negocio
- Testear el filtrado sin llamar a la API
- Mantener la personalidad de Ginga en un solo lugar (SISTEMA)

---

## 10. Dependencias y Configuracion

### 10.1 Requisitos (`requirements.txt`)

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
pandas==2.2.3
httpx==0.28.1
python-dotenv==1.0.1
pytest==8.3.4
```

### 10.2 Variables de Entorno (`.env`)

```
GEMINI_API_KEY=tu_api_key_de_gemini
OPENWEATHER_API_KEY=tu_api_key_de_openweather
```

### 10.3 Inicio del Servidor

```bash
# Windows
iniciar_servidor.bat

# Manual
python -m uvicorn src.main:app --reload --port 8000
```

### 10.4 Acceso

- UI: `http://localhost:8000`
- API: `POST http://localhost:8000/api/chat`

---

## 11. Metricas del Codigo

| Metrica | Valor |
|---|---|
| Lineas de Python (src/) | ~1.100 |
| Lineas de CSS | 305 |
| Lineas de JavaScript | 117 |
| Lineas de HTML | 46 |
| Tests unitarios | 19 |
| Archivos Python | 11 |
| Datasets CSV | 3 |
| Actividades en dataset | 141 |
| Opiniones en dataset | 103 |
| Endpoints API | 1 |

---

## 12. Mejoras Pendientes

1. **Integrar balnearios_0.csv:** El dataset esta cargado pero no se usa en el pipeline de recomendacion.
2. **Invertir sentimiento con negacion:** El flag `negado` en `sentiment.py` se detecta pero no se aplica para flipppear el label.
3. **Filtrado geografico mas robusto:** Actualmente usa keyword matching puro. Un modelo NLP o embeddings permitirian detectar menciones indirectas a otras ciudades.
4. **Historial de conversacion:** Actualmente cada mensaje es independiente. Agregar memoria de contexto permitiria follow-ups como "y en esa zona, algo para chicos?".
5. **Cache de clima:** Actualmente llama a OpenWeatherMap en cada request. Un cache de 10-15 minutos reduciria llamadas a la API.
6. **Tests de integracion:** Los tests actuales cubren solo funciones aisladas del orquestador. Falta testear el flujo completo recommend() + generar_respuesta().
7. **Despliegue:** Actualmente corre localmente. Falta configuracion para produccion (Docker, Gunicorn, etc.).

---

*Informe generado automaticamente a partir del historial de codigo fuente del proyecto MareaActiva.*
