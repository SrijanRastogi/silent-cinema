"""OpenCV intertitle detector.

The detector targets the dominant silent-era convention: light lettering on a
dark card. It samples frames, binarises with Otsu, keeps text-sized connected
components, and scores the resulting block. It is a heuristic candidate
generator, not a claim of accuracy on arbitrary film stock.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import cv2
import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class DetectorConfig:
    """Documented heuristic parameters. Values are fractions unless stated."""

    max_width: int = 640
    min_coverage: float = 0.002
    max_coverage: float = 0.18
    max_background_luma: float = 110.0
    min_component_area: int = 10
    min_component_height_frac: float = 0.012
    max_component_height_frac: float = 0.45
    max_component_width_frac: float = 0.90
    min_components: int = 4
    min_block_width_frac: float = 0.10
    min_block_height_frac: float = 0.015


@dataclass(frozen=True)
class FrameAnalysis:
    """Outcome of scoring one frame."""

    is_intertitle: bool
    score: float
    coverage: float
    components: int
    reason: str


class IntertitleDetector(Protocol):
    """Boundary for native detection and future adapters."""

    def analyse(self, image: NDArray[np.uint8]) -> FrameAnalysis: ...


class OpenCvIntertitleDetector:
    """Heuristic detector for light text on dark intertitle cards."""

    def __init__(self, config: DetectorConfig | None = None) -> None:
        self.config = config or DetectorConfig()

    def analyse(self, image: NDArray[np.uint8]) -> FrameAnalysis:
        config = self.config
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image

        height, width = gray.shape[:2]
        if width == 0 or height == 0:
            return FrameAnalysis(False, 0.0, 0.0, 0, "empty_frame")
        if width > config.max_width:
            scale = config.max_width / width
            gray = cv2.resize(
                gray,
                (config.max_width, max(1, round(height * scale))),
                interpolation=cv2.INTER_AREA,
            )
            height, width = gray.shape[:2]

        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        coverage = float(cv2.countNonZero(binary)) / float(binary.size)
        if coverage > 0.5:
            # Keep the minority class as foreground: dark text on a light card.
            binary = cv2.bitwise_not(binary)
            coverage = 1.0 - coverage

        if coverage < config.min_coverage:
            return FrameAnalysis(False, 0.0, coverage, 0, "no_foreground")
        if coverage > config.max_coverage:
            return FrameAnalysis(False, 0.0, coverage, 0, "too_much_foreground")

        background = float(np.percentile(gray, 10))
        if background > config.max_background_luma:
            return FrameAnalysis(False, 0.0, coverage, 0, "background_too_bright")

        kernel = np.ones((2, 2), dtype=np.uint8)
        mask = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        count, _labels, stats, _centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)

        min_height = max(2, round(config.min_component_height_frac * height))
        max_height = max(min_height, round(config.max_component_height_frac * height))
        max_width = max(2, round(config.max_component_width_frac * width))

        xs: list[int] = []
        ys: list[int] = []
        x2s: list[int] = []
        y2s: list[int] = []
        for label in range(1, count):
            x, y, component_width, component_height, area = stats[label]
            if area < config.min_component_area:
                continue
            if component_height < min_height or component_height > max_height:
                continue
            if component_width > max_width:
                continue
            aspect = component_width / component_height
            if aspect < 0.05 or aspect > 25:
                continue
            xs.append(int(x))
            ys.append(int(y))
            x2s.append(int(x + component_width))
            y2s.append(int(y + component_height))

        components = len(xs)
        if components < config.min_components:
            return FrameAnalysis(False, 0.0, coverage, components, "too_few_components")

        block_width = max(x2s) - min(xs)
        block_height = max(y2s) - min(ys)
        if block_width / width < config.min_block_width_frac:
            return FrameAnalysis(False, 0.0, coverage, components, "text_block_too_narrow")
        if block_height / height < config.min_block_height_frac:
            return FrameAnalysis(False, 0.0, coverage, components, "text_block_too_short")

        contrast = (float(np.percentile(gray, 95)) - float(np.percentile(gray, 5))) / 255.0
        coverage_fit = min(coverage / 0.02, 1.0)
        component_fit = min(components / 8.0, 1.0)
        score = round(0.60 * contrast + 0.25 * coverage_fit + 0.15 * component_fit, 4)
        return FrameAnalysis(True, score, coverage, components, "ok")
