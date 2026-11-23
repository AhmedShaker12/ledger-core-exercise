# Rejected

## Criteria refused

- **#2, "E7 causes exactly one overdraft fee, on Day 2":** refused. E7 is value-dated Day 2, so as of Day 5 the closing ledger balances of Days 2, 4 and 5 are negative (Day 3 stays at +5.00 thanks to the Day 3 credit). Each negative day gets a fee: three, not one.
- **#4, "a settlement referencing an unknown authorization must be rejected":** refused. No rule in the brief requires a settlement to reference an authorization. Also, in practice an issuer cannot refuse cleared funds. E6 (Auth-Z) is posted and reported as a warning. See also AMBIGUITIES.md, item 1.
- **#7, "the three BHD instalments must each be BHD 3.334":** refused. 3 x 3.334 = 10.002, not 10.000. See also AMBIGUITIES.md, item 4.

## Approaches abandoned mid-build

- **Authorization status inside ledger entries:** abandoned. A hold that later settles would need its entry changed, which breaks append-only. Authorizations are now MEMO entries (hold placed, hold released, declined) in the same append-only store; their state is derived from those entries.
- **Reprinting every balance in every day's output:** abandoned. Too much repetition; replaced by numbers written once with labels (D1-a style), new label on restatement.
- **A genuinely failing test with red CI:** abandoned in favour of `xfail(strict=True)`, which keeps CI meaningful while the test still fails and can't silently pass.
- **A general dependency graph:** considered and rejected, because the dependencies are strictly linear per account.
- **A separate DECISIONS.md:** abandoned; NUMBERS, AMBIGUITIES and REJECTED cover it.
