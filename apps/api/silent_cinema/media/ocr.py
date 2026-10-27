"""Tesseract OCR adapter with deterministic preprocessing."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import cv2
import pytesseract
from PIL import Image
from pytesseract import Output

LANGUAGE_PATTERN = re.compile(r"^[a-z0-9_]+(\+[a-z0-9_]+)*$")


class OcrError(RuntimeError):
    """Tesseract failed with a stable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class OcrResult:
    """Recognised text and word-confidence summary."""

    text: str
    confidence: float
    word_count: int


class OcrEngine(Protocol):
    """Boundary for Tesseract and future OCR engines."""

    def read(self, image_path: Path) -> OcrResult: ...


def normalize_ocr_text(raw: str) -> str:
    """Collapse spacing and drop lines without letters or digits."""
    lines: list[str] = []
    for line in raw.replace("\r", "").split("\n"):
        cleaned = re.sub(r"[ \t]+", " ", line).strip()
        if not cleaned:
            continue
        if not any(character.isalnum() for character in cleaned):
            continue
        lines.append(cleaned)
    return "\n".join(lines)


class TesseractOcr:
    """Read a still frame with Tesseract, using word-level output."""

    def __init__(
        self,
        *,
        binary: str = "tesseract",
        language: str = "eng",
        page_segmentation_mode: int = 6,
        timeout_seconds: float = 60,
    ) -> None:
        if not LANGUAGE_PATTERN.match(language):
            raise OcrError("ocr_language_invalid", "The OCR language tag is not valid.")
        self.binary = binary
        self.language = language
        self.page_segmentation_mode = page_segmentation_mode
        self.timeout_seconds = timeout_seconds

    def read(self, image_path: Path) -> OcrResult:
        image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise OcrError("frame_unreadable", "The sampled frame could not be decoded.")

        upscaled = cv2.resize(image, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
        _, binary = cv2.threshold(upscaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # Tesseract expects dark glyphs on a light page.
        prepared = cv2.bitwise_not(binary)
        prepared = cv2.copyMakeBorder(prepared, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)

        pytesseract.pytesseract.tesseract_cmd = self.binary
        try:
            data = pytesseract.image_to_data(
                Image.fromarray(prepared),
                lang=self.language,
                config=f"--oem 3 --psm {self.page_segmentation_mode}",
                output_type=Output.DICT,
                timeout=self.timeout_seconds,
            )
        except pytesseract.TesseractNotFoundError as error:
            raise OcrError(
                "ocr_unavailable", "Tesseract is not installed or not on PATH."
            ) from error
        except pytesseract.TesseractError as error:
            message = str(error)
            code = (
                "ocr_language_unavailable" if "Failed loading language" in message else "ocr_failed"
            )
            raise OcrError(code, "Tesseract could not read this frame.") from error
        except RuntimeError as error:
            raise OcrError("ocr_timeout", "Tesseract exceeded its time limit.") from error

        words: list[str] = []
        confidences: list[float] = []
        grouped: dict[tuple[int, int, int], list[str]] = {}
        raw_text = data.get("text", [])
        raw_conf = data.get("conf", [])
        for index, word in enumerate(raw_text):
            cleaned = str(word).strip()
            if not cleaned:
                continue
            words.append(cleaned)
            try:
                confidence = float(raw_conf[index])
            except (IndexError, TypeError, ValueError):
                confidence = -1.0
            if confidence >= 0:
                confidences.append(confidence)
            key = (
                int(data["block_num"][index]),
                int(data["par_num"][index]),
                int(data["line_num"][index]),
            )
            grouped.setdefault(key, []).append(cleaned)

        text = normalize_ocr_text("\n".join(" ".join(parts) for parts in grouped.values()))
        mean_confidence = (
            round(sum(confidences) / len(confidences) / 100.0, 4) if confidences else 0.0
        )
        return OcrResult(text=text, confidence=mean_confidence, word_count=len(words))
