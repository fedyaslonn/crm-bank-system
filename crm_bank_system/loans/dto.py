from dataclasses import dataclass
from datetime import datetime

from users.models import CustomUser


@dataclass
class LoanDTO:
    amount: float
    interest_rate: float
    term: float