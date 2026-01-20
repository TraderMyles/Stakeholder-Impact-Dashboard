from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class PolicyChoice(str, Enum):
    DEV_CAPITALISE_VS_EXPENSE = "DEV_CAPITALISE_VS_EXPENSE"
    IP_FAIR_VALUE_VS_COST = "IP_FAIR_VALUE_VS_COST"


class EvaluationRequest(BaseModel):
    policy_choice: PolicyChoice
    company_name: str = Field(default="SampleCo")
    currency: str = Field(default="GBP")
    revenue: float = Field(default=1200.0)
    operating_profit: float = Field(default=180.0)
    profit_after_tax: float = Field(default=120.0)
    equity: float = Field(default=800.0)
    debt: float = Field(default=300.0)
    shares_outstanding: float = Field(default=100.0)
    tax_rate: float = Field(default=0.25)
    covenant_max_gearing: Optional[float] = Field(default=None)


class ResponseMetadata(BaseModel):
    request_id: str
    timestamp_utc: str
    company_name: str
    policy_choice: PolicyChoice
    currency: str


class ScenarioOutput(BaseModel):
    label: str
    headline_metrics: Dict[str, float]


class StakeholderImpact(BaseModel):
    title: str
    bullet_impacts: List[str]
    narrative: str


class StakeholderOutputs(BaseModel):
    investors: StakeholderImpact
    lenders: StakeholderImpact
    management: StakeholderImpact
    regulators: StakeholderImpact


class EvaluationResponse(BaseModel):
    metadata: ResponseMetadata
    base_case: ScenarioOutput
    option_a: ScenarioOutput
    option_b: ScenarioOutput
    stakeholders: StakeholderOutputs
