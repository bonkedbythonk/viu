import os
import pathlib
import re
import shlex
import shutil
import subprocess
import sys

from httpx import get
from rich import print
from rich.console import Console
from rich.markdown import Markdown

from ...core.constants import (
    AUTHOR,
    CLI_NAME_LOWER,
    GIT_REPO,
    PROJECT_NAME,
    __version__,
)

API_URL = f"https://api.{GIT_REPO}/repos/{AUTHOR}/{CLI_NAME_LOWER}/releases/latest"


def print_release_json(release_json):
    version = release_json.get("tag_name", "unknown")
    release_name = release_json.get("name", version)
    release_body = release_json.get("body", "No release notes available.")
    published_at = release_json.get("published_at", "unknown")

    console = Console()

    print(f"[bold cyan]Release: {release_name}[/]")
    print(f"[dim]Version: {version}[/]")
    print(f"[dim]Published: {published_at}[/]")
    print()

    # Display release notes as markdown if available
    if release_body and release_body.strip():
        markdown = Markdown(release_body)
        console.print(markdown)


def check_for_updates():
    USER_AGENT = f"{CLI_NAME_LOWER} user"
    try:
        response = get(
            API_URL,
            headers={
                "User-Agent": USER_AGENT,
                "X-GitHub-Api-Version": "2022-11-28",
                "Accept": "application/vnd.github+json",
            },
        )
    except Exception:
        print("You are not connected to the internet")
        return True, {}

    if response.status_code == 200:
        release_json = response.json()
        remote_tag = list(
            map(int, release_json["tag_name"].replace("v", "").split("."))
        )
        local_tag = list(map(int, __version__.replace("v", "").split(".")))
        if (
            (remote_tag[0] > local_tag[0])
            or (remote_tag[1] > local_tag[1] and remote_tag[0] == local_tag[0])
            or (
                remote_tag[2] > local_tag[2]
                and remote_tag[0] == local_tag[0]
                and remote_tag[1] == local_tag[1]
            )
        ):
            is_latest = False
        else:
            is_latest = True

        return (is_latest, release_json)
    else:
        print("Failed to check for updates")
        print(response.text)
        return (True, {})


def is_git_repo(author, repository):
    # Check if the current directory contains a .git folder
    git_dir = pathlib.Path(".git")
    if not git_dir.exists() or not git_dir.is_dir():
        return False

    # Check if the config file exists
    config_path = git_dir / "config"
    if not config_path.exists():
        return False

    try:
        # Read the .git/config file to find the remote repository URL
        with config_path.open("r") as git_config:
            git_config_content = git_config.read()
    except (FileNotFoundError, PermissionError):
        return False

    # Use regex to find the repository URL in the config file
    repo_name_pattern = r"url\s*=\s*.+/([^/]+/[^/]+)\.git"
    match = re.search(repo_name_pattern, git_config_content)

    # Return True if match found and repository name matches
    return bool(match) and match.group(1) == f"{author}/{repository}"


def update_app(force=False):
    is_latest, release_json = check_for_updates()
    if is_latest and not force:
        print("[green]App is up to date[/]")
        return False, release_json
    tag_name = release_json["tag_name"]

    print("[cyan]Updating app to version %s[/]" % tag_name)
    if os.path.exists("/nix/store") and os.path.exists("/run/current-system"):
        NIX = shutil.which("nix")
        if not NIX:
            print("[red]Cannot find nix, it looks like your system is broken.[/]")
            return False, release_json

        process = subprocess.run(
            [NIX, "profile", "upgrade", CLI_NAME_LOWER], check=False
        )
    elif is_git_repo(AUTHOR, CLI_NAME_LOWER):
        GIT_EXECUTABLE = shutil.which("git")
        args = [
            GIT_EXECUTABLE,
            "pull",
        ]

        print(f"Pulling latest changes from the repository via git: {shlex.join(args)}")

        if not GIT_EXECUTABLE:
            print("[red]Cannot find git please install it.[/]")
            return False, release_json

        process = subprocess.run(
            args,
            check=False,
        )

    elif UV := shutil.which("uv"):
        process = subprocess.run([UV, "tool", "upgrade", PROJECT_NAME], check=False)
    elif PIPX := shutil.which("pipx"):
        process = subprocess.run([PIPX, "upgrade", PROJECT_NAME], check=False)
    else:
        PYTHON_EXECUTABLE = sys.executable

        args = [
            PYTHON_EXECUTABLE,
            "-m",
            "pip",
            "install",
            PROJECT_NAME,
            "-U",
            "--no-warn-script-location",
        ]
        if sys.prefix == sys.base_prefix:
            # ensure NOT in a venv, where --user flag can cause an error.
            # TODO: Get value of 'include-system-site-packages' in pyenv.cfg.
            args.append("--user")

        process = subprocess.run(args, check=False)
    if process.returncode == 0:
        print(
            "[green]Its recommended to run the following after updating:\n\tanicat config --update (to get the latest config docs)\n\tanicat cache --clean (to get rid of any potential issues)[/]",
            file=sys.stderr,
        )
        return True, release_json
    else:
        return False, release_json
