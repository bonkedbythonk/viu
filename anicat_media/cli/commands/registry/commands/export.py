"""
Registry export command - export registry data to various formats
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import click

from .....core.config import AppConfig
from ....service.feedback import FeedbackService
from ....service.registry.service import MediaRegistryService

if TYPE_CHECKING:
    from ....service.registry.models import MediaRecord


@click.command(help="Export registry data to various formats")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "csv", "xml"], case_sensitive=False),
    default="json",
    help="Export format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path (auto-generated if not specified)",
)
@click.option(
    "--include-metadata", is_flag=True, help="Include detailed media metadata in export"
)
@click.option(
    "--status",
    multiple=True,
    type=click.Choice(
        ["watching", "completed", "planning", "dropped", "paused", "repeating"],
        case_sensitive=False,
    ),
    help="Only export specific status lists",
)
@click.option("--compress", is_flag=True, help="Compress the output file")
@click.option(
    "--api",
    default="anilist",
    type=click.Choice(["anilist"], case_sensitive=False),
    help="Media API registry to export",
)
@click.pass_obj
def export(
    config: AppConfig,
    output_format: str,
    output: Path | None,
    include_metadata: bool,
    status: tuple[str, ...],
    compress: bool,
    api: str,
):
    """
    Export your local media registry to various formats.

    Supports JSON, CSV, and XML formats. Can optionally include
    detailed metadata and compress the output.
    """
    feedback = FeedbackService(config)

    try:
        registry_service = MediaRegistryService(api, config.media_registry)

        # Generate output filename if not specified
        if not output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            extension = output_format.lower()
            if compress:
                extension += ".gz"
            output_path = Path(f"anicat_registry_{api}_{timestamp}.{extension}")
        else:
            output_path = output

        # Get export data
        export_data = _prepare_export_data(registry_service, include_metadata, status)

        if not export_data["media"]:
            feedback.warning(
                "No Data", "No media entries to export based on your criteria."
            )
            return

        # Export based on format
        if output_format.lower() == "json":
            _export_json(export_data, output_path)
        elif output_format.lower() == "csv":
            _export_csv(export_data, output_path)
        elif output_format.lower() == "xml":
            _export_xml(export_data, output_path)

        if compress:
            _compress_file(output_path, feedback)
            output_path = output_path.with_suffix(output_path.suffix + ".gz")

        feedback.success(
            "Export Complete",
            f"Registry exported to {output_path} ({_format_file_size(output_path)})",
        )

    except Exception as e:
        feedback.error("Export Error", f"Failed to export registry: {e}")
        raise click.Abort()


def _prepare_export_data(
    registry_service: MediaRegistryService,
    include_metadata: bool,
    status_filter: tuple[str, ...],
) -> dict:
    """Prepare data for export based on options."""
    from .....libs.media_api.types import UserMediaListStatus

    status_map = {
        "watching": UserMediaListStatus.WATCHING,
        "completed": UserMediaListStatus.COMPLETED,
        "planning": UserMediaListStatus.PLANNING,
        "dropped": UserMediaListStatus.DROPPED,
        "paused": UserMediaListStatus.PAUSED,
        "repeating": UserMediaListStatus.REPEATING,
    }
    status_enums = {status_map[s] for s in status_filter}

    export_data = {
        "metadata": {
            "export_timestamp": datetime.now().isoformat(),
            "registry_version": registry_service._load_index().version,
            "include_metadata": include_metadata,
            "filtered_status": list(status_filter) if status_filter else "all",
        },
        "statistics": registry_service.get_registry_stats(),
        "media": [],
    }

    all_records = registry_service.get_all_media_records()

    for record in all_records:
        index_entry = registry_service.get_media_index_entry(record.media_item.id)

        if status_enums and (not index_entry or index_entry.status not in status_enums):
            continue

        media_data = _flatten_record_for_export(record, index_entry, include_metadata)
        export_data["media"].append(media_data)

    return export_data


def _flatten_record_for_export(
    record: "MediaRecord", index_entry, include_metadata: bool
) -> dict:
    """Helper to convert a MediaRecord into a flat dictionary for exporting."""
    media_item = record.media_item

    data = {
        "id": media_item.id,
        "title_english": media_item.title.english,
        "title_romaji": media_item.title.romaji,
        "title_native": media_item.title.native,
        "user_status": index_entry.status.value
        if index_entry and index_entry.status
        else None,
        "user_progress": index_entry.progress if index_entry else None,
        "user_score": index_entry.score if index_entry else None,
        "user_last_watched": index_entry.last_watched.isoformat()
        if index_entry and index_entry.last_watched
        else None,
        "user_notes": index_entry.notes if index_entry else None,
    }

    if include_metadata:
        data.update(
            {
                "format": media_item.format.value if media_item.format else None,
                "episodes": media_item.episodes,
                "duration_minutes": media_item.duration,
                "media_status": media_item.status.value if media_item.status else None,
                "start_date": media_item.start_date.isoformat()
                if media_item.start_date
                else None,
                "end_date": media_item.end_date.isoformat()
                if media_item.end_date
                else None,
                "average_score": media_item.average_score,
                "popularity": media_item.popularity,
                "genres": ", ".join([genre.value for genre in media_item.genres]),
                "tags": ", ".join([tag.name.value for tag in media_item.tags]),
                "studios": ", ".join(
                    [studio.name for studio in media_item.studios if studio.name]
                ),
                "description": media_item.description,
                "cover_image_large": media_item.cover_image.large
                if media_item.cover_image
                else None,
            }
        )
    return data


def _export_json(data: dict, output_path: Path):
    """Export data to JSON format."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _export_csv(data: dict, output_path: Path):
    """Export data to CSV format."""
    if not data["media"]:
        return

    fieldnames = list(data["media"][0].keys())

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data["media"])


def _export_xml(data: dict, output_path: Path):
    """Export data to XML format."""
    import xml.etree.ElementTree as ET

    root = ET.Element("anicat_registry")

    # Add metadata
    metadata_elem = ET.SubElement(root, "metadata")
    for key, value in data["metadata"].items():
        if value is not None:
            elem = ET.SubElement(metadata_elem, key)
            elem.text = str(value)

    # Add media
    media_list_elem = ET.SubElement(root, "media_list")
    for media in data["media"]:
        media_elem = ET.SubElement(media_list_elem, "media")
        for key, value in media.items():
            if value is not None:
                field_elem = ET.SubElement(media_elem, key)
                field_elem.text = str(value)

    # Write XML
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)  # Pretty print
    tree.write(output_path, encoding="utf-8", xml_declaration=True)


def _compress_file(file_path: Path, feedback: FeedbackService):
    """Compresses a file using gzip and removes the original."""
    import gzip
    import shutil

    compressed_path = file_path.with_suffix(file_path.suffix + ".gz")
    try:
        with open(file_path, "rb") as f_in:
            with gzip.open(compressed_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        file_path.unlink()  # Remove original file
    except Exception as e:
        feedback.warning("Compression Failed", f"Could not compress {file_path}: {e}")


def _format_file_size(file_path: Path) -> str:
    """Format file size in human-readable format."""
    try:
        size_bytes: float = float(file_path.stat().st_size)
        if size_bytes < 1024.0:
            return f"{int(size_bytes)} B"
        for unit in ["KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    except FileNotFoundError:
        return "Unknown size"
