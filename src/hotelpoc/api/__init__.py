"""
hotelpoc
========
Package maison pour explorer les APIs hôtelières (Amadeus, Expedia…).

Structure :
- hotelpoc.api     → appels aux APIs (ex: get_token, search_hotel_offers)
- hotelpoc.utils   → utilitaires (logging, dates, transforms)
- hotelpoc.storage → (plus tard) gestion BDD
"""

__version__ = "0.1.0"

# Exposer les fonctions principales directement au niveau top-level
from .api.amadeus import get_token, search_hotel_offers

__all__ = [
    "__version__",
    "get_token",
    "search_hotel_offers",
]
