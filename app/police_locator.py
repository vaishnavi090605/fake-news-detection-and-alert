"""
Police Locator Module — TruthGuard AI
Finds the nearest police station based on the user's voluntary/detected location
and manages the repeated fake news threshold (> 3 strikes).
Supports real GPS coordinate calculation via Haversine distance.
"""

import math
import re

POLICE_STATIONS = [
    {
        "keywords": ["anurag", "ghatkesar", "venkatapur", "medchal", "pocharam", "korremula", "peerzadiguda"],
        "name": "Ghatkesar Police Station & Cyber Monitoring Cell",
        "commissionerate": "Rachakonda Police Commissionerate",
        "address": "Ghatkesar Main Road, Near Anurag University, Hyderabad, Telangana 501301",
        "distance": "2.4 km from Anurag University Campus",
        "lat": 17.4475,
        "lon": 78.6833,
        "sho_officer": "Station House Officer (SHO), Ghatkesar PS",
        "phone": "+91-40-27853400 / Dial 100",
        "cyber_helpline": "1930",
        "email": "bachuvaishnavi098@gmail.com",
        "maps_link": "https://maps.google.com/?q=Ghatkesar+Police+Station+Hyderabad",
    },
    {
        "keywords": ["uppal", "boduppal", "habsiguda", "ramanathapur", "nacharam", "mallapur"],
        "name": "Uppal Police Station & Cyber Cell",
        "commissionerate": "Rachakonda Police Commissionerate",
        "address": "Uppal Ring Road, Hyderabad, Telangana 500039",
        "distance": "7.5 km",
        "lat": 17.4018,
        "lon": 78.5602,
        "sho_officer": "Inspector of Police, Uppal PS",
        "phone": "+91-40-27853420 / Dial 100",
        "cyber_helpline": "1930",
        "email": "bachuvaishnavi098@gmail.com",
        "maps_link": "https://maps.google.com/?q=Uppal+Police+Station+Hyderabad",
    },
    {
        "keywords": ["hitec", "madhapur", "gachibowli", "kondapur", "cyberabad", "raidurgam", "kukatpally", "miyapur"],
        "name": "Madhapur Cyber Crime Police Station",
        "commissionerate": "Cyberabad Police Commissionerate",
        "address": "Cyberabad Police Commissionerate Complex, Gachibowli, Hyderabad 500032",
        "distance": "12.0 km",
        "lat": 17.4399,
        "lon": 78.3685,
        "sho_officer": "Assistant Commissioner of Police (Cyber Crime)",
        "phone": "+91-40-27852400 / Dial 100",
        "cyber_helpline": "1930",
        "email": "bachuvaishnavi098@gmail.com",
        "maps_link": "https://maps.google.com/?q=Cyberabad+Police+Commissionerate+Hyderabad",
    },
    {
        "keywords": ["hyderabad", "secunderabad", "telangana", "begumpet", "charminar", "banjara", "jubilee", "punjagutta", "abids"],
        "name": "Central Cyber Crime Police Station, Hyderabad City",
        "commissionerate": "Hyderabad City Police Commissionerate",
        "address": "CCRB Complex, Basheerbagh, Hyderabad, Telangana 500029",
        "distance": "15.0 km",
        "lat": 17.4024,
        "lon": 78.4767,
        "sho_officer": "DCP Cyber Crimes, Hyderabad",
        "phone": "+91-40-27852435 / Dial 100",
        "cyber_helpline": "1930",
        "email": "bachuvaishnavi098@gmail.com",
        "maps_link": "https://maps.google.com/?q=Basheerbagh+Police+Headquarters+Hyderabad",
    },
]

DEFAULT_STATION = POLICE_STATIONS[0]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance in kilometers between two GPS coordinates."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


def find_nearest_police_station(location_str: str | None = None) -> dict:
    """
    Finds the closest police station either through real GPS coordinate computation
    (Haversine formula) or keyword location matching.
    """
    if not location_str:
        return DEFAULT_STATION.copy()

    # 1. Try to extract real GPS coordinates (e.g. "GPS: 17.4475, 78.6833" or "17.4475, 78.6833")
    gps_match = re.search(r"[-+]?\b(\d{1,2}\.\d+)[,\s]+([-+]?\d{1,3}\.\d+)\b", location_str)
    if gps_match:
        try:
            user_lat = float(gps_match.group(1))
            user_lon = float(gps_match.group(2))

            best_station = None
            min_dist = float("inf")

            for station in POLICE_STATIONS:
                dist = haversine_km(user_lat, user_lon, station["lat"], station["lon"])
                if dist < min_dist:
                    min_dist = dist
                    best_station = station

            if best_station:
                res = best_station.copy()
                res["distance"] = f"{min_dist} km (Calculated from real device GPS)"
                res["maps_link"] = (
                    f"https://www.google.com/maps/dir/?api=1&origin={user_lat},{user_lon}&destination={best_station['lat']},{best_station['lon']}"
                )
                return res
        except Exception:
            pass

    # 2. Fall back to keyword matching
    loc_lower = location_str.lower().strip()
    for station in POLICE_STATIONS:
        for kw in station["keywords"]:
            if kw in loc_lower:
                return station.copy()

    return DEFAULT_STATION.copy()
