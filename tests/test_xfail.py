import pytest

from ledger.ledger import Ledger
from ledger.model import Event, EventType, Kind


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Reveals: the overdraft fee is fixed in AED, but every entry must be in the "
        "account's currency, so a negative BHD account gets no fee (CurrencyMismatch). "
        "Charging it needs FX support, which is out of scope."
    ),
)
def test_negative_bhd_account_is_charged_an_overdraft_fee() -> None:
    led = Ledger()
    led.apply(Event("X1", EventType.DEBIT, 1, "ACC-002", "BHD", 1000, 1))
    led.close_through("ACC-002", 1)
    # Wanted production behaviour: the negative day carries a fee entry.
    fees = [e for e in led.entries if e.account == "ACC-002" and e.kind is Kind.FEE]
    assert [e.value_day for e in fees] == [1]
