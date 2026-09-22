import os
import shutil
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile

from Backend.cnic_validator import extract_cnic
from Backend.ocr import extract_text_from_image
from Backend.schemas import VerificationResponse
from Backend.verification import verify_cnic


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="CNIC Verification System",
    description="CNIC image verification using OCR and Supabase",
    version="1.0.0"
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "CNIC Verification API is running"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ============================================================
# VERIFY CNIC
# ============================================================

@app.post(
    "/verify-cnic",
    response_model=VerificationResponse
)
async def verify_cnic_image(
    file: UploadFile = File(...)
):
    """
    CNIC verification pipeline:

        Image
          ↓
        File validation
          ↓
        Temporary file
          ↓
        OCR
          ↓
        Extract CNIC
          ↓
        Supabase verification
          ↓
        ACCEPTED / REJECTED
          ↓
        Return complete CNIC information
    """

    # ========================================================
    # STEP 1: CHECK FILE TYPE
    # ========================================================

    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/jpg"
    }

    if file.content_type not in allowed_types:

        raise HTTPException(
            status_code=400,
            detail="Please upload a JPG or PNG image."
        )

    # ========================================================
    # CHECK FILE EXTENSION
    # ========================================================

    if file.filename:

        extension = os.path.splitext(
            file.filename
        )[1].lower()

        if extension not in [
            ".jpg",
            ".jpeg",
            ".png"
        ]:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid image extension. "
                    "Please upload JPG or PNG."
                )
            )

    temp_path = None

    try:

        # ====================================================
        # STEP 2: SAVE TEMPORARY IMAGE
        # ====================================================

        suffix = ".jpg"

        if file.filename:

            extension = os.path.splitext(
                file.filename
            )[1].lower()

            if extension in [
                ".jpg",
                ".jpeg",
                ".png"
            ]:

                suffix = extension

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp_file:

            temp_path = temp_file.name

            shutil.copyfileobj(
                file.file,
                temp_file
            )

        # ====================================================
        # STEP 3: OCR
        # ====================================================

        extracted_text = extract_text_from_image(
            temp_path
        )

        if not extracted_text:

            return VerificationResponse(
                success=False,
                cnic=None,
                status="REJECTED",
                message=(
                    "No text could be extracted "
                    "from the image."
                ),
                name=None,
                father_name=None,
                gender=None,
                country_to_stay=None,
                identity_number=None,
                date_of_birth=None,
                date_of_issue=None,
                date_of_expiry=None,
                address=None
            )

        print(
            "\n========== OCR TEXT =========="
        )

        print(extracted_text)

        print(
            "==============================\n"
        )

        # ====================================================
        # STEP 4: EXTRACT CNIC
        # ====================================================

        extracted_cnic = extract_cnic(
            extracted_text
        )

        print(
            "EXTRACTED CNIC:",
            extracted_cnic
        )

        if not extracted_cnic:

            return VerificationResponse(
                success=False,
                cnic=None,
                status="REJECTED",
                message=(
                    "CNIC number could not be detected. "
                    "Please upload a clear CNIC image."
                ),
                name=None,
                father_name=None,
                gender=None,
                country_to_stay=None,
                identity_number=None,
                date_of_birth=None,
                date_of_issue=None,
                date_of_expiry=None,
                address=None
            )

        # ====================================================
        # STEP 5: VERIFY CNIC
        # ====================================================

        print(
            "OCR CNIC CANDIDATE:",
            extracted_cnic
        )

        result = verify_cnic(
            extracted_cnic
        )

        print(
            "DATABASE RESULT:",
            result
        )

        # ====================================================
        # STEP 6: RETURN COMPLETE RESULT
        # ====================================================

        return VerificationResponse(
            **result
        )

    # ========================================================
    # HTTP ERROR
    # ========================================================

    except HTTPException:
        raise

    # ========================================================
    # GENERAL ERROR
    # ========================================================

    except Exception as e:

        print(
            "\n========== ERROR =========="
        )

        print(
            str(e)
        )

        print(
            "===========================\n"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "An error occurred while processing "
                "the CNIC image."
            )
        )

    # ========================================================
    # DELETE TEMPORARY FILE
    # ========================================================

    finally:

        if (
            temp_path
            and os.path.exists(temp_path)
        ):

            os.remove(
                temp_path
            )