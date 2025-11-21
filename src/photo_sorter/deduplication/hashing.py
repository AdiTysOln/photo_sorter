import hashlib
from pathlib import Path
from typing import List, Optional

from PIL import Image  # used for opening images
import imagehash       # library for perceptual hash

from photo_sorter.scanning.models import PhotoInfo


def compute_file_hash(path: Path, chunk_size: int = 8192) -> str:
    """
    Computes SHA-256 hash for a file.
    Works in chunks (chunk_size) to support large files.
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
    Returns hex string or None if file cannot be read.
    """
    try:
        with Image.open(path) as img:
            ph = imagehash.phash(img)  # can experiment later with ahash, dhash, whash
            return str(ph)  # hex format by default (e.g. 'ff8f0f00...')
    except Exception:
        # Error reading file / format - return None
        return None


def annotate_photos_with_file_hash(photos: List[PhotoInfo]) -> List[PhotoInfo]:
    """
    Adds SHA-256 hash to each PhotoInfo in the list (in-place).
    Computes file hash for each photo and saves it in the file_hash field.
    Works in-place on the list passed as argument, returning the same list
    for convenience in chaining.
    """
    for photo in photos:
        # Don't recompute if hash already exists
        if photo.file_hash is None:
            try:
                photo.file_hash = compute_file_hash(photo.path)
            except FileNotFoundError:
                # If file disappeared - leave as None
                photo.file_hash = None

    return photos

def annotate_photos_with_perceptual_hash(photos: List[PhotoInfo]) -> List[PhotoInfo]:
    """
    Adds perceptual hash (pHash) to each PhotoInfo in the list (in-place).
    Computes perceptual hash for each photo and saves it in the perceptual_hash field.
    Works in-place but returns the list for convenience.
    """
    for photo in photos:
        if photo.perceptual_hash is None:
            photo.perceptual_hash = compute_perceptual_hash(photo.path)

    return photos