from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Mensaje del usuario")


class SentimentInfo(BaseModel):
    label: str
    score: float


class ActivityItem(BaseModel):
    descripcion: str
    categoria: str = ""
    zona: str = ""
    intensidad: str
    edad: str = "Todas las edades"
    sentimiento: SentimentInfo | None = None
    advertencia: str | None = None


class WeatherInfo(BaseModel):
    temperature: float
    condition: str
    description: str
    wind_speed_kmh: float


class ChatResponse(BaseModel):
    response: str = Field(..., description="Respuesta de Ginga para el chat")
    items: list[ActivityItem] = Field(default_factory=list)
    weather: WeatherInfo | None = None
    advertencias: list[str] = Field(default_factory=list)
