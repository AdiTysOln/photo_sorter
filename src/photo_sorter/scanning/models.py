from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from datetime import datetime


@dataclass
class PhotoInfo:
    """
    Basic information about a photo file.
    """
    path: Path                 # Pełna ścieżka do pliku
    file_name: str             # Nazwa pliku (bez ścieżki)

    # Poniższe pola zostawiamy na później – będziemy je stopniowo wypełniać
    size_bytes: Optional[int] = None      # Rozmiar pliku w bajtach
    taken_at: Optional[datetime] = None   # Data wykonania zdjęcia (EXIF lub mtime)
    # Tu w przyszłości: hash, jakość, tagi, itp.
