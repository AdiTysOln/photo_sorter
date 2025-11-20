from pathlib import Path

# Importujemy naszą funkcję ze skanera
from photo_sorter.scanning.filesystem_scanner import list_photo_paths


if __name__ == "__main__":
    # TODO: podmień tę ścieżkę na swój katalog ze zdjęciami
    photos_folder = Path.home() / "Pictures"  # np. /home/user/Pictures

    print(f"Scanning folder: {photos_folder}")

    paths = list_photo_paths(photos_folder)

    print(f"Found {len(paths)} photo files.")
    for p in paths[:20]:
        # Wyświetlamy maksymalnie 20 pierwszych ścieżek, żeby nie zalać terminala
        print("-", p)
