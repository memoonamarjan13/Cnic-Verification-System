from Backend.cnic_validator import (
    clean_cnic,
    extract_cnic,
    validate_cnic
)


def test_clean_cnic():

    result = clean_cnic(
        "17301-2521251-3"
    )

    assert result == "1730125212537"


def test_valid_cnic():

    assert validate_cnic(
        "1730125212537"
    )


def test_invalid_cnic():

    assert not validate_cnic(
        "12345"
    )


def test_extract_cnic():

    text = """
    Name Muhammad Ahmed
    CNIC 17301-2521251-3
    Date of Birth 12-03-1998
    """

    result = extract_cnic(text)

    assert result == "1730125212537"