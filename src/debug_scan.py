from pathlib import Path

from photo_sorter.scanning.filesystem_scanner import list_photo_paths
from photo_sorter.scanning.image_analyzer import build_photo_infos
from photo_sorter.scanning.sorting import sort_photos_by_taken_date
from photo_sorter.deduplication.hashing import annotate_photos_with_file_hash


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

    # Test hashy pliku — krok 2 Etapu 3
    # Uzupełniamy hash pliku dla wszystkich zdjęć
    annotate_photos_with_file_hash(photos_sorted)

    print("\n=== TEST HASHY PLIKÓW (pierwsze 5) ===")
    for photo in photos_sorted[:5]:
        print(f"{photo.path}")
        print(f"  size: {photo.size_bytes} B")
        hash_preview = f"{photo.file_hash[:40]} ..." if photo.file_hash is not None else "<brak>"
        print(f"  file_hash: {hash_preview}")

