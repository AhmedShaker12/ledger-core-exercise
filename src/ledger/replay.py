"""Replay the event stream and print one block per day and account."""

from ledger.config import ACCOUNTS, DAYS
from ledger.ledger import Ledger
from ledger.model import Event, EventType, Kind, fmt

T = EventType
A1, A2 = "ACC-001", "ACC-002"

STREAM = [
    Event("E1", T.CREDIT, 1, A1, "AED", 120000, 1),
    Event("E2", T.DEBIT, 1, A1, "AED", 95000, 1),
    Event("E3", T.AUTHORIZATION, 2, A1, "AED", 20000, 2, auth_id="Auth-A"),
    Event("E4", T.CREDIT, 3, A1, "AED", 40000, 3),
    Event("E5", T.SETTLEMENT, 4, A1, "AED", 18500, 4, auth_id="Auth-A"),
    Event("E6", T.SETTLEMENT, 4, A1, "AED", 18000, 4, auth_id="Auth-Z"),
    Event("E7", T.DEBIT, 5, A1, "AED", 62000, 2),
    Event("E8", T.AUTHORIZATION, 5, A1, "AED", 9000, 5, auth_id="Auth-B"),
    Event("E9", T.REVERSAL, 6, A1, "AED", 0, 2, reverses="E7"),
    Event("E10", T.CREDIT, 5, A2, "BHD", 10000, 5, instalments=3),
]


def run(stream: list[Event] = STREAM) -> Ledger:
    led = Ledger()
    for event in stream:
        led.apply(event)
    led.finish()
    return led


def report(led: Ledger) -> list[str]:
    """Every number is printed once under a label. A restated day gets the next
    letter (D2-a, D2-b, ...); a label is never reused."""
    lines: list[str] = []
    labels: dict[tuple[str, int], int] = {}

    def label(account: str, n: int) -> str:
        labels[(account, n)] = labels.get((account, n), 0) + 1
        return f"D{n}-{chr(ord('a') + labels[(account, n)] - 1)}"

    for k in range(1, DAYS + 1):
        lines.append(f"=== Day {k} ===")
        for account, cur in ACCOUNTS.items():
            lines.append(f"{account} ({cur})")
            matrix = led.matrix[account]
            for n in range(1, k + 1):
                cell, before = matrix[(n, k)], matrix.get((n, k - 1))
                if before and (cell.closing, cell.fee) == (before.closing, before.fee):
                    continue
                note = "  (restated)" if before else ""
                amount = fmt(cell.closing, cur)
                lines.append(f"  {label(account, n)}  Day {n} closing  {amount}{note}")
            booked = [
                e for e in led.entries if e.account == account and e.booking_day == k
            ]
            fees = [
                f"Day {e.value_day} {'refund' if e.kind is Kind.FEE_REFUND else 'fee'} "
                f"{fmt(e.amount, e.currency)}"
                for e in booked
                if e.kind in (Kind.FEE, Kind.FEE_REFUND)
            ]
            lines.append(f"  Fees: {', '.join(fees) or 'none'}")
            for e in booked:
                if e.kind is Kind.INTEREST:
                    lines.append(f"  Interest capitalized: {fmt(e.amount, cur)}")
                    closing = fmt(led.ledger_balance(account, k, k), cur)
                    tag = label(account, k)
                    lines.append(f"  {tag}  Day {k} closing after interest  {closing}")
            auths = led.auth_states(account, k)
            states = [f"{auth} {state}" for auth, state in auths.items()]
            lines.append(f"  Auth: {'; '.join(states) or 'none'}")
            for title, notices in (("Warnings", led.warnings), ("Errors", led.errors)):
                found = [m for d, a, m in notices if (d, a) == (k, account)]
                lines.append(f"  {title}: {'; '.join(found) or 'none'}")
    return lines


def main() -> None:
    print("\n".join(report(run())))


if __name__ == "__main__":
    main()
