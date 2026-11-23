import pytest

from ledger.ledger import Ledger
from ledger.model import CurrencyMismatch, Direction, Kind

CR, DR = Direction.CR, Direction.DR


def test_balance_filters_by_value_day_and_as_of() -> None:
    led = Ledger()
    led._append("E1", "ACC-001", "AED", 1000, CR, Kind.CREDIT, (1, 1))
    led._append("E2", "ACC-001", "AED", 300, DR, Kind.DEBIT, (3, 2))
    assert led.ledger_balance("ACC-001", 1, 3) == 1000
    assert led.ledger_balance("ACC-001", 2, 2) == 1000
    assert led.ledger_balance("ACC-001", 2, 3) == 700


def test_hold_reduces_available_not_ledger() -> None:
    led = Ledger()
    led._append("E1", "ACC-001", "AED", 1000, CR, Kind.CREDIT, (1, 1))
    led._append("E2", "ACC-001", "AED", 400, DR, Kind.HOLD_PLACED, (1, 1), "Auth-X")
    assert led.ledger_balance("ACC-001", 1, 1) == 1000
    assert led.available("ACC-001", 1, 1) == 600
    led._append("E3", "ACC-001", "AED", 400, CR, Kind.HOLD_RELEASED, (2, 2), "Auth-X")
    assert led.available("ACC-001", 2, 2) == 1000


def test_currency_mismatch_refused() -> None:
    led = Ledger()
    with pytest.raises(CurrencyMismatch):
        led._append("F", "ACC-002", "AED", 2500, DR, Kind.FEE, (1, 1))
    assert led.entries == []
