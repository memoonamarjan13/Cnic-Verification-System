
import re


# ============================================================
# CLEAN CNIC
# ============================================================

def clean_cnic(cnic: str) -> str:
    """
    Keep only numeric digits.

    Example:
        17301-0218141-5
        ->
        1730102181415
    """

    if not cnic:
        return ""

    return re.sub(r"\D", "", str(cnic))


# ============================================================
# VALIDATE CNIC
# ============================================================

def validate_cnic(cnic: str) -> bool:
    """
    Pakistani CNIC must contain exactly 13 digits.
    """

    cleaned = clean_cnic(cnic)

    return len(cleaned) == 13


# ============================================================
# FORMAT CNIC
# ============================================================

def format_cnic(cnic: str) -> str | None:
    """
    Convert 13 digits into Pakistani CNIC format.

    Example:
        1730102181415
        ->
        17301-0218141-5
    """

    cleaned = clean_cnic(cnic)

    if len(cleaned) != 13:
        return None

    return (
        f"{cleaned[:5]}-"
        f"{cleaned[5:12]}-"
        f"{cleaned[12]}"
    )


# ============================================================
# EXTRACT CNIC FROM OCR TEXT
# ============================================================

def extract_cnic(text: str) -> str | None:
    """
    Extract a Pakistani CNIC from OCR text.

    Supported formats:

        17301-0218141-5
        1730102181415
        17301 0218141 5
        17301-02181415

    Only a verified 13-digit candidate is returned.

    Incomplete OCR results are rejected.
    """

    if not text:
        print("NO OCR TEXT FOUND")
        return None

    text = str(text)

    # Normalize spaces
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()

    print("\n========== CNIC EXTRACTION ==========")
    print("OCR TEXT FOR CNIC EXTRACTION:", text)

    # ========================================================
    # 1. STANDARD CNIC FORMAT
    #
    # Example:
    # 17301-0218141-5
    # ========================================================

    standard_pattern = (
        r"(?<!\d)"
        r"(\d{5})"
        r"[-\s]"
        r"(\d{7})"
        r"[-\s]"
        r"(\d)"
        r"(?!\d)"
    )

    match = re.search(standard_pattern, text)

    if match:

        digits = "".join(match.groups())

        formatted = format_cnic(digits)

        if formatted:

            print(
                "VALID CNIC FOUND USING STANDARD FORMAT:",
                formatted
            )

            return formatted

    # ========================================================
    # 2. EXACT 13 DIGITS
    #
    # Example:
    # 1730102181415
    # ========================================================

    pattern_13 = r"(?<!\d)(\d{13})(?!\d)"

    match = re.search(pattern_13, text)

    if match:

        digits = match.group(1)

        formatted = format_cnic(digits)

        if formatted:

            print(
                "VALID CNIC FOUND FROM 13 DIGITS:",
                formatted
            )

            return formatted

    # ========================================================
    # 3. FIRST HYPHEN ONLY
    #
    # Example:
    # 17301-02181415
    # ========================================================

    compact_pattern = (
        r"(?<!\d)"
        r"(\d{5})"
        r"-"
        r"(\d{8})"
        r"(?!\d)"
    )

    match = re.search(compact_pattern, text)

    if match:

        digits = (
            match.group(1)
            + match.group(2)
        )

        formatted = format_cnic(digits)

        if formatted:

            print(
                "VALID CNIC FOUND FROM COMPACT FORMAT:",
                formatted
            )

            return formatted

    # ========================================================
    # 4. SEARCH NUMERIC SEQUENCES
    # ========================================================

    digit_sequences = re.findall(r"\d+", text)

    for sequence in digit_sequences:

        if len(sequence) == 13:

            formatted = format_cnic(sequence)

            if formatted:

                print(
                    "VALID CNIC FOUND FROM DIGIT SEQUENCE:",
                    formatted
                )

                return formatted

    # ========================================================
    # 5. INCOMPLETE OR INVALID OCR
    # ========================================================

    print("NO VALID CNIC FOUND")
    print("====================================")

    return None