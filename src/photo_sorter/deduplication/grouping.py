from typing import List, Dict
from photo_sorter.scanning.models import PhotoInfo


def _group_photos_by_file_hash(photos: List[PhotoInfo]) -> Dict[str, List[PhotoInfo]]:
    """
    Groups photos by their file_hash (only non-None hashes).
    """
    groups: Dict[str, List[PhotoInfo]] = {}

    for photo in photos:
        if not photo.file_hash:
            # No hash - e.g. file disappeared or wasn't computed
            continue

        if photo.file_hash not in groups:
            groups[photo.file_hash] = []

        groups[photo.file_hash].append(photo)

    return groups


def find_exact_duplicate_groups(photos: List[PhotoInfo]) -> List[List[PhotoInfo]]:
    """
    Finds groups of exact duplicates based on file_hash.
    Returns lists of PhotoInfo where each inner list is a group of
    identical files (same hash), with size of at least 2.
    """
    grouped = _group_photos_by_file_hash(photos)
    duplicate_groups: List[List[PhotoInfo]] = []

    for _, items in grouped.items():
        if len(items) >= 2:
            duplicate_groups.append(items)

    return duplicate_groups


def hamming_distance_hex(hash1: str, hash2: str) -> int:
    """
    Computes Hamming distance between two hex-encoded hashes.
    If lengths differ, truncates to the shorter one for safety.
    """
    if not hash1 or not hash2:
        raise ValueError("Both hashes must be non-empty strings")

    if len(hash1) != len(hash2):
        min_len = min(len(hash1), len(hash2))
        hash1 = hash1[:min_len]
        hash2 = hash2[:min_len]

    n1 = int(hash1, 16)
    n2 = int(hash2, 16)
    return (n1 ^ n2).bit_count()


def find_near_duplicate_groups(
    photos: List[PhotoInfo],
    max_distance: int = 5,
) -> List[List[PhotoInfo]]:
    """
    Finds groups of near-duplicate photos based on perceptual_hash.
    max_distance - maximum Hamming distance between hashes,
    above which photos are not treated as near-duplicates.

    Implementation:
     - takes only photos with perceptual_hash != None,
     - builds groups as connected components by distance threshold.
    """
    candidates: List[PhotoInfo] = [p for p in photos if p.perceptual_hash]
    n = len(candidates)

    if n == 0:
        return []

    visited = [False] * n
    groups: List[List[PhotoInfo]] = []

    for i in range(n):
        if visited[i]:
            continue

        visited[i] = True
        group = [candidates[i]]
        frontier = [i]

        while frontier:
            current_idx = frontier.pop()
            current_hash = candidates[current_idx].perceptual_hash
            assert current_hash is not None

            for j in range(n):
                if visited[j]:
                    continue

                other_hash = candidates[j].perceptual_hash
                if other_hash is None:
                    continue

                distance = hamming_distance_hex(current_hash, other_hash)
                if distance <= max_distance:
                    visited[j] = True
                    group.append(candidates[j])
                    frontier.append(j)

        if len(group) >= 2:
            groups.append(group)

    return groups
