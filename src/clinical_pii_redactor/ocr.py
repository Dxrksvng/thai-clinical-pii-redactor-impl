from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


Box = tuple[int, int, int, int]


@dataclass(frozen=True)
class TextRegion:
    box: Box
    text: str
    confidence: float


class OCRProvider(Protocol):
    def read(self, image_path: Path) -> list[TextRegion]: ...


class EasyOCRProvider:
    """Optional EasyOCR adapter loaded only when the OCR extra is installed."""

    def __init__(self, languages: tuple[str, ...] = ("th", "en")) -> None:
        try:
            import easyocr
        except ImportError as exc:
            raise RuntimeError("Install the OCR extra: pip install -e '.[ocr]'") from exc
        self._reader = easyocr.Reader(list(languages))

    def read(self, image_path: Path) -> list[TextRegion]:
        regions: list[TextRegion] = []
        for polygon, text, confidence in self._reader.readtext(str(image_path)):
            xs = [int(point[0]) for point in polygon]
            ys = [int(point[1]) for point in polygon]
            regions.append(TextRegion((min(xs), min(ys), max(xs), max(ys)), text, float(confidence)))
        return regions

