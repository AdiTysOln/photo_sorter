from pathlib import Path
from typing import Iterable, List


# Obsługiwane rozszerzenia plików graficznych na start
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def _iter_photo_paths(root: Path) -> Iterable[Path]:
    """
    Iterate over all supported photo files under the given root directory.

    :param root: Base directory to scan.
    :return: Generator of Path objects pointing to photo files.
    """
    # Używamy rglob, żeby przejść rekurencyjnie po wszystkich podkatalogach
    for path in root.rglob("*"):
        if not path.is_file():
            continue

        # Sprawdzamy rozszerzenie w trybie case-insensitive
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def list_photo_paths(root_path: str | Path) -> List[Path]:
    """
    Return a list of Paths to supported photo files (JPG/PNG) inside a folder.

    :param root_path: Directory to scan (string or Path).
    :return: List of Path objects pointing to photo files.
    """
    root = Path(root_path).expanduser().resolve()

    # Walidacja wejścia – lepiej dostać czytelny błąd niż cicho zwrócić pustą listę
    if not root.exists():
        raise FileNotFoundError(f"Folder does not exist: {root}")

    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    # Zbieramy wszystkie pasujące ścieżki
    return list(_iter_photo_paths(root))
