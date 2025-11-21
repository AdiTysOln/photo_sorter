import hashlib
from pathlib import Path
from typing import List

from photo_sorter.scanning.models import PhotoInfo


def compute_file_hash(path: Path, chunk_size: int = 8192) -> str:
    """
    Computes SHA-256 hash for a file.
    # Funkcja liczy hash pliku SHA-256.
    # Działa po kawałkach (chunk_size), żeby wspierać duże pliki.
    """
    sha = hashlib.sha256()

    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            sha.update(chunk)

    return sha.hexdigest()


def annotate_photos_with_file_hash(photos: List[PhotoInfo]) -> List[PhotoInfo]:
    """
    Adds SHA-256 hash to each PhotoInfo in the list (in-place).
    # Dla każdego zdjęcia liczy hash pliku i zapisuje w polu file_hash.
    # Działa na liście przekazanej w argumencie (modyfikacja in-place),
    # a na końcu zwraca tę samą listę dla wygody dalszego łańcuchowania.
    """
    for photo in photos:
        # Nie przeliczamy drugi raz, jeśli hash już jest
        if photo.file_hash is None:
            try:
                photo.file_hash = compute_file_hash(photo.path)
            except FileNotFoundError:
                # Jeśli plik zniknął – zostawiamy None
                photo.file_hash = None

    return photos
