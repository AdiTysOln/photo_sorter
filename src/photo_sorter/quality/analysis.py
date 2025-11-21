from __future__ import annotations

from pathlib import Path
from typing import Optional

import cv2  # OpenCV library for image processing
import numpy as np  # used for variance calculation

from photo_sorter.scanning.models import PhotoInfo  # our model from Stage 2/3

def compute_blur_score_for_path(image_path: Path) -> Optional[float]:
    """
    Compute a simple blur score for a single image file using the variance
    of the Laplacian (classic OpenCV sharpness metric).

    :param image_path: Path to an image file on disk.
    :return: Blur score (higher = sharper, lower = more blurred), or None if
             the image could not be read.
    """
    # Load image as grayscale
    # This gives us one "brightness" value per pixel instead of 3 channels (RGB/BGR)
    img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)

    if img is None:
        # If OpenCV couldn't load the file (e.g. corrupted / no permissions),
        # return None - higher level code can handle it.
        return None

    # Compute Laplacian (detects brightness changes, i.e. "edges")
    # Sharp image -> many edges -> high Laplacian variance
    # Blurry image -> few edges -> low Laplacian variance
    laplacian = cv2.Laplacian(img, cv2.CV_64F)

    # Variance (how much values differ from the mean)
    variance = float(np.var(laplacian))

    return variance

def compute_brightness_score_for_path(image_path: Path) -> Optional[float]:
    """
    Compute a brightness score (mean pixel intensity) for a single image file.

    :param image_path: Path to an image file on disk.
    :return: Brightness score (0-255), or None if the file could not be read.
    """
    img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)

    if img is None:
        return None

    brightness = float(np.mean(img))
    return brightness

def annotate_photos_with_quality(photos: list[PhotoInfo]) -> None:
    """
    Annotate a list of PhotoInfo objects with basic quality metrics:
    - blur_score (variance of Laplacian)
    - brightness_score (mean grayscale intensity)

    This function mutates the PhotoInfo objects in-place.

    :param photos: List of PhotoInfo objects created by the scanning module
                   (e.g. build_photo_infos(...) used in debug_scan.py).
    """
    for photo in photos:
        # Use existing metrics based on file path
        blur = compute_blur_score_for_path(photo.path)
        brightness = compute_brightness_score_for_path(photo.path)

        photo.blur_score = blur
        photo.brightness_score = brightness

        # At this stage we DON'T decide yet if the photo is trash,
        # so we leave is_potential_trash as None.
        # Trash flags will be added in the next function.

def find_potential_trash_photos(
    photos: list[PhotoInfo],
    blur_threshold: float = 100.0,
    brightness_too_dark: float = 40.0,
    brightness_too_bright: float = 210.0,
) -> list[PhotoInfo]:
    """
    Mark photos as potential trash based on blur and brightness criteria.

    The function assumes blur_score and brightness_score have already been
    computed by annotate_photos_with_quality().

    Returns a list of photos classified as potential trash.
    """
    trash_list = []

    for photo in photos:
        blur = photo.blur_score
        brightness = photo.brightness_score

        # If data missing - treat as "uncertain", but not as certain trash
        if blur is None or brightness is None:
            photo.is_potential_trash = None
            continue

        # Rules:
        is_blurry = blur < blur_threshold
        is_dark = brightness < brightness_too_dark
        is_bright = brightness > brightness_too_bright

        if is_blurry or is_dark or is_bright:
            photo.is_potential_trash = True
            trash_list.append(photo)
        else:
            photo.is_potential_trash = False

    return trash_list