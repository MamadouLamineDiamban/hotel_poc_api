# amadeus_list_by_city_df.py
"""
Fonctions minimalistes et robustes pour:
1) Obtenir un token sandbox Amadeus
2) Lister des hôtels par code ville (IATA) via Hotel List (by-city)
3) Convertir la réponse en DataFrame pandas
"""

from __future__ import annotations
import os, time, httpx, pandas as pd
from dotenv import load_dotenv

AUTH_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
LIST_BY_CITY_URL = "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city"

load_dotenv()

def _post(url: str, data: dict, timeout: int = 20) -> httpx.Response:
    last_exc = None
    for attempt in range(3):
        try:
            return httpx.post(
                url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
                timeout=timeout,
            )
        except httpx.HTTPError as e:
            last_exc = e
            time.sleep(0.5 * (attempt + 1))
    raise last_exc

def _get(url: str, headers: dict, params: dict, timeout: int = 30) -> httpx.Response:
    last_exc = None
    for attempt in range(3):
        try:
            return httpx.get(url, headers=headers, params=params, timeout=timeout)
        except httpx.HTTPError as e:
            last_exc = e
            time.sleep(0.5 * (attempt + 1))
    raise last_exc

def get_token() -> str:
    client_id = os.getenv("AMADEUS_CLIENT_ID")
    client_secret = os.getenv("AMADEUS_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError("AMADEUS_CLIENT_ID / AMADEUS_CLIENT_SECRET manquants dans .env")

    resp = _post(AUTH_URL, {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    })
    resp.raise_for_status()
    token = resp.json().get("access_token")
    if not token:
        raise RuntimeError("Token introuvable dans la réponse OAuth.")
    return token

def list_hotels_by_city(token: str, city_code: str) -> list[dict]:
    if not city_code or len(city_code) != 3:
        raise ValueError("city_code doit être un code IATA à 3 lettres (ex: 'PAR').")
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    params = {"cityCode": city_code.upper()}

    resp = _get(LIST_BY_CITY_URL, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json().get("data", [])

def hotels_to_dataframe(hotels: list[dict]) -> pd.DataFrame:
    """Aplatis quelques champs utiles dans un DataFrame."""
    rows = []
    for h in hotels:
        addr = h.get("address") or {}
        geo = h.get("geoCode") or {}
        rows.append({
            "hotelId": h.get("hotelId"),
            "name": h.get("name"),
            "chainCode": h.get("chainCode"),
            "city": addr.get("cityName"),
            "country": addr.get("countryCode"),
            "postalCode": addr.get("postalCode"),
            "latitude": geo.get("latitude"),
            "longitude": geo.get("longitude"),
        })
    return pd.DataFrame(rows)

if __name__ == "__main__":
    tok = get_token()
    hotels = list_hotels_by_city(tok, "PAR")
    df = hotels_to_dataframe(hotels)
    print(df.head(10))
