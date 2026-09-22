
import os
import re
import cv2
import easyocr


# ============================================================
# CREATE OCR READER ONLY ONCE
# ============================================================

reader = easyocr.Reader(
    ["en"],
    gpu=False
)


# ============================================================
# EXTRACT TEXT FROM CNIC IMAGE
# ============================================================

def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from a CNIC image.

    Uses multiple preprocessing methods
    and OCR attempts to improve digit recognition.
    """

    if not os.path.exists(image_path):

        raise FileNotFoundError(
            "Image file does not exist."
        )

    image = cv2.imread(image_path)

    if image is None:

        raise ValueError(
            "Could not read the uploaded image."
        )

    height, width = image.shape[:2]

    print("\n========== IMAGE INFORMATION ==========")
    print("Image width:", width)
    print("Image height:", height)
    print("=======================================")

    # ========================================================
    # IDENTITY NUMBER REGION
    # ========================================================
    #
    # Use a wider region so that digits are not cut off.
    #
    # IMPORTANT:
    # These coordinates depend on your CNIC image layout.
    #

    x1 = int(width * 0.10)
    x2 = int(width * 0.90)

    y1 = int(height * 0.55)
    y2 = int(height * 0.90)

    roi = image[y1:y2, x1:x2]

    if roi.size == 0:

        raise ValueError(
            "Could not locate Identity Number area."
        )

    # ========================================================
    # UPSCALE
    # ========================================================

    roi = cv2.resize(
        roi,
        None,
        fx=4,
        fy=4,
        interpolation=cv2.INTER_CUBIC
    )

    # ========================================================
    # GRAYSCALE
    # ========================================================

    gray = cv2.cvtColor(
        roi,
        cv2.COLOR_BGR2GRAY
    )

    # ========================================================
    # CONTRAST ENHANCEMENT
    # ========================================================

    clahe = cv2.createCLAHE(
        clipLimit=3.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(gray)

    # ========================================================
    # THRESHOLD
    # ========================================================

    threshold = cv2.threshold(
        enhanced,
        0,
        255,
        cv2.THRESH_BINARY
        + cv2.THRESH_OTSU
    )[1]

    # ========================================================
    # SHARPEN IMAGE
    # ========================================================

    sharpen_kernel = (
        "not_used"
    )

    sharpened = cv2.detailEnhance(
        cv2.cvtColor(
            roi,
            cv2.COLOR_BGR2RGB
        ),
        sigma_s=10,
        sigma_r=0.15
    )

    sharpened_gray = cv2.cvtColor(
        sharpened,
        cv2.COLOR_RGB2GRAY
    )

    # ========================================================
    # OCR ATTEMPTS
    # ========================================================

    images = [
        ("ENHANCED", enhanced),
        ("THRESHOLD", threshold),
        ("GRAY", gray),
        ("SHARPENED", sharpened_gray)
    ]

    all_text = []

    for name, processed_image in images:

        print(
            f"\n========== OCR ATTEMPT: {name} =========="
        )

        results = reader.readtext(
            processed_image,
            detail=1,
            paragraph=False,
            allowlist="0123456789-"
        )

        for result in results:

            text = result[1].strip()
            confidence = result[2]

            print(
                f"OCR CNIC TEXT: {text} | "
                f"CONFIDENCE: {confidence:.3f}"
            )

            if text:

                all_text.append(text)

    # ========================================================
    # COMBINE OCR RESULTS
    # ========================================================

    final_text = " ".join(all_text)

    print("\n========== FINAL OCR TEXT ==========")
    print(final_text)
    print("====================================")

    return final_text
