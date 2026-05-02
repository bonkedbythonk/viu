def generate_config_toml_from_app_model(*args, **kwargs) -> str:
    return """
  ▄▀█ █▄░█ █ █▀▀ ▄▀█ ▀█▀
  █▀█ █░▀█ █ █▄▄ █▀█ ░█░

[general]
provider = "animepahe"
selector = "fzf"
image_renderer = "icat"
manga_viewer = "icat"
hidden_categories = ["Planned", "Dropped", "Rewatching", "Paused"]
icons = true

[stream]
player = "iina"
quality = "1080"
translation_type = "sub"
auto_next = true
use_ipc = true

[anilist]
preferred_language = "english"
per_page = 15

[downloads]
downloads_dir = "~/Movies/anicat"

[fzf]
opts = "--layout=reverse --border=rounded --info=inline --ansi"
"""
