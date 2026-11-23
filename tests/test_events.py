from ledger.ledger import Ledger
from ledger.model import Category, Event, EventType, Kind

T = EventType


def ev(eid: str, t: EventType, day: int, amount: int, **kw: object) -> Event:
    fields: dict[str, object] = {"account": "ACC-001", "currency": "AED"}
    fields.update(kw)
    return Event(eid, t, day, amount=amount, value_day=day, **fields)  # type: ignore[arg-type]


def test_instalments_put_remainder_on_last() -> None:
    led = Ledger()
    led.apply(
        ev("E10", T.CREDIT, 5, 10000, account="ACC-002", currency="BHD", instalments=3)
    )
    assert [e.amount for e in led.entries] == [3333, 3333, 3334]


def test_authorization_approved_and_declined() -> None:
    led = Ledger()
    led.apply(ev("E1", T.CREDIT, 1, 25000))
    led.apply(ev("E2", T.AUTHORIZATION, 2, 20000, auth_id="Auth-A"))
    led.apply(ev("E3", T.AUTHORIZATION, 2, 9000, auth_id="Auth-B"))
    assert led.auth_states("ACC-001", 2) == {"Auth-A": "ACTIVE", "Auth-B": "DECLINED"}
    assert led.available("ACC-001", 2, 2) == 5000
    assert led.ledger_balance("ACC-001", 2, 2) == 25000


def test_settlement_releases_full_hold() -> None:
    led = Ledger()
    led.apply(ev("E1", T.CREDIT, 1, 25000))
    led.apply(ev("E2", T.AUTHORIZATION, 2, 20000, auth_id="Auth-A"))
    led.apply(ev("E3", T.SETTLEMENT, 4, 18500, auth_id="Auth-A"))
    assert led.auth_states("ACC-001", 4) == {"Auth-A": "SETTLED"}
    assert led.holds("ACC-001", 4, 4) == 0
    assert led.ledger_balance("ACC-001", 4, 4) == 6500


def test_unknown_settlement_posts_with_warning() -> None:
    led = Ledger()
    led.apply(ev("E6", T.SETTLEMENT, 4, 18000, auth_id="Auth-Z"))
    assert led.ledger_balance("ACC-001", 4, 4) == -18000
    assert led.warnings and not led.errors


def test_reversal_posts_opposite_entry() -> None:
    led = Ledger()
    led.apply(ev("E1", T.CREDIT, 1, 100000))
    led.apply(ev("E7", T.DEBIT, 5, 62000))
    led.apply(ev("E9", T.REVERSAL, 6, 0, reverses="E7"))
    rev = led.entries[-1]
    assert (rev.kind, rev.amount, rev.ref) == (Kind.REVERSAL, 62000, "2")
    assert led.ledger_balance("ACC-001", 6, 6) == 100000


def test_refusals_post_nothing() -> None:
    led = Ledger()
    led.apply(ev("E1", T.CREDIT, 3, 100))
    led.apply(ev("E2", T.CREDIT, 2, 100))  # booking day goes backwards
    led.apply(ev("E3", T.CREDIT, 3, 100, currency="BHD"))
    led.apply(ev("E4", T.REVERSAL, 3, 0, reverses="E99"))
    assert len(led.entries) == 1
    assert [msg.split(":")[0] for _, _, msg in led.errors] == ["E2", "E3", "E4"]


def test_ledger_ignores_memo() -> None:
    led = Ledger()
    led.apply(ev("E1", T.CREDIT, 1, 1000))
    led.apply(ev("E2", T.AUTHORIZATION, 1, 400, auth_id="Auth-X"))
    assert any(e.category is Category.MEMO for e in led.entries)
    assert led.ledger_balance("ACC-001", 1, 1) == 1000
