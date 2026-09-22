
from typing import Optional

from pydantic import BaseModel


class VerificationResponse(BaseModel):

    success: bool

    cnic: Optional[str] = None

    status: str

    message: str

    # Supabase id is an integer
    id: Optional[int] = None

    name: Optional[str] = None

    father_name: Optional[str] = None

    gender: Optional[str] = None

    country_to_stay: Optional[str] = None

    identity_number: Optional[str] = None

    date_of_birth: Optional[str] = None

    date_of_issue: Optional[str] = None

    date_of_expiry: Optional[str] = None

