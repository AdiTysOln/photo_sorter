from typing import List

from .models import PhotoInfo


def sort_photos_by_taken_date(
    photos: List[PhotoInfo],
    descending: bool = False,
) -> List[PhotoInfo]:
    """
    Return a new list of photos sorted by 'taken_at' date.
    Photos without date (taken_at is None) go to the end.
    """

    def sort_key(photo: PhotoInfo):
        # True > False, więc zdjęcia bez daty trafią na koniec
        return (photo.taken_at is None, photo.taken_at)

    # Zwracamy NOWĄ listę, oryginalnej nie ruszamy
    return sorted(photos, key=sort_key, reverse=descending)
