from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import Optional


@dataclass
class PhotoInfo:
    path: Path
    file_name: str
    size_bytes: int
    taken_at: Optional[datetime]

    # SHA-256 hash całego pliku – używany do identycznych duplikatów 1:1
    file_hash: Optional[str] = None

    # Perceptual hash (np. pHash) – używany do near-duplikatów
    perceptual_hash: Optional[str] = None


