"""
Turns an untrusted uploaded file into a safe, normalized image - or
rejects it. This is the real security boundary for uploads (Section 29):
- Never trusts the client's declared Content-Type.
- Verifies the bytes are genuinely one of the three allowed formats by
  actually decoding them with Pillow, not by checking the filename.
- Re-encodes from scratch, which strips any embedded scripts/metadata.
- Size is checked BEFORE full decoding, to avoid a "decompression bomb".
"""
from io import BytesIO
from PIL import Image
from fastapi import HTTPException

MAX_UPLOAD_BYTES = 5 * 1024 * 1024   # 5MB
MAX_DIMENSION = 2000                  # reject anything larger than this, either side
DISPLAY_MAX_DIMENSION = 1200          # re-encoded output is capped here

_ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


def validate_and_process_image(raw_bytes: bytes) -> tuple[bytes, str, str]:
    if len(raw_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="Image is too large. Maximum size is 5MB.")

    try:
        image = Image.open(BytesIO(raw_bytes))
        image.verify()                       # cheap structural check first
        image = Image.open(BytesIO(raw_bytes))  # verify() consumes the stream - reopen it
    except Exception:
        raise HTTPException(status_code=400, detail="This file is not a valid image.")

    if image.format not in _ALLOWED_FORMATS:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, and WebP images are allowed.")
    if image.width > MAX_DIMENSION or image.height > MAX_DIMENSION:
        raise HTTPException(status_code=400, detail=f"Image dimensions must be under {MAX_DIMENSION}x{MAX_DIMENSION}px.")

    # Re-encoding from scratch is what strips EXIF/metadata and any
    # non-image payload smuggled inside the file, rather than trusting
    # and storing the uploaded bytes exactly as received.
    image = image.convert("RGB")
    image.thumbnail((DISPLAY_MAX_DIMENSION, DISPLAY_MAX_DIMENSION))
    output = BytesIO()
    image.save(output, format="JPEG", quality=85)
    return output.getvalue(), "jpg", "image/jpeg"