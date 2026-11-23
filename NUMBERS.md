# Numbers

Every constant in the ledger, split into the ones chosen and the ones given by the brief. All constants live in `src/ledger/config.py`. Money is always an integer in minor units of an explicit currency.

## Chosen

### Rounding mode: half-up
Ties round away from zero. Reasons in AMBIGUITIES.md, item 10.

### Rounding point: each daily accrual

Each day's interest is rounded to the currency's precision when it is calculated, not the total at the end.

- Effect on ACC-001: the rounded accruals sum to 0.79 (0.10 + 0.10 + 0.26 + 0.11 + 0.11 + 0.11); the exact sum is 0.802.
- **Reason:** the brief implies it: the rounded daily accruals must sum exactly to the capitalized total.

### Rate as an integer: 4 basis points

`RATE_BP = 4`. The daily accrual is amount x 4 / 10,000, rounded half-up, in integer minor units.

- **Reason:** no floats; exact integer math. Basis points (1/10,000) is the coarsest integer scale that represents 0.04% exactly; half that resolution could not.

### Instalment remainder: +0.001 on the last instalment

E10's BHD 10.000 is 10,000 fils, which does not divide by 3. Each instalment is 10,000 // 3 = 3,333 fils and the remaining 1 fil goes on the last: 3.333, 3.333, 3.334.

- **Reason:** the last instalment carrying the residual is a standard practice.

## Given

Listed as given by the brief, not chosen:

| Constant | Value | In `config.py` |
|---|---|---|
| Overdraft fee | AED 25.00 | `FEE_AMOUNT = 2500`, `FEE_CURRENCY = "AED"` |
| Daily interest rate | 0.04% per day | `RATE_BP = 4` |
| Precision | AED 2 decimal places, BHD 3 | `PRECISION` |
| Window | 6 days | `DAYS = 6` |
| Opening balances | 0 for both accounts | the column computation starts from 0 |

## Test constants

None. The property tests were skipped, so there are no test constants.
