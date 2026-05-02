def time_to_seconds(time_str: str) -> int:
    """Convert HH:MM:SS to seconds."""
    try:
        parts = time_str.split(":")
        if len(parts) == 3:
            h, m, s = map(int, parts)
            return h * 3600 + m * 60 + s
    except (ValueError, AttributeError):
        pass
    return 0


def calculate_completion_percentage(last_watch_time: str, total_duration: str) -> float:
    """
    Calculates the percentage completion based on last watch time and total duration.

    Args:
        last_watch_time: A string representing the last watched time in 'HH:MM:SS' format.
        total_duration: A string representing the total duration in 'HH:MM:SS' format.

    Returns:
        A float representing the percentage completion (0.0 to 100.0).
        Returns 0.0 if total_duration is '00:00:00'.
        Caps the percentage at 100.0 if last_watch_time exceeds total_duration.

    Raises:
        ValueError: If the input time strings are not in the expected format.
    """
    last_watch_seconds = time_to_seconds(last_watch_time)
    total_duration_seconds = time_to_seconds(total_duration)

    if total_duration_seconds == 0:
        return 0.0  # Avoid division by zero, return 0% for zero duration

    # Calculate raw percentage
    percentage = (last_watch_seconds / total_duration_seconds) * 100.0

    # Ensure percentage does not exceed 100%
    return min(percentage, 100.0)
