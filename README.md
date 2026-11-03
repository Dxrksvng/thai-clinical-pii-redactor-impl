<div align="center">

# Thai Clinical PII Redactor (implementation)

**Clean-room, privacy-first redaction of synthetic Thai clinical document images.**

![Visibility private](https://img.shields.io/badge/Visibility-private-red?style=for-the-badge) ![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white) ![License MIT](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge) ![Data synthetic only](https://img.shields.io/badge/Data-synthetic_only-2ea44f?style=for-the-badge) ![Tests pytest](https://img.shields.io/badge/Tests-pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)

</div>

> Prototype, not a PDPA certification or production medical system. Public overview: `Dxrksvng/thai-clinical-pii-redactor`.

## Tech stack

<p align="center">
  <img src="https://skillicons.dev/icons?i=py,opencv,pytest,github&perline=10" alt="Tech stack" />
</p>

## Pipeline

```mermaid
flowchart LR
    IMG["Document image"] --> OCR["OCRProvider (protocol)\nEasyOCRProvider or SidecarOCRProvider"]
    OCR --> TR["TextRegion\ntext + bounding box"]
    TR --> DET["detect_pii()\nThai ID with checksum, mobile phone,\nHN/AN, labelled DOB, labelled names"]
    DET --> RED["redact_document()\nopaque black rectangles"]
    RED --> OUT["Redacted image"]
    RED --> AUD[("Audit record\nfile SHA-256 + entity counts only")]
    DET -- "zero detections" --> REV{{"Mandatory human review"}}
```

## Code map

| Path | Role |
|---|---|
| `src/clinical_pii_redactor/ocr.py` | `TextRegion`, `OCRProvider` protocol, optional `EasyOCRProvider` |
| `src/clinical_pii_redactor/detectors.py` | `detect_pii`, Thai national-ID checksum validation |
| `src/clinical_pii_redactor/pipeline.py` | `redact_document`, `PipelineResult`, metadata-only audit counts |
| `src/clinical_pii_redactor/cli.py` | `clinical-pii-redact` command, sidecar OCR for deterministic demos |
| `examples/synthetic_regions.json` | Pre-computed OCR regions for reproducible tests |
| `tests/` | Detector and pipeline tests |

---

A clean-room, privacy-first prototype for redacting personally identifiable information from **synthetic Thai clinical-document images**.

This repository was rebuilt from scratch as a personal engineering project. It contains no employer source code, patient data, internal architecture, production configuration, or confidential evaluation material. It does not represent any employer's security practices.

## What it does

```text
document image
  → OCR text regions
  → deterministic PII detection
  → irreversible black-box redaction
  → metadata-only audit record
  → mandatory review when no region is detected
```

The implemented baseline detects:

- Thai national IDs with checksum validation
- Thai mobile-phone numbers
- hospital identifiers such as HN/AN
- labelled dates of birth
- names following explicit Thai/English name labels

EasyOCR is available through an optional adapter. The deterministic sidecar adapter makes tests reproducible without downloading model weights.

## Safety boundaries

- No raw OCR text or detected values are written to audit logs.
- A zero-detection result is **not** treated as safe; it is routed to human review.
- Redaction uses opaque black rectangles, not reversible blur or pixelation.
- The baseline name detector is deliberately conservative. Production use requires a licensed and independently evaluated Thai NER model.
- This project is a prototype, not a PDPA certification or production medical system.

## Install and test

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```

For EasyOCR:

```bash
pip install -e '.[ocr]'
clinical-pii-redact input.png output/redacted.png
```

For a deterministic synthetic demo:

```bash
clinical-pii-redact examples/synthetic_document.png output/redacted.png \
  --ocr-json examples/synthetic_regions.json
```

## Evaluation roadmap

Before any real-world use:

1. Generate or license a Thai synthetic document corpus.
2. Annotate PII boxes by entity type.
3. Split by template/source to prevent leakage.
4. Report per-class precision, recall, F1, and document-level leakage rate.
5. Add Thai NER and barcode detection behind versioned adapters.
6. Require human review for low-confidence and no-box cases.

## License

MIT. Synthetic or third-party datasets keep their own licenses and are not included here.
