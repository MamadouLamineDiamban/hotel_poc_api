import os, httpx
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID")
CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")

def get_token():
    r = httpx.post(
        "https://test.api.amadeus.com/v1/security/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        timeout=20,
    )
    r.raise_for_status()
    return r.json()["access_token"]

def search_hotels(token):
    url = "https://test.api.amadeus.com/v3/shopping/hotel-offers"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "cityCode": "PAR",
        "checkInDate": "2025-11-01",
        "checkOutDate": "2025-11-03",
        "adults": 2,
        "currency": "EUR",
        "page[limit]": 5,
    }
    r = httpx.get(url, headers=headers, params=params, timeout=30)
    print("Status:", r.status_code)
    print(r.text[:400])   # pour debug : début du payload
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    token = get_token()
    data = search_hotels(token)
