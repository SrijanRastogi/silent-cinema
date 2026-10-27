"""Media probing, detection, and OCR building blocks."""

from __future__ import annotations

from silent_cinema.media.detector import (
    DetectorConfig,
    FrameAnalysis,
    IntertitleDetector,
    OpenCvIntertitleDetector,
)
from silent_cinema.media.ocr import OcrEngine, OcrResult, TesseractOcr
from silent_cinema.media.pipeline import DetectionOptions, DetectionResult, detect_intertitles
from silent_cinema.media.probe import MediaInfo, probe_media

__all__ = [
    "DetectionOptions",
    "DetectionResult",
    "DetectorConfig",
    "FrameAnalysis",
    "IntertitleDetector",
    "MediaInfo",
    "OcrEngine",
    "OcrResult",
    "OpenCvIntertitleDetector",
    "TesseractOcr",
    "detect_intertitles",
    "probe_media",
]
