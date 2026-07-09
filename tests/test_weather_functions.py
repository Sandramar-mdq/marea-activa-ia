from src.services.orchestrator import _apply_weather_warnings, _build_advertencia
from src.services.weather import WeatherData


class TestApplyWeatherWarnings:

    def test_none_weather_returns_empty(self):
        result = {}
        assert _apply_weather_warnings(result, None) == []
        assert result == {}

    def test_normal_weather_no_warnings(self):
        weather = WeatherData(22.0, "Clear", "cielo claro", 10.0)
        result = {}
        warnings = _apply_weather_warnings(result, weather)
        assert warnings == []
        assert result == {}

    def test_rain_sets_lluvia_and_warning(self):
        weather = WeatherData(18.0, "Rain", "lluvia ligera", 10.0)
        result = {}
        warnings = _apply_weather_warnings(result, weather)
        assert len(warnings) == 1
        assert "Lluvia activa" in warnings[0]
        assert result["_lluvia"] is True

    def test_thunderstorm_sets_lluvia(self):
        weather = WeatherData(16.0, "Thunderstorm", "tormenta", 5.0)
        result = {}
        _apply_weather_warnings(result, weather)
        assert result["_lluvia"] is True

    def test_drizzle_sets_lluvia(self):
        weather = WeatherData(15.0, "Drizzle", "llovizna", 5.0)
        result = {}
        _apply_weather_warnings(result, weather)
        assert result["_lluvia"] is True

    def test_squall_sets_lluvia(self):
        weather = WeatherData(14.0, "Squall", "chubasco", 20.0)
        result = {}
        _apply_weather_warnings(result, weather)
        assert result["_lluvia"] is True

    def test_strong_wind_sets_viento_fuerte(self):
        weather = WeatherData(20.0, "Clouds", "nublado", 30.0)
        result = {}
        warnings = _apply_weather_warnings(result, weather)
        assert len(warnings) == 1
        assert "Viento fuerte" in warnings[0]
        assert "30" in warnings[0]
        assert result["_viento_fuerte"] is True

    def test_wind_exactly_25_no_warning(self):
        weather = WeatherData(20.0, "Clouds", "nublado", 25.0)
        result = {}
        warnings = _apply_weather_warnings(result, weather)
        assert warnings == []

    def test_rain_and_strong_wind_both_warnings(self):
        weather = WeatherData(16.0, "Thunderstorm", "tormenta", 40.0)
        result = {}
        warnings = _apply_weather_warnings(result, weather)
        assert len(warnings) == 2
        assert result["_lluvia"] is True
        assert result["_viento_fuerte"] is True


class TestBuildAdvertencia:

    def test_none_weather_returns_none(self):
        assert _build_advertencia({"categoria": "Playa"}, None) is None

    def test_lluvia_aire_libre_returns_warning(self):
        weather = WeatherData(18.0, "Rain", "lluvia", 10.0)
        item = {"_lluvia": True, "categoria": "Deportes Acuaticos", "descripcion": "Kayak en el puerto"}
        assert (
            _build_advertencia(item, weather)
            == "Actividad al aire libre - verificar condiciones climaticas"
        )

    def test_lluvia_techada_returns_none(self):
        weather = WeatherData(18.0, "Rain", "lluvia", 10.0)
        item = {"_lluvia": True, "categoria": "Museos y Centros Culturales", "descripcion": "Visita al museo"}
        assert _build_advertencia(item, weather) is None

    def test_lluvia_casinos_returns_none(self):
        weather = WeatherData(18.0, "Rain", "lluvia", 10.0)
        item = {"_lluvia": True, "categoria": "Casinos y Bingos", "descripcion": "Casino central"}
        assert _build_advertencia(item, weather) is None

    def test_lluvia_bowlings_returns_none(self):
        weather = WeatherData(18.0, "Rain", "lluvia", 10.0)
        item = {"_lluvia": True, "categoria": "Bowlings", "descripcion": "Bolish del puerto"}
        assert _build_advertencia(item, weather) is None

    def test_viento_fuerte_nautica_returns_warning(self):
        weather = WeatherData(20.0, "Clouds", "nublado", 35.0)
        item = {"_viento_fuerte": True, "categoria": "Deportes", "descripcion": "Pesca deportiva en el muelle"}
        assert (
            _build_advertencia(item, weather)
            == "Viento fuerte (35.0 km/h) - precaucion"
        )

    def test_viento_fuerte_surf_returns_warning(self):
        weather = WeatherData(22.0, "Clear", "despejado", 40.0)
        item = {"_viento_fuerte": True, "categoria": "Playa", "descripcion": "Surf en playa grande"}
        assert (
            _build_advertencia(item, weather)
            == "Viento fuerte (40.0 km/h) - precaucion"
        )

    def test_viento_fuerte_no_nautica_returns_none(self):
        weather = WeatherData(20.0, "Clouds", "nublado", 35.0)
        item = {"_viento_fuerte": True, "categoria": "Parques", "descripcion": "Caminata por la costa"}
        assert _build_advertencia(item, weather) is None

    def test_no_flags_returns_none(self):
        weather = WeatherData(22.0, "Clear", "despejado", 10.0)
        item = {"categoria": "Playa", "descripcion": "Caminata por la playa"}
        assert _build_advertencia(item, weather) is None

    def test_lluvia_techada_with_viento_fuerte_nautica(self):
        weather = WeatherData(16.0, "Rain", "lluvia", 35.0)
        item = {
            "_lluvia": True,
            "_viento_fuerte": True,
            "categoria": "Museos y Centros Culturales",
            "descripcion": "Pesca en el muelle",
        }
        assert (
            _build_advertencia(item, weather)
            == "Viento fuerte (35.0 km/h) - precaucion"
        )
