from __future__ import annotations

import argparse
import json
from pathlib import Path

from .ocr import EasyOCRProvider, TextRegion
from .pipeline import redact_document


class SidecarOCRProvider:
    def __init__(self, sidecar: Path) -> None:
        self.sidecar = sidecar

    def read(self, image_path: Path) -> list[TextRegion]:
        del image_path
        payload = json.loads(self.sidecar.read_text(encoding="utf-8"))
        return [TextRegion(tuple(item["box"]), item["text"], item["confidence"]) for item in payload]


def main() -> None:
    parser = argparse.ArgumentParser(description="Redact PII from a document image")
    parser.add_argument("image", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--ocr-json", type=Path, help="Use deterministic OCR regions from JSON")
    args = parser.parse_args()

    provider = SidecarOCRProvider(args.ocr_json) if args.ocr_json else EasyOCRProvider()
    result = redact_document(args.image, args.output, provider)
    print(json.dumps({
        "output": str(result.output_path),
        "audit": str(result.audit_path),
        "redacted_regions": len(result.redacted_regions),
        "review_required": result.review_required,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

