from typing import List, Dict
from photo_sorter.scanning.models import PhotoInfo


def _group_photos_by_file_hash(photos: List[PhotoInfo]) -> Dict[str, List[PhotoInfo]]:
    """
    Groups photos by their file_hash (only non-None hashes).
    # Grupuje zdjęcia po hashach plików (pomija None).
    """
    groups: Dict[str, List[PhotoInfo]] = {}

    for photo in photos:
        if not photo.file_hash:
            # Brak hasha – np. plik zniknął albo nie został przeliczony
            continue

        if photo.file_hash not in groups:
            groups[photo.file_hash] = []

        groups[photo.file_hash].append(photo)

    return groups


def find_exact_duplicate_groups(photos: List[PhotoInfo]) -> List[List[PhotoInfo]]:
    """
    Finds groups of exact duplicates based on file_hash.
    # Zwraca listy PhotoInfo, gdzie każdy wewnętrzny zbiór to grupa
    # identycznych plików (ten sam hash), o rozmiarze co najmniej 2.
    """
    grouped = _group_photos_by_file_hash(photos)
    duplicate_groups: List[List[PhotoInfo]] = []

    for _, items in grouped.items():
        if len(items) >= 2:
            duplicate_groups.append(items)

    return duplicate_groups
