"""Tests for security helpers."""

from __future__ import annotations

from pathlib import Path

from app.utils.security import (
    content_hash,
    is_allowed_image,
    is_valid_pdf,
    is_within_directory,
    sanitize_filename,
    sniff_image_type,
)


def test_sanitize_filename_strips_path():
    # Path.name strips directory components, so only the basename remains
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("my file (1).pdf") == "my_file_1_.pdf"
    assert sanitize_filename("...pdf") == "pdf"


def test_sanitize_filename_empty():
    assert sanitize_filename("!!!") == "file"


def test_is_valid_pdf():
    assert is_valid_pdf(b"%PDF-1.4 rest") is True
    assert is_valid_pdf(b"not a pdf") is False


def test_content_hash():
    assert content_hash(b"abc") == content_hash(b"abc")
    assert content_hash(b"abc") != content_hash(b"abd")


def test_sniff_image_png():
    import base64

    # 1x1 PNG
    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )
    assert sniff_image_type(png) == "image/png"
    assert is_allowed_image(png) is True


def test_sniff_image_rejects_text():
    assert sniff_image_type(b"just some text") is None
    assert is_allowed_image(b"just some text") is False


def test_is_within_directory(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    inside = base / "file.txt"
    inside.write_text("x")
    outside = tmp_path / "outside.txt"
    outside.write_text("y")
    assert is_within_directory(inside, base) is True
    assert is_within_directory(outside, base) is False
