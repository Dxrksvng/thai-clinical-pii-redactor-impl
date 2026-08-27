from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw

from .detectors import detect_pii
from .ocr import OCRProvider, TextRegion


@dataclass(frozen=True)
class RedactedRegion:
    box: tuple[int, int, int, int]
    entity_types: tuple[str, ...]
    confidence: float


@dataclass(frozen=True)
class PipelineResult:
    output_path: Path
    audit_path: Path
    redacted_regions: tuple[RedactedRegion, ...]
    review_required: bool


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def redact_document(
    image_path: Path,
    output_path: Path,
    ocr: OCRProvider,
    *,
    minimum_ocr_confidence: float = 0.35,
) -> PipelineResult:
    """Redact detected PII and write a metadata-only audit record.

    Raw OCR text and detected values are deliberately excluded from the audit.
    No-box results are flagged for mandatory human review.
    """
    regions = ocr.read(image_path)
    redactions: list[RedactedRegion] = []
    for region in regions:
        if region.confidence < minimum_ocr_confidence:
            continue
        detections = detect_pii(region.text)
        if detections:
            redactions.append(
                RedactedRegion(
                    region.box,
                    tuple(sorted({item.entity_type for item in detections})),
                    min(region.confidence, min(item.confidence for item in detections)),
                )
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(image_path) as source:
        image = source.convert("RGB")
        draw = ImageDraw.Draw(image)
        for redaction in redactions:
            draw.rectangle(redaction.box, fill="black")
        image.save(output_path)

    audit_path = output_path.with_suffix(output_path.suffix + ".audit.json")
    audit = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_sha256": _sha256(image_path),
        "output_sha256": _sha256(output_path),
        "region_count": len(redactions),
        "entity_counts": _entity_counts(redactions),
        "review_required": not redactions,
        "redactions": [asdict(item) for item in redactions],
    }
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    return PipelineResult(output_path, audit_path, tuple(redactions), not redactions)


def _entity_counts(redactions: Iterable[RedactedRegion]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for redaction in redactions:
        for entity_type in redaction.entity_types:
            counts[entity_type] = counts.get(entity_type, 0) + 1
    return counts

