import io
from datetime import datetime

import requests
import streamlit as st
from PIL import Image


# ============================================================
# CONFIGURATION
# ============================================================

API_URL = "http://10.0.20.123:8000"
VERIFY_ENDPOINT = f"{API_URL}/verify-cnic"

MAX_FILE_SIZE_MB = 10
REQUEST_TIMEOUT = 120


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Pakistan CNIC Verification",
    page_icon="🪪",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SESSION STATE
# ============================================================

if "page" not in st.session_state:
    st.session_state.page = "Home"

if "verification_history" not in st.session_state:
    st.session_state.verification_history = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None


# ============================================================
# CUSTOM STREAMLIT CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background-color: #f5f7fb;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    section[data-testid="stSidebar"] {
        background-color: #0f3d2e;
    }

    section[data-testid="stSidebar"] * {
        color: white;
    }

    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        min-height: 45px;
    }

    div[data-testid="metric-container"] {
        background-color: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 15px;
    }

    section[data-testid="stFileUploader"] {
        background-color: white;
        border-radius: 12px;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def check_backend():
    """Check whether FastAPI backend is running."""

    try:
        response = requests.get(
            API_URL,
            timeout=5,
        )

        return response.status_code == 200

    except requests.exceptions.RequestException:
        return False


def safe_value(value):
    """Return readable value for missing fields."""

    if value is None:
        return "Not available"

    if isinstance(value, str) and not value.strip():
        return "Not available"

    return str(value)


def prepare_image(uploaded_file):
    """
    Resize and compress the uploaded CNIC image.

    This reduces memory usage and OCR processing time.
    """

    image_bytes = uploaded_file.getvalue()

    image = Image.open(
        io.BytesIO(image_bytes)
    )

    # Convert PNG/RGBA/etc. to RGB
    if image.mode != "RGB":
        image = image.convert("RGB")

    # Maximum image dimensions
    max_width = 1600
    max_height = 1200

    image.thumbnail(
        (max_width, max_height),
        Image.Resampling.LANCZOS,
    )

    # Compress as JPEG
    output = io.BytesIO()

    image.save(
        output,
        format="JPEG",
        quality=85,
        optimize=True,
    )

    return output.getvalue()


def verify_cnic(uploaded_file):
    """Send resized CNIC image to FastAPI."""

    compressed_bytes = prepare_image(
        uploaded_file
    )

    files = {
        "file": (
            "cnic.jpg",
            compressed_bytes,
            "image/jpeg",
        )
    }

    return requests.post(
        VERIFY_ENDPOINT,
        files=files,
        timeout=REQUEST_TIMEOUT,
    )


def get_database_record(result):
    """
    Get database record from different possible
    FastAPI response structures.
    """

    # Case 1:
    # {
    #     "record": {...}
    # }
    record = result.get("record")

    if isinstance(record, dict):
        return record

    # Case 2:
    # {
    #     "data": {...}
    # }
    record = result.get("data")

    if isinstance(record, dict):
        return record

    # Case 3:
    # Database fields are directly in response
    return result


def add_history(result, record):
    """Store verification result in session history."""

    cnic = (
        record.get("identity_number")
        or result.get("cnic")
        or "Not detected"
    )

    name = (
        record.get("name")
        or "Not available"
    )

    history_item = {
        "time": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "status": result.get(
            "status",
            "UNKNOWN",
        ),
        "cnic": cnic,
        "name": name,
    }

    st.session_state.verification_history.insert(
        0,
        history_item,
    )


def display_verified_information(result):
    """
    Display all information returned by the
    database.
    """

    record = get_database_record(result)

    st.divider()

    st.subheader(
        "📋 Verified Information"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.write("**CNIC Number**")

        st.info(
            safe_value(
                record.get("identity_number")
                or result.get("cnic")
            )
        )

        st.write("**Name**")

        st.info(
            safe_value(
                record.get("name")
            )
        )

        st.write("**Father Name**")

        st.info(
            safe_value(
                record.get("father_name")
            )
        )

        st.write("**Gender**")

        st.info(
            safe_value(
                record.get("gender")
            )
        )

    with col2:

        st.write("**Country to Stay**")

        st.info(
            safe_value(
                record.get(
                    "country_to_stay"
                )
            )
        )

        st.write("**Date of Birth**")

        st.info(
            safe_value(
                record.get(
                    "date_of_birth"
                )
            )
        )

        st.write("**Date of Issue**")

        st.info(
            safe_value(
                record.get(
                    "date_of_issue"
                )
            )
        )

        st.write("**Date of Expiry**")

        st.info(
            safe_value(
                record.get(
                    "date_of_expiry"
                )
            )
        )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("# 🪪 CNIC")

    st.markdown(
        "### Pakistan Verification System"
    )

    st.divider()

    st.markdown("### Navigation")

    if st.button(
        "🏠 Home",
        use_container_width=True,
    ):
        st.session_state.page = "Home"
        st.rerun()

    if st.button(
        "🔍 Verify CNIC",
        use_container_width=True,
    ):
        st.session_state.page = "Verify CNIC"
        st.rerun()

    if st.button(
        "📋 Last Result",
        use_container_width=True,
    ):
        st.session_state.page = "Last Result"
        st.rerun()

    if st.button(
        "📊 Dashboard",
        use_container_width=True,
    ):
        st.session_state.page = "Dashboard"
        st.rerun()

    if st.button(
        "ℹ️ About System",
        use_container_width=True,
    ):
        st.session_state.page = "About System"
        st.rerun()

    if st.button(
        "🔐 Privacy & Security",
        use_container_width=True,
    ):
        st.session_state.page = "Privacy & Security"
        st.rerun()

    st.divider()

    # Backend status
    backend_online = check_backend()

    if backend_online:

        st.success(
            "🟢 Backend Online"
        )

    else:

        st.error(
            "🔴 Backend Offline"
        )

    st.divider()

    st.caption(
        "Pakistan CNIC Verification System"
    )

    st.caption(
        "FastAPI • Streamlit • OCR • Supabase"
    )


# ============================================================
# HOME PAGE
# ============================================================

if st.session_state.page == "Home":

    st.title(
        "🪪 Pakistan CNIC Verification System"
    )

    st.subheader(
        "Secure image-based identity verification"
    )

    st.write(
        """
        This system verifies Pakistani CNIC information by
        extracting the identity number from an uploaded CNIC
        image and checking it against the authorized
        verification database.
        """
    )

    st.divider()

    # Statistics
    total = len(
        st.session_state.verification_history
    )

    accepted = sum(
        1
        for item in
        st.session_state.verification_history
        if item["status"] == "ACCEPTED"
    )

    rejected = sum(
        1
        for item in
        st.session_state.verification_history
        if item["status"] == "REJECTED"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Total Checks",
            total,
        )

    with col2:

        st.metric(
            "Accepted",
            accepted,
        )

    with col3:

        st.metric(
            "Rejected",
            rejected,
        )

    with col4:

        if check_backend():

            st.metric(
                "Server",
                "Online",
            )

        else:

            st.metric(
                "Server",
                "Offline",
            )

    st.divider()

    # Features
    st.subheader(
        "✨ System Features"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.info(
            """
            ### 📷 Image Upload

            Upload a clear CNIC image in
            JPG, JPEG, or PNG format.
            """
        )

    with col2:

        st.info(
            """
            ### 🔤 OCR Extraction

            The system extracts the
            CNIC number from the image.
            """
        )

    with col3:

        st.info(
            """
            ### 🗄️ Database Verification

            The extracted CNIC is checked
            against the verification database.
            """
        )

    st.divider()

    st.subheader(
        "🚀 Start Verification"
    )

    st.write(
        "Upload a CNIC image and verify its information."
    )

    if st.button(
        "🔍 Start CNIC Verification",
        type="primary",
        use_container_width=True,
    ):

        st.session_state.page = "Verify CNIC"

        st.rerun()


# ============================================================
# VERIFY CNIC PAGE
# ============================================================

elif st.session_state.page == "Verify CNIC":

    st.title(
        "🔍 Verify CNIC"
    )

    st.write(
        "Upload a clear image of the CNIC to begin verification."
    )

    st.divider()

    uploaded_file = st.file_uploader(
        "Choose CNIC image",
        type=[
            "jpg",
            "jpeg",
            "png",
        ],
        accept_multiple_files=False,
    )

    if uploaded_file is not None:

        file_size_mb = (
            uploaded_file.size
            / (1024 * 1024)
        )

        if file_size_mb > MAX_FILE_SIZE_MB:

            st.error(
                f"File is too large. Maximum size is "
                f"{MAX_FILE_SIZE_MB} MB."
            )

            st.stop()

        st.caption(
            f"📄 {uploaded_file.name} | "
            f"📦 {file_size_mb:.2f} MB"
        )

        # Image preview
        try:

            image_bytes = uploaded_file.getvalue()

            preview_image = Image.open(
                io.BytesIO(image_bytes)
            )

            st.image(
                preview_image,
                caption="Uploaded CNIC",
                width=500,
            )

            st.caption(
                f"Original image size: "
                f"{preview_image.width} × "
                f"{preview_image.height}"
            )

        except Exception:

            st.error(
                "The uploaded file could not be read "
                "as an image."
            )

            st.stop()

        st.divider()

        # Verify button
        if st.button(
            "🔍 Verify CNIC",
            type="primary",
            use_container_width=True,
        ):

            # Check backend
            if not check_backend():

                st.error(
                    "❌ FastAPI backend is offline."
                )

            else:

                with st.spinner(
                    "🔄 Processing CNIC... "
                    "Please wait."
                ):

                    try:

                        response = verify_cnic(
                            uploaded_file
                        )

                        # --------------------------------
                        # HTTP 200
                        # --------------------------------

                        if response.status_code == 200:

                            try:

                                result = response.json()

                            except ValueError:

                                st.error(
                                    "Invalid response received "
                                    "from backend."
                                )

                                st.stop()

                            # --------------------------------
                            # Get database record
                            # --------------------------------

                            record = get_database_record(
                                result
                            )

                            # Save result
                            st.session_state.last_result = result

                            add_history(
                                result,
                                record,
                            )

                            # --------------------------------
                            # Status
                            # --------------------------------

                            status = str(
                                result.get(
                                    "status",
                                    "",
                                )
                            ).upper()

                            # --------------------------------
                            # ACCEPTED
                            # --------------------------------

                            if status == "ACCEPTED":

                                st.success(
                                    "✅ CNIC VERIFIED SUCCESSFULLY"
                                )

                                st.write(
                                    result.get(
                                        "message",
                                        "CNIC record found in database.",
                                    )
                                )

                                display_verified_information(
                                    result
                                )

                            # --------------------------------
                            # REJECTED
                            # --------------------------------

                            else:

                                st.error(
                                    "❌ CNIC VERIFICATION REJECTED"
                                )

                                st.warning(
                                    result.get(
                                        "message",
                                        "CNIC was not found "
                                        "in the verification database.",
                                    )
                                )

                                detected_cnic = (
                                    result.get("cnic")
                                    or record.get(
                                        "identity_number"
                                    )
                                )

                                if detected_cnic:

                                    st.write(
                                        "**Detected CNIC:**"
                                    )

                                    st.code(
                                        str(
                                            detected_cnic
                                        )
                                    )

                        # --------------------------------
                        # HTTP ERROR
                        # --------------------------------

                        else:

                            st.error(
                                f"Backend returned HTTP "
                                f"{response.status_code}"
                            )

                            # Try to show backend error
                            try:

                                error_data = response.json()

                                st.json(
                                    error_data
                                )

                            except Exception:

                                st.code(
                                    response.text
                                )

                    # ------------------------------------
                    # TIMEOUT
                    # ------------------------------------

                    except requests.exceptions.Timeout:

                        st.error(
                            "❌ Verification request timed out."
                        )

                        st.info(
                            "The OCR process is taking too long. "
                            "The image has already been resized "
                            "before being sent to the backend."
                        )

                    # ------------------------------------
                    # CONNECTION ERROR
                    # ------------------------------------

                    except requests.exceptions.ConnectionError:

                        st.error(
                            "❌ Could not connect to FastAPI."
                        )

                    # ------------------------------------
                    # REQUEST ERROR
                    # ------------------------------------

                    except requests.exceptions.RequestException as e:

                        st.error(
                            f"❌ Request failed: {e}"
                        )

                    # ------------------------------------
                    # OTHER ERROR
                    # ------------------------------------

                    except Exception as e:

                        st.error(
                            f"❌ Unexpected error: {e}"
                        )


# ============================================================
# LAST RESULT PAGE
# ============================================================

elif st.session_state.page == "Last Result":

    st.title(
        "📋 Last Verification Result"
    )

    result = st.session_state.last_result

    if result is None:

        st.info(
            "No verification has been performed yet."
        )

        st.write(
            "Go to **Verify CNIC** to perform a verification."
        )

    else:

        status = str(
            result.get(
                "status",
                "",
            )
        ).upper()

        if status == "ACCEPTED":

            st.success(
                "✅ CNIC VERIFIED"
            )

        else:

            st.error(
                "❌ CNIC REJECTED"
            )

        st.write(
            result.get(
                "message",
                "",
            )
        )

        if status == "ACCEPTED":

            display_verified_information(
                result
            )

        else:

            record = get_database_record(
                result
            )

            detected_cnic = (
                result.get("cnic")
                or record.get(
                    "identity_number"
                )
            )

            if detected_cnic:

                st.write(
                    "**Detected CNIC:**"
                )

                st.code(
                    str(
                        detected_cnic
                    )
                )


# ============================================================
# DASHBOARD PAGE
# ============================================================

elif st.session_state.page == "Dashboard":

    st.title(
        "📊 Verification Dashboard"
    )

    history = (
        st.session_state.verification_history
    )

    total = len(history)

    accepted = sum(
        1
        for item in history
        if item["status"] == "ACCEPTED"
    )

    rejected = sum(
        1
        for item in history
        if item["status"] == "REJECTED"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Total Verifications",
            total,
        )

    with col2:

        st.metric(
            "Accepted",
            accepted,
        )

    with col3:

        st.metric(
            "Rejected",
            rejected,
        )

    st.divider()

    if total == 0:

        st.info(
            "No verification activity in this session."
        )

    else:

        st.subheader(
            "📋 Verification History"
        )

        for item in history:

            with st.expander(
                f"{item['status']} — "
                f"{item['cnic']} — "
                f"{item['time']}"
            ):

                st.write(
                    f"**Status:** {item['status']}"
                )

                st.write(
                    f"**CNIC:** {item['cnic']}"
                )

                st.write(
                    f"**Name:** {item['name']}"
                )

                st.write(
                    f"**Time:** {item['time']}"
                )

        st.divider()

        if st.button(
            "🗑️ Clear Session History",
            use_container_width=True,
        ):

            st.session_state.verification_history = []

            st.session_state.last_result = None

            st.success(
                "Verification history cleared."
            )

            st.rerun()


# ============================================================
# ABOUT PAGE
# ============================================================

elif st.session_state.page == "About System":

    st.title(
        "ℹ️ About the System"
    )

    st.write(
        """
        ### Pakistan CNIC Verification System

        This application is an image-based CNIC verification
        system designed for authorized verification purposes.

        The application combines several technologies to
        process a CNIC image and verify the extracted identity
        number against a database.
        """
    )

    st.divider()

    st.subheader(
        "⚙️ Technology Stack"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.info(
            """
            **Frontend**

            - Streamlit
            - Python
            - Image Upload
            - Interactive Dashboard
            """
        )

    with col2:

        st.info(
            """
            **Backend**

            - FastAPI
            - EasyOCR
            - OpenCV
            - Supabase
            """
        )

    st.divider()

    st.subheader(
        "🔄 Verification Pipeline"
    )

    st.write(
        """
        **Step 1 →** Upload CNIC image

        **Step 2 →** Image resizing and preprocessing

        **Step 3 →** OCR text extraction

        **Step 4 →** CNIC number extraction

        **Step 5 →** Database lookup

        **Step 6 →** Verification result

        **Step 7 →** Display verified information
        """
    )


# ============================================================
# PRIVACY PAGE
# ============================================================

elif st.session_state.page == "Privacy & Security":

    st.title(
        "🔐 Privacy & Security"
    )

    st.warning(
        "CNIC information is sensitive personal information."
    )

    st.write(
        """
        ### Important Security Guidelines

        - Use this system only for authorized verification.
        - Do not share CNIC images publicly.
        - Do not share verification results unnecessarily.
        - Protect database access credentials.
        - Keep API keys and Supabase credentials private.
        - Do not place secret keys directly inside frontend code.
        - Use secure HTTPS communication in production.
        """
    )

    st.divider()

    st.subheader(
        "🛡️ Recommended Production Security"
    )

    st.write(
        """
        For a production deployment, consider:

        1. HTTPS/TLS
        2. Authentication and authorization
        3. Role-based access control
        4. Secure environment variables
        5. Audit logging
        6. Rate limiting
        7. Encrypted storage
        8. Automatic deletion of uploaded images
        9. Database access policies
        10. Proper handling of sensitive identity information
        """
    )

    st.divider()

    st.info(
        "This application should be used as an authorized "
        "verification tool and not as a public CNIC lookup service."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🪪 Pakistan CNIC Verification System | "
    "Streamlit + FastAPI + OCR + Supabase"
)