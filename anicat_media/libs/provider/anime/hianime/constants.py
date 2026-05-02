# The base domain for HiAnime.
HIANIME_DOMAIN = "hianime.to"
HIANIME_BASE_URL = f"https://{HIANIME_DOMAIN}"

# The endpoint for making AJAX requests (fetching episodes, servers, etc.).
HIANIME_AJAX_URL = f"{HIANIME_BASE_URL}/ajax"

# The base URL for search queries.
SEARCH_URL = f"{HIANIME_BASE_URL}/search"

# The Referer header is crucial for making successful requests to the AJAX endpoints.
AJAX_REFERER_HEADER = f"{HIANIME_BASE_URL}/"
