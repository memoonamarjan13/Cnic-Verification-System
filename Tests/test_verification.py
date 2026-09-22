def test_cnic_found():

    fake_database = {
        "1730125212537": {
            "name": "Muhammad Ahmed",
            "status": "approved"
        }
    }

    cnic = "1730125212537"

    assert cnic in fake_database
    assert fake_database[cnic]["status"] == "approved"


def test_cnic_not_found():

    fake_database = {
        "1730125212537": {
            "name": "Muhammad Ahmed",
            "status": "approved"
        }
    }

    cnic = "1730125212599"

    assert cnic not in fake_database