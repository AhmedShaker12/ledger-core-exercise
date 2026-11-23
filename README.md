# ledger-core-exercise

An in-memory account ledger core, written as an exercise. It replays a fixed stream of ten events over a six-day window for two accounts (ACC-001 in AED, ACC-002 in BHD) and prints, for each day, the closing ledger balances, fee assessments, authorization states, warnings and errors. There is no web layer, persistence, UI or database.

## How to run

Requirements: Python 3.12 (see `.python-version`), [uv](https://docs.astral.sh/uv/) and GNU make.

```
make install   # install dependencies from uv.lock
make run       # replay the event stream and print one block per day
make check     # ruff format and lint, mypy strict, pytest with coverage (what CI runs)
```

Without make: `uv sync --locked`, then `uv run python -m ledger.replay` and `uv run pytest`.

## Reading the output

`make run` prints one block per day, and inside it one block per account:

```
=== Day 5 ===
ACC-001 (AED)
  D2-b  Day 2 closing  -395.00  (restated)
  D3-b  Day 3 closing  5.00  (restated)
  D4-b  Day 4 closing  -385.00  (restated)
  D5-a  Day 5 closing  -410.00
  Fees: Day 2 fee 25.00, Day 4 fee 25.00, Day 5 fee 25.00
  Auth: Auth-A SETTLED; Auth-B DECLINED
  Warnings: none
  Errors: none
```

- **Balance lines** carry a label: the value day plus a letter (`D2-a`, `D2-b`, ...). Each number is printed once. When a back-dated entry changes an earlier day's closing, that day is printed again with the next letter and marked `(restated)`; old labels are never reused. Earlier days that did not change are not reprinted.
- **Fees** lists the fee and refund entries booked at that day's close, each by the value day it belongs to. A fee is booked with the negative day as its value date, even when it is booked later.
- **Interest capitalized** appears on Day 6 only, followed by the Day 6 closing after interest on its own label (`D6-b`).
- **Auth** shows every authorization seen on the account so far, with its state as of that day: ACTIVE, SETTLED or DECLINED. A declined authorization is a state, not an error.
- **Warnings** are events that were posted but need attention.
- **Errors** are refusals: the event was refused and nothing was posted. No event in the given stream is refused, so this line reads `none` on all six days.

### Key figures

| | Day 1 | Day 2 | Day 3 | Day 4 | Day 5 | Day 6 |
|---|---|---|---|---|---|---|
| ACC-001 as of Day 5 (E7 posted) | 250.00 | -395.00 | 5.00 | -385.00 | -410.00 | |
| ACC-001 final (after E9) | 250.00 | 250.00 | 650.00 | 285.00 | 285.00 | 285.00, then 285.79 |
| ACC-002 final | 0.000 | 0.000 | 0.000 | 0.000 | 10.000 | 10.000, then 10.008 |

- E7 (debit 620.00, booked Day 5, value Day 2) makes Days 2, 4 and 5 negative, so the Day 5 close books three fees.
- E9 (booked Day 6) reverses E7; the Day 6 close refunds the three fees, each with the original fee's value date.
- Interest capitalized on Day 6: AED 0.79 on ACC-001, BHD 0.008 on ACC-002.
- E6 settles Auth-Z, which was never authorized: it is posted and reported as a warning on Day 4.
- Auth-A (hold 200.00) settles for 185.00 on Day 4; the full hold is released. Auth-B (hold 90.00) is declined on Day 5, because the available balance is -335.00.

## Design in brief

- **Money** is an integer in minor units with an explicit currency (AED 2 decimal places, BHD 3). No floats. Every entry must be in its account's currency.
- **One append-only entry store.** Every event becomes one or more entries; nothing is changed or deleted. Corrections (reversals, fee refunds) are new entries.
- **POSTED and MEMO entries.** POSTED entries make up the ledger balance. Authorizations are MEMO entries (hold placed, hold released, declined) that never move the ledger balance; an authorization's state is derived from its entries. Available balance = ledger balance minus active holds.
- **Value days and as-of days.** Each account has a balance matrix: rows are value days, columns are as-of days. Cell (N, K) is "value day N as known at the end of day K". Closing day K computes column K top-down; each day starts from the previous day's closing, fee included, so a back-dated entry flows into every later day. A closed column is never changed. The matrix is derived and can be rebuilt from the entries.
- **Fee reconciliation.** At each close, for each value day, the fee due is compared with the net fee already booked for that day, and a fee, a refund or nothing is appended. This keeps one net fee per negative value day.
- **Interest** is 4 basis points per day on positive closing balances, rounded half-up for each day, and capitalized at the end of Day 6 as one credit equal to the sum of the rounded daily accruals.
- **Per-account clocks.** Each account keeps its own booking day, so E10 (Day 5, listed after E9) is on time for ACC-002. An event with a strictly earlier booking day than the previous event on the same account is refused.
- **Refusals** (errors, nothing posted): wrong currency, booking day going backwards, a reversal of an unknown event, and a settlement on a declined or already settled authorization. A settlement on an unknown authorization is posted with a warning.

Code, in `src/ledger/`:

| File | Contents |
|---|---|
| `config.py` | constants: precision, accounts, fee, rate, window |
| `model.py` | events, entries, matrix cells, error types |
| `ledger.py` | the entry store, balance queries, events to entries, day close, fee reconciliation, capitalization |
| `replay.py` | the event stream and the per-day output |

## Tests

`make check` runs the whole suite. `tests/test_ledger.py` holds one test per accepted acceptance criterion and the balance invariant (each closing equals the sum of the POSTED entries behind it). The other test files cover each module.

**The failing test:** `tests/test_xfail.py` is the one test that fails by design, marked `xfail(strict=True)` and annotated inline. It asserts that a negative BHD account is charged an overdraft fee; today the AED fee is refused, because every entry must be in the account's currency. It reveals that cross-currency fees need FX support, which is out of scope. `strict=True` keeps CI green while the test fails, and turns CI red if it ever starts passing.

## Other documents

- [NUMBERS.md](NUMBERS.md): every constant, chosen or given, and why.
- [AMBIGUITIES.md](AMBIGUITIES.md): every ambiguity found and how it was resolved.
- [REJECTED.md](REJECTED.md): the refused acceptance criteria (#2, #4, #7) and the approaches abandoned mid-build.
- [WORKLOG.md](WORKLOG.md): timestamped work log.
