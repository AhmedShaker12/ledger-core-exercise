from dataclasses import dataclass
from enum import StrEnum

from ledger.config import PRECISION


class Direction(StrEnum):
    CR = "CR"
    DR = "DR"


class Category(StrEnum):
    POSTED = "POSTED"
    MEMO = "MEMO"


class Kind(StrEnum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"
    SETTLEMENT = "SETTLEMENT"
    REVERSAL = "REVERSAL"
    FEE = "FEE"
    FEE_REFUND = "FEE_REFUND"
    INTEREST = "INTEREST"
    HOLD_PLACED = "HOLD_PLACED"
    HOLD_RELEASED = "HOLD_RELEASED"
    AUTH_DECLINED = "AUTH_DECLINED"


MEMO_KINDS = {Kind.HOLD_PLACED, Kind.HOLD_RELEASED, Kind.AUTH_DECLINED}


class EventType(StrEnum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"
    AUTHORIZATION = "AUTHORIZATION"
    SETTLEMENT = "SETTLEMENT"
    REVERSAL = "REVERSAL"


@dataclass(frozen=True)
class Entry:
    entry_id: int
    event_id: str
    account: str
    currency: str
    amount: int
    direction: Direction
    kind: Kind
    booking_day: int
    value_day: int
    ref: str | None = None

    @property
    def category(self) -> Category:
        return Category.MEMO if self.kind in MEMO_KINDS else Category.POSTED

    @property
    def signed(self) -> int:
        return self.amount if self.direction is Direction.CR else -self.amount


@dataclass(frozen=True)
class Event:
    event_id: str
    type: EventType
    booking_day: int
    account: str
    currency: str
    amount: int
    value_day: int
    auth_id: str | None = None
    reverses: str | None = None
    instalments: int = 1


@dataclass(frozen=True)
class Cell:
    """Value day N as known at the end of as-of day K."""

    pre_fee: int
    fee: int
    closing: int
    interest: int
    available: int


class LedgerError(Exception):
    """An event or entry was refused; nothing was posted."""


class CurrencyMismatch(LedgerError):
    pass


class BookingDayBackwards(LedgerError):
    pass


class AuthorizationNotActive(LedgerError):
    pass


def fmt(amount: int, currency: str) -> str:
    places = PRECISION[currency]
    whole, frac = divmod(abs(amount), 10**places)
    return f"{'-' if amount < 0 else ''}{whole}.{frac:0{places}d}"
