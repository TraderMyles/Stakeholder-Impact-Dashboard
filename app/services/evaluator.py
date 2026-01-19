from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.models.schemas import (
    EvaluationRequest,
    EvaluationResponse,
    PolicyChoice,
    ResponseMetadata,
    ScenarioOutput,
    StakeholderImpact,
    StakeholderOutputs,
)


def _metrics_for_choice(policy_choice: PolicyChoice) -> dict:
    if policy_choice == PolicyChoice.DEV_CAPITALISE_VS_EXPENSE:
        return {
            "base_case": {"eps": 1.42, "gearing": 28.0, "bonus_estimate": 1.1, "prudence_score": 6.5},
            "option_a": {"eps": 1.58, "gearing": 31.0, "bonus_estimate": 1.3, "prudence_score": 5.8},
            "option_b": {"eps": 1.30, "gearing": 24.0, "bonus_estimate": 0.9, "prudence_score": 7.2},
        }
    return {
        "base_case": {"eps": 1.10, "gearing": 22.0, "bonus_estimate": 0.8, "prudence_score": 7.4},
        "option_a": {"eps": 1.36, "gearing": 27.0, "bonus_estimate": 1.0, "prudence_score": 6.1},
        "option_b": {"eps": 0.98, "gearing": 19.0, "bonus_estimate": 0.7, "prudence_score": 8.0},
    }


def _stakeholders_for_choice(policy_choice: PolicyChoice) -> StakeholderOutputs:
    if policy_choice == PolicyChoice.DEV_CAPITALISE_VS_EXPENSE:
        return StakeholderOutputs(
            investors=StakeholderImpact(
                title="Investors",
                bullet_impacts=[
                    "Capitalising lifts near-term EPS visibility.",
                    "Cash conversion narrative stays neutral in the stub.",
                ],
                narrative=(
                    "Investors see higher short-term earnings with a larger asset base. "
                    "The trade-off is a longer payback story that may temper valuation multiples."
                ),
            ),
            lenders=StakeholderImpact(
                title="Lenders",
                bullet_impacts=[
                    "Higher assets support covenant headroom in this scenario.",
                    "Gearing ticks up from deferred expense treatment.",
                ],
                narrative=(
                    "Lenders note the stronger balance sheet optics, even as leverage rises. "
                    "They request clearer impairment triggers in the policy narrative."
                ),
            ),
            management=StakeholderImpact(
                title="Management",
                bullet_impacts=[
                    "Bonus metrics improve with capitalisation.",
                    "Delivery pressure increases to justify the asset.",
                ],
                narrative=(
                    "Management benefits from a smoother earnings profile. "
                    "Execution discipline becomes the key justification for the choice."
                ),
            ),
            regulators=StakeholderImpact(
                title="Regulators",
                bullet_impacts=[
                    "Expect tighter documentation on development criteria.",
                    "Scrutiny on impairment testing cadence.",
                ],
                narrative=(
                    "Regulators focus on evidence that capitalised projects meet recognition criteria. "
                    "They signal that disclosure quality will drive acceptance."
                ),
            ),
        )
    return StakeholderOutputs(
        investors=StakeholderImpact(
            title="Investors",
            bullet_impacts=[
                "Fair value introduces more volatility into EPS.",
                "Potential upside from remeasurement gains.",
            ],
            narrative=(
                "Investors weigh the transparency of fair value against earnings noise. "
                "They value the signal on asset quality but discount for volatility."
            ),
        ),
        lenders=StakeholderImpact(
            title="Lenders",
            bullet_impacts=[
                "Fair value swings complicate covenant predictability.",
                "Cost basis looks steadier in stress tests.",
            ],
            narrative=(
                "Lenders prefer stability for covenant monitoring. "
                "They request sensitivity disclosures around valuation assumptions."
            ),
        ),
        management=StakeholderImpact(
            title="Management",
            bullet_impacts=[
                "Valuation teams gain prominence in reporting cycles.",
                "Narrative must explain revaluation drivers.",
            ],
            narrative=(
                "Management spends more time defending valuation inputs. "
                "A clear story on value drivers becomes central to stakeholder trust."
            ),
        ),
        regulators=StakeholderImpact(
            title="Regulators",
            bullet_impacts=[
                "Expect robust valuation governance processes.",
                "Cost basis may reduce disclosure burden.",
            ],
            narrative=(
                "Regulators focus on valuation independence and model governance. "
                "They look for consistency in assumptions across reporting periods."
            ),
        ),
    )


def evaluate(payload: EvaluationRequest) -> EvaluationResponse:
    metrics = _metrics_for_choice(payload.policy_choice)
    stakeholders = _stakeholders_for_choice(payload.policy_choice)
    timestamp = datetime.now(timezone.utc).isoformat()

    return EvaluationResponse(
        metadata=ResponseMetadata(
            request_id=str(uuid4()),
            timestamp_utc=timestamp,
            company_name=payload.company_name,
            policy_choice=payload.policy_choice,
            currency=payload.currency,
        ),
        base_case=ScenarioOutput(label="Base case", headline_metrics=metrics["base_case"]),
        option_a=ScenarioOutput(label="Option A", headline_metrics=metrics["option_a"]),
        option_b=ScenarioOutput(label="Option B", headline_metrics=metrics["option_b"]),
        stakeholders=stakeholders,
    )
