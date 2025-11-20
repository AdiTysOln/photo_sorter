import hashlib
from pathlib import Path

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
