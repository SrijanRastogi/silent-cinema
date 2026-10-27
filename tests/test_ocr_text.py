"""Unit tests for OCR text normalisation and adapter validation."""

from __future__ import annotations

import pytest
from silent_cinema.media.ocr import OcrError, TesseractOcr, normalize_ocr_text


def test_normalisation_collapses_spacing_and_keeps_unicode() -> None:
    raw = "  Chapitre   I  \n\n— «\nParis,   1927\r\n"

    assert normalize_ocr_text(raw) == "Chapitre I\nParis, 1927"


def test_normalisation_drops_punctuation_only_noise() -> None:
    assert normalize_ocr_text("...\n| | |\nTHE END\n***") == "THE END"


def test_normalisation_preserves_accented_and_non_latin_text() -> None:
    assert normalize_ocr_text("ÉLÉGIE\n第一章\n Grüße") == "ÉLÉGIE\n第一章\nGrüße"


def test_invalid_language_tag_is_rejected_before_tesseract() -> None:
    with pytest.raises(OcrError) as caught:
        TesseractOcr(language="eng; rm -rf /")

    assert caught.value.code == "ocr_language_invalid"
