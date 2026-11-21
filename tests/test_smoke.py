import ledger


def test_package_imports() -> None:
    assert ledger.__name__ == "ledger"
