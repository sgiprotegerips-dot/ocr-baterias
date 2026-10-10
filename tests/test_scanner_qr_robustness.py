import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import cv2
import numpy as np
import segno

from src.bateria.qr_codec import encode_compact_payload, decode_payload
from src.bateria.qr_detect import _decode_image, detect_identity_qr


def _create_synthetic_qr(text="BRP1|A|2026-09-26|1098765432|PEREZ GOMEZ", scale=6):
    qr = segno.make(text, error="m")
    buf = io.BytesIO()
    qr.save(buf, kind="png", scale=scale, border=2)
    buf.seek(0)
    return cv2.imdecode(np.frombuffer(buf.getvalue(), np.uint8), cv2.IMREAD_GRAYSCALE)


def test_qr_scanner_top_right():
    qr_img = _create_synthetic_qr()
    qh, qw = qr_img.shape
    page = np.full((3508, 2480), 248, dtype=np.uint8)
    page[200 : 200 + qh, 2000 : 2000 + qw] = qr_img

    decoded = _decode_image(page)
    assert decoded is not None
    assert decoded.startswith("BRP1|A|")
    payload = decode_payload(decoded)
    assert payload["cedula"] == "1098765432"
    print("PASS: test_qr_scanner_top_right")


def test_qr_scanner_bottom_signature():
    qr_img = _create_synthetic_qr()
    qh, qw = qr_img.shape
    page = np.full((3508, 2480), 248, dtype=np.uint8)
    page[2800 : 2800 + qh, 1800 : 1800 + qw] = qr_img

    decoded = _decode_image(page)
    assert decoded is not None
    payload = decode_payload(decoded)
    assert payload["cedula"] == "1098765432"
    print("PASS: test_qr_scanner_bottom_signature")


def test_qr_scanner_tilted_manual_sticker():
    qr_img = _create_synthetic_qr()
    qh, qw = qr_img.shape
    M = cv2.getRotationMatrix2D((qw / 2.0, qh / 2.0), 12, 1.0)
    qr_tilted = cv2.warpAffine(qr_img, M, (qw, qh), borderValue=255)

    page = np.full((3508, 2480), 248, dtype=np.uint8)
    page[200 : 200 + qh, 2000 : 2000 + qw] = qr_tilted

    decoded = _decode_image(page)
    assert decoded is not None
    payload = decode_payload(decoded)
    assert payload["cedula"] == "1098765432"
    print("PASS: test_qr_scanner_tilted_manual_sticker")


def test_qr_scanner_inverted_180_degrees():
    qr_img = _create_synthetic_qr()
    qh, qw = qr_img.shape
    page = np.full((3508, 2480), 248, dtype=np.uint8)
    page[200 : 200 + qh, 2000 : 2000 + qw] = qr_img

    page_180 = cv2.rotate(page, cv2.ROTATE_180)
    decoded = _decode_image(page_180)
    assert decoded is not None
    payload = decode_payload(decoded)
    assert payload["cedula"] == "1098765432"
    print("PASS: test_qr_scanner_inverted_180_degrees")


def test_qr_scanner_faded_thermal():
    qr_img = _create_synthetic_qr()
    qh, qw = qr_img.shape
    faded = ((qr_img.astype(float) / 255.0) * (215 - 110) + 110).astype(np.uint8)

    page = np.full((3508, 2480), 248, dtype=np.uint8)
    page[200 : 200 + qh, 2000 : 2000 + qw] = faded

    decoded = _decode_image(page)
    assert decoded is not None
    payload = decode_payload(decoded)
    assert payload["cedula"] == "1098765432"
    print("PASS: test_qr_scanner_faded_thermal")


def test_qr_scanner_blurred():
    qr_img = _create_synthetic_qr()
    qh, qw = qr_img.shape
    blurred = cv2.GaussianBlur(qr_img, (5, 5), 1.2)

    page = np.full((3508, 2480), 248, dtype=np.uint8)
    page[200 : 200 + qh, 2000 : 2000 + qw] = blurred

    decoded = _decode_image(page)
    assert decoded is not None
    payload = decode_payload(decoded)
    assert payload["cedula"] == "1098765432"
    print("PASS: test_qr_scanner_blurred")


def test_detect_identity_qr_classified_pipeline():
    qr_img = _create_synthetic_qr()
    qh, qw = qr_img.shape
    page1 = np.full((2400, 1700), 250, dtype=np.uint8)
    page1[100 : 100 + qh, 1300 : 1300 + qw] = qr_img

    classified = [
        {"target_page": 1, "img": page1, "info": {"kind": "consentimiento"}},
        {"target_page": 2, "img": np.full((2400, 1700), 255, dtype=np.uint8), "info": {"kind": "ficha"}},
    ]
    ident = detect_identity_qr(classified)
    assert ident is not None
    assert ident["cedula"] == "1098765432"
    assert ident["forma"] == "A"
    print("PASS: test_detect_identity_qr_classified_pipeline")


if __name__ == "__main__":
    test_qr_scanner_top_right()
    test_qr_scanner_bottom_signature()
    test_qr_scanner_tilted_manual_sticker()
    test_qr_scanner_inverted_180_degrees()
    test_qr_scanner_faded_thermal()
    test_qr_scanner_blurred()
    test_detect_identity_qr_classified_pipeline()
    print("\nALL SCANNER QR ROBUSTNESS TESTS PASSED SUCCESSFULLY!")
