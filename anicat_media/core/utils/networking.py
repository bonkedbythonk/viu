import os
import random
import re
from urllib.parse import unquote, urlparse

import httpx

TIMEOUT = 10


def random_user_agent():
    _USER_AGENT_TPL = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/%s Safari/537.36"
    _CHROME_VERSIONS = (
        "90.0.4430.212",
        "90.0.4430.24",
        "90.0.4430.70",
        "90.0.4430.72",
        "90.0.4430.85",
        "90.0.4430.93",
        "91.0.4472.101",
        "91.0.4472.106",
        "91.0.4472.114",
        "91.0.4472.124",
        "91.0.4472.164",
        "91.0.4472.19",
        "91.0.4472.77",
        "92.0.4515.107",
        "92.0.4515.115",
        "92.0.4515.131",
        "92.0.4515.159",
        "92.0.4515.43",
        "93.0.4556.0",
        "93.0.4577.15",
        "93.0.4577.63",
        "93.0.4577.82",
        "94.0.4606.41",
        "94.0.4606.54",
        "94.0.4606.61",
        "94.0.4606.71",
        "94.0.4606.81",
        "94.0.4606.85",
        "95.0.4638.17",
        "95.0.4638.50",
        "95.0.4638.54",
        "95.0.4638.69",
        "95.0.4638.74",
        "96.0.4664.18",
        "96.0.4664.45",
        "96.0.4664.55",
        "96.0.4664.93",
        "97.0.4692.20",
    )
    return _USER_AGENT_TPL % random.choice(_CHROME_VERSIONS)


def get_remote_filename(response: httpx.Response) -> str | None:
    """
    Extracts the filename from the Content-Disposition header or the URL.

    Args:
        response: The httpx.Response object.

    Returns:
        The extracted filename as a string, or None if not found.
    """
    content_disposition = response.headers.get("Content-Disposition")
    if content_disposition:
        filename_match = re.search(
            r"filename\*=(.+)", content_disposition, re.IGNORECASE
        )
        if filename_match:
            encoded_filename = filename_match.group(1).strip()
            try:
                if "''" in encoded_filename:
                    parts = encoded_filename.split("''", 1)
                    if len(parts) == 2:
                        return unquote(parts[1])
                return unquote(
                    encoded_filename
                )  # Fallback for simple URL-encoded parts
            except Exception:
                pass  # Fallback to filename or URL if decoding fails

        filename_match = re.search(
            r"filename=\"?([^\";]+)\"?", content_disposition, re.IGNORECASE
        )
        if filename_match:
            return unquote(filename_match.group(1).strip())

    parsed_url = urlparse(str(response.url))  # Convert httpx.URL to string for urlparse
    path = parsed_url.path
    if path:
        filename_from_url = os.path.basename(path)
        if filename_from_url:
            filename_from_url = filename_from_url.split("?")[0].split("#")[0]
            return unquote(filename_from_url)  # Unquote URL-encoded characters

    return None
