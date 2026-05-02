# GitHub Copilot Instructions for the anicat Repository

Hello, Copilot! This document provides instructions and context to help you understand the `anicat` codebase. Following these guidelines will help you generate code that is consistent, maintainable, and aligned with the project's architecture.

## 1. High-Level Project Goal

`anicat` is a command-line tool that brings the anime browsing, streaming, and management experience to the terminal. It integrates with metadata providers like AniList and scrapes streaming links from various anime provider websites. The core goals are efficiency, extensibility, and providing a powerful, scriptable user experience.

## 2. Core Architectural Concepts

The project follows a clean, layered architecture. When generating code, please adhere to this structure.

#### Layer 1: CLI (`anicat/cli`)
*   **Purpose:** Handles user interaction, command parsing, and displaying output.
*   **Key Libraries:** `click` for command structure, `rich` for styled output.
*   **Interactive Mode:** The interactive TUI is managed by the `Session` object in `anicat/cli/interactive/session.py`. It's a state machine where each menu is a function that returns the next `State` or an `InternalDirective` (like `BACK` or `EXIT`).
*   **Guideline:** **CLI files should not contain complex business logic.** They should parse arguments and delegate tasks to the Service Layer.

#### Layer 2: Service (`anicat/cli/service`)
*   **Purpose:** Contains the core application logic. Services act as orchestrators, connecting the CLI layer with the various library components.
*   **Examples:** `DownloadService`, `PlayerService`, `MediaRegistryService`, `WatchHistoryService`.
*   **Guideline:** When adding new functionality (e.g., a new way to manage downloads), it should likely be implemented in a service or an existing service should be extended. Services are the "brains" of the application.

#### Layer 3: Libraries (`anicat/libs`)
*   **Purpose:** A collection of independent, reusable modules with well-defined contracts (Abstract Base Classes).
*   **`media_api`:** Interfaces with metadata services like AniList. All new metadata clients **must** inherit from `BaseApiClient`.
*   **`provider`:** Interfaces with anime streaming websites. All new providers **must** inherit from `BaseAnimeProvider`.
*   **`player`:** Wrappers around external media players like MPV. All new players **must** inherit from `BasePlayer`.
*   **`selectors`:** Wrappers for interactive UI tools like FZF or Rofi. All new selectors **must** inherit from `BaseSelector`.
*   **Guideline:** Libraries should be self-contained and not depend on the CLI or Service layers. They receive configuration and perform their specific task.

#### Layer 4: Core (`anicat/core`)
*   **Purpose:** Foundational code shared across the entire application.
*   **`config`:** Pydantic models defining the application's configuration structure. **This is the single source of truth for all settings.**
*   **`downloader`:** The underlying logic for downloading files (using `yt-dlp` or `httpx`).
*   **`exceptions`:** Custom exception classes used throughout the project.
*   **`utils`:** Common, low-level utility functions.
*   **Guideline:** Code in `core` should be generic and have no dependencies on other layers except for other `core` modules.

## 3. Key Technologies
*   **Dependency Management:** `uv` is used for all package management and task running. Refer to `pyproject.toml` for dependencies.
*   **Configuration:** **Pydantic** is used exclusively. The entire configuration is defined in `anicat/core/config/model.py`.
*   **CLI Framework:** `click`. We use a custom `LazyGroup` to load commands on demand for faster startup.
*   **HTTP Client:** `httpx` is the standard for all network requests.

## 4. How to Add New Features

Follow these patterns to ensure your contributions fit the existing architecture.

### How to Add a New Provider
1.  **Create Directory:** Add a new folder in `anicat/libs/provider/anime/newprovider/`.
2.  **Implement `BaseAnimeProvider`:** In `provider.py`, create a class `NewProvider` that inherits from `BaseAnimeProvider` and implement the `search`, `get`, and `episode_streams` methods.
3.  **Create Mappers:** In `mappers.py`, write functions to convert the provider's API/HTML data into the generic Pydantic models from `anicat/libs/provider/anime/types.py` (e.g., `SearchResult`, `Anime`, `Server`).
4.  **Register Provider:**
    *   Add the provider's name to the `ProviderName` enum in `anicat/libs/provider/anime/types.py`.
    *   Add it to the `PROVIDERS_AVAILABLE` dictionary in `anicat/libs/provider/anime/provider.py`.

### How to Add a New Player
1.  **Create Directory:** Add a new folder in `anicat/libs/player/newplayer/`.
2.  **Implement `BasePlayer`:** In `player.py`, create a class `NewPlayer` that inherits from `BasePlayer` and implement the `play` method. It should call the player's executable via `subprocess`.
3.  **Add Configuration:** If the player has settings, add a `NewPlayerConfig` Pydantic model in `anicat/core/config/model.py`, and add it to the main `AppConfig`. Also add defaults and descriptions.
4.  **Register Player:** Add the player's name to the `PLAYERS` list and the factory logic in `anicat/libs/player/player.py`.

### How to Add a New Selector
1.  **Create Directory:** Add a new folder in `anicat/libs/selectors/newselector/`.
2.  **Implement `BaseSelector`:** In `selector.py`, create a class `NewSelector` that inherits from `BaseSelector` and implement `choose`, `confirm`, and `ask`.
3.  **Add Configuration:** If needed, add a `NewSelectorConfig` to `anicat/core/config/model.py`.
4.  **Register Selector:** Add the selector's name to the `SELECTORS` list and the factory logic in `anicat/libs/selectors/selector.py`. Update the `Literal` type hint for `selector` in `GeneralConfig`.

### How to Add a New CLI Command
*   **Top-Level Command (`anicat my-command`):**
    1.  Create `anicat/cli/commands/my_command.py` with your `click.command()`.
    2.  Register it in the `commands` dictionary in `anicat/cli/cli.py`.
*   **Subcommand (`anicat anilist my-subcommand`):**
    1.  Create `anicat/cli/commands/anilist/commands/my_subcommand.py`.
    2.  Register it in the `lazy_subcommands` dictionary of the parent `click.group()` (e.g., in `anicat/cli/commands/anilist/cmd.py`).

### How to Add a New Configuration Option
1.  **Add to Model:** Add the field to the appropriate Pydantic model in `anicat/core/config/model.py`.
2.  **Add Default:** Add a default value in `anicat/core/config/defaults.py`.
3.  **Add Description:** Add a user-friendly description in `anicat/core/config/descriptions.py`.
4.  The config loader and CLI option generation will handle the rest automatically.

## 5. Code Style and Conventions
*   **Style:** `ruff` for formatting, `ruff` for linting. The `pre-commit` hooks handle this.
*   **Types:** Full type hinting is mandatory. All code must pass `pyright`.
*   **Commits:** Adhere to the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) standard.
*   **Logging:** Use Python's `logging` module. Do not use `print()` for debugging or informational messages in library or service code.

## 6. Do's and Don'ts

*   ✅ **DO** use the abstract base classes (`BaseProvider`, `BasePlayer`, etc.) as contracts.
*   ✅ **DO** place business logic in the `service` layer.
*   ✅ **DO** use the Pydantic models in `anicat/core/config/model.py` as the single source of truth for configuration.
*   ✅ **DO** use the `Context` object in interactive menus to access services and configuration.

*   ❌ **DON'T** hardcode configuration values. Access them via the `config` object.
*   ❌ **DON'T** put complex logic directly into `click` command functions. Delegate to a service.
*   ❌ **DON'T** make direct `httpx` calls outside of a `provider` or `media_api` library.
*   ❌ **DON'T** introduce new dependencies without updating `pyproject.toml` and discussing it first.

