"""수익 자동화 테스트용 간단한 계산 모듈."""

from dataclasses import dataclass


@dataclass
class IncomeStream:
    """하나의 수익원(예: 블로그 광고, 디지털 상품)."""

    name: str
    monthly_revenue: float
    monthly_cost: float = 0.0

    @property
    def monthly_profit(self) -> float:
        return self.monthly_revenue - self.monthly_cost


def total_profit(streams: list[IncomeStream]) -> float:
    """모든 수익원의 월 순이익 합계."""
    return sum(s.monthly_profit for s in streams)


def best_stream(streams: list[IncomeStream]) -> IncomeStream | None:
    """월 순이익이 가장 큰 수익원. 목록이 비어 있으면 None."""
    if not streams:
        return None
    return max(streams, key=lambda s: s.monthly_profit)
