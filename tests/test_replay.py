import pytest

from ledger.replay import main, report, run


def test_report_prints_restated_days_under_new_labels() -> None:
    lines = report(run())
    assert "  D2-b  Day 2 closing  -395.00  (restated)" in lines
    assert "  D6-b  Day 6 closing after interest  285.79" in lines
    labels, account = [], ""
    for line in lines:
        if line.startswith("ACC-"):
            account = line.split()[0]
        elif line.startswith("  D"):
            labels.append((account, line.split()[0]))
    assert len(labels) == len(set(labels))  # never reused within an account


def test_main_prints_every_day(capsys: pytest.CaptureFixture[str]) -> None:
    main()
    out = capsys.readouterr().out
    assert all(f"=== Day {k} ===" in out for k in range(1, 7))
