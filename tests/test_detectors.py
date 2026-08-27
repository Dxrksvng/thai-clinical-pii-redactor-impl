from clinical_pii_redactor.detectors import detect_pii, thai_id_checksum_is_valid


def test_valid_thai_id_checksum() -> None:
    assert thai_id_checksum_is_valid("1-1017-00207-03-0")
    assert not thai_id_checksum_is_valid("1-1017-00207-03-1")


def test_detects_explicit_clinical_pii() -> None:
    text = "ชื่อผู้ป่วย: สมชาย ใจดี HN: AB-12345 โทร 081-234-5678"
    types = {item.entity_type for item in detect_pii(text)}
    assert types == {"PERSON", "HOSPITAL_ID", "PHONE"}


def test_does_not_treat_arbitrary_text_as_name() -> None:
    assert detect_pii("ร้านสมชาย โทรสารทั่วไป") == []
