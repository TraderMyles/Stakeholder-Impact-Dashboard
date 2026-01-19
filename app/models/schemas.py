from enum import Enum
from typing import Dict, List

from pydantic import BaseModel, Field


class PolicyChoice(str, Enum):
    DEV_CAPITALISE_VS_EXPENSE = "DEV_CAPITALISE_VS_EXPENSE"
    IP_FAIR_VALUE_VS_COST = "IP_FAIR_VALUE_VS_COST"


class EvaluationRequest(BaseModel):
    policy_choice: PolicyChoice
    company_name: str = Field(default="SampleCo")
    currency: str = Field(default="GBP")


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
