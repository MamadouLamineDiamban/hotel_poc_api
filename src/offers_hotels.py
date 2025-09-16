# hotel_offers_all_per_hotel.py
from __future__ import annotations
import os
from datetime import date, timedelta
from typing import List, Dict, Any
import httpx
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

AUTH_URL   = "https://test.api.amadeus.com/v1/security/oauth2/token"
OFFERS_URL = "https://test.api.amadeus.com/v3/shopping/hotel-offers"

def get_token() -> str:
    r = httpx.post(
        AUTH_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": os.getenv("AMADEUS_CLIENT_ID"),
            "client_secret": os.getenv("AMADEUS_CLIENT_SECRET"),
        },
        headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        timeout=20,
    )
    r.raise_for_status()
    tok = r.json().get("access_token")
    if not tok:
        raise RuntimeError("Token introuvable")
    return tok

def get_offers_all(token: str, hotel_ids: List[str], checkin: str, checkout: str, adults: int = 2, lang: str = "FR") -> List[Dict[str, Any]]:
    """Récupère toutes les offres renvoyées par v3 pour les IDs fournis (sans tronquer côté client)."""
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    params = {
        "hotelIds": ",".join(hotel_ids),
        "adults": str(adults),
        "roomQuantity": "1",
        "checkInDate": checkin,
        "checkOutDate": checkout,
        "currency": "EUR",
        "lang": lang,  # descriptions FR si dispo
        # Si besoin, tu peux ajouter "page[limit]" et "page[offset]" si Amadeus te retourne beaucoup de résultats.
    }
    r = httpx.get(OFFERS_URL, headers=headers, params=params, timeout=60)
    if r.status_code >= 400:
        print("OFFERS ERROR:", r.status_code, r.text[:400])
    r.raise_for_status()
    return r.json().get("data", []) or []

def offers_to_df(items: List[Dict[str, Any]]) -> pd.DataFrame:
    """1 ligne = 1 offre; on garde les champs clés (prix, chambre, board, paymentType, annulation)."""
    from datetime import date as _d
    rows = []
    for it in items:
        h = it.get("hotel") or {}
        hid = h.get("hotelId")
        hname = h.get("name")
        city = h.get("cityCode")
        lat = h.get("latitude"); lon = h.get("longitude")

        for of in it.get("offers") or []:
            price = (of.get("price") or {})
            total = price.get("total"); cur = price.get("currency")
            ci = of.get("checkInDate"); co = of.get("checkOutDate")

            # prix / nuit
            nights = nightly = None
            try:
                d0 = _d.fromisoformat(ci); d1 = _d.fromisoformat(co)
                nights = max((d1 - d0).days, 1)
                nightly = round(float(total)/nights, 2) if total else None
            except Exception:
                pass

            room = of.get("room") or {}
            t_est = room.get("typeEstimated") or {}
            room_desc = (room.get("description") or {}).get("text")
            board = of.get("boardType")  # ex: ROOM_ONLY, BREAKFAST, HALF_BOARD...

            # pas de nom d’OTA : mais on a le mode de paiement
            payment = of.get("paymentType")  # ex: PAY_AT_HOTEL / PREPAID

            # un petit résumé d’annulation (si dispo)
            policies = (of.get("policies") or {}).get("cancellations") or []
            cancel_summary = None
            if policies:
                # on prend la première règle comme résumé
                p0 = policies[0]
                cancel_summary = f"{p0.get('description', {}).get('text', '')}".strip() or str(p0)[:140]

            rows.append({
                # Prix d'abord
                "price_total": float(total) if total else None,
                "currency": cur,
                "price_per_night": nightly,
                "nights": nights,

                # Hôtel
                "hotelId": hid,
                "hotel_name": hname,
                "city": city,
                "latitude": lat,
                "longitude": lon,

                # Séjour
                "checkIn": ci,
                "checkOut": co,

                # Offre / chambre
                "offerId": of.get("id"),
                "room_type": room.get("type"),
                "room_category": t_est.get("category"),
                "room_beds": t_est.get("beds"),
                "bed_type": t_est.get("bedType"),
                "room_desc": room_desc,
                "boardType": board,
                "paymentType": payment,
                "cancel_policy": cancel_summary,
                # Pas de champ "site/OTA" dans la réponse Self-Service.
            })
    return pd.DataFrame(rows)

if __name__ == "__main__":
    token = get_token()

    ci = (date.today() + timedelta(days=20)).isoformat()
    co = (date.today() + timedelta(days=22)).isoformat()

    # prends 3–10 hotelIds qui renvoient des offres en sandbox
    hotel_ids = ["ARNCEACH", "BWNCE645", "MDNCEMER"]

    items = get_offers_all(token, hotel_ids, ci, co, adults=2, lang="FR")
    df = offers_to_df(items)

    pd.set_option("display.max_columns", None)
    print(df.head(20))
    # df.to_csv("all_offers_per_hotel.csv", index=False)
