import json
import logging
import re
import subprocess
from pathlib import Path
from typing import List, Optional

import httpx

from ...types import EpisodeStream, Server, Subtitle
from ..types import HiAnimeSource

logger = logging.getLogger(__name__)

# The path to our Node.js decryption script, relative to this file.
DECRYPT_SCRIPT_PATH = Path(__file__).parent / "js" / "megacloud_decrypt.js"


class MegaCloudExtractor:
    """
    Extractor for MegaCloud streams.

    It works by:
    1. Fetching the embed page.
    2. Finding the encrypted sources data and the URL to a JavaScript file.
    3. Fetching the JavaScript file and using regex to find decryption keys.
    4. Calling an external Node.js script to perform the decryption.
    5. Parsing the decrypted result to get the final stream URLs.
    """

    def _run_node_script(self, encrypted_string: str, vars_json: str) -> Optional[dict]:
        """
        Executes the Node.js decryption script as a subprocess.

        Args:
            encrypted_string: The large encrypted sources string.
            vars_json: A JSON string of the array of indexes for key extraction.

        Returns:
            The decrypted data as a dictionary, or None on failure.
        """
        if not DECRYPT_SCRIPT_PATH.exists():
            logger.error(
                f"Node.js decryption script not found at: {DECRYPT_SCRIPT_PATH}"
            )
            return None

        command = ["node", str(DECRYPT_SCRIPT_PATH), encrypted_string, vars_json]

        try:
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                cwd=DECRYPT_SCRIPT_PATH.parent,  # Run from the 'js' directory
            )
            return json.loads(process.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"Node.js script failed with error: {e.stderr}")
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON output from Node.js script.")
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while running Node.js script: {e}"
            )

        return None

    def extract_vars_from_script(self, script_content: str) -> Optional[str]:
        """
        Uses regex to find the variable array needed for decryption from the script content.
        This pattern is based on the logic from the TypeScript project.
        """
        # This regex is a Python adaptation of the one in the TypeScript source.
        # It looks for the specific pattern that initializes the decryption keys.
        regex = r"case\s*0x[0-9a-f]+:(?![^;]*=partKey)\s*\w+\s*=\s*(\w+)\s*,\s*\w+\s*=\s*(\w+);"
        matches = re.findall(regex, script_content)

        if not matches:
            logger.error("Could not find decryption variables in the script.")
            return None

        def matching_key(value: str, script: str) -> Optional[str]:
            # This nested function replicates the `matchingKey` logic from the TS file.
            key_regex = re.compile(f",{value}=((?:0x)?([0-9a-fA-F]+))")
            match = key_regex.search(script)
            return match.group(1) if match else None

        vars_array = []
        for match in matches:
            try:
                key1_hex = matching_key(match[0], script_content)
                key2_hex = matching_key(match[1], script_content)
                if key1_hex and key2_hex:
                    vars_array.append([int(key1_hex, 16), int(key2_hex, 16)])
            except (ValueError, TypeError):
                logger.warning(
                    f"Could not parse hex values from script for match: {match}"
                )
                continue

        return json.dumps(vars_array) if vars_array else None

    def extract(self, embed_url: str) -> Optional[Server]:
        """
        Main extraction method.

        Args:
            embed_url: The URL of the MegaCloud embed page.

        Returns:
            A Server object containing stream links and subtitles.
        """
        try:
            with httpx.Client() as client:
                # 1. Get the embed page content
                embed_response = client.get(
                    embed_url, headers={"Referer": constants.HIANIME_BASE_URL}
                )
                embed_response.raise_for_status()
                embed_html = embed_response.text

                # 2. Find the encrypted sources and the script URL
                # The data is usually stored in a script tag as `var sources = [...]`.
                sources_match = re.search(r"var sources = ([^;]+);", embed_html)
                script_url_match = re.search(
                    r'src="(/js/player/a/prod/e1-player.min.js\?[^"]+)"', embed_html
                )

                if not sources_match or not script_url_match:
                    logger.error("Could not find sources or script URL in embed page.")
                    return None

                encrypted_sources_data = json.loads(sources_match.group(1))
                script_url = "https:" + script_url_match.group(1)

                encrypted_string = encrypted_sources_data.get("sources")
                if not isinstance(encrypted_string, str) or not encrypted_string:
                    logger.error("Encrypted sources string is missing or invalid.")
                    return None

                # 3. Fetch the script and extract decryption variables
                script_response = client.get(script_url)
                script_response.raise_for_status()
                vars_json = self.extract_vars_from_script(script_response.text)

                if not vars_json:
                    return None

                # 4. Decrypt using the Node.js script
                decrypted_data = self._run_node_script(encrypted_string, vars_json)
                if not decrypted_data or not isinstance(decrypted_data, list):
                    logger.error("Decryption failed or returned invalid data.")
                    return None

                # 5. Map to generic models
                streams = [
                    EpisodeStream(
                        link=source["file"], quality="auto", format=source["type"]
                    )
                    for source in decrypted_data
                ]

                subtitles = [
                    Subtitle(url=track["file"], language=track.get("label", "en"))
                    for track in encrypted_sources_data.get("tracks", [])
                    if track.get("kind") == "captions"
                ]

                return Server(
                    name="MegaCloud",
                    links=streams,
                    subtitles=subtitles,
                    headers={"Referer": "https://megacloud.tv/"},
                )

        except Exception as e:
            logger.error(f"MegaCloud extraction failed: {e}", exc_info=True)
            return None
