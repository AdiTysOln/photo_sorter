from pathlib import Path
from typing import Any, Dict, List

import shutil
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

# Global variable to remember the last scanned root folder.  # Zmienna globalna z ostatnio skanowanym folderem (do tworzenia trash_preview).
LAST_ANALYZED_ROOT: Path | None = None

# Global reference to the trash Listbox widget.  # Globalne odniesienie do Listboxa z listą śmieci.
TRASH_LISTBOX: tk.Listbox | None = None


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


def refresh_trash_listbox() -> None:
    """
    Refresh the GUI Listbox that shows potential trash photos.

    This function reads data from LAST_ANALYSIS_RESULT["potential_trash"]
    (which is a list[PhotoInfo]) and fills the Listbox with a simple
    textual representation: file name + full path.

    # Funkcja odświeża Listbox z potencjalnymi śmieciami.
    # Dane bierzemy z LAST_ANALYSIS_RESULT["potential_trash"],
    # czyli listy obiektów PhotoInfo zwróconej przez backend.
    """
    global TRASH_LISTBOX, LAST_ANALYSIS_RESULT

    if TRASH_LISTBOX is None:
        # GUI has not created the Listbox yet.
        # GUI nie utworzyło jeszcze Listboxa – nie ma czego odświeżać.
        return

    # Clear current content.
    # Czyścimy aktualną zawartość listy.
    TRASH_LISTBOX.delete(0, tk.END)

    if LAST_ANALYSIS_RESULT is None:
        # No analysis has been run yet.
        # Analiza jeszcze nie była uruchamiana.
        return

    potential_trash = LAST_ANALYSIS_RESULT.get("potential_trash") or []

    # We expect potential_trash to be a list[PhotoInfo].
    # Zakładamy, że potential_trash to list[PhotoInfo].
    for item in potential_trash:
        try:
            path = item.path  # type: ignore[attr-defined]
            display_text = f"{path.name}  |  {path}"
        except AttributeError:
            # Fallback – if the structure is different, show raw object.
            # Awaryjnie – jeśli struktura jest inna, pokazujemy surowy obiekt.
            display_text = str(item)

        TRASH_LISTBOX.insert(tk.END, display_text)


def move_all_potential_trash_to_preview(
    root_folder: Path,
    potential_trash: list[Any],
) -> int:
    """
    Move all potential trash photos to a 'trash_preview' subfolder
    inside the given root folder.

    Returns the number of successfully moved files.

    # Funkcja przenosi wszystkie potencjalne śmieci do podfolderu
    # 'trash_preview' w katalogu głównym skanowania.
    # Zwraca liczbę faktycznie przeniesionych plików.
    """
    trash_dir = root_folder / "trash_preview"
    trash_dir.mkdir(exist_ok=True)

    moved_count = 0

    for item in potential_trash:
        try:
            src_path = item.path  # type: ignore[attr-defined]
        except AttributeError:
            # If object has no .path attribute, we skip it.
            # Jeśli obiekt nie ma atrybutu .path, pomijamy go.
            continue

        if not isinstance(src_path, Path):
            src_path = Path(src_path)

        # Skip if file does not exist anymore or is not a regular file.
        # Pomijamy, jeśli plik już nie istnieje albo nie jest zwykłym plikiem.
        if not src_path.exists() or not src_path.is_file():
            continue

        # Skip if the file is already in trash_dir.
        # Jeśli plik już jest w trash_preview, nie ruszamy go.
        if src_path.parent == trash_dir:
            continue

        dest_path = trash_dir / src_path.name

        # If destination exists, generate a unique name.
        # Jeśli docelowy plik istnieje, generujemy unikalną nazwę.
        if dest_path.exists():
            stem = dest_path.stem
            suffix = dest_path.suffix
            counter = 1
            while True:
                candidate = trash_dir / f"{stem}__trash_{counter}{suffix}"
                if not candidate.exists():
                    dest_path = candidate
                    break
                counter += 1

        shutil.move(str(src_path), str(dest_path))
        moved_count += 1

    return moved_count


def create_main_window() -> tk.Tk:
    """
    Create the main Tkinter window with a button and basic summary labels.

    The GUI does NOT compute anything by itself. It only:
    - lets the user choose a folder,
    - calls run_backend_pipeline(root_folder: Path),
    - displays a few numbers from the returned data,
    - shows a Listbox with potential trash photos,
    - allows moving all potential trash photos to trash_preview/.
    """
    global TRASH_LISTBOX, LAST_ANALYZED_ROOT

    root = tk.Tk()
    root.title("Photo Sorter - Etap 5 (mini GUI)")

    # StringVars to update labels dynamically.  # StringVar pozwala łatwo aktualizować tekst w labelkach.
    selected_folder_var = tk.StringVar(
        value="Nie wybrano jeszcze żadnego folderu."
    )
    stats_var = tk.StringVar(
        value="Nie wykonano jeszcze skanowania."
    )

    # --- Button callbacks ---

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
        global LAST_ANALYSIS_RESULT, LAST_ANALYZED_ROOT
        LAST_ANALYSIS_RESULT = summary
        LAST_ANALYZED_ROOT = root_folder

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

        # After updating stats, refresh the trash Listbox based on backend data.
        # Po zaktualizowaniu statystyk odświeżamy Listbox ze śmieciami na podstawie danych z backendu.
        refresh_trash_listbox()

    def on_move_all_trash() -> None:
        """
        Move all potential trash photos (from LAST_ANALYSIS_RESULT["potential_trash"])
        into trash_preview/ under the last analyzed root folder.

        # Funkcja przenosi wszystkie potencjalne śmieci z ostatniego skanowania
        # do podfolderu trash_preview/ w katalogu głównym.
        """
        global LAST_ANALYSIS_RESULT, LAST_ANALYZED_ROOT

        if LAST_ANALYSIS_RESULT is None or LAST_ANALYZED_ROOT is None:
            messagebox.showinfo(
                "Brak danych",
                "Najpierw przeskanuj folder, zanim spróbujesz przenieść śmieci.",
            )
            return

        potential_trash = LAST_ANALYSIS_RESULT.get("potential_trash") or []
        if not potential_trash:
            messagebox.showinfo(
                "Brak śmieci",
                "Brak potencjalnych zdjęć 'śmieciowych' do przeniesienia.",
            )
            return

        moved = move_all_potential_trash_to_preview(
            LAST_ANALYZED_ROOT,
            potential_trash,
        )

        # After moving, we clear the potential_trash list in the analysis result.
        # Po przeniesieniu czyścimy listę potential_trash w wynikach analizy.
        LAST_ANALYSIS_RESULT["potential_trash"] = []

        # Recompute stats for the labels.
        # Przeliczamy statystyki na potrzeby etykiety.
        photos = LAST_ANALYSIS_RESULT["photos"]
        exact_groups = LAST_ANALYSIS_RESULT["exact_groups"]
        num_photos = len(photos)
        num_exact_groups = len(exact_groups)
        num_potential_trash = len(LAST_ANALYSIS_RESULT["potential_trash"])

        stats_text = (
            f"Liczba znalezionych zdjęć: {num_photos}\n"
            f"Liczba grup dokładnych duplikatów: {num_exact_groups}\n"
            f"Liczba potencjalnych zdjęć 'śmieciowych': {num_potential_trash}"
        )
        stats_var.set(stats_text)

        # Refresh the Listbox to reflect the new (empty) potential trash list.
        # Odświeżamy Listbox, żeby pokazać aktualny (pusty) stan listy śmieci.
        refresh_trash_listbox()

        messagebox.showinfo(
            "Przenoszenie zakończone",
            f"Przeniesiono {moved} plików do folderu 'trash_preview' w:\n{LAST_ANALYZED_ROOT}",
        )

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

    # --- Potential trash list (read-only + move button) ---
    # Lista potencjalnych śmieci (na razie odczyt + przycisk przeniesienia wszystkich).
    trash_frame = tk.Frame(main_frame, pady=12)
    trash_frame.pack(fill="both", expand=True)

    trash_label = tk.Label(
        trash_frame,
        text="Potencjalne zdjęcia 'śmieciowe' (z backendu):",
        justify="left",
    )
    trash_label.pack(anchor="w")

    listbox_container = tk.Frame(trash_frame)
    listbox_container.pack(fill="both", expand=True)

    TRASH_LISTBOX = tk.Listbox(
        listbox_container,
        height=15,           # approximate number of rows  # przybliżona liczba widocznych wierszy
        selectmode=tk.EXTENDED,  # future: select multiple for moving  # przyszłość: zaznaczanie wielu do przenoszenia
    )
    TRASH_LISTBOX.pack(side="left", fill="both", expand=True)

    scrollbar = tk.Scrollbar(
        listbox_container,
        orient="vertical",
        command=TRASH_LISTBOX.yview,
    )
    scrollbar.pack(side="right", fill="y")

    TRASH_LISTBOX.config(yscrollcommand=scrollbar.set)

    move_button = tk.Button(
        trash_frame,
        text="Przenieś wszystkie śmieci do trash_preview",
        command=on_move_all_trash,
    )
    move_button.pack(anchor="e", pady=(8, 0))

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
