from dataclasses import dataclass


@dataclass
class CNICRecord:
    id: int
    cnic: str
    name: str
    status: str