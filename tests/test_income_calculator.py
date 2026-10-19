import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from income_calculator import IncomeStream, best_stream, total_profit


def test_monthly_profit():
    s = IncomeStream("blog", monthly_revenue=100, monthly_cost=30)
    assert s.monthly_profit == 70


def test_total_profit():
    streams = [
        IncomeStream("blog", 100, 30),
        IncomeStream("ebook", 200, 50),
    ]
    assert total_profit(streams) == 220


def test_best_stream():
    streams = [
        IncomeStream("blog", 100, 30),
        IncomeStream("ebook", 200, 50),
    ]
    assert best_stream(streams).name == "ebook"


def test_best_stream_empty():
    assert best_stream([]) is None
