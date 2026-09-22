from Backend.database import supabase


# ============================================================
# CLEAN DIGITS
# ============================================================

def clean_digits(value: str) -> str:
    """
    Keep only numeric digits.

    Example:
        17301-0218141-5
        ->
        1730102181415
    """

    if not value:
        return ""

    return "".join(
        character
        for character in value
        if character.isdigit()
    )


# ============================================================
# NORMALIZE CNIC
# ============================================================

def normalize_cnic(cnic: str) -> str:
    """
    Convert a 13-digit CNIC into standard format.

    Example:
        1730102181415
        ->
        17301-0218141-5
    """

    digits = clean_digits(cnic)

    if len(digits) != 13:
        return cnic

    return (
        f"{digits[:5]}-"
        f"{digits[5:12]}-"
        f"{digits[12]}"
    )


# ============================================================
# LEVENSHTEIN DISTANCE
# ============================================================

def levenshtein_distance(a: str, b: str) -> int:
    """
    Calculate character difference between two strings.
    """

    if a == b:
        return 0

    if not a:
        return len(b)

    if not b:
        return len(a)

    previous_row = list(range(len(b) + 1))

    for i, char_a in enumerate(a, start=1):

        current_row = [i]

        for j, char_b in enumerate(b, start=1):

            insert_cost = current_row[j - 1] + 1

            delete_cost = previous_row[j] + 1

            replace_cost = (
                previous_row[j - 1]
                + (char_a != char_b)
            )

            current_row.append(
                min(
                    insert_cost,
                    delete_cost,
                    replace_cost
                )
            )

        previous_row = current_row

    return previous_row[-1]


# ============================================================
# FIND CLOSE CNIC
# ============================================================

def find_matching_cnic(
    ocr_cnic: str,
    records: list
):
    """
    Compare noisy OCR CNIC against CNICs
    stored in Supabase.

    Returns:
        Matching database record
        or None
    """

    ocr_digits = clean_digits(ocr_cnic)

    if not ocr_digits:
        return None

    print("\n========== CNIC DATABASE MATCHING ==========")
    print("OCR DIGITS:", ocr_digits)

    best_record = None
    best_distance = 999

    for record in records:

        database_cnic = record.get("identity_number")

        if not database_cnic:
            continue

        database_digits = clean_digits(
            database_cnic
        )

        distance = levenshtein_distance(
            ocr_digits,
            database_digits
        )

        print(
            "DATABASE CNIC:",
            database_cnic,
            "| OCR:",
            ocr_digits,
            "| DISTANCE:",
            distance
        )

        if distance < best_distance:
            best_distance = distance
            best_record = record

    # ========================================================
    # SAFETY CHECK
    # ========================================================

    if best_record is not None:

        database_cnic = best_record.get(
            "identity_number"
        )

        database_digits = clean_digits(
            database_cnic
        )

        # First 5 digits must match
        if (
            len(ocr_digits) >= 5
            and len(database_digits) == 13
            and ocr_digits[:5] == database_digits[:5]
        ):

            # Allow maximum 2 OCR errors
            if best_distance <= 2:

                print(
                    "CLOSE CNIC MATCH FOUND:",
                    database_cnic
                )

                print(
                    "MATCH DISTANCE:",
                    best_distance
                )

                print(
                    "=========================================="
                )

                return best_record

    print("NO CLOSE CNIC MATCH FOUND")
    print("==========================================")

    return None


# ============================================================
# VERIFY CNIC
# ============================================================

def verify_cnic(cnic: str) -> dict:
    """
    Verify CNIC against Supabase.

    Process:

        OCR CNIC
             ↓
        Exact database search
             ↓
        If not found
             ↓
        Fuzzy OCR comparison
             ↓
        Database record
    """

    # ========================================================
    # NO CNIC
    # ========================================================

    if not cnic:

        return {
            "success": False,
            "cnic": None,
            "status": "REJECTED",
            "message": (
                "Could not extract a CNIC number "
                "from the uploaded image."
            ),
            "id": None,
            "name": None,
            "father_name": None,
            "gender": None,
            "country_to_stay": None,
            "identity_number": None,
            "date_of_birth": None,
            "date_of_issue": None,
            "date_of_expiry": None
        }

    # ========================================================
    # CLEAN OCR VALUE
    # ========================================================

    cleaned_ocr = clean_digits(cnic)

    print("\n========== CNIC VERIFICATION ==========")

    print("EXTRACTED CNIC:", cnic)

    print("OCR DIGITS:", cleaned_ocr)

    # ========================================================
    # NORMALIZE CNIC
    # ========================================================

    normalized_cnic = normalize_cnic(cnic)

    print(
        "NORMALIZED CNIC:",
        normalized_cnic
    )

    # ========================================================
    # SUPABASE COLUMNS
    # ========================================================

    # IMPORTANT:
    # Do NOT add "address" here because your Supabase
    # cnic_records table does not have an address column.

    select_columns = (
        "id, "
        "name, "
        "father_name, "
        "gender, "
        "country_to_stay, "
        "identity_number, "
        "date_of_birth, "
        "date_of_issue, "
        "date_of_expiry"
    )

    # ========================================================
    # GET DATABASE RECORDS
    # ========================================================

    response = (
        supabase
        .table("cnic_records")
        .select(select_columns)
        .execute()
    )

    records = response.data or []

    print(
        "DATABASE RECORD COUNT:",
        len(records)
    )

    # ========================================================
    # 1. EXACT DATABASE MATCH
    # ========================================================

    if len(cleaned_ocr) == 13:

        exact_response = (
            supabase
            .table("cnic_records")
            .select(select_columns)
            .eq(
                "identity_number",
                normalized_cnic
            )
            .limit(1)
            .execute()
        )

        exact_records = (
            exact_response.data or []
        )

        print(
            "EXACT DATABASE RECORDS:",
            exact_records
        )

        if exact_records:

            record = exact_records[0]

            print(
                "EXACT CNIC MATCH FOUND:",
                record.get("identity_number")
            )

            print(
                "======================================"
            )

            return {
                "success": True,

                "cnic": record.get(
                    "identity_number"
                ),

                "status": "ACCEPTED",

                "message": (
                    "CNIC verified successfully. "
                    "Record found in verification database."
                ),

                "id": record.get("id"),

                "name": record.get("name"),

                "father_name": record.get(
                    "father_name"
                ),

                "gender": record.get(
                    "gender"
                ),

                "country_to_stay": record.get(
                    "country_to_stay"
                ),

                "identity_number": record.get(
                    "identity_number"
                ),

                "date_of_birth": record.get(
                    "date_of_birth"
                ),

                "date_of_issue": record.get(
                    "date_of_issue"
                ),

                "date_of_expiry": record.get(
                    "date_of_expiry"
                )
            }

    # ========================================================
    # 2. OCR ERROR MATCH
    # ========================================================

    matched_record = find_matching_cnic(
        cleaned_ocr,
        records
    )

    # ========================================================
    # CLOSE MATCH FOUND
    # ========================================================

    if matched_record:

        print(
            "DATABASE RESULT:",
            matched_record
        )

        return {
            "success": True,

            "cnic": matched_record.get(
                "identity_number"
            ),

            "status": "ACCEPTED",

            "message": (
                "CNIC verified successfully. "
                "The OCR contained minor recognition "
                "errors, but a matching record was "
                "found in the verification database."
            ),

            "id": matched_record.get(
                "id"
            ),

            "name": matched_record.get(
                "name"
            ),

            "father_name": matched_record.get(
                "father_name"
            ),

            "gender": matched_record.get(
                "gender"
            ),

            "country_to_stay": matched_record.get(
                "country_to_stay"
            ),

            "identity_number": matched_record.get(
                "identity_number"
            ),

            "date_of_birth": matched_record.get(
                "date_of_birth"
            ),

            "date_of_issue": matched_record.get(
                "date_of_issue"
            ),

            "date_of_expiry": matched_record.get(
                "date_of_expiry"
            )
        }

    # ========================================================
    # NO MATCH
    # ========================================================

    print(
        "CNIC NOT FOUND IN DATABASE"
    )

    print(
        "======================================"
    )

    return {
        "success": False,

        "cnic": normalized_cnic,

        "status": "REJECTED",

        "message": (
            "CNIC was extracted from the image, "
            "but no matching record was found "
            "in the verification database."
        ),

        "id": None,

        "name": None,

        "father_name": None,

        "gender": None,

        "country_to_stay": None,

        "identity_number": normalized_cnic,

        "date_of_birth": None,

        "date_of_issue": None,

        "date_of_expiry": None
    }