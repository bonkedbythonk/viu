"""
Registry clean command - clean up orphaned entries and invalid data
"""

import json
from typing import Dict, List

import click
from rich.console import Console
from rich.table import Table

from .....core.config import AppConfig
from ....service.feedback import FeedbackService
from ....service.registry.service import MediaRegistryService


@click.command(help="Clean up orphaned entries and invalid data from registry")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be cleaned without making changes"
)
@click.option(
    "--orphaned",
    is_flag=True,
    help="Remove orphaned media records (index entries without files)",
)
@click.option("--invalid", is_flag=True, help="Remove invalid or corrupted entries")
@click.option("--duplicates", is_flag=True, help="Remove duplicate entries")
@click.option(
    "--old-format", is_flag=True, help="Clean entries from old registry format versions"
)
@click.option(
    "--force", "-f", is_flag=True, help="Force cleanup without confirmation prompts"
)
@click.option(
    "--api",
    default="anilist",
    type=click.Choice(["anilist"], case_sensitive=False),
    help="Media API registry to clean",
)
@click.pass_obj
def clean(
    config: AppConfig,
    dry_run: bool,
    orphaned: bool,
    invalid: bool,
    duplicates: bool,
    old_format: bool,
    force: bool,
    api: str,
):
    """
    Clean up your local media registry.

    Can remove orphaned entries, invalid data, duplicates, and entries
    from old format versions. Use --dry-run to preview changes.
    """
    feedback = FeedbackService(config)
    console = Console()

    # Default to all cleanup types if none specified
    if not any([orphaned, invalid, duplicates, old_format]):
        orphaned = invalid = duplicates = old_format = True

    try:
        registry_service = MediaRegistryService(api, config.media_registry)

        cleanup_results: Dict[str, List] = {
            "orphaned": [],
            "invalid": [],
            "duplicates": [],
            "old_format": [],
        }

        # Analyze registry for cleanup opportunities
        with feedback.progress("Analyzing registry..."):
            _analyze_registry(
                registry_service,
                cleanup_results,
                orphaned,
                invalid,
                duplicates,
                old_format,
            )

        # Show cleanup summary
        _display_cleanup_summary(console, cleanup_results, config.general.icons)

        total_items = sum(len(items) for items in cleanup_results.values())
        if total_items == 0:
            feedback.success(
                "Registry Clean", "No cleanup needed - registry is already clean!"
            )
            return

        if not dry_run:
            if not force and not click.confirm(
                f"Clean up {total_items} items from registry?"
            ):
                feedback.info("Cleanup Cancelled", "No changes were made")
                return

            # Perform cleanup
            _perform_cleanup(registry_service, cleanup_results, feedback)
        else:
            feedback.info("Dry Run Complete", f"Would clean up {total_items} items")

    except Exception as e:
        feedback.error("Cleanup Error", f"Failed to clean registry: {e}")
        raise click.Abort()


def _analyze_registry(
    registry_service: MediaRegistryService,
    results: Dict[str, List],
    check_orphaned: bool,
    check_invalid: bool,
    check_duplicates: bool,
    check_old_format: bool,
):
    """Analyze registry for cleanup opportunities."""
    if check_orphaned:
        results["orphaned"] = _find_orphaned_entries(registry_service)
    if check_invalid:
        results["invalid"] = _find_invalid_entries(registry_service)
    if check_duplicates:
        results["duplicates"] = _find_duplicate_entries(registry_service)
    if check_old_format:
        results["old_format"] = _find_old_format_entries(registry_service)


def _find_orphaned_entries(registry_service: MediaRegistryService) -> list:
    """Find index entries that don't have corresponding media files."""
    orphaned = []
    index = registry_service._load_index()
    for entry_key, entry in index.media_index.items():
        media_file = registry_service._get_media_file_path(entry.media_id)
        if not media_file.exists():
            orphaned.append(
                {"id": entry.media_id, "key": entry_key, "reason": "Media file missing"}
            )
    return orphaned


def _find_invalid_entries(registry_service: MediaRegistryService) -> list:
    """Find invalid or corrupted entries."""
    invalid = []
    for media_file in registry_service.media_registry_dir.glob("*.json"):
        try:
            media_id = int(media_file.stem)
            record = registry_service.get_media_record(media_id)
            if (
                not record
                or not record.media_item
                or not record.media_item.title.english
                and not record.media_item.title.romaji
            ):
                invalid.append(
                    {
                        "id": media_id,
                        "file": media_file,
                        "reason": "Invalid record structure or missing title",
                    }
                )
        except (ValueError, json.JSONDecodeError) as e:
            invalid.append(
                {
                    "id": media_file.stem,
                    "file": media_file,
                    "reason": f"File corruption: {e}",
                }
            )
    return invalid


def _find_duplicate_entries(registry_service: MediaRegistryService) -> list:
    """Find duplicate entries (same media ID appearing multiple times)."""
    duplicates = []
    seen_ids = set()
    index = registry_service._load_index()
    for entry_key, entry in index.media_index.items():
        if entry.media_id in seen_ids:
            duplicates.append(
                {
                    "id": entry.media_id,
                    "key": entry_key,
                    "reason": "Duplicate media ID in index",
                }
            )
        else:
            seen_ids.add(entry.media_id)
    return duplicates


def _find_old_format_entries(registry_service: MediaRegistryService) -> list:
    """Find entries from old registry format versions."""
    from ....service.registry.service import REGISTRY_VERSION

    old_format = []
    index = registry_service._load_index()
    if index.version != REGISTRY_VERSION:
        old_format.append(
            {
                "id": "index",
                "file": registry_service._index_file,
                "reason": f"Index version mismatch ({index.version})",
            }
        )
    return old_format


def _display_cleanup_summary(console: Console, results: Dict[str, List], icons: bool):
    """Display summary of cleanup opportunities."""
    table = Table(title=f"{'🧹 ' if icons else ''}Registry Cleanup Summary")
    table.add_column("Category", style="cyan", no_wrap=True)
    table.add_column("Count", style="magenta", justify="right")
    table.add_column("Description", style="white")

    categories = {
        "orphaned": "Orphaned Entries",
        "invalid": "Invalid/Corrupt Entries",
        "duplicates": "Duplicate Entries",
        "old_format": "Outdated Format",
    }
    for category, display_name in categories.items():
        count = len(results[category])
        description = "None found"
        if count > 0:
            reasons = {item["reason"] for item in results[category][:3]}
            description = "; ".join(list(reasons)[:2])
            if len(reasons) > 2:
                description += "..."
        table.add_row(display_name, str(count), description)
    console.print(table)
    console.print()


def _perform_cleanup(
    registry_service: MediaRegistryService,
    results: Dict[str, List],
    feedback: FeedbackService,
):
    """Perform the actual cleanup operations."""
    cleaned_count = 0
    total_to_clean = sum(len(v) for v in results.values())

    with feedback.progress("Cleaning registry...", total=total_to_clean) as (
        task_id,
        progress,
    ):

        def _cleanup_item(item_list, cleanup_func):
            nonlocal cleaned_count
            for item in item_list:
                try:
                    cleanup_func(item)
                    cleaned_count += 1
                except Exception as e:
                    feedback.warning(
                        "Cleanup Error",
                        f"Failed to clean item {item.get('id', 'N/A')}: {e}",
                    )
                progress.advance(task_id)  # type: ignore

        index = registry_service._load_index()

        _cleanup_item(
            results["orphaned"], lambda item: index.media_index.pop(item["key"], None)
        )
        _cleanup_item(results["invalid"], lambda item: item["file"].unlink())
        _cleanup_item(
            results["duplicates"], lambda item: index.media_index.pop(item["key"], None)
        )

        from ....service.registry.service import REGISTRY_VERSION

        # For old format, we just re-save the index to update its version
        if results["old_format"]:
            index.version = REGISTRY_VERSION
            progress.advance(task_id, len(results["old_format"]))  # type:ignore

        registry_service._save_index(index)
        feedback.success(
            "Cleanup Complete",
            f"Successfully cleaned {cleaned_count} items from the registry.",
        )
