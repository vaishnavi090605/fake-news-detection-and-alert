"""
Police Locator Module — TruthGuard AI
Finds the nearest police station based on the user's voluntary/detected location
and manages the repeated fake news threshold (> 3 strikes).
"""

POLICE_STATIONS = [
    {
        "keywords": ["anurag", "ghatkesar", "venkatapur", "medchal", "pocharam", "korremula"],
        "name": "Ghatkesar Police Station & Cyber Monitoring Cell",
        "commissionerate": "Rachakonda Police Commissionerate",
        "address": "Ghatkesar Main Road, Near Anurag University, Hyderabad, Telangana 501301",
        "distance": "2.4 km from Anurag University Campus",
        "sho_officer": "Station House Officer (SHO), Ghatkesar PS",
        "phone": "+91-40-27853400 / Dial 100",
        "cyber_helpline": "1930",
        "email": "bachuvaishnavi098@gmail.com",
        "maps_link": "https://maps.google.com/?q=Ghatkesar+Police+Station+Hyderabad",
    },
    {
        "keywords": ["uppal", "boduppal", "habsiguda", "ramanathapur", "nacharam"],
        "name": "Uppal Police Station & Cyber Cell",
        "commissionerate": "Rachakonda Police Commissionerate",
        "address": "Uppal Ring Road, Hyderabad, Telangana 500039",
        "distance": "7.5 km",
        "sho_officer": "Inspector of Police, Uppal PS",
        "phone": "+91-40-27853420 / Dial 100",
        "cyber_helpline": "1930",
        "email": "bachuvaishnavi098@gmail.com",
        "maps_link": "https://maps.google.com/?q=Uppal+Police+Station+Hyderabad",
    },
    {
        "keywords": ["hitec", "madhapur", "gachibowli", "kondapur", "cyberabad", "raidurgam"],
        "name": "Madhapur Cyber Crime Police Station",
        "commissionerate": "Cyberabad Police Commissionerate",
        "address": "Cyberabad Police Commissionerate Complex, Gachibowli, Hyderabad 500032",
        "distance": "12.0 km",
        "sho_officer": "Assistant Commissioner of Police (Cyber Crime)",
        "phone": "+91-40-27852400 / Dial 100",
        "cyber_helpline": "1930",
        "email": "bachuvaishnavi098@gmail.com",
        "maps_link": "https://maps.google.com/?q=Cyberabad+Police+Commissionerate+Hyderabad",
    },
    {
        "keywords": ["hyderabad", "secunderabad", "telangana", "begumpet", "charminar", "banjara"],
        "name": "Central Cyber Crime Police Station, Hyderabad City",
        "commissionerate": "Hyderabad City Police Commissionerate",
        "address": "CCRB Complex, Basheerbagh, Hyderabad, Telangana 500029",
        "distance": "15.0 km",
        "sho_officer": "DCP Cyber Crimes, Hyderabad",
        "phone": "+91-40-27852435 / Dial 100",
        "cyber_helpline": "1930",
        "email": "bachuvaishnavi098@gmail.com",
        "maps_link": "https://maps.google.com/?q=Basheerbagh+Police+Headquarters+Hyderabad",
    },
]

DEFAULT_STATION = POLICE_STATIONS[0]


def find_nearest_police_station(location_str: str | None = None) -> dict:
    """Matches the user location string against known stations or returns default Anurag/Ghatkesar PS."""
    if not location_str:
        return DEFAULT_STATION

    loc_lower = location_str.lower().strip()
    for station in POLICE_STATIONS:
        for kw in station["keywords"]:
            if kw in loc_lower:
                return station

    return DEFAULT_STATION
