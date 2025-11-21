from pathlib import Path
from typing import Iterable, List


# Supported image file extensions for initial implementation
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def _iter_photo_paths(root: Path) -> Iterable[Path]:
    """
    Iterate over all supported photo files under the given root directory.

    :param root: Base directory to scan.
    :return: Generator of Path objects pointing to photo files.
    """
    # Use rglob to recursively traverse all subdirectories
    for path in root.rglob("*"):
        if not path.is_file():
            continue

        # Check extension in case-insensitive mode
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def list_photo_paths(root_path: str | Path) -> List[Path]:
    """
    Return a list of Paths to supported photo files (JPG/PNG) inside a folder.

    :param root_path: Directory to scan (string or Path).
    :return: List of Path objects pointing to photo files.
    """
    root = Path(root_path).expanduser().resolve()

    # Input validation - better to get a clear error than silently return an empty list
    if not root.exists():
        raise FileNotFoundError(f"Folder does not exist: {root}")

    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    # Collect all matching paths
    return list(_iter_photo_paths(root))
