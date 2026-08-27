import json
from pathlib import Path

from PIL import Image

from clinical_pii_redactor.ocr import TextRegion
from clinical_pii_redactor.pipeline import redact_document


class FakeOCR:
    def __init__(self, regions: list[TextRegion]) -> None:
        self.regions = regions

    def read(self, image_path: Path) -> list[TextRegion]:
        return self.regions


def test_redacts_pixels_and_excludes_raw_pii_from_audit(tmp_path: Path) -> None:
    source = tmp_path / "synthetic.png"
    output = tmp_path / "redacted.png"
    Image.new("RGB", (200, 100), "white").save(source)
    pii = "HN: TEST-1234"

    result = redact_document(source, output, FakeOCR([TextRegion((10, 10, 100, 40), pii, 0.99)]))

    assert Image.open(output).getpixel((20, 20)) == (0, 0, 0)
    audit_text = result.audit_path.read_text(encoding="utf-8")
    assert pii not in audit_text
    assert json.loads(audit_text)["entity_counts"] == {"HOSPITAL_ID": 1}
    assert not result.review_required


def test_no_box_fails_to_human_review(tmp_path: Path) -> None:
    source = tmp_path / "synthetic.png"
    Image.new("RGB", (80, 40), "white").save(source)
    result = redact_document(source, tmp_path / "out.png", FakeOCR([]))
    assert result.review_required

