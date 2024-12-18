from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional

from users.models import CustomUser


@dataclass
class ClientCardDTO:
    user: str
    card_number: str
    wallet_address: str
    expiration_date: datetime
    balance: int = field(default=0)

@dataclass
class TransactionDTO:
    sender: CustomUser
    recipient: Optional[CustomUser]
    amount: Decimal
    currency_to: str
    currency_from: str
    type: str