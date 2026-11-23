from ledger.config import ACCOUNTS
from ledger.model import Category, CurrencyMismatch, Direction, Entry, Kind


class Ledger:
    def __init__(self) -> None:
        self.entries: list[Entry] = []

    def _append(
        self,
        event_id: str,
        account: str,
        currency: str,
        amount: int,
        direction: Direction,
        kind: Kind,
        days: tuple[int, int],
        ref: str | None = None,
    ) -> Entry:
        """The only writer. Entries are appended, never changed or removed.

        days is (booking_day, value_day).
        """
        if currency != ACCOUNTS[account]:
            raise CurrencyMismatch(
                f"{currency} entry on {ACCOUNTS[account]} account {account}"
            )
        entry = Entry(
            len(self.entries) + 1,
            event_id,
            account,
            currency,
            amount,
            direction,
            kind,
            *days,
            ref,
        )
        self.entries.append(entry)
        return entry

    def _select(self, account: str, value_day: int, as_of: int) -> list[Entry]:
        return [
            e
            for e in self.entries
            if e.account == account
            and e.value_day <= value_day
            and e.booking_day <= as_of
        ]

    def ledger_balance(self, account: str, value_day: int, as_of: int) -> int:
        """POSTED entries with value day <= value_day, booked by the end of as_of."""
        entries = self._select(account, value_day, as_of)
        return sum(e.signed for e in entries if e.category is Category.POSTED)

    def holds(self, account: str, value_day: int, as_of: int) -> int:
        """Active holds: placed minus released."""
        entries = self._select(account, value_day, as_of)
        placed = sum(e.amount for e in entries if e.kind is Kind.HOLD_PLACED)
        released = sum(e.amount for e in entries if e.kind is Kind.HOLD_RELEASED)
        return placed - released

    def available(self, account: str, value_day: int, as_of: int) -> int:
        balance = self.ledger_balance(account, value_day, as_of)
        return balance - self.holds(account, value_day, as_of)
