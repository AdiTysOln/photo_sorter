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

      # Hash-related fields (Etap 3)
    file_hash: Optional[str] = None
    perceptual_hash: Optional[str] = None

    # Quality-related fields (Etap 4)
    blur_score: Optional[float] = None  # niższa wartość -> bardziej rozmazane
    brightness_score: Optional[float] = None  # średnia jasność (0-255)
    is_potential_trash: Optional[bool] = None  # True/False po analizie jakości
