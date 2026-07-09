# AGENTS.md - MareaActiva

## 🌊 Contexto del Proyecto
- **Nombre:** MareaActiva (Recomendador de turismo deportivo y aventura en MDP).
- **Bot:** Ginga (Asistente empática, sociable, playera y estimulante).

## 🛠️ Reglas Operativas Estrictas (Desarrollo Seguro)

1. **Desarrollo Fragmentado Extremo:** Está terminantemente prohibido generar múltiples archivos de código complejos en un solo turno. Iremos creando y probando un archivo a la vez. No avances al siguiente paso sin mi aprobación explícita.
2. **Costo Cero y Local:** Todo el procesamiento y limpieza de datos se hace localmente con Pandas. No se usan bases de datos externas de pago ni servicios cloud.
3. **Análisis de Sentimiento Simple:** Se calculará de forma local usando las estrellas del CSV (1-5) como señal principal y un diccionario básico de palabras clave en español.
4. **Cierre con GitHub (Regla de Oro):** Al final de cada interacción o sesión donde logremos un avance funcional, debés recordarme y guiarme paso a paso con los comandos `git add`, `git commit -m "..."` y `git push` para respaldar mi código en el repositorio.

## 📂 Estructura Base Aceptada

Respetaremos la arquitectura modular propuesta en el PLAN (FastAPI + Pandas + HTML/JS), ejecutada capa por capa.
