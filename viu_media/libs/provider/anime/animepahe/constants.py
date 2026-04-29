import re

ANIMEPAHE = "animepahe.pw"
ANIMEPAHE_BASE = f"https://{ANIMEPAHE}"
ANIMEPAHE_ENDPOINT = f"{ANIMEPAHE_BASE}/api"

SERVERS_AVAILABLE = ["kwik"]

KWIK_HOST = "kwik.cx"

REQUEST_HEADERS = {
    "Host": ANIMEPAHE,
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": ANIMEPAHE_BASE,
    "X-Requested-With": "XMLHttpRequest",
    "DNT": "1",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "TE": "trailers",
}

SERVER_HEADERS = {
    "Host": KWIK_HOST,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "DNT": "1",
    "Connection": "keep-alive",
    "Referer": f"{ANIMEPAHE_BASE}/",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "iframe",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Priority": "u=4",
    "TE": "trailers",
}

# Regex to extract the direct stream URL from decoded Kwik JS
JUICY_STREAM_REGEX = re.compile(r"source='(.*)';")

# Regex for the Kwik p,a,c,k,e,d decoder parameter extraction
KWIK_RE = re.compile(r"Player\|(.+?)'")
