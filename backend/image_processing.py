from io import BytesIO

from PIL import Image, ImageOps


def optimize_image(image_bytes, max_dimension=1024, quality=85):
    """Resize and compress an uploaded image for Gemini analysis."""

    image = Image.open(BytesIO(image_bytes))

    # Correct orientation using EXIF metadata
    image = ImageOps.exif_transpose(image)

    # Convert to RGB for JPEG compatibility
    image = image.convert("RGB")

    # Resize while preserving aspect ratio
    image.thumbnail(
        (max_dimension, max_dimension),
        Image.Resampling.LANCZOS,
    )

    # Compress image into memory
    buffer = BytesIO()

    image.save(
        buffer,
        format="JPEG",
        quality=quality,
        optimize=True,
    )

    return buffer.getvalue()
