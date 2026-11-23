"""The event stream end to end: one test per acceptance criterion, then the final
numbers and the matrix invariant."""

import pytest

from ledger.config import ACCOUNTS
from ledger.ledger import Ledger
from ledger.model import Category, Event, EventType, Kind
from ledger.replay import run

A1, A2 = "ACC-001", "ACC-002"


@pytest.fixture(scope="module")
def led() -> Ledger:
    return run()


def test_c1_day2_before_fee(led: Ledger) -> None:
    assert led.matrix[A1][(2, 5)].pre_fee == -37000


def test_c2_refused_e7_causes_three_fees(led: Ledger) -> None:
    fees = [e for e in led.entries if e.kind is Kind.FEE and e.booking_day == 5]
    assert [e.value_day for e in fees] == [2, 4, 5]


def test_c3_auth_a_settles(led: Ledger) -> None:
    linked = [(e.kind, e.amount, e.value_day) for e in led.entries if e.ref == "Auth-A"]
    assert (Kind.SETTLEMENT, 18500, 4) in linked
    assert (Kind.HOLD_RELEASED, 20000, 4) in linked
    assert led.auth_states(A1, 4)["Auth-A"] == "SETTLED"


def test_c4_refused_unknown_auth_posts_with_warning(led: Ledger) -> None:
    e6 = [e for e in led.entries if e.event_id == "E6"]
    assert [(e.kind, e.amount, e.category) for e in e6] == [
        (Kind.SETTLEMENT, 18000, Category.POSTED)
    ]
    assert [(d, a) for d, a, m in led.warnings if "Auth-Z" in m] == [(4, A1)]
    assert led.errors == []


def test_c5_hold_reduces_available_only() -> None:
    # Auth-B is declined in the stream, so the rule is checked on its own.
    hold = Ledger()
    hold.apply(Event("E1", EventType.CREDIT, 1, A1, "AED", 28500, 1))
    hold.apply(Event("E8", EventType.AUTHORIZATION, 1, A1, "AED", 9000, 1, "Auth-B"))
    assert hold.ledger_balance(A1, 1, 1) == 28500
    assert hold.available(A1, 1, 1) == 19500


def test_auth_b_declined(led: Ledger) -> None:
    declined = [e for e in led.entries if e.kind is Kind.AUTH_DECLINED]
    assert [(e.ref, e.amount, e.booking_day) for e in declined] == [("Auth-B", 0, 5)]
    assert led.auth_states(A1, 6)["Auth-B"] == "DECLINED"


def test_c6_values_return_after_e9(led: Ledger) -> None:
    m = led.matrix[A1]
    for n in range(1, 5):
        assert (m[(n, 6)].closing, m[(n, 6)].fee) == (m[(n, 4)].closing, m[(n, 4)].fee)


def test_c7_refused_instalments(led: Ledger) -> None:
    e10 = [e.amount for e in led.entries if e.event_id == "E10"]
    assert e10 == [3333, 3333, 3334]
    assert sum(e10) == 10000


def test_c8_accruals_sum_to_capitalized(led: Ledger) -> None:
    for account in ACCOUNTS:
        accruals = sum(led.matrix[account][(n, 6)].interest for n in range(1, 7))
        interest = [
            e.amount
            for e in led.entries
            if e.account == account and e.kind is Kind.INTEREST
        ]
        assert interest == [accruals]


def test_final_numbers(led: Ledger) -> None:
    m1, m2 = led.matrix[A1], led.matrix[A2]
    column5 = [
        (m1[(n, 5)].pre_fee, m1[(n, 5)].fee, m1[(n, 5)].closing) for n in range(1, 6)
    ]
    assert column5 == [
        (25000, 0, 25000),
        (-37000, 2500, -39500),
        (500, 0, 500),
        (-36000, 2500, -38500),
        (-38500, 2500, -41000),
    ]
    column6 = [(m1[(n, 6)].closing, m1[(n, 6)].interest) for n in range(1, 7)]
    assert column6 == [
        (25000, 10),
        (25000, 10),
        (65000, 26),
        (28500, 11),
        (28500, 11),
        (28500, 11),
    ]
    assert led.ledger_balance(A1, 6, 6) == 28579
    assert [m2[(n, 6)].interest for n in (5, 6)] == [4, 4]
    assert m2[(5, 5)].closing == 10000
    assert led.ledger_balance(A2, 6, 6) == 10008


def test_invariant_closing_equals_entry_sum(led: Ledger) -> None:
    # The Day 6 interest credit is posted after the last column is computed.
    for account, cells in led.matrix.items():
        for (n, k), cell in cells.items():
            assert cell.closing == sum(
                e.signed
                for e in led.entries
                if e.account == account
                and e.category is Category.POSTED
                and e.kind is not Kind.INTEREST
                and e.value_day <= n
                and e.booking_day <= k
            )
