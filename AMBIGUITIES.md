# Ambiguities

Every ambiguity found in the brief, the readings considered, how it was resolved and why.

## 1. Criterion 4 and posting E6

E6 settles Auth-Z, which has no preceding authorization event.

Readings:
- reject the unmatched settlement, so the funds do not leave the account;
- post it and flag it.

**Resolution:** E6 is posted and reported on a warning line, and criterion 4 is refused. The reasons are in REJECTED.md.

## 2. Criterion 6: values or records

"All balances and fees return to their pre-E7 values."

Readings:
- the values: balances and net fees;
- the entry records themselves. Under append-only, the fee and refund records remain.

**Resolution:** values.

**Reason:** Under append-only, records can never 'return' to an earlier state, so a records reading would make the criterion impossible by design. The brief can't mean that, so it means values.

## 3. Criterion 6: "pre-E7" as of when

Readings:
- a snapshot of the state just before E7 posted, at the end of Day 4;
- as if E7 never happened. Under this reading Auth-B would be approved and criterion 6 would be false.

**Resolution:** the snapshot at the end of Day 4, compared on value days 1 to 4, the days that existed then. Days 5 and 6 have no pre-E7 values.

**Reason:** 'Pre-E7 values' means values that existed before E7 arrived. 'As if E7 never happened' describes a history that never existed, so there are no such values to return to. Auth-B is Day 5, outside the compared days 1–4.

## 4. Criterion 7: E10: 'three equal instalments' is impossible at 3 decimal places

Three equal amounts at 3 decimal places are impossible: 3 x 3.334 = 10.002, not 10.000.

**Resolution:** 3.333, 3.333 and 3.334. The remainder placement is in NUMBERS.md.

## 5. E10 replay order

E10 (booked Day 5) is listed after E9 (booked Day 6), and the stream is replayed in the order given.

Readings:
- per-account clocks;
- a global clock that accepts a late posting;
- a global clock that rejects it.

**Resolution:** per-account clocks, so E10 is on time for ACC-002.

**Reason:** both accounts may stream their transactions separately, so Day 5 for ACC-002 can arrive after Day 6 for ACC-001.

## 6. AED fee on the BHD account

The overdraft fee is AED 25.00, but every entry must be in the account's currency, so the fee cannot post on a negative BHD account.

**Resolution:** the fee is rejected and reported as an error. This never happens in the given stream; it is the deliberately failing test (`tests/test_xfail.py`).

## 7. Day 6 interest base

Is the Day 6 accrual computed on the Day 6 closing before or after capitalizing the earlier days' interest?

**Resolution:** before.

**Reason:** the interest is determined on each of the six days on its own and only paid at the close of Day 6, so it is more natural to compute it on the Day 6 closing balance without interest.

## 8. Instalments on the same value day

Real instalments are usually spread over time, but E10's three instalments all carry value date Day 5.

**Resolution:** accepted as given for E10.

**Reason:** several instalments on the same value day may be a customer paying off the final three instalments on the same day.

## 9. Booking day going backwards on the same account

This does not occur in the stream, but per-account clocks raise the question.

**Resolution:** an event with a strictly earlier booking day than the previous event on the same account is refused and reported as an error. Same-day events are allowed.

**Reason:** time going backwards on one account is more likely a fault than a feature, so the run must flag it as an error rather than absorb it.

## 10. Rounding mode

The brief names no rounding mode.

Readings:
- half-up;
- half-even.

**Resolution:** half-up.

**Reason:** half-up is the common commercial convention and what customers expect on a statement. It changes no figure in this stream: 0.114 rounds to 0.11 under either mode.

## 11. "Once per day": per value day or per booking day

The Day 5 close books three fees at once, for value days 2, 4 and 5.

Readings:
- one net fee per value day;
- one fee per booking day.

**Resolution:** one net fee per value day.

**Reason:** the rule ties the fee to that day's closing ledger balance, which is a value-day quantity. One fee per booking day would leave some negative days without a fee whenever a single close assesses several. Each late fee carries the negative day as its value date.
