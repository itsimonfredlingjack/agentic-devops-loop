"""QR code generation unit tests."""

import base64

import pytest


@pytest.mark.asyncio
async def test_qr_generation():
    """QR code generates valid base64 PNG."""
    from eventit.services.ticket_service import _generate_qr_b64

    result = _generate_qr_b64("test-uuid-1234")
    assert isinstance(result, str)
    assert len(result) > 100  # Not empty

    # Verify it's valid base64
    decoded = base64.b64decode(result)
    assert decoded[:8] == b"\x89PNG\r\n\x1a\n"  # PNG magic bytes


@pytest.mark.asyncio
async def test_qr_uniqueness():
    """Different inputs produce different QR codes."""
    from eventit.services.ticket_service import _generate_qr_b64

    qr1 = _generate_qr_b64("uuid-aaa")
    qr2 = _generate_qr_b64("uuid-bbb")
    assert qr1 != qr2
