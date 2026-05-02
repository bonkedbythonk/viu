import logging
import os
import time
import uuid
from pathlib import Path
from typing import IO, Any, Union

logger = logging.getLogger(__name__)


class NO_DEFAULT:
    pass


def sanitize_filename(s, restricted=False, is_id=NO_DEFAULT):
    """Sanitizes a string so it could be used as part of a filename.
    @param restricted   Use a stricter subset of allowed characters
    @param is_id        Whether this is an ID that should be kept unchanged if possible.
                        If unset, yt-dlp's new sanitization rules are in effect
    """
    import itertools
    import unicodedata
    import re

    ACCENT_CHARS = dict(
        zip(
            "ÂÃÄÀÁÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖŐØŒÙÚÛÜŰÝÞßàáâãäåæçèéêëìíîïðñòóôõöőøœùúûüűýþÿ",
            itertools.chain(
                "AAAAAA",
                ["AE"],
                "CEEEEIIIIDNOOOOOOO",
                ["OE"],
                "UUUUUY",
                ["TH", "ss"],
                "aaaaaa",
                ["ae"],
                "ceeeeiiiionooooooo",
                ["oe"],
                "uuuuuy",
                ["th"],
                "y",
            ),
        )
    )

    if s == "":
        return ""

    def replace_insane(char):
        if restricted and char in ACCENT_CHARS:
            return ACCENT_CHARS[char]
        elif not restricted and char == "\n":
            return "\0 "
        elif is_id is NO_DEFAULT and not restricted and char in '"*:<>?|/\\':
            # Replace with their full-width unicode counterparts
            return {"/": "\u29f8", "\\": "\u29f9"}.get(char, chr(ord(char) + 0xFEE0))
        elif char == "?" or ord(char) < 32 or ord(char) == 127:
            return ""
        elif char == '"':
            return "" if restricted else "'"
        elif char == ":":
            return "\0_\0-" if restricted else "\0 \0-"
        elif char in "\\/|*<>":
            return "\0_"
        if restricted and (
            char in "!&'()[]{}$;`^,#" or char.isspace() or ord(char) > 127
        ):
            return "" if unicodedata.category(char)[0] in "CM" else "\0_"
        return char

    # Replace look-alike Unicode glyphs
    if restricted and (is_id is NO_DEFAULT or not is_id):
        s = unicodedata.normalize("NFKC", s)
    s = re.sub(
        r"[0-9]+(?::[0-9]+)+", lambda m: m.group(0).replace(":", "_"), s
    )  # Handle timestamps
    result = "".join(map(replace_insane, s))
    if is_id is NO_DEFAULT:
        result = re.sub(
            r"(\0.)(?:(?=\1)..)+", r"\1", result
        )  # Remove repeated substitute chars
        STRIP_RE = r"(?:\0.|[ _-])*"
        result = re.sub(
            f"^\0.{STRIP_RE}|{STRIP_RE}\0.$", "", result
        )  # Remove substitute chars from start/end
    result = result.replace("\0", "") or "_"

    if not is_id:
        while "__" in result:
            result = result.replace("__", "_")
        result = result.strip("_")
        # Common case of "Foreign band name - English song title"
        if restricted and result.startswith("-_"):
            result = result[2:]
        if result.startswith("-"):
            result = "_" + result[len("-") :]
        result = result.lstrip(".")
        if not result:
            result = "_"
    return result


def get_file_modification_time(filepath: Path) -> float:
    """
    Returns the modification time of a file as a Unix timestamp.
    Returns 0 if the file does not exist.
    """
    if filepath.exists():
        return filepath.stat().st_mtime
    return 0


def check_file_modified(filepath: Path, previous_mtime: float) -> tuple[float, bool]:
    """
    Checks if a file has been modified since a given previous modification time.
    """
    current_mtime = get_file_modification_time(filepath)
    return current_mtime, current_mtime > previous_mtime


class AtomicWriter:
    """
    A context manager for performing atomic file writes.

    Writes are first directed to a temporary file. If the 'with' block
    completes successfully, the temporary file is atomically renamed
    to the target path, ensuring that the target file is never in
    a partially written or corrupted state. If an error occurs, the
    temporary file is cleaned up, and the original target file remains
    untouched.

    Usage:
        # For text files
        with AtomicWriter(Path("my_file.txt"), mode="w", encoding="utf-8") as f:
            f.write("Hello, world!\n")
            f.write("This is an atomic write.")

        # For binary files
        with AtomicWriter(Path("binary_data.bin"), mode="wb") as f:
            f.write(b"\x01\x02\x03\x04")
    """

    def __init__(
        self, target_path: Path, mode: str = "w", encoding: Union[str, None] = "utf-8"
    ):
        """
        Initializes the AtomicWriter.

        Args:
            target_path: The Path object for the final destination file.
            mode: The file opening mode (e.g., 'w', 'wb'). Only write modes are supported.
                  'a' (append) and 'x' (exclusive creation) modes are not supported
                  as this class is designed for full file replacement.
            encoding: The encoding to use for text modes ('w', 'wt').
                      Should be None for binary modes ('wb').

        Raises:
            ValueError: If an unsupported file mode is provided.
        """
        if "a" in mode:
            raise ValueError(
                "AtomicWriter does not support 'append' mode ('a'). "
                "It's designed for full file replacement."
            )
        if "x" in mode:
            raise ValueError(
                "AtomicWriter does not support 'exclusive creation' mode ('x'). "
                "It handles creation/replacement atomically."
            )
        if "r" in mode:
            raise ValueError("AtomicWriter is for writing, not reading.")
        if "b" in mode and encoding is not None:
            raise ValueError("Encoding must be None for binary write modes ('wb').")
        if "b" not in mode and encoding is None:
            raise ValueError(
                "Encoding must be specified for text write modes ('w', 'wt')."
            )

        self.target_path = target_path
        self.mode = mode
        self.encoding = encoding

        temp_filename = f"{target_path.name}.{os.getpid()}.{uuid.uuid4()}.tmp"
        self.temp_path = target_path.parent / temp_filename

        self._file_handle: Union[IO[Any], None] = None

    def __enter__(self) -> IO[Any]:
        """
        Enters the context, opens the temporary file for writing,
        and returns the file handle.

        Ensures the parent directory of the target file exists.

        Returns:
            A file-like object (TextIO or BinaryIO) for writing.

        Raises:
            Exception: If there's an error opening the temporary file.
        """
        try:
            self.target_path.parent.mkdir(parents=True, exist_ok=True)

            self._file_handle = self.temp_path.open(
                mode=self.mode, encoding=self.encoding
            )
            return self._file_handle
        except Exception as e:
            logger.error(f"Error opening temporary file {self.temp_path}: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Exits the context. Closes the temporary file.

        If no exception occurred within the 'with' block, atomically renames
        the temporary file to the target path. Otherwise, cleans up the
        temporary file, ensuring the original target file remains untouched.

        Args:
            exc_type: The type of exception raised in the 'with' block (or None).
            exc_val: The exception instance (or None).
            exc_tb: The traceback object (or None).

        Returns:
            False: To propagate any exception that occurred within the 'with' block.
                   (Returning True would suppress the exception).
        """
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None

        if exc_type is None:
            try:
                os.replace(self.temp_path, self.target_path)
                logger.debug(f"Successfully wrote atomically to {self.target_path}")
            except OSError as e:
                logger.error(
                    f"Error renaming temporary file {self.temp_path} to {self.target_path}: {e}"
                )
                try:
                    self.temp_path.unlink(missing_ok=True)
                except OSError as cleanup_e:
                    logger.error(
                        f"Failed to clean up temporary file {self.temp_path} after rename error: {cleanup_e}"
                    )
                raise
        else:
            logger.debug(
                f"An error occurred during write. Cleaning up temporary file {self.temp_path}."
            )
            try:
                self.temp_path.unlink(missing_ok=True)
            except OSError as e:
                logger.error(f"Error cleaning up temporary file {self.temp_path}: {e}")
        return False


class FileLock:
    def __init__(
        self, lock_file_path: Path, timeout: float = 300, stale_timeout: float = 300
    ):
        """
        Initializes a file-based lock.

        Args:
            lock_file_path: The Path object for the lock file.
            timeout: How long (in seconds) to wait to acquire the lock.
                     Set to 0 for non-blocking attempt. Set to -1 for indefinite wait.
            stale_timeout: If the lock file is older than this (in seconds),
                           it's considered stale and will be broken.
        """
        self.lock_file_path = lock_file_path
        self.timeout = timeout
        self.stale_timeout = stale_timeout
        self._acquired = False
        self._pid = os.getpid()  # Get current process ID

    def _acquire_atomic(self) -> bool:
        """
        Attempts to atomically create the lock file.
        Returns True on success, False on failure (file already exists).
        Writes the PID and timestamp to the lock file.
        """
        try:
            # Use 'x' mode for atomic creation: create only if it doesn't exist.
            # If it exists, FileExistsError is raised.
            with self.lock_file_path.open("x") as f:
                f.write(f"{self._pid}\n{time.time()}")
            return True
        except FileExistsError:
            return False
        except Exception as e:
            # Handle other potential errors during file creation/write
            logger.error(f"Error creating lock file {self.lock_file_path}: {e}")
            return False

    def _is_stale(self) -> bool:
        """
        Checks if the existing lock file is stale based on its modification time
        or the PID inside it.
        """
        if not self.lock_file_path.exists():
            return False  # Not stale if it doesn't exist

        try:
            # Read PID and timestamp from the lock file
            with self.lock_file_path.open("r") as f:
                lines = f.readlines()
                if len(lines) >= 2:
                    locked_timestamp = float(lines[1].strip())
                    current_time = time.time()
                    if current_time - locked_timestamp > self.stale_timeout:
                        logger.warning(
                            f"Lock file {self.lock_file_path} is older than {self.stale_timeout} seconds. Considering it stale."
                        )
                        return True
            return False

        except (ValueError, IndexError, FileNotFoundError, OSError) as e:
            logger.warning(
                f"Could not read or parse lock file {self.lock_file_path}. Assuming it's stale due to potential corruption: {e}"
            )
            return True

    def acquire(self):
        """
        Attempts to acquire the lock. Blocks until acquired or timeout occurs.
        """
        start_time = time.time()
        while True:
            if self._acquire_atomic():
                self._acquired = True
                logger.debug(f"Lock acquired by PID {self._pid}.")
                return

            if self._is_stale():
                logger.debug(
                    f"Existing lock file {self.lock_file_path} is stale. Attempting to break it."
                )
                try:
                    self.lock_file_path.unlink()
                    if self._acquire_atomic():
                        self._acquired = True
                        logger.debug(
                            f"Stale lock broken and new lock acquired by PID {self._pid}."
                        )
                        return
                except OSError as e:
                    logger.error(
                        f"Could not remove stale lock file {self.lock_file_path}: {e}"
                    )

            if self.timeout >= 0 and time.time() - start_time > self.timeout:
                raise TimeoutError(
                    f"Failed to acquire lock {self.lock_file_path} within {self.timeout} seconds."
                )

            sleep_time = 0.1
            if self.timeout == -1:
                logger.debug(f"Waiting for lock {self.lock_file_path} indefinitely...")
                time.sleep(sleep_time)
            elif self.timeout > 0:
                logger.debug(
                    f"Waiting for lock {self.lock_file_path} ({round(self.timeout - (time.time() - start_time), 1)}s remaining)..."
                )
                time.sleep(
                    min(
                        sleep_time,
                        self.timeout - (time.time() - start_time)
                        if self.timeout - (time.time() - start_time) > 0
                        else sleep_time,
                    )
                )
            else:
                raise BlockingIOError(
                    f"Lock {self.lock_file_path} is currently held by another process (non-blocking)."
                )

    def release(self):
        """
        Releases the lock by deleting the lock file.
        """
        if self._acquired:
            try:
                self.lock_file_path.unlink(missing_ok=True)
                self._acquired = False
                logger.debug(f"Lock released by PID {self._pid}.")
            except OSError as e:
                logger.error(f"Error releasing lock file {self.lock_file_path}: {e}")
        else:
            logger.warning(
                "Attempted to release a lock that was not acquired by PID {self._pid}."
            )

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
