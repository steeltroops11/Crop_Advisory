"""
src/weather.py — Phase 2, Step 6
Real-time Weather Ingestion & PAU Agronomic Weather-Gate Evaluator.

Uses Open-Meteo API (free, reliable, no API key required) to fetch
current weather and 48-hour forecasts for Punjab districts.
Applies PAU rules:
  1. Rain gate: withhold irrigation & urea if rain forecasted in 24-48h.
  2. Wind gate (PAU wheat rule): withhold irrigation if wind > 12-15 km/h (prevents lodging).
  3. Formats weather context for injection into RAG prompt.
"""

import sys
from pathlib import Path
import time
import requests
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, Any

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from src.config import (
    OPEN_METEO_BASE_URL,
    DEFAULT_DISTRICT,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
)

# ---------------------------------------------------------------------------
# Coordinates for Major Punjab Agricultural Districts
# ---------------------------------------------------------------------------

PUNJAB_DISTRICTS: Dict[str, Tuple[float, float]] = {
    "ludhiana": (30.9010, 75.8573),
    "amritsar": (31.6340, 74.8723),
    "jalandhar": (31.3260, 75.5762),
    "bathinda": (30.2110, 74.9455),
    "patiala": (30.3398, 76.3869),
    "sangrur": (30.2458, 75.8420),
    "firozpur": (30.9237, 74.6067),
    "gurdaspur": (32.0419, 75.4053),
    "hoshiarpur": (31.5273, 75.9149),
    "moga": (30.8165, 75.1717),
    "muktsar": (30.4762, 74.5122),
    "mansa": (29.9880, 75.3934),
    "kapurthala": (31.3800, 75.3800),
    "fatehgarh sahib": (30.6480, 76.3980),
    "rupnagar": (30.9700, 76.5300),
    "fazilka": (30.4030, 74.0280),
    "tarn taran": (31.4520, 74.9270),
    "barnala": (30.3819, 75.5463),
}


@dataclass
class WeatherData:
    """Current conditions and 48-hour outlook."""
    district: str
    latitude: float
    longitude: float
    temperature_c: float
    humidity_pct: int
    current_rain_mm: float
    current_wind_kmh: float
    total_rain_next_48h_mm: float
    max_rain_probability_48h: int
    max_wind_next_48h_kmh: float
    timestamp: float


@dataclass
class WeatherGateAssessment:
    """PAU agronomic rule assessment based on weather."""
    district: str
    rain_risk: str             # "none", "moderate", "high"
    wind_risk: str             # "safe", "advisory", "high_risk"
    irrigation_gate: str       # Actionable PAU guidance for irrigation
    fertilizer_gate: str       # Actionable PAU guidance for urea/fertilizer
    weather_summary_text: str  # Ready to inject into RAG context


class WeatherService:
    """
    Fetches real-time weather from Open-Meteo and applies PAU weather gates.
    Caches results per district for 30 minutes to stay fast and resilient.
    """

    def __init__(self, cache_ttl_seconds: int = 1800):
        self.cache_ttl = cache_ttl_seconds
        self._cache: Dict[str, Tuple[float, WeatherData]] = {}

    def resolve_district(self, query_or_district: Optional[str]) -> Tuple[str, float, float]:
        """Resolve district name and coordinates from text, default to Ludhiana."""
        if not query_or_district:
            return DEFAULT_DISTRICT, DEFAULT_LATITUDE, DEFAULT_LONGITUDE

        q_lower = query_or_district.lower()
        for district, (lat, lon) in PUNJAB_DISTRICTS.items():
            if district in q_lower:
                return district.capitalize(), lat, lon

        return DEFAULT_DISTRICT, DEFAULT_LATITUDE, DEFAULT_LONGITUDE

    def get_weather(self, district_name: Optional[str] = None) -> Optional[WeatherData]:
        """Fetch current weather + 48h forecast for a given Punjab district."""
        district, lat, lon = self.resolve_district(district_name)
        cache_key = district.lower()

        # Check cache
        now = time.time()
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if now - cached_time < self.cache_ttl:
                return cached_data

        params = {
            "latitude": lat,
            "longitude": lon,
            "current": ["temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m"],
            "hourly": ["precipitation", "precipitation_probability", "wind_speed_10m"],
            "forecast_days": 3,
            "timezone": "Asia/Kolkata",
        }

        try:
            response = requests.get(OPEN_METEO_BASE_URL, params=params, timeout=6)
            response.raise_for_status()
            data = response.json()

            current = data.get("current", {})
            hourly = data.get("hourly", {})

            # Slice next 48 hours
            precip_48h = hourly.get("precipitation", [])[:48]
            prob_48h = hourly.get("precipitation_probability", [])[:48]
            wind_48h = hourly.get("wind_speed_10m", [])[:48]

            total_rain = sum(p for p in precip_48h if p is not None)
            max_prob = max((p for p in prob_48h if p is not None), default=0)
            max_wind = max((w for w in wind_48h if w is not None), default=current.get("wind_speed_10m", 0.0))

            weather_data = WeatherData(
                district=district,
                latitude=lat,
                longitude=lon,
                temperature_c=float(current.get("temperature_2m", 25.0)),
                humidity_pct=int(current.get("relative_humidity_2m", 60)),
                current_rain_mm=float(current.get("precipitation", 0.0)),
                current_wind_kmh=float(current.get("wind_speed_10m", 5.0)),
                total_rain_next_48h_mm=round(total_rain, 1),
                max_rain_probability_48h=int(max_prob),
                max_wind_next_48h_kmh=round(max_wind, 1),
                timestamp=now,
            )

            # Store in cache
            self._cache[cache_key] = (now, weather_data)
            return weather_data

        except Exception as e:
            print(f"⚠️ WeatherService error for {district}: {e}. Using fallback values.")
            return WeatherData(
                district=district,
                latitude=lat,
                longitude=lon,
                temperature_c=25.0,
                humidity_pct=60,
                current_rain_mm=0.0,
                current_wind_kmh=5.0,
                total_rain_next_48h_mm=0.0,
                max_rain_probability_48h=0,
                max_wind_next_48h_kmh=8.0,
                timestamp=now,
            )

    def evaluate_gates(
        self,
        weather: WeatherData,
        crop: Optional[str] = None
    ) -> WeatherGateAssessment:
        """
        Apply PAU Weather-Gate agronomic rules:
        - Rain Gate: rain forecasted in next 48h -> halt irrigation & urea broadcast.
        - Wind Gate (PAU Wheat rule): wind > 12-15 km/h -> halt irrigation to prevent lodging.
        """
        # 1. Evaluate Rain Risk
        if weather.total_rain_next_48h_mm >= 10.0 or weather.max_rain_probability_48h >= 70:
            rain_risk = "high"
            rain_irrig_msg = (
                f"🌧️ PAU RAIN GATE (HIGH): Rain predicted in {weather.district} over next 48h "
                f"({weather.total_rain_next_48h_mm}mm expected, {weather.max_rain_probability_48h}% chance). "
                f"WITHHOLD all irrigation immediately to avoid waterlogging and groundwater waste."
            )
            rain_fert_msg = (
                f"⚠️ PAU FERTILIZER GATE: DO NOT apply or top-dress urea right now. "
                f"Rain will wash away nitrogen through runoff and cause severe leaching loss."
            )
        elif weather.total_rain_next_48h_mm >= 3.0 or weather.max_rain_probability_48h >= 40:
            rain_risk = "moderate"
            rain_irrig_msg = (
                f"⛅ PAU RAIN GATE (MODERATE): Light rain chance ({weather.max_rain_probability_48h}%, "
                f"~{weather.total_rain_next_48h_mm}mm) in {weather.district}. "
                f"Postpone irrigation for 24 hours until skies clear."
            )
            rain_fert_msg = (
                "⚠️ PAU FERTILIZER ADVISORY: Hold urea application until rain risk subsides."
            )
        else:
            rain_risk = "none"
            rain_irrig_msg = (
                f"☀️ PAU RAIN GATE (CLEAR): No significant rain expected in {weather.district} "
                f"(next 48h rain ~{weather.total_rain_next_48h_mm}mm). Irrigation may proceed as per crop schedule."
            )
            rain_fert_msg = (
                "✅ PAU FERTILIZER: Normal fertilization / urea schedule may proceed as per stage."
            )

        # 2. Evaluate Wind Risk (critical for Wheat lodging in Feb-March)
        if weather.max_wind_next_48h_kmh >= 15.0:
            wind_risk = "high_risk"
            wind_msg = (
                f"💨 PAU WIND GATE (DANGER): High surface wind gusts up to {weather.max_wind_next_48h_kmh} km/h "
                f"forecasted in {weather.district}. STRICT PAU RULE: DO NOT irrigate standing tall wheat "
                f"or heavy crops — wet root-zone under high wind causes fatal plant lodging (ਫਸਲ ਡਿੱਗਣਾ)."
            )
        elif weather.max_wind_next_48h_kmh >= 12.0:
            wind_risk = "advisory"
            wind_msg = (
                f"💨 PAU WIND GATE (ADVISORY): Moderate wind ({weather.max_wind_next_48h_kmh} km/h). "
                f"Irrigate only during calm morning/evening hours."
            )
        else:
            wind_risk = "safe"
            wind_msg = f"🍃 PAU WIND GATE (SAFE): Wind speeds calm ({weather.max_wind_next_48h_kmh} km/h)."

        # 3. Format Combined Context for LLM injection
        summary = (
            f"📍 REAL-TIME WEATHER FOR {weather.district.upper()} (Source: Open-Meteo):\n"
            f"• Current Temp: {weather.temperature_c}°C | Humidity: {weather.humidity_pct}%\n"
            f"• Current Wind: {weather.current_wind_kmh} km/h | 48h Max Wind: {weather.max_wind_next_48h_kmh} km/h\n"
            f"• 48h Rain Forecast: {weather.total_rain_next_48h_mm} mm (Rain probability: {weather.max_rain_probability_48h}%)\n"
            f"PAU WEATHER GATES TRIGGERED:\n"
            f"- Irrigation: {rain_irrig_msg}\n"
            f"- Wind Lodging Risk: {wind_msg}\n"
            f"- Fertilizer / Urea: {rain_fert_msg}"
        )

        return WeatherGateAssessment(
            district=weather.district,
            rain_risk=rain_risk,
            wind_risk=wind_risk,
            irrigation_gate=rain_irrig_msg,
            fertilizer_gate=rain_fert_msg,
            weather_summary_text=summary,
        )


if __name__ == "__main__":
    service = WeatherService()
    weather = service.get_weather("Ludhiana")
    gates = service.evaluate_gates(weather, crop="wheat")
    print("\n" + "=" * 60)
    print(gates.weather_summary_text)
    print("=" * 60)
