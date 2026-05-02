"""
Example usage for the registry command
"""

main = """

Examples:
  # Sync with remote AniList
  anicat registry sync --upload --download

  # Show detailed registry statistics  
  anicat registry stats --detailed

  # Search local registry
  anicat registry search "attack on titan"

  # Export registry to JSON
  anicat registry export --format json --output backup.json

  # Import from backup
  anicat registry import backup.json

  # Clean up orphaned entries
  anicat registry clean --dry-run

  # Create full backup
  anicat registry backup --compress

  # Restore from backup
  anicat registry restore backup.tar.gz
"""
