import hashlib
from pathlib import Path
from typing import List, Optional

from PIL import Image  # używane do otwierania obrazów
import imagehash       # biblioteka do perceptual hash

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


def compute_perceptual_hash(path: Path) -> Optional[str]:
    """
    Computes perceptual hash (pHash) for an image file.
    # Liczy perceptual hash (pHash) dla pliku graficznego.
    # Zwraca hex string albo None, jeśli nie uda się odczytać pliku.
    """
    try:
        with Image.open(path) as img:
            ph = imagehash.phash(img)  # możesz później eksperymentować (ahash, dhash, whash)
            return str(ph)  # domyślnie hex (np. 'ff8f0f00...')
    except Exception:
        # Błąd przy odczycie pliku / formacie – zostawiamy None
        return None


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

def annotate_photos_with_perceptual_hash(photos: List[PhotoInfo]) -> List[PhotoInfo]:
    """
    Adds perceptual hash (pHash) to each PhotoInfo in the list (in-place).
    # Dla każdego zdjęcia liczy perceptual hash i zapisuje w polu perceptual_hash.
    # Działa in-place, ale zwraca listę dla wygody.
    """
    for photo in photos:
        if photo.perceptual_hash is None:
            photo.perceptual_hash = compute_perceptual_hash(photo.path)

    return photos