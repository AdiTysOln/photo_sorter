from pathlib import Path

from photo_sorter.scanning.filesystem_scanner import list_photo_paths
from photo_sorter.scanning.image_analyzer import build_photo_infos
from photo_sorter.scanning.sorting import sort_photos_by_taken_date
from photo_sorter.deduplication.hashing import (
    annotate_photos_with_file_hash,
    annotate_photos_with_perceptual_hash,  # <- to dodajemy
)
from photo_sorter.deduplication.grouping import (
    find_exact_duplicate_groups,
    find_near_duplicate_groups,
    hamming_distance_hex,
)


if __name__ == "__main__":
    # Katalog testowy, który założyłeś
    photos_folder = Path("/home/adrian/Desktop/projects/k_test_mix")

    print(f"Scanning folder: {photos_folder}")

    # 1) Zbieramy ścieżki do plików graficznych
    paths = list_photo_paths(photos_folder)
    print(f"Found {len(paths)} photo files.")

    if not paths:
        print("No photo files found. Exiting.")
        raise SystemExit(0)

    # 2) Budujemy listę PhotoInfo na podstawie metadanych pliku (EXIF + mtime)
    photos = build_photo_infos(paths)

    # 3) Sortujemy zdjęcia po dacie (rosnąco – najstarsze najpierw)
    photos_sorted = sort_photos_by_taken_date(photos, descending=False)

    print("\nFirst 10 photos (sorted by date):")
    for photo in photos_sorted[:10]:
        taken_at_str = (
            photo.taken_at.isoformat(sep=" ", timespec="seconds")
            if photo.taken_at
            else "N/A"
        )

        print(f"- {taken_at_str} | {photo.size_bytes:>8} B | {photo.path}")

    # 4) Uzupełniamy hash pliku dla wszystkich zdjęć
    annotate_photos_with_file_hash(photos_sorted)

    print("\n=== TEST HASHY PLIKÓW (pierwsze 5) ===")
    for photo in photos_sorted[:5]:
        print(f"{photo.path}")
        print(f"  size: {photo.size_bytes} B")
        hash_preview = (
            f"{photo.file_hash[:40]} ..." if photo.file_hash is not None else "<brak>"
        )
        print(f"  file_hash: {hash_preview}")

    # 4b) Uzupełniamy perceptual hash (pHash) dla wszystkich zdjęć
    annotate_photos_with_perceptual_hash(photos_sorted)

    print("\n=== TEST PERCEPTUAL HASHES (first 5) ===")
    for photo in photos_sorted[:5]:
        print(f"{photo.path}")
        ph = photo.perceptual_hash or "<brak>"
        print(f"  perceptual_hash: {ph}")

    # 5) Szukamy grup identycznych duplikatów po file_hash
    duplicate_groups = find_exact_duplicate_groups(photos_sorted)

    total_groups = len(duplicate_groups)
    total_photos_in_groups = sum(len(g) for g in duplicate_groups)

    print("\n=== EXACT DUPLICATE GROUPS (by file hash) ===")
    print(f"Total groups: {total_groups}")
    print(f"Total photos in groups: {total_photos_in_groups}")

    # Podgląd pierwszych kilku grup
    max_groups_to_show = 3

    for idx, group in enumerate(duplicate_groups[:max_groups_to_show], start=1):
        example_hash = group[0].file_hash[:16] if group[0].file_hash else "<brak>"
        print(f"\nGroup {idx} (size {len(group)}), hash: {example_hash}...")
        for photo in group:
            print(f"  - {photo.path}")

    # 6) Near-duplicate groups based on perceptual_hash
    near_duplicate_groups = find_near_duplicate_groups(photos_sorted, max_distance=5)

    total_near_groups = len(near_duplicate_groups)
    total_near_photos = sum(len(g) for g in near_duplicate_groups)

    print("\n=== NEAR DUPLICATE GROUPS (by perceptual hash, max_distance=5) ===")
    print(f"Total groups: {total_near_groups}")
    print(f"Total photos in groups: {total_near_photos}")

    max_near_groups_to_show = 3

    for idx, group in enumerate(near_duplicate_groups[:max_near_groups_to_show], start=1):
        ref = group[0]
        print(f"\nNear Group {idx} (size {len(group)}), reference:")
        print(f"  ref path:  {ref.path}")
        print(f"  ref pHash: {ref.perceptual_hash}")

        for photo in group[1:]:
            if photo.perceptual_hash is None or ref.perceptual_hash is None:
                distance = "?"
            else:
                distance = hamming_distance_hex(ref.perceptual_hash, photo.perceptual_hash)

            print(f"  - {photo.path}")
            print(f"    pHash:    {photo.perceptual_hash}")
            print(f"    distance: {distance}")
