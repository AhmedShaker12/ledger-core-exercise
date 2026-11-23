from ledger.config import ACCOUNTS
from ledger.model import (
    BookingDayBackwards,
    Category,
    CurrencyMismatch,
    Direction,
    Entry,
    Event,
    EventType,
    Kind,
    LedgerError,
)

CR, DR = Direction.CR, Direction.DR
Notice = tuple[int, str, str]  # (day, account, message)


def check_currency(account: str, currency: str) -> None:
    if currency != ACCOUNTS[account]:
        raise CurrencyMismatch(f"{currency} entry on {ACCOUNTS[account]} account")


class Ledger:
    def __init__(self) -> None:
        self.entries: list[Entry] = []
        self.errors: list[Notice] = []
        self.warnings: list[Notice] = []
        self.clock: dict[str, int] = {}  # last booking day per account

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
        check_currency(account, currency)
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

    def auth_states(self, account: str, as_of: int) -> dict[str, str]:
        """Derived from the memo entries; the last one per authorization wins."""
        states = {
            Kind.HOLD_PLACED: "ACTIVE",
            Kind.HOLD_RELEASED: "SETTLED",
            Kind.AUTH_DECLINED: "DECLINED",
        }
        return {
            e.ref: states[e.kind]
            for e in self.entries
            if e.account == account
            and e.booking_day <= as_of
            and e.kind in states
            and e.ref
        }

    def apply(self, event: Event) -> None:
        """Turn one event into entries. A refusal is recorded; nothing is posted."""
        try:
            self._apply(event)
        except LedgerError as err:
            self.errors.append(
                (event.booking_day, event.account, f"{event.event_id}: {err}")
            )

    def _apply(self, ev: Event) -> None:
        # Per-account clocks: only a strictly earlier booking day is refused.
        last = self.clock.get(ev.account, 0)
        if ev.booking_day < last:
            raise BookingDayBackwards(f"booking day {ev.booking_day} after day {last}")
        check_currency(ev.account, ev.currency)
        self.clock[ev.account] = ev.booking_day
        days = (ev.booking_day, ev.value_day)

        def post(
            amount: int, direction: Direction, kind: Kind, ref: str | None
        ) -> None:
            self._append(
                ev.event_id, ev.account, ev.currency, amount, direction, kind, days, ref
            )

        if ev.type in (EventType.CREDIT, EventType.DEBIT):
            kind, direction = (
                (Kind.CREDIT, CR) if ev.type is EventType.CREDIT else (Kind.DEBIT, DR)
            )
            # Remainder in minor units goes on the last instalment.
            part = ev.amount // ev.instalments
            remainder = ev.amount - part * ev.instalments
            for i in range(ev.instalments):
                last_one = i == ev.instalments - 1
                post(part + remainder * last_one, direction, kind, None)
        elif ev.type is EventType.AUTHORIZATION:
            available = self.available(ev.account, ev.value_day, ev.booking_day)
            if available - ev.amount >= 0:
                post(ev.amount, DR, Kind.HOLD_PLACED, ev.auth_id)
            else:
                post(0, DR, Kind.AUTH_DECLINED, ev.auth_id)
        elif ev.type is EventType.SETTLEMENT:
            post(ev.amount, DR, Kind.SETTLEMENT, ev.auth_id)
            hold = self._active_hold(ev.account, ev.auth_id)
            if hold:
                # The full hold is released, including any part not settled.
                post(hold.amount, CR, Kind.HOLD_RELEASED, ev.auth_id)
            else:
                msg = f"{ev.event_id}: posted, no active authorization {ev.auth_id}"
                self.warnings.append((ev.booking_day, ev.account, msg))
        else:
            originals = [
                e
                for e in self.entries
                if e.event_id == ev.reverses and e.category is Category.POSTED
            ]
            if not originals:
                raise LedgerError(f"nothing to reverse for {ev.reverses}")
            for e in originals:
                opposite = CR if e.direction is DR else DR
                post(e.amount, opposite, Kind.REVERSAL, str(e.entry_id))

    def _active_hold(self, account: str, auth_id: str | None) -> Entry | None:
        linked = [e for e in self.entries if e.account == account and e.ref == auth_id]
        if any(e.kind is Kind.HOLD_RELEASED for e in linked):
            return None
        return next((e for e in linked if e.kind is Kind.HOLD_PLACED), None)
