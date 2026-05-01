# viu_media/cli/config/generate.py
import itertools
import json
import textwrap
from enum import Enum
from pathlib import Path
from typing import Any, Literal, get_args, get_origin

from pydantic.fields import ComputedFieldInfo, FieldInfo
from pydantic_core import PydanticUndefined

from ...core.config import AppConfig
from ...core.constants import (
    APP_ASCII_ART,
    CLI_NAME,
    DISCORD_INVITE,
    REPO_HOME,
    SUPPORT_PROJECT_URL,
)

# The header for the config file.
config_asci = "\n".join(
    [f"# {line}" for line in APP_ASCII_ART.read_text(encoding="utf-8").split()]
)
CONFIG_HEADER = f"""
# ==============================================================================
#
{config_asci}
#
# ==============================================================================
# This is the Viu configuration file. It uses the TOML format.
# You can modify these values to customize the behavior of Viu.
# For more information on the available options, please refer to the
# official documentation on GitHub.
# ==============================================================================
""".lstrip()

CONFIG_FOOTER = f"""
# ==============================================================================
#
# HOPE YOU ENJOY {CLI_NAME} AND BE SURE TO STAR THE PROJECT ON GITHUB
# {REPO_HOME}
#
# Also join the discord server
# where the anime tech community lives :)
# {DISCORD_INVITE}
# If you like the project and are able to support it please consider buying me a coffee at {SUPPORT_PROJECT_URL}.
# If you would like to connect with me join the discord server from there you can dm for hackathons, or even to tell me a joke 😂
# Otherwise enjoy your terminal anime browser experience 😁
#
# ==============================================================================
""".lstrip()


def generate_config_toml_from_app_model(app_model: AppConfig) -> str:
    """Generate a clean, minimal TOML configuration file content."""

    minimal_toml = f"""{CONFIG_HEADER}

[general]
welcome_screen = true
icons = true
api_client = "anilist"
provider = "allanime"
manga_viewer = "icat"

[stream]
player = "iina"
quality = "1080"
translation_type = "sub"
server = "TOP"
auto_next = false
continue_from_watch_history = true

[downloads]
downloader = "auto"
enable_tracking = true
max_concurrent = 3

[anilist]
# Add your AniList token below to enable tracking and sync features
# token = "YOUR_TOKEN_HERE"
preferred_language = "english"

[fzf]
header_color = "95,135,175"

{CONFIG_FOOTER}"""
    return minimal_toml


def _format_toml_value(value: Any) -> str:
    """
    Manually formats a Python value into a TOML-compliant string.
    This avoids needing an external TOML writer dependency.
    """
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, Enum):
        return f'"{value.value}"'

    # Handle strings and Paths, differentiating between single and multi-line
    if isinstance(value, (str, Path)):
        str_val = str(value)
        if "\n" in str_val:
            # For multi-line strings, use triple quotes.
            # Also, escape any triple quotes that might be in the string itself.
            escaped_val = str_val.replace('"""', '\\"\\"\\"')
            return f'"""\n{escaped_val}"""'
        else:
            # For single-line strings, use double quotes and escape relevant characters.
            escaped_val = str_val.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped_val}"'

    # Fallback for any other types
    return f'"{str(value)}"'


def _get_field_type_comment(field_info: FieldInfo | ComputedFieldInfo) -> str:
    """Generate a comment with type information for a field."""
    field_type = (
        field_info.annotation
        if isinstance(field_info, FieldInfo)
        else field_info.return_type
    )

    possible_values = []
    if field_type is not None:
        if isinstance(field_type, type) and issubclass(field_type, Enum):
            possible_values = [member.value for member in field_type]
        elif hasattr(field_type, "__origin__") and get_origin(field_type) is Literal:
            args = get_args(field_type)
            if args:
                possible_values = list(args)

    if possible_values:
        formatted_values = ", ".join(json.dumps(v) for v in possible_values)
        return f"Possible values: [ {formatted_values} ]"
    type_name = _get_type_name(field_type)
    range_info = _get_range_info(field_info)

    if range_info:
        return f"Type: {type_name} ({range_info})"
    elif type_name:
        return f"Type: {type_name}"

    return ""


def _get_type_name(field_type: Any) -> str:
    """Get a user-friendly name for a field's type."""
    if field_type is str:
        return "string"
    if field_type is int:
        return "integer"
    if field_type is float:
        return "float"
    if field_type is bool:
        return "boolean"
    if field_type is Path:
        return "path"
    return ""


def _get_range_info(field_info: FieldInfo | ComputedFieldInfo) -> str:
    """Get a string describing the numeric range of a field."""
    constraints = {}
    if (
        isinstance(field_info, FieldInfo)
        and hasattr(field_info, "metadata")
        and field_info.metadata
    ):
        for constraint in field_info.metadata:
            constraint_type = type(constraint).__name__
            if constraint_type == "Ge" and hasattr(constraint, "ge"):
                constraints["min"] = constraint.ge
            elif constraint_type == "Le" and hasattr(constraint, "le"):
                constraints["max"] = constraint.le
            elif constraint_type == "Gt" and hasattr(constraint, "gt"):
                constraints["min"] = constraint.gt + 1
            elif constraint_type == "Lt" and hasattr(constraint, "lt"):
                constraints["max"] = constraint.lt - 1

    if constraints:
        min_val = constraints.get("min", "N/A")
        max_val = constraints.get("max", "N/A")
        return f"Range: {min_val}-{max_val}"

    return ""
