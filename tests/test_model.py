from ledger.model import Category, Direction, Entry, Kind, fmt


def entry(kind: Kind, direction: Direction, amount: int = 100) -> Entry:
    return Entry(1, "E1", "ACC-001", "AED", amount, direction, kind, 1, 1)


def test_signed_amount_follows_direction() -> None:
    assert entry(Kind.CREDIT, Direction.CR).signed == 100
    assert entry(Kind.DEBIT, Direction.DR).signed == -100


def test_category_derives_from_kind() -> None:
    assert entry(Kind.FEE, Direction.DR).category is Category.POSTED
    assert entry(Kind.HOLD_PLACED, Direction.DR).category is Category.MEMO


def test_fmt_uses_currency_precision() -> None:
    assert fmt(2500, "AED") == "25.00"
    assert fmt(-37000, "AED") == "-370.00"
    assert fmt(4, "BHD") == "0.004"
