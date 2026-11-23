from ledger.ledger import Ledger, daily_interest
from ledger.model import Event, EventType, Kind


def credit(eid: str, booked: int, value: int, amount: int) -> Event:
    return Event(eid, EventType.CREDIT, booked, "ACC-001", "AED", amount, value)


def debit(eid: str, booked: int, value: int, amount: int) -> Event:
    return Event(eid, EventType.DEBIT, booked, "ACC-001", "AED", amount, value)


def fee_entries(led: Ledger) -> list[tuple[Kind, int, int, int]]:
    return [
        (e.kind, e.amount, e.booking_day, e.value_day)
        for e in led.entries
        if e.kind in (Kind.FEE, Kind.FEE_REFUND)
    ]


def test_fee_reconciliation() -> None:
    led = Ledger()
    led.apply(credit("E1", 1, 1, 10000))
    led.apply(debit("E2", 2, 2, 30000))
    led.close_through("ACC-001", 2)
    assert fee_entries(led) == [(Kind.FEE, 2500, 2, 2)]
    led.apply(credit("E3", 3, 2, 50000))  # back-dated: day 2 turns positive
    led.close_through("ACC-001", 3)
    assert fee_entries(led)[1:] == [(Kind.FEE_REFUND, 2500, 3, 2)]
    led._close("ACC-001", 3)  # a repeat close books nothing
    assert len(fee_entries(led)) == 2


def test_back_dated_entry_restates_later_days() -> None:
    led = Ledger()
    led.apply(credit("E1", 1, 1, 10000))
    led.apply(credit("E2", 3, 3, 1000))
    led.apply(debit("E3", 4, 2, 30000))
    led.close_through("ACC-001", 4)
    m = led.matrix["ACC-001"]
    assert m[(3, 3)].closing == 11000
    assert (m[(2, 4)].pre_fee, m[(2, 4)].fee, m[(2, 4)].closing) == (
        -20000,
        2500,
        -22500,
    )
    assert m[(3, 4)].closing == -24000  # day 3 also negative: its own fee
    assert m[(3, 4)].fee == 2500


def test_daily_interest_rounds_half_up_on_positive_only() -> None:
    assert daily_interest(28500) == 11  # 11.4
    assert daily_interest(12500) == 5  # 5.0
    assert daily_interest(1250) == 1  # 0.5 rounds up
    assert daily_interest(-28500) == 0
