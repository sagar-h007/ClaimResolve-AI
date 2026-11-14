from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class DashboardStatsResponse(BaseModel):
    total_claims_processed: int
    total_denied_claims: int
    appeals_generated: int
    appeals_pending_review: int
    recovered_revenue: float
    total_denied_value: float
    appeal_success_rate: float  # e.g. 74.5%
    average_processing_time_hours: float  # e.g. 1.8 hrs


class TimeSeriesItem(BaseModel):
    date: str
    claims_count: int
    appeals_drafted: int
    recovered_revenue: float


class DistributionItem(BaseModel):
    name: str
    count: int
    amount: float
    percentage: float


class AnalyticsOverviewResponse(BaseModel):
    kpis: DashboardStatsResponse
    claims_over_time: List[TimeSeriesItem]
    denial_reasons_distribution: List[DistributionItem]
    payer_distribution: List[DistributionItem]
    appeal_outcomes: List[DistributionItem]
    monthly_recovered_revenue: List[TimeSeriesItem]

