from pathlib import Path
from datetime import datetime
from typing import Iterable, List, Optional

from PIL import Image, ExifTags  # Pillow: odczyt EXIF

from .models import PhotoInfo


# Klucze EXIF, które mogą zawierać datę wykonania zdjęcia
EXIF_DATETIME_KEYS = ("DateTimeOriginal", "DateTimeDigitized", "DateTime")


def _parse_exif_datetime(value: str) -> Optional[datetime]:
    """
    Parse EXIF datetime string like '2025:11:18 20:08:13' into datetime.
    """
    try:
        # Typowy format daty w EXIF
        return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except Exception:
        return None


def _get_exif_datetime(path: Path) -> Optional[datetime]:
    """
    Try to read the best datetime from EXIF metadata.
    Returns None if EXIF is missing or cannot be parsed.
    """
    try:
        with Image.open(path) as img:
            exif = img._getexif()
    except Exception:
        # # Jeśli nie da się otworzyć pliku lub nie ma EXIF – trudno, lecimy dalej
        return None

    if not exif:
        return None

    # Mapowanie numerycznych kluczy EXIF na czytelne nazwy
    exif_named = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}

    for key in EXIF_DATETIME_KEYS:
        raw_value = exif_named.get(key)
        if not raw_value:
            continue

        # Czasem EXIF potrafi zwrócić bytes zamiast str
        if isinstance(raw_value, bytes):
            try:
                raw_value = raw_value.decode(errors="ignore")
            except Exception:
                continue

        if isinstance(raw_value, str):
            dt = _parse_exif_datetime(raw_value.strip())
            if dt:
                return dt

    return None


def build_photo_info(path: Path) -> PhotoInfo:
    """
    Create PhotoInfo using EXIF datetime if possible,
    otherwise fall back to filesystem modification time (mtime).
    """
    # Pobieramy dane z systemu plików
    stat_result = path.stat()
    size_bytes = stat_result.st_size
    fs_mtime = datetime.fromtimestamp(stat_result.st_mtime)

    # Najpierw próbujemy EXIF
    exif_dt = _get_exif_datetime(path)

    # Wybieramy najlepszą datę: EXIF jeśli jest, w przeciwnym razie mtime
    taken_at = exif_dt or fs_mtime

    return PhotoInfo(
        path=path,
        file_name=path.name,
        size_bytes=size_bytes,
        taken_at=taken_at,
    )


def build_photo_infos(paths: Iterable[Path]) -> List[PhotoInfo]:
    """
    Convert iterable of Paths into a list of PhotoInfo objects.
    """
    return [build_photo_info(p) for p in paths]

