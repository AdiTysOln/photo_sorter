from pathlib import Path
from typing import Any, Dict, List

import tkinter as tk
from tkinter import filedialog, messagebox

# Backend imports – GUI tylko je wywołuje, nie implementuje logiki.  # GUI tylko używa backendu, nie robi obliczeń samodzielnie.
from photo_sorter.scanning.filesystem_scanner import list_photo_paths
from photo_sorter.scanning.image_analyzer import build_photo_infos
from photo_sorter.scanning.sorting import sort_photos_by_taken_date
from photo_sorter.deduplication.hashing import (
    annotate_photos_with_file_hash,
    annotate_photos_with_perceptual_hash,
)
from photo_sorter.deduplication.grouping import (
    find_exact_duplicate_groups,
    find_near_duplicate_groups,
)
from photo_sorter.quality.analysis import (
    annotate_photos_with_quality,
    find_potential_trash_photos,
)


# Global variable to keep last analysis result in memory.  # Zmienna globalna, w której trzymamy wynik ostatniej analizy (na przyszłe etapy GUI).
LAST_ANALYSIS_RESULT: Dict[str, Any] | None = None


def run_backend_pipeline(root_folder: Path) -> Dict[str, Any]:
    """
    Run the full backend pipeline for a given folder and return summary data.
    This is basically the same logic you used in debug_scan.py, but wrapped
    into a reusable function for the GUI.

    :param root_folder: Folder with photos to analyze.
    :return: Dict with photos list, duplicate groups and potential trash photos.
    """
    # 1. Scan filesystem and collect photo paths.  # 1. Skanujemy system plików i zbieramy ścieżki do zdjęć.
    photo_paths: List[Path] = list_photo_paths(root_folder)

    # 2. Build PhotoInfo objects from paths.  # 2. Budujemy obiekty PhotoInfo na podstawie ścieżek.
    photos = build_photo_infos(photo_paths)

    # 3. Sort photos by taken date (for nicer ordering later).  # 3. Sortujemy zdjęcia po dacie wykonania (lepsza kolejność).
    photos = sort_photos_by_taken_date(photos)

    # 4. Annotate photos with file hash and perceptual hash.  # 4. Dodajemy hash pliku i hash percepcyjny do PhotoInfo.
    annotate_photos_with_file_hash(photos)
    annotate_photos_with_perceptual_hash(photos)

    # 5. Find exact and near duplicate groups based on hashes.  # 5. Szukamy grup dokładnych i podobnych duplikatów na podstawie hashy.
    exact_groups = find_exact_duplicate_groups(photos)
    near_groups = find_near_duplicate_groups(photos)  # max_distance używa domyślnej wartości, jeśli ją ustawiłeś.

    # 6. Annotate quality metrics and find potential trash photos.  # 6. Liczymy jakość (ostrość/jasność) i szukamy potencjalnych śmieci.
    annotate_photos_with_quality(photos)
    potential_trash = find_potential_trash_photos(photos)

    # 7. Return everything in a dict, so GUI can use it.  # 7. Zwracamy wszystko w słowniku, żeby GUI mogło z tego korzystać.
    summary: Dict[str, Any] = {
        "photos": photos,  # list[PhotoInfo]
        "exact_groups": exact_groups,  # list[list[PhotoInfo]]
        "near_groups": near_groups,  # list[list[PhotoInfo]]
        "potential_trash": potential_trash,  # list[PhotoInfo]
    }
    return summary


def create_main_window() -> tk.Tk:
    """
    Create the main Tkinter window with a button and basic summary labels.

    The GUI does NOT compute anything by itself. It only:
    - lets the user choose a folder,
    - calls run_backend_pipeline(root_folder: Path),
    - displays a few numbers from the returned data.
    """
    root = tk.Tk()
    root.title("Photo Sorter - Etap 5 (mini GUI)")

    # StringVars to update labels dynamically.  # StringVar pozwala łatwo aktualizować tekst w labelkach.
    selected_folder_var = tk.StringVar(
        value="Nie wybrano jeszcze żadnego folderu."
    )
    stats_var = tk.StringVar(
        value="Nie wykonano jeszcze skanowania."
    )

    # --- Button callback ---

    def on_choose_and_scan() -> None:
        """
        Ask user for a folder, run backend pipeline and update labels.

        Important data flow explanation:
        - This function gets a folder path from filedialog (string).
        - It converts that string to Path and calls run_backend_pipeline(Path).
        - run_backend_pipeline uses:
          * list_photo_paths -> returns list[Path],
          * build_photo_infos -> returns photos: list[PhotoInfo],
          * sort_photos_by_taken_date(photos),
          * annotate_photos_with_file_hash(photos),
          * annotate_photos_with_perceptual_hash(photos),
          * find_exact_duplicate_groups(photos),
          * annotate_photos_with_quality(photos),
          * find_potential_trash_photos(photos).
        - GUI then only reads:
          * len(photos),
          * len(exact_groups),
          * len(potential_trash)
          and displays those numbers.
        """
        folder_str = filedialog.askdirectory()
        if not folder_str:
            # User cancelled the dialog.  # Użytkownik anulował okno wyboru folderu.
            return

        selected_folder_var.set(f"Wybrany folder: {folder_str}")

        root_folder = Path(folder_str)

        try:
            summary = run_backend_pipeline(root_folder)
        except Exception as exc:  # noqa: BLE001
            # Show a simple error dialog if backend crashed.  # Pokazujemy prosty komunikat błędu, jeśli backend się wywalił.
            messagebox.showerror(
                "Błąd analizy",
                f"Wystąpił błąd podczas skanowania folderu:\n{exc}",
            )
            return

        # Make summary globally available for future GUI steps.  # Zapisujemy wynik globalnie na potrzeby kolejnych kroków GUI.
        global LAST_ANALYSIS_RESULT
        LAST_ANALYSIS_RESULT = summary

        photos = summary["photos"]
        exact_groups = summary["exact_groups"]
        potential_trash = summary["potential_trash"]

        num_photos = len(photos)
        num_exact_groups = len(exact_groups)
        num_potential_trash = len(potential_trash)

        stats_text = (
            f"Liczba znalezionych zdjęć: {num_photos}\n"
            f"Liczba grup dokładnych duplikatów: {num_exact_groups}\n"
            f"Liczba potencjalnych zdjęć 'śmieciowych': {num_potential_trash}"
        )
        stats_var.set(stats_text)

    # --- Layout ---

    main_frame = tk.Frame(root, padx=16, pady=16)
    main_frame.pack(fill="both", expand=True)

    choose_button = tk.Button(
        main_frame,
        text="Wybierz folder i przeskanuj",
        command=on_choose_and_scan,
    )
    choose_button.pack(anchor="w")

    folder_label = tk.Label(
        main_frame,
        textvariable=selected_folder_var,
        justify="left",
        wraplength=600,
    )
    folder_label.pack(anchor="w", pady=(8, 4))

    stats_label = tk.Label(
        main_frame,
        textvariable=stats_var,
        justify="left",
        wraplength=600,
    )
    stats_label.pack(anchor="w", pady=(4, 0))

    return root


def main() -> None:
    """
    Entry point for running the GUI from Python.  # Główna funkcja uruchamiająca GUI (dla python -m lub import main()).
    """
    root = create_main_window()
    root.mainloop()


if __name__ == "__main__":
    # This allows you to run the GUI with "python -m photo_sorter.gui"  # Dzięki temu możesz odpalić GUI przez "python -m photo_sorter.gui".
    main()
