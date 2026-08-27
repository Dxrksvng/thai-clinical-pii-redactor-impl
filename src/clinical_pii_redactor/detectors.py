from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Detection:
    entity_type: str
    value: str
    start: int
    end: int
    confidence: float
    detector: str


PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("THAI_ID", re.compile(r"(?<!\d)\d(?:[ -]?\d){12}(?!\d)")),
    ("PHONE", re.compile(r"(?<!\d)(?:\+66|0)[ -]?[689]\d(?:[ -]?\d){7}(?!\d)")),
    ("HOSPITAL_ID", re.compile(r"(?i)\b(?:HN|AN)\s*[:#.-]?\s*[A-Z0-9/-]{4,20}\b")),
    (
        "DATE_OF_BIRTH",
        re.compile(r"(?i)(?:DOB|เกิด|วันเกิด)\s*[:.-]?\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"),
    ),
)

NAME_LABEL = re.compile(
    r"(?i)(?:ชื่อ(?:ผู้ป่วย)?|patient\s*name|name)\s*[:.-]\s*([^\n,;]{2,80})"
)


def thai_id_checksum_is_valid(value: str) -> bool:
    digits = re.sub(r"\D", "", value)
    if len(digits) != 13 or len(set(digits)) == 1:
        return False
    check = (11 - sum(int(digits[i]) * (13 - i) for i in range(12)) % 11) % 10
    return check == int(digits[-1])


def detect_pii(text: str) -> list[Detection]:
    """Detect explicit Thai clinical-document identifiers in OCR text.

    The detector is intentionally conservative for names: it only redacts text
    following an explicit name label. A production system should add a licensed,
    evaluated Thai NER model and a human-review queue.
    """
    detections: list[Detection] = []
    for entity_type, pattern in PATTERNS:
        for match in pattern.finditer(text):
            if entity_type == "THAI_ID" and not thai_id_checksum_is_valid(match.group()):
                continue
            detections.append(
                Detection(entity_type, match.group(), match.start(), match.end(), 1.0, "rule")
            )

    for match in NAME_LABEL.finditer(text):
        start, end = match.span(1)
        detections.append(Detection("PERSON", match.group(1), start, end, 0.85, "label-context"))

    return sorted(detections, key=lambda item: (item.start, item.end))

